"""
İndirme yöneticisi sekmesi
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QHeaderView, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
import os
import json

class DownloadManagerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.downloads_file = "downloads.json"
        self.search_tab = None
        self.active_downloads = {}  # Aktif indirmeler için
        self.icon_cache = None  # İkon cache referansı
        self.init_ui()
        self.load_downloads()
    
    def set_search_tab(self, search_tab):
        """Search tab referansını ayarla"""
        self.search_tab = search_tab
    
    def set_icon_cache(self, icon_cache):
        """İkon cache referansını ayarla"""
        self.icon_cache = icon_cache
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık ve butonlar
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("İndirilen Pluginler"))
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_downloads)
        header_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Geçmişi Temizle")
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Çoklu işlem butonları
        multi_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.clicked.connect(self.select_all_downloads)
        multi_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Seçimi Kaldır")
        deselect_all_btn.clicked.connect(self.deselect_all_downloads)
        multi_layout.addWidget(deselect_all_btn)
        
        multi_layout.addStretch()
        
        self.redownload_selected_btn = QPushButton("Seçilenleri Yeniden İndir")
        self.redownload_selected_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 6px 12px; }")
        self.redownload_selected_btn.clicked.connect(self.redownload_selected_plugins)
        self.redownload_selected_btn.setEnabled(False)
        multi_layout.addWidget(self.redownload_selected_btn)
        
        self.delete_selected_btn = QPushButton("Seçilenleri Sil")
        self.delete_selected_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 6px 12px; }")
        self.delete_selected_btn.clicked.connect(self.delete_selected_downloads)
        self.delete_selected_btn.setEnabled(False)
        multi_layout.addWidget(self.delete_selected_btn)
        
        layout.addLayout(multi_layout)
        
        # İndirme tablosu
        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(8)
        self.downloads_table.setHorizontalHeaderLabels([
            "Seç", "İkon", "Plugin Adı", "Versiyon", "API", "İndirme Tarihi", "Dosya Yolu", "Aksiyon"
        ])
        
        # Tablo ayarları
        header = self.downloads_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # İkon
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Plugin Adı
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Versiyon
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # API
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Tarih
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Dosya Yolu
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Aksiyon
        
        # Sütun genişlikleri
        self.downloads_table.setColumnWidth(0, 50)   # Seç
        self.downloads_table.setColumnWidth(1, 70)   # İkon
        self.downloads_table.setColumnWidth(2, 200)  # Plugin Adı
        self.downloads_table.setColumnWidth(3, 120)  # Versiyon
        self.downloads_table.setColumnWidth(4, 80)   # API
        self.downloads_table.setColumnWidth(5, 140)  # Tarih
        self.downloads_table.setColumnWidth(7, 200)  # Aksiyon
        
        # Satır yüksekliği
        self.downloads_table.verticalHeader().setDefaultSectionSize(60)
        
        layout.addWidget(self.downloads_table)
        
        # İstatistikler
        self.stats_label = QLabel("Toplam indirme: 0")
        layout.addWidget(self.stats_label)
        
    def load_downloads(self):
        """İndirme geçmişini yükle"""
        try:
            downloads = []
            if os.path.exists(self.downloads_file):
                try:
                    with open(self.downloads_file, 'r', encoding='utf-8') as f:
                        downloads = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    downloads = []
            
            self.downloads_table.setRowCount(len(downloads))
            
            for row, download in enumerate(downloads):
                # Seçim checkbox'ı
                from PyQt6.QtWidgets import QCheckBox
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(self.update_multi_buttons)
                self.downloads_table.setCellWidget(row, 0, checkbox)
                
                # İkon
                api_type = download.get('api', 'N/A')
                icon_label = self.create_api_icon(api_type)
                self.downloads_table.setCellWidget(row, 1, icon_label)
                
                self.downloads_table.setItem(row, 2, QTableWidgetItem(download.get('name', 'N/A')))
                self.downloads_table.setItem(row, 3, QTableWidgetItem(download.get('version', 'N/A')))
                self.downloads_table.setItem(row, 4, QTableWidgetItem(download.get('api', 'N/A')))
                self.downloads_table.setItem(row, 5, QTableWidgetItem(download.get('date', 'N/A')))
                self.downloads_table.setItem(row, 6, QTableWidgetItem(download.get('path', 'N/A')))
                
                # Aksiyon butonları
                button_widget = QWidget()
                button_layout = QHBoxLayout(button_widget)
                button_layout.setContentsMargins(2, 2, 2, 2)
                
                # Yeniden indir butonu
                redownload_btn = QPushButton("Yeniden İndir")
                redownload_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 4px 8px; }")
                redownload_btn.clicked.connect(lambda checked, d=download: self.redownload_plugin(d))
                button_layout.addWidget(redownload_btn)
                
                # Dosya aç butonu
                open_file_btn = QPushButton("Dosya Aç")
                open_file_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px 8px; }")
                open_file_btn.clicked.connect(lambda checked, d=download: self.open_file_location(d))
                button_layout.addWidget(open_file_btn)
                
                # Sil butonu
                delete_btn = QPushButton("Sil")
                delete_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; padding: 4px 8px; }")
                delete_btn.clicked.connect(lambda checked, d=download, r=row: self.delete_single_download(d, r))
                button_layout.addWidget(delete_btn)
                
                self.downloads_table.setCellWidget(row, 7, button_widget)
            
            self.stats_label.setText(f"Toplam indirme: {len(downloads)}")
            print(f"İndirme geçmişi yüklendi: {len(downloads)} kayıt")
            
        except Exception as e:
            print(f"İndirme geçmişi yüklenirken hata: {e}")
            QMessageBox.warning(self, "Uyarı", f"İndirme geçmişi yüklenemedi: {e}")
            # Hata durumunda boş tablo göster
            self.downloads_table.setRowCount(0)
            self.stats_label.setText("Toplam indirme: 0")
    
    def clear_history(self):
        """İndirme geçmişini temizle"""
        reply = QMessageBox.question(
            self, 
            "Onay", 
            "İndirme geçmişini temizlemek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(self.downloads_file):
                    os.remove(self.downloads_file)
                self.load_downloads()
                QMessageBox.information(self, "Başarılı", "İndirme geçmişi temizlendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Geçmiş temizlenemedi: {e}")
    
    def add_download(self, name, version, api, path):
        """Yeni indirme kaydı ekle"""
        try:
            # Mevcut kayıtları yükle
            downloads = []
            if os.path.exists(self.downloads_file):
                try:
                    with open(self.downloads_file, 'r', encoding='utf-8') as f:
                        downloads = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    downloads = []
            
            from datetime import datetime
            download_record = {
                'name': name,
                'version': version,
                'api': api,
                'path': path,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            downloads.append(download_record)
            
            # Kayıtları dosyaya yaz
            with open(self.downloads_file, 'w', encoding='utf-8') as f:
                json.dump(downloads, f, ensure_ascii=False, indent=2)
            
            # Tabloyu güncelle
            self.load_downloads()
            
            print(f"İndirme kaydı eklendi: {name} - {version}")
            
        except Exception as e:
            print(f"İndirme kaydı eklenemedi: {e}")
            QMessageBox.warning(self, "Uyarı", f"İndirme kaydı eklenemedi: {e}")   
    def redownload_plugin(self, download_record):
        """Plugin'i yeniden indir"""
        try:
            if not self.search_tab:
                QMessageBox.warning(self, "Uyarı", "Arama sekmesi bulunamadı!")
                return
            
            plugin_name = download_record.get('name', '')
            api_type = download_record.get('api', 'Modrinth')
            
            # Plugin'i ara
            if api_type == "Modrinth":
                from ..api.modrinth_api import ModrinthAPI
                api = ModrinthAPI()
                results = api.search_plugins(plugin_name, limit=10)
            else:
                from ..api.spigot_api import SpigotAPI
                api = SpigotAPI()
                results = api.search_plugins(plugin_name, size=10)
            
            if not results:
                QMessageBox.warning(self, "Uyarı", f"'{plugin_name}' plugini bulunamadı!")
                return
            
            # İlk sonucu al (en uygun match)
            plugin = results[0]
            
            # İndirme dialog'unu aç
            from .download_dialog import DownloadDialog
            dialog = DownloadDialog(plugin, api_type, self)
            dialog.set_download_manager(self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yeniden indirme hatası: {e}")
    
    def start_multiple_downloads(self, plugins_data):
        """Çoklu indirme başlat"""
        try:
            from .multi_download_dialog import MultiDownloadDialog
            dialog = MultiDownloadDialog(plugins_data, self)
            dialog.set_download_manager(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Çoklu indirme hatası: {e}")
    
    def create_api_icon(self, api_type):
        """API ikonu oluştur"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if api_type == "Modrinth":
            icon_label.setText("M")
            icon_label.setStyleSheet("border: 1px solid #1bd96a; border-radius: 4px; background-color: #1bd96a; color: white; font-weight: bold; font-size: 16px;")
        elif api_type == "Spigot":
            icon_label.setText("S")
            icon_label.setStyleSheet("border: 1px solid #f4a261; border-radius: 4px; background-color: #f4a261; color: white; font-weight: bold; font-size: 16px;")
        else:
            icon_label.setText("?")
            icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; background-color: #ccc; color: white; font-weight: bold; font-size: 16px;")
        
        return icon_label   
 
    def select_all_downloads(self):
        """Tüm indirmeleri seç"""
        for row in range(self.downloads_table.rowCount()):
            checkbox = self.downloads_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_downloads(self):
        """Tüm seçimleri kaldır"""
        for row in range(self.downloads_table.rowCount()):
            checkbox = self.downloads_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def update_multi_buttons(self):
        """Çoklu işlem butonlarını güncelle"""
        selected_count = 0
        for row in range(self.downloads_table.rowCount()):
            checkbox = self.downloads_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.redownload_selected_btn.setEnabled(selected_count > 0)
        self.delete_selected_btn.setEnabled(selected_count > 0)
        
        if selected_count > 0:
            self.redownload_selected_btn.setText(f"Seçilenleri Yeniden İndir ({selected_count})")
            self.delete_selected_btn.setText(f"Seçilenleri Sil ({selected_count})")
        else:
            self.redownload_selected_btn.setText("Seçilenleri Yeniden İndir")
            self.delete_selected_btn.setText("Seçilenleri Sil")
    
    def open_file_location(self, download_record):
        """Dosya konumunu aç"""
        try:
            import subprocess
            import os
            
            file_path = download_record.get('path', '')
            if os.path.exists(file_path):
                # Windows'ta dosya konumunu aç
                subprocess.run(['explorer', '/select,', file_path])
            else:
                QMessageBox.warning(self, "Uyarı", f"Dosya bulunamadı:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya konumu açılamadı: {e}")
    
    def delete_single_download(self, download_record, row):
        """Tek indirme kaydını sil"""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{download_record.get('name', 'N/A')}' kaydını silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # JSON'dan sil
                downloads = []
                if os.path.exists(self.downloads_file):
                    with open(self.downloads_file, 'r', encoding='utf-8') as f:
                        downloads = json.load(f)
                
                # Kaydı bul ve sil
                for i, download in enumerate(downloads):
                    if (download.get('name') == download_record.get('name') and 
                        download.get('date') == download_record.get('date')):
                        downloads.pop(i)
                        break
                
                # Dosyaya yaz
                with open(self.downloads_file, 'w', encoding='utf-8') as f:
                    json.dump(downloads, f, ensure_ascii=False, indent=2)
                
                # Tabloyu yenile
                self.load_downloads()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayıt silinemedi: {e}")
    
    def redownload_selected_plugins(self):
        """Seçili pluginleri yeniden indir"""
        try:
            selected_downloads = []
            
            # Seçili kayıtları topla
            downloads = []
            if os.path.exists(self.downloads_file):
                with open(self.downloads_file, 'r', encoding='utf-8') as f:
                    downloads = json.load(f)
            
            for row in range(self.downloads_table.rowCount()):
                checkbox = self.downloads_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    if row < len(downloads):
                        selected_downloads.append(downloads[row])
            
            if not selected_downloads:
                QMessageBox.warning(self, "Uyarı", "Seçili plugin bulunamadı!")
                return
            
            # Çoklu yeniden indirme dialog'unu aç
            from .redownload_dialog import RedownloadDialog
            dialog = RedownloadDialog(selected_downloads, self)
            dialog.set_download_manager(self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yeniden indirme hatası: {e}")
    
    def delete_selected_downloads(self):
        """Seçili indirme kayıtlarını sil"""
        selected_count = 0
        for row in range(self.downloads_table.rowCount()):
            checkbox = self.downloads_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        if selected_count == 0:
            QMessageBox.warning(self, "Uyarı", "Silinecek kayıt seçilmedi!")
            return
        
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{selected_count} kaydı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Mevcut kayıtları yükle
                downloads = []
                if os.path.exists(self.downloads_file):
                    with open(self.downloads_file, 'r', encoding='utf-8') as f:
                        downloads = json.load(f)
                
                # Seçili kayıtları sil (tersten git ki index karışmasın)
                for row in range(self.downloads_table.rowCount() - 1, -1, -1):
                    checkbox = self.downloads_table.cellWidget(row, 0)
                    if checkbox and checkbox.isChecked():
                        if row < len(downloads):
                            downloads.pop(row)
                
                # Dosyaya yaz
                with open(self.downloads_file, 'w', encoding='utf-8') as f:
                    json.dump(downloads, f, ensure_ascii=False, indent=2)
                
                # Tabloyu yenile
                self.load_downloads()
                
                QMessageBox.information(self, "Başarılı", f"{selected_count} kayıt silindi.")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kayıtlar silinemedi: {e}")