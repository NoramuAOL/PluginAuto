"""
Plugin arama sekmesi
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                            QComboBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import asyncio

from ..api.modrinth_api import ModrinthAPI
from ..api.spigot_api import SpigotAPI
from .download_dialog import DownloadDialog



class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_type, query):
        super().__init__()
        self.api_type = api_type
        self.query = query
        
    def run(self):
        try:
            results = []
            
            if self.api_type == "Karışık":
                # Hem Modrinth hem Spigot'tan ara
                modrinth_api = ModrinthAPI()
                spigot_api = SpigotAPI()
                
                modrinth_results = modrinth_api.search_plugins(self.query, limit=10)
                spigot_results = spigot_api.search_plugins(self.query, size=10)
                
                # Modrinth sonuçlarını işaretle
                for result in modrinth_results:
                    result['_api_source'] = 'Modrinth'
                    results.append(result)
                
                # Spigot sonuçlarını işaretle
                for result in spigot_results:
                    result['_api_source'] = 'Spigot'
                    results.append(result)
                
                # Karıştır
                import random
                random.shuffle(results)
                
            elif self.api_type == "Modrinth":
                api = ModrinthAPI()
                results = api.search_plugins(self.query)
                for result in results:
                    result['_api_source'] = 'Modrinth'
            else:  # Spigot
                api = SpigotAPI()
                results = api.search_plugins(self.query)
                for result in results:
                    result['_api_source'] = 'Spigot'
            
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))

class PluginSearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.download_manager = None
        self.lists_tab = None
        self.current_results = []
        self.selected_plugins = set()  # Seçili pluginleri sakla
        self.icon_cache = None  # İkon cache referansı
        self.init_ui()
    
    def set_download_manager(self, download_manager):
        """Download manager referansını ayarla"""
        self.download_manager = download_manager
    
    def set_lists_tab(self, lists_tab):
        """Lists tab referansını ayarla"""
        self.lists_tab = lists_tab
    
    def set_icon_cache(self, icon_cache):
        """İkon cache referansını ayarla"""
        self.icon_cache = icon_cache
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Arama bölümü
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("API:"))
        self.api_combo = QComboBox()
        self.api_combo.addItems(["Karışık", "Modrinth", "Spigot"])
        search_layout.addWidget(self.api_combo)
        
        search_layout.addWidget(QLabel("Arama:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Plugin adı girin...")
        self.search_input.returnPressed.connect(self.search_plugins)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Ara")
        self.search_button.clicked.connect(self.search_plugins)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Çoklu indirme butonları
        multi_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.clicked.connect(self.select_all_results)
        multi_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Seçimi Kaldır")
        deselect_all_btn.clicked.connect(self.deselect_all_results)
        multi_layout.addWidget(deselect_all_btn)
        
        multi_layout.addStretch()
        
        self.multi_download_btn = QPushButton("Seçilenleri İndir")
        self.multi_download_btn.clicked.connect(self.download_selected_plugins)
        self.multi_download_btn.setEnabled(False)
        multi_layout.addWidget(self.multi_download_btn)
        
        layout.addLayout(multi_layout)
        
        # Sonuçlar tablosu
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Seç", "İkon", "Ad", "Açıklama", "Yazar", "API", "İndirme", "Aksiyon"
        ])
        
        # Tablo ayarları
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # İkon
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Ad
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Açıklama
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Yazar
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # API
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # İndirme
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Aksiyon
        
        # Sütun genişlikleri
        self.results_table.setColumnWidth(0, 50)   # Seç
        self.results_table.setColumnWidth(1, 70)   # İkon
        self.results_table.setColumnWidth(2, 200)  # Ad
        self.results_table.setColumnWidth(4, 120)  # Yazar
        self.results_table.setColumnWidth(5, 80)   # API
        self.results_table.setColumnWidth(6, 80)   # İndirme
        self.results_table.setColumnWidth(7, 150)  # Aksiyon
        
        # Satır yüksekliği
        self.results_table.verticalHeader().setDefaultSectionSize(60)
        
        # Sağ tık menüsü
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.results_table)
        
    def search_plugins(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Uyarı", "Lütfen arama terimi girin!")
            return
            
        api_type = self.api_combo.currentText()
        
        # Önceki worker'ı durdur
        if hasattr(self, 'search_worker') and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
        
        # Arama butonunu devre dışı bırak
        self.search_button.setEnabled(False)
        self.search_button.setText("Aranıyor...")
        
        # Worker thread başlat
        self.search_worker = SearchWorker(api_type, query)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.error_occurred.connect(self.handle_error)
        self.search_worker.finished.connect(self.search_finished)
        self.search_worker.start()
    
    def search_finished(self):
        """Arama tamamlandığında çağrılır"""
        self.search_button.setEnabled(True)
        self.search_button.setText("Ara")
        
    def display_results(self, results):
        self.results_table.setRowCount(len(results))
        self.current_results = results  # Sonuçları sakla
        
        for row, plugin in enumerate(results):
            # API kaynağını belirle
            api_source = plugin.get('_api_source', self.api_combo.currentText())
            
            if api_source == "Modrinth":
                name = plugin.get('title', 'N/A')
                description = plugin.get('description', 'N/A')
                author = plugin.get('author', 'N/A')
                downloads = plugin.get('downloads', 0)
                icon_url = plugin.get('icon_url', '')
                plugin_id = plugin.get('project_id') or plugin.get('slug', '')
                    
            else:  # Spigot
                name = plugin.get('name', 'N/A')
                description = plugin.get('tag', 'N/A')
                
                # Yazar bilgisini güvenli şekilde al
                author_info = plugin.get('author')
                if isinstance(author_info, dict):
                    author = author_info.get('username', author_info.get('name', 'Bilinmeyen'))
                elif isinstance(author_info, str):
                    author = author_info
                else:
                    # Debug için author bilgisini yazdır
                    print(f"Plugin: {name}, Author data: {author_info}, Type: {type(author_info)}")
                    author = 'Bilinmeyen'
                downloads = plugin.get('downloads', 0)
                
                # Spigot ikon URL'sini oluştur
                icon_data = plugin.get('icon', {})
                icon_url = ''
                
                if icon_data:
                    try:
                        if isinstance(icon_data, dict) and 'url' in icon_data:
                            url = icon_data['url']
                            if url.startswith('http'):
                                icon_url = url
                            elif url.startswith('/'):
                                icon_url = f"https://www.spigotmc.org{url}"
                            else:
                                icon_url = f"https://www.spigotmc.org/{url}"
                    except:
                        pass
                
                # Spigot için şimdilik varsayılan ikon kullan (API karmaşık)
                # Gelecekte daha detaylı ikon desteği eklenebilir
                if not icon_url:
                    icon_url = ''  # Varsayılan S ikonu kullanılacak
                    
                plugin_id = str(plugin.get('id', ''))
            
            # Seçim checkbox'ı
            from PyQt6.QtWidgets import QCheckBox
            checkbox = QCheckBox()
            
            # Önceki seçimi koru
            plugin_key = f"{api_source}:{plugin_id}"
            if plugin_key in self.selected_plugins:
                checkbox.setChecked(True)
            
            checkbox.stateChanged.connect(lambda state, key=plugin_key: self.handle_selection_change(state, key))
            self.results_table.setCellWidget(row, 0, checkbox)
            
            # İkon
            icon_label = self.create_icon_label(icon_url, api_source)
            self.results_table.setCellWidget(row, 1, icon_label)
            
            self.results_table.setItem(row, 2, QTableWidgetItem(name))
            self.results_table.setItem(row, 3, QTableWidgetItem(description))
            self.results_table.setItem(row, 4, QTableWidgetItem(author))
            self.results_table.setItem(row, 5, QTableWidgetItem(api_source))
            self.results_table.setItem(row, 6, QTableWidgetItem(str(downloads)))
            
            # İndir butonu ve çıkar butonu
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            download_btn = QPushButton("İndir")
            download_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 4px 8px; }")
            download_btn.clicked.connect(lambda checked, p=plugin: self.download_plugin(p))
            button_layout.addWidget(download_btn)
            
            remove_btn = QPushButton("Çıkar")
            remove_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; padding: 4px 8px; }")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_plugin_from_results(r))
            button_layout.addWidget(remove_btn)
            
            self.results_table.setCellWidget(row, 7, button_widget)
        
        # Buton durumu search_finished'da ayarlanacak
        
    def handle_error(self, error_msg):
        QMessageBox.critical(self, "Hata", f"Arama hatası: {error_msg}")
        # Buton durumu search_finished'da ayarlanacak
        
    def download_plugin(self, plugin):
        api_source = plugin.get('_api_source', self.api_combo.currentText())
        dialog = DownloadDialog(plugin, api_source, self)
        dialog.set_download_manager(self.download_manager)
        dialog.exec()  
  
    def select_all_results(self):
        """Tüm sonuçları seç"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_results(self):
        """Tüm seçimleri kaldır"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def update_multi_download_button(self):
        """Çoklu indirme butonunu güncelle"""
        selected_count = 0
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.multi_download_btn.setEnabled(selected_count > 0)
        if selected_count > 0:
            self.multi_download_btn.setText(f"Seçilenleri İndir ({selected_count})")
        else:
            self.multi_download_btn.setText("Seçilenleri İndir")
    
    def download_selected_plugins(self):
        """Seçili pluginleri indir"""
        try:
            selected_plugins = []
            
            for row in range(self.results_table.rowCount()):
                checkbox = self.results_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    plugin = self.current_results[row]
                    api_source = plugin.get('_api_source', self.api_combo.currentText())
                    
                    # Plugin için en son versiyonu al
                    if api_source == "Modrinth":
                        from ..api.modrinth_api import ModrinthAPI
                        api = ModrinthAPI()
                        plugin_id = plugin.get('project_id') or plugin.get('slug')
                        versions = api.get_plugin_versions(plugin_id)
                    else:
                        from ..api.spigot_api import SpigotAPI
                        api = SpigotAPI()
                        plugin_id = plugin.get('id')
                        versions = api.get_plugin_versions(plugin_id)
                    
                    if versions:
                        latest_version = versions[0]  # İlk versiyon genellikle en son
                        selected_plugins.append({
                            'plugin': plugin,
                            'version': latest_version,
                            'api': api_source
                        })
            
            if not selected_plugins:
                QMessageBox.warning(self, "Uyarı", "Seçili plugin bulunamadı!")
                return
            
            # Çoklu indirme dialog'unu aç
            from .multi_download_dialog import MultiDownloadDialog
            dialog = MultiDownloadDialog(selected_plugins, self)
            dialog.set_download_manager(self.download_manager)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Çoklu indirme hatası: {e}")    
   
    def create_icon_label(self, icon_url, api_source):
        """Plugin ikonu oluştur (cache desteği ile)"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt, QThread, pyqtSignal
        import requests
        
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        
        # İkon URL'si varsa ve cache sistemimiz varsa
        if icon_url and icon_url.strip() and self.icon_cache is not None:
            # Cache'de var mı kontrol et
            if icon_url in self.icon_cache:
                # Cache'den al
                cached_pixmap = self.icon_cache[icon_url]
                if not cached_pixmap.isNull():
                    scaled_pixmap = cached_pixmap.scaled(46, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                    return icon_label
            else:
                # Cache'de yok, arka planda indir
                self.download_icon_async(icon_url, icon_label)
        
        # Varsayılan ikon (API'ye göre) - indirme sırasında gösterilecek
        if api_source == "Modrinth":
            icon_label.setText("M")
            icon_label.setStyleSheet("border: 1px solid #1bd96a; border-radius: 4px; background-color: #1bd96a; color: white; font-weight: bold; font-size: 16px;")
        else:
            icon_label.setText("S")
            icon_label.setStyleSheet("border: 1px solid #f4a261; border-radius: 4px; background-color: #f4a261; color: white; font-weight: bold; font-size: 16px;")
        
        return icon_label
    
    def download_icon_async(self, icon_url, icon_label):
        """İkonu arka planda indir ve cache'e ekle"""
        if not hasattr(self, 'icon_workers'):
            self.icon_workers = []
        
        # Worker thread oluştur
        worker = IconDownloadWorker(icon_url)
        worker.icon_downloaded.connect(lambda pixmap: self.on_icon_downloaded(icon_url, pixmap, icon_label))
        worker.start()
        
        # Worker'ı listede tut (garbage collection'dan korunmak için)
        self.icon_workers.append(worker)
        
        # Eski worker'ları temizle
        self.icon_workers = [w for w in self.icon_workers if w.isRunning()]
    
    def on_icon_downloaded(self, icon_url, pixmap, icon_label):
        """İkon indirildiğinde çağrılır"""
        if not pixmap.isNull() and self.icon_cache is not None:
            # Cache'e ekle
            self.icon_cache[icon_url] = pixmap
            
            # Label'ı güncelle
            scaled_pixmap = pixmap.scaled(46, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
            
            # Ana pencereye cache güncellemesini bildir
            main_window = self.window()
            if hasattr(main_window, 'update_cache_stats'):
                main_window.update_cache_stats()
    
    def handle_selection_change(self, state, plugin_key):
        """Seçim değişikliğini işle"""
        if state == 2:  # Checked
            self.selected_plugins.add(plugin_key)
        else:  # Unchecked
            self.selected_plugins.discard(plugin_key)
        
        self.update_multi_download_button()
    
    def remove_plugin_from_results(self, row):
        """Plugin'i sonuçlardan çıkar"""
        if row < len(self.current_results):
            # Seçimden de çıkar
            plugin = self.current_results[row]
            api_source = plugin.get('_api_source', self.api_combo.currentText())
            
            if api_source == "Modrinth":
                plugin_id = plugin.get('project_id') or plugin.get('slug', '')
            else:
                plugin_id = str(plugin.get('id', ''))
            
            plugin_key = f"{api_source}:{plugin_id}"
            self.selected_plugins.discard(plugin_key)
            
            # Listeden çıkar
            self.current_results.pop(row)
            
            # Tabloyu yeniden oluştur
            self.display_results(self.current_results)    
   
    def show_context_menu(self, position):
        """Sağ tık menüsünü göster"""
        if not self.lists_tab:
            return
            
        item = self.results_table.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        if row >= len(self.current_results):
            return
        
        plugin = self.current_results[row]
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        add_to_list_action = menu.addAction("Listeye Ekle")
        add_to_list_action.triggered.connect(lambda: self.add_plugin_to_list(plugin))
        
        menu.exec(self.results_table.mapToGlobal(position))
    
    def add_plugin_to_list(self, plugin):
        """Plugin'i listeye ekleme dialog'unu aç"""
        if not self.lists_tab:
            QMessageBox.warning(self, "Uyarı", "Plugin Listeleri sekmesi bulunamadı!")
            return
        
        from .add_to_list_dialog import AddToListDialog
        dialog = AddToListDialog(plugin, self.lists_tab, self)
        dialog.exec()
class IconDownloadWorker(QThread):
    """İkon indirme worker thread'i"""
    icon_downloaded = pyqtSignal(object)  # QPixmap signal
    
    def __init__(self, icon_url):
        super().__init__()
        self.icon_url = icon_url
        
    def run(self):
        """İkonu indir"""
        try:
            import requests
            from PyQt6.QtGui import QPixmap
            
            headers = {
                'User-Agent': 'Minecraft-Plugin-Downloader/1.0'
            }
            response = requests.get(self.icon_url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.icon_downloaded.emit(pixmap)
            else:
                self.icon_downloaded.emit(QPixmap())
        except Exception as e:
            print(f"İkon indirme hatası ({self.icon_url}): {e}")
            from PyQt6.QtGui import QPixmap
            self.icon_downloaded.emit(QPixmap())
