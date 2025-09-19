"""
Plugin'i listeye ekleme dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QMessageBox, QTextEdit,
                            QGroupBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import json

from ..api.modrinth_api import ModrinthAPI
from ..api.spigot_api import SpigotAPI

class VersionLoadWorker(QThread):
    versions_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, plugin, api_type):
        super().__init__()
        self.plugin = plugin
        self.api_type = api_type
        
    def run(self):
        try:
            if self.api_type == "Modrinth":
                api = ModrinthAPI()
                plugin_id = self.plugin.get('project_id') or self.plugin.get('slug')
                versions = api.get_plugin_versions(plugin_id, limit=200)  # Daha fazla sürüm al
            else:  # Spigot
                api = SpigotAPI()
                plugin_id = self.plugin.get('id')
                versions = api.get_plugin_versions(plugin_id, size=30)
            
            self.versions_loaded.emit(versions)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AddToListDialog(QDialog):
    def __init__(self, plugin, lists_tab, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.lists_tab = lists_tab
        self.versions = []
        self.selected_version_data = None
        self.init_ui()
        self.load_versions()
        
    def init_ui(self):
        self.setWindowTitle("Listeye Plugin Ekle")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Plugin bilgileri
        api_source = self.plugin.get('_api_source', 'Unknown')
        if api_source == "Modrinth":
            plugin_name = self.plugin.get('title', 'N/A')
            plugin_desc = self.plugin.get('description', 'N/A')
            plugin_author = self.plugin.get('author', 'N/A')
        else:
            plugin_name = self.plugin.get('name', 'N/A')
            plugin_desc = self.plugin.get('tag', 'N/A')
            
            # Yazar bilgisini güvenli şekilde al
            author_info = self.plugin.get('author')
            if isinstance(author_info, dict):
                plugin_author = author_info.get('username', author_info.get('name', 'Bilinmeyen'))
            elif isinstance(author_info, str):
                plugin_author = author_info
            else:
                plugin_author = 'Bilinmeyen'
        
        # Plugin info group
        info_group = QGroupBox("Plugin Bilgileri")
        info_layout = QVBoxLayout(info_group)
        
        info_layout.addWidget(QLabel(f"Ad: {plugin_name}"))
        info_layout.addWidget(QLabel(f"Yazar: {plugin_author}"))
        info_layout.addWidget(QLabel(f"API: {api_source}"))
        
        desc_text = QTextEdit()
        desc_text.setPlainText(plugin_desc)
        desc_text.setMaximumHeight(80)
        desc_text.setReadOnly(True)
        info_layout.addWidget(desc_text)
        
        layout.addWidget(info_group)
        
        # Sürüm seçimi group
        version_group = QGroupBox("Sürüm Seçimi")
        version_layout = QVBoxLayout(version_group)
        
        # Sürüm seçimi combo
        version_select_layout = QHBoxLayout()
        version_select_layout.addWidget(QLabel("Sürüm:"))
        
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(300)
        self.version_combo.currentTextChanged.connect(self.version_selected)
        version_select_layout.addWidget(self.version_combo)
        
        version_layout.addLayout(version_select_layout)
        
        # Bilgi notu
        info_label = QLabel("💡 İlk sürüm en güncel sürümdür. İstediğiniz sürümü seçebilirsiniz.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        version_layout.addWidget(info_label)
        
        layout.addWidget(version_group)
        
        # Liste seçimi
        list_group = QGroupBox("Liste Seçimi")
        list_layout = QVBoxLayout(list_group)
        
        list_select_layout = QHBoxLayout()
        list_select_layout.addWidget(QLabel("Liste:"))
        
        self.list_combo = QComboBox()
        self.load_available_lists()
        list_select_layout.addWidget(self.list_combo)
        
        new_list_btn = QPushButton("Yeni Liste")
        new_list_btn.clicked.connect(self.create_new_list)
        list_select_layout.addWidget(new_list_btn)
        
        list_layout.addLayout(list_select_layout)
        layout.addWidget(list_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Listeye Ekle")
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; }")
        self.add_btn.clicked.connect(self.add_to_list)
        button_layout.addWidget(self.add_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_available_lists(self):
        """Mevcut listeleri yükle"""
        lists = self.lists_tab.get_list_names()
        self.list_combo.clear()
        
        if lists:
            self.list_combo.addItems(lists)
        else:
            self.list_combo.addItem("Liste bulunamadı")
    
    def create_new_list(self):
        """Yeni liste oluştur"""
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Yeni Liste", "Liste adı:")
        if ok and name.strip():
            # Lists tab'dan yeni liste oluştur
            self.lists_tab.create_new_list_from_dialog(name.strip())
            # Combo'yu güncelle
            self.load_available_lists()
            # Yeni listeyi seç
            index = self.list_combo.findText(name.strip())
            if index >= 0:
                self.list_combo.setCurrentIndex(index)
    
    def load_versions(self):
        """Plugin versiyonlarını yükle"""
        api_source = self.plugin.get('_api_source', 'Unknown')
        
        self.version_combo.clear()
        self.version_combo.addItem("Yükleniyor...", None)
        
        # Worker thread ile versiyonları yükle
        self.version_worker = VersionLoadWorker(self.plugin, api_source)
        self.version_worker.versions_loaded.connect(self.versions_loaded)
        self.version_worker.error_occurred.connect(self.version_load_error)
        self.version_worker.start()
    
    def versions_loaded(self, versions):
        """Versiyonlar yüklendiğinde"""
        self.versions = versions
        self.version_combo.clear()
        
        if versions:
            for version in versions:
                api_source = self.plugin.get('_api_source', 'Unknown')
                
                if api_source == "Modrinth":
                    version_name = version.get('version_number', 'N/A')
                    game_versions = version.get('game_versions', [])
                    if game_versions:
                        display_name = f"{version_name} (MC: {', '.join(game_versions)})"
                    else:
                        display_name = version_name
                else:
                    version_name = version.get('name', 'N/A')
                    display_name = version_name
                
                self.version_combo.addItem(display_name, version)
        else:
            self.version_combo.addItem("Sürüm bulunamadı", None)
    
    def version_load_error(self, error):
        """Versiyon yükleme hatası"""
        self.version_combo.clear()
        self.version_combo.addItem("Hata: Sürümler yüklenemedi", None)
        QMessageBox.warning(self, "Uyarı", f"Sürümler yüklenemedi: {error}")
    
    def version_selected(self):
        """Sürüm seçildiğinde"""
        self.selected_version_data = self.version_combo.currentData()
        # Buton durumunu güncelle
        self.add_btn.setEnabled(self.selected_version_data is not None)
    
    def add_to_list(self):
        """Plugin'i listeye ekle"""
        # Liste seçimi kontrol et
        if self.list_combo.currentText() == "Liste bulunamadı":
            QMessageBox.warning(self, "Uyarı", "Önce bir liste oluşturun!")
            return
        
        selected_list = self.list_combo.currentText()
        
        # Plugin verilerini hazırla
        api_source = self.plugin.get('_api_source', 'Unknown')
        
        if api_source == "Modrinth":
            plugin_name = self.plugin.get('title', 'N/A')
            plugin_id = self.plugin.get('project_id') or self.plugin.get('slug', '')
        else:
            plugin_name = self.plugin.get('name', 'N/A')
            plugin_id = str(self.plugin.get('id', ''))
        
        # Sürüm bilgilerini belirle
        if not self.selected_version_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir sürüm seçin!")
            return
        
        version_type = "specific"
        if api_source == "Modrinth":
            current_version = self.selected_version_data.get('version_number', 'N/A')
        else:
            current_version = self.selected_version_data.get('name', 'N/A')
        version_data = self.selected_version_data
        
        # İkon URL'sini al
        if api_source == "Modrinth":
            icon_url = self.plugin.get('icon_url', '')
        else:
            # Spigot ikon URL'sini oluştur
            icon_data = self.plugin.get('icon', {})
            icon_url = ''
            if icon_data and isinstance(icon_data, dict) and 'url' in icon_data:
                url = icon_data['url']
                if url.startswith('http'):
                    icon_url = url
                elif url.startswith('/'):
                    icon_url = f"https://www.spigotmc.org{url}"
                else:
                    icon_url = f"https://www.spigotmc.org/{url}"
        
        plugin_data = {
            'name': plugin_name,
            'plugin_id': plugin_id,
            'api': api_source,
            'version_type': version_type,
            'current_version': current_version,
            'latest_version': 'Kontrol ediliyor...',
            'version_data': version_data,
            'icon_url': icon_url,
            'added_date': self.get_current_datetime(),
            'last_checked': self.get_current_datetime()
        }
        
        # Listeye ekle
        success = self.lists_tab.add_plugin_to_list(selected_list, plugin_data)
        
        if success:
            QMessageBox.information(self, "Başarılı", f"'{plugin_name}' başarıyla '{selected_list}' listesine eklendi!")
            self.accept()
    
    def get_current_datetime(self):
        """Şu anki tarih-saat"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')