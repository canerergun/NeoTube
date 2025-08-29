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

```bash
python NeoTube.py
```

2. İndirilecek YouTube URL'lerini Girin

 • Bir veya birden fazla YouTube oynatma listesi veya video bağlantısını girin.

3. Kayıt Klasörünü Seçin

• Videoların kaydedileceği ana klasörü belirleyin.

4. İndirmeyi Başlatın

• "İndirmeyi Başlat" butonuna basarak işlemi başlatın.

5. Duraklat ve Devam Et

• "Duraklat" ve "Devam Et" butonlarıyla indirme işlemini yönetebilirsiniz.


## 📷 NeoTube Arayüz

<img width="701" height="630" alt="Ekran görüntüsü 2025-07-12 175703" src="https://github.com/user-attachments/assets/ebe266d8-9059-48a9-bed7-fdd3860a35f9" />



## 📂 Klasör Yapısı

```bash
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
