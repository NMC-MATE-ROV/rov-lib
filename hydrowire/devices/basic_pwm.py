from ..manager import HydroWireManager
class PWM:
    """
        Basic pwm interface for rov components
        Log level 0 = no logging
        Log level 1 = only error logging (Default)
        Log level 2 = log all action responses
    """

    def __init__(self, name: str, manager: HydroWireManager, log_level: int = 1):
        self.name = name
        self.manager = manager
        self.log_level = log_level

    async def set_pwm(self, duty_cycle: float):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "pwm", 
                    "duty_cycle": duty_cycle
                },
                expect_response=(self.log_level is not 0)
        )
        if (self.log_level is 1) or (self.log_level is 2):
            # TODO: Add logging functionality
            return

    async def set_pwm_frequency(self, duty_cycle: float, frequency: float):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "pwm_frequency", 
                    "duty_cycle": duty_cycle,
                    "frequency": frequency
                },
                expect_response=(self.log_level is not 0)
        )
        if (self.log_level is 1) or (self.log_level is 2):
            # TODO: Add logging functionality
            return

    async def get_state(self):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "get_state",
                },
                expect_response=true
        )
        return response
