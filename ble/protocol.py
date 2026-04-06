import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def decode_chipsea_v1(data: bytes) -> dict:
    """
    Decodifica registros do protocolo Chipsea V1 (FFF4).
    """
    if len(data) < 10:
        logger.warning(f"V1 decodificação falhou. Tamanho inesperado: {len(data)}")
        return None
        
    if data[0] == 0xF2 and data[1] == 0x00:
        return None # Final dos dados do histórico
        
    try:
        b0 = data[0]
        year = ((b0 & 0xF0) >> 4) + 2017
        month = (b0 & 0x0F)
        # Ajuste de segurança para o mês (1 a 12)
        if month == 0: month = 1

        day = data[1]
        hour = data[2]
        minute = data[3]
        second = data[4]

        # Evita erro na conversão do timestamp (ex: device battery out)
        if day == 0: day = 1
        if hour > 23: hour = 0
        if minute > 59: minute = 0
        if second > 59: second = 0
        
        dt = datetime(year, month, day, hour, minute, second)
        
        b5 = data[5]
        b6 = data[6]
        
        scale_type = b5 & 0xF0
        weight_raw = ((b5 & 0x0F) << 8) + b6
        weight_kg = weight_raw * 0.1
        
        b7 = data[7]
        b8 = data[8]
        b9 = data[9]
        impedance = b7 + (b8 << 8) + (b9 << 16)
        
        return {
            "protocol": "v1",
            "timestamp": dt,
            "weight_kg": weight_kg,
            "impedance": impedance if impedance > 0 else None,
            "is_stable": True, # Registros finalizados são estáveis
            "scale_type": scale_type,
            "raw_hex": data.hex()
        }
    except Exception as e:
        logger.error(f"Erro ao decodificar V1 {data.hex()}: {e}")
        return None

def decode_chipsea_v2_weight(data: bytes) -> dict:
    """
    Decode real-time weight from Chipsea V2 FFB2 notify.
    Maverick Smart-S8: weight at bytes 1-2 little-endian, raw units = 10g (÷100 for kg).
    """
    if len(data) < 3:
        return None

    hex_str = data.hex()

    # Weight: bytes 1-2 little-endian, units of 10g → divide by 100 for kg
    weight_raw = int.from_bytes(data[1:3], 'little')
    weight_kg = weight_raw / 100.0

    # Stability: byte 3 or byte 4 depending on packet length
    is_stable = False
    if len(data) >= 5:
        is_stable = data[4] == 0x00  # 0x01=measuring, 0x00=stable/final
    elif len(data) >= 4:
        is_stable = data[3] in (0x00, 0x02)

    if weight_kg < 2.0:
        return None  # empty scale noise

    if weight_kg > 300.0:
        return None  # obviously wrong

    return {"protocol": "v2_weight", "weight_kg": weight_kg,
            "is_stable": is_stable, "raw_hex": hex_str}


def decode_chipsea_v2_bia(data: bytes) -> dict:
    """
    Decode FFB3 indicate packets from Maverick Smart-S8 (Chipsea V2).

    Packet structure (20 bytes):
      [0]    sequence counter (increments per packet)
      [1]    record type: 0x18 = config/init, 0x23 = measurement history
      [2]    sub-packet index: 0x00 = data, 0x01/0x02 = continuation (empty)
      [3:]   payload (depends on record type)

    Measurement sub-packet 0 (byte[1]=0x23, byte[2]=0x00):
      [3:7]  timestamp (device-internal encoding)
      [7]    impedance low byte (tentative)
      [8]    user metadata (age or slot)
      [9:12] weight: 3 bytes big-endian, ÷1000 for kg
      [12:]  flags / padding
    """
    if len(data) < 12:
        return None

    hex_str = data.hex()
    record_type = data[1]
    sub_index = data[2]

    # ── Init / config packets (record type 0x18 or byte[3] == 0xAA) ──
    if record_type == 0x18 or data[3] == 0xAA:
        return {"protocol": "v2_init", "raw_hex": hex_str, "is_init": True}

    # ── Sub-packets 01/02: continuation frames (always zeros) ──
    if sub_index != 0x00:
        return {"protocol": "v2_init", "raw_hex": hex_str, "is_init": True}

    # ── All-zero payload: skip ──
    if all(b == 0 for b in data[3:]):
        return {"protocol": "v2_init", "raw_hex": hex_str, "is_init": True}

    # ── Measurement data (record type 0x23, sub-packet 0x00) ──
    # Weight: bytes 9-11 big-endian, units of 1g → ÷1000 for kg
    weight_raw = int.from_bytes(data[9:12], 'big')
    weight_kg = weight_raw / 1000.0

    if weight_kg < 2.0 or weight_kg > 300.0:
        logger.debug(f"FFB3 weight out of range: {weight_kg:.3f} kg from {hex_str}")
        return None

    # Impedance: byte[7] might carry impedance data (varies between measurements)
    # Values seen: 0x96=150, 0x9d=157 — tentative, needs more data
    impedance = None
    imp_byte = data[7]
    if imp_byte > 0:
        impedance = imp_byte  # raw value, may need scaling

    logger.info(f"FFB3 decoded: {weight_kg:.1f} kg, imp_raw={imp_byte} from {hex_str}")

    return {"protocol": "v2_bia", "weight_kg": weight_kg,
            "impedance": impedance,
            "is_stable": True, "raw_hex": hex_str}
