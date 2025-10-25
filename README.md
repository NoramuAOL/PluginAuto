# 🎮 PluginAuto | Server Setuper'ler için devrim

Minecraft sunucu yöneticileri için geliştirilmiş, **plugin indirme ve yönetim** uygulaması. Spigot ve Modrinth platformlarından kolayca plugin arayın, indirin ve listeler oluşturun!

**Not:** Program artık `.exe` halinde! İndirip çalıştırmanız yeterli. Kaynak kodları da açık, dilediğiniz gibi inceleyebilirsiniz.

---

## 🚀 Özellikler

### 🔍 Akıllı Plugin Arama
- **Spigot** ve **Modrinth** platformlarından arama
- **Karışık Arama**: Hangi platformda olduğunu bilmiyorsanız, her ikisinden birden arayın
- **Paralı Plugin Filtresi**: Sadece ücretsiz pluginleri görebilirsiniz
- **API Sıralama**: Arama sonuçlarını istediğiniz sıraya göre düzenleyin

### 📋 Plugin Listeleri
**EN ÖNEMLİ ÖZELLİK!** 
- Farklı sunucular için ayrı listeler oluşturun
- Pluginleri listelere ekleyin
- **Tek tıkla tüm listeyi indirin** veya tek tek seçin
- Özel ikon ekleyebilirsiniz
- Listeler arası plugin transferi

### 💾 İndirme Yöneticisi
- Tüm indirme geçmişiniz kaydedilir
- Önceden indirdiğiniz pluginleri tekrar indirebilirsiniz
- Toplu yeniden indirme
- Her plugin için direkt web sitesine git butonu
- İndirme klasörünü açma

### ⚡ Performans
- **İkon Cache**: Plugin ikonları önbelleklenir, daha hızlı yükleme
- **Otomatik Güncelleme**: Her zaman son sürüm indirilebilir
- **Çoklu İndirme**: Aynı anda birden fazla plugin indirin
- **Hızlı Arama**: Optimize edilmiş API istekleri

### 🎨 Modern Arayüz
- Temiz ve kullanıcı dostu tasarım
- Karanlık tema uyumlu
- Sezgisel kontroller
- Türkçe dil desteği

---

## 📥 Kurulum

### Windows (.exe)
1. [Releases](../../releases) sayfasından son sürümü indirin
2. `.exe` dosyasını çalıştırın
3. Hepsi bu kadar!

### Kaynak Koddan (Python)
```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Programı çalıştırın
python main.py
```

---

## 🎯 Nasıl Kullanılır?

### 1️⃣ Plugin Arama
- **Plugin Arama** sekmesine gidin
- API seçin (Modrinth / Spigot / Karışık)
- Plugin adını yazın ve "Ara" butonuna tıklayın
- İstediğiniz plugini seçip indirin

### 2️⃣ Liste Oluşturma
- **Plugin Listeleri** sekmesine gidin
- "Yeni Liste" butonuna tıklayın
- Liste adı ve ikon seçin
- Pluginleri arayıp sağ tıklayarak "Listeye Ekle" seçin

### 3️⃣ Toplu İndirme
- Listenizden pluginleri seçin
- "Seçilenleri İndir" butonuna tıklayın
- Tüm pluginler otomatik indirilir

### 4️⃣ Ayarlar
- **Ayarlar** sekmesinden:
  - İndirme klasörünü değiştirin
  - API önceliğini ayarlayın
  - Paralı pluginleri göster/gizle
  - Arama limiti belirleyin

---

## 🛠️ Teknik Detaylar

- **Dil**: Python 3.11+
- **GUI**: PyQt6
- **API**: Spigot (Spiget) & Modrinth v2
- **Async**: aiohttp, qasync
- **Platform**: Windows

---

## 🤝 Destek & İletişim

- **Discord Sunucusu**: https://discord.gg/VPpxS5B6
- **Yol Haritası**: Discord sunucumuzda paylaşılıyor
- **Hata Bildirimi**: [Issues](../../issues) sayfasından bildirebilirsiniz

---

## 📜 Lisans

Bu proje açık kaynaklıdır. Kaynak kodları inceleyebilir, değiştirebilir ve paylaşabilirsiniz.

---

## 🌟 Teşekkürler

PluginAuto'yu kullandığınız için teşekkürler! Umarım sunucu kurulumlarınızı kolaylaştırır.

**İyi oyunlar! 🎮**
