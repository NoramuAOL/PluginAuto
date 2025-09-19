"""
Liste düzenleme dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTextEdit, QComboBox,
                            QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt

class EditListDialog(QDialog):
    def __init__(self, list_name, list_info, parent=None):
        super().__init__(parent)
        self.original_name = list_name
        self.list_info = list_info
        self.init_ui()
        self.load_current_data()
        
    def init_ui(self):
        self.setWindowTitle("Liste Düzenle")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Liste bilgileri group
        info_group = QGroupBox("Liste Bilgileri")
        info_layout = QGridLayout(info_group)
        
        # Liste adı
        info_layout.addWidget(QLabel("Liste Adı:"), 0, 0)
        self.name_input = QLineEdit()
        info_layout.addWidget(self.name_input, 0, 1)
        
        # İkon seçimi
        info_layout.addWidget(QLabel("İkon:"), 1, 0)
        self.icon_combo = QComboBox()
        self.icon_combo.addItems([
            "📋 Varsayılan",
            "🎮 Oyun",
            "⚔️ PvP",
            "🏠 Survival", 
            "🏭 Teknik",
            "🎨 Yaratıcı",
            "🛡️ Koruma",
            "💰 Ekonomi",
            "🎪 Eğlence",
            "🔧 Yönetim",
            "🌍 Dünya",
            "👥 Sosyal",
            "📊 İstatistik",
            "🎯 Hedef",
            "⭐ Favoriler",
            "🔥 Popüler",
            "🆕 Yeni",
            "🧪 Test",
            "📦 Paket",
            "🎁 Özel"
        ])
        info_layout.addWidget(self.icon_combo, 1, 1)
        
        layout.addWidget(info_group)
        
        # Açıklama group
        desc_group = QGroupBox("Açıklama")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        desc_layout.addWidget(self.description_input)
        
        layout.addWidget(desc_group)
        
        # İstatistikler group
        stats_group = QGroupBox("İstatistikler")
        stats_layout = QGridLayout(stats_group)
        
        plugin_count = len(self.list_info.get('plugins', []))
        created_date = self.list_info.get('created_date', 'Bilinmiyor')
        last_updated = self.list_info.get('last_updated', 'Bilinmiyor')
        
        stats_layout.addWidget(QLabel("Plugin Sayısı:"), 0, 0)
        stats_layout.addWidget(QLabel(str(plugin_count)), 0, 1)
        
        stats_layout.addWidget(QLabel("Oluşturulma:"), 1, 0)
        stats_layout.addWidget(QLabel(created_date), 1, 1)
        
        stats_layout.addWidget(QLabel("Son Güncelleme:"), 2, 0)
        stats_layout.addWidget(QLabel(last_updated), 2, 1)
        
        layout.addWidget(stats_group)
        
        # Önizleme group
        preview_group = QGroupBox("Önizleme")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(preview_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Değişiklikleri Kaydet")
        self.save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; }")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Değişiklikleri dinle
        self.name_input.textChanged.connect(self.update_preview)
        self.icon_combo.currentTextChanged.connect(self.update_preview)
        self.description_input.textChanged.connect(self.update_preview)
        
    def load_current_data(self):
        """Mevcut verileri yükle"""
        self.name_input.setText(self.original_name)
        
        # İkon seçimini ayarla
        current_icon = self.list_info.get('icon', '📋 Varsayılan')
        index = self.icon_combo.findText(current_icon)
        if index >= 0:
            self.icon_combo.setCurrentIndex(index)
        
        # Açıklamayı yükle
        self.description_input.setPlainText(self.list_info.get('description', ''))
        
        # İlk önizlemeyi güncelle
        self.update_preview()
        
    def update_preview(self):
        """Önizlemeyi güncelle"""
        name = self.name_input.text().strip()
        icon = self.icon_combo.currentText()
        description = self.description_input.toPlainText().strip()
        
        # Buton durumunu güncelle
        self.save_btn.setEnabled(bool(name))
        
        # Önizlemeyi güncelle
        if name:
            preview_text = f"{icon} {name}"
            if description:
                preview_text += f"\n{description}"
            else:
                preview_text += "\nAçıklama yok"
        else:
            preview_text = f"{icon} Liste Adı\nAçıklama burada görünecek..."
        
        self.preview_label.setText(preview_text)
    
    def get_list_data(self):
        """Liste verilerini döndür"""
        return {
            'name': self.name_input.text().strip(),
            'icon': self.icon_combo.currentText(),
            'description': self.description_input.toPlainText().strip()
        }