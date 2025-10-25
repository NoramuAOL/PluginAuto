"""
Modrinth API ile plugin arama ve indirme işlemleri
"""

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
import aiohttp
import aiofiles
import asyncio
from typing import List, Dict, Optional
import os
import time

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Minecraft-Plugin-Downloader/1.0'
        })
        self._aio_session = None  # Lazy initialization for async session
    
    def search_plugins(self, query: str, limit: int = 20, include_premium: bool = False) -> List[Dict]:
        """Plugin arama"""
        url = f"{self.BASE_URL}/search"
        params = {
            'query': query,
            'limit': limit,
            'facets': '[["project_type:plugin"]]'
        }
        
        try:
            response = self.session.get(
                url, 
                params=params,
                timeout=(3.05, 27)  # (connect, read) timeout
            )
            response.raise_for_status()
            data = response.json()
            results = data.get('hits', [])
            
            # Modrinth genelde ücretsiz ama yine de kontrol et
            if not include_premium:
                # Eğer gelecekte premium özelliği eklenirse filtrele
                filtered_results = []
                for plugin in results:
                    # Modrinth'te şu an premium yok, ama ileride olabilir
                    is_premium = plugin.get('premium', False)
                    if not is_premium:
                        filtered_results.append(plugin)
                return filtered_results
            
            return results
            
        except Timeout:
            print(f"Modrinth arama timeout: {url}")
            return []
        except ConnectionError as e:
            print(f"Modrinth bağlantı hatası: {e}")
            return []
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                print("Modrinth rate limit, 5 saniye bekleniyor...")
                time.sleep(5)
                return self.search_plugins(query, limit)  # Retry
            print(f"Modrinth HTTP hatası: {e}")
            return []
        except Exception as e:
            print(f"Modrinth beklenmeyen hata: {e}")
            return []
    
    def get_plugin_details(self, plugin_id: str) -> Optional[Dict]:
        """Plugin detaylarını getir"""
        url = f"{self.BASE_URL}/project/{plugin_id}"
        
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
    
    def get_plugin_versions(self, plugin_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Plugin versiyonlarını getir"""
        url = f"{self.BASE_URL}/project/{plugin_id}/version"
        params = {
            'limit': min(limit, 100),  # Modrinth maksimum 100 limit
            'offset': offset
        }
        
        try:
            response = self.session.get(url, params=params, timeout=(3.05, 27))
            response.raise_for_status()
            versions = response.json()
            
            # Eğer limit 100'den fazlaysa, pagination ile daha fazla al
            if limit > 100 and len(versions) == 100:
                remaining = limit - 100
                next_offset = offset + 100
                
                while remaining > 0 and len(versions) % 100 == 0:
                    try:
                        next_params = {
                            'limit': min(remaining, 100),
                            'offset': next_offset
                        }
                        next_response = self.session.get(url, params=next_params, timeout=(3.05, 27))
                        next_response.raise_for_status()
                        
                        next_versions = next_response.json()
                        if not next_versions:
                            break
                            
                        versions.extend(next_versions)
                        remaining -= len(next_versions)
                        next_offset += len(next_versions)
                        
                        if len(next_versions) < 100:
                            break
                            
                    except Exception as e:
                        print(f"Pagination hatası: {e}")
                        break
            
            return versions
            
        except Timeout:
            print(f"Version listesi timeout: {plugin_id}")
            return []
        except HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limit, 5 saniye bekleniyor...")
                time.sleep(5)
                return self.get_plugin_versions(plugin_id, limit, offset)
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
    
    async def download_plugin(self, download_url: str, download_path: str, progress_callback=None) -> bool:
        """Plugin indirme"""
        try:
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            session = await self.get_aio_session()
            
            async with session.get(download_url) as response:
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
            print(f"İndirme timeout: {download_url}")
            return False
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return False
    
    def __del__(self):
        """Destructor - session'ları kapat"""
        if hasattr(self, 'session'):
            self.session.close()