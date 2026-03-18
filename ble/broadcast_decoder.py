import logging

logger = logging.getLogger(__name__)

def decode_okok_broadcast(company_id: int, byte_data: bytes):
    """
    Decodifica o payload "Manufacturer Data" passivo emitido 
    por balanças Chipsea/OKOK, modelo F-6988 e similares.
    """
    # Filtro rígido para evitar ler beacons da Microsoft/Apple
    # A F-6988 sempre envia 13 bytes.
    if len(byte_data) != 13:
        return None
        
    # A assinatura clássica da OKOK no meio do payload é 0x0A 0x01 (nos bytes 4 e 5)
    if byte_data[4] != 0x0a or byte_data[5] != 0x01:
        return None

    hex_data = byte_data.hex()
    
    try:
        # Extrai o peso dos primeiros 2 bytes (Big Endian)
        weight_raw = (byte_data[0] << 8) | byte_data[1]
        weight_kg = weight_raw / 100.0
        
        # Ignorar pesos absurdos (ex: pé na balança, ruído)
        if weight_kg < 5.0 or weight_kg > 400.0:
            return None
            
        # Decodifica impedância (bytes 2 e 3)
        impedance_raw = (byte_data[2] << 8) | byte_data[3]
        
        # A impedância da OKOK/Chipsea varia muito, porém costuma ser enviada quando fecha o cálculo.
        # Em fase de medição, a balança envia `0000`. Quando consolida, envia `1770` (ex: 600 ohm).
        impedance = 0.0
        if impedance_raw > 0:
            impedance = impedance_raw / 10.0
        
        is_stable = (impedance > 0.0 or byte_data[6] > 0) # Byte 6 costuma rolar "time" ou sequence
        is_final_bia = (impedance > 0.0)

        return {
            "weight_kg": weight_kg,
            "impedance": impedance if is_final_bia else None,
            "is_stable": is_stable,
            "is_final_bia": is_final_bia,
            "raw_hex": byte_data.hex(),
            "company_id": company_id
        }
    except Exception as e:
        logger.debug(f"Erro ao decodificar broadcast OKOK: {e} - Hex: {byte_data.hex()}")
        return None
