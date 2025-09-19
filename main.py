"""
Minecraft Plugin Downloader
PyQt6 tabanlı Spigot ve Modrinth plugin indirici
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Minecraft Plugin Downloader")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()