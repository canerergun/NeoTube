import sys
import os
import yt_dlp
import webbrowser
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QProgressBar, QFileDialog, QHBoxLayout, QSizePolicy,
    QScrollArea
)
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, Qt
from plyer import notification

# --- Yardımcı Fonksiyonlar ---
def sanitize_filename(name):
    """
    Windows için geçersiz karakterleri temizler ve geçerli bir dosya adı döndürür.
    """
    return re.sub(r'[<>:"/\\|?*]', '-', name)

# --- Playlist Başlık Çözümleme Thread ---
class TitleResolverThread(QThread):
    """
    Arka planda URL'lerin başlıklarını çözümlemek için kullanılan bir QThread.
    """
    resolved = pyqtSignal(dict)  # {url: title}

    def __init__(self, urls):
        super().__init__()
        self.urls = urls

    def run(self):
        results = {}
        ydl_opts = {'quiet': True, 'extract_flat': True, 'force_generic_extractor': True, 'log_level': 'warning'}
        for url in self.urls:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = sanitize_filename(info.get("title", url))
                    results[url] = title
            except Exception:
                results[url] = url
        self.resolved.emit(results)

# --- İndirme Thread ---
class DownloadThread(QThread):
    """
    Video indirme işlemini yönetmek için kullanılan bir QThread.
    """
    progress = pyqtSignal(str)
    update_progress_bar = pyqtSignal(int)
    current_url = pyqtSignal(str)
    download_finished = pyqtSignal()
    update_url_status_ui = pyqtSignal(str, str)

    def __init__(self, urls, titles, save_path, cookies_file=None):
        super().__init__()
        self.urls = urls
        self.titles = titles
        self.save_path = save_path
        self.cookies_file = cookies_file
        self._pause = False
        self._stop = False
        self.mutex = QMutex()

    def run(self):
        total_playlists = len(self.urls)
        
        # Terminal çıktısını tamamen susturmak için
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            for idx, url in enumerate(self.urls, start=1):
                if self._stop:
                    break
                
                while self._pause:
                    self.msleep(200)

                title = self.titles.get(url, url)
                self.current_url.emit(url)

                def progress_hook(d):
                    self.mutex.lock()
                    if d['status'] == 'downloading':
                        if d.get('total_bytes') is not None and d['total_bytes'] > 0:
                            downloaded_percentage = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                            self.update_progress_bar.emit(downloaded_percentage)
                        elif d.get('total_bytes_estimate') is not None and d['total_bytes_estimate'] > 0:
                            downloaded_percentage = int(d['downloaded_bytes'] / d['total_bytes_estimate'] * 100)
                            self.update_progress_bar.emit(downloaded_percentage)
                    elif d['status'] == 'finished':
                        self.update_progress_bar.emit(0)
                        self.update_url_status_ui.emit(url, "completed")
                    elif d['status'] == 'downloaded':
                        self.update_url_status_ui.emit(url, "skipped")
                    self.mutex.unlock()

                try:
                    self.progress.emit(f"📥 {idx}/{total_playlists} - İndiriliyor: {title}")
                    
                    output_template = os.path.join(self.save_path, sanitize_filename(title), "%(title)s.%(ext)s")
                    
                    ydl_opts = {
                        "outtmpl": output_template,
                        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
                        "quiet": True,
                        "ignoreerrors": True,
                        "progress_hooks": [progress_hook],
                        "noplaylist": False,
                    }
                    
                    if self.cookies_file and os.path.exists(self.cookies_file):
                        ydl_opts['cookiefile'] = self.cookies_file

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    self.update_progress_bar.emit(0)

                except Exception as e:
                    self.update_progress_bar.emit(0)
                    if "This video is available to this channel's members" in str(e):
                        self.progress.emit(f"⚠️ {idx}/{total_playlists} - Atlandı (Üyelere Özel): {title}")
                        self.update_url_status_ui.emit(url, "skipped")
                    else:
                        self.progress.emit(f"❌ Hata ({title}): {e}")
                        self.update_url_status_ui.emit(url, "error")
                    
            self.download_finished.emit()
            
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def pause_download(self):
        self._pause = True

    def resume_download(self):
        self._pause = False
        
    def stop_download(self):
        self._stop = True

# --- Ana Arayüz ---
class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeoTube")
        self.setGeometry(250, 100, 1200, 800)
        self.setStyleSheet("background-color: #2e2e2e; color: white; font-family: Arial, sans-serif; font-size: 14px;")
        
        self.url_titles = {}
        self.download_thread = None
        self.resolver_thread = None
        self.download_folder = ""
        
        self.cookies_file = self.find_cookies_file()

        self.init_ui()

    def find_cookies_file(self):
        cookies_path = os.path.join(os.path.dirname(sys.argv[0]), "youtube_cookies.txt")
        if os.path.exists(cookies_path):
            return cookies_path
        return None

    def init_ui(self):
        layout = QVBoxLayout()
        
        title_label = QLabel("NeoTube")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffcc00; text-align: center;")
        layout.addWidget(title_label)
        
        url_label = QLabel("Playlist URL'lerini Girin (Her satıra bir URL):")
        layout.addWidget(url_label)
        self.url_text = QTextEdit()
        self.url_text.setPlaceholderText("Playlist URL'lerini buraya yapıştırın...")
        self.url_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.url_text.textChanged.connect(self.clean_and_resolve_urls)
        layout.addWidget(self.url_text, stretch=3)
        
        folder_btn = QPushButton("Klasör Seç")
        folder_btn.setStyleSheet("background-color: #ffcc00; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(folder_btn)

        self.folder_line = QLabel("Henüz klasör seçilmedi")
        self.folder_line.setStyleSheet("background-color: #444; padding: 8px; border-radius: 3px;")
        layout.addWidget(self.folder_line)

        # --- Dinamik URL Listesi ve Durum Gösterimi ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.url_list_widget = QWidget()
        self.url_list_layout = QVBoxLayout(self.url_list_widget)
        self.url_list_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.url_list_widget)
        layout.addWidget(self.scroll_area, stretch=5)
        
        self.current_label = QLabel("Henüz indirme başlamadı...")
        self.current_label.setStyleSheet("color: #00ffcc; font-weight: bold;")
        layout.addWidget(self.current_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("height: 25px;")
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.download_btn = QPushButton("İndirmeyi Başlat")
        self.download_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.download_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.download_btn)
        self.pause_btn = QPushButton("Duraklat")
        self.pause_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.pause_btn.clicked.connect(self.pause_download)
        btn_layout.addWidget(self.pause_btn)
        self.resume_btn = QPushButton("Devam Et")
        self.resume_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.resume_btn.clicked.connect(self.resume_download)
        btn_layout.addWidget(self.resume_btn)
        layout.addLayout(btn_layout)

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

    def clear_url_list_widget(self):
        """Dinamik URL listesini temizler."""
        while self.url_list_layout.count():
            item = self.url_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout = item.layout()
            if layout:
                self.clear_layout(layout)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self.clear_layout(sub_layout)

    def clean_and_resolve_urls(self):
        """
        URL'leri temizler ve başlıklarını çözümlemek için bir thread başlatır.
        """
        raw_urls = [u.strip() for u in self.url_text.toPlainText().splitlines() if u.strip()]
        self.url_text.blockSignals(True)
        self.url_text.setText("\n".join(raw_urls))
        self.url_text.blockSignals(False)

        if not raw_urls:
            self.clear_url_list_widget()
            return

        if self.resolver_thread and self.resolver_thread.isRunning():
            return
        
        self.url_titles.clear()
        self.resolver_thread = TitleResolverThread(raw_urls)
        self.resolver_thread.resolved.connect(self.update_url_titles)
        self.resolver_thread.start()

    def update_url_titles(self, results):
        """
        URL-başlık eşlemesini ve dinamik URL listesini günceller.
        """
        self.url_titles = results
        self.clear_url_list_widget()

        for idx, (url, title) in enumerate(results.items(), start=1):
            item_layout = QHBoxLayout()
            item_label = QLabel(f"{idx}. {title}")
            item_label.setStyleSheet("background-color: #444; padding: 5px; border-radius: 3px;")
            item_url_label = QLabel(url)
            item_url_label.setStyleSheet("background-color: #444; padding: 5px; border-radius: 3px;")
            item_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            item_url_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            item_layout.addWidget(item_label)
            item_layout.addWidget(item_url_label)
            
            item_widget = QWidget()
            item_widget.setLayout(item_layout)
            self.url_list_layout.addWidget(item_widget)

    def select_folder(self):
        """
        İndirme klasörünü seçmek için bir iletişim kutusu açar.
        """
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç", "")
        if folder:
            self.download_folder = folder
            self.folder_line.setText(folder)

    def start_download(self):
        """
        İndirme işlemini yeni bir thread'de başlatır.
        """
        urls = list(self.url_titles.keys()) if self.url_titles else []

        if not urls:
            notification.notify(title="Hata", message="Lütfen en az bir playlist URL'si girin.")
            return
        if not self.download_folder:
            notification.notify(title="Hata", message="Lütfen indirilecek klasörü seçin.")
            return
        
        self.url_text.setDisabled(True)
        self.download_btn.setDisabled(True)
        self.progress_bar.setValue(0)
        
        self.download_thread = DownloadThread(urls, self.url_titles, self.download_folder, self.cookies_file)
        self.download_thread.progress.connect(self.current_label.setText)
        self.download_thread.update_progress_bar.connect(self.progress_bar.setValue)
        self.download_thread.current_url.connect(self.update_url_status)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.update_url_status_ui.connect(self.update_ui_status)
        self.download_thread.start()

    def update_url_status(self, current_url):
        """
        URL listesindeki indirme durumunu günceller.
        """
        for i in range(self.url_list_layout.count()):
            widget_item = self.url_list_layout.itemAt(i)
            if widget_item:
                item_widget = widget_item.widget()
                if item_widget:
                    item_layout = item_widget.layout()
                    url_label = item_layout.itemAt(1).widget()
                    if url_label and url_label.text() == current_url:
                        item_layout.itemAt(0).widget().setStyleSheet("background-color: #ffcc00; padding: 5px; border-radius: 3px;")
                        item_layout.itemAt(1).widget().setStyleSheet("background-color: #ffcc00; padding: 5px; border-radius: 3px;")

    def update_ui_status(self, url, status):
        """
        URL indirme durumuna göre arayüzdeki renkleri ve durumları günceller.
        """
        for i in range(self.url_list_layout.count()):
            widget_item = self.url_list_layout.itemAt(i)
            if widget_item:
                item_widget = widget_item.widget()
                if item_widget:
                    item_layout = item_widget.layout()
                    url_label = item_layout.itemAt(1).widget()
                    if url_label and url_label.text() == url:
                        if status == "completed":
                            color = "#28a745"
                            item_layout.itemAt(0).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")
                            item_layout.itemAt(1).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")
                        elif status == "skipped":
                            color = "#007bff"
                            item_layout.itemAt(0).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")
                            item_layout.itemAt(1).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")
                        elif status == "error":
                            color = "#dc3545"
                            item_layout.itemAt(0).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")
                            item_layout.itemAt(1).widget().setStyleSheet(f"background-color: {color}; padding: 5px; border-radius: 3px;")

    def pause_download(self):
        """
        İndirme thread'ini duraklatır.
        """
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.pause_download()
            self.current_label.setText("⏸️ Duraklatıldı...")

    def resume_download(self):
        """
        İndirme thread'ini devam ettirir.
        """
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.resume_download()
            self.current_label.setText("▶️ Devam ediyor...")

    def on_download_finished(self):
        """
        Tüm indirmeler tamamlandığında çalışır.
        """
        self.download_btn.setDisabled(False)
        self.url_text.setDisabled(False)
        self.current_label.setText("İndirme tamamlandı!")
        notification.notify(title="İndirme Tamamlandı", message="Tüm playlistler başarıyla indirildi!")

# --- Ana Program ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoDownloader()
    win.show()
    sys.exit(app.exec_())