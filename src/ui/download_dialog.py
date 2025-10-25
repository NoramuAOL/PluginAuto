"""
Plugin indirme dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QComboBox, QFileDialog,
                            QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import asyncio
import os

from ..api.modrinth_api import ModrinthAPI
from ..api.spigot_api import SpigotAPI

class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, api_type, plugin, version, download_path):
        super().__init__()
        self.api_type = api_type
        self.plugin = plugin
        self.version = version
        self.download_path = download_path
        
    def run(self):
        try:
            # Windows için event loop policy ayarla
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            api = None
            try:
                if self.api_type == "Modrinth":
                    api = ModrinthAPI()
                    # Modrinth için download URL'i version'dan al
                    download_url = self.version.get('files', [{}])[0].get('url')
                    if download_url:
                        success = loop.run_until_complete(
                            api.download_plugin(download_url, self.download_path, self.update_progress)
                        )
                    else:
                        success = False
                else:  # Spigot
                    api = SpigotAPI()
                    plugin_id = self.plugin.get('id')
                    version_id = self.version.get('id')
                    success = loop.run_until_complete(
                        api.download_plugin(plugin_id, version_id, self.download_path, self.update_progress)
                    )
                
                self.download_finished.emit(success, self.download_path)
                
            finally:
                # API session'ını kapat
                if api:
                    try:
                        loop.run_until_complete(api.close_aio_session())
                    except:
                        pass
                
                # Loop'u güvenli şekilde kapat
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except:
                    pass
                finally:
                    loop.close()
                    
        except Exception as e:
            print(f"Download worker hatası: {e}")
            self.download_finished.emit(False, str(e))
    
    def update_progress(self, progress):
        self.progress_updated.emit(progress)

class DownloadDialog(QDialog):
    def __init__(self, plugin, api_type, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.api_type = api_type
        self.versions = []
        self.download_manager = None
        self.init_ui()
        self.load_versions()
    
    def set_download_manager(self, download_manager):
        """Download manager referansını ayarla"""
        self.download_manager = download_manager
        
    def init_ui(self):
        self.setWindowTitle("Plugin İndir")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Plugin bilgileri
        if self.api_type == "Modrinth":
            plugin_name = self.plugin.get('title', 'N/A')
            plugin_desc = self.plugin.get('description', 'N/A')
        else:
            plugin_name = self.plugin.get('name', 'N/A')
            plugin_desc = self.plugin.get('tag', 'N/A')
        
        layout.addWidget(QLabel(f"Plugin: {plugin_name}"))
        
        desc_text = QTextEdit()
        desc_text.setPlainText(plugin_desc)
        desc_text.setMaximumHeight(100)
        desc_text.setReadOnly(True)
        layout.addWidget(desc_text)
        
        # Versiyon seçimi
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Versiyon:"))
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(300)
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)
        
        # İndirme yolu
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("İndirme Yolu:"))
        self.path_input = QLabel("plugins/")
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Gözat")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("İndir")
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_versions(self):
        try:
            if self.api_type == "Modrinth":
                api = ModrinthAPI()
                plugin_id = self.plugin.get('project_id') or self.plugin.get('slug')
                self.versions = api.get_plugin_versions(plugin_id, limit=200)
            else:
                api = SpigotAPI()
                plugin_id = self.plugin.get('id')
                self.versions = api.get_plugin_versions(plugin_id)
            
            # Combo box'ı doldur
            for version in self.versions:
                if self.api_type == "Modrinth":
                    version_name = version.get('version_number', 'N/A')
                    game_versions = version.get('game_versions', [])
                    if game_versions:
                        display_name = f"{version_name} (MC: {', '.join(game_versions)})"
                    else:
                        display_name = version_name
                else:
                    version_name = version.get('name', 'N/A')
                    # Spigot için MC sürüm bilgisi genelde yok, sadece versiyon adı
                    display_name = version_name
                
                self.version_combo.addItem(display_name, version)
                
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Versiyonlar yüklenemedi: {e}")
    
    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "İndirme Klasörü Seç")
        if folder:
            self.path_input.setText(folder)
    
    def start_download(self):
        if not self.versions:
            QMessageBox.warning(self, "Uyarı", "Versiyon bulunamadı!")
            return
            
        selected_version = self.version_combo.currentData()
        if not selected_version:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir versiyon seçin!")
            return
        
        # Dosya adını oluştur
        if self.api_type == "Modrinth":
            plugin_name = self.plugin.get('title', 'plugin')
            file_name = selected_version.get('files', [{}])[0].get('filename', f"{plugin_name}.jar")
        else:
            plugin_name = self.plugin.get('name', 'plugin')
            file_name = f"{plugin_name}.jar"
        
        download_path = os.path.join(self.path_input.text(), file_name)
        
        # İndirme klasörünü oluştur
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        # UI'yi güncelle
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Worker thread başlat
        self.download_worker = DownloadWorker(
            self.api_type, self.plugin, selected_version, download_path
        )
        self.download_worker.progress_updated.connect(self.progress_bar.setValue)
        self.download_worker.download_finished.connect(self.download_completed)
        self.download_worker.start()
    
    def download_completed(self, success, message):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        
        if success:
            # İndirme kaydını ekle
            if self.download_manager:
                if self.api_type == "Modrinth":
                    plugin_name = self.plugin.get('title', 'N/A')
                else:
                    plugin_name = self.plugin.get('name', 'N/A')
                
                selected_version = self.version_combo.currentData()
                if self.api_type == "Modrinth":
                    version_name = selected_version.get('version_number', 'N/A')
                else:
                    version_name = selected_version.get('name', 'N/A')
                
                self.download_manager.add_download(
                    plugin_name, 
                    version_name, 
                    self.api_type, 
                    message
                )
            
            QMessageBox.information(self, "Başarılı", f"Plugin başarıyla indirildi:\n{message}")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", f"İndirme başarısız:\n{message}")