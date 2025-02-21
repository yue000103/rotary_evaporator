class RobotDriver:
    def __init__(self, config):
        self._load_config(config['robot'])
        
    async def execute(self, command: str) -> dict:
        """异步执行指令"""
        try:
            async with timeout(self.timeout):
                return await self._send_hardware_command(command)
        except HardwareError as e:
            self._trigger_emergency_stop()
            raise DeviceControlError(f"Robot failed: {str(e)}")