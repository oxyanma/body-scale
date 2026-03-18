import pytest
from datetime import datetime
from ble.protocol import decode_chipsea_v1

def test_decode_v1_known_bytes():
    """
    Test V1 decoding using known hex bytes.
    The instruction states:
    'Ex: 67-1F-0F-1E-3B-F2-E0-7A-12-00 deve decodificar para 
    31/Jul/2023 15:30:59, 73.6kg, impedância 4730.'
    """
    hex_str = "671f0f1e3bf2e07a1200"
    data = bytes.fromhex(hex_str)
    
    result = decode_chipsea_v1(data)
    
    assert result is not None
    assert result["protocol"] == "v1"
    
    # 67 (hex) -> 0110 0111 (bin) -> year = 0110 (6) + 2017 = 2023. month = 0111 (7) -> Jul
    assert result["timestamp"] == datetime(2023, 7, 31, 15, 30, 59)
    
    # weight b5(F2), b6(E0). b5 & 0x0F = 0x02. 0x02 << 8 + E0 = 200 + E0(224) = 512 + 224 = 736
    # weight_kg = 736 * 0.1 = 73.6
    assert abs(result["weight_kg"] - 73.6) < 0.01
    
    # impedance b7(7A), b8(12), b9(00). 7A (122) + 12(18) << 8 = 122 + 4608 = 4730
    assert result["impedance"] == 4730
    assert result["is_stable"] is True
