from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

def run_basic_gui(**config):
    """
    Launch a minimal Qt window with 'Hello World' centered.
    If a QApplication exists, it will reuse it and not call exec().
    """
    app = QApplication.instance()
    own_app = app is None
    if own_app:
        app = QApplication([])

    window = QWidget()
    window.setWindowTitle("HydroWire Basic GUI")
    layout = QVBoxLayout(window)
    label = QLabel("Hello World")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    window.setLayout(layout)
    window.resize(300, 200)
    window.show()

    if own_app:
        return app.exec()
    return 0

def stop_basic_gui():
    """
    Close all top-level widgets created by QApplication.
    """
    app = QApplication.instance()
    if app is not None:
        if app:
            for w in app.topLevelWidgets():
                w.close()

if __name__ == "__main__":
    run_basic_gui()
