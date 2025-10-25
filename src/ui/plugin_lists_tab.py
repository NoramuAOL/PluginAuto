"""
Plugin Listeleri sekmesi
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QPushButton, QInputDialog,
                            QMessageBox, QSplitter, QTableWidget, QTableWidgetItem,
                            QHeaderView, QCheckBox, QMenu, QComboBox, QDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
import os
import json
from datetime import datetime
from ..utils import SettingsManager, IconManager, IconCacheMixin, PluginSorter, ListManager

class PluginListsTab(QWidget, IconCacheMixin):
    def __init__(self):
        super().__init__()
        self.download_manager = None
        self.current_list_name = None
        self.icon_cache = None  # İkon cache referansı
        self.list_manager = ListManager()
        self.lists_file = "plugin_lists.json"  # Liste dosyası
        self.init_ui()
        self.load_lists()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Sol panel - Liste yönetimi
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Liste başlığı ve butonları
        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("Plugin Listeleri"))
        list_header.addStretch()
        
        new_list_btn = QPushButton("Yeni Liste")
        new_list_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px 12px; }")
        new_list_btn.clicked.connect(self.create_new_list)
        list_header.addWidget(new_list_btn)
        
        left_layout.addLayout(list_header)
        
        # Liste widget'ı
        self.lists_widget = QListWidget()
        self.lists_widget.itemClicked.connect(self.list_selected)
        self.lists_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lists_widget.customContextMenuRequested.connect(self.show_list_context_menu)
        self.lists_widget.setIconSize(QSize(32, 32))  # İkon boyutunu ayarla
        left_layout.addWidget(self.lists_widget)
        
        # Liste istatistikleri
        self.list_stats_label = QLabel("Liste seçilmedi")
        left_layout.addWidget(self.list_stats_label)
        
        # Sağ panel - Plugin yönetimi
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Plugin başlığı
        plugin_header = QHBoxLayout()
        self.plugin_list_title = QLabel("Plugin listesi seçin")
        plugin_header.addWidget(self.plugin_list_title)
        plugin_header.addStretch()
        
        # Sıralama butonu
        sort_btn = QPushButton("Sıralamayı Değiştir")
        sort_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 6px 12px; }")
        sort_btn.clicked.connect(self.change_sorting)
        plugin_header.addWidget(sort_btn)
        
        right_layout.addLayout(plugin_header)
        
        # Çoklu işlem butonları
        multi_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.clicked.connect(self.select_all_plugins)
        multi_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Seçimi Kaldır")
        deselect_all_btn.clicked.connect(self.deselect_all_plugins)
        multi_layout.addWidget(deselect_all_btn)
        
        multi_layout.addStretch()
        
        self.download_selected_btn = QPushButton("Seçilenleri İndir")
        self.download_selected_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px 12px; }")
        self.download_selected_btn.clicked.connect(self.download_selected_plugins)
        self.download_selected_btn.setEnabled(False)
        multi_layout.addWidget(self.download_selected_btn)
        
        self.remove_selected_btn = QPushButton("Seçilenleri Kaldır")
        self.remove_selected_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 6px 12px; }")
        self.remove_selected_btn.clicked.connect(self.remove_selected_plugins)
        self.remove_selected_btn.setEnabled(False)
        multi_layout.addWidget(self.remove_selected_btn)
        
        self.transfer_selected_btn = QPushButton("Seçilenleri Aktar")
        self.transfer_selected_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 6px 12px; }")
        self.transfer_selected_btn.clicked.connect(self.transfer_selected_plugins)
        self.transfer_selected_btn.setEnabled(False)
        multi_layout.addWidget(self.transfer_selected_btn)
        
        right_layout.addLayout(multi_layout)
        
        # Plugin tablosu
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(6)
        self.plugins_table.setHorizontalHeaderLabels([
            "Seç", "İkon", "Plugin Adı", "Mevcut Sürüm", "API", "Aksiyon"
        ])
        
        # Tablo ayarları
        header = self.plugins_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        
        self.plugins_table.setColumnWidth(0, 50)
        self.plugins_table.setColumnWidth(1, 70)
        self.plugins_table.setColumnWidth(2, 200)
        self.plugins_table.setColumnWidth(3, 120)
        self.plugins_table.setColumnWidth(4, 80)
        self.plugins_table.setColumnWidth(5, 150)
        
        self.plugins_table.verticalHeader().setDefaultSectionSize(60)
        
        right_layout.addWidget(self.plugins_table)
        
        # Splitter ile panelleri ayır
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])  # Sol panel 300px, sağ panel 700px
        
        layout.addWidget(splitter)
        
    def set_download_manager(self, download_manager):
        """Download manager referansını ayarla"""
        self.download_manager = download_manager
    
    def set_icon_cache(self, icon_cache):
        """İkon cache referansını ayarla"""
        self.icon_cache = icon_cache
        
    def load_lists(self):
        """Plugin listelerini yükle"""
        try:
            lists_data = self.list_manager.load_lists()
            
            self.lists_widget.clear()
            for list_name, list_info in lists_data.items():
                # İkon ve açıklama bilgisini al
                icon = list_info.get('icon', '📋 Varsayılan')
                description = list_info.get('description', '')
                custom_icon_path = list_info.get('custom_icon_path', '')
                
                # Liste item'ını oluştur
                item = QListWidgetItem()
                
                # Özel ikon varsa kullan
                if custom_icon_path and os.path.exists(custom_icon_path):
                    pixmap = QPixmap(custom_icon_path)
                    if not pixmap.isNull():
                        # İkonu uygun boyuta ölçeklendir (32x32)
                        scaled_pixmap = pixmap.scaled(
                            32, 32,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        icon_obj = QIcon(scaled_pixmap)
                        item.setIcon(icon_obj)
                        item.setText(list_name)
                    else:
                        # Özel ikon yüklenemezse emoji kullan
                        icon_emoji = icon.split(' ')[0] if icon else '📋'
                        item.setText(f"{icon_emoji} {list_name}")
                else:
                    # Sadece emoji kısmını al
                    icon_emoji = icon.split(' ')[0] if icon else '📋'
                    item.setText(f"{icon_emoji} {list_name}")
                
                # Tooltip olarak açıklamayı ekle
                if description:
                    item.setToolTip(f"{list_name}\n\n{description}")
                else:
                    item.setToolTip(list_name)
                
                # Liste adını data olarak sakla
                item.setData(Qt.ItemDataRole.UserRole, list_name)
                
                self.lists_widget.addItem(item)
                
        except Exception as e:
            print(f"Liste yükleme hatası: {e}")
            QMessageBox.warning(self, "Uyarı", f"Listeler yüklenemedi: {e}")
    
    def create_new_list(self):
        """Yeni liste oluştur"""
        from .create_list_dialog import CreateListDialog
        dialog = CreateListDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            list_data = dialog.get_list_data()
            
            # Mevcut listeleri kontrol et
            try:
                if os.path.exists(self.lists_file):
                    with open(self.lists_file, 'r', encoding='utf-8') as f:
                        lists_data = json.load(f)
                else:
                    lists_data = {}
                
                if list_data['name'] in lists_data:
                    QMessageBox.warning(self, "Uyarı", "Bu isimde bir liste zaten var!")
                    return
                
                # Yeni liste oluştur
                lists_data[list_data['name']] = {
                    'plugins': [],
                    'icon': list_data['icon'],
                    'description': list_data['description'],
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Dosyaya kaydet
                with open(self.lists_file, 'w', encoding='utf-8') as f:
                    json.dump(lists_data, f, ensure_ascii=False, indent=2)
                
                # UI'yi güncelle
                self.load_lists()
                
                # Yeni listeyi seç
                for i in range(self.lists_widget.count()):
                    if self.lists_widget.item(i).text() == list_data['name']:
                        self.lists_widget.setCurrentRow(i)
                        self.list_selected(self.lists_widget.item(i))
                        break
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Liste oluşturulamadı: {e}")
    
    def show_list_context_menu(self, position):
        """Liste sağ tık menüsü"""
        item = self.lists_widget.itemAt(position)
        if item is None:
            return
        
        list_name = item.data(Qt.ItemDataRole.UserRole)
        if not list_name:
            list_name = item.text().split(' ', 1)[-1]
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("Düzenle")
        edit_action.triggered.connect(lambda: self.edit_list(list_name))
        
        rename_action = menu.addAction("Yeniden Adlandır")
        rename_action.triggered.connect(lambda: self.rename_list(list_name))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Sil")
        delete_action.triggered.connect(lambda: self.delete_list(list_name))
        
        menu.exec(self.lists_widget.mapToGlobal(position))
    
    def rename_list(self, old_name):
        """Liste adını değiştir"""
        new_name, ok = QInputDialog.getText(self, "Liste Adını Değiştir", "Yeni ad:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            try:
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
                
                if new_name.strip() in lists_data:
                    QMessageBox.warning(self, "Uyarı", "Bu isimde bir liste zaten var!")
                    return
                
                # Listeyi yeniden adlandır
                lists_data[new_name.strip()] = lists_data.pop(old_name)
                
                with open(self.lists_file, 'w', encoding='utf-8') as f:
                    json.dump(lists_data, f, ensure_ascii=False, indent=2)
                
                self.load_lists()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Liste adı değiştirilemedi: {e}")
    
    def delete_list(self, list_name):
        """Liste sil"""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{list_name}' listesini silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
                
                if list_name in lists_data:
                    del lists_data[list_name]
                
                with open(self.lists_file, 'w', encoding='utf-8') as f:
                    json.dump(lists_data, f, ensure_ascii=False, indent=2)
                
                self.load_lists()
                self.clear_plugin_table()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Liste silinemedi: {e}")
    
    def list_selected(self, item):
        """Liste seçildiğinde"""
        if item is None:
            return
            
        # Gerçek liste adını data'dan al
        self.current_list_name = item.data(Qt.ItemDataRole.UserRole)
        if not self.current_list_name:
            # Fallback: text'ten emoji'yi temizle
            self.current_list_name = item.text().split(' ', 1)[-1]
        
        self.plugin_list_title.setText(f"Liste: {self.current_list_name}")
        
        self.load_plugins_for_list(self.current_list_name)
        self.update_list_stats()
    
    def load_plugins_for_list(self, list_name):
        """Seçili liste için pluginleri yükle"""
        try:
            if not os.path.exists(self.lists_file):
                return
                
            with open(self.lists_file, 'r', encoding='utf-8') as f:
                lists_data = json.load(f)
            
            if list_name not in lists_data:
                return
            
            plugins = lists_data[list_name].get('plugins', [])
            self.display_plugins(plugins)
            
        except Exception as e:
            print(f"Plugin yükleme hatası: {e}")
            QMessageBox.warning(self, "Uyarı", f"Pluginler yüklenemedi: {e}")
    
    def display_plugins(self, plugins):
        """Pluginleri tabloda göster"""
        # API önceliğine göre sırala
        sorted_plugins = PluginSorter.sort_by_api_priority(plugins)
        self.plugins_table.setRowCount(len(sorted_plugins))
        
        for row, plugin in enumerate(sorted_plugins):
            # Seçim checkbox'ı
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_multi_buttons)
            self.plugins_table.setCellWidget(row, 0, checkbox)
            
            # İkon (cache'den veya varsayılan)
            api_type = plugin.get('api', 'N/A')
            icon_url = plugin.get('icon_url', '')
            icon_label = IconManager.create_cached_icon(icon_url, api_type, self.icon_cache, self.download_icon_async)
            self.plugins_table.setCellWidget(row, 1, icon_label)
            
            # Plugin bilgileri
            self.plugins_table.setItem(row, 2, QTableWidgetItem(plugin.get('name', 'N/A')))
            self.plugins_table.setItem(row, 3, QTableWidgetItem(plugin.get('current_version', 'N/A')))
            self.plugins_table.setItem(row, 4, QTableWidgetItem(plugin.get('api', 'N/A')))
            
            # İndir ve Git butonları
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            download_btn = QPushButton("İndir")
            download_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 4px 8px; }")
            download_btn.clicked.connect(lambda checked, p=plugin: self.download_single_plugin(p))
            button_layout.addWidget(download_btn)
            
            git_btn = QPushButton("Git")
            git_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px 8px; }")
            git_btn.clicked.connect(lambda checked, p=plugin: self.open_plugin_website(p))
            button_layout.addWidget(git_btn)
            
            self.plugins_table.setCellWidget(row, 5, button_widget)
    

    

    
    def clear_plugin_table(self):
        """Plugin tablosunu temizle"""
        self.plugins_table.setRowCount(0)
        self.plugin_list_title.setText("Plugin listesi seçin")
        self.current_list_name = None
    
    def update_list_stats(self):
        """Liste istatistiklerini güncelle"""
        if not self.current_list_name:
            self.list_stats_label.setText("Liste seçilmedi")
            return
            
        plugin_count = self.plugins_table.rowCount()
        self.list_stats_label.setText(f"Toplam plugin: {plugin_count}")
    
    def update_multi_buttons(self):
        """Çoklu işlem butonlarını güncelle"""
        selected_count = 0
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.download_selected_btn.setEnabled(selected_count > 0)
        self.remove_selected_btn.setEnabled(selected_count > 0)
        self.transfer_selected_btn.setEnabled(selected_count > 0)
        
        if selected_count > 0:
            self.download_selected_btn.setText(f"Seçilenleri İndir ({selected_count})")
            self.remove_selected_btn.setText(f"Seçilenleri Kaldır ({selected_count})")
            self.transfer_selected_btn.setText(f"Seçilenleri Aktar ({selected_count})")
        else:
            self.download_selected_btn.setText("Seçilenleri İndir")
            self.remove_selected_btn.setText("Seçilenleri Kaldır")
            self.transfer_selected_btn.setText("Seçilenleri Aktar")
    
    def select_all_plugins(self):
        """Tüm pluginleri seç"""
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
    
    def add_plugin_to_list(self, list_name, plugin_data):
        """Plugin'i listeye ekle"""
        try:
            if not os.path.exists(self.lists_file):
                lists_data = {}
            else:
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
            
            if list_name not in lists_data:
                lists_data[list_name] = {
                    'plugins': [],
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # Plugin zaten listede var mı kontrol et
            existing_plugins = lists_data[list_name]['plugins']
            for existing in existing_plugins:
                if (existing.get('name') == plugin_data.get('name') and 
                    existing.get('api') == plugin_data.get('api')):
                    QMessageBox.information(self, "Bilgi", "Bu plugin zaten listede mevcut!")
                    return False
            
            # Plugin'i ekle
            lists_data[list_name]['plugins'].append(plugin_data)
            lists_data[list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Dosyaya kaydet
            with open(self.lists_file, 'w', encoding='utf-8') as f:
                json.dump(lists_data, f, ensure_ascii=False, indent=2)
            
            # Eğer bu liste şu anda seçiliyse, tabloyu güncelle
            if self.current_list_name == list_name:
                self.load_plugins_for_list(list_name)
                self.update_list_stats()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Plugin listeye eklenemedi: {e}")
            return False
    
    def get_list_names(self):
        """Mevcut liste isimlerini döndür"""
        return self.list_manager.get_list_names()
    
    def download_single_plugin(self, plugin):
        """Tek plugin indir"""
        try:
            api_type = plugin.get('api', 'Modrinth')
            plugin_name = plugin.get('name', 'N/A')
            plugin_id = plugin.get('plugin_id', '')
            
            # Seçili sürümü al
            selected_version = plugin.get('version_data')
            if not selected_version:
                QMessageBox.warning(self, "Uyarı", f"{plugin_name} için sürüm verisi bulunamadı!")
                return
            
            # Plugin objesini oluştur (download_dialog için)
            if api_type == "Modrinth":
                plugin_obj = {
                    'title': plugin_name,
                    'project_id': plugin_id,
                    'slug': plugin_id,
                    '_api_source': 'Modrinth'
                }
            else:
                plugin_obj = {
                    'name': plugin_name,
                    'id': int(plugin_id),
                    '_api_source': 'Spigot'
                }
            
            # İndirme dialog'unu aç
            from .download_dialog import DownloadDialog
            dialog = DownloadDialog(plugin_obj, api_type, self)
            dialog.set_download_manager(self.download_manager)
            
            # Seçili sürümü ayarla
            dialog.versions = [selected_version]
            dialog.version_combo.clear()
            
            if api_type == "Modrinth":
                version_name = selected_version.get('version_number', 'N/A')
                game_versions = selected_version.get('game_versions', [])
                if game_versions:
                    display_name = f"{version_name} (MC: {', '.join(game_versions)})"
                else:
                    display_name = version_name
            else:
                version_name = selected_version.get('name', 'N/A')
                display_name = version_name
            
            dialog.version_combo.addItem(display_name, selected_version)
            dialog.version_combo.setCurrentIndex(0)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İndirme hatası: {e}")
    
    def remove_single_plugin(self, plugin, row):
        """Tek plugin kaldır"""
        plugin_name = plugin.get('name', 'N/A')
        
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{plugin_name}' pluginini listeden kaldırmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Liste verilerini yükle
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
                
                if self.current_list_name in lists_data:
                    plugins = lists_data[self.current_list_name]['plugins']
                    
                    if row < len(plugins):
                        # Plugin'i listeden çıkar
                        plugins.pop(row)
                        
                        # Güncellenmiş listeyi kaydet
                        lists_data[self.current_list_name]['plugins'] = plugins
                        lists_data[self.current_list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        with open(self.lists_file, 'w', encoding='utf-8') as f:
                            json.dump(lists_data, f, ensure_ascii=False, indent=2)
                        
                        # Tabloyu yenile
                        self.load_plugins_for_list(self.current_list_name)
                        self.update_list_stats()
                        
                        QMessageBox.information(self, "Başarılı", f"'{plugin_name}' listeden kaldırıldı.")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Plugin kaldırılamadı: {e}")
    
    def download_selected_plugins(self):
        """Seçili pluginleri indir"""
        try:
            selected_plugins = []
            
            # Seçili pluginleri topla
            for row in range(self.plugins_table.rowCount()):
                checkbox = self.plugins_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    # Liste verilerini al
                    with open(self.lists_file, 'r', encoding='utf-8') as f:
                        lists_data = json.load(f)
                    
                    if self.current_list_name in lists_data:
                        plugins = lists_data[self.current_list_name]['plugins']
                        if row < len(plugins):
                            plugin = plugins[row]
                            
                            # Plugin için sürüm bilgisini hazırla
                            api_type = plugin.get('api', 'Modrinth')
                            plugin_id = plugin.get('plugin_id', '')
                            version_type = plugin.get('version_type', 'latest')
                            
                            # Seçili sürümü al
                            selected_version = plugin.get('version_data')
                            if not selected_version:
                                continue
                            
                            # Plugin objesini oluştur
                            if api_type == "Modrinth":
                                plugin_obj = {
                                    'title': plugin.get('name'),
                                    'project_id': plugin_id,
                                    'slug': plugin_id,
                                    '_api_source': 'Modrinth'
                                }
                            else:
                                plugin_obj = {
                                    'name': plugin.get('name'),
                                    'id': int(plugin_id),
                                    '_api_source': 'Spigot'
                                }
                            
                            selected_plugins.append({
                                'plugin': plugin_obj,
                                'version': selected_version,
                                'api': api_type
                            })
            
            if not selected_plugins:
                QMessageBox.warning(self, "Uyarı", "İndirilecek plugin seçilmedi!")
                return
            
            # Çoklu indirme dialog'unu aç
            from .multi_download_dialog import MultiDownloadDialog
            dialog = MultiDownloadDialog(selected_plugins, self)
            dialog.set_download_manager(self.download_manager)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Çoklu indirme hatası: {e}")
    
    def open_plugin_website(self, plugin):
        """Plugin'in web sitesini aç"""
        try:
            import webbrowser
            
            api_type = plugin.get('api', 'Modrinth')
            plugin_id = plugin.get('plugin_id', '')
            
            if api_type == "Modrinth":
                # Modrinth URL'si
                if plugin_id:
                    url = f"https://modrinth.com/plugin/{plugin_id}"
                else:
                    QMessageBox.warning(self, "Uyarı", "Plugin ID bulunamadı!")
                    return
            else:  # Spigot
                # Spigot URL'si
                if plugin_id:
                    url = f"https://www.spigotmc.org/resources/{plugin_id}/"
                else:
                    QMessageBox.warning(self, "Uyarı", "Plugin ID bulunamadı!")
                    return
            
            webbrowser.open(url)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Web sitesi açılamadı: {e}")
    

    

    
    def change_sorting(self):
        """Sıralamayı değiştir"""
        try:
            current_priority = SettingsManager.get_api_priority()
            
            # Mevcut sıralamayı göster ve değiştirme seçenekleri sun
            options = ["Modrinth Önce", "Spigot Önce", "Rastgele"]
            current_index = 0
            if current_priority in options:
                current_index = options.index(current_priority)
            
            new_priority, ok = QInputDialog.getItem(
                self, 
                "Sıralama Değiştir", 
                "API Öncelik Sırası:", 
                options, 
                current_index, 
                False
            )
            
            if ok and new_priority != current_priority:
                # Ayarları güncelle
                if SettingsManager.update_api_priority(new_priority):
                    # Tabloyu yeniden yükle
                    if self.current_list_name:
                        self.load_plugins_for_list(self.current_list_name)
                    
                    QMessageBox.information(self, "Başarılı", f"Sıralama '{new_priority}' olarak değiştirildi.")
                else:
                    QMessageBox.critical(self, "Hata", "Sıralama ayarı kaydedilemedi!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sıralama değiştirilemedi: {e}")
    


    def remove_selected_plugins(self):
        """Seçili pluginleri kaldır"""
        selected_count = 0
        selected_rows = []
        
        # Seçili satırları topla
        for row in range(self.plugins_table.rowCount()):
            checkbox = self.plugins_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
                selected_rows.append(row)
        
        if selected_count == 0:
            QMessageBox.warning(self, "Uyarı", "Kaldırılacak plugin seçilmedi!")
            return
        
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{selected_count} plugini listeden kaldırmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Liste verilerini yükle
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
                
                if self.current_list_name in lists_data:
                    plugins = lists_data[self.current_list_name]['plugins']
                    
                    # Seçili pluginleri sil (tersten git ki index karışmasın)
                    for row in sorted(selected_rows, reverse=True):
                        if row < len(plugins):
                            plugins.pop(row)
                    
                    # Güncellenmiş listeyi kaydet
                    lists_data[self.current_list_name]['plugins'] = plugins
                    lists_data[self.current_list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    with open(self.lists_file, 'w', encoding='utf-8') as f:
                        json.dump(lists_data, f, ensure_ascii=False, indent=2)
                    
                    # Tabloyu yenile
                    self.load_plugins_for_list(self.current_list_name)
                    self.update_list_stats()
                    
                    QMessageBox.information(self, "Başarılı", f"{selected_count} plugin listeden kaldırıldı.")
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Pluginler kaldırılamadı: {e}")
    
 
   
    def create_new_list_from_dialog(self, name):
        """Dialog'dan yeni liste oluştur (basit versiyon)"""
        try:
            if os.path.exists(self.lists_file):
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    lists_data = json.load(f)
            else:
                lists_data = {}
            
            if name in lists_data:
                QMessageBox.warning(self, "Uyarı", "Bu isimde bir liste zaten var!")
                return False
            
            # Yeni liste oluştur (basit versiyon)
            lists_data[name] = {
                'plugins': [],
                'icon': '📋 Varsayılan',
                'description': '',
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Dosyaya kaydet
            with open(self.lists_file, 'w', encoding='utf-8') as f:
                json.dump(lists_data, f, ensure_ascii=False, indent=2)
            
            # UI'yi güncelle
            self.load_lists()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Liste oluşturulamadı: {e}")
            return False    
    
 
    def edit_list(self, list_name):
        """Liste düzenle"""
        try:
            with open(self.lists_file, 'r', encoding='utf-8') as f:
                lists_data = json.load(f)
            
            if list_name not in lists_data:
                QMessageBox.warning(self, "Uyarı", "Liste bulunamadı!")
                return
            
            list_info = lists_data[list_name]
            
            from .edit_list_dialog import EditListDialog
            dialog = EditListDialog(list_name, list_info, self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_list_data()
                
                # Liste adı değiştiyse
                if updated_data['name'] != list_name:
                    if updated_data['name'] in lists_data:
                        QMessageBox.warning(self, "Uyarı", "Bu isimde bir liste zaten var!")
                        return
                    
                    # Eski listeyi sil, yeni adla ekle
                    lists_data[updated_data['name']] = lists_data.pop(list_name)
                    list_name = updated_data['name']
                
                # Liste bilgilerini güncelle
                lists_data[list_name]['icon'] = updated_data['icon']
                lists_data[list_name]['description'] = updated_data['description']
                lists_data[list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Dosyaya kaydet
                with open(self.lists_file, 'w', encoding='utf-8') as f:
                    json.dump(lists_data, f, ensure_ascii=False, indent=2)
                
                # UI'yi güncelle
                self.load_lists()
                
                # Güncellenmiş listeyi seç
                for i in range(self.lists_widget.count()):
                    item = self.lists_widget.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == list_name:
                        self.lists_widget.setCurrentRow(i)
                        self.list_selected(item)
                        break
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Liste düzenlenemedi: {e}")
    
    def transfer_selected_plugins(self):
        """Seçili plugin'leri başka listeye aktar"""
        try:
            # Seçili plugin'leri topla
            selected_plugins = []
            selected_rows = []
            
            for row in range(self.plugins_table.rowCount()):
                checkbox = self.plugins_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)
            
            if not selected_rows:
                QMessageBox.warning(self, "Uyarı", "Aktarılacak plugin seçilmedi!")
                return
            
            # Mevcut liste verilerini al
            with open(self.lists_file, 'r', encoding='utf-8') as f:
                lists_data = json.load(f)
            
            if self.current_list_name not in lists_data:
                QMessageBox.warning(self, "Uyarı", "Kaynak liste bulunamadı!")
                return
            
            plugins = lists_data[self.current_list_name]['plugins']
            
            # Seçili plugin'leri al
            for row in selected_rows:
                if row < len(plugins):
                    selected_plugins.append(plugins[row])
            
            if not selected_plugins:
                QMessageBox.warning(self, "Uyarı", "Aktarılacak plugin bulunamadı!")
                return
            
            # Transfer dialog'unu aç
            from .transfer_plugins_dialog import TransferPluginsDialog
            dialog = TransferPluginsDialog(selected_plugins, self.get_list_names(), self.current_list_name, self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                transfer_data = dialog.get_transfer_data()
                target_list = transfer_data['target_list']
                transfer_mode = transfer_data['transfer_mode']
                plugins_to_transfer = transfer_data['plugins']
                
                # Plugin'leri aktar
                success, message = self.list_manager.transfer_plugins(
                    self.current_list_name, 
                    target_list, 
                    plugins_to_transfer
                )
                
                if success:
                    QMessageBox.information(self, "Başarılı", message)
                else:
                    QMessageBox.warning(self, "Uyarı", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Plugin aktarma hatası: {e}")