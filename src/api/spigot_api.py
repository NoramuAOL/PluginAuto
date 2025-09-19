"""
Spigot API ile plugin arama ve indirme işlemleri
"""

import requests
import aiohttp
import aiofiles
import asyncio
from typing import List, Dict, Optional
import os

class SpigotAPI:
    BASE_URL = "https://api.spiget.org/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Minecraft-Plugin-Downloader/1.0'
        })
    
    def search_plugins(self, query: str, size: int = 20) -> List[Dict]:
        """Plugin arama"""
        try:
            url = f"{self.BASE_URL}/search/resources/{query}"
            params = {'size': size, 'sort': '-downloads'}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            results = response.json()
            
            # Her plugin için detay bilgilerini al (ikon ve yazar için)
            for plugin in results:
                plugin_id = plugin.get('id')
                if plugin_id:
                    try:
                        # Plugin detaylarını al
                        detail_url = f"{self.BASE_URL}/resources/{plugin_id}"
                        detail_response = self.session.get(detail_url)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # İkon bilgisini ekle
                            if 'icon' in detail_data:
                                plugin['icon'] = detail_data['icon']
                            
                            # Yazar bilgisini ekle
                            if 'author' in detail_data:
                                plugin['author'] = detail_data['author']
                    except:
                        # Hata durumunda devam et
                        pass
            
            return results
        except Exception as e:
            print(f"Spigot arama hatası: {e}")
            return []
    
    def get_plugin_details(self, plugin_id: int) -> Optional[Dict]:
        """Plugin detaylarını getir"""
        try:
            url = f"{self.BASE_URL}/resources/{plugin_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Plugin detay hatası: {e}")
            return None
    
    def get_plugin_versions(self, plugin_id: int, size: int = 50) -> List[Dict]:
        """Plugin versiyonlarını getir"""
        try:
            url = f"{self.BASE_URL}/resources/{plugin_id}/versions"
            params = {'size': size, 'sort': '-id'}  # En yeni sürümler önce
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Version listesi hatası: {e}")
            return []
    
    async def download_plugin(self, plugin_id: int, version_id: int, download_path: str, progress_callback=None) -> bool:
        """Plugin indirme"""
        try:
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            url = f"{self.BASE_URL}/resources/{plugin_id}/versions/{version_id}/download"
            
            # Windows için connector ayarları
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        async with aiofiles.open(download_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(8192):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback and total_size > 0:
                                    progress = int((downloaded / total_size) * 100)
                                    progress_callback(progress)
                        
                        return True
            return False
        except asyncio.CancelledError:
            print("İndirme iptal edildi")
            return False
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return False