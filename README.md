# 🎬 NeoTube Pro

NeoTube Pro, yt-dlp tabanlı gelişmiş bir video / playlist indirici masaüstü uygulamasıdır.
Modern arayüz (CustomTkinter), hız limiti, kalite seçimi, kuyruk sistemi ve favoriler desteği sunar.

## 🚀 Özellikler

✅ Playlist ve tek video indirme

🎞️ Video kalite seçimi (1080p / 720p / 480p / best)

🎧 Sadece ses indirme (audio, audio_320)

⚡ Eşzamanlı parça indirme (concurrent fragments)

🚀 Hız limiti (MB/s)

⏸️ Duraklat / devam et / durdur

📋 İndirme kuyruğu

⭐ Favori URL listesi (oturum bazlı)

📊 Oturum istatistikleri

🔔 İndirme bitince masaüstü bildirimi

🧠 Otomatik başlık çözümleme

🎨 Modern GUI (CustomTkinter)



## 🖥️ Gereksinimler

```bash
Python 3.10+

FFmpeg (PATH’e ekli olmalı)

Deno (isteğe bağlı, bazı extractor’lar için)
```


## 📦 Kurulum

1️⃣ Depoyu klonla

```bash
git clone https://github.com/canerergun/NeoTube.git
cd NeoTube
```

2️⃣ Gerekli kütüphaneleri yükle

```bash
pip install -r requirements.txt
```

## ▶️ Çalıştırma

```bash
python NeoTube.py
```


## 📷 NeoTube Arayüz

<img width="1499" height="928" alt="NeoTube" src="https://github.com/user-attachments/assets/7e37413d-23f5-4f90-af07-54cc6b2b8855" />

## ⚙️ Kullanım


- Playlist veya video URL’lerini gir (her satıra 1 URL)

- Kalite seç

- İndirme klasörünü seç

- İndirmeyi Başlat butonuna bas

Durumlar:

- ⏳ Bekliyor

- ⏬ İndiriliyor

- ✅ Tamamlandı

- ❌ Hata

- ⏭️ Atlandı


## 🧪 Desteklenen Formatlar

| Seçenek    | Açıklama      |
| ---------- | ------------- |
| best       | En iyi kalite |
| 1080p      | Max 1080p     |
| 720p       | Max 720p      |
| 480p       | Max 480p      |
| audio      | Sadece ses    |
| audio_320  | 320kbps ses   |
| video_only | Sadece video  |




## 📂 Klasör Yapısı

```bash
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


## ❓ Sıkça Sorulan Sorular

1️⃣ Oynatma listesi olmayan tek bir video indirirsem ne olur?

• Video, seçtiğiniz ana klasörün içine kaydedilir.

2️⃣ İndirme sırasında hata alıyorum, ne yapmalıyım?

• `yt-dlp` kütüphanesinin güncel olduğundan emin olun:
```bash
pip install --upgrade yt-dlp
```
• YouTube'un politikaları nedeniyle bazı videoların indirilmesi engellenmiş olabilir.


## 👨‍💻 Geliştirici  
Bu proje **Caner Ergün** tarafından geliştirilmiştir.  

## 📜 Lisans
Bu proje MIT Lisansı ile lisanslanmıştır.
