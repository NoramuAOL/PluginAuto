"""
Minecraft Plugin Downloader
PyQt6 tabanlı Spigot ve Modrinth plugin indirici
"""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft Plugin Downloader")
    app.setApplicationVersion("1.0.0")
    
    # Async event loop entegrasyonu (qasync)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()
    
    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    main()