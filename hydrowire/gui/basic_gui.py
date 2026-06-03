from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from typing import Dict, Any
from ..manager import get_manager, HydroWireManager
import asyncio

async def run_basic_gui(**config):
    app = QApplication.instance()
    own_app = app is None
    if own_app:
        app = QApplication([])

    manager = await get_manager()

    stats = {}
    if manager is None:
        # Manager not available in this process (GUI likely running in child process).
        # If a manager URI was provided in config, create a temporary client to fetch stats.
        manager_uri = config.get("manager_uri") or config.get("uri")
        if manager_uri:
            try:
                from ..client import WebSocketCommandClient
                async with WebSocketCommandClient(manager_uri) as client:
                    stats = await client.send_command(device_id="system", command={"action": "get_info"}, expect_response=True)
            except Exception as e:
                print(f"Unable to contact manager at {manager_uri}: {e}")
                stats = {}
        else:
            print("manager does not exist and no manager_uri provided")
            stats = {}
    else:
        # manager is in same process; run coroutine to get stats in this thread's event loop
        try:
            stats = await manager.get_system_stats()
        except Exception as e:
            print(f"Error obtaining system stats: {e}")
            stats = {}

    heartbeat = stats.get("uptime_seconds", "N/A") if isinstance(stats, dict) else "N/A"

    window = QWidget()
    window.setWindowTitle("HydroWire Basic GUI")
    layout = QVBoxLayout(window)
    label = QLabel(f"{heartbeat}")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    window.setLayout(layout)
    window.resize(300, 200)
    window.show()

    if own_app:
        return app.exec()
    return 0

def stop_basic_gui():
    app = QApplication.instance()
    if app is None:
        return False
    try:
        # Post a quit request to the application's thread so it exits cleanly.
        # Using QMetaObject.invokeMethod with QueuedConnection ensures the
        # call is executed in the GUI thread even when invoked from another
        # thread.
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
    import asyncio
    asyncio.run(run_basic_gui())
