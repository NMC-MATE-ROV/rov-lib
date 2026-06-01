from typing import Optional, Dict, Any
from ..manager import HydroWireManager

class LED:
    """
        LED interface
        Log level 0 = no logging
        Log level 1 = only error logging (Default)
        Log level 2 = log all action responses
    """

    def __init__(self, name: str, manager: HydroWireManager, log_level: int = 1):
        self.name = name
        self.manager = manager
        self.log_level = log_level

    async def set_brightness(self, brightness: float):
        """
        Sets the brightness of the LED
        The brightness must be in the range 0-1
        """
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "pwm", 
                    "duty_cycle": brightness
                },
                expect_response=(self.log_level is not 0)
        )
        self.log(response)

    async def set_brightness_frequency(self, brightness: float, frequency: float):
        """
        Sets the brightness of the LED and the frequency in Hz
        """
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "pwm_frequency", 
                    "duty_cycle": brightness,
                    "frequency": frequency
                },
                expect_response=(self.log_level is not 0)
        )
        self.log(response)

    async def turn_on(self):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "turn_on",
                },
                expect_response=(self.log_level is not 0)
        )
        self.log(response)

    async def turn_off(self):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "turn_off",
                },
                expect_response=(self.log_level is not 0)
        )
        self.log(response)

    async def toggle(self):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "toggle",
                },
                expect_response=(self.log_level is not 0)
        )
        self.log(response)

    async def get_state(self):
        response = await self.manager.send_command(
                device_id=self.name, 
                command={
                    "action": "get_state",
                },
                expect_response=true
        )
        return response

    def log(self, loggable: Optional[Dict[str, Any]]):
        if loggable is not None:
             match self.log_level:
                case 0:
                    return
                case 1:
                    if loggable.get("error") is not None:
                        print(f"Error: {self.name}: {loggable.get('error')}")
                case 2:
                    print(f"{loggable}")
