import sys

from PySide6.QtWidgets import QApplication

from media_downloader.gui_main import GuiMain

if __name__ == "__main__":
    app = QApplication()
    gui_main = GuiMain()
    gui_main.show()
    sys.exit(app.exec())
