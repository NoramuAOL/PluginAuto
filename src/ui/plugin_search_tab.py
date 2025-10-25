"""
Plugin arama sekmesi
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                            QComboBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot
import asyncio

from ..api.modrinth_api import ModrinthAPI
from ..api.spigot_api import SpigotAPI
from .download_dialog import DownloadDialog
from ..utils import SettingsManager, IconManager, IconCacheMixin, PluginSorter



class SearchWorker(QObject):
    """Worker object for plugin search - PyQt6 best practice"""
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, api_type, query):
        super().__init__()
        self.api_type = api_type
        self.query = query
    
    @pyqtSlot()
    def do_work(self):
        """Arama işlemini gerçekleştir"""
        try:
            results = []
            
            # Paralı plugin ayarını al
            show_premium = SettingsManager.get_show_premium_plugins()
            
            if self.api_type == "Karışık":
                # Hem Modrinth hem Spigot'tan ara
                modrinth_api = ModrinthAPI()
                spigot_api = SpigotAPI()
                
                modrinth_results = modrinth_api.search_plugins(self.query, limit=10, include_premium=show_premium)
                spigot_results = spigot_api.search_plugins(self.query, size=10, include_premium=show_premium)
                
                # Modrinth sonuçlarını işaretle
                for result in modrinth_results:
                    result['_api_source'] = 'Modrinth'
                
                # Spigot sonuçlarını işaretle
                for result in spigot_results:
                    result['_api_source'] = 'Spigot'
                
                # API önceliğine göre sırala
                results = PluginSorter.sort_search_results(modrinth_results, spigot_results)
                
            elif self.api_type == "Modrinth":
                api = ModrinthAPI()
                results = api.search_plugins(self.query, include_premium=show_premium)
                for result in results:
                    result['_api_source'] = 'Modrinth'
            else:  # Spigot
                api = SpigotAPI()
                results = api.search_plugins(self.query, include_premium=show_premium)
                for result in results:
                    result['_api_source'] = 'Spigot'
            
            self.results_ready.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

class PluginSearchTab(QWidget, IconCacheMixin):
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
        
        # Önceki worker'ı temizle
        self.cleanup_worker()
        
        # Arama butonunu devre dışı bırak
        self.search_button.setEnabled(False)
        self.search_button.setText("Aranıyor...")
        
        # Worker object pattern (PyQt6 best practice)
        self.search_thread = QThread()
        self.search_worker = SearchWorker(api_type, query)
        self.search_worker.moveToThread(self.search_thread)
        
        # Bağlantılar
        self.search_thread.started.connect(self.search_worker.do_work)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.error_occurred.connect(self.handle_error)
        self.search_worker.finished.connect(self.search_finished)
        
        self.search_thread.start()
    
    def cleanup_worker(self):
        """Worker'ı güvenli şekilde temizle"""
        if hasattr(self, 'search_thread'):
            try:
                if self.search_thread.isRunning():
                    self.search_thread.quit()
                    self.search_thread.wait(5000)  # 5 saniye bekle
                    if self.search_thread.isRunning():
                        print("Warning: Search thread did not stop gracefully")
            except RuntimeError:
                # Thread zaten silinmiş, sorun değil
                pass
    
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
            icon_label = IconManager.create_cached_icon(icon_url, api_source, self.icon_cache, self.download_icon_async)
            self.results_table.setCellWidget(row, 1, icon_label)
            
            self.results_table.setItem(row, 2, QTableWidgetItem(name))
            self.results_table.setItem(row, 3, QTableWidgetItem(description))
            self.results_table.setItem(row, 4, QTableWidgetItem(author))
            self.results_table.setItem(row, 5, QTableWidgetItem(api_source))
            self.results_table.setItem(row, 6, QTableWidgetItem(str(downloads)))
            
            # İndir ve Git butonları
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            download_btn = QPushButton("İndir")
            download_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 4px 8px; }")
            download_btn.clicked.connect(lambda checked, p=plugin: self.download_plugin(p))
            button_layout.addWidget(download_btn)
            
            git_btn = QPushButton("Git")
            git_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px 8px; }")
            git_btn.clicked.connect(lambda checked, p=plugin: self.open_plugin_website(p))
            button_layout.addWidget(git_btn)
            
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
    
    def open_plugin_website(self, plugin):
        """Plugin'in web sitesini aç"""
        try:
            import webbrowser
            
            api_source = plugin.get('_api_source', self.api_combo.currentText())
            
            if api_source == "Modrinth":
                # Modrinth URL'si
                project_id = plugin.get('project_id') or plugin.get('slug', '')
                if project_id:
                    url = f"https://modrinth.com/plugin/{project_id}"
                else:
                    QMessageBox.warning(self, "Uyarı", "Plugin ID bulunamadı!")
                    return
            else:  # Spigot
                # Spigot URL'si
                plugin_id = plugin.get('id', '')
                if plugin_id:
                    url = f"https://www.spigotmc.org/resources/{plugin_id}/"
                else:
                    QMessageBox.warning(self, "Uyarı", "Plugin ID bulunamadı!")
                    return
            
            webbrowser.open(url)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Web sitesi açılamadı: {e}")  
  
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

