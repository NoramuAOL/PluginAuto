"""
Ana pencere UI
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QLabel, QLineEdit, QPushButton, 
                            QTableWidget, QTableWidgetItem, QProgressBar,
                            QFileDialog, QMessageBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from .plugin_search_tab import PluginSearchTab
from .download_manager_tab import DownloadManagerTab
from .settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Global ikon cache sistemi
        self.icon_cache = {}  # URL -> QPixmap mapping
        # API instance'larını takip et (session cleanup için)
        self._api_instances = []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Minecraft Plugin Downloader")
        self.setGeometry(100, 100, 1000, 700)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        layout = QVBoxLayout(central_widget)
        

        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Tabları oluştur
        self.search_tab = PluginSearchTab()
        self.download_tab = DownloadManagerTab()
        self.settings_tab = SettingsTab()
        
        # Plugin Listeleri sekmesini import et ve oluştur
        from .plugin_lists_tab import PluginListsTab
        self.lists_tab = PluginListsTab()
        
        # Search tab'a download manager referansını ver
        self.search_tab.set_download_manager(self.download_tab)
        # Download manager'a search tab referansını ver
        self.download_tab.set_search_tab(self.search_tab)
        # Search tab'a lists tab referansını ver
        self.search_tab.set_lists_tab(self.lists_tab)
        # Lists tab'a download manager referansını ver
        self.lists_tab.set_download_manager(self.download_tab)
        
        # Tüm sekmeler için ikon cache referansını ver
        self.search_tab.set_icon_cache(self.icon_cache)
        self.download_tab.set_icon_cache(self.icon_cache)
        self.lists_tab.set_icon_cache(self.icon_cache)
        
        # Tabları ekle
        self.tab_widget.addTab(self.search_tab, "Plugin Arama")
        self.tab_widget.addTab(self.lists_tab, "Plugin Listeleri")
        self.tab_widget.addTab(self.download_tab, "İndirme Yöneticisi")
        self.tab_widget.addTab(self.settings_tab, "Ayarlar")
        
        layout.addWidget(self.tab_widget)
        
        # Durum çubuğu
        self.statusBar().showMessage("Hazır")
        
        # İndirme geçmişini yükle
        self.download_tab.load_downloads()
        
        # Cache istatistiklerini göster
        self.update_cache_stats()
    
    def update_cache_stats(self):
        """Cache istatistiklerini güncelle"""
        cache_count = len(self.icon_cache)
        if cache_count > 0:
            self.statusBar().showMessage(f"Hazır - {cache_count} ikon cache'de")
        else:
            self.statusBar().showMessage("Hazır")
    
    def clear_icon_cache(self):
        """İkon cache'ini temizle"""
        self.icon_cache.clear()
        self.update_cache_stats()
    
    def closeEvent(self, event):
        """Pencere kapatılırken temizlik yap"""
        import asyncio
        
        # Worker thread'leri temizle
        if hasattr(self.search_tab, 'cleanup_worker'):
            try:
                self.search_tab.cleanup_worker()
            except:
                pass
        
        # İkon worker'larını temizle
        if hasattr(self.search_tab, 'icon_workers'):
            for worker in list(self.search_tab.icon_workers.values()):
                try:
                    if worker.isRunning():
                        worker.quit()
                        worker.wait(1000)
                except:
                    pass
        
        # Async session'ları kapat
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Event loop çalışıyorsa, task olarak ekle
                for api_instance in self._api_instances:
                    if hasattr(api_instance, 'close_aio_session'):
                        loop.create_task(api_instance.close_aio_session())
            else:
                # Event loop çalışmıyorsa, direkt çalıştır
                for api_instance in self._api_instances:
                    if hasattr(api_instance, 'close_aio_session'):
                        loop.run_until_complete(api_instance.close_aio_session())
        except:
            pass
        
        event.accept()