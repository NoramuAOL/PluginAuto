"""
Spigot API ile plugin arama ve indirme işlemleri
"""

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
import aiohttp
import aiofiles
import asyncio
from typing import List, Dict, Optional
import os
import time

class SpigotAPI:
    BASE_URL = "https://api.spiget.org/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Minecraft-Plugin-Downloader/1.0'
        })
        self._aio_session = None  # Lazy initialization for async session
    
    def search_plugins(self, query: str, size: int = 20, include_premium: bool = False) -> List[Dict]:
        """Plugin arama"""
        url = f"{self.BASE_URL}/search/resources/{query}"
        params = {'size': size, 'sort': '-downloads'}
        
        try:
            response = self.session.get(url, params=params, timeout=(3.05, 27))
            response.raise_for_status()
            results = response.json()
            
            # Her plugin için detay bilgilerini al (ikon ve yazar için)
            filtered_results = []
            for plugin in results:
                plugin_id = plugin.get('id')
                if plugin_id:
                    try:
                        detail_url = f"{self.BASE_URL}/resources/{plugin_id}"
                        detail_response = self.session.get(detail_url, timeout=(3.05, 27))
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # Paralı plugin kontrolü
                            is_premium = detail_data.get('premium', False)
                            has_price = detail_data.get('price', 0) > 0
                            
                            # Paralı pluginleri filtrele (include_premium False ise)
                            if not include_premium and (is_premium or has_price):
                                continue
                            
                            if 'icon' in detail_data:
                                plugin['icon'] = detail_data['icon']
                            
                            if 'author' in detail_data:
                                plugin['author'] = detail_data['author']
                            
                            # Premium bilgisini ekle
                            plugin['premium'] = is_premium
                            plugin['price'] = detail_data.get('price', 0)
                            
                            filtered_results.append(plugin)
                    except:
                        # Hata durumunda plugin'i ekle (detay alınamazsa)
                        if include_premium:
                            filtered_results.append(plugin)
            
            return filtered_results
            
        except Timeout:
            print(f"Spigot arama timeout: {url}")
            return []
        except ConnectionError as e:
            print(f"Spigot bağlantı hatası: {e}")
            return []
        except HTTPError as e:
            if e.response.status_code == 429:
                print("Spigot rate limit, 5 saniye bekleniyor...")
                time.sleep(5)
                return self.search_plugins(query, size)
            print(f"Spigot HTTP hatası: {e}")
            return []
        except Exception as e:
            print(f"Spigot beklenmeyen hata: {e}")
            return []
    
    def get_plugin_details(self, plugin_id: int) -> Optional[Dict]:
        """Plugin detaylarını getir"""
        url = f"{self.BASE_URL}/resources/{plugin_id}"
        
        try:
            response = self.session.get(url, timeout=(3.05, 27))
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            print(f"Plugin detay timeout: {plugin_id}")
            return None
        except HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limit, 5 saniye bekleniyor...")
                time.sleep(5)
                return self.get_plugin_details(plugin_id)
            print(f"Plugin detay HTTP hatası: {e}")
            return None
        except Exception as e:
            print(f"Plugin detay hatası: {e}")
            return None
    
    def get_plugin_versions(self, plugin_id: int, size: int = 50) -> List[Dict]:
        """Plugin versiyonlarını getir"""
        url = f"{self.BASE_URL}/resources/{plugin_id}/versions"
        params = {'size': size, 'sort': '-id'}
        
        try:
            response = self.session.get(url, params=params, timeout=(3.05, 27))
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            print(f"Version listesi timeout: {plugin_id}")
            return []
        except HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limit, 5 saniye bekleniyor...")
                time.sleep(5)
                return self.get_plugin_versions(plugin_id, size)
            print(f"Version listesi HTTP hatası: {e}")
            return []
        except Exception as e:
            print(f"Version listesi hatası: {e}")
            return []
    
    async def get_aio_session(self):
        """Async session'ı lazy initialization ile al"""
        if self._aio_session is None or self._aio_session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=15
            )
            timeout = aiohttp.ClientTimeout(
                total=300,
                connect=30,
                sock_connect=30,
                sock_read=60
            )
            self._aio_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                connector_owner=True,
                headers={'User-Agent': 'Minecraft-Plugin-Downloader/1.0'}
            )
        return self._aio_session
    
    async def close_aio_session(self):
        """Async session'ı kapat"""
        if self._aio_session and not self._aio_session.closed:
            await self._aio_session.close()
            await asyncio.sleep(0.250)  # SSL bağlantıları için grace period
    
    async def download_plugin(self, plugin_id: int, version_id: int, download_path: str, progress_callback=None) -> bool:
        """Plugin indirme"""
        try:
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            url = f"{self.BASE_URL}/resources/{plugin_id}/versions/{version_id}/download"
            session = await self.get_aio_session()
            
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
        except asyncio.TimeoutError:
            print(f"İndirme timeout: {url}")
            return False
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return False
    
    def __del__(self):
        """Destructor - session'ları kapat"""
        if hasattr(self, 'session'):
            self.session.close()