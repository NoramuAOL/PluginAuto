"""
Plugin aktarma dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QRadioButton, QButtonGroup,
                            QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
                            QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
import json

class TransferPluginsDialog(QDialog):
    def __init__(self, plugins, available_lists, current_list, parent=None):
        super().__init__(parent)
        self.plugins = plugins
        self.available_lists = [lst for lst in available_lists if lst != current_list]
        self.current_list = current_list
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Plugin'leri Aktar")
        self.setModal(True)
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Hedef liste seçimi
        target_group = QGroupBox("Hedef Liste")
        target_layout = QVBoxLayout(target_group)
        
        target_layout.addWidget(QLabel("Plugin'leri hangi listeye aktarmak istiyorsunuz?"))
        
        self.target_combo = QComboBox()
        self.target_combo.addItems(self.available_lists)
        target_layout.addWidget(self.target_combo)
        
        layout.addWidget(target_group)
        
        # Aktarma modu seçimi
        mode_group = QGroupBox("Aktarma Modu")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup()
        
        self.same_version_radio = QRadioButton("Aynı Sürüm - Plugin'leri mevcut sürümleriyle aktar")
        self.same_version_radio.setChecked(True)
        self.mode_group.addButton(self.same_version_radio, 0)
        mode_layout.addWidget(self.same_version_radio)
        
        self.different_version_radio = QRadioButton("Farklı Sürüm - Her plugin için sürüm seçebilir")
        self.mode_group.addButton(self.different_version_radio, 1)
        mode_layout.addWidget(self.different_version_radio)
        
        layout.addWidget(mode_group)
        
        # Plugin listesi
        plugins_group = QGroupBox(f"Aktarılacak Plugin'ler ({len(self.plugins)} adet)")
        plugins_layout = QVBoxLayout(plugins_group)
        
        # Plugin tablosu
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(5)
        self.plugins_table.setHorizontalHeaderLabels([
            "Seç", "Plugin Adı", "Mevcut Sürüm", "API", "Yeni Sürüm"
        ])
        
        # Tablo ayarları
        header = self.plugins_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        
        self.plugins_table.setColumnWidth(0, 50)
        self.plugins_table.setColumnWidth(1, 200)
        self.plugins_table.setColumnWidth(2, 120)
        self.plugins_table.setColumnWidth(3, 80)
        self.plugins_table.setColumnWidth(4, 150)
        
        self.load_plugins()
        plugins_layout.addWidget(self.plugins_table)
        
        # Tümünü seç/kaldır butonları
        select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.clicked.connect(self.select_all_plugins)
        select_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Seçimi Kaldır")
        deselect_all_btn.clicked.connect(self.deselect_all_plugins)
        select_layout.addWidget(deselect_all_btn)
        
        select_layout.addStretch()
        plugins_layout.addLayout(select_layout)
        
        layout.addWidget(plugins_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.transfer_btn = QPushButton("Plugin'leri Aktar")
        self.transfer_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; }")
        self.transfer_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.transfer_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Mod değişikliklerini dinle
        self.same_version_radio.toggled.connect(self.on_mode_changed)
        self.different_version_radio.toggled.connect(self.on_mode_changed)
        
    def load_plugins(self):
        """Plugin'leri tabloya yükle"""
        self.plugins_table.setRowCount(len(self.plugins))
        
        for row, plugin in enumerate(self.plugins):
            # Seçim checkbox'ı
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.plugins_table.setCellWidget(row, 0, checkbox)
            
            # Plugin bilgileri
            self.plugins_table.setItem(row, 1, QTableWidgetItem(plugin.get('name', 'N/A')))
            self.plugins_table.setItem(row, 2, QTableWidgetItem(plugin.get('current_version', 'N/A')))
            self.plugins_table.setItem(row, 3, QTableWidgetItem(plugin.get('api', 'N/A')))
            
            # Sürüm seçimi (başlangıçta gizli)
            version_combo = QComboBox()
            version_combo.addItem(plugin.get('current_version', 'N/A'))
            version_combo.setEnabled(False)
            self.plugins_table.setCellWidget(row, 4, version_combo)
    
    def on_mode_changed(self):
        """Mod değiştiğinde çağrılır"""
        different_version_mode = self.different_version_radio.isChecked()
        
        # Sürüm combo'larını etkinleştir/devre dışı bırak
        for row in range(self.plugins_table.rowCount()):
            version_combo = self.plugins_table.cellWidget(row, 4)
            if version_combo:
                version_combo.setEnabled(different_version_mode)
                
                if different_version_mode:
                    # Farklı sürüm modunda sürümleri yükle
                    self.load_versions_for_plugin(row)
    
    def load_versions_for_plugin(self, row):
        """Plugin için mevcut sürümleri yükle"""
        try:
            plugin = self.plugins[row]
            api_type = plugin.get('api', 'Modrinth')
            plugin_id = plugin.get('plugin_id', '')
            
            version_combo = self.plugins_table.cellWidget(row, 4)
            if not version_combo:
                return
            
            version_combo.clear()
            version_combo.addItem("Yükleniyor...")
            
            # API'den sürümleri al
            if api_type == "Modrinth":
                from ..api.modrinth_api import ModrinthAPI
                api = ModrinthAPI()
                versions = api.get_plugin_versions(plugin_id)
            else:
                from ..api.spigot_api import SpigotAPI
                api = SpigotAPI()
                versions = api.get_plugin_versions(plugin_id)
            
            version_combo.clear()
            
            if versions:
                for version in versions[:10]:  # İlk 10 sürümü göster
                    if api_type == "Modrinth":
                        version_name = version.get('version_number', 'N/A')
                        game_versions = version.get('game_versions', [])
                        if game_versions:
                            display_name = f"{version_name} (MC: {', '.join(game_versions[:3])})"
                        else:
                            display_name = version_name
                    else:
                        version_name = version.get('name', 'N/A')
                        display_name = version_name
                    
                    version_combo.addItem(display_name, version)
            else:
                version_combo.addItem("Sürüm bulunamadı")
                
        except Exception as e:
            print(f"Sürüm yükleme hatası: {e}")
            version_combo = self.plugins_table.cellWidget(row, 4)
            if version_combo:
                version_combo.clear()
                version_combo.addItem("Hata")
    
    def select_all_plugins(self):
        """Tüm plugin'leri seç"""
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_plugins(self):
        """Tüm seçimleri kaldır"""
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def get_transfer_data(self):
        """Aktarma verilerini döndür"""
        target_list = self.target_combo.currentText()
        transfer_mode = "same_version" if self.same_version_radio.isChecked() else "different_version"
        
        plugins_to_transfer = []
        
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                plugin = self.plugins[row].copy()
                
                # Farklı sürüm modunda seçili sürümü al
                if transfer_mode == "different_version":
                    version_combo = self.plugins_table.cellWidget(row, 4)
                    if version_combo and version_combo.currentData():
                        selected_version = version_combo.currentData()
                        plugin['version_data'] = selected_version
                        
                        # Sürüm bilgisini güncelle
                        if plugin.get('api') == 'Modrinth':
                            plugin['current_version'] = selected_version.get('version_number', 'N/A')
                        else:
                            plugin['current_version'] = selected_version.get('name', 'N/A')
                
                plugins_to_transfer.append(plugin)
        
        return {
            'target_list': target_list,
            'transfer_mode': transfer_mode,
            'plugins': plugins_to_transfer
        }