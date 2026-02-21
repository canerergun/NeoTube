import customtkinter as ctk
import yt_dlp
import os
import webbrowser
import re
import threading
from plyer import notification
from tkinter import filedialog, messagebox
import subprocess
import sys
import time
import queue

# CustomTkinter teması ve görünüm ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TitleResolverThread(threading.Thread):
    """URL'lerin başlıklarını çözümlemek için thread"""

    def __init__(self, urls, callback, progress_callback=None):
        super().__init__()
        self.urls = urls
        self.callback = callback
        self.progress_callback = progress_callback
        self.daemon = True
        self._stop_flag = False

    def run(self):
        results = {}
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'ignoreerrors': True,
            'no_warnings': True
        }

        for i, url in enumerate(self.urls):
            if self._stop_flag:
                break

            if self.progress_callback:
                self.progress_callback(i + 1, len(self.urls), f"Çözümleniyor: {url[:50]}...")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        title = info.get("title", url)
                        # Playlist mi tek video mu kontrol et
                        if 'entries' in info:  # Playlist
                            video_count = len(info['entries']) if info['entries'] else 0
                            title = f"📁 {title} (Playlist - {video_count} video)"
                        else:  # Tek video
                            duration = info.get('duration', 0)
                            if duration:
                                minutes = duration // 60
                                seconds = duration % 60
                                title = f"🎬 {title} ({minutes}:{seconds:02d})"
                            else:
                                title = f"🎬 {title}"
                        results[url] = self.sanitize_filename(title)
                    else:
                        results[url] = f"⚠️ {url} (Çözümlenemedi)"
            except Exception as e:
                results[url] = f"❌ {url} (Hata: {str(e)[:30]})"

        self.callback(results)

    def stop(self):
        self._stop_flag = True

    def sanitize_filename(self, name):
        """Windows için geçersiz karakterleri temizler"""
        return re.sub(r'[<>:"/\\|?*]', '-', name)


class DownloadThread(threading.Thread):
    """Video indirme işlemini yöneten thread"""

    def __init__(self, urls, titles, save_path, format_preference="best", concurrent=3, proxy=None, speed_limit=None):
        super().__init__()
        self.urls = urls
        self.titles = titles
        self.save_path = save_path
        self.format_preference = format_preference
        self.concurrent = concurrent
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.daemon = True
        self._pause_flag = False
        self._stop_flag = False
        self.current_url_index = 0
        self.total_urls = len(urls)
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.start_time = None
        self.download_queue = queue.Queue()
        self.completed_list = []

        # Callback'ler
        self.on_progress = None
        self.on_url_status = None
        self.on_finished = None
        self.on_current_url = None
        self.on_progress_bar = None
        self.on_error = None
        self.on_speed_update = None
        self.on_queue_update = None

        # FFmpeg ve Deno yollarını otomatik bul
        self.ffmpeg_path = self.find_ffmpeg()
        self.deno_path = self.find_deno()

    def find_ffmpeg(self):
        """FFmpeg'in yolunu bul"""
        possible_paths = [
            "C:\\ffmpeg-8.0.1-essentials_build\\bin\\ffmpeg.exe",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
            os.path.expanduser("~\\ffmpeg\\bin\\ffmpeg.exe"),
            "ffmpeg"
        ]

        for path in possible_paths:
            try:
                if path == "ffmpeg":
                    subprocess.run([path, "-version"], capture_output=True, check=True)
                    return path
                elif os.path.exists(path):
                    return path
            except:
                continue
        return None

    def find_deno(self):
        """Deno'nun yolunu bul"""
        user_deno = os.path.expanduser("~\\.deno\\bin\\deno.exe")
        if os.path.exists(user_deno):
            return user_deno

        possible_paths = [
            os.path.expanduser("~\\AppData\\Local\\deno\\deno.exe"),
            "C:\\Program Files\\deno\\deno.exe",
            "deno"
        ]

        for path in possible_paths:
            try:
                if path == "deno":
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    return path
                elif os.path.exists(path):
                    return path
            except:
                continue
        return None

    def run(self):
        self.start_time = time.time()

        for idx, url in enumerate(self.urls, start=1):
            self.current_url_index = idx
            self.downloaded_bytes = 0
            self.total_bytes = 0

            if self._stop_flag:
                break

            while self._pause_flag:
                time.sleep(0.2)

            title = self.titles.get(url, f"URL {idx}")
            clean_title = re.sub(r'[<>:"/\\|?*]', '-',
                                 title.replace("📁 ", "").replace("🎬 ", "").replace("⚠️ ", "").replace("❌ ", ""))

            if self.on_current_url:
                self.on_current_url(url, clean_title)

            if self.on_queue_update:
                self.on_queue_update(idx, self.total_urls, clean_title)

            def progress_hook(d):
                if self._stop_flag:
                    raise Exception("İndirme durduruldu")

                if d['status'] == 'downloading':
                    # İlerleme yüzdesi
                    if d.get('total_bytes'):
                        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                        self.downloaded_bytes = d['downloaded_bytes']
                        self.total_bytes = d['total_bytes']
                    elif d.get('total_bytes_estimate'):
                        percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                        self.downloaded_bytes = d['downloaded_bytes']
                        self.total_bytes = d['total_bytes_estimate']
                    else:
                        percent = 0

                    if self.on_progress_bar:
                        self.on_progress_bar(int(percent))

                    # Hız ve ETA
                    speed = d.get('speed', 0)
                    if speed and self.on_speed_update:
                        speed_mb = speed / 1024 / 1024
                        eta = d.get('eta', 0)

                        if eta:
                            minutes = eta // 60
                            seconds = eta % 60
                            eta_str = f"{minutes}:{seconds:02d}"
                        else:
                            eta_str = "??"

                        self.on_speed_update(f"{speed_mb:.1f} MB/s", eta_str)

                elif d['status'] == 'finished':
                    if self.on_progress_bar:
                        self.on_progress_bar(100)
                    if self.on_url_status:
                        self.on_url_status(url, "completed", clean_title)
                    self.completed_list.append(url)

            try:
                if self.on_progress:
                    self.on_progress(f"📥 {idx}/{self.total_urls} - İndiriliyor: {clean_title}")

                # Format seçeneklerini ayarla
                format_map = {
                    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
                    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
                    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
                    "audio": "bestaudio/best",
                    "audio_320": "bestaudio[abr>320]/bestaudio",
                    "video_only": "bestvideo[ext=mp4]"
                }

                format_selector = format_map.get(self.format_preference, format_map["best"])

                # Playlist için klasör oluştur
                playlist_folder = os.path.join(self.save_path, clean_title)
                os.makedirs(playlist_folder, exist_ok=True)

                output_template = os.path.join(playlist_folder, "%(title)s.%(ext)s")

                ydl_opts = {
                    "outtmpl": output_template,
                    "format": format_selector,
                    "quiet": True,
                    "no_warnings": True,
                    "ignoreerrors": True,
                    "progress_hooks": [progress_hook],
                    "noplaylist": False,
                    "extract_flat": False,
                    "continuedl": True,
                    "retries": 10,
                    "fragment_retries": 10,
                    "concurrent_fragment_downloads": self.concurrent,
                }

                # Proxy ekle
                if self.proxy:
                    ydl_opts["proxy"] = self.proxy

                # Hız limiti ekle
                if self.speed_limit:
                    ydl_opts["ratelimit"] = self.speed_limit * 1024 * 1024  # MB to bytes

                # FFmpeg yolunu ekle
                if self.ffmpeg_path:
                    ydl_opts["ffmpeg_location"] = self.ffmpeg_path

                # Deno yolunu ekle
                if self.deno_path:
                    ydl_opts["extractor_args"] = {
                        "youtube": {
                            "js_runtime": [f"deno:{self.deno_path}"]
                        }
                    }

                # Kullanıcı ajanı
                ydl_opts["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                if self.on_url_status:
                    self.on_url_status(url, "completed", clean_title)

            except Exception as e:
                if self.on_progress_bar:
                    self.on_progress_bar(0)
                error_msg = str(e)

                if "members" in error_msg.lower() or "private" in error_msg.lower():
                    if self.on_progress:
                        self.on_progress(f"⚠️ {idx}/{self.total_urls} - Atlandı (Özel/Üyelere Özel): {clean_title}")
                    if self.on_url_status:
                        self.on_url_status(url, "skipped", clean_title)
                else:
                    if self.on_progress:
                        self.on_progress(f"❌ {idx}/{self.total_urls} - Hata: {clean_title}")
                    if self.on_url_status:
                        self.on_url_status(url, "error", clean_title)
                    if self.on_error:
                        self.on_error(f"Hata: {error_msg[:100]}...")

        if self.on_finished:
            self.on_finished()

    def pause(self):
        self._pause_flag = True

    def resume(self):
        self._pause_flag = False

    def stop(self):
        self._stop_flag = True


class URLItem(ctk.CTkFrame):
    """URL listesi öğesi - Geliştirilmiş"""

    def __init__(self, master, index, title, url, **kwargs):
        super().__init__(master, **kwargs)

        # Frame'in kendisini yapılandır
        self.configure(height=40)
        self.grid_propagate(False)

        # Grid yapılandırması
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)

        # Index numarası
        self.index_label = ctk.CTkLabel(
            self,
            text=f"{index}.",
            width=30,
            anchor="e",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.index_label.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="w")

        # Başlık
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            anchor="w",
            fg_color=("gray70", "gray20"),
            corner_radius=5,
            height=30
        )
        self.title_label.grid(row=0, column=1, padx=2, pady=5, sticky="ew")

        # URL
        self.url_label = ctk.CTkLabel(
            self,
            text=url,
            anchor="w",
            fg_color=("gray70", "gray20"),
            corner_radius=5,
            height=30
        )
        self.url_label.grid(row=0, column=2, padx=2, pady=5, sticky="ew")

        # Durum ikonu
        self.status_label = ctk.CTkLabel(
            self,
            text="⏳",
            width=30,
            anchor="center",
            font=ctk.CTkFont(size=16)
        )
        self.status_label.grid(row=0, column=3, padx=(2, 5), pady=5)

        # Favori yıldızı
        self.fav_label = ctk.CTkLabel(
            self,
            text="☆",
            width=20,
            anchor="center",
            font=ctk.CTkFont(size=16)
        )
        self.fav_label.grid(row=0, column=4, padx=(0, 5), pady=5)

    def set_status(self, status):
        """Duruma göre renk ve ikon değiştir"""
        colors = {
            "downloading": "#ffcc00",
            "completed": "#28a745",
            "skipped": "#007bff",
            "error": "#dc3545",
            "waiting": ("gray70", "gray20")
        }
        icons = {
            "downloading": "⏬",
            "completed": "✅",
            "skipped": "⏭️",
            "error": "❌",
            "waiting": "⏳"
        }

        color = colors.get(status, ("gray70", "gray20"))
        icon = icons.get(status, "⏳")

        self.title_label.configure(fg_color=color)
        self.url_label.configure(fg_color=color)
        self.status_label.configure(text=icon)

    def set_favorite(self, is_favorite):
        """Favori durumunu güncelle"""
        self.fav_label.configure(text="★" if is_favorite else "☆", text_color="#ffcc00" if is_favorite else "gray")


class DownloadQueueItem(ctk.CTkFrame):
    """İndirme kuyruğu öğesi"""

    def __init__(self, master, index, title, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(height=30)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self,
            text=f"{index}. {title}",
            anchor="w",
            fg_color=("gray60", "gray30"),
            corner_radius=3,
            height=25
        )
        self.label.grid(row=0, column=0, padx=2, pady=2, sticky="ew")


class NeoTubeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere ayarları
        self.title("NeoTube Pro - Gelişmiş Video İndirici")
        self.geometry("1500x900")
        self.minsize(1300, 700)

        # Değişkenler
        self.url_titles = {}
        self.download_thread = None
        self.resolver_thread = None
        self.download_folder = ""
        self.url_items = []
        self.is_downloading = False
        self._resolve_after_id = None
        self.favorites = set()  # Favoriler sadece oturum için
        self.download_history = []  # Geçmiş sadece oturum için

        # UI'ı oluştur
        self.setup_ui()

        # Otomatik kontrol
        self.after(1000, self.check_requirements)

    def check_requirements(self):
        """Gerekli bileşenleri kontrol et"""
        ffmpeg_found = False
        deno_found = False

        # FFmpeg kontrolü
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            ffmpeg_found = True
        except:
            ffmpeg_paths = [
                "C:\\ffmpeg-8.0.1-essentials_build\\bin\\ffmpeg.exe",
                "C:\\ffmpeg\\bin\\ffmpeg.exe",
                os.path.expanduser("~\\ffmpeg\\bin\\ffmpeg.exe")
            ]
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    ffmpeg_found = True
                    break

        # Deno kontrolü
        try:
            subprocess.run(["deno", "--version"], capture_output=True, check=True)
            deno_found = True
        except:
            deno_path = os.path.expanduser("~\\.deno\\bin\\deno.exe")
            if os.path.exists(deno_path):
                deno_found = True

        # Durum mesajını güncelle
        status_messages = []
        if ffmpeg_found:
            status_messages.append("✅ FFmpeg: Hazır")
        else:
            status_messages.append("❌ FFmpeg: Bulunamadı")

        if deno_found:
            status_messages.append("✅ Deno: Hazır")
        else:
            status_messages.append("❌ Deno: Bulunamadı")

        self.requirement_label.configure(text=" | ".join(status_messages))

    def setup_ui(self):
        # Ana grid yapılandırması
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=0)

        # Üst bilgi çubuğu
        top_frame = ctk.CTkFrame(self, height=70, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        # Logo ve başlık
        title_label = ctk.CTkLabel(
            top_frame,
            text="🎬 NeoTube Pro",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#ffcc00"
        )
        title_label.grid(row=0, column=0, padx=(0, 20), sticky="w")

        # Gereksinim durumu
        self.requirement_label = ctk.CTkLabel(
            top_frame,
            text="🔍 Bileşenler kontrol ediliyor...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.requirement_label.grid(row=0, column=1, padx=10, sticky="e")

        # SOL TARAF - ANA İÇERİK
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, rowspan=5, padx=(20, 10), pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)

        # URL giriş alanı
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=0)

        url_label = ctk.CTkLabel(
            input_frame,
            text="📋 Playlist/Video URL'leri (Her satıra bir URL):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        url_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # URL text area
        self.url_text = ctk.CTkTextbox(input_frame, height=100)
        self.url_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.url_text.bind("<<Modified>>", self.on_text_modified)

        # Sağ taraftaki butonlar
        right_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        right_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        self.clear_btn = ctk.CTkButton(
            right_frame,
            text="🗑️ Temizle",
            command=self.clear_all_urls,
            width=100,
            fg_color="#6c757d"
        )
        self.clear_btn.pack(pady=5)

        # Ayarlar çubuğu
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Format seçimi
        format_label = ctk.CTkLabel(settings_frame, text="📊 Kalite:", font=ctk.CTkFont(size=12))
        format_label.grid(row=0, column=0, padx=(5, 2), pady=10, sticky="w")

        self.format_var = ctk.StringVar(value="best")
        format_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["best", "1080p", "720p", "480p", "audio", "audio_320", "video_only"],
            variable=self.format_var,
            width=90
        )
        format_menu.grid(row=0, column=1, padx=2, pady=10, sticky="w")

        # Eşzamanlı indirme
        concurrent_label = ctk.CTkLabel(settings_frame, text="⚡ Eşzamanlı:", font=ctk.CTkFont(size=12))
        concurrent_label.grid(row=0, column=2, padx=(10, 2), pady=10, sticky="w")

        self.concurrent_var = ctk.IntVar(value=3)
        concurrent_spinbox = ctk.CTkEntry(settings_frame, width=40, textvariable=self.concurrent_var)
        concurrent_spinbox.grid(row=0, column=3, padx=2, pady=10, sticky="w")

        # Hız limiti
        speed_label = ctk.CTkLabel(settings_frame, text="🚀 Hız Limiti:", font=ctk.CTkFont(size=12))
        speed_label.grid(row=0, column=4, padx=(10, 2), pady=10, sticky="w")

        self.speed_var = ctk.StringVar(value="0 (Sınırsız)")
        speed_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=["0 (Sınırsız)", "1 MB/s", "5 MB/s", "10 MB/s", "50 MB/s"],
            variable=self.speed_var,
            width=90
        )
        speed_menu.grid(row=0, column=5, padx=2, pady=10, sticky="w")

        # Klasör seçme alanı
        folder_frame = ctk.CTkFrame(main_frame)
        folder_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)

        folder_label = ctk.CTkLabel(
            folder_frame,
            text="📂 İndirme Klasörü:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        folder_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.folder_path = ctk.CTkLabel(
            folder_frame,
            text="Henüz seçilmedi",
            fg_color=("gray75", "gray25"),
            corner_radius=5,
            height=32,
            anchor="w"
        )
        self.folder_path.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.folder_btn = ctk.CTkButton(
            folder_frame,
            text="📁 Gözat",
            command=self.select_folder,
            width=100,
            fg_color="#ffcc00",
            text_color="black",
            hover_color="#ffd700"
        )
        self.folder_btn.grid(row=0, column=2, padx=10, pady=10)

        # URL listesi başlığı
        list_header = ctk.CTkFrame(main_frame)
        list_header.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")
        list_header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            list_header,
            text="📋 URL Listesi ve Durum",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left", padx=10, pady=5)

        self.stats_label = ctk.CTkLabel(
            list_header,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(side="left", padx=20, pady=5)

        # URL listesi scroll alanı
        self.url_list_frame = ctk.CTkScrollableFrame(
            main_frame,
            label_text="",
            corner_radius=10
        )
        self.url_list_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        # SAĞ TARAF - YENİ ÖZELLİKLER PANELİ
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=1, column=1, rowspan=4, padx=(10, 20), pady=10, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)

        # İndirme Kuyruğu
        queue_frame = ctk.CTkFrame(right_panel)
        queue_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        queue_label = ctk.CTkLabel(
            queue_frame,
            text="📋 İndirme Kuyruğu",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        queue_label.pack(pady=(5, 0))

        self.queue_frame = ctk.CTkScrollableFrame(queue_frame, height=150)
        self.queue_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.queue_items = []

        # Favoriler
        fav_frame = ctk.CTkFrame(right_panel)
        fav_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        fav_label = ctk.CTkLabel(
            fav_frame,
            text="⭐ Favori URL'ler (Bu oturum)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        fav_label.pack(pady=(5, 0))

        self.fav_listbox = ctk.CTkScrollableFrame(fav_frame, height=100)
        self.fav_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.update_favorites_display()

        # İstatistikler
        stats_frame = ctk.CTkFrame(right_panel)
        stats_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        stats_label = ctk.CTkLabel(
            stats_frame,
            text="📊 İstatistikler (Bu oturum)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_label.pack(pady=(5, 0))

        self.stats_text = ctk.CTkTextbox(stats_frame, height=100, state="disabled")
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.update_stats()

        # Durum ve ilerleme alanı
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=0)
        status_frame.grid_columnconfigure(2, weight=0)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="⏸️ Hazır",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00ffcc"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.speed_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.speed_label.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="e")

        self.eta_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.eta_label.grid(row=0, column=2, padx=10, pady=(10, 5), sticky="e")

        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # Kontrol butonları
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)  # 4 buton oldu (Geçmiş kaldırıldı)

        # İndirme butonları
        self.download_btn = ctk.CTkButton(
            button_frame,
            text="▶️ İndirmeyi Başlat",
            command=self.start_download,
            fg_color="#28a745",
            hover_color="#2ecc71",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.download_btn.grid(row=0, column=0, padx=2, pady=5, sticky="ew")

        self.pause_btn = ctk.CTkButton(
            button_frame,
            text="⏸️ Duraklat",
            command=self.pause_download,
            fg_color="#dc3545",
            hover_color="#e74c3c",
            height=40,
            state="disabled",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.pause_btn.grid(row=0, column=1, padx=2, pady=5, sticky="ew")

        self.resume_btn = ctk.CTkButton(
            button_frame,
            text="▶️ Devam Et",
            command=self.resume_download,
            fg_color="#007bff",
            hover_color="#3498db",
            height=40,
            state="disabled",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.resume_btn.grid(row=0, column=2, padx=2, pady=5, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹️ Durdur",
            command=self.stop_download,
            fg_color="#6c757d",
            hover_color="#5a6268",
            height=40,
            state="disabled",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.stop_btn.grid(row=0, column=3, padx=2, pady=5, sticky="ew")

        # Geliştirici bilgileri
        dev_frame = ctk.CTkFrame(self, fg_color="transparent")
        dev_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        dev_label = ctk.CTkLabel(
            dev_frame,
            text="Geliştirici: Caner Ergün | © 2026 NeoTube Pro v3.0",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        dev_label.pack(side="left", padx=5)

        # Sosyal medya butonları
        social_buttons = [
            ("LinkedIn", "#0A66C2", "https://linkedin.com/in/devseu/"),
            ("GitHub", "#333", "https://github.com/canerergun"),
            ("Instagram", "#C13584", "https://instagram.com/devseu"),
            ("Twitch", "#9146FF", "https://twitch.tv/devseu")
        ]

        for name, color, url in social_buttons:
            btn = ctk.CTkButton(
                dev_frame,
                text=name,
                fg_color=color,
                hover_color=color,
                width=70,
                height=25,
                command=lambda u=url: webbrowser.open(u)
            )
            btn.pack(side="right", padx=2)

    def on_text_modified(self, event):
        """URL metni değiştiğinde"""
        self.url_text.edit_modified(False)

        # Önceki after işlemini iptal et
        if self._resolve_after_id is not None:
            try:
                self.after_cancel(self._resolve_after_id)
            except:
                pass
            self._resolve_after_id = None

        # Yeni after işlemini başlat
        self._resolve_after_id = self.after(800, self.clean_and_resolve_urls)

    def clean_and_resolve_urls(self):
        """URL'leri temizle ve başlıkları çözümle"""
        raw_urls = [u.strip() for u in self.url_text.get("1.0", "end-1c").splitlines() if u.strip()]

        if not raw_urls:
            self.clear_url_list()
            return

        # Eski thread'i durdur
        if self.resolver_thread is not None:
            try:
                if hasattr(self.resolver_thread, 'is_alive') and self.resolver_thread.is_alive():
                    self.resolver_thread.stop()
            except:
                pass

        self.url_titles.clear()
        self.status_label.configure(text="⏳ URL'ler çözümleniyor...")

        self.resolver_thread = TitleResolverThread(
            raw_urls,
            self.update_url_titles,
            self.update_resolve_progress
        )
        self.resolver_thread.start()

        # After ID'yi temizle
        self._resolve_after_id = None

    def update_resolve_progress(self, current, total, message):
        """Çözümleme ilerlemesini güncelle"""
        self.status_label.configure(text=f"⏳ {message} ({current}/{total})")

    def update_url_titles(self, results):
        """URL başlıklarını güncelle"""
        self.url_titles = results
        self.clear_url_list()
        self.url_items.clear()

        # İstatistikleri hesapla
        total = len(results)
        working = sum(1 for v in results.values() if not v.startswith(("❌", "⚠️")))
        failed = total - working

        for idx, (url, title) in enumerate(results.items(), start=1):
            # Güvenli widget oluşturma
            item = URLItem(self.url_list_frame, idx, title, url)
            item.pack(fill="x", padx=5, pady=2, expand=False)

            # Favori kontrolü (oturum için)
            if url in self.favorites:
                item.set_favorite(True)

            # Çift tıklama ile favoriye ekle
            item.bind("<Double-Button-1>", lambda e, u=url: self.toggle_favorite(u))

            self.url_items.append(item)

            # Başlangıç durumu
            if title.startswith("❌"):
                item.set_status("error")
            elif title.startswith("⚠️"):
                item.set_status("skipped")
            else:
                item.set_status("waiting")

        self.stats_label.configure(text=f"📊 Toplam: {total} | Hazır: {working} | Hatalı: {failed}")
        self.status_label.configure(text=f"✅ {working} URL hazır. İndirmeye hazır.")
        self.update_stats()

    def clear_url_list(self):
        """URL listesini güvenli şekilde temizle"""
        try:
            for item in self.url_items:
                try:
                    item.destroy()
                except:
                    pass
            self.url_items.clear()

            # Scrollable frame'in içindeki tüm widget'ları temizle
            for widget in self.url_list_frame.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
        except:
            pass

    def clear_all_urls(self):
        """Tüm URL'leri temizle"""
        self.url_text.delete("1.0", "end")
        self.url_titles.clear()
        self.clear_url_list()
        self.stats_label.configure(text="")
        self.status_label.configure(text="⏸️ Hazır")

    def select_folder(self):
        """İndirme klasörünü seç"""
        folder = filedialog.askdirectory(title="İndirme Klasörü Seç")
        if folder:
            self.download_folder = folder
            self.folder_path.configure(text=folder, text_color="white")

    def toggle_favorite(self, url):
        """URL'yi favorilere ekle/çıkar (sadece oturum için)"""
        if url in self.favorites:
            self.favorites.remove(url)
        else:
            self.favorites.add(url)

        # Görünümü güncelle
        for item, (item_url, _) in zip(self.url_items, self.url_titles.items()):
            if item_url == url:
                item.set_favorite(url in self.favorites)
                break

        # Favori listesini güncelle
        self.update_favorites_display()
        self.update_stats()

    def update_favorites_display(self):
        """Favori listesini güncelle"""
        for widget in self.fav_listbox.winfo_children():
            widget.destroy()

        for url in list(self.favorites)[-10:]:  # Son 10 favori
            frame = ctk.CTkFrame(self.fav_listbox)
            frame.pack(fill="x", padx=2, pady=1)

            label = ctk.CTkLabel(
                frame,
                text=f"★ {url[:50]}...",
                anchor="w",
                fg_color=("gray60", "gray30"),
                corner_radius=3,
                height=20
            )
            label.pack(fill="x", padx=2, pady=1)

            # Tıklanınca URL'yi ekle
            label.bind("<Button-1>", lambda e, u=url: self.add_favorite_to_list(u))

    def add_favorite_to_list(self, url):
        """Favori URL'yi listeye ekle"""
        current_text = self.url_text.get("1.0", "end-1c")
        if current_text:
            self.url_text.insert("end", f"\n{url}")
        else:
            self.url_text.insert("1.0", url)

    def update_stats(self):
        """İstatistikleri güncelle (sadece oturum için)"""
        total_downloads = len(self.download_history)
        total_favorites = len(self.favorites)

        stats_text = f"Bu Oturum:\n"
        stats_text += f"📥 İndirilen: {total_downloads}\n"
        stats_text += f"⭐ Favori: {total_favorites}\n"

        if self.download_history:
            last_download = self.download_history[-1]
            stats_text += f"\nSon İndirme:\n{last_download.get('title', '')[:30]}..."

        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.configure(state="disabled")

    def update_queue_display(self, current, total, title):
        """İndirme kuyruğunu güncelle"""
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        for i in range(current, total + 1):
            item_text = f"{i}. {title}" if i == current else f"{i}. Sırada..."
            item = DownloadQueueItem(self.queue_frame, i, item_text)
            item.pack(fill="x", padx=2, pady=1)

    def start_download(self):
        """İndirme işlemini başlat"""
        urls = list(self.url_titles.keys())

        if not urls:
            messagebox.showwarning("Uyarı", "Lütfen en az bir playlist URL'si girin.")
            return

        if not self.download_folder:
            messagebox.showwarning("Uyarı", "Lütfen indirilecek klasörü seçin.")
            return

        if self.is_downloading:
            messagebox.showinfo("Bilgi", "Zaten bir indirme işlemi devam ediyor.")
            return

        # Hız limitini al
        speed_text = self.speed_var.get()
        speed_limit = None
        if speed_text != "0 (Sınırsız)":
            try:
                speed_limit = int(speed_text.split()[0])
            except:
                pass

        self.is_downloading = True
        self.url_text.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.clear_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")

        # Tüm URL'leri "waiting" durumuna getir
        for item in self.url_items:
            item.set_status("waiting")

        self.download_thread = DownloadThread(
            urls,
            self.url_titles,
            self.download_folder,
            self.format_var.get(),
            self.concurrent_var.get(),
            None,  # proxy
            speed_limit
        )

        # Callback'leri bağla
        self.download_thread.on_progress = self.update_status
        self.download_thread.on_progress_bar = self.update_progress
        self.download_thread.on_current_url = self.highlight_current_url
        self.download_thread.on_url_status = self.update_url_status
        self.download_thread.on_finished = self.on_download_finished
        self.download_thread.on_error = self.on_download_error
        self.download_thread.on_speed_update = self.update_speed
        self.download_thread.on_queue_update = self.update_queue_display

        self.download_thread.start()

    def update_status(self, message):
        """Durum mesajını güncelle"""
        self.status_label.configure(text=message)

    def update_progress(self, value):
        """İlerleme çubuğunu güncelle"""
        self.progress_bar.set(value / 100)

    def update_speed(self, speed, eta):
        """Hız ve ETA bilgilerini güncelle"""
        self.speed_label.configure(text=f"⚡ {speed}")
        self.eta_label.configure(text=f"⏱️ Kalan: {eta}")

    def highlight_current_url(self, url, title):
        """İndirilen URL'yi vurgula"""
        url_list = list(self.url_titles.keys())
        for i, item_url in enumerate(url_list):
            if i < len(self.url_items) and item_url == url:
                self.url_items[i].set_status("downloading")
                break

    def update_url_status(self, url, status, title=None):
        """URL durumunu güncelle"""
        url_list = list(self.url_titles.keys())
        for i, item_url in enumerate(url_list):
            if i < len(self.url_items) and item_url == url:
                self.url_items[i].set_status(status)
                break

        # İndirme geçmişine ekle (sadece oturum için)
        if status == "completed":
            self.download_history.append({
                "url": url,
                "title": title,
                "format": self.format_var.get()
            })
            self.update_stats()

    def pause_download(self):
        """İndirmeyi duraklat"""
        if self.download_thread and hasattr(self.download_thread, 'is_alive') and self.download_thread.is_alive():
            self.download_thread.pause()
            self.status_label.configure(text="⏸️ İndirme duraklatıldı")
            self.pause_btn.configure(state="disabled")
            self.resume_btn.configure(state="normal")

    def resume_download(self):
        """İndirmeye devam et"""
        if self.download_thread and hasattr(self.download_thread, 'is_alive') and self.download_thread.is_alive():
            self.download_thread.resume()
            self.status_label.configure(text="▶️ İndirme devam ediyor...")
            self.pause_btn.configure(state="normal")
            self.resume_btn.configure(state="disabled")

    def stop_download(self):
        """İndirmeyi durdur"""
        if self.download_thread and hasattr(self.download_thread, 'is_alive') and self.download_thread.is_alive():
            result = messagebox.askyesno("Onay", "İndirme işlemini durdurmak istediğinize emin misiniz?")
            if result:
                self.download_thread.stop()
                self.status_label.configure(text="⏹️ İndirme durduruldu")
                self.reset_ui_after_download()

    def on_download_finished(self):
        """İndirme tamamlandığında"""
        elapsed_time = time.time() - self.download_thread.start_time if self.download_thread else 0
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        self.status_label.configure(text=f"✅ Tüm indirmeler tamamlandı! (Süre: {minutes}d {seconds}s)")
        self.progress_bar.set(1.0)

        notification.notify(
            title="NeoTube Pro - İndirme Tamamlandı",
            message=f"{len(self.url_titles)} playlist/video başarıyla indirildi!",
            timeout=5
        )

        messagebox.showinfo("Başarılı",
                            f"Tüm indirmeler başarıyla tamamlandı!\nSüre: {minutes} dakika {seconds} saniye")
        self.reset_ui_after_download()

    def on_download_error(self, error_message):
        """İndirme hatası olduğunda"""
        self.status_label.configure(text=f"❌ Hata oluştu")
        messagebox.showerror("Hata", f"İndirme sırasında hata oluştu:\n{error_message}")

    def reset_ui_after_download(self):
        """İndirme sonrası UI'ı sıfırla"""
        self.is_downloading = False
        self.url_text.configure(state="normal")
        self.download_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.clear_btn.configure(state="normal")

        # Kuyruğu temizle
        for widget in self.queue_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = NeoTubeApp()
    app.mainloop()