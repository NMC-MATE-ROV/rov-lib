"""A tiny async websocket client to send JSON commands to HydroWire devices."""
import asyncio
import json
from typing import Optional, Any, Dict

import websockets


class WebSocketCommandClient:
    """Async context-manager websocket client that sends/receives JSON commands.

    Example:
        async with WebSocketCommandClient("ws://host:port") as client:
            await client.send_command(
                device_id="led",
                command={"action": "pwm", "duty_cycle": 0.5}
            )
            # Sends: {"device": "led", "cmd": "pwm", "params": {"duty_cycle": 0.5}}
    """

    def __init__(self, uri: str, timeout: float = 10.0):
        self.uri = uri
        self.timeout = timeout
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self) -> None:
        while self._ws is None:
            try:
                self._ws = await websockets.connect(self.uri)
            except Exception as e:
                print("websocket does not exist, ensure device is connected to network")
                print("Waiting 5 seconds before reattempting connection")
                await asyncio.sleep(5)

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def send_command(
        self,
        device_id: str,
        command: Dict[str, Any],
        expect_response: bool = False
    ) -> Optional[dict]:
        """Send a JSON command to a specific device over the websocket.

        Args:
            device_id: The ID of the target device on HydroWire
            command: The command dictionary to send (must contain "action" key)
            expect_response: If True, waits for one JSON response and returns it

        Returns:
            Response dictionary if expect_response=True, otherwise None

        Note:
            Command structure groups parameters under "params" key:
            Input:  {"action": "pwm", "duty_cycle": 0.5, "enable": true}
            Sent:   {"device": "led", "cmd": "pwm", "params": {"duty_cycle": 0.5, "enable": true}}
        """
        if self._ws is None:
            await self.connect()

        # Extract action as cmd and collect parameters
        action = command.get("action", "unknown")
        # Build parameter dict with all command parameters except "action"
        params = {k: v for k, v in command.items() if k != "action"}

        # Build payload with device, cmd, and params
        payload = {
            "device": device_id,
            "cmd": action,
            "params": params
        }

        await self._ws.send(json.dumps(payload))
        if expect_response:
            data = await asyncio.wait_for(self._ws.recv(), timeout=self.timeout)
            return json.loads(data)
        return None

