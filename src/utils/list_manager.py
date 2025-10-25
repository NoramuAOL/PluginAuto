"""
Plugin listesi yönetimi utilities
"""

import json
import os
from datetime import datetime

class ListManager:
    """Plugin listesi yönetimi sınıfı"""
    
    def __init__(self, lists_file="plugin_lists.json"):
        self.lists_file = lists_file
    
    def load_lists(self):
        """Plugin listelerini yükle"""
        try:
            if os.path.exists(self.lists_file):
                with open(self.lists_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Liste yükleme hatası: {e}")
            return {}
    
    def save_lists(self, lists_data):
        """Plugin listelerini kaydet"""
        try:
            with open(self.lists_file, 'w', encoding='utf-8') as f:
                json.dump(lists_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Liste kaydetme hatası: {e}")
            return False
    
    def get_list_names(self):
        """Mevcut liste isimlerini döndür"""
        lists_data = self.load_lists()
        return list(lists_data.keys())
    
    def create_list(self, name, icon="📋 Varsayılan", description="", custom_icon_path=""):
        """Yeni liste oluştur"""
        lists_data = self.load_lists()
        
        if name in lists_data:
            return False, "Bu isimde bir liste zaten var!"
        
        lists_data[name] = {
            'plugins': [],
            'icon': icon,
            'description': description,
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if custom_icon_path:
            lists_data[name]['custom_icon_path'] = custom_icon_path
        
        success = self.save_lists(lists_data)
        return success, "Liste başarıyla oluşturuldu." if success else "Liste oluşturulamadı."
    
    def delete_list(self, name):
        """Liste sil"""
        lists_data = self.load_lists()
        
        if name not in lists_data:
            return False, "Liste bulunamadı!"
        
        del lists_data[name]
        success = self.save_lists(lists_data)
        return success, "Liste başarıyla silindi." if success else "Liste silinemedi."
    
    def rename_list(self, old_name, new_name):
        """Liste adını değiştir"""
        lists_data = self.load_lists()
        
        if old_name not in lists_data:
            return False, "Kaynak liste bulunamadı!"
        
        if new_name in lists_data:
            return False, "Bu isimde bir liste zaten var!"
        
        lists_data[new_name] = lists_data.pop(old_name)
        lists_data[new_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = self.save_lists(lists_data)
        return success, "Liste adı başarıyla değiştirildi." if success else "Liste adı değiştirilemedi."
    
    def update_list(self, name, icon=None, description=None, custom_icon_path=None):
        """Liste bilgilerini güncelle"""
        lists_data = self.load_lists()
        
        if name not in lists_data:
            return False, "Liste bulunamadı!"
        
        if icon is not None:
            lists_data[name]['icon'] = icon
        
        if description is not None:
            lists_data[name]['description'] = description
        
        if custom_icon_path is not None:
            lists_data[name]['custom_icon_path'] = custom_icon_path
        
        lists_data[name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = self.save_lists(lists_data)
        return success, "Liste başarıyla güncellendi." if success else "Liste güncellenemedi."
    
    def add_plugin_to_list(self, list_name, plugin_data):
        """Plugin'i listeye ekle"""
        lists_data = self.load_lists()
        
        if list_name not in lists_data:
            return False, "Liste bulunamadı!"
        
        # Plugin zaten listede var mı kontrol et
        existing_plugins = lists_data[list_name]['plugins']
        for existing in existing_plugins:
            if (existing.get('name') == plugin_data.get('name') and 
                existing.get('api') == plugin_data.get('api')):
                return False, "Bu plugin zaten listede mevcut!"
        
        # Plugin'i ekle
        lists_data[list_name]['plugins'].append(plugin_data)
        lists_data[list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = self.save_lists(lists_data)
        return success, "Plugin başarıyla eklendi." if success else "Plugin eklenemedi."
    
    def remove_plugin_from_list(self, list_name, plugin_index):
        """Plugin'i listeden çıkar"""
        lists_data = self.load_lists()
        
        if list_name not in lists_data:
            return False, "Liste bulunamadı!"
        
        plugins = lists_data[list_name]['plugins']
        
        if plugin_index >= len(plugins):
            return False, "Plugin bulunamadı!"
        
        plugins.pop(plugin_index)
        lists_data[list_name]['plugins'] = plugins
        lists_data[list_name]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = self.save_lists(lists_data)
        return success, "Plugin başarıyla kaldırıldı." if success else "Plugin kaldırılamadı."
    
    def transfer_plugins(self, source_list, target_list, plugins_to_transfer):
        """Plugin'leri bir listeden diğerine aktar"""
        lists_data = self.load_lists()
        
        if source_list not in lists_data:
            return False, "Kaynak liste bulunamadı!"
        
        if target_list not in lists_data:
            return False, "Hedef liste bulunamadı!"
        
        target_plugins = lists_data[target_list]['plugins']
        added_count = 0
        
        for plugin in plugins_to_transfer:
            # Aynı plugin zaten var mı kontrol et
            exists = False
            for existing in target_plugins:
                if (existing.get('name') == plugin.get('name') and 
                    existing.get('api') == plugin.get('api')):
                    exists = True
                    break
            
            if not exists:
                target_plugins.append(plugin)
                added_count += 1
        
        # Hedef listeyi güncelle
        lists_data[target_list]['plugins'] = target_plugins
        lists_data[target_list]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        success = self.save_lists(lists_data)
        
        if success:
            message = f"{added_count} plugin '{target_list}' listesine aktarıldı."
            if len(plugins_to_transfer) - added_count > 0:
                message += f"\n{len(plugins_to_transfer) - added_count} plugin zaten mevcuttu."
            return True, message
        else:
            return False, "Plugin'ler aktarılamadı."