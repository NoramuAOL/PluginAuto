"""
Ayarlar yönetimi için utility fonksiyonları
"""

import json
import os

class SettingsManager:
    """Ayarlar yönetimi sınıfı"""
    
    @staticmethod
    def get_settings_file():
        """Ayarlar dosya yolunu döndür"""
        return "settings.json"
    
    @staticmethod
    def load_settings():
        """Ayarları yükle"""
        try:
            settings_file = SettingsManager.get_settings_file()
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return SettingsManager.get_default_settings()
        except Exception as e:
            print(f"Ayarlar yüklenemedi: {e}")
            return SettingsManager.get_default_settings()
    
    @staticmethod
    def save_settings(settings):
        """Ayarları kaydet"""
        try:
            settings_file = SettingsManager.get_settings_file()
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ayarlar kaydedilemedi: {e}")
            return False
    
    @staticmethod
    def get_default_settings():
        """Varsayılan ayarları döndür"""
        return {
            'default_folder': 'plugins',
            'concurrent_downloads': 3,
            'search_limit': 20,
            'default_api': 'Modrinth',
            'api_priority': 'Modrinth Önce',
            'show_premium_plugins': False
        }
    
    @staticmethod
    def get_api_priority():
        """API öncelik ayarını al"""
        settings = SettingsManager.load_settings()
        return settings.get('api_priority', 'Modrinth Önce')
    
    @staticmethod
    def update_api_priority(new_priority):
        """API öncelik ayarını güncelle"""
        settings = SettingsManager.load_settings()
        settings['api_priority'] = new_priority
        return SettingsManager.save_settings(settings)
    
    @staticmethod
    def get_show_premium_plugins():
        """Paralı pluginleri göster ayarını al"""
        settings = SettingsManager.load_settings()
        return settings.get('show_premium_plugins', False)