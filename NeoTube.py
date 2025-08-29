import sys
import os
import yt_dlp
import webbrowser
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal
from plyer import notification

def sanitize_filename(name):
    # Windows için geçersiz karakterleri temizle
    return re.sub(r'[<>:"/\\|?*]', '-', name)

class DownloadThread(QThread):
    update_progress = pyqtSignal(int)
    download_finished = pyqtSignal()
    paused = False

    def __init__(self, urls, folder):
        super().__init__()
        self.urls = urls
        self.folder = folder

    def run(self):
        for url in self.urls:
            playlist_title = self.get_playlist_title(url)
            folder_path = os.path.join(self.folder, playlist_title) if playlist_title else self.folder
            os.makedirs(folder_path, exist_ok=True)
            self.download_playlist_or_video(url, folder_path)
        self.download_finished.emit()

    def get_playlist_title(self, url):
        ydl_opts = {'quiet': True, 'extract_flat': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'İndirilenler')
                return sanitize_filename(title)  # 🔥 Temizlenmiş klasör adı
        except Exception:
            return 'İndirilenler'

    def download_playlist_or_video(self, url, folder):
        ydl_opts = {
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'progress_hooks': [self.progress_hook],
            'verbose': True,
            'ignoreerrors': True,
            'noplaylist': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
            except Exception as e:
                notification.notify(title="İndirme Hatası", message=f"Video indirilirken hata oluştu: {e}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            while self.paused:
                self.msleep(100)
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes'] > 0:
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.update_progress.emit(progress)

    def pause_download(self):
        self.paused = True

    def resume_download(self):
        self.paused = False

class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NeoTube")
        self.setGeometry(300, 300, 700, 600)
        self.setStyleSheet("background-color: #2e2e2e; color: white; font-family: Arial, sans-serif; font-size: 14px;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("NeoTube")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffcc00; text-align: center;")
        layout.addWidget(title_label)

        url_label = QLabel("Playlist URL'lerini Girin (Her satıra bir URL):")
        layout.addWidget(url_label)

        self.url_text = QTextEdit()
        self.url_text.setPlaceholderText("Playlist URL'lerini buraya yapıştırın...")
        layout.addWidget(self.url_text)

        folder_label = QLabel("İndirilecek Klasörü Seçin:")
        layout.addWidget(folder_label)

        folder_btn = QPushButton("Klasör Seç")
        folder_btn.setStyleSheet("background-color: #ffcc00; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(folder_btn)

        self.folder_line = QLabel("")
        self.folder_line.setStyleSheet("background-color: #444; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.folder_line)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()

        download_btn = QPushButton("İndirmeyi Başlat")
        download_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        download_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(download_btn)

        pause_btn = QPushButton("Duraklat")
        pause_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        pause_btn.clicked.connect(self.pause_download)
        btn_layout.addWidget(pause_btn)

        resume_btn = QPushButton("Devam Et")
        resume_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        resume_btn.clicked.connect(self.resume_download)
        btn_layout.addWidget(resume_btn)

        layout.addLayout(btn_layout)

        # Geliştirici bilgileri ve sosyal medya butonları
        dev_layout = QHBoxLayout()
        dev_label = QLabel("👨‍💻 Geliştirici: Caner Ergün")
        dev_label.setStyleSheet("color: #ffcc00; font-size: 14px; font-weight: bold;")
        dev_layout.addWidget(dev_label)

        def add_social_button(name, color, url):
            btn = QPushButton(name)
            btn.setStyleSheet(f"background-color: {color}; color: white; border-radius: 5px; padding: 5px;")
            btn.clicked.connect(lambda: webbrowser.open(url))
            dev_layout.addWidget(btn)

        add_social_button("LinkedIn", "#0A66C2", "https://www.linkedin.com/in/devseu/")
        add_social_button("GitHub", "#333", "https://github.com/canerergun")
        add_social_button("Instagram", "#C13584", "https://www.instagram.com/devseu")
        add_social_button("Twitch", "#9146FF", "https://www.twitch.tv/devseu")

        layout.addLayout(dev_layout)

        self.setLayout(layout)
        self.thread = None
        self.download_folder = ""

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç", "")
        if folder:
            self.download_folder = folder
            self.folder_line.setText(folder)

    def start_download(self):
        urls = self.url_text.toPlainText().strip().splitlines()
        if not urls:
            notification.notify(title="Hata", message="Lütfen en az bir playlist URL'si girin.")
            return
        if not self.download_folder:
            notification.notify(title="Hata", message="Lütfen indirilecek klasörü seçin.")
            return

        self.progress_bar.setValue(0)
        self.thread = DownloadThread(urls, self.download_folder)
        self.thread.update_progress.connect(self.update_progress)
        self.thread.download_finished.connect(self.download_finished)
        self.thread.start()

    def pause_download(self):
        if self.thread:
            self.thread.pause_download()

    def resume_download(self):
        if self.thread:
            self.thread.resume_download()

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def download_finished(self):
        notification.notify(title="İndirme Tamamlandı", message="Tüm playlistler başarıyla indirildi!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoDownloader()
    win.show()
    sys.exit(app.exec_())
