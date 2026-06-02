"""Example usage demonstrating how to use the rov-interface library."""

import asyncio
from time import sleep

from hydrowire import HydroWireManager as ROVManager
from hydrowire import LED


async def main():
    """Example of using the ROVManager as a library in your main app."""

    # Initialize the manager with ROV WebSocket address
    manager = ROVManager("ws://rov-pi:3000/ws")

    # Start the library (initialize communication)
    await manager.start(
            gui_enabled=True
    )

    try:
        # Example 1: Send command to LED device
        # response = await manager.send_command(
        #     device_id="led",
        #     command={"action": "pwm", "duty_cycle": 0.5},
        #     expect_response=True
        # )
        # print(f"Led response: {response}")
        #
        # response = await manager.send_command(
        #     device_id="led",
        #     command={"action": "get_state"},
        #     expect_response=True
        # )
        # print(f"Led status: {response}")
        #
        # sleep(2)
        #
        # print("Sending turn off command to LED")
        # response = await manager.send_command(
        #     device_id="led",
        #     command={"action": "pwm", "duty_cycle": 0.0},
        #     expect_response=True
        # )
        # print(f"Led response: {response}")
        # Sends: {"device": "led", "cmd": "pwm", "params": {"duty_cycle": 0.5}}
        while True:
            key = input()
            if key == 'q':
                break
            led = LED(
                    name="led",
                    manager=manager,
            )

            await led.toggle()

        # Example 2: Send command to camera
        # response = await manager.send_command(
        #     device_id="camera_main",
        #     command={"action": "capture", "resolution": "4k"},
        #     expect_response=True
        # )
        # print(f"Camera response: {response}")
        # Sends: {"device": "camera_main", "cmd": "capture", "params": {"resolution": "4k"}}

        # Example 3: Send fire-and-forget command (no response expected)
        # await manager.send_command(
        #     device_id="lights",
        #     command={"action": "set_brightness", "level": 50}
        # )
        # print("Lights command sent")
        # Sends: {"device": "lights", "cmd": "set_brightness", "params": {"level": 50}}

    finally:
        # Always clean up
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())

