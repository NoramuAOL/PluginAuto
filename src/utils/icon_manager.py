"""
İkon yönetimi ve cache sistemi
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import weakref

class IconManager:
    """İkon yönetimi sınıfı"""
    
    @staticmethod
    def create_api_icon(api_type, size=48):
        """API ikonu oluştur"""
        icon_label = QLabel()
        icon_label.setFixedSize(size, size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if api_type == "Modrinth":
            icon_label.setText("M")
            icon_label.setStyleSheet(f"border: 1px solid #1bd96a; border-radius: 4px; background-color: #1bd96a; color: white; font-weight: bold; font-size: {size//3}px;")
        elif api_type == "Spigot":
            icon_label.setText("S")
            icon_label.setStyleSheet(f"border: 1px solid #f4a261; border-radius: 4px; background-color: #f4a261; color: white; font-weight: bold; font-size: {size//3}px;")
        else:
            icon_label.setText("?")
            icon_label.setStyleSheet(f"border: 1px solid #ccc; border-radius: 4px; background-color: #ccc; color: white; font-weight: bold; font-size: {size//3}px;")
        
        return icon_label
    
    @staticmethod
    def create_cached_icon(icon_url, api_type, icon_cache, download_callback=None, size=48):
        """Cache destekli ikon oluştur"""
        icon_label = QLabel()
        icon_label.setFixedSize(size, size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        
        # İkon URL'si varsa ve cache sistemimiz varsa
        if icon_url and icon_url.strip() and icon_cache is not None:
            # Cache'de var mı kontrol et
            if icon_url in icon_cache:
                # Cache'den al
                cached_pixmap = icon_cache[icon_url]
                if not cached_pixmap.isNull():
                    scaled_pixmap = cached_pixmap.scaled(size-2, size-2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                    return icon_label
            else:
                # Cache'de yok, arka planda indir
                if download_callback:
                    download_callback(icon_url, icon_label)
        
        # Varsayılan ikon (API'ye göre) - indirme sırasında gösterilecek
        if api_type == "Modrinth":
            icon_label.setText("M")
            icon_label.setStyleSheet(f"border: 1px solid #1bd96a; border-radius: 4px; background-color: #1bd96a; color: white; font-weight: bold; font-size: {size//3}px;")
        elif api_type == "Spigot":
            icon_label.setText("S")
            icon_label.setStyleSheet(f"border: 1px solid #f4a261; border-radius: 4px; background-color: #f4a261; color: white; font-weight: bold; font-size: {size//3}px;")
        else:
            icon_label.setText("?")
            icon_label.setStyleSheet(f"border: 1px solid #ccc; border-radius: 4px; background-color: #ccc; color: white; font-weight: bold; font-size: {size//3}px;")
        
        return icon_label

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
            self.icon_downloaded.emit(QPixmap())

class IconCacheMixin:
    """İkon cache işlemleri için mixin sınıfı"""
    
    def download_icon_async(self, icon_url, icon_label):
        """İkonu arka planda indir ve cache'e ekle"""
        if not hasattr(self, 'icon_workers'):
            self.icon_workers = {}
        
        # Aynı URL için zaten indirme varsa, tekrar başlatma
        if icon_url in self.icon_workers:
            existing_worker = self.icon_workers[icon_url]
            if existing_worker.isRunning():
                return
        
        # Worker thread oluştur
        worker = IconDownloadWorker(icon_url)
        
        # Weak reference kullanarak QLabel'ı tut (silinirse None olur)
        try:
            label_ref = weakref.ref(icon_label)
        except TypeError:
            # Bazı Qt objeleri weakref desteklemez, direkt referans kullan
            label_ref = lambda: icon_label
        
        worker.icon_downloaded.connect(lambda pixmap: self.on_icon_downloaded(icon_url, pixmap, label_ref))
        worker.finished.connect(lambda: self.cleanup_icon_worker(icon_url))
        worker.start()
        
        # Worker'ı dictionary'de tut
        self.icon_workers[icon_url] = worker
    
    def cleanup_icon_worker(self, icon_url):
        """İkon worker'ını temizle"""
        if hasattr(self, 'icon_workers') and icon_url in self.icon_workers:
            worker = self.icon_workers[icon_url]
            if not worker.isRunning():
                worker.deleteLater()
                del self.icon_workers[icon_url]
    
    def on_icon_downloaded(self, icon_url, pixmap, label_ref):
        """İkon indirildiğinde çağrılır"""
        # Weak reference'dan label'ı al
        try:
            icon_label = label_ref()
        except:
            icon_label = None
        
        if icon_label is None:
            # Label silinmiş, işlem yapma
            return
        
        if not pixmap.isNull() and hasattr(self, 'icon_cache') and self.icon_cache is not None:
            # Cache'e ekle
            self.icon_cache[icon_url] = pixmap
            
            try:
                # Label'ı güncelle
                size = icon_label.size()
                scaled_pixmap = pixmap.scaled(
                    size.width()-2, 
                    size.height()-2, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
                icon_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
                
                # Ana pencereye cache güncellemesini bildir
                main_window = self.window()
                if hasattr(main_window, 'update_cache_stats'):
                    main_window.update_cache_stats()
            except RuntimeError:
                # Label silinmiş, sessizce geç
                pass