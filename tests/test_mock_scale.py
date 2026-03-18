import asyncio
import logging

logger = logging.getLogger(__name__)

class MockBleakClient:
    """
    Simula o comportamento de um BleakClient conectado a uma balança Chipsea.
    Permite rodar o projeto sem hardware físico.
    """
    def __init__(self, address_or_device, protocol_version="v2"):
        self.address = address_or_device.address if hasattr(address_or_device, 'address') else str(address_or_device)
        self.is_connected = False
        self.protocol_version = protocol_version
        self._notify_callbacks = {}
        self._simulation_task = None
        
        self.mock_weight = 75.5  # Peso alvo para simular
        self.mock_impedance = 500  # Impedância simulada

    async def connect(self, **kwargs):
        self.is_connected = True
        logger.info(f"[Mock] Conectado a {self.address}")
        return True

    async def disconnect(self):
        self.is_connected = False
        if self._simulation_task:
            self._simulation_task.cancel()
        logger.info("[Mock] Desconectado")
        return True

    async def start_notify(self, char_uuid, callback, **kwargs):
        uuid_str = str(char_uuid).lower()
        self._notify_callbacks[uuid_str] = callback
        logger.debug(f"[Mock] start_notify registrado para {uuid_str}")

        # Se for a notificação em tempo real do v2 (FFB2), inicia simulação de estabilização
        if self.protocol_version == "v2" and "ffb2" in uuid_str:
            if not self._simulation_task:
                self._simulation_task = asyncio.create_task(self._simulate_v2_measure())

    async def stop_notify(self, char_uuid):
        uuid_str = str(char_uuid).lower()
        if uuid_str in self._notify_callbacks:
            del self._notify_callbacks[uuid_str]
        logger.debug(f"[Mock] stop_notify para {uuid_str}")

    async def write_gatt_char(self, char_uuid, data, response=False):
        logger.debug(f"[Mock] Escreveu em {char_uuid}: {data.hex()}")
        # Em V1, enviar F2 00 aciona o dump de histórico
        if self.protocol_version == "v1" and data == bytes([0xF2, 0x00]):
            from ble.constants import CHIPSEA_NOTIFY_CHAR_UUID
            target_uuid = CHIPSEA_NOTIFY_CHAR_UUID
            if target_uuid in self._notify_callbacks:
                logger.info(f"[Mock] Simulando resposta de histórico V1...")
                # Envia um dado válido (o mesmo do test_protocol.py)
                resp_data = bytes.fromhex("671f0f1e3bf2e07a1200")
                self._notify_callbacks[target_uuid](1, resp_data)
                # Envia fim de blocos F2 00
                await asyncio.sleep(0.5)
                end_data = bytearray(10)
                end_data[0] = 0xF2
                end_data[1] = 0x00
                self._notify_callbacks[target_uuid](1, end_data)

    async def _simulate_v2_measure(self):
        from ble.constants import CHIPSEA_V2_BIA_CHAR_UUID, CHIPSEA_V2_WEIGHT_CHAR_UUID
        char_v2_weight = CHIPSEA_V2_WEIGHT_CHAR_UUID
        char_v2_bia = CHIPSEA_V2_BIA_CHAR_UUID

        target_raw = int(self.mock_weight * 100)
        
        logger.info("[Mock] Iniciando simulação de subida na balança...")
        
        # 1. Simula peso flutuando (3 segundos)
        for step in range(3, 0, -1):
            if not self.is_connected: return
            await asyncio.sleep(1)
            
            curr_raw = target_raw - (step * 50)  # Menor e subindo
            
            b6 = (curr_raw >> 16) & 0x03
            b7 = (curr_raw >> 8) & 0xFF
            b8 = curr_raw & 0xFF
            
            data = bytearray(10)
            data[4] = 0x01 # instável
            data[6] = b6
            data[7] = b7
            data[8] = b8
            
            if char_v2_weight in self._notify_callbacks:
                self._notify_callbacks[char_v2_weight](1, data)

        # 2. Peso estabilizado
        await asyncio.sleep(1)
        if not self.is_connected: return
        data = bytearray(10)
        data[4] = 0x02 # ESTÁVEL
        data[6] = (target_raw >> 16) & 0x03
        data[7] = (target_raw >> 8) & 0xFF
        data[8] = target_raw & 0xFF
        if char_v2_weight in self._notify_callbacks:
            self._notify_callbacks[char_v2_weight](1, data)
        logger.info("[Mock] Peso estabilizado!")

        # 3. Cálculo de BIA final (Indication)
        await asyncio.sleep(2)
        if not self.is_connected: return
        data_bia = bytearray(10)
        data_bia[3] = 0xA3 # Indicador de final
        data_bia[5] = (target_raw >> 16) & 0x03
        data_bia[6] = (target_raw >> 8) & 0xFF
        data_bia[7] = target_raw & 0xFF
        # Impedância = 500 => 0x01F4
        data_bia[8] = (self.mock_impedance >> 8) & 0xFF
        data_bia[9] = self.mock_impedance & 0xFF
        
        if char_v2_bia in self._notify_callbacks:
            self._notify_callbacks[char_v2_bia](1, data_bia)
            logger.info("[Mock] BIA concluída!")

class MockBleakScanner:
    """Mock para descobrir a balança virtual."""
    @classmethod
    async def discover(cls, timeout=5.0, return_adv=False):
        await asyncio.sleep(1) # Simula scan
        
        class MockDevice:
            address = "00:11:22:33:44:55"
            name = "Chipsea-BLE"
            rssi = -55
            metadata = {
                "uuids": ["0000ffb0-0000-1000-8000-00805f9b34fb"]
            }
            
        if return_adv:
            return {MockDevice.address: (MockDevice(), MockDevice())}
        return [MockDevice()]
