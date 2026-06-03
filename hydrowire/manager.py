"""HydroWire Manager - Main entry point for library initialization and control."""
import asyncio
import inspect
from typing import Optional, Dict, Any, Callable
from .client import WebSocketCommandClient


def _process_run_callable(callable_obj, kwargs):
    """Helper run in child process to execute GUI callable (coroutine or regular)."""
    import asyncio as _asyncio, inspect as _inspect
    try:
        if _inspect.iscoroutinefunction(callable_obj):
            _asyncio.run(callable_obj(**kwargs))
        else:
            callable_obj(**kwargs)
    except Exception as e:
        print(f"GUI process raised: {e}")


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
        # capture the event loop this manager runs on so other threads (e.g., GUI threads)
        # can schedule manager coroutines back onto this loop safely.
        self._loop = asyncio.get_running_loop()
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
        # Ensure module-level convenience getter returns this instance when
        # an instance's start() is used directly (not via the module-level start()).
        global _manager
        _manager = self

        await self.initialize()
        if gui_enabled:
            await self._start_gui(gui_callable=gui_callable, gui_stop_callable=gui_stop_callable, **gui_config)

    async def _start_gui(self, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **config) -> None:
        """Start GUI in a separate process so it doesn't interfere with the asyncio loop.

        Qt requires GUI objects to live in a single native thread (typically the
        process's main thread). Creating QApplication inside a background thread
        can cause undefined behavior and crashes. Running the GUI in a child
        process isolates it and prevents segmentation faults on shutdown.

        Stores references to the process and a stop callable to allow graceful
        shutdown in close().
        """
        import multiprocessing, inspect, functools, signal, time

        stop_callable = gui_stop_callable

        if gui_callable is None:
            try:
                from .gui.basic_gui import run_basic_gui
                gui_callable = run_basic_gui
                # No safe cross-process stop function available by default
                stop_callable = None
            except Exception as e:
                print(f"Unable to import basic GUI: {e}. Skipping GUI startup.")
                return

        # Run the GUI callable in a separate process so QApplication is created
        # in that process's main thread (avoids Qt crash on shutdown).
        # Pass the manager URI into the child's kwargs so the GUI process can
        # connect directly when the manager object isn't available across processes.
        new_config = dict(config or {})
        new_config.setdefault("manager_uri", getattr(self, "uri", None))
        proc = multiprocessing.Process(target=_process_run_callable, args=(gui_callable, new_config), daemon=True)
        proc.start()

        # Provide a stop callable that attempts graceful termination of the child
        # process. This is process-local; it cannot call functions inside the
        # child, but it's a reasonable fallback when no explicit cross-process
        # stop callable is provided.
        def _stop_proc():
            try:
                if not proc.is_alive():
                    return True
                # Try a gentle terminate first
                proc.terminate()
                # Give it a short moment to exit
                proc.join(2)
                return not proc.is_alive()
            except Exception:
                return False

        self._gui_process = proc
        # prefer user-provided stop callable if it exists and we're running in same process
        self._gui_stop_callable = stop_callable or _stop_proc

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
        try:
            if hasattr(self, "_gui_stop_callable") and self._gui_stop_callable:
                stopped = False
                try:
                    result = self._gui_stop_callable()
                    # If the callable returned an awaitable (async function), await it
                    if asyncio.iscoroutine(result) or hasattr(result, "__await__"):
                        try:
                            await result
                            stopped = True
                        except Exception:
                            stopped = False
                    else:
                        try:
                            stopped = bool(result)
                        except Exception:
                            stopped = False
                except Exception:
                    # If calling the stop callable raised, attempt to await it in case it's async
                    try:
                        await self._gui_stop_callable()
                        stopped = True
                    except Exception:
                        stopped = False

                # If a child process was used for the GUI, join it
                if hasattr(self, "_gui_process") and self._gui_process is not None:
                    try:
                        await asyncio.to_thread(self._gui_process.join, 5)
                    except Exception as e:
                        print(f"Error joining GUI process: {e}")
            # If we have a GUI process but no stop callable, try joining it directly
            elif hasattr(self, "_gui_process") and self._gui_process is not None:
                try:
                    await asyncio.to_thread(self._gui_process.join, 5)
                except Exception as e:
                    print(f"Error joining GUI process: {e}")
        except Exception as e:
            print(f"Error while stopping GUI: {e}")

        if self.client:
            await self.client.close()
        self._running = False
        print("HydroWire Manager closed")

    async def get_system_stats(self) -> Dict[str, Any]:
        """Retrieve system stats.

        If called from a different event loop (for example, a GUI running in a
        separate thread), schedule the underlying send_command coroutine on the
        manager's original loop to avoid "Future attached to a different loop"
        errors from objects (like websocket transports) tied to that loop.
        """
        coro = self.send_command(
            device_id="system",
            command={"action": "get_info"},
            expect_response=True,
        )

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in caller; just await the coroutine (will use manager loop)
            return await coro

        mgr_loop = getattr(self, "_loop", None)
        # If manager loop is unknown or caller is running on the same loop, await directly
        if mgr_loop is None or mgr_loop is current_loop:
            return await coro

        # Schedule coroutine on the manager's loop and await the concurrent future
        cfut = asyncio.run_coroutine_threadsafe(coro, mgr_loop)
        return await asyncio.wrap_future(cfut, loop=current_loop)


_manager: Optional[HydroWireManager] = None


async def start(uri: str, gui_enabled: bool = False, gui_callable: Optional[Callable] = None, gui_stop_callable: Optional[Callable] = None, **gui_config) -> HydroWireManager:
    global _manager
    _manager = HydroWireManager(uri)
    await _manager.start(gui_enabled=gui_enabled, gui_callable=gui_callable, gui_stop_callable=gui_stop_callable, **gui_config)
    return _manager


async def get_manager() -> Optional[HydroWireManager]:
    return _manager
