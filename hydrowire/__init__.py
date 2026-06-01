"""hydrowire package - HydroWire communication and control library"""

__all__ = ["WebSocketCommandClient", "HydroWireManager", "start", "get_manager", "PWM", "LED"]
__version__ = "0.0.10"

from .client import WebSocketCommandClient
from .manager import HydroWireManager, start, get_manager
from .devices.basic_pwm import PWM
from .devices.led import LED
