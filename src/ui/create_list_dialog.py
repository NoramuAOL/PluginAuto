"""
Yeni liste oluşturma dialog penceresi
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTextEdit, QComboBox,
                            QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt

class CreateListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Yeni Liste Oluştur")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Liste bilgileri group
        info_group = QGroupBox("Liste Bilgileri")
        info_layout = QGridLayout(info_group)
        
        # Liste adı
        info_layout.addWidget(QLabel("Liste Adı:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Survival Pluginleri")
        info_layout.addWidget(self.name_input, 0, 1)
        
        # İkon seçimi
        info_layout.addWidget(QLabel("İkon:"), 1, 0)
        
        icon_layout = QHBoxLayout()
        
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
        icon_layout.addWidget(self.icon_combo)
        
        # Özel ikon seç butonu
        self.custom_icon_btn = QPushButton("Özel İkon Seç")
        self.custom_icon_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px 8px; }")
        self.custom_icon_btn.clicked.connect(self.select_custom_icon)
        icon_layout.addWidget(self.custom_icon_btn)
        
        info_layout.addLayout(icon_layout, 1, 1)
        
        # Özel ikon önizleme
        self.custom_icon_preview = QLabel()
        self.custom_icon_preview.setFixedSize(32, 32)
        self.custom_icon_preview.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        self.custom_icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.custom_icon_preview.hide()
        info_layout.addWidget(self.custom_icon_preview, 1, 2)
        
        # Özel ikon yolu
        self.custom_icon_path = ""
        
        layout.addWidget(info_group)
        
        # Açıklama group
        desc_group = QGroupBox("Açıklama")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Bu liste hakkında kısa bir açıklama yazın...")
        self.description_input.setMaximumHeight(100)
        desc_layout.addWidget(self.description_input)
        
        layout.addWidget(desc_group)
        
        # Önizleme group
        preview_group = QGroupBox("Önizleme")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("📋 Liste Adı\nAçıklama burada görünecek...")
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
        
        self.create_btn = QPushButton("Liste Oluştur")
        self.create_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; }")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setEnabled(False)
        button_layout.addWidget(self.create_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Değişiklikleri dinle
        self.name_input.textChanged.connect(self.update_preview)
        self.icon_combo.currentTextChanged.connect(self.update_preview)
        self.description_input.textChanged.connect(self.update_preview)
        
        # İlk önizlemeyi güncelle
        self.update_preview()
        
    def update_preview(self):
        """Önizlemeyi güncelle"""
        name = self.name_input.text().strip()
        icon = self.icon_combo.currentText()
        description = self.description_input.toPlainText().strip()
        
        # Buton durumunu güncelle
        self.create_btn.setEnabled(bool(name))
        
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
    
    def select_custom_icon(self):
        """Özel ikon seç"""
        from PyQt6.QtWidgets import QFileDialog
        import os
        import shutil
        
        # Dosya seç
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Özel İkon Seç",
            "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.gif *.bmp *.ico)"
        )
        
        if file_path:
            try:
                # images klasörünü oluştur
                images_dir = "images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                # Dosya adını oluştur
                file_name = os.path.basename(file_path)
                name_part, ext = os.path.splitext(file_name)
                
                # Benzersiz dosya adı oluştur
                counter = 1
                new_file_name = file_name
                while os.path.exists(os.path.join(images_dir, new_file_name)):
                    new_file_name = f"{name_part}_{counter}{ext}"
                    counter += 1
                
                # Dosyayı kopyala
                new_file_path = os.path.join(images_dir, new_file_name)
                shutil.copy2(file_path, new_file_path)
                
                # Özel ikon yolunu kaydet
                self.custom_icon_path = new_file_path
                
                # Önizlemeyi güncelle
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap(new_file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.custom_icon_preview.setPixmap(scaled_pixmap)
                    self.custom_icon_preview.show()
                
                # Combo'yu özel ikon moduna al
                self.icon_combo.setCurrentText("🖼️ Özel İkon")
                if self.icon_combo.currentText() != "🖼️ Özel İkon":
                    self.icon_combo.addItem("🖼️ Özel İkon")
                    self.icon_combo.setCurrentText("🖼️ Özel İkon")
                
                self.update_preview()
                
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Hata", f"İkon kopyalanamadı: {e}")
    
    def get_list_data(self):
        """Liste verilerini döndür"""
        data = {
            'name': self.name_input.text().strip(),
            'icon': self.icon_combo.currentText(),
            'description': self.description_input.toPlainText().strip()
        }
        
        # Özel ikon varsa yolunu ekle
        if self.custom_icon_path:
            data['custom_icon_path'] = self.custom_icon_path
        
        return data