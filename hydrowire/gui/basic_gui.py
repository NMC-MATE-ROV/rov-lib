from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from typing import Dict, Any
from qasync import QEventLoop
from ..client import WebSocketCommandClient
import asyncio


def run_basic_gui(**config):
    """Run a very small GUI and refresh the displayed uptime periodically.

    Prefers qasync integration when available so asyncio coroutines run
    inside the Qt event loop. If qasync is not installed, falls back to a
    simple approach that opens a fresh asyncio loop for each update tick.
    """

    app = QApplication.instance()
    own_app = app is None
    if own_app:
        app = QApplication([])

    manager_uri = config.get("manager_uri") or config.get("uri")
    interval = int(config.get("interval_ms", 200))

    async def async_main():
        client = WebSocketCommandClient(manager_uri)

        async def get_stats():
            return await client.send_command(device_id="system", command={"action": "get_info"}, expect_response=True)

        try:
            stats = await get_stats()
            heartbeat = stats.get("uptime_seconds", "N/A") if isinstance(stats, dict) else "N/A"
        except Exception:
            heartbeat = "N/A"

        window = QWidget()
        window.setWindowTitle("HydroWire Basic GUI")
        layout = QVBoxLayout(window)
        label = QLabel(f"{heartbeat}")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        window.setLayout(layout)
        window.resize(300, 200)
        window.show()

        async def updater():
            while True:
                try:
                    stats = await get_stats()
                    hb = stats.get("uptime_seconds", "N/A") if isinstance(stats, dict) else "N/A"
                    label.setText(f"{hb}")
                except Exception as e:
                    print(f"GUI update error: {e}")
                await asyncio.sleep(interval / 1000.0)

        task = asyncio.create_task(updater())

        # Wait until the QApplication is about to quit
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def _on_quit():
            if not future.done():
                future.set_result(None)

        app.aboutToQuit.connect(_on_quit)

        try:
            await future
        finally:
            task.cancel()
            try:
                await task
            except Exception:
                pass
            try:
                await client.close()
            except Exception:
                pass

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(async_main())


def stop_basic_gui():
    app = QApplication.instance()
    if app is None:
        return False
    try:
        # Post a quit request to the application's thread so it exits cleanly.
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(app, "quit", Qt.QueuedConnection)
    except Exception:
        # Fallback: try to close top-level widgets and call quit directly.
        try:
            for w in app.topLevelWidgets():
                w.close()
            app.quit()
        except Exception:
            return False
    return True


if __name__ == "__main__":
    run_basic_gui()
