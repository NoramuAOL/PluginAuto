"""
Modrinth API ile plugin arama ve indirme işlemleri
"""

import requests
import aiohttp
import aiofiles
import asyncio
from typing import List, Dict, Optional
import os

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Minecraft-Plugin-Downloader/1.0'
        })
    
    def search_plugins(self, query: str, limit: int = 20) -> List[Dict]:
        """Plugin arama"""
        try:
            url = f"{self.BASE_URL}/search"
            params = {
                'query': query,
                'limit': limit,
                'facets': '[["project_type:plugin"]]'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('hits', [])
        except Exception as e:
            print(f"Modrinth arama hatası: {e}")
            return []
    
    def get_plugin_details(self, plugin_id: str) -> Optional[Dict]:
        """Plugin detaylarını getir"""
        try:
            url = f"{self.BASE_URL}/project/{plugin_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Plugin detay hatası: {e}")
            return None
    
    def get_plugin_versions(self, plugin_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Plugin versiyonlarını getir"""
        try:
            url = f"{self.BASE_URL}/project/{plugin_id}/version"
            params = {
                'limit': min(limit, 100),  # Modrinth maksimum 100 limit
                'offset': offset
            }
            response = self.session.get(url, params=params)
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
                        next_response = self.session.get(url, params=next_params)
                        next_response.raise_for_status()
                        
                        next_versions = next_response.json()
                        if not next_versions:  # Daha fazla sürüm yok
                            break
                            
                        versions.extend(next_versions)
                        remaining -= len(next_versions)
                        next_offset += len(next_versions)
                        
                        # Sonsuz döngüyü önle
                        if len(next_versions) < 100:
                            break
                            
                    except Exception as e:
                        print(f"Pagination hatası: {e}")
                        break
            
            return versions
        except Exception as e:
            print(f"Version listesi hatası: {e}")
            return []
    
    async def download_plugin(self, download_url: str, download_path: str, progress_callback=None) -> bool:
        """Plugin indirme"""
        try:
            # İndirme klasörünü oluştur
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            # Windows için connector ayarları
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
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
        except Exception as e:
            print(f"İndirme hatası: {e}")
            return False