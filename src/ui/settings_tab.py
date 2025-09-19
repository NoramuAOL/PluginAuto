"""
Ayarlar sekmesi
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QSpinBox,
                            QGroupBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
import json
import os

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # İndirme ayarları
        download_group = QGroupBox("İndirme Ayarları")
        download_layout = QVBoxLayout(download_group)
        
        # Varsayılan indirme klasörü
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Varsayılan İndirme Klasörü:"))
        
        self.folder_input = QLineEdit(self.settings.get('default_folder', 'plugins'))
        folder_layout.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Gözat")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        
        download_layout.addLayout(folder_layout)
        
        # Eşzamanlı indirme sayısı
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Eşzamanlı İndirme Sayısı:"))
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(self.settings.get('concurrent_downloads', 3))
        concurrent_layout.addWidget(self.concurrent_spin)
        
        download_layout.addLayout(concurrent_layout)
        
        layout.addWidget(download_group)
        
        # API ayarları
        api_group = QGroupBox("API Ayarları")
        api_layout = QVBoxLayout(api_group)
        
        # Arama sonuç limiti
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Arama Sonuç Limiti:"))
        
        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(10)
        self.limit_spin.setMaximum(100)
        self.limit_spin.setValue(self.settings.get('search_limit', 20))
        limit_layout.addWidget(self.limit_spin)
        
        api_layout.addLayout(limit_layout)
        
        # Varsayılan API
        default_api_layout = QHBoxLayout()
        default_api_layout.addWidget(QLabel("Varsayılan API:"))
        
        from PyQt6.QtWidgets import QComboBox
        self.default_api_combo = QComboBox()
        self.default_api_combo.addItems(["Modrinth", "Spigot"])
        self.default_api_combo.setCurrentText(self.settings.get('default_api', 'Modrinth'))
        default_api_layout.addWidget(self.default_api_combo)
        
        api_layout.addLayout(default_api_layout)
        
        layout.addWidget(api_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Varsayılana Sıfırla")
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def load_settings(self):
        """Ayarları yükle"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.get_default_settings()
        except Exception as e:
            print(f"Ayarlar yüklenemedi: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Varsayılan ayarları döndür"""
        return {
            'default_folder': 'plugins',
            'concurrent_downloads': 3,
            'search_limit': 20,
            'default_api': 'Modrinth'
        }
    
    def save_settings(self):
        """Ayarları kaydet"""
        try:
            self.settings = {
                'default_folder': self.folder_input.text(),
                'concurrent_downloads': self.concurrent_spin.value(),
                'search_limit': self.limit_spin.value(),
                'default_api': self.default_api_combo.currentText()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Başarılı", "Ayarlar kaydedildi.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilemedi: {e}")
    
    def reset_settings(self):
        """Ayarları varsayılana sıfırla"""
        reply = QMessageBox.question(
            self,
            "Onay",
            "Ayarları varsayılana sıfırlamak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self.get_default_settings()
            self.update_ui()
            QMessageBox.information(self, "Başarılı", "Ayarlar sıfırlandı.")
    
    def update_ui(self):
        """UI'yi ayarlara göre güncelle"""
        self.folder_input.setText(self.settings.get('default_folder', 'plugins'))
        self.concurrent_spin.setValue(self.settings.get('concurrent_downloads', 3))
        self.limit_spin.setValue(self.settings.get('search_limit', 20))
        self.default_api_combo.setCurrentText(self.settings.get('default_api', 'Modrinth'))
    
    def browse_folder(self):
        """Klasör seç"""
        folder = QFileDialog.getExistingDirectory(self, "Varsayılan İndirme Klasörü Seç")
        if folder:
            self.folder_input.setText(folder)