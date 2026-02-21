<<<<<<< HEAD
# 🎬 NeoTube Pro - Gelişmiş Video İndirici

Modern, özellik zengini ve kullanıcı dostu bir YouTube video indirme uygulaması. CustomTkinter ile geliştirilmiş şık arayüzü ve gelişmiş özellikleriyle video indirme deneyimini bir üst seviyeye taşır.

## ✨ Özellikler

### 🎯 Temel Özellikler
- **🎥 YouTube Desteği**: Tek videolar, oynatma listeleri ve çoklu URL desteği
- **📁 Akıllı Klasör Yönetimi**: Her oynatma listesi için otomatik ayrı klasör oluşturma
- **🎨 Modern Arayüz**: CustomTkinter ile karanlık/aydınlık tema desteği
- **📊 Çoklu Kalite Seçenekleri**: 480p, 720p, 1080p, En İyi Kalite, Sadece Ses ve daha fazlası

### ⚡ Gelişmiş Özellikler
- **⏸️ İndirme Kontrolü**: Duraklat, devam ettir ve durdur desteği
- **🚀 Hız Limiti**: Bant genişliği kontrolü için özelleştirilebilir hız limiti
- **⚡ Eşzamanlı İndirme**: Aynı anda birden fazla parça indirme
- **📋 İndirme Kuyruğu**: Gerçek zamanlı kuyruk yönetimi ve görünümü
- **⭐ Favoriler**: Sık kullanılan URL'leri favorilere ekleme
- **📜 İndirme Geçmişi**: Son 100 indirme kaydını tutma ve görüntüleme
- **⏰ Zamanlayıcı**: İndirmeleri belirli bir saate planlama (Demo modu)

### 🔧 Teknik Özellikler
- **🎬 FFmpeg Entegrasyonu**: Otomatik FFmpeg algılama ve entegrasyonu
- **🦕 Deno Runtime**: YouTube JS engelini aşmak için Deno desteği

- **🔔 Sistem Bildirimleri**: İndirme tamamlandığında masaüstü bildirimleri
- **🛡️ Hata Yönetimi**: Özel/üye videoları atlama ve hata kurtarma

## 🛠️ Gereksinimler

### Zorunlu Bağımlılıklar
```bash
pip install customtkinter yt-dlp plyer
```

## 💻 Gerekli Bileşenler

FFmpeg: Video işleme ve birleştirme için

İndir: https://ffmpeg.org/download.html

Windows: C:\ffmpeg\bin\ffmpeg.exe yoluna kurun veya PATH'e ekleyin

---------------------------------------------------------------
Deno: YouTube JS engelini aşmak için

İndir: https://deno.land/

Windows: ~\.deno\bin\deno.exe otomatik algılanır

## 🚀 Kurulum ve Kullanım

1. Projeyi İndirin
```bash
git clone https://github.com/canerergun/NeoTube.git
cd NeoTube
```
2. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

3. Uygulamayı Başlatın
=======
# 🎥 NeoTube  

Bu proje, YouTube videolarını ve oynatma listelerini kolayca indirmenizi sağlayan bir PyQt5 arayüzüne sahip bir uygulamadır.  
Her oynatma listesi için ayrı bir klasör oluşturur ve videoları ilgili klasöre indirir.  

## 🚀 Özellikler  

- 📌 **YouTube videolarını ve oynatma listelerini destekler**  
- 📁 **Her oynatma listesi için ayrı klasör oluşturur**  
- 🎯 **Videoları en iyi kaliteyle indirir**  
- 📉 **İndirme sırasında ilerleme çubuğu ile süreç takibi**  
- ⏸ **İndirme duraklatma ve devam ettirme desteği**  

## 🛠 Gereksinimler  

Projeyi çalıştırmadan önce aşağıdaki kütüphanelerin yüklü olduğundan emin olun:  

```bash
pip install yt-dlp PyQt5 plyer
```


## 💻 Kullanım

1. Uygulamayı Başlatın

>>>>>>> dd538265985add7d22a91984fb250f6e98cb53fc
```bash
python NeoTube.py
```

<<<<<<< HEAD
### 📖 Kullanım Kılavuzu

## URL Ekleme
1. Metin alanına YouTube video veya oynatma listesi URL'lerini yapıştırın
2. Her satıra bir URL gelecek şekilde düzenleyin
3. URL'ler otomatik olarak çözümlenir ve başlıklar gösterilir
## İndirme Ayarları
- Kalite: İstenilen video kalitesini seçin (best, 1080p, 720p, 480p, audio, vb.)
- Eşzamanlı: Aynı anda indirilecek parça sayısı (1-5)
- Hız Limiti: Maksimum indirme hızını sınırlayın
## İndirme İşlemi
1. Klasör Seç: İndirilenlerin kaydedileceği ana klasörü belirleyin
2. Başlat: "İndirmeyi Başlat" butonuna tıklayın
3. Yönet: İlerlemeyi izleyin, gerekirse duraklatın veya durdurun
## Favoriler ve Geçmiş
- ⭐ Favori Ekle: URL öğesine çift tıklayarak favorilere ekleyin
- 📜 Geçmiş: Son indirmeleri görüntüleyin ve tekrar indirin


=======
2. İndirilecek YouTube URL'lerini Girin

 • Bir veya birden fazla YouTube oynatma listesi veya video bağlantısını girin.

3. Kayıt Klasörünü Seçin

• Videoların kaydedileceği ana klasörü belirleyin.

4. İndirmeyi Başlatın

• "İndirmeyi Başlat" butonuna basarak işlemi başlatın.

5. Duraklat ve Devam Et

• "Duraklat" ve "Devam Et" butonlarıyla indirme işlemini yönetebilirsiniz.
>>>>>>> dd538265985add7d22a91984fb250f6e98cb53fc


## 📷 NeoTube Arayüz

<img width="1195" height="784" alt="Yeni NeoTube Arayüz" src="https://github.com/user-attachments/assets/2839bd88-106d-40b0-bfd4-0f6646f1b42a" />


## 📂 Klasör Yapısı

```bash
<<<<<<< HEAD
/İndirme_Klasörü/
├── 🎬 Tek_Video_Başlığı/
│   └── Video_Adı.mp4
├── 📁 Oynatma_Listesi_1/
│   ├── Video_1.mp4
│   ├── Video_2.mp4
│   └── ...
└── 📁 Oynatma_Listesi_2/
    ├── Video_1.mp4
    └── ...
```

## ⚙️ Yapılandırma
Uygulama ayarları neotube_config.json dosyasında saklanır:
```bash
{
    "download_folder": "C:\\İndirilenler",
    "last_urls": ["..."],
    "format_preference": "best",
    "concurrent_downloads": 3,
    "theme": "dark",
    "favorites": ["..."],
    "download_history": [...]
}
``` 

## 🔧 Sorun Giderme

FFmpeg Bulunamadı Hatası
```bash
# Windows - FFmpeg'i PATH'e ekleyin veya şu konumlara kurun:
C:\ffmpeg\bin\ffmpeg.exe
C:\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe
%USERPROFILE%\ffmpeg\bin\ffmpeg.exe
```

Deno Bulunamadı Hatası
```bash
# PowerShell ile Deno kurulumu:
irm https://deno.land/install.ps1 | iex
```

yt-dlp Güncelleme
```bash
pip install --upgrade yt-dlp
```

Özel/Üye Videoları
- ⚠️ Bu videolar otomatik olarak atlanır
- Hata mesajı yerine "Atlandı" durumu gösterilir



=======
/İndirilen_Klasör  
   ├── Playlist_1/  
   │   ├── Video_1.mp4  
   │   ├── Video_2.mp4  
   │   └── ...  
   ├── Playlist_2/  
   │   ├── Video_1.mp4  
   │   ├── Video_2.mp4  
   │   └── ...  
   ├── Playlist_3/  
   │   ├── Video_1.mp4  
   │   ├── Video_2.mp4  
   │   └── ...  
```

>>>>>>> dd538265985add7d22a91984fb250f6e98cb53fc
## ❓ Sıkça Sorulan Sorular

1️⃣ Oynatma listesi olmayan tek bir video indirirsem ne olur?

• Video, seçtiğiniz ana klasörün içine kaydedilir.

2️⃣ İndirme sırasında hata alıyorum, ne yapmalıyım?

• `yt-dlp` kütüphanesinin güncel olduğundan emin olun:
```bash
pip install --upgrade yt-dlp
```
• YouTube'un politikaları nedeniyle bazı videoların indirilmesi engellenmiş olabilir.

<<<<<<< HEAD


=======
>>>>>>> dd538265985add7d22a91984fb250f6e98cb53fc
## 👨‍💻 Geliştirici  
Bu proje **Caner Ergün** tarafından geliştirilmiştir.  

## 📜 Lisans
Bu proje MIT Lisansı ile lisanslanmıştır.
