"""HydroWire Manager - Main entry point for library initialization and control."""
import asyncio
from typing import Optional, Dict, Any, Callable
from .client import WebSocketCommandClient


class HydroWireManager:
    """Main manager class for HydroWire communication and application control.

    Handles WebSocket connection, command routing to devices,
    and integration with optional GUI components.
    """

    def __init__(self, uri: str, timeout: float = 10.0):
        """Initialize HydroWire Manager.

        Args:
            uri: WebSocket URI for devices (e.g., "ws://localhost:8000")
            timeout: Command timeout in seconds
        """
        self.uri = uri
        self.timeout = timeout
        self.client: Optional[WebSocketCommandClient] = None
        self._running = False
        self._gui_app = None
        self._command_handlers: Dict[str, Callable] = {}

    async def initialize(self) -> None:
        """Initialize connection to devices."""
        self.client = WebSocketCommandClient(self.uri, timeout=self.timeout)
        await self.client.connect()
        self._running = True
        print(f"HydroWire Manager initialized. Connected to {self.uri}")

    async def close(self) -> None:
        """Close connection."""
        if self.client:
            await self.client.close()
        self._running = False
        print("HydroWire Manager closed")

    async def send_command(
        self,
        device_id: str,
        command: Dict[str, Any],
        expect_response: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Send a command to a specific device.

        Args:
            device_id: Target device ID (e.g., "arm_1", "camera_main")
            command: Command dictionary with action and parameters
            expect_response: Whether to wait for response

        Returns:
            Response dict if expect_response=True, otherwise None
        """
        if not self._running or not self.client:
            raise RuntimeError("HydroWire Manager not initialized. Call initialize() first.")

        return await self.client.send_command(device_id, command, expect_response)

    def register_command_handler(self, command_type: str, handler: Callable) -> None:
        """Register a handler for a specific command type."""
        self._command_handlers[command_type] = handler

    def attach_gui(self, gui_app: Any) -> None:
        """Attach a GUI application instance."""
        self._gui_app = gui_app
        print("GUI application attached to HydroWire Manager")

    async def start(self, gui_enabled: bool = False, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **gui_config) -> None:
        """Start the manager and optionally the GUI.

        If gui_enabled is True, a GUI will be started in a background thread. A
        custom gui_callable may be provided which should be a callable that
        blocks while the GUI is running (e.g., starts a Qt event loop). A
        corresponding gui_stop_callable may be provided to request graceful
        shutdown of the GUI. If gui_callable is None, the built-in
        hydrowire.gui.basic_gui.run_basic_gui is used and its stop function
        will be used automatically.
        """
        await self.initialize()
        if gui_enabled:
            await self._start_gui(gui_callable=gui_callable, gui_stop_callable=gui_stop_callable, **gui_config)

    async def _start_gui(self, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **config) -> None:
        """Start GUI in a background thread so it doesn't block asyncio loop.

        Stores references to the thread and stop callable to allow graceful
        shutdown in close().
        """
        import threading

        stop_callable = gui_stop_callable

        if gui_callable is None:
            try:
                from .gui.basic_gui import run_basic_gui, stop_basic_gui
                gui_callable = run_basic_gui
                stop_callable = stop_basic_gui
            except Exception as e:
                print(f"Unable to import basic GUI: {e}. Skipping GUI startup.")
                return

        def _runner():
            try:
                gui_callable(**config)
            except Exception as e:
                print(f"GUI exited with exception: {e}")

        thread = threading.Thread(target=_runner, daemon=False)
        thread.start()

        # store references for shutdown
        self._gui_thread = thread
        self._gui_stop_callable = stop_callable

    async def run(self, gui_enabled: bool = False, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **gui_config) -> None:
        try:
            await self.start(gui_enabled=gui_enabled, gui_callable=gui_callable, gui_stop_callable=gui_stop_callable, **gui_config)
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutdown signal received")
        finally:
            await self.close()

    async def close(self) -> None:
        """Close connection and attempt graceful GUI shutdown if present."""
        # Attempt to stop GUI first so app loop exits cleanly
        if hasattr(self, "_gui_stop_callable") and self._gui_stop_callable:
            try:
                stopped = False
                try:
                    stopped = self._gui_stop_callable()
                except TypeError:
                    # If stop callable is async or requires await, run it in event loop
                    try:
                        await self._gui_stop_callable()
                        stopped = True
                    except Exception:
                        stopped = False
                if stopped:
                    # join the thread (with timeout) to wait for it to exit
                    if hasattr(self, "_gui_thread") and self._gui_thread is not None:
                        try:
                            await asyncio.to_thread(self._gui_thread.join, 5)
                        except Exception as e:
                            print(f"Error joining GUI thread: {e}")
            except Exception as e:
                print(f"Error while stopping GUI: {e}")

        if self.client:
            await self.client.close()
        self._running = False
        print("HydroWire Manager closed")


_manager: Optional[HydroWireManager] = None


async def start(uri: str, gui_enabled: bool = False, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **gui_config) -> HydroWireManager:
    global _manager
    _manager = HydroWireManager(uri)
    await _manager.start(gui_enabled=gui_enabled, gui_callable=gui_callable, gui_stop_callable=gui_stop_callable, **gui_config)
    return _manager


async def get_manager() -> Optional[HydroWireManager]:
    return _manager

