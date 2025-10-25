"""
Çoklu yeniden indirme dialog penceresi
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

class RedownloadWorker(QThread):
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
                        success = loop.run_until_complete(self.redownload_single_item(item, row))
                        completed += 1
                        
                        plugin_name = item.get('name', 'Unknown')
                        self.download_finished.emit(success, plugin_name, row)
                        self.progress_updated.emit(completed, total_items)
                    except Exception as e:
                        print(f"Öğe yeniden indirme hatası: {e}")
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
            print(f"Redownload worker thread hatası: {e}")
            self.download_finished.emit(False, str(e), -1)
    
    async def redownload_single_item(self, item, row):
        try:
            if self.cancelled:
                return False
                
            plugin_name = item.get('name', '')
            api_type = item.get('api', 'Modrinth')
            selected_version = item.get('selected_version')
            
            def progress_callback(progress):
                if not self.cancelled:
                    self.item_progress_updated.emit(row, progress)
            
            # Dosya adını oluştur
            if selected_version:
                if api_type == "Modrinth":
                    file_name = selected_version.get('files', [{}])[0].get('filename', f"{plugin_name}.jar")
                else:
                    file_name = f"{plugin_name}.jar"
            else:
                file_name = f"{plugin_name}.jar"
            
            download_path = os.path.join(self.download_folder, file_name)
            
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            api = None
            spigot_api = None
            try:
                if api_type == "Modrinth" and selected_version:
                    api = ModrinthAPI()
                    download_url = selected_version.get('files', [{}])[0].get('url')
                    if download_url:
                        success = await api.download_plugin(download_url, download_path, progress_callback)
                    else:
                        success = False
                elif api_type == "Spigot" and selected_version:
                    api = SpigotAPI()
                    # Spigot için plugin ID'sini bul
                    spigot_api = SpigotAPI()
                    search_results = spigot_api.search_plugins(plugin_name, size=5)
                    if search_results:
                        plugin_id = search_results[0].get('id')
                        version_id = selected_version.get('id')
                        success = await api.download_plugin(plugin_id, version_id, download_path, progress_callback)
                    else:
                        success = False
                else:
                    success = False
                
                return success
            finally:
                # API session'larını kapat
                if api:
                    try:
                        await api.close_aio_session()
                    except:
                        pass
                if spigot_api:
                    try:
                        await spigot_api.close_aio_session()
                    except:
                        pass
            
        except asyncio.CancelledError:
            print("Yeniden indirme iptal edildi")
            return False
        except Exception as e:
            print(f"Yeniden indirme hatası: {e}")
            return False
    
    def cancel(self):
        self.cancelled = True

class RedownloadDialog(QDialog):
    def __init__(self, download_records, parent=None):
        super().__init__(parent)
        self.download_records = download_records
        self.download_manager = None
        self.download_worker = None
        self.plugin_versions = {}  # Plugin sürümlerini sakla
        self.init_ui()
        self.load_plugin_versions()
        
    def init_ui(self):
        self.setWindowTitle("Çoklu Yeniden İndirme")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Başlık
        layout.addWidget(QLabel(f"Yeniden indirilecek {len(self.download_records)} plugin:"))
        
        # Plugin tablosu
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(6)
        self.plugins_table.setHorizontalHeaderLabels([
            "Seç", "Plugin Adı", "Mevcut Sürüm", "Yeni Sürüm", "API", "Durum"
        ])
        
        # Tablo ayarları
        header = self.plugins_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        
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
        
        self.download_btn = QPushButton("Yeniden İndirmeyi Başlat")
        self.download_btn.clicked.connect(self.start_redownloads)
        button_layout.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.cancel_downloads)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def populate_table(self):
        """Tabloyu plugin verileri ile doldur"""
        self.plugins_table.setRowCount(len(self.download_records))
        
        for row, record in enumerate(self.download_records):
            # Seçim checkbox'ı
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.plugins_table.setCellWidget(row, 0, checkbox)
            
            # Plugin adı
            name = record.get('name', 'N/A')
            self.plugins_table.setItem(row, 1, QTableWidgetItem(name))
            
            # Mevcut sürüm
            current_version = record.get('version', 'N/A')
            self.plugins_table.setItem(row, 2, QTableWidgetItem(current_version))
            
            # Yeni sürüm seçimi (başlangıçta boş)
            version_combo = QComboBox()
            version_combo.addItem("Yükleniyor...", None)
            self.plugins_table.setCellWidget(row, 3, version_combo)
            
            # API
            api_type = record.get('api', 'N/A')
            self.plugins_table.setItem(row, 4, QTableWidgetItem(api_type))
            
            # Durum
            self.plugins_table.setItem(row, 5, QTableWidgetItem("Bekliyor"))
    
    def load_plugin_versions(self):
        """Tüm pluginler için sürümleri yükle"""
        for row, record in enumerate(self.download_records):
            try:
                plugin_name = record.get('name', '')
                api_type = record.get('api', 'Modrinth')
                
                if api_type == "Modrinth":
                    # Modrinth'te plugin ara
                    api = ModrinthAPI()
                    search_results = api.search_plugins(plugin_name, limit=5)
                    if search_results:
                        plugin = search_results[0]
                        plugin_id = plugin.get('project_id') or plugin.get('slug')
                        versions = api.get_plugin_versions(plugin_id, limit=200)
                        self.update_version_combo(row, versions, api_type)
                else:
                    # Spigot'ta plugin ara
                    api = SpigotAPI()
                    search_results = api.search_plugins(plugin_name, size=5)
                    if search_results:
                        plugin = search_results[0]
                        plugin_id = plugin.get('id')
                        versions = api.get_plugin_versions(plugin_id, size=20)
                        self.update_version_combo(row, versions, api_type)
                        
            except Exception as e:
                print(f"Sürüm yükleme hatası ({plugin_name}): {e}")
                self.update_version_combo(row, [], api_type)
    
    def update_version_combo(self, row, versions, api_type):
        """Sürüm combo'sunu güncelle"""
        version_combo = self.plugins_table.cellWidget(row, 3)
        version_combo.clear()
        
        if versions:
            for version in versions:
                if api_type == "Modrinth":
                    version_name = version.get('version_number', 'N/A')
                    game_versions = version.get('game_versions', [])
                    if game_versions:
                        display_name = f"{version_name} (MC: {', '.join(game_versions[-2:])})"
                    else:
                        display_name = version_name
                else:
                    version_name = version.get('name', 'N/A')
                    display_name = version_name
                
                version_combo.addItem(display_name, version)
            
            # İlk sürümü seç
            version_combo.setCurrentIndex(0)
        else:
            version_combo.addItem("Sürüm bulunamadı", None)
    
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
    
    def start_redownloads(self):
        """Yeniden indirmeleri başlat"""
        # Seçili pluginleri al
        selected_items = []
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox.isChecked():
                # Seçilen sürümü al
                version_combo = self.plugins_table.cellWidget(row, 3)
                selected_version = version_combo.currentData()
                
                if selected_version:
                    # Orijinal record'u kopyala ve sürümü ekle
                    item_data = self.download_records[row].copy()
                    item_data['selected_version'] = selected_version
                    selected_items.append(item_data)
        
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir plugin seçin!")
            return
        
        # UI'yi güncelle
        self.download_btn.setEnabled(False)
        self.overall_progress.setMaximum(len(selected_items))
        self.overall_progress.setValue(0)
        
        # Durum güncelle
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox.isChecked():
                self.plugins_table.setItem(row, 5, QTableWidgetItem("İndiriliyor"))
        
        # Worker thread başlat
        self.download_worker = RedownloadWorker(selected_items, self.folder_input.text())
        self.download_worker.progress_updated.connect(self.update_overall_progress)
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
    
    def item_download_finished(self, success, name, row):
        """Öğe indirme tamamlandı"""
        if success:
            self.plugins_table.setItem(row, 5, QTableWidgetItem("Tamamlandı"))
            
            # İndirme kaydını ekle
            if self.download_manager and row < len(self.download_records):
                record = self.download_records[row]
                version_combo = self.plugins_table.cellWidget(row, 3)
                selected_version = version_combo.currentData()
                
                if selected_version:
                    api_type = record.get('api', 'N/A')
                    plugin_name = record.get('name', 'N/A')
                    
                    if api_type == "Modrinth":
                        version_name = selected_version.get('version_number', 'N/A')
                    else:
                        version_name = selected_version.get('name', 'N/A')
                    
                    file_path = os.path.join(self.folder_input.text(), f"{plugin_name}.jar")
                    self.download_manager.add_download(plugin_name, version_name, api_type, file_path)
        else:
            self.plugins_table.setItem(row, 5, QTableWidgetItem("Başarısız"))
    
    def all_downloads_finished(self):
        """Tüm indirmeler tamamlandı"""
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Tamamlandı")
        QMessageBox.information(self, "Tamamlandı", "Tüm yeniden indirmeler tamamlandı!")
    
    def set_download_manager(self, download_manager):
        """Download manager referansını ayarla"""
        self.download_manager = download_manager