"""
Çoklu plugin indirme dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QTableWidget, QTableWidgetItem,
                            QHeaderView, QCheckBox, QMessageBox, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import asyncio
import os
from datetime import datetime

from ..api.modrinth_api import ModrinthAPI
from ..api.spigot_api import SpigotAPI

class MultiDownloadWorker(QThread):
    progress_updated = pyqtSignal(int, int)  # current, total
    item_progress_updated = pyqtSignal(int, int)  # row, progress
    download_finished = pyqtSignal(bool, str, int)  # success, message, row
    all_finished = pyqtSignal()
    
    def __init__(self, download_items, download_folder):
        super().__init__()
        self.download_items = download_items
        self.download_folder = download_folder
        self.cancelled = False
        
    def run(self):
        try:
            # Windows için event loop policy ayarla
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                total_items = len(self.download_items)
                completed = 0
                
                for row, item in enumerate(self.download_items):
                    if self.cancelled:
                        break
                        
                    try:
                        success = loop.run_until_complete(self.download_single_item(item, row))
                        completed += 1
                        
                        plugin_name = item.get('plugin', {}).get('title') or item.get('plugin', {}).get('name', 'Unknown')
                        self.download_finished.emit(success, plugin_name, row)
                        self.progress_updated.emit(completed, total_items)
                    except Exception as e:
                        print(f"Öğe indirme hatası: {e}")
                        self.download_finished.emit(False, str(e), row)
                        completed += 1
                        self.progress_updated.emit(completed, total_items)
                
                self.all_finished.emit()
                
            finally:
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
            print(f"Worker thread hatası: {e}")
            self.download_finished.emit(False, str(e), -1)
    
    async def download_single_item(self, item, row):
        try:
            if self.cancelled:
                return False
                
            api_type = item['api']
            plugin = item['plugin']
            version = item['version']
            
            # Dosya adını oluştur
            if api_type == "Modrinth":
                plugin_name = plugin.get('title', 'plugin')
                file_name = version.get('files', [{}])[0].get('filename', f"{plugin_name}.jar")
            else:
                plugin_name = plugin.get('name', 'plugin')
                file_name = f"{plugin_name}.jar"
            
            download_path = os.path.join(self.download_folder, file_name)
            
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            def progress_callback(progress):
                if not self.cancelled:
                    self.item_progress_updated.emit(row, progress)
            
            api = None
            try:
                if api_type == "Modrinth":
                    api = ModrinthAPI()
                    download_url = version.get('files', [{}])[0].get('url')
                    if download_url:
                        success = await api.download_plugin(download_url, download_path, progress_callback)
                    else:
                        success = False
                else:  # Spigot
                    api = SpigotAPI()
                    plugin_id = plugin.get('id')
                    version_id = version.get('id')
                    success = await api.download_plugin(plugin_id, version_id, download_path, progress_callback)
                
                return success
            finally:
                # API session'ını kapat
                if api:
                    try:
                        await api.close_aio_session()
                    except:
                        pass
            
        except asyncio.CancelledError:
            print("İndirme iptal edildi")
            return False
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return False
    
    def cancel(self):
        self.cancelled = True

class MultiDownloadDialog(QDialog):
    def __init__(self, plugins_data, parent=None):
        super().__init__(parent)
        self.plugins_data = plugins_data
        self.download_manager = None
        self.download_worker = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Çoklu Plugin İndirme")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Başlık
        layout.addWidget(QLabel(f"İndirilecek {len(self.plugins_data)} plugin:"))
        
        # Plugin tablosu
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(6)
        self.plugins_table.setHorizontalHeaderLabels([
            "Seç", "Plugin Adı", "Sürüm", "API", "Durum", "İlerleme"
        ])
        
        # Tablo ayarları
        header = self.plugins_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.populate_table()
        layout.addWidget(self.plugins_table)
        
        # İndirme klasörü
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("İndirme Klasörü:"))
        
        self.folder_input = QLabel("plugins/")
        folder_layout.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Gözat")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        layout.addLayout(folder_layout)
        
        # Genel ilerleme
        self.overall_progress = QProgressBar()
        layout.addWidget(self.overall_progress)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tümünü Kaldır")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        
        self.download_btn = QPushButton("İndirmeyi Başlat")
        self.download_btn.clicked.connect(self.start_downloads)
        button_layout.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.cancel_downloads)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def populate_table(self):
        """Tabloyu plugin verileri ile doldur"""
        self.plugins_table.setRowCount(len(self.plugins_data))
        
        for row, plugin_data in enumerate(self.plugins_data):
            # Seçim checkbox'ı
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.plugins_table.setCellWidget(row, 0, checkbox)
            
            # Plugin adı
            if plugin_data['api'] == "Modrinth":
                name = plugin_data['plugin'].get('title', 'N/A')
            else:
                name = plugin_data['plugin'].get('name', 'N/A')
            
            self.plugins_table.setItem(row, 1, QTableWidgetItem(name))
            
            # Sürüm seçimi
            version_combo = QComboBox()
            self.load_versions_for_plugin(plugin_data, version_combo, row)
            self.plugins_table.setCellWidget(row, 2, version_combo)
            
            self.plugins_table.setItem(row, 3, QTableWidgetItem(plugin_data['api']))
            self.plugins_table.setItem(row, 4, QTableWidgetItem("Bekliyor"))
            
            # İlerleme çubuğu
            progress_bar = QProgressBar()
            progress_bar.setVisible(False)
            self.plugins_table.setCellWidget(row, 5, progress_bar)
    
    def browse_folder(self):
        """Klasör seç"""
        folder = QFileDialog.getExistingDirectory(self, "İndirme Klasörü Seç")
        if folder:
            self.folder_input.setText(folder)
    
    def select_all(self):
        """Tümünü seç"""
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            checkbox.setChecked(True)
    
    def deselect_all(self):
        """Tümünü kaldır"""
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            checkbox.setChecked(False)
    
    def start_downloads(self):
        """İndirmeleri başlat"""
        # Seçili pluginleri al
        selected_items = []
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox.isChecked():
                # Seçilen sürümü al
                version_combo = self.plugins_table.cellWidget(row, 2)
                selected_version = version_combo.currentData()
                
                if selected_version:
                    # Orijinal plugin data'sını kopyala ve sürümü güncelle
                    item_data = self.plugins_data[row].copy()
                    item_data['version'] = selected_version
                    selected_items.append(item_data)
        
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir plugin seçin!")
            return
        
        # UI'yi güncelle
        self.download_btn.setEnabled(False)
        self.overall_progress.setMaximum(len(selected_items))
        self.overall_progress.setValue(0)
        
        # Progress bar'ları göster
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox.isChecked():
                progress_bar = self.plugins_table.cellWidget(row, 5)
                progress_bar.setVisible(True)
                self.plugins_table.setItem(row, 4, QTableWidgetItem("İndiriliyor"))
        
        # Worker thread başlat
        self.download_worker = MultiDownloadWorker(selected_items, self.folder_input.text())
        self.download_worker.progress_updated.connect(self.update_overall_progress)
        self.download_worker.item_progress_updated.connect(self.update_item_progress)
        self.download_worker.download_finished.connect(self.item_download_finished)
        self.download_worker.all_finished.connect(self.all_downloads_finished)
        self.download_worker.start()
    
    def cancel_downloads(self):
        """İndirmeleri iptal et"""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait()
        self.reject()
    
    def update_overall_progress(self, current, total):
        """Genel ilerlemeyi güncelle"""
        self.overall_progress.setValue(current)
    
    def update_item_progress(self, row, progress):
        """Öğe ilerlemesini güncelle"""
        progress_bar = self.plugins_table.cellWidget(row, 4)
        if progress_bar:
            progress_bar.setValue(progress)
    
    def item_download_finished(self, success, name, row):
        """Öğe indirme tamamlandı"""
        if success:
            self.plugins_table.setItem(row, 4, QTableWidgetItem("Tamamlandı"))
            
            # İndirme kaydını ekle
            if self.download_manager and row < len(self.plugins_data):
                plugin_data = self.plugins_data[row]
                api_type = plugin_data['api']
                
                if api_type == "Modrinth":
                    plugin_name = plugin_data['plugin'].get('title', 'N/A')
                    version_name = plugin_data['version'].get('version_number', 'N/A')
                else:
                    plugin_name = plugin_data['plugin'].get('name', 'N/A')
                    version_name = plugin_data['version'].get('name', 'N/A')
                
                file_path = os.path.join(self.folder_input.text(), f"{plugin_name}.jar")
                self.download_manager.add_download(plugin_name, version_name, api_type, file_path)
        else:
            self.plugins_table.setItem(row, 4, QTableWidgetItem("Başarısız"))
    
    def all_downloads_finished(self):
        """Tüm indirmeler tamamlandı"""
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Tamamlandı")
        QMessageBox.information(self, "Tamamlandı", "Tüm indirmeler tamamlandı!")
    
    def set_download_manager(self, download_manager):
        """Download manager referansını ayarla"""
        self.download_manager = download_manager    

    def load_versions_for_plugin(self, plugin_data, version_combo, row):
        """Plugin için sürümleri yükle"""
        try:
            api_type = plugin_data['api']
            plugin = plugin_data['plugin']
            
            if api_type == "Modrinth":
                from ..api.modrinth_api import ModrinthAPI
                api = ModrinthAPI()
                plugin_id = plugin.get('project_id') or plugin.get('slug')
                versions = api.get_plugin_versions(plugin_id, limit=200)
                
                for version in versions[:10]:  # İlk 10 sürüm
                    version_name = version.get('version_number', 'N/A')
                    game_versions = version.get('game_versions', [])
                    if game_versions:
                        display_name = f"{version_name} (MC: {', '.join(game_versions[-2:])})"
                    else:
                        display_name = version_name
                    version_combo.addItem(display_name, version)
                    
            else:  # Spigot
                from ..api.spigot_api import SpigotAPI
                api = SpigotAPI()
                plugin_id = plugin.get('id')
                versions = api.get_plugin_versions(plugin_id)
                
                for version in versions[:10]:  # İlk 10 sürüm
                    version_name = version.get('name', 'N/A')
                    version_combo.addItem(version_name, version)
            
            # Varsayılan olarak ilk sürümü seç
            if version_combo.count() > 0:
                version_combo.setCurrentIndex(0)
            else:
                version_combo.addItem("Sürüm bulunamadı", None)
                
        except Exception as e:
            print(f"Sürüm yükleme hatası: {e}")
            version_combo.addItem("Hata", None)