"""
Plugin sıralama ve filtreleme utilities
"""

from .settings_manager import SettingsManager

class PluginSorter:
    """Plugin sıralama işlemleri"""
    
    @staticmethod
    def sort_by_api_priority(items, api_key='api'):
        """Plugin'leri/indirmeleri API önceliğine göre sırala"""
        api_priority = SettingsManager.get_api_priority()
        
        if api_priority == "Modrinth Önce":
            # Önce Modrinth, sonra Spigot
            modrinth_items = [item for item in items if item.get(api_key) == 'Modrinth']
            spigot_items = [item for item in items if item.get(api_key) == 'Spigot']
            other_items = [item for item in items if item.get(api_key) not in ['Modrinth', 'Spigot']]
            return modrinth_items + spigot_items + other_items
        elif api_priority == "Spigot Önce":
            # Önce Spigot, sonra Modrinth
            spigot_items = [item for item in items if item.get(api_key) == 'Spigot']
            modrinth_items = [item for item in items if item.get(api_key) == 'Modrinth']
            other_items = [item for item in items if item.get(api_key) not in ['Modrinth', 'Spigot']]
            return spigot_items + modrinth_items + other_items
        else:  # Rastgele veya diğer
            return items
    
    @staticmethod
    def sort_search_results(modrinth_results, spigot_results):
        """Arama sonuçlarını API önceliğine göre sırala"""
        api_priority = SettingsManager.get_api_priority()
        
        # Sonuçları işaretle
        for result in modrinth_results:
            result['_api_source'] = 'Modrinth'
        
        for result in spigot_results:
            result['_api_source'] = 'Spigot'
        
        if api_priority == "Modrinth Önce":
            # Önce Modrinth, sonra Spigot
            return modrinth_results + spigot_results
        elif api_priority == "Spigot Önce":
            # Önce Spigot, sonra Modrinth
            return spigot_results + modrinth_results
        else:  # Rastgele
            # Karıştır
            all_results = modrinth_results + spigot_results
            import random
            random.shuffle(all_results)
            return all_results