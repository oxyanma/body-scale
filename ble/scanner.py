import asyncio
import logging
from bleak import BleakScanner
import os

from .constants import (
    CHIPSEA_SERVICE_UUID, 
    CHIPSEA_V2_SERVICE_UUID,
    CHIPSEA_DEVICE_NAME_PREFIXES
)

# Mock support for development without hardware
if os.environ.get("USE_MOCK_BLE", "0") == "1":
    from tests.test_mock_scale import MockBleakScanner as BleakScanner

logger = logging.getLogger(__name__)

async def scan_for_scale(timeout=10.0):
    """
    Realiza o scan BLE procurando por balanças Chipsea.
    Filtra pelo nome do dispositivo e/ou UUID de serviço.
    """
    logger.info(f"Iniciando scan BLE por {timeout} segundos...")
    try:
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    except Exception as e:
        logger.error(f"Erro durante o scan BLE: {e}")
        return []

    found_devices = []
    
    # devices param is a dict {address: (device, adv_data)} in modern bleak
    for address, tpl in devices.items():
        if len(tpl) == 2:
            device, adv_data = tpl
            name = device.name or adv_data.local_name or "Unknown"
            uuids = [u.lower() for u in adv_data.service_uuids]
        else:
            # Fallback for mock or older bleak
            device = tpl
            name = device.name or "Unknown"
            uuids = [u.lower() for u in getattr(device, 'metadata', {}).get('uuids', [])]
        
        is_chipsea_name = any(prefix.lower() in name.lower() for prefix in CHIPSEA_DEVICE_NAME_PREFIXES)
        is_chipsea_uuid = (CHIPSEA_SERVICE_UUID.lower() in uuids) or (CHIPSEA_V2_SERVICE_UUID.lower() in uuids)
        
        if is_chipsea_name or is_chipsea_uuid:
            if CHIPSEA_SERVICE_UUID.lower() in uuids:
                protocol = "v1"
            elif CHIPSEA_V2_SERVICE_UUID.lower() in uuids:
                protocol = "v2"
            else:
                protocol = "unknown"

            found_devices.append({
                "address": address,
                "name": name,
                "rssi": device.rssi,
                "protocol_hint": protocol,
                "device": device
            })
            logger.info(f"Encontrado dispositivo Chipsea: {name} ({address}) RSSI: {device.rssi} Proto: {protocol}")
            
    return found_devices

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    devices = asyncio.run(scan_for_scale())
    if not devices:
        print("Nenhuma balança encontrada.")
    else:
        print(f"{len(devices)} balança(s) encontrada(s):")
        for d in devices:
            print(f"- {d['name']} [{d['address']}] (RSSI: {d['rssi']} dBm)")
