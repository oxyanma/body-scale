import asyncio
import threading
import logging
from bleak import BleakScanner, BleakClient
from database.db import get_session
from database.models import User
from dashboard.state import app_state
from calculations.body_composition import get_all_metrics
from ble.protocol import decode_chipsea_v2_weight, decode_chipsea_v2_bia

logger = logging.getLogger(__name__)

# Chipsea V2 UUIDs
SVC_FFB0 = "0000ffb0-0000-1000-8000-00805f9b34fb"
CHR_FFB1 = "0000ffb1-0000-1000-8000-00805f9b34fb"  # Write
CHR_FFB2 = "0000ffb2-0000-1000-8000-00805f9b34fb"  # Notify (weight)
CHR_FFB3 = "0000ffb3-0000-1000-8000-00805f9b34fb"  # Indicate (BIA)

SCAN_TIMEOUT = 300  # 5 minutes — user can take their time
MEASURE_TIMEOUT = 120  # 2 minutes once connected
MIN_VALID_WEIGHT = 5.0  # kg — anything below is noise/init


def _get_active_user():
    height, age, sex, act, waist, hip = 175, 35, 'M', 'moderate', None, None
    try:
        from database.db import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.is_active == True).first()
            if user:
                height = user.height_cm
                age = user.age
                sex = user.sex
                act = user.activity_level
                waist = getattr(user, 'waist_cm', None)
                hip = getattr(user, 'hip_cm', None)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
    return height, age, sex, act, waist, hip


def _build_unit_cmd():
    return bytes([0x0D, 0x10, 0x01])  # kg


def _build_user_cmd(height_cm, age, sex):
    gender_byte = 0x01 if sex == 'M' else 0x00
    return bytes([0x0D, 0x12, int(height_cm) & 0xFF, int(age) & 0xFF, gender_byte, 0x00])


def _is_scale(device, advertisement_data):
    """Check if a BLE device is our scale."""
    uuids = [u.lower() for u in advertisement_data.service_uuids]
    name = (device.name or advertisement_data.local_name or "").lower()
    return SVC_FFB0 in uuids or "maverick" in name or "smart-s" in name


async def _wait_for_scale():
    """Continuous BLE scan — returns BLEDevice the instant the scale appears."""
    found_event = asyncio.Event()
    result = [None]

    def _on_detect(device, adv):
        if result[0] is None and _is_scale(device, adv):
            name = device.name or adv.local_name or "?"
            logger.info(f"Scale detected: {name} [{device.address}] rssi={adv.rssi}")
            result[0] = device
            found_event.set()

    scanner = BleakScanner(detection_callback=_on_detect)
    logger.info(f"Starting continuous scan (up to {SCAN_TIMEOUT}s)...")
    await scanner.start()
    try:
        await asyncio.wait_for(found_event.wait(), timeout=SCAN_TIMEOUT)
    except asyncio.TimeoutError:
        pass
    finally:
        await scanner.stop()

    return result[0]


async def _run_measurement():
    user_height, user_age, user_sex, user_act, user_waist, user_hip = _get_active_user()
    logger.info(f"User profile: h={user_height} age={user_age} sex={user_sex}")

    # --- Phase 1: Continuous scan until scale appears ---
    app_state.set_status("Listening...")
    device = await _wait_for_scale()

    if not device:
        app_state.set_status("Disconnected")
        app_state.set_scan_error("Scale not found after 5 min. Step on the scale to wake it up and try again.")
        return

    dev_name = device.name or "Scale"
    app_state.set_status(f"Connected — waiting for measurement...", device_name=dev_name)

    # --- Phase 2: Connect + measure ---
    final_event = asyncio.Event()
    best_weight = [0.0]
    best_impedance = [None]
    raw_packets = []
    ffb3_count = [0]  # track FFB3 measurement packets received

    def _update_metrics(weight, impedance=None):
        if weight and weight >= MIN_VALID_WEIGHT:
            metrics = get_all_metrics(
                weight, user_height, user_age, user_sex,
                impedance, user_act,
                waist_cm=user_waist, hip_cm=user_hip
            )
            app_state.set_metrics(metrics)

    def on_ffb2(sender, data: bytearray):
        raw = bytes(data)
        logger.info(f"FFB2 [{len(raw)}B]: {raw.hex()}")
        raw_packets.append(("FFB2", raw))
        decoded = decode_chipsea_v2_weight(raw)
        if decoded and decoded.get("weight_kg") and decoded["weight_kg"] >= MIN_VALID_WEIGHT:
            w = decoded["weight_kg"]
            stable = decoded.get("is_stable", False)
            logger.info(f"FFB2: {w:.2f} kg stable={stable} ({decoded['protocol']})")
            best_weight[0] = w
            app_state.update_weight(w, stable=stable)
            app_state.set_status(f"Connected — {w:.1f} kg", device_name=dev_name)
            _update_metrics(w)
            if stable:
                _update_metrics(w, best_impedance[0])
                final_event.set()

    def on_ffb3(sender, data: bytearray):
        raw = bytes(data)
        logger.info(f"FFB3 [{len(raw)}B]: {raw.hex()}")
        raw_packets.append(("FFB3", raw))
        decoded = decode_chipsea_v2_bia(raw)
        if not decoded:
            return
        if decoded.get("is_init"):
            logger.info(f"FFB3 init/skip: {raw.hex()}")
            return
        w = decoded.get("weight_kg")
        imp = decoded.get("impedance")
        logger.info(f"FFB3 measurement: w={w} imp={imp} ({decoded['protocol']})")
        ffb3_count[0] += 1
        if w and w >= MIN_VALID_WEIGHT:
            best_weight[0] = w
            app_state.update_weight(w, stable=True)
            app_state.set_status(f"Connected — {w:.1f} kg (history)", device_name=dev_name)
        if imp and imp > 0:
            best_impedance[0] = imp
            app_state.update_impedance(imp)

    try:
        async with BleakClient(device, timeout=20.0) as client:
            if not client.is_connected:
                app_state.set_scan_error("Failed to connect to the scale.")
                app_state.set_status("Disconnected")
                return

            logger.info(f"Connected to {dev_name}")

            # Subscribe
            await client.start_notify(CHR_FFB2, on_ffb2)
            logger.info("Subscribed FFB2")
            try:
                await client.start_notify(CHR_FFB3, on_ffb3)
                logger.info("Subscribed FFB3")
            except Exception as e:
                logger.warning(f"FFB3 subscribe failed: {e}")

            # Send init commands
            try:
                await client.write_gatt_char(CHR_FFB1, _build_unit_cmd())
                await asyncio.sleep(0.3)
                await client.write_gatt_char(CHR_FFB1, _build_user_cmd(user_height, user_age, user_sex))
                logger.info("Sent unit + user profile to FFB1")
            except Exception as e:
                logger.warning(f"FFB1 write failed: {e}")

            app_state.set_status(f"Connected — step on the scale", device_name=dev_name)

            # Wait for weight data from FFB2 (live) or FFB3 (history).
            # Strategy: poll every 5s. Once we have valid weight and data
            # stops flowing for 15s, finalize.
            max_wait = MEASURE_TIMEOUT
            no_change_rounds = 0
            prev_weight = 0.0
            prev_ffb3 = 0
            elapsed = 0

            while elapsed < max_wait:
                # Check if FFB2 gave a stable live reading (instant finalize)
                if final_event.is_set():
                    logger.info(f"FFB2 stable reading: {best_weight[0]:.1f} kg")
                    break

                await asyncio.sleep(5)
                elapsed += 5

                cur_weight = best_weight[0]
                cur_ffb3 = ffb3_count[0]

                if cur_weight >= MIN_VALID_WEIGHT:
                    # We have valid weight — check if data stopped flowing
                    if cur_weight == prev_weight and cur_ffb3 == prev_ffb3:
                        no_change_rounds += 1
                        if no_change_rounds >= 3:  # 15s of no new data
                            logger.info(f"Data stable for 15s, finalizing")
                            break
                    else:
                        no_change_rounds = 0
                        app_state.set_status(
                            f"Connected — {cur_weight:.1f} kg",
                            device_name=dev_name
                        )

                prev_weight = cur_weight
                prev_ffb3 = cur_ffb3

            # Finalize
            if best_weight[0] >= MIN_VALID_WEIGHT:
                _update_metrics(best_weight[0], best_impedance[0])
                app_state.set_status("Done")
                logger.info(f"Measurement finalized: {best_weight[0]:.1f} kg, imp={best_impedance[0]}")
            else:
                app_state.set_status("Disconnected")
                app_state.set_scan_error(
                    "No valid weight received. Close the Maverick app on your phone, "
                    "remove the Bluetooth bond and try again."
                )

            try:
                await client.stop_notify(CHR_FFB2)
            except Exception:
                pass
            try:
                await client.stop_notify(CHR_FFB3)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"GATT error: {e}", exc_info=True)
        app_state.set_status("Disconnected")
        app_state.set_scan_error(f"Connection error: {e}")

    # Dump raw packets for protocol debugging
    if raw_packets:
        logger.info(f"=== Raw packets ({len(raw_packets)}) ===")
        for tag, pkt in raw_packets:
            logger.info(f"  {tag}: {pkt.hex()}")


def run_ble_workflow():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_measurement())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Fatal BLE error: {e}", exc_info=True)
        app_state.set_status("Disconnected")
        app_state.set_scan_error(f"Execution error: {e}")


def start_ble_measurement_thread():
    app_state.reset()
    t = threading.Thread(target=run_ble_workflow, daemon=True)
    t.start()
