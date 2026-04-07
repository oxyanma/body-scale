#!/usr/bin/env python3
"""
Segmental BLE capture for Maverick Smart-S8 (8-electrode).

HOLD THE HAND BARS during the entire measurement!
The scale needs all 8 electrodes to measure segmental impedance.

Captures all FFB2/FFB3 packets and analyzes sub-packets 01/02
which should contain segmental impedance data when hand bars are held.
"""
import asyncio
import sys
from datetime import datetime
from bleak import BleakScanner, BleakClient

SVC_FFB0 = "0000ffb0-0000-1000-8000-00805f9b34fb"
CHR_FFB1 = "0000ffb1-0000-1000-8000-00805f9b34fb"
CHR_FFB2 = "0000ffb2-0000-1000-8000-00805f9b34fb"
CHR_FFB3 = "0000ffb3-0000-1000-8000-00805f9b34fb"

all_packets = []
ffb3_by_seq = {}  # seq -> {0: data, 1: data, 2: data}
got_stable = False


def on_ffb2(sender, data: bytearray):
    global got_stable
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    raw = bytes(data)
    all_packets.append(("FFB2", ts, raw))

    if len(raw) < 9:
        return

    weight_raw = raw[1] | (raw[2] << 8)
    weight_kg = weight_raw / 10.0
    measuring = raw[4]
    imp_raw = raw[7] | (raw[8] << 8)

    if weight_kg > 5.0:
        state = "MEASURING" if measuring == 1 else "STABLE"
        if measuring != 1:
            got_stable = True
        print(f"\r  [{ts}] FFB2  {weight_kg:7.1f} kg  [{state}]  imp={imp_raw}", end="", flush=True)


def on_ffb3(sender, data: bytearray):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    raw = bytes(data)
    all_packets.append(("FFB3", ts, raw))

    if len(raw) < 3:
        return

    seq = raw[0]
    record_type = raw[1]
    sub_index = raw[2]
    payload = raw[3:]
    is_nonzero = any(b != 0 for b in payload)

    # Group by sequence
    if seq not in ffb3_by_seq:
        ffb3_by_seq[seq] = {}
    ffb3_by_seq[seq][sub_index] = raw

    # Highlight non-zero sub-packets
    marker = "★ DATA" if is_nonzero else "  empty"
    print(f"\n  [{ts}] FFB3  seq={seq:#04x} type={record_type:#04x} sub={sub_index}  {marker}")
    print(f"           hex: {raw.hex()}")

    if is_nonzero:
        # Detailed byte breakdown
        print(f"           bytes: ", end="")
        for i, b in enumerate(raw):
            print(f"[{i}]={b:#04x}({b:3d}) ", end="")
            if (i + 1) % 8 == 0:
                print(f"\n                  ", end="")
        print()

        if sub_index == 0x00 and len(raw) >= 12:
            # Known: bytes 9:12 = weight (BE, ÷1000)
            weight_raw = int.from_bytes(raw[9:12], 'big')
            weight_kg = weight_raw / 1000.0
            imp_byte = raw[7]
            print(f"           → sub0: weight={weight_kg:.3f}kg, imp_byte={imp_byte}")

        elif sub_index in (0x01, 0x02):
            # SEGMENTAL DATA — try various decodings
            print(f"           → sub{sub_index} NON-ZERO! Possible segmental impedance:")
            # Try 2-byte pairs (big-endian and little-endian)
            for i in range(3, len(raw) - 1, 2):
                val_be = (raw[i] << 8) | raw[i + 1]
                val_le = raw[i] | (raw[i + 1] << 8)
                if val_be > 0:
                    print(f"             bytes[{i}:{i+2}] BE={val_be} LE={val_le}"
                          f"  (÷10={val_be/10:.1f} ÷100={val_be/100:.2f})")


async def main():
    print("=" * 65)
    print("  Maverick Smart-S8 — SEGMENTAL Capture (8 electrodes)")
    print("=" * 65)
    print()
    print("  ⚠️  HOLD THE HAND BARS during the ENTIRE measurement!")
    print("  The scale needs hand contact for segmental impedance.")
    print()

    # Scan
    print("[SCAN] Looking for scale — step on it to wake BLE...")
    target = None
    for attempt in range(30):
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        for addr, (dev, adv) in devices.items():
            uuids = [u.lower() for u in adv.service_uuids]
            name = dev.name or adv.local_name or ""
            if SVC_FFB0 in uuids or "maverick" in name.lower():
                target = dev
                print(f"[FOUND] {name} [{dev.address}] RSSI={adv.rssi}")
                break
        if target:
            break
        sys.stdout.write(f"\r[SCAN] Attempt {attempt+1}/30 — not found yet...")
        sys.stdout.flush()

    if not target:
        print("\n[ERROR] Scale not found!")
        sys.exit(1)

    print(f"[CONNECT] {target.name}...")
    async with BleakClient(target, timeout=20.0) as client:
        print(f"[OK] Connected")

        # List all characteristics
        print("\n[GATT]")
        for svc in client.services:
            if "ffb" in svc.uuid.lower():
                for c in svc.characteristics:
                    print(f"  {c.uuid} [{','.join(c.properties)}]")

        # Subscribe
        await client.start_notify(CHR_FFB2, on_ffb2)
        await client.start_notify(CHR_FFB3, on_ffb3)
        print("[OK] Subscribed FFB2 + FFB3")

        # Send user profile
        try:
            await client.write_gatt_char(CHR_FFB1, bytes([0x0D, 0x10, 0x01]))  # kg
            await asyncio.sleep(0.3)
            await client.write_gatt_char(CHR_FFB1, bytes([0x0D, 0x12, 175, 25, 0x01, 0x00]))  # M, 175cm, 25y
            print("[OK] Profile sent (175cm, 25y, male)")
        except Exception as e:
            print(f"[WARN] FFB1: {e}")

        print()
        print("=" * 65)
        print("  >>> STEP ON SCALE + GRAB HAND BARS — HOLD THEM! <<<")
        print("  >>> Stay still until scale beeps (up to 2 min)   <<<")
        print("=" * 65)
        print()

        # Capture for 150 seconds (segmental takes longer)
        await asyncio.sleep(150)

        try:
            await client.stop_notify(CHR_FFB2)
            await client.stop_notify(CHR_FFB3)
        except:
            pass

    # ═══════════════ ANALYSIS ═══════════════
    print()
    print("=" * 65)
    print(f"  CAPTURE COMPLETE — {len(all_packets)} packets")
    print("=" * 65)

    ffb3_total = [p for p in all_packets if p[0] == "FFB3"]
    print(f"  FFB2 packets: {len(all_packets) - len(ffb3_total)}")
    print(f"  FFB3 packets: {len(ffb3_total)}")

    # Analyze FFB3 groups
    print(f"\n  FFB3 measurement groups: {len(ffb3_by_seq)}")
    has_segmental = False

    for seq in sorted(ffb3_by_seq.keys()):
        group = ffb3_by_seq[seq]
        subs = sorted(group.keys())
        print(f"\n  ── Seq {seq:#04x} (sub-packets: {subs}) ──")

        for si in subs:
            pkt = group[si]
            payload = pkt[3:]
            nonzero = any(b != 0 for b in payload)
            status = "★ DATA" if nonzero else "  zeros"
            print(f"    sub[{si}]: {pkt.hex()}  {status}")

            if nonzero and si in (1, 2):
                has_segmental = True
                print(f"    *** SEGMENTAL DATA FOUND IN SUB-PACKET {si}! ***")
                # Decode as 2-byte pairs
                for i in range(3, len(pkt) - 1, 2):
                    val = (pkt[i] << 8) | pkt[i + 1]
                    if val > 0:
                        print(f"      bytes[{i}:{i+2}] = {val} (÷10={val/10:.1f}, ÷100={val/100:.2f})")

    print()
    if has_segmental:
        print("  ✅ SEGMENTAL DATA DETECTED in sub-packets 01/02!")
        print("     The scale IS sending per-limb impedance data.")
    else:
        print("  ❌ Sub-packets 01/02 are ALL ZEROS.")
        print("     Possible reasons:")
        print("       1. You didn't hold the hand bars")
        print("       2. Hand contact was lost during measurement")
        print("       3. Scale doesn't transmit segmental data via BLE")
        print("       4. Need different FFB1 command to enable segmental mode")

    # Save raw dump
    outfile = "/tmp/maverick_segmental.txt"
    with open(outfile, "w") as f:
        for tag, ts, raw in all_packets:
            f.write(f"{tag} [{ts}] {raw.hex()}\n")
        f.write(f"\n# Groups:\n")
        for seq in sorted(ffb3_by_seq.keys()):
            for si in sorted(ffb3_by_seq[seq].keys()):
                pkt = ffb3_by_seq[seq][si]
                f.write(f"seq={seq:#04x} sub={si}: {pkt.hex()}\n")
    print(f"\n  Raw data → {outfile}")


if __name__ == "__main__":
    asyncio.run(main())
