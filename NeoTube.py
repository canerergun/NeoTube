#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███╗   ██╗███████╗ ██████╗ ████████╗██╗   ██╗██████╗ ███████╗             ║
║   ████╗  ██║██╔════╝██╔═══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝             ║
║   ██╔██╗ ██║█████╗  ██║   ██║   ██║   ██║   ██║██████╔╝█████╗               ║
║   ██║╚██╗██║██╔══╝  ██║   ██║   ██║   ██║   ██║██╔══██╗██╔══╝               ║
║   ██║ ╚████║███████╗╚██████╔╝   ██║   ╚██████╔╝██████╔╝███████╗             ║
║   ╚═╝  ╚═══╝╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝             ║
║                                                                               ║
║   🚀 NeoTube Pro v5.0 – Ultimate Video Downloader & Converter                ║
║   📥 İndir | 🔄 Dönüştür | ⭐ Favoriler | 📊 İstatistikler | 🌙 Tema        ║
║   🔒 Özel/Üyelik atlama | ⚡ Çoklu indirme | 🎵 Ses çıkarma                  ║
║   🖼️ Küçük resim | 📝 Altyazı | 🌐 Proxy | 🛡️ Hata yönetimi                ║
║   ⏱️ Zamanlama | 💤 Uyku/Kapatma | 📁 Playlist klasörü                       ║
║                                                                               ║
║   📌 Geliştirici: Caner Ergün                                                ║
║   🔗 GitHub: https://github.com/canerergun/neotube                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import importlib
import os
import webbrowser
import re
import threading
import time
import urllib.request
import zipfile
import shutil
import socket
import json
import hashlib
import base64
import random
import string
import queue
import tempfile
import platform
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from tkinter import filedialog, messagebox, simpledialog
from tkinter import Tk, Label, ttk

# ============================================================
# 1. BAĞIMLILIK KONTROLÜ VE OTOMATİK KURULUM (GELİŞMİŞ)
# ============================================================
def install_package(package: str, upgrade: bool = False) -> bool:
    """Paket kurulumu yapar, başarılıysa True döner."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package)
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def check_and_install_dependencies():
    required = ['customtkinter', 'yt_dlp', 'plyer']
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if not missing:
        return  # Hiç eksik yok, devam et
    
    # Eksik paketler var, kullanıcıya bilgi ver ve kurulum yap
    root = Tk()
    root.title("NeoTube Kurulumu")
    root.geometry("450x180")
    root.configure(bg='#2b2b2b')
    root.attributes('-topmost', True)
    
    lbl = Label(
        root,
        text=f"Eksik paketler: {', '.join(missing)}\nKurulum yapılıyor...\nLütfen bekleyin.",
        fg='white', bg='#2b2b2b', font=('Arial', 11), justify='center'
    )
    lbl.pack(pady=25)
    
    progress = ttk.Progressbar(root, length=350, mode='indeterminate')
    progress.pack(pady=15)
    progress.start()
    root.update()

    try:
        for pkg in missing:
            install_package(pkg)
        # yt-dlp'yi güncelle
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        progress.stop()
        progress.destroy()
        Label(
            root,
            text="✅ Kurulum tamamlandı!\nUygulama devam ediyor...",
            fg='#34D399', bg='#2b2b2b', font=('Arial', 11)
        ).pack(pady=15)
        root.update()
        time.sleep(1.5)
        root.destroy()
        # ⛔ YENİDEN BAŞLATMA YOK - sadece kurulum yapıldı ve fonksiyon bitiyor
        return  # <-- BU SATIR ÖNEMLİ: Yeniden başlatma yok, normal devam eder

    except Exception as e:
        root.destroy()
        messagebox.showerror(
            "Kurulum Hatası",
            f"Paket kurulumu başarısız:\n{e}\n\n"
            "Lütfen elle yükleyin:\npip install customtkinter yt-dlp plyer"
        )
        sys.exit(1)  # Hata durumunda çık, ama yeniden başlatma yok



check_and_install_dependencies()

# ============================================================
# 2. İTHALATLAR (KONTROLLÜ)
# ============================================================
import customtkinter as ctk
import yt_dlp
from plyer import notification
from yt_dlp.utils import DownloadCancelled, sanitize_filename
from PIL import Image, ImageTk
import requests

# ============================================================
# 3. SABİTLER VE VERSİYON
# ============================================================
VERSION = "v5.0.0"
APP_NAME = "NeoTube Pro"
AUTHOR = "Caner Ergün"
GITHUB_URL = "https://github.com/canerergun/neotube"
WEBSITE_URL = "https://neotube.dev"
YOUTUBE_CHANNEL = "https://youtube.com/@devseu"
DISCORD_URL = "https://discord.gg/neotube"
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "NeoTube")
MAX_HISTORY_SIZE = 500
MAX_CONCURRENT = 20
DEFAULT_CONCURRENT = 3
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# ============================================================
# 4. ENUMLAR
# ============================================================
class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    WAITING = "waiting"

class QualityPreset(Enum):
    BEST = "best"
    HD_1080P = "1080p"
    HD_720P = "720p"
    SD_480P = "480p"
    SD_360P = "360p"
    AUDIO_MP3_128 = "MP3 (128k)"
    AUDIO_MP3_320 = "MP3 (320k)"
    AUDIO_M4A = "m4a"
    AUDIO_FLAC = "flac"
    VIDEO_ONLY = "video_only"

class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"

class Language(Enum):
    TURKISH = "tr"
    ENGLISH = "en"

class PostAction(Enum):
    NONE = "none"
    OPEN_FOLDER = "open_folder"
    SHUTDOWN = "shutdown"
    SLEEP = "sleep"
    EXIT_APP = "exit_app"
    PLAY_SOUND = "play_sound"

# ============================================================
# 5. DATA CLASSES (GELİŞMİŞ)
# ============================================================
@dataclass
class DownloadItem:
    url: str
    title: str = ""
    status: str = "pending"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    file_path: str = ""
    quality: str = "best"
    format: str = "mp4"
    size: str = ""
    duration: str = ""
    channel: str = ""
    channel_id: str = ""
    thumbnail: str = ""
    date_added: str = ""
    is_playlist: bool = False
    playlist_title: str = ""
    playlist_index: int = 0
    playlist_count: int = 0
    is_members_only: bool = False
    is_private: bool = False
    folder_path: str = ""
    has_subtitles: bool = False
    has_thumbnail: bool = False
    view_count: int = 0
    like_count: int = 0
    upload_date: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadItem":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})

@dataclass
class Settings:
    theme: str = "dark"
    language: str = "tr"
    download_path: str = DEFAULT_DOWNLOAD_PATH
    default_quality: str = "best"
    default_format: str = "mp4"
    concurrent_downloads: int = 3
    max_retries: int = 3
    speed_limit: int = 0
    proxy: str = ""
    user_agent: str = ""
    subtitles: bool = False
    subtitle_lang: str = "tr"
    embed_thumbnail: bool = True
    channel_folder: bool = False
    playlist_folder: bool = True
    video_folder: bool = False
    file_name_template: str = "%(title)s"
    post_action: str = "none"
    auto_resume: bool = True
    notify_on_complete: bool = True
    sound_on_complete: bool = False
    auto_update: bool = True
    check_updates: bool = True
    skip_members_only: bool = True
    skip_private_videos: bool = True
    window_width: int = 1500
    window_height: int = 950
    window_x: int = -1
    window_y: int = -1
    show_speed_in_title: bool = True
    confirm_before_exit: bool = True
    auto_open_folder: bool = False
    keep_history: bool = True
    history_size: int = 500
    debug_mode: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})

@dataclass
class Favorite:
    url: str
    title: str = ""
    channel: str = ""
    date_added: str = ""
    thumbnail: str = ""
    duration: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Favorite":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})

@dataclass
class Stats:
    total_downloads: int = 0
    total_size_bytes: int = 0
    total_size_str: str = "0 B"
    last_download: str = ""
    last_download_time: str = ""
    total_playlists: int = 0
    total_errors: int = 0
    total_skipped: int = 0
    total_favorites: int = 0
    total_duration_seconds: int = 0
    total_duration_str: str = "0:00:00"
    first_download_date: str = ""
    last_activity: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Stats":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})

# ============================================================
# 6. FFMPEG YÖNETİCİSİ (GELİŞMİŞ)
# ============================================================
class FFmpegManager:
    """FFmpeg bulma, indirme ve yönetme sınıfı."""

    @staticmethod
    def find_system_ffmpeg() -> Optional[str]:
        """Sistemde yüklü FFmpeg'i arar."""
        # PATH üzerinden ara
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path

        # Yaygın Windows dizinleri
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            os.path.expanduser(r"~\AppData\Local\ffmpeg\bin\ffmpeg.exe"),
            os.path.expanduser(r"~\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe"),
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path

        # FFMPEG_HOME ortam değişkeni
        ffmpeg_home = os.environ.get('FFMPEG_HOME', '')
        if ffmpeg_home:
            candidate = os.path.join(ffmpeg_home, 'bin', 'ffmpeg.exe')
            if os.path.isfile(candidate):
                return candidate
            candidate = os.path.join(ffmpeg_home, 'ffmpeg.exe')
            if os.path.isfile(candidate):
                return candidate

        # macOS/Linux için common
        if platform.system() != "Windows":
            try:
                result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass

        return None

    @staticmethod
    def download_ffmpeg(progress_callback: Optional[Callable] = None) -> Optional[str]:
        """FFmpeg'i indirir ve kurar."""
        # Önce sistemde var mı kontrol et
        system_path = FFmpegManager.find_system_ffmpeg()
        if system_path:
            return system_path

        # Windows dışında otomatik kurulum yapma (kullanıcıya bırak)
        if platform.system() != "Windows":
            return None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(base_dir, "ffmpeg", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")

        if os.path.exists(ffmpeg_exe):
            return ffmpeg_exe

        # İnternet kontrolü
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
        except OSError:
            return None

        zip_path = os.path.join(base_dir, "ffmpeg_temp.zip")

        try:
            if progress_callback:
                progress_callback(0, "FFmpeg indiriliyor...")

            urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, zip_path)

            if progress_callback:
                progress_callback(30, "FFmpeg arşivi açılıyor...")

            with zipfile.ZipFile(zip_path, 'r') as zf:
                extracted = None
                for member in zf.namelist():
                    if member.endswith("ffmpeg.exe"):
                        zf.extract(member, base_dir)
                        extracted = os.path.join(base_dir, member)
                        break

            if extracted and os.path.isfile(extracted):
                os.makedirs(ffmpeg_dir, exist_ok=True)
                shutil.move(extracted, ffmpeg_exe)
                if os.path.exists(zip_path):
                    os.remove(zip_path)

                if progress_callback:
                    progress_callback(100, "✅ FFmpeg kuruldu!")

                # Temizlik: boş klasörleri sil
                for root, dirs, files in os.walk(base_dir):
                    if root != base_dir and not os.listdir(root):
                        try:
                            os.rmdir(root)
                        except:
                            pass

                return ffmpeg_exe if os.path.isfile(ffmpeg_exe) else None

        except Exception as e:
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            print(f"FFmpeg indirme hatası: {e}")
            return None

        return None

    @staticmethod
    def get_ffmpeg_path(progress_callback: Optional[Callable] = None) -> Optional[str]:
        """FFmpeg yolunu döndürür, yoksa indirmeyi dener."""
        # Önce uygulama dizinindeki ffmpeg.exe'yi kontrol et
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(base_dir, "ffmpeg", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")

        if os.path.exists(ffmpeg_exe):
            return ffmpeg_exe

        # Sistemde ara
        system_path = FFmpegManager.find_system_ffmpeg()
        if system_path:
            return system_path

        # İndirmeyi dene
        return FFmpegManager.download_ffmpeg(progress_callback)

# ============================================================
# 7. YARDIMCI FONKSİYONLAR (GELİŞMİŞ)
# ============================================================
def is_private_video(info: dict) -> bool:
    """Videonun özel olup olmadığını kontrol eder."""
    if info.get('availability') == 'private':
        return True
    if info.get('live_status') == 'is_upcoming' and info.get('release_timestamp'):
        return True
    if info.get('is_private') is True:
        return True
    return False

def is_members_only(info: dict) -> bool:
    """Videonun üyelere özel olup olmadığını kontrol eder."""
    availability = info.get('availability', '')
    if availability in ('premium', 'subscriber_only', 'members_only', 'member_preview'):
        return True
    if info.get('is_premium') or info.get('requires_subscription'):
        return True
    if info.get('is_members_only') is True:
        return True
    return False

def format_duration(seconds: Union[int, float, str]) -> str:
    """Saniyeyi okunabilir süre formatına çevirir."""
    try:
        secs = int(seconds)
        if secs < 0:
            return "0:00"
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except (TypeError, ValueError):
        return "??:??"

def format_size(bytes: int) -> str:
    """Bayt değerini okunabilir boyut formatına çevirir."""
    if bytes is None or bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while bytes >= 1024 and i < len(units) - 1:
        bytes /= 1024
        i += 1
    return f"{bytes:.1f} {units[i]}"

def sanitize_filename_custom(filename: str) -> str:
    """Dosya adını geçersiz karakterlerden arındırır."""
    if not filename:
        return "Unknown"
    # Geçersiz karakterleri temizle
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    # Kontrol karakterlerini temizle
    filename = ''.join(c for c in filename if ord(c) >= 32)
    filename = filename.strip()
    # Uzunluğu sınırla
    if len(filename) > 200:
        filename = filename[:200]
    return filename or "Unknown"

def clean_title(title: str) -> str:
    """Başlıktaki emoji ve özel işaretleri temizler."""
    if not title:
        return "Unknown"
    # Emoji öneklerini temizle
    for prefix in ("📁 ", "🎬 ", "⚠️ ", "❌ ", "🔒 ", "⏳ ", "✅ "):
        title = title.replace(prefix, "")
    return sanitize_filename_custom(title)

def extract_urls(text: str) -> List[str]:
    """Metinden tüm URL'leri çıkarır."""
    pattern = r'https?://[^\s]+'
    return re.findall(pattern, text)

def parse_speed_limit(spd_str: str) -> Optional[int]:
    """Hız limiti metnini MB/s cinsinden çözümler."""
    if not spd_str:
        return None
    spd_str = spd_str.strip()
    if spd_str.startswith("0") or "sınırsız" in spd_str.lower() or "unlimited" in spd_str.lower():
        return None
    try:
        # "5 MB/s" -> 5
        num = re.search(r'(\d+)', spd_str)
        if num:
            return int(num.group(1))
    except:
        pass
    return None

def version_compare(v1: str, v2: str) -> int:
    """Sürüm numaralarını karşılaştırır. -1: v1<v2, 0: eşit, 1: v1>v2"""
    def normalize(v):
        return [int(x) for x in re.sub(r'[^0-9.]', '', v).split('.')]
    a = normalize(v1)
    b = normalize(v2)
    for i in range(min(len(a), len(b))):
        if a[i] < b[i]:
            return -1
        elif a[i] > b[i]:
            return 1
    return len(a) - len(b)

def get_random_user_agent() -> str:
    """Rastgele bir kullanıcı aracı döndürür."""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    return random.choice(agents)

def get_system_info() -> dict:
    """Sistem bilgilerini döndürür."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "processor": platform.processor(),
        "hostname": platform.node(),
    }

# ============================================================
# 8. TEMA YÖNETİCİSİ (GELİŞMİŞ)
# ============================================================
class ThemeManager:
    """Tema yönetimi ve renk paletleri."""

    THEMES = {
        "dark": {
            "bg_primary": "#0A0A14",
            "bg_secondary": "#141424",
            "bg_card": "#1A1A30",
            "bg_input": "#252540",
            "bg_hover": "#2A2A4A",
            "text_primary": "#F0F0F8",
            "text_secondary": "#94A3B8",
            "text_muted": "#64748B",
            "accent": "#3B82F6",
            "accent_hover": "#60A5FA",
            "accent_light": "#1E3A5F",
            "success": "#34D399",
            "success_dark": "#10B981",
            "warning": "#FBBF24",
            "error": "#F87171",
            "border": "#2D2D44",
            "sidebar_bg": "#111122",
            "header_bg": "#141428",
            "button_bg": "#3B82F6",
            "button_hover": "#2563EB",
            "progress_bg": "#1A1A30",
            "progress_fg": "#3B82F6",
            "scrollbar_bg": "#1A1A30",
            "scrollbar_thumb": "#3B82F6",
            "status_bar_bg": "#0A0A14",
        },
        "light": {
            "bg_primary": "#F0F2F8",
            "bg_secondary": "#FFFFFF",
            "bg_card": "#FFFFFF",
            "bg_input": "#E8EAF0",
            "bg_hover": "#E0E4EC",
            "text_primary": "#1A1A2E",
            "text_secondary": "#6B7280",
            "text_muted": "#9CA3AF",
            "accent": "#2563EB",
            "accent_hover": "#1D4ED8",
            "accent_light": "#DBEAFE",
            "success": "#10B981",
            "success_dark": "#059669",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "border": "#E5E7EB",
            "sidebar_bg": "#FFFFFF",
            "header_bg": "#FFFFFF",
            "button_bg": "#2563EB",
            "button_hover": "#1D4ED8",
            "progress_bg": "#E5E7EB",
            "progress_fg": "#2563EB",
            "scrollbar_bg": "#E5E7EB",
            "scrollbar_thumb": "#2563EB",
            "status_bar_bg": "#F0F2F8",
        }
    }

    @classmethod
    def get(cls, theme_name: str) -> dict:
        """Tema renklerini döndürür."""
        return cls.THEMES.get(theme_name, cls.THEMES["dark"])

    @classmethod
    def get_theme_list(cls) -> List[str]:
        """Mevcut temaların listesini döndürür."""
        return list(cls.THEMES.keys())

# ============================================================
# 9. DİL YÖNETİCİSİ (GELİŞMİŞ)
# ============================================================
class LanguageManager:
    """Çoklu dil desteği."""

    STRINGS = {
        "tr": {
            "app_title": "NeoTube Pro - Profesyonel Video İndirici",
            "welcome": "🎬 NeoTube'a Hoş Geldiniz",
            "welcome_desc": "YouTube, Vimeo ve diğer platformlardan video indirin.",
            "url_label": "🔗 Video URL",
            "analyze": "Analiz Et",
            "download": "⬇ İndir",
            "download_all": "Tümünü İndir",
            "options": "⚙ İndirme Seçenekleri",
            "quality": "Kalite",
            "format": "Format",
            "subtitles": "Altyazı İndir",
            "status_ready": "Hazır",
            "status_analyzing": "Analiz ediliyor...",
            "status_downloading": "İndiriliyor...",
            "status_complete": "✅ İndirme tamamlandı!",
            "status_error": "Hata",
            "no_url": "Lütfen bir URL girin!",
            "invalid_url": "Geçersiz URL!",
            "analysis_error": "Analiz Hatası",
            "download_error": "İndirme Hatası",
            "download_success": "Başarılı",
            "history": "📋 İndirme Geçmişi",
            "history_empty": "Henüz indirme geçmişi yok 📭",
            "clear_history": "🗑 Temizle",
            "clear_confirm": "Tüm geçmişi silmek istediğinize emin misiniz?",
            "settings": "⚙ Ayarlar",
            "general": "📁 Genel Ayarlar",
            "download_path": "İndirme Klasörü:",
            "change_path": "Değiştir",
            "default_quality": "Varsayılan Kalite:",
            "save_settings": "💾 Ayarları Kaydet",
            "settings_saved": "Ayarlar kaydedildi!",
            "about": "ℹ Hakkında",
            "about_text": f"NeoTube Pro {VERSION}\n{AUTHOR} tarafından geliştirilmiştir.",
            "favorites": "⭐ Favoriler",
            "add_favorite": "Favoriye Ekle",
            "remove_favorite": "Favoriden Çıkar",
            "export": "Dışa Aktar",
            "import": "İçe Aktar",
            "import_file": "Dosyadan Yükle",
            "batch_add": "Toplu URL Ekle",
            "url_count": "URL Sayısı: {}",
            "paste": "📋 Yapıştır",
            "clear_all": "Tümünü Temizle",
            "converter": "🔄 Dönüştürücü",
            "convert": "Dönüştür",
            "output_format": "Çıktı Formatı",
            "select_files": "Dosya Seç",
            "select_folder": "Klasör Seç",
            "progress": "İlerleme",
            "speed": "Hız",
            "eta": "Kalan Süre",
            "completed": "Tamamlandı",
            "failed": "Başarısız",
            "pending": "Bekliyor",
            "downloading": "İndiriliyor",
            "ready": "Hazır",
            "start_download": "İndirmeyi Başlat",
            "download_completed": "✅ İndirme tamamlandı!",
            "download_failed": "❌ İndirme başarısız!",
            "total_downloads": "Toplam İndirme: {}",
            "total_favorites": "Toplam Favori: {}",
            "last_download": "Son İndirme: {}",
            "members_skipped": "🔒 Atlandı (Üyelik): {}",
            "private_skipped": "🔒 Atlandı (Özel): {}",
            "members_only": "🔒 Üyelik Gerektiriyor",
            "skip_members": "Üyelik Gerektiren Videoları Atl",
            "skip_private": "Özel Videoları Atl",
            "theme_change_blocked": "Tema değiştirilemez: Aktif indirme devam ediyor!",
            "no_active_downloads": "Aktif indirme bulunmuyor 🎉",
            "resolving": "🔍 URL'ler çözümleniyor...",
            "resolving_complete": "✅ {} URL hazır, indirmeye hazır!",
            "resolving_no_urls": "⚠ Hiç geçerli URL bulunamadı!",
            "ffmpeg_downloading": "⬇ FFmpeg indiriliyor...",
            "ffmpeg_error": "FFmpeg yüklenemedi!",
            "internet_error": "🌐 İnternet bağlantısı yok!",
            "convert_ready": "Hazır",
            "convert_starting": "Dönüştürme başlatılıyor...",
            "convert_complete": "✅ Tümü dönüştürüldü!",
            "convert_partial": "⚠ {}/{} başarılı, {} hata!",
            "no_files_selected": "Lütfen dönüştürülecek dosyaları seçin!",
            "ffmpeg_missing": "FFmpeg yüklü değil!",
            "folder_no_media": "Klasörde medya dosyası bulunamadı.",
            "error_log": "Hata Günlüğü",
            "no_error_log": "Hata günlüğü yok.",
            "close": "Kapat",
            "dark": "Koyu",
            "light": "Açık",
            "github": "GitHub",
            "social": "Sosyal Medya",
            "statistics": "📊 İstatistikler",
            "concurrent": "Eşzamanlı İndirme:",
            "speed_limit": "Hız Limiti:",
            "folder": "Klasör:",
            "queue": "📋 Kuyruk",
            "favorites_title": "⭐ Favoriler",
            "stats": "📊 İstatistikler",
            "open_converter": "🔄 Dönüştürücüyü Aç",
            "confirm_exit": "Çıkmak istediğinize emin misiniz?",
            "downloads_tab": "⬇ İndirmeler",
            "history_tab": "📋 Geçmiş",
            "favorites_tab": "⭐ Favoriler",
            "settings_tab": "⚙ Ayarlar",
            "converter_tab": "🔄 Dönüştürücü",
            "about_tab": "ℹ Hakkında",
            "new_update": "🔄 Yeni Güncelleme Mevcut!",
            "update_available": "{} sürümü yayınlandı. Güncellemek ister misiniz?",
            "downloading_update": "Güncelleme indiriliyor...",
            "update_complete": "Güncelleme tamamlandı. Uygulama yeniden başlatılıyor.",
            "update_error": "Güncelleme başarısız oldu.",
            "cancel": "İptal",
            "ok": "Tamam",
            "yes": "Evet",
            "no": "Hayır",
            "all": "Tümü",
            "none": "Hiçbiri",
            "select_all": "Tümünü Seç",
            "deselect_all": "Seçimi Kaldır",
            "invert_selection": "Seçimi Ters Çevir",
            "delete_selected": "Seçilenleri Sil",
            "no_selection": "Seçim yapılmadı.",
            "confirm_delete": "Seçilen öğeleri silmek istediğinize emin misiniz?",
            "playlist_folder": "Playlist klasörü oluştur",
            "channel_folder": "Kanal klasörü oluştur",
            "video_folder": "Video klasörü oluştur",
            "embed_thumbnail": "Küçük resim ekle",
            "file_name_template": "Dosya adı şablonu:",
            "post_action": "İndirme sonrası eylem:",
            "notify_on_complete": "Bildirim göster",
            "sound_on_complete": "Ses çal",
            "auto_resume": "Devam et (kesintiden sonra)",
            "check_updates": "Başlangıçta güncelleme kontrol et",
            "skip_members": "Üyelik videolarını atla",
            "skip_private": "Özel videoları atla",
            "show_speed_in_title": "Başlıkta hızı göster",
            "confirm_before_exit": "Çıkışta onay iste",
            "auto_open_folder": "İndirme sonrası klasörü aç",
            "keep_history": "Geçmişi sakla",
            "history_size": "Geçmiş boyutu:",
            "debug_mode": "Hata ayıklama modu",
            "proxy": "Proxy (opsiyonel):",
            "user_agent": "Kullanıcı aracı:",
            "subtitle_lang": "Altyazı dili:",
            "language": "Dil:",
            "theme": "Tema:",
            "reset_settings": "Ayarları Sıfırla",
            "reset_confirm": "Tüm ayarları varsayılana döndürmek istediğinize emin misiniz?",
            "reset_done": "Ayarlar sıfırlandı.",
            "export_history": "Geçmişi dışa aktar",
            "import_history": "Geçmişi içe aktar",
            "export_favorites": "Favorileri dışa aktar",
            "import_favorites": "Favorileri içe aktar",
            "file": "Dosya",
            "edit": "Düzenle",
            "view": "Görünüm",
            "help": "Yardım",
            "donate": "Bağış Yap",
            "support": "Destek",
            "report_bug": "Hata Bildir",
            "feature_request": "Özellik Öner",
            "documentation": "Dokümantasyon",
            "license": "Lisans",
            "privacy_policy": "Gizlilik Politikası",
            "terms_of_service": "Kullanım Şartları",
        },
        "en": {
            "app_title": "NeoTube Pro - Professional Video Downloader",
            "welcome": "🎬 Welcome to NeoTube",
            "welcome_desc": "Download videos from YouTube, Vimeo and more.",
            "url_label": "🔗 Video URL",
            "analyze": "Analyze",
            "download": "⬇ Download",
            "download_all": "Download All",
            "options": "⚙ Download Options",
            "quality": "Quality",
            "format": "Format",
            "subtitles": "Download Subtitles",
            "status_ready": "Ready",
            "status_analyzing": "Analyzing...",
            "status_downloading": "Downloading...",
            "status_complete": "✅ Download complete!",
            "status_error": "Error",
            "no_url": "Please enter a URL!",
            "invalid_url": "Invalid URL!",
            "analysis_error": "Analysis Error",
            "download_error": "Download Error",
            "download_success": "Success",
            "history": "📋 Download History",
            "history_empty": "No download history yet 📭",
            "clear_history": "🗑 Clear",
            "clear_confirm": "Are you sure you want to clear all history?",
            "settings": "⚙ Settings",
            "general": "📁 General Settings",
            "download_path": "Download Folder:",
            "change_path": "Change",
            "default_quality": "Default Quality:",
            "save_settings": "💾 Save Settings",
            "settings_saved": "Settings saved!",
            "about": "ℹ About",
            "about_text": f"NeoTube Pro {VERSION}\nDeveloped by {AUTHOR}",
            "favorites": "⭐ Favorites",
            "add_favorite": "Add to Favorites",
            "remove_favorite": "Remove from Favorites",
            "export": "Export",
            "import": "Import",
            "import_file": "Import from File",
            "batch_add": "Add Multiple URLs",
            "url_count": "URL Count: {}",
            "paste": "📋 Paste",
            "clear_all": "Clear All",
            "converter": "🔄 Converter",
            "convert": "Convert",
            "output_format": "Output Format",
            "select_files": "Select Files",
            "select_folder": "Select Folder",
            "progress": "Progress",
            "speed": "Speed",
            "eta": "ETA",
            "completed": "Completed",
            "failed": "Failed",
            "pending": "Pending",
            "downloading": "Downloading",
            "ready": "Ready",
            "start_download": "Start Download",
            "download_completed": "✅ Download completed!",
            "download_failed": "❌ Download failed!",
            "total_downloads": "Total Downloads: {}",
            "total_favorites": "Total Favorites: {}",
            "last_download": "Last Download: {}",
            "members_skipped": "🔒 Skipped (Members): {}",
            "private_skipped": "🔒 Skipped (Private): {}",
            "members_only": "🔒 Members Only",
            "skip_members": "Skip Members-Only Videos",
            "skip_private": "Skip Private Videos",
            "theme_change_blocked": "Cannot change theme: Active download in progress!",
            "no_active_downloads": "No active downloads 🎉",
            "resolving": "🔍 Resolving URLs...",
            "resolving_complete": "✅ {} URLs ready to download!",
            "resolving_no_urls": "⚠ No valid URLs found!",
            "ffmpeg_downloading": "⬇ Downloading FFmpeg...",
            "ffmpeg_error": "Failed to install FFmpeg!",
            "internet_error": "🌐 No internet connection!",
            "convert_ready": "Ready",
            "convert_starting": "Starting conversion...",
            "convert_complete": "✅ All converted!",
            "convert_partial": "⚠ {}/{} succeeded, {} failed!",
            "no_files_selected": "Please select files to convert!",
            "ffmpeg_missing": "FFmpeg is not installed!",
            "folder_no_media": "No media files found in folder.",
            "error_log": "Error Log",
            "no_error_log": "No error log.",
            "close": "Close",
            "dark": "Dark",
            "light": "Light",
            "github": "GitHub",
            "social": "Social Media",
            "statistics": "📊 Statistics",
            "concurrent": "Concurrent Downloads:",
            "speed_limit": "Speed Limit:",
            "folder": "Folder:",
            "queue": "📋 Queue",
            "favorites_title": "⭐ Favorites",
            "stats": "📊 Statistics",
            "open_converter": "🔄 Open Converter",
            "confirm_exit": "Are you sure you want to exit?",
            "downloads_tab": "⬇ Downloads",
            "history_tab": "📋 History",
            "favorites_tab": "⭐ Favorites",
            "settings_tab": "⚙ Settings",
            "converter_tab": "🔄 Converter",
            "about_tab": "ℹ About",
            "new_update": "🔄 New Update Available!",
            "update_available": "{} version is available. Would you like to update?",
            "downloading_update": "Downloading update...",
            "update_complete": "Update complete. Application will restart.",
            "update_error": "Update failed.",
            "cancel": "Cancel",
            "ok": "OK",
            "yes": "Yes",
            "no": "No",
            "all": "All",
            "none": "None",
            "select_all": "Select All",
            "deselect_all": "Deselect All",
            "invert_selection": "Invert Selection",
            "delete_selected": "Delete Selected",
            "no_selection": "No selection.",
            "confirm_delete": "Are you sure you want to delete selected items?",
            "playlist_folder": "Create playlist folder",
            "channel_folder": "Create channel folder",
            "video_folder": "Create video folder",
            "embed_thumbnail": "Embed thumbnail",
            "file_name_template": "File name template:",
            "post_action": "Post-download action:",
            "notify_on_complete": "Show notification",
            "sound_on_complete": "Play sound",
            "auto_resume": "Auto-resume (after interruption)",
            "check_updates": "Check for updates on startup",
            "skip_members": "Skip members-only videos",
            "skip_private": "Skip private videos",
            "show_speed_in_title": "Show speed in title",
            "confirm_before_exit": "Confirm before exit",
            "auto_open_folder": "Open folder after download",
            "keep_history": "Keep history",
            "history_size": "History size:",
            "debug_mode": "Debug mode",
            "proxy": "Proxy (optional):",
            "user_agent": "User agent:",
            "subtitle_lang": "Subtitle language:",
            "language": "Language:",
            "theme": "Theme:",
            "reset_settings": "Reset Settings",
            "reset_confirm": "Are you sure you want to reset all settings to default?",
            "reset_done": "Settings reset.",
            "export_history": "Export history",
            "import_history": "Import history",
            "export_favorites": "Export favorites",
            "import_favorites": "Import favorites",
            "file": "File",
            "edit": "Edit",
            "view": "View",
            "help": "Help",
            "donate": "Donate",
            "support": "Support",
            "report_bug": "Report Bug",
            "feature_request": "Feature Request",
            "documentation": "Documentation",
            "license": "License",
            "privacy_policy": "Privacy Policy",
            "terms_of_service": "Terms of Service",
        }
    }

    @classmethod
    def get(cls, lang: str, key: str) -> str:
        """Belirtilen dil ve anahtar için metni döndürür."""
        return cls.STRINGS.get(lang, cls.STRINGS["tr"]).get(key, key)

    @classmethod
    def get_languages(cls) -> List[str]:
        """Mevcut dillerin listesini döndürür."""
        return list(cls.STRINGS.keys())

# ============================================================
# 10. ÖZEL WIDGET'LAR (GELİŞMİŞ)
# ============================================================
class ModernCard(ctk.CTkFrame):
    """Modern kart widget'ı."""
    def __init__(self, master, theme: dict, **kwargs):
        self.theme = theme
        super().__init__(
            master,
            fg_color=theme["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=theme["border"],
            **kwargs
        )

class ModernButton(ctk.CTkButton):
    """Modern buton widget'ı."""
    def __init__(self, master, theme: dict, text: str, command=None,
                 icon: str = "", width: int = 120, height: int = 40,
                 font_size: int = 13, variant: str = "primary", **kwargs):
        self.theme = theme
        colors = {
            "primary": (theme["button_bg"], theme["button_hover"]),
            "secondary": (theme["bg_input"], theme["bg_hover"]),
            "success": ("#10B981", "#059669"),
            "danger": ("#EF4444", "#DC2626"),
            "warning": ("#F59E0B", "#D97706"),
            "info": ("#3B82F6", "#2563EB"),
        }
        bg, hover = colors.get(variant, colors["primary"])
        display_text = f"{icon} {text}" if icon else text
        super().__init__(
            master,
            text=display_text,
            command=command,
            width=width,
            height=height,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"),
            fg_color=bg,
            hover_color=hover,
            text_color="white" if variant in ("primary", "success", "danger", "warning", "info") else theme["text_primary"],
            **kwargs
        )

class ModernEntry(ctk.CTkEntry):
    """Modern giriş kutusu."""
    def __init__(self, master, theme: dict, placeholder: str = "",
                 width: int = 300, height: int = 44, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=theme["bg_input"],
            text_color=theme["text_primary"],
            placeholder_text=placeholder,
            placeholder_text_color=theme["text_muted"],
            border_color=theme["border"],
            border_width=1,
            **kwargs
        )

class ModernTextArea(ctk.CTkTextbox):
    """Modern metin alanı."""
    def __init__(self, master, theme: dict, height: int = 100, **kwargs):
        super().__init__(
            master,
            height=height,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=theme["bg_input"],
            text_color=theme["text_primary"],
            border_color=theme["border"],
            border_width=1,
            **kwargs
        )

class ModernProgressBar(ctk.CTkProgressBar):
    """Modern ilerleme çubuğu."""
    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(
            master,
            corner_radius=6,
            fg_color=theme["progress_bg"],
            progress_color=theme["progress_fg"],
            **kwargs
        )

class StatusBadge(ctk.CTkLabel):
    """Durum rozeti."""
    STATUS_COLORS = {
        "waiting": ("gray70", "gray25"),
        "pending": ("gray70", "gray25"),
        "downloading": ("#ffcc00", "#806600"),
        "completed": ("#28a745", "#1a6e2e"),
        "error": ("#dc3545", "#a71d2a"),
        "skipped": ("#007bff", "#004d99"),
        "private": ("#6c757d", "#4a4a4a"),
        "cancelled": ("#6c757d", "#4a4a4a"),
    }

    STATUS_ICONS = {
        "waiting": "⏳",
        "pending": "⏳",
        "downloading": "⏬",
        "completed": "✅",
        "error": "❌",
        "skipped": "⏭️",
        "private": "🔒",
        "cancelled": "⏹️",
    }

    def __init__(self, master, status: str = "waiting", **kwargs):
        color = self.STATUS_COLORS.get(status, ("gray70", "gray25"))
        icon = self.STATUS_ICONS.get(status, "⏳")
        super().__init__(
            master,
            text=icon,
            font=ctk.CTkFont(size=16),
            **kwargs
        )
        self.status = status
        self._apply_color(color)

    def _apply_color(self, color):
        if isinstance(color, tuple):
            self.configure(fg_color=color)
        else:
            self.configure(fg_color=color)

    def set_status(self, status: str):
        self.status = status
        color = self.STATUS_COLORS.get(status, ("gray70", "gray25"))
        icon = self.STATUS_ICONS.get(status, "⏳")
        self.configure(text=icon)
        self._apply_color(color)

# ============================================================
# 11. TITLE RESOLVER THREAD (GELİŞMİŞ - DÜZELTİLMİŞ)
# ============================================================
class TitleResolverThread(threading.Thread):
    """URL'leri çözümleyen, başlıkları ve playlist adlarını alan thread."""

    def __init__(self, urls: List[str], callback: Callable,
                 progress_callback: Optional[Callable] = None,
                 skip_private: bool = True, skip_members: bool = True):
        super().__init__(daemon=True)
        self.urls = urls
        self.callback = callback
        self.progress_callback = progress_callback
        self.skip_private = skip_private
        self.skip_members = skip_members
        self._stop_flag = False
        self._results: Dict[str, str] = {}
        self._playlist_names: Dict[str, str] = {}
        self._metadata: Dict[str, dict] = {}

    def run(self):
        ydl_opts = {
            'quiet': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'user_agent': get_random_user_agent(),
        }

        for i, url in enumerate(self.urls):
            if self._stop_flag:
                break

            if self.progress_callback:
                self.progress_callback(i + 1, len(self.urls), f"Çözümleniyor: {url[:50]}...")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    if info is None:
                        self._results[url] = f"⚠️ {url} (Çözümlenemedi)"
                        continue

                    self._metadata[url] = info

                    if self.skip_private and is_private_video(info):
                        self._results[url] = f"🔒 {url} (Özel video - atlandı)"
                        continue
                    if self.skip_members and is_members_only(info):
                        self._results[url] = f"🔒 {url} (Üyelik gerektiriyor - atlandı)"
                        continue

                    title = info.get("title") or url

                    # ========== PLAYLIST ADI ALMA (GELİŞMİŞ) ==========
                    playlist_title = None

                    # 1. Eğer _type 'playlist' ise, title'ı doğrudan kullan
                    if info.get('_type') == 'playlist':
                        playlist_title = info.get('title', '')
                        if playlist_title:
                            # "(Playlist - 161 video)" gibi ekleri temizle
                            playlist_title = re.sub(r'\s*\(Playlist\s*-\s*\d+\s*video\)', '', playlist_title, flags=re.IGNORECASE)
                            playlist_title = playlist_title.strip()
                            print(f"[PLAYLIST] title'den alındı: {playlist_title}")

                    # 2. Eğer olmadıysa, eski yöntemleri dene
                    if not playlist_title:
                        if info.get('playlist_title'):
                            playlist_title = info['playlist_title']
                        elif info.get('playlist') and isinstance(info['playlist'], str):
                            playlist_title = info['playlist']
                        elif info.get('playlist') and isinstance(info['playlist'], dict):
                            playlist_title = info['playlist'].get('title')

                    # 3. En son çare: URL'den list= parametresini al
                    if not playlist_title:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(url)
                        query = urllib.parse.parse_qs(parsed.query)
                        list_id = query.get('list', [None])[0]
                        if list_id:
                            playlist_title = f"Playlist_{list_id}"
                            print(f"[PLAYLIST] URL'den ID alındı: {playlist_title}")

                    if playlist_title:
                        self._playlist_names[url] = str(playlist_title)
                        print(f"[PLAYLIST] {url[:60]} -> {playlist_title}")
                    else:
                        # Debug
                        print(f"[DEBUG] info keys: {list(info.keys())}")
                        print(f"[DEBUG] playlist_title: {info.get('playlist_title')}")
                        print(f"[DEBUG] playlist: {info.get('playlist')}")

                    # Sonuç metni
                    if 'entries' in info:
                        entries = info.get('entries') or []
                        count = len(list(entries))
                        self._results[url] = f"📁 {title} (Playlist - {count} video)"
                    else:
                        dur = info.get('duration')
                        if dur:
                            self._results[url] = f"🎬 {title} ({format_duration(dur)})"
                        else:
                            self._results[url] = f"🎬 {title}"

            except Exception as exc:
                err = str(exc).lower()
                if "private" in err or "sign in" in err:
                    self._results[url] = f"🔒 {url} (Özel video - erişim yok)"
                elif "members" in err or "premium" in err:
                    self._results[url] = f"🔒 {url} (Üyelik gerektiriyor)"
                else:
                    self._results[url] = f"❌ {url} (Hata: {str(exc)[:40]})"

        self.callback(self._results, self._playlist_names, self._metadata)

    def stop(self):
        self._stop_flag = True

# ============================================================
# 12. DOWNLOAD THREAD (GELİŞMİŞ)
# ============================================================
FORMAT_MAP = {
    "best":         "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p":        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "720p":         "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
    "480p":         "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
    "360p":         "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
    "MP3 (128k)":   "bestaudio/best",
    "MP3 (320k)":   "bestaudio/best",
    "m4a":          "bestaudio/best",
    "flac":         "bestaudio/best",
    "video_only":   "bestvideo[ext=mp4]",
}

AUDIO_CODECS = {
    "mp3": {"codec": "libmp3lame", "quality": "192k"},
    "m4a": {"codec": "aac", "quality": "192k"},
    "flac": {"codec": "flac", "quality": "5"},
    "wav": {"codec": "pcm_s16le", "quality": None},
    "aac": {"codec": "aac", "quality": "192k"},
    "ogg": {"codec": "libvorbis", "quality": "5"},
}

class DownloadThread(threading.Thread):
    """Tüm URL'leri sırayla indirir, hataları atlar, pop-up açmaz."""

    def __init__(self, urls: List[str], titles: Dict[str, str],
                 playlist_names: Dict[str, str], metadata: Dict[str, dict],
                 save_path: str, fmt: str = "best",
                 concurrent: int = 3, proxy: Optional[str] = None,
                 speed_limit: Optional[int] = None, ffmpeg: Optional[str] = None,
                 subtitles: bool = False, subtitle_lang: str = "tr",
                 embed_thumbnail: bool = True, skip_private: bool = True,
                 skip_members: bool = True, file_template: str = "%(title)s",
                 post_action: str = "none", notify: bool = True,
                 playlist_folder: bool = True, channel_folder: bool = False,
                 video_folder: bool = False):
        super().__init__(daemon=True)
        self.urls = urls
        self.titles = titles
        self.playlist_names = playlist_names
        self.metadata = metadata
        self.save_path = save_path
        self.fmt = fmt
        self.concurrent = concurrent if ffmpeg else 1
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.ffmpeg = ffmpeg
        self.subtitles = subtitles
        self.subtitle_lang = subtitle_lang
        self.embed_thumbnail = embed_thumbnail
        self.skip_private = skip_private
        self.skip_members = skip_members
        self.file_template = file_template
        self.post_action = post_action
        self.notify = notify
        self.playlist_folder = playlist_folder
        self.channel_folder = channel_folder
        self.video_folder = video_folder

        self._pause = False
        self._stop = False
        self.idx = 0
        self.total = len(urls)
        self.start_time = None
        self.completed_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self._lock = threading.Lock()

        # Callbacks
        self.cb_progress = None
        self.cb_status = None
        self.cb_done = None
        self.cb_current = None
        self.cb_bar = None
        self.cb_error = None
        self.cb_speed = None
        self.cb_queue = None
        self.cb_eta = None
        self.cb_item_complete = None
        self.cb_skip = None

    def _make_hook(self, item_index: int):
        def hook(d):
            if self._stop:
                raise DownloadCancelled()
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                pct = int(downloaded / total * 100) if total else 0
                if self.cb_bar:
                    self.cb_bar(pct)
                spd = d.get('speed', 0)
                if spd and self.cb_speed:
                    mb = spd / 1024 / 1024
                    eta = d.get('eta', 0) or 0
                    eta_str = f"{eta // 60}:{eta % 60:02d}"
                    self.cb_speed(f"{mb:.1f} MB/s", eta_str)
                if self.cb_eta:
                    eta = d.get('eta', 0) or 0
                    if eta > 0:
                        self.cb_eta(f"{eta // 60}:{eta % 60:02d}")
            elif d['status'] == 'finished':
                if self.cb_bar:
                    self.cb_bar(100)
        return hook

    def _build_opts(self, folder: str, outtmpl: str, selector: str,
                    post_processors: List[dict], item: DownloadItem) -> dict:
        opts = {
            "outtmpl": outtmpl,
            "format": selector,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "progress_hooks": [self._make_hook(item.playlist_index or self.idx)],
            "noplaylist": False,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": self.concurrent,
            "postprocessors": post_processors,
            "user_agent": get_random_user_agent(),
            "verbose": False,
            "no_progress": True,
            "socket_timeout": 30,
            "extract_flat": False,
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        if self.speed_limit:
            opts["ratelimit"] = int(self.speed_limit * 1024 * 1024)
        if self.ffmpeg:
            opts["ffmpeg_location"] = self.ffmpeg
        if self.subtitles:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = [self.subtitle_lang]
            opts["writeautomaticsub"] = True
        return opts

    def _get_folder_structure(self, url: str, video_title: str) -> str:
        """Playlist, kanal ve video klasörlerini iç içe oluşturur."""
        folder = self.save_path

        # 1. Playlist klasörü
        if self.playlist_folder and url in self.playlist_names:
            playlist_name = self.playlist_names[url]
            playlist_clean = clean_title(playlist_name)
            folder = os.path.join(folder, playlist_clean)
            print(f"[DOWNLOAD] Playlist klasörü: {folder}")

        # 2. Kanal klasörü (isteğe bağlı)
        if self.channel_folder and url in self.metadata:
            channel = self.metadata[url].get('uploader', '')
            if channel:
                folder = os.path.join(folder, clean_title(channel))

        # 3. Video klasörü (isteğe bağlı)
        if self.video_folder:
            folder = os.path.join(folder, video_title)

        return folder

    def run(self):
        self.start_time = time.time()
        print(f"[DOWNLOAD] Toplam {self.total} URL işlenecek.")

        for i, url in enumerate(self.urls, start=1):
            self.idx = i
            print(f"[DOWNLOAD] {i}/{self.total} - İşleniyor: {url[:60]}...")

            if self._stop:
                break

            while self._pause and not self._stop:
                time.sleep(0.2)

            raw_title = self.titles.get(url, f"URL {i}")
            print(f"[DOWNLOAD] Başlık: {raw_title[:50]}")

            # Özel, üyelik veya hatalı URL'leri atla
            if raw_title.startswith("🔒"):
                if self.cb_skip:
                    self.cb_skip(url, "private", raw_title)
                self.skipped_count += 1
                continue
            if raw_title.startswith("❌"):
                if self.cb_skip:
                    self.cb_skip(url, "error", raw_title)
                self.error_count += 1
                continue
            if raw_title.startswith("⚠️"):
                if self.cb_skip:
                    self.cb_skip(url, "skipped", raw_title)
                self.skipped_count += 1
                continue

            clean = clean_title(raw_title)

            if self.cb_current:
                self.cb_current(url, clean)
            if self.cb_queue:
                self.cb_queue(i, self.total, clean)
            if self.cb_progress:
                self.cb_progress(f"📥 {i}/{self.total} - İndiriliyor: {clean}")

            # ========== KLASÖR OLUŞTUR ==========
            try:
                folder = self._get_folder_structure(url, clean)
                os.makedirs(folder, exist_ok=True)
                print(f"[DOWNLOAD] Klasör: {folder}")
            except Exception as e:
                err = f"Klasör oluşturulamadı: {e}"
                print(f"[ERROR] {err}")
                if self.cb_error:
                    self.cb_error(err)
                self.error_count += 1
                continue  # sonraki URL'ye geç

            # ========== İNDİRME ==========
            fmt = self.fmt
            selector = FORMAT_MAP.get(fmt, FORMAT_MAP["best"])
            post_processors = []

            is_audio = fmt in ("MP3 (128k)", "MP3 (320k)", "m4a", "flac", "wav", "aac", "ogg")
            if is_audio and self.ffmpeg:
                audio_fmt = "mp3" if fmt.startswith("MP3") else fmt
                codec_info = AUDIO_CODECS.get(audio_fmt, {"codec": "libmp3lame", "quality": "192k"})
                quality = "0" if fmt == "MP3 (320k)" else "5" if fmt == "MP3 (128k)" else codec_info.get("quality", "192k")
                post_processors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_fmt,
                    'preferredquality': quality,
                }]
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")

            if self.embed_thumbnail and not is_audio:
                post_processors.append({'key': 'EmbedThumbnail'})

            if self.file_template and self.file_template != "%(title)s":
                template = self.file_template
                template = template.replace("{title}", "%(title)s")
                template = template.replace("{channel}", "%(uploader)s")
                template = template.replace("{id}", "%(id)s")
                template = template.replace("{date}", "%(upload_date)s")
                outtmpl = os.path.join(folder, f"{template}.%(ext)s")

            opts = self._build_opts(folder, outtmpl, selector, post_processors, DownloadItem(url=url))

            try:
                print(f"[DOWNLOAD] Başlanıyor: {url[:60]}...")
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                if info:
                    item = DownloadItem(
                        url=url,
                        title=info.get('title', clean),
                        status="completed",
                        quality=fmt,
                        format=fmt,
                        channel=info.get('uploader', ''),
                        duration=format_duration(info.get('duration', 0)),
                        folder_path=folder,
                        is_playlist=bool(info.get('playlist')),
                        playlist_title=self.playlist_names.get(url, ''),
                        playlist_index=info.get('playlist_index', 0),
                        playlist_count=info.get('playlist_count', 0),
                        view_count=info.get('view_count', 0),
                        like_count=info.get('like_count', 0),
                        upload_date=info.get('upload_date', ''),
                    )
                    try:
                        real_path = ydl.prepare_filename(info)
                        if os.path.exists(real_path):
                            item.size = format_size(os.path.getsize(real_path))
                            item.file_path = real_path
                    except:
                        pass

                    self.completed_count += 1
                    if self.cb_item_complete:
                        self.cb_item_complete(item)

                if self.cb_status:
                    self.cb_status(url, "completed", clean)

                print(f"[DOWNLOAD] Tamamlandı: {clean[:40]}")

            except DownloadCancelled:
                print("[DOWNLOAD] Kullanıcı tarafından durduruldu.")
                break  # döngüyü kır

            except Exception as exc:
                # Her türlü hata burada yakalanır ve devam edilir
                if self.cb_bar:
                    self.cb_bar(0)
                msg = str(exc).lower()
                if "private" in msg or "sign in" in msg:
                    status = "private"
                    log = f"🔒 {i}/{self.total} - Özel video atlandı: {clean}"
                elif "members" in msg:
                    status = "skipped"
                    log = f"⚠️ {i}/{self.total} - Üyelere özel atlandı: {clean}"
                else:
                    status = "error"
                    log = f"❌ {i}/{self.total} - Hata: {clean}"
                    self.error_count += 1
                    if self.cb_error:
                        self.cb_error(f"Hata ({clean}):\n{str(exc)[:120]}")

                print(f"[ERROR] {log}")
                if self.cb_progress:
                    self.cb_progress(log)
                if self.cb_status:
                    self.cb_status(url, status, clean)

        # Tüm URL'ler işlendi
        print(f"[DOWNLOAD] Tüm işlemler bitti. Başarılı: {self.completed_count}, Hata: {self.error_count}, Atlanan: {self.skipped_count}")
        if self.cb_done:
            self.cb_done()

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def stop(self):
        self._stop = True

# ============================================================
# 13. CONVERTER WINDOW (GELİŞMİŞ)
# ============================================================
class ConverterWindow(ctk.CTkToplevel):
    """Dönüştürücü penceresi."""

    AUDIO_CODEC_MAP = {
        "mp3":  ["-acodec", "libmp3lame", "-ab", "192k"],
        "wma":  ["-acodec", "wmav2", "-ab", "192k"],
        "aac":  ["-acodec", "aac", "-b:a", "192k"],
        "flac": ["-acodec", "flac", "-compression_level", "5"],
        "ogg":  ["-acodec", "libvorbis", "-qscale:a", "5"],
        "m4a":  ["-acodec", "aac", "-b:a", "192k", "-f", "ipod"],
        "wav":  ["-acodec", "pcm_s16le"],
        "WAV (22050 Hz)": ["-acodec", "pcm_s16le", "-ac", "1", "-ar", "22050"],
    }

    def __init__(self, master):
        super().__init__(master)
        self.title("NeoTube Dönüştürücü")
        self.geometry("850x700")
        self.minsize(700, 560)
        self.resizable(True, True)

        self.master_app = master
        self.files: List[str] = []
        self.out_fmt = ctk.StringVar(value="mp3")
        self.out_dir = ""
        self.trim_silence = ctk.BooleanVar(value=False)
        self.normalize_audio = ctk.BooleanVar(value=False)
        self.bitrate_var = ctk.StringVar(value="192k")
        self.file_widgets: List[Tuple[ctk.CTkLabel, str]] = []

        self.ffmpeg_path = getattr(master, 'ffmpeg_path', None)

        self._build_ui()
        self._check_ffmpeg()
        self.lift()
        self.focus_force()

    def _check_ffmpeg(self):
        ok = bool(self.ffmpeg_path and os.path.isfile(self.ffmpeg_path))
        if ok:
            self.conv_btn.configure(state="normal", text="🔄 Başlat")
            self.stat_lbl.configure(text="Hazır")
        else:
            self.conv_btn.configure(state="disabled", text="❌ FFmpeg Yok")
            self.stat_lbl.configure(text="HATA: FFmpeg bulunamadı, dönüştürme yapılamaz.")

    def bring_to_front(self):
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # Başlık
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
        ctk.CTkLabel(
            header,
            text="🔄 Medya Dönüştürücü",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        # Girdi seçimi
        inp = ctk.CTkFrame(self)
        inp.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        inp.grid_columnconfigure(0, weight=1)

        self.src_lbl = ctk.CTkLabel(
            inp, text="Hiçbir dosya seçilmedi", height=30,
            fg_color=("gray75", "gray25"), corner_radius=5, anchor="w"
        )
        self.src_lbl.grid(row=0, column=0, sticky="ew", padx=(8, 8), pady=5)

        btn_row = ctk.CTkFrame(inp, fg_color="transparent")
        btn_row.grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_row, text="📁 Dosya", width=90, command=self._add_files).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="📂 Klasör", width=90, command=self._add_folder).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑️ Temizle", width=80, fg_color="gray", command=self._clear).pack(side="left", padx=2)

        # Format & Ayarlar
        fmt_row = ctk.CTkFrame(self)
        fmt_row.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        fmt_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fmt_row, text="🎵 Format:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.format_menu = ctk.CTkOptionMenu(
            fmt_row,
            values=["mp3", "wma", "aac", "flac", "ogg", "m4a", "wav", "WAV (22050 Hz)"],
            variable=self.out_fmt, width=150
        )
        self.format_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(fmt_row, text="Bitrate:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        bitrate_menu = ctk.CTkOptionMenu(
            fmt_row,
            values=["64k", "96k", "128k", "192k", "256k", "320k", "lossless"],
            variable=self.bitrate_var, width=100
        )
        bitrate_menu.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        ctk.CTkCheckBox(
            fmt_row, text="✂️ Sessizlikleri kes (deneysel)",
            variable=self.trim_silence
        ).grid(row=0, column=4, padx=10, pady=5, sticky="w")

        ctk.CTkCheckBox(
            fmt_row, text="🔊 Normalize ses",
            variable=self.normalize_audio
        ).grid(row=0, column=5, padx=10, pady=5, sticky="w")

        # Çıktı klasörü
        out_row = ctk.CTkFrame(self)
        out_row.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)

        self.out_lbl = ctk.CTkLabel(
            out_row, text="Varsayılan: Kaynak ile aynı klasör", height=30,
            fg_color=("gray75", "gray25"), corner_radius=5, anchor="w"
        )
        self.out_lbl.grid(row=0, column=0, sticky="ew", padx=(8, 8), pady=5)
        ctk.CTkButton(out_row, text="📁 Değiştir", width=110, command=self._pick_out).grid(row=0, column=1, padx=8, pady=5)

        # Dosya listesi
        ctk.CTkLabel(self, text="📋 Dosyalar:", font=ctk.CTkFont(weight="bold")).grid(
            row=4, column=0, padx=20, pady=(8, 0), sticky="w"
        )
        self.listbox = ctk.CTkScrollableFrame(self, height=220)
        self.listbox.grid(row=5, column=0, padx=20, pady=8, sticky="nsew")

        # İlerleme
        self.pbar = ctk.CTkProgressBar(self)
        self.pbar.grid(row=6, column=0, padx=20, pady=(5, 0), sticky="ew")
        self.pbar.set(0)

        self.stat_lbl = ctk.CTkLabel(self, text="Hazır")
        self.stat_lbl.grid(row=7, column=0, padx=20, pady=5)

        self.conv_btn = ctk.CTkButton(
            self, text="🔄 Başlat", fg_color="#28a745", height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start
        )
        self.conv_btn.grid(row=8, column=0, padx=20, pady=(5, 20), sticky="ew")

    # ---------- Dosya yönetimi ----------
    def _add_files(self):
        paths = filedialog.askopenfilenames(
            parent=self,
            title="Medya dosyaları seç",
            filetypes=[
                ("Medya", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.flac *.ogg *.m4a *.wma *.aac"),
                ("Tümü", "*.*"),
            ]
        )
        if paths:
            self.files.extend(paths)
            self._refresh_list()
        self.bring_to_front()

    def _add_folder(self):
        d = filedialog.askdirectory(parent=self, title="Klasör seç")
        if d:
            exts = ('.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav',
                    '.flac', '.ogg', '.m4a', '.wma', '.aac')
            found = []
            for root_dir, _, names in os.walk(d):
                for name in names:
                    if name.lower().endswith(exts):
                        found.append(os.path.join(root_dir, name))
            self.files = found
            self.src_lbl.configure(text=f"Klasör: {d}")
            self._refresh_list()
        self.bring_to_front()

    def _clear(self):
        self.files.clear()
        self.src_lbl.configure(text="Hiçbir dosya seçilmedi")
        self._refresh_list()

    def _refresh_list(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self.file_widgets.clear()

        for i, path in enumerate(self.files):
            row = ctk.CTkFrame(self.listbox)
            row.pack(fill="x", padx=5, pady=2)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(path)}", anchor="w").grid(
                row=0, column=0, padx=5, pady=3, sticky="ew"
            )
            sl = ctk.CTkLabel(
                row, text="⏳ bekliyor", width=120,
                fg_color=("gray70", "gray20"), corner_radius=3
            )
            sl.grid(row=0, column=1, padx=5, pady=3)
            self.file_widgets.append((sl, path))

        self.stat_lbl.configure(text=f"{len(self.files)} dosya seçildi")

    def _pick_out(self):
        d = filedialog.askdirectory(parent=self, title="Çıktı klasörü seç")
        if d:
            self.out_dir = d
            self.out_lbl.configure(text=d)
        self.bring_to_front()

    # ---------- Dönüştürme ----------
    def _start(self):
        if not self.files:
            messagebox.showwarning("Uyarı", "Lütfen dosya ekleyin.", parent=self)
            return
        if not self.ffmpeg_path or not os.path.isfile(self.ffmpeg_path):
            messagebox.showerror("Hata", "FFmpeg bulunamadı.", parent=self)
            return
        self.conv_btn.configure(state="disabled", text="⏳ Dönüştürülüyor...")
        self.stat_lbl.configure(text="Dönüştürülüyor...")
        self.pbar.set(0)
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _build_ffmpeg_cmd(self, input_path: str, output_path: str, fmt: str) -> List[str]:
        """FFmpeg komut listesini oluşturur."""
        ffmpeg = self.ffmpeg_path
        cmd = [ffmpeg, "-i", input_path, "-y"]

        # Format spesifik ayarlar
        if fmt == "WAV (22050 Hz)":
            cmd += ["-acodec", "pcm_s16le", "-ac", "1", "-ar", "22050"]
        else:
            cmd += ["-vn"]
            codec_args = self.AUDIO_CODEC_MAP.get(fmt, ["-acodec", "copy"])
            cmd += codec_args

        # Bitrate
        bitrate = self.bitrate_var.get()
        if bitrate != "lossless" and bitrate not in ("192k", ""):
            # Bitrate parametresi ekle
            if "-ab" in cmd:
                idx = cmd.index("-ab")
                cmd[idx + 1] = bitrate
            else:
                cmd += ["-ab", bitrate]

        # Sessizlik filtresi
        if self.trim_silence.get():
            cmd += ["-af", "silenceremove=start_periods=1:start_threshold=0.1:start_duration=0.1"
                           ":stop_periods=-1:stop_threshold=0.1:stop_duration=0.1"]

        # Normalize
        if self.normalize_audio.get():
            cmd += ["-af", "loudnorm=I=-16:LRA=11:TP=-1.5"]

        cmd.append(output_path)
        return cmd

    def _convert_worker(self):
        fmt = self.out_fmt.get()
        ext = "wav" if fmt == "WAV (22050 Hz)" else fmt
        total = len(self.file_widgets)

        for i, (slbl, path) in enumerate(self.file_widgets):
            self.after(0, lambda s=slbl: s.configure(text="🔄 dönüşüyor", fg_color="#ffcc00"))

            base_name = os.path.splitext(os.path.basename(path))[0]
            target_dir = self.out_dir or os.path.dirname(path)
            out_path = os.path.join(target_dir, f"{base_name}.{ext}")

            # Çakışma önleme
            counter = 1
            while os.path.exists(out_path):
                out_path = os.path.join(target_dir, f"{base_name}_{counter}.{ext}")
                counter += 1

            success = False
            try:
                cmd = self._build_ffmpeg_cmd(path, out_path, fmt)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600
                )

                if result.returncode == 0:
                    success = True
                else:
                    # Sessizlik filtresi hatasıysa filtresiz dene
                    if self.trim_silence.get() and "silenceremove" in (result.stderr or ""):
                        self.trim_silence.set(False)
                        cmd_nf = self._build_ffmpeg_cmd(path, out_path, fmt)
                        self.trim_silence.set(True)
                        retry = subprocess.run(
                            cmd_nf,
                            capture_output=True,
                            encoding='utf-8',
                            errors='replace',
                            timeout=600
                        )
                        if retry.returncode == 0:
                            success = True
                            self.after(0, lambda s=slbl: s.configure(
                                text="✅ tamam (filtresiz)", fg_color="#28a745"
                            ))

                    if not success:
                        err_snip = (result.stderr or "FFmpeg hatası")[-60:]
                        self.after(0, lambda s=slbl, e=err_snip: s.configure(
                            text=f"❌ {e}", fg_color="#dc3545"
                        ))

            except subprocess.TimeoutExpired:
                self.after(0, lambda s=slbl: s.configure(text="❌ zaman aşımı", fg_color="#dc3545"))
            except Exception as exc:
                snip = str(exc)[:50]
                self.after(0, lambda s=slbl, e=snip: s.configure(text=f"❌ {e}", fg_color="#dc3545"))

            if success:
                self.after(0, lambda s=slbl: s.configure(text="✅ tamam", fg_color="#28a745"))

            self.after(0, lambda v=(i + 1) / total: self.pbar.set(v))

        self.after(0, self._convert_done)

    def _convert_done(self):
        self.conv_btn.configure(state="normal", text="🔄 Başlat")
        self.stat_lbl.configure(text="✅ Tamamlandı!")
        self.pbar.set(1.0)
        messagebox.showinfo("Bitti", f"{len(self.files)} dosya dönüştürüldü.", parent=self)
        self.bring_to_front()

# ============================================================
# 14. URL ITEM (GELİŞMİŞ)
# ============================================================
class URLItem(ctk.CTkFrame):
    """URL listesi öğesi."""

    def __init__(self, master, index: int, title: str, url: str, **kwargs):
        super().__init__(master, height=40, **kwargs)
        self.pack_propagate(False)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)

        ctk.CTkLabel(
            self, text=f"{index}.", width=30, anchor="e",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5)

        ctk.CTkLabel(self, text=title, anchor="w").grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )
        ctk.CTkLabel(self, text=url[:60], anchor="w").grid(
            row=0, column=2, padx=5, pady=5, sticky="ew"
        )

        self.status_lbl = ctk.CTkLabel(self, text="⏳", width=30, font=ctk.CTkFont(size=16))
        self.status_lbl.grid(row=0, column=3, padx=5)

        self.fav_lbl = ctk.CTkLabel(self, text="☆", width=20, font=ctk.CTkFont(size=16))
        self.fav_lbl.grid(row=0, column=4, padx=5)

        self.set_status("waiting")

    def _safe_after(self, fn):
        try:
            if self.winfo_exists():
                self.after_idle(fn)
        except Exception:
            pass

    def set_status(self, status: str):
        colors = {
            "waiting": ("gray70", "gray25"),
            "pending": ("gray70", "gray25"),
            "downloading": ("#ffcc00", "#806600"),
            "completed": ("#28a745", "#1a6e2e"),
            "error": ("#dc3545", "#a71d2a"),
            "skipped": ("#007bff", "#004d99"),
            "private": ("#6c757d", "#4a4a4a"),
            "cancelled": ("#6c757d", "#4a4a4a"),
        }
        icons = {
            "waiting": "⏳",
            "pending": "⏳",
            "downloading": "⏬",
            "completed": "✅",
            "error": "❌",
            "skipped": "⏭️",
            "private": "🔒",
            "cancelled": "⏹️",
        }
        color = colors.get(status, ("gray70", "gray25"))
        icon = icons.get(status, "⏳")

        def apply():
            try:
                if self.winfo_exists():
                    self.configure(fg_color=color)
                    self.status_lbl.configure(text=icon)
            except Exception:
                pass

        self._safe_after(apply)

    def set_fav(self, fav: bool):
        def apply():
            try:
                if self.winfo_exists():
                    self.fav_lbl.configure(
                        text="★" if fav else "☆",
                        text_color="#ffcc00" if fav else "gray"
                    )
            except Exception:
                pass
        self._safe_after(apply)

# ============================================================
# 15. NEO TUBE APP (ANA UYGULAMA - GELİŞMİŞ)
# ============================================================
class NeoTubeApp(ctk.CTk):
    """Ana uygulama sınıfı."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1550x950")
        self.minsize(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ---- Veri ----
        self.settings = Settings()
        self.completed_downloads: List[DownloadItem] = []
        self.favorites: List[Favorite] = []
        self.stats = Stats()
        self.url_titles: Dict[str, str] = {}
        self.playlist_names: Dict[str, str] = {}
        self.metadata: Dict[str, dict] = {}
        self.url_items: List[URLItem] = []
        self.active_downloads: List[DownloadItem] = []
        self.resolved_urls: List[str] = []
        self.error_logs: List[str] = []
        self._convert_files: List[str] = []

        # ---- Durum ----
        self.is_downloading = False
        self.download_thread: Optional[DownloadThread] = None
        self.resolver_thread: Optional[TitleResolverThread] = None
        self.converter_thread: Optional[ConverterWindow] = None
        self._resolve_id = None
        self._lock = threading.Lock()
        self._ffmpeg_downloading = False

        # ---- FFmpeg ----
        self.ffmpeg_path = FFmpegManager.get_ffmpeg_path()
        self.ffmpeg_installed = bool(self.ffmpeg_path and os.path.isfile(self.ffmpeg_path))

        # ---- UI Değişkenleri ----
        self.concurrent_var = ctk.StringVar(value=str(self.settings.concurrent_downloads))
        self.quality_var = ctk.StringVar(value=self.settings.default_quality)
        self.format_var = ctk.StringVar(value=self.settings.default_format)
        self.subtitle_var = ctk.BooleanVar(value=self.settings.subtitles)
        self.playlist_folder_var = ctk.BooleanVar(value=self.settings.playlist_folder)
        self.channel_folder_var = ctk.BooleanVar(value=self.settings.channel_folder)
        self.video_folder_var = ctk.BooleanVar(value=self.settings.video_folder)
        self.skip_members_var = ctk.BooleanVar(value=self.settings.skip_members_only)
        self.skip_private_var = ctk.BooleanVar(value=self.settings.skip_private_videos)
        self.embed_thumbnail_var = ctk.BooleanVar(value=self.settings.embed_thumbnail)
        self.notify_var = ctk.BooleanVar(value=self.settings.notify_on_complete)
        self.auto_resume_var = ctk.BooleanVar(value=self.settings.auto_resume)

        # ---- Yükleme ----
        self._load_settings()
        self._load_data()
        self._load_favorites()
        self._load_stats()

        self.current_theme = self.settings.theme
        self.current_lang = self.settings.language
        self.theme = ThemeManager.get(self.current_theme)

        # ---- Pencere ----
        w, h = self.settings.window_width, self.settings.window_height
        x, y = self.settings.window_x, self.settings.window_y
        if x >= 0 and y >= 0:
            self.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.geometry(f"{w}x{h}")

        os.makedirs(self.settings.download_path, exist_ok=True)

        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")

        # ---- UI ----
        self._build_ui()
        self._apply_theme()
        self._setup_shortcuts()
        self._update_ffmpeg_status()

        if self.settings.check_updates:
            self.after(3000, self._check_updates)

        if not self.ffmpeg_installed:
            self.after(2000, self._download_ffmpeg_background)

    # ============================================================
    # VERİ YÖNETİMİ
    # ============================================================
    def _load_settings(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_settings.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings = Settings.from_dict(data)
            except:
                pass

    def _save_settings(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_settings.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
        except:
            pass

    def _load_data(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_data.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.completed_downloads = [DownloadItem.from_dict(d) for d in data.get("history", [])]
            except:
                pass

    def _save_data(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_data.json")
        try:
            data = {"history": [d.to_dict() for d in self.completed_downloads[-MAX_HISTORY_SIZE:]]}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _load_favorites(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_favorites.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorites = [Favorite.from_dict(d) for d in data]
            except:
                pass

    def _save_favorites(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_favorites.json")
        try:
            data = [f.to_dict() for f in self.favorites]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def _load_stats(self):
        path = os.path.join(os.path.dirname(__file__), "neotube_stats.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.stats = Stats.from_dict(data)
            except:
                pass

    def _save_stats(self):
        self.stats.total_favorites = len(self.favorites)
        path = os.path.join(os.path.dirname(__file__), "neotube_stats.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.stats.to_dict(), f, indent=2, ensure_ascii=False)
        except:
            pass

    def _save_error_log(self, error: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {error}"
        self.error_logs.append(log_entry)
        path = os.path.join(os.path.dirname(__file__), "error.log")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except:
            pass

    # ============================================================
    # FFMPEG YÖNETİMİ
    # ============================================================
    def _update_ffmpeg_status(self):
        try:
            if self.ffmpeg_installed:
                self.ffmpeg_status_label.configure(text="✅ FFmpeg", text_color=self.theme["success"])
            else:
                self.ffmpeg_status_label.configure(text="❌ FFmpeg", text_color=self.theme["error"])
        except:
            pass

    def _download_ffmpeg_background(self):
        if self._ffmpeg_downloading:
            return
        self._ffmpeg_downloading = True

        def download():
            try:
                self.after(0, lambda: self.ffmpeg_status_label.configure(
                    text="⬇ FFmpeg indiriliyor...",
                    text_color=self.theme["warning"]
                ))
                ffmpeg_path = FFmpegManager.get_ffmpeg_path()
                if ffmpeg_path and os.path.isfile(ffmpeg_path):
                    self.ffmpeg_path = ffmpeg_path
                    self.ffmpeg_installed = True
                    self.after(0, self._update_ffmpeg_status)
                else:
                    self.after(0, lambda: self.ffmpeg_status_label.configure(
                        text="❌ FFmpeg indirilemedi",
                        text_color=self.theme["error"]
                    ))
            except Exception as e:
                self._save_error_log(f"FFmpeg download error: {e}")
            finally:
                self._ffmpeg_downloading = False

        threading.Thread(target=download, daemon=True).start()

    # ============================================================
    # UI OLUŞTURMA
    # ============================================================
    def _build_ui(self):
        self.configure(fg_color=self.theme["bg_primary"])

        # Ana container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # Sidebar
        self._build_sidebar()

        # Ana içerik
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", width=1200)
        self.content_frame.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=0)
        self.content_frame.pack_propagate(False)

        # Header
        self._build_header()

        # Sayfalar
        self.pages = {}
        self.current_page = None

        self._build_home_page()
        self._build_downloads_page()
        self._build_history_page()
        self._build_favorites_page()
        self._build_converter_page()
        self._build_settings_page()
        self._build_about_page()

        self.show_page("home")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            fg_color=self.theme["sidebar_bg"],
            width=80,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", padx=10, pady=(20, 10))
        logo_frame.pack_propagate(False)

        self.logo_label = ctk.CTkLabel(
            logo_frame,
            text="▶",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Navigasyon
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=20)

        self.nav_buttons = {}
        nav_items = [
            ("home", "🏠", "Ana Sayfa"),
            ("downloads", "⬇", "İndirmeler"),
            ("history", "📋", "Geçmiş"),
            ("favorites", "⭐", "Favoriler"),
            ("converter", "🔄", "Dönüştürücü"),
            ("settings", "⚙", "Ayarlar"),
            ("about", "ℹ", "Hakkında"),
        ]

        for page_id, icon, tooltip in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=icon,
                width=50,
                height=50,
                corner_radius=14,
                font=ctk.CTkFont(family="Segoe UI", size=22),
                fg_color="transparent",
                hover_color=self.theme["accent_light"],
                text_color=self.theme["text_secondary"],
                command=lambda p=page_id: self.show_page(p)
            )
            btn.pack(pady=5)
            # Tooltip için hover bind
            btn.bind("<Enter>", lambda e, t=tooltip: self.status_label.configure(text=t))
            btn.bind("<Leave>", lambda e: self.status_label.configure(text="Hazır"))
            self.nav_buttons[page_id] = btn

        # Alt kısım
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=20)

        # Tema butonu
        self.theme_btn = ctk.CTkButton(
            bottom_frame,
            text="🌙" if self.current_theme == "dark" else "☀",
            width=50,
            height=50,
            corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=22),
            fg_color=self.theme["accent_light"],
            hover_color=self.theme["accent"],
            text_color=self.theme["accent"],
            command=self._toggle_theme
        )
        self.theme_btn.pack()

        # FFmpeg durumu
        self.ffmpeg_status_label = ctk.CTkLabel(
            bottom_frame,
            text="⏳ FFmpeg",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"]
        )
        self.ffmpeg_status_label.pack(pady=(10, 0))

    def _build_header(self):
        self.header = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.theme["header_bg"],
            height=70,
            corner_radius=0
        )
        self.header.pack(fill="x", padx=0, pady=0)
        self.header.pack_propagate(False)

        # Başlık
        self.header_title = ctk.CTkLabel(
            self.header,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.theme["text_primary"]
        )
        self.header_title.pack(side="left", padx=30, pady=15)

        # URL girişi
        self.header_url = ModernEntry(
            self.header, self.theme,
            placeholder="YouTube URL yapıştır...",
            width=400
        )
        self.header_url.pack(side="left", padx=20, pady=13)
        self.header_url.bind("<Return>", lambda e: self._quick_analyze())

        # Yapıştır butonu
        self.paste_btn = ModernButton(
            self.header, self.theme,
            text="📋",
            command=self._paste_from_clipboard,
            width=44,
            height=38,
            font_size=16,
            variant="secondary"
        )
        self.paste_btn.pack(side="left", padx=(0, 5), pady=16)

        # Analiz butonu
        self.quick_btn = ModernButton(
            self.header, self.theme,
            text="🔍 Analiz Et",
            command=self._quick_analyze,
            width=110,
            height=38,
            font_size=12
        )
        self.quick_btn.pack(side="left", padx=(0, 20), pady=16)

        # Sağ taraftaki durum
        status_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        status_frame.pack(side="right", padx=30, pady=15)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"]
        )
        self.status_label.pack(side="left", padx=(0, 15))

        self.header_version = ctk.CTkLabel(
            status_frame,
            text=VERSION,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"]
        )
        self.header_version.pack(side="left")

    def _build_home_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["home"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # Hoş geldiniz kartı
        welcome_card = ModernCard(scroll, self.theme)
        welcome_card.pack(fill="x", pady=(0, 20))

        welcome_inner = ctk.CTkFrame(welcome_card, fg_color="transparent")
        welcome_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            welcome_inner,
            text="🎬 NeoTube'a Hoş Geldiniz",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            welcome_inner,
            text="YouTube, Vimeo ve diğer platformlardan video indirin. "
                 "Playlist, kanal, özel/üyelik videoları otomatik atlanır.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.theme["text_secondary"]
        ).pack(anchor="w", pady=(8, 0))

        # URL giriş kartı
        url_card = ModernCard(scroll, self.theme)
        url_card.pack(fill="x", pady=(0, 20))

        url_inner = ctk.CTkFrame(url_card, fg_color="transparent")
        url_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            url_inner,
            text="🔗 Video URL",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        url_row = ctk.CTkFrame(url_inner, fg_color="transparent")
        url_row.pack(fill="x", pady=(12, 0))

        self.url_entry = ModernEntry(
            url_row, self.theme,
            placeholder="https://www.youtube.com/watch?v=...",
            width=500
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<KeyRelease>", lambda e: self._on_url_change())

        self.analyze_btn = ModernButton(
            url_row, self.theme,
            text="Analiz Et",
            command=self._analyze_url,
            width=120,
            height=44,
            font_size=13
        )
        self.analyze_btn.pack(side="left", padx=(12, 0))

        self.add_fav_btn = ModernButton(
            url_row, self.theme,
            text="⭐",
            command=self._add_favorite_from_url,
            width=44,
            height=44,
            font_size=16,
            variant="secondary"
        )
        self.add_fav_btn.pack(side="left", padx=(5, 0))

        # Toplu URL
        self.url_count_label = ctk.CTkLabel(
            url_inner,
            text="URL Sayısı: 0",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"]
        )
        self.url_count_label.pack(anchor="w", pady=(8, 0))

        batch_frame = ctk.CTkFrame(url_inner, fg_color="transparent")
        batch_frame.pack(fill="x", pady=(12, 0))

        self.batch_text = ModernTextArea(
            batch_frame, self.theme,
            height=80
        )
        self.batch_text.pack(fill="x")
        self.batch_text.bind("<KeyRelease>", self._on_batch_change)

        batch_btn_row = ctk.CTkFrame(batch_frame, fg_color="transparent")
        batch_btn_row.pack(fill="x", pady=(8, 0))

        ModernButton(
            batch_btn_row, self.theme,
            text="Dosyadan Yükle",
            command=self._import_from_file,
            width=140,
            height=32,
            font_size=11,
            variant="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            batch_btn_row, self.theme,
            text="Tümünü Temizle",
            command=self._clear_batch,
            width=120,
            height=32,
            font_size=11,
            variant="secondary"
        ).pack(side="left")

        # Çözümleme durumu
        self.resolving_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        self.resolving_frame.pack(fill="x", padx=30, pady=(5, 10))
        self.resolving_frame.pack_forget()

        self.resolving_label = ctk.CTkLabel(
            self.resolving_frame,
            text="🔍 URL'ler çözümleniyor...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.resolving_label.pack(anchor="w")

        self.resolving_progress = ctk.CTkProgressBar(
            self.resolving_frame,
            width=600,
            height=6,
            corner_radius=3,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["accent"]
        )
        self.resolving_progress.pack(fill="x", pady=(8, 0))
        self.resolving_progress.set(0)

        # URL listesi
        self.url_list_frame = ctk.CTkScrollableFrame(url_card, height=150, fg_color="transparent")
        self.url_list_frame.pack(fill="x", padx=30, pady=(10, 20))

        # Başlat butonu
        self.start_download_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        self.start_download_frame.pack(fill="x", padx=30, pady=(0, 15))
        self.start_download_frame.pack_forget()

        self.start_download_btn = ModernButton(
            self.start_download_frame, self.theme,
            text="▶ İndirmeyi Başlat",
            command=self._start_download_from_resolved,
            width=220,
            height=44,
            font_size=14,
            variant="success"
        )
        self.start_download_btn.pack(anchor="w")

        # Seçenekler
        options_card = ModernCard(scroll, self.theme)
        options_card.pack(fill="x", pady=(0, 20))

        options_inner = ctk.CTkFrame(options_card, fg_color="transparent")
        options_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            options_inner,
            text="⚙ İndirme Seçenekleri",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        options_grid = ctk.CTkFrame(options_inner, fg_color="transparent")
        options_grid.pack(fill="x", pady=(15, 0))

        # Kalite
        q_frame = ctk.CTkFrame(options_grid, fg_color="transparent")
        q_frame.pack(side="left", padx=(0, 25))
        ctk.CTkLabel(
            q_frame,
            text="Kalite",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(anchor="w")
        self.quality_combo = ctk.CTkComboBox(
            q_frame,
            values=["best", "1080p", "720p", "480p", "360p", "MP3 (128k)", "MP3 (320k)", "video_only"],
            variable=self.quality_var,
            width=150,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_light"],
            button_color=self.theme["accent"],
        )
        self.quality_combo.pack(pady=(5, 0))

        # Format
        f_frame = ctk.CTkFrame(options_grid, fg_color="transparent")
        f_frame.pack(side="left", padx=(0, 25))
        ctk.CTkLabel(
            f_frame,
            text="Format",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(anchor="w")
        self.format_combo = ctk.CTkComboBox(
            f_frame,
            values=["mp4", "mkv", "webm", "mp3", "m4a", "wav", "flac"],
            variable=self.format_var,
            width=120,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_light"],
            button_color=self.theme["accent"],
        )
        self.format_combo.pack(pady=(5, 0))

        # Altyazı
        sub_frame = ctk.CTkFrame(options_grid, fg_color="transparent")
        sub_frame.pack(side="left", padx=(0, 25))
        self.subtitle_check = ctk.CTkCheckBox(
            sub_frame,
            text="Altyazı İndir",
            variable=self.subtitle_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        )
        self.subtitle_check.pack(pady=(20, 0))

        # Küçük resim
        thumb_frame = ctk.CTkFrame(options_grid, fg_color="transparent")
        thumb_frame.pack(side="left", padx=(0, 25))
        self.thumb_check = ctk.CTkCheckBox(
            thumb_frame,
            text="Küçük Resim Ekle",
            variable=self.embed_thumbnail_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        )
        self.thumb_check.pack(pady=(20, 0))

        # İlerleme
        self.progress_card = ModernCard(scroll, self.theme)
        self.progress_card.pack(fill="x", pady=(0, 20))
        self.progress_card.pack_forget()

        progress_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            progress_inner,
            text="📊 İlerleme",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_inner,
            width=700,
            height=12,
            corner_radius=6,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["progress_fg"]
        )
        self.progress_bar.pack(fill="x", pady=(15, 10))
        self.progress_bar.set(0)

        self.progress_info = ctk.CTkLabel(
            progress_inner,
            text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.progress_info.pack(anchor="w")

        self.speed_label = ctk.CTkLabel(
            progress_inner,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        )
        self.speed_label.pack(anchor="w", pady=(5, 0))

        # İstatistikler
        stat_card = ModernCard(scroll, self.theme)
        stat_card.pack(fill="x", pady=(0, 10))

        stat_inner = ctk.CTkFrame(stat_card, fg_color="transparent")
        stat_inner.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            stat_inner,
            text="📊 İstatistikler",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        stat_row = ctk.CTkFrame(stat_inner, fg_color="transparent")
        stat_row.pack(fill="x", pady=(10, 0))

        self.total_dl_label = ctk.CTkLabel(
            stat_row,
            text=f"Toplam İndirme: {self.stats.total_downloads}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.total_dl_label.pack(side="left", padx=(0, 30))

        self.total_fav_label = ctk.CTkLabel(
            stat_row,
            text=f"Toplam Favori: {len(self.favorites)}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.total_fav_label.pack(side="left", padx=(0, 30))

        self.last_dl_label = ctk.CTkLabel(
            stat_row,
            text=f"Son İndirme: {self.stats.last_download[:30] + '...' if len(self.stats.last_download) > 30 else self.stats.last_download or '—'}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.last_dl_label.pack(side="left")

    def _build_downloads_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["downloads"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            scroll,
            text="⬇ Aktif İndirmeler",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 20))

        self.downloads_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.downloads_list_frame.pack(fill="x")
        self._refresh_downloads_list()

    def _build_history_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["history"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="📋 İndirme Geçmişi",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        ModernButton(
            header_frame, self.theme,
            text="🗑 Temizle",
            command=self._clear_history,
            width=120,
            height=34,
            font_size=12,
            variant="danger"
        ).pack(side="right")

        self.history_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.history_list_frame.pack(fill="x")
        self._refresh_history()

    def _build_favorites_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["favorites"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="⭐ Favoriler",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ModernButton(
            btn_frame, self.theme,
            text="Dışa Aktar",
            command=self._export_favorites,
            width=100,
            height=34,
            font_size=12,
            variant="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            btn_frame, self.theme,
            text="İçe Aktar",
            command=self._import_favorites,
            width=100,
            height=34,
            font_size=12,
            variant="secondary"
        ).pack(side="left")

        self.favorites_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.favorites_list_frame.pack(fill="x")
        self._refresh_favorites()

    def _build_converter_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["converter"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            scroll,
            text="🔄 Dönüştürücü",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 20))

        # FFmpeg uyarısı
        self.conv_ffmpeg_warn = ctk.CTkLabel(
            scroll,
            text="⚠️ FFmpeg yüklü değil! Dönüştürme işlemi yapılamaz.",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["error"]
        )
        self.conv_ffmpeg_warn.pack(anchor="w", pady=(0, 15))
        if self.ffmpeg_installed:
            self.conv_ffmpeg_warn.pack_forget()

        conv_card = ModernCard(scroll, self.theme)
        conv_card.pack(fill="x", pady=(0, 20))

        conv_inner = ctk.CTkFrame(conv_card, fg_color="transparent")
        conv_inner.pack(fill="x", padx=30, pady=25)

        file_frame = ctk.CTkFrame(conv_inner, fg_color="transparent")
        file_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            file_frame,
            text="📁 Dosyalar:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        file_btn_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_btn_row.pack(fill="x", pady=(8, 0))

        ModernButton(
            file_btn_row, self.theme,
            text="Dosya Seç",
            command=self._select_convert_files,
            width=140,
            height=34,
            font_size=12,
            variant="secondary"
        ).pack(side="left", padx=(0, 8))

        ModernButton(
            file_btn_row, self.theme,
            text="Klasör Seç",
            command=self._select_convert_folder,
            width=140,
            height=34,
            font_size=12,
            variant="secondary"
        ).pack(side="left")

        self.convert_files_label = ctk.CTkLabel(
            file_frame,
            text="Henüz dosya seçilmedi",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"]
        )
        self.convert_files_label.pack(anchor="w", pady=(8, 0))

        format_row = ctk.CTkFrame(conv_inner, fg_color="transparent")
        format_row.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            format_row,
            text="Çıktı Formatı:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_secondary"]
        ).pack(side="left", padx=(0, 15))

        self.convert_format_var = ctk.StringVar(value="mp3")
        self.convert_format_combo = ctk.CTkComboBox(
            format_row,
            values=["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"],
            variable=self.convert_format_var,
            width=120,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_light"],
            button_color=self.theme["accent"],
        )
        self.convert_format_combo.pack(side="left")

        self.convert_btn = ModernButton(
            conv_inner, self.theme,
            text="Dönüştür",
            command=self._start_conversion,
            width=160,
            height=44,
            font_size=13,
            variant="success"
        )
        self.convert_btn.pack(anchor="w", pady=(15, 0))
        if not self.ffmpeg_installed:
            self.convert_btn.configure(state="disabled")

        self.convert_progress_frame = ctk.CTkFrame(conv_inner, fg_color="transparent")
        self.convert_progress_frame.pack(fill="x", pady=(15, 0))

        self.convert_progress_bar = ctk.CTkProgressBar(
            self.convert_progress_frame,
            width=600,
            height=10,
            corner_radius=5,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["progress_fg"]
        )
        self.convert_progress_bar.pack(fill="x")
        self.convert_progress_bar.set(0)

        self.convert_status_label = ctk.CTkLabel(
            self.convert_progress_frame,
            text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.convert_status_label.pack(anchor="w", pady=(8, 0))

    def _build_settings_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["settings"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            scroll,
            text="⚙ Ayarlar",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 20))

        # Genel Ayarlar
        gen_card = ModernCard(scroll, self.theme)
        gen_card.pack(fill="x", pady=(0, 20))

        gen_inner = ctk.CTkFrame(gen_card, fg_color="transparent")
        gen_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            gen_inner,
            text="📁 Genel Ayarlar",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        # İndirme klasörü
        path_row = ctk.CTkFrame(gen_inner, fg_color="transparent")
        path_row.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            path_row,
            text="İndirme Klasörü:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        self.path_label = ctk.CTkLabel(
            path_row,
            text=self.settings.download_path[:40] + "..." if len(self.settings.download_path) > 40 else self.settings.download_path,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"]
        )
        self.path_label.pack(side="left", padx=(15, 0), fill="x", expand=True)

        ModernButton(
            path_row, self.theme,
            text="Değiştir",
            command=self._change_download_path,
            width=90,
            height=32,
            font_size=11,
            variant="secondary"
        ).pack(side="right")

        # Eşzamanlı indirme
        conc_row = ctk.CTkFrame(gen_inner, fg_color="transparent")
        conc_row.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            conc_row,
            text="Eşzamanlı İndirme:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        self.concurrent_combo = ctk.CTkComboBox(
            conc_row,
            values=["1", "2", "3", "4", "5", "10", "15", "20"],
            variable=self.concurrent_var,
            width=80,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_light"],
            button_color=self.theme["accent"],
        )
        self.concurrent_combo.pack(side="left", padx=(15, 0))

        # Hız limiti
        speed_row = ctk.CTkFrame(gen_inner, fg_color="transparent")
        speed_row.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            speed_row,
            text="Hız Limiti:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        self.speed_combo = ctk.CTkComboBox(
            speed_row,
            values=["0 (Sınırsız)", "1 MB/s", "2 MB/s", "5 MB/s", "10 MB/s", "20 MB/s", "50 MB/s"],
            variable=ctk.StringVar(value="0 (Sınırsız)"),
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            dropdown_fg_color=self.theme["bg_card"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_light"],
            button_color=self.theme["accent"],
        )
        self.speed_combo.pack(side="left", padx=(15, 0))

        # Klasör ayarları
        folder_frame = ctk.CTkFrame(gen_inner, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            folder_frame,
            text="📁 Klasör Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkCheckBox(
            folder_frame,
            text="Playlist klasörü oluştur",
            variable=self.playlist_folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            folder_frame,
            text="Kanal klasörü oluştur",
            variable=self.channel_folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            folder_frame,
            text="Video klasörü oluştur",
            variable=self.video_folder_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        # Atlama ayarları
        skip_frame = ctk.CTkFrame(gen_inner, fg_color="transparent")
        skip_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            skip_frame,
            text="🔒 Atlama Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkCheckBox(
            skip_frame,
            text="Üyelik Gerektiren Videoları Atl",
            variable=self.skip_members_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            skip_frame,
            text="Özel Videoları Atl",
            variable=self.skip_private_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        # Diğer ayarlar
        other_frame = ctk.CTkFrame(gen_inner, fg_color="transparent")
        other_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            other_frame,
            text="⚙ Diğer Ayarlar",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkCheckBox(
            other_frame,
            text="Küçük Resim Ekle",
            variable=self.embed_thumbnail_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            other_frame,
            text="Bildirim Göster",
            variable=self.notify_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            other_frame,
            text="Devam Et (kesintiden sonra)",
            variable=self.auto_resume_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        # Kaydet butonu
        ModernButton(
            gen_inner, self.theme,
            text="💾 Ayarları Kaydet",
            command=self._save_settings_from_ui,
            width=180,
            height=42,
            font_size=13
        ).pack(anchor="w", pady=(25, 0))

    def _build_about_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["about"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        about_card = ModernCard(scroll, self.theme)
        about_card.pack(fill="x", pady=(0, 20))

        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            about_inner,
            text="ℹ Hakkında",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            about_inner,
            text=f"NeoTube Pro {VERSION}\n{AUTHOR} tarafından geliştirilmiştir.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.theme["text_secondary"]
        ).pack(anchor="w", pady=(10, 0))

        ctk.CTkLabel(
            about_inner,
            text="NeoTube, YouTube, Vimeo ve diğer platformlardan "
                 "video indirmek için geliştirilmiş profesyonel bir araçtır.\n"
                 "Tamamen açık kaynak ve ücretsizdir.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w", pady=(10, 0))

        # Sosyal medya butonları
        social_frame = ctk.CTkFrame(about_inner, fg_color="transparent")
        social_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            social_frame,
            text="Sosyal Medya:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(side="left", padx=(0, 15))

        social_links = [
            ("GitHub", GITHUB_URL),
            ("YouTube", YOUTUBE_CHANNEL),
            ("Discord", DISCORD_URL),
            ("Website", WEBSITE_URL),
        ]

        for name, url in social_links:
            ModernButton(
                social_frame, self.theme,
                text=name,
                command=lambda u=url: webbrowser.open(u),
                width=80,
                height=30,
                font_size=11,
                variant="secondary"
            ).pack(side="left", padx=(0, 5))

        # Sistem bilgileri
        sys_card = ModernCard(scroll, self.theme)
        sys_card.pack(fill="x", pady=(0, 20))

        sys_inner = ctk.CTkFrame(sys_card, fg_color="transparent")
        sys_inner.pack(fill="x", padx=30, pady=25)

        ctk.CTkLabel(
            sys_inner,
            text="🖥️ Sistem Bilgileri",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        sys_info = get_system_info()
        info_text = (
            f"İşletim Sistemi: {sys_info['os']} {sys_info['os_version']}\n"
            f"Mimari: {sys_info['architecture']}\n"
            f"Python: {sys_info['python_version']}\n"
            f"İşlemci: {sys_info['processor'] or 'Bilinmiyor'}"
        )

        ctk.CTkLabel(
            sys_inner,
            text=info_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"],
            justify="left"
        ).pack(anchor="w", pady=(10, 0))

        # Lisans
        ctk.CTkLabel(
            sys_inner,
            text="© 2026 NeoTube Pro | GNU GPLv3 Lisansı",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w", pady=(15, 0))

    # ============================================================
    # SAYFA GEZİNME
    # ============================================================
    def show_page(self, page_id: str):
        try:
            if self.current_page:
                self.pages[self.current_page].pack_forget()
                for btn_id, btn in self.nav_buttons.items():
                    btn.configure(fg_color="transparent", text_color=self.theme["text_secondary"])

            self.current_page = page_id
            self.pages[page_id].pack(fill="both", expand=True)

            if page_id in self.nav_buttons:
                self.nav_buttons[page_id].configure(
                    fg_color=self.theme["accent_light"],
                    text_color=self.theme["accent"]
                )

            if page_id == "history":
                self._refresh_history()
            elif page_id == "favorites":
                self._refresh_favorites()
            elif page_id == "downloads":
                self._refresh_downloads_list()
        except:
            pass

    # ============================================================
    # TEMA
    # ============================================================
    def _toggle_theme(self):
        if self.is_downloading:
            messagebox.showwarning("Uyarı", "Tema değiştirilemez: Aktif indirme devam ediyor!")
            return

        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme = ThemeManager.get(self.current_theme)
        self.settings.theme = self.current_theme
        ctk.set_appearance_mode(self.current_theme)
        self._apply_theme()
        self._save_settings()

    def _apply_theme(self):
        try:
            self.configure(fg_color=self.theme["bg_primary"])
            self.sidebar.configure(fg_color=self.theme["sidebar_bg"])
            self.header.configure(fg_color=self.theme["header_bg"])
            self.theme_btn.configure(
                text="🌙" if self.current_theme == "dark" else "☀",
                fg_color=self.theme["accent_light"],
                text_color=self.theme["accent"],
                hover_color=self.theme["accent"]
            )

            # Sayfaları yeniden oluştur
            for page_id, page in list(self.pages.items()):
                page.destroy()
            self.pages = {}
            self._build_home_page()
            self._build_downloads_page()
            self._build_history_page()
            self._build_favorites_page()
            self._build_converter_page()
            self._build_settings_page()
            self._build_about_page()

            if self.current_page:
                self.show_page(self.current_page)

            self._update_ffmpeg_status()
            self._resolve_urls()
        except:
            pass

    # ============================================================
    # KLAVYE KISAYOLLARI
    # ============================================================
    def _setup_shortcuts(self):
        self.bind("<Control-d>", lambda e: self._quick_analyze())
        self.bind("<Control-D>", lambda e: self._quick_analyze())
        self.bind("<Control-v>", lambda e: self._paste_from_clipboard())
        self.bind("<Control-V>", lambda e: self._paste_from_clipboard())
        self.bind("<Control-f>", lambda e: self._add_favorite_from_url())
        self.bind("<Control-F>", lambda e: self._add_favorite_from_url())
        self.bind("<Control-a>", lambda e: self.url_entry.focus_set())
        self.bind("<Escape>", lambda e: self.focus_set())

    # ============================================================
    # URL İŞLEMLERİ
    # ============================================================
    def _paste_from_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.header_url.delete(0, "end")
                self.header_url.insert(0, text)
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, text)
                self._on_url_change()
        except:
            pass

    def _on_url_change(self):
        if self._resolve_id:
            self.after_cancel(self._resolve_id)
            self._resolve_id = None
        self._resolve_id = self.after(800, self._resolve_urls)

    def _on_batch_change(self, event=None):
        if self._resolve_id:
            self.after_cancel(self._resolve_id)
            self._resolve_id = None
        self._resolve_id = self.after(800, self._resolve_urls)
        self._update_url_count()

    def _update_url_count(self):
        try:
            text = self.batch_text.get("1.0", "end-1c")
            urls = extract_urls(text)
            self.url_count_label.configure(text=f"URL Sayısı: {len(urls)}")
        except:
            pass

    def _import_from_file(self):
        path = filedialog.askopenfilename(
            title="URL Listesi Seç",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.batch_text.delete("1.0", "end")
                    self.batch_text.insert("1.0", f.read())
                    self._update_url_count()
                    self._resolve_urls()
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya okunamadı: {e}")

    def _clear_batch(self):
        self.batch_text.delete("1.0", "end")
        self._update_url_count()
        self.url_titles.clear()
        self.playlist_names.clear()
        self.metadata.clear()
        self.resolved_urls.clear()
        self._clear_url_list()
        self.resolving_frame.pack_forget()
        self.start_download_frame.pack_forget()

    def _quick_analyze(self):
        url = self.header_url.get().strip()
        if url:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self.show_page("home")
            self._resolve_urls()
        else:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin!")

    def _analyze_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin!")
            return
        self._resolve_urls()

    # ============================================================
    # URL ÇÖZÜMLEME
    # ============================================================
    def _resolve_urls(self):
        raw = []
        text = self.batch_text.get("1.0", "end-1c")
        raw.extend(extract_urls(text))

        url = self.url_entry.get().strip()
        if url and url.startswith(("http://", "https://")):
            raw.append(url)

        if not raw:
            self._clear_url_list()
            self.resolving_frame.pack_forget()
            self.start_download_frame.pack_forget()
            self.status_label.configure(text="Hazır")
            self.resolved_urls = []
            return

        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()
            self.resolver_thread.join(timeout=1)

        self.url_titles.clear()
        self.playlist_names.clear()
        self.metadata.clear()
        self.resolved_urls = []
        self.status_label.configure(text="Analiz ediliyor...")

        self.resolving_frame.pack(fill="x", padx=30, pady=(5, 10))
        self.start_download_frame.pack_forget()
        self.analyze_btn.configure(state="disabled", text="⏳")
        self.resolving_label.configure(
            text=f"🔍 URL'ler çözümleniyor... (0/{len(raw)})",
            text_color=self.theme["accent"]
        )
        self.resolving_progress.set(0)

        try:
            self.resolver_thread = TitleResolverThread(
                raw,
                callback=self._on_resolved,
                progress_callback=self._on_resolve_progress,
                skip_private=self.skip_private_var.get(),
                skip_members=self.skip_members_var.get()
            )
            self.resolver_thread.start()
        except Exception as e:
            self.analyze_btn.configure(state="normal", text="Analiz Et")
            self.resolving_frame.pack_forget()
            self.status_label.configure(text="❌ " + str(e)[:50])
            self._save_error_log(f"Resolver thread error: {e}")

    def _on_resolve_progress(self, cur: int, tot: int, msg: str):
        def update():
            try:
                progress = cur / tot
                self.resolving_progress.set(progress)
                self.resolving_label.configure(
                    text=f"🔍 {msg} ({cur}/{tot})",
                    text_color=self.theme["accent"]
                )
                self.status_label.configure(text=f"⏳ {msg} ({cur}/{tot})")
            except:
                pass
        self.after(0, update)

    def _on_resolved(self, results: dict, playlist_names: dict, metadata: dict):
        def update():
            print(f"[DEBUG2] playlist_names geldi: {playlist_names}")   # debug
            self.url_titles = results
            self.playlist_names = playlist_names
            self.metadata = metadata
            self._clear_url_list()
            self.resolved_urls = list(results.keys())

            ok_count = 0
            private_count = 0
            error_count = 0
            members_count = 0

            for idx, (url, title) in enumerate(results.items(), 1):
                item_frame = ctk.CTkFrame(
                    self.url_list_frame,
                    fg_color=self.theme["bg_input"],
                    corner_radius=8
                )
                item_frame.pack(fill="x", padx=2, pady=2)
                item_frame.grid_columnconfigure(0, weight=1)

                status_icon = "🔄"
                if title.startswith("🔒"):
                    status_icon = "🔒"
                    if "Üyelik" in title or "Members" in title:
                        members_count += 1
                    else:
                        private_count += 1
                elif title.startswith("❌") or title.startswith("⚠️"):
                    status_icon = "❌"
                    error_count += 1
                else:
                    ok_count += 1

                ctk.CTkLabel(
                    item_frame,
                    text=f"{status_icon} {title[:60]}{'...' if len(title) > 60 else ''}",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=self.theme["text_primary"],
                    anchor="w"
                ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

                is_fav = any(f.url == url for f in self.favorites)
                fav_btn = ctk.CTkButton(
                    item_frame,
                    text="★" if is_fav else "☆",
                    width=30,
                    height=25,
                    font=ctk.CTkFont(size=14),
                    fg_color="transparent",
                    hover_color=self.theme["accent_light"],
                    text_color="#ffcc00" if is_fav else self.theme["text_muted"],
                    command=lambda u=url: self._toggle_favorite(u)
                )
                fav_btn.grid(row=0, column=1, padx=5, pady=5)

                self.url_items.append((url, title, item_frame))

            parts = [f"Toplam: {len(results)}", f"Hazır: {ok_count}"]
            if members_count:
                parts.append(f"Üyelik: {members_count}")
            if private_count:
                parts.append(f"Özel: {private_count}")
            if error_count:
                parts.append(f"Hatalı: {error_count}")
            self.url_count_label.configure(text=" | ".join(parts))

            self.analyze_btn.configure(state="normal", text="Analiz Et")

            if ok_count > 0:
                self.resolving_label.configure(
                    text=f"✅ {ok_count} URL hazır, indirmeye hazır!",
                    text_color=self.theme["success"]
                )
                self.resolving_progress.set(1.0)

                self.start_download_frame.pack(fill="x", padx=30, pady=(5, 15))
                self.start_download_btn.configure(
                    text=f"▶ {ok_count} URL'yi İndir",
                    state="normal"
                )
                self.status_label.configure(text=f"✅ {ok_count} URL hazır.")
            else:
                self.resolving_label.configure(
                    text="⚠ Hiç geçerli URL bulunamadı!",
                    text_color=self.theme["error"]
                )
                self.start_download_frame.pack_forget()
                self.status_label.configure(text="⚠ Hiç geçerli URL yok!")

            self.after(3000, lambda: self.resolving_frame.pack_forget())

        self.after(0, update)

    def _clear_url_list(self):
        for _, _, frame in self.url_items:
            try:
                if frame.winfo_exists():
                    frame.destroy()
            except:
                pass
        self.url_items.clear()

    def _toggle_favorite(self, url: str):
        if any(f.url == url for f in self.favorites):
            self.favorites = [f for f in self.favorites if f.url != url]
        else:
            fav = Favorite(
                url=url,
                title=self.url_titles.get(url, url)[:60],
                date_added=datetime.now().strftime("%d.%m.%Y %H:%M")
            )
            self.favorites.append(fav)
        self._save_favorites()
        self._refresh_favorites()
        self.total_fav_label.configure(
            text=f"Toplam Favori: {len(self.favorites)}"
        )
        self._resolve_urls()

    def _add_favorite_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin!")
            return
        if any(f.url == url for f in self.favorites):
            messagebox.showinfo("Bilgi", "Bu URL zaten favorilerde!")
            return

        title = url
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', url)
        except:
            pass

        fav = Favorite(
            url=url,
            title=title[:60],
            date_added=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
        self.favorites.append(fav)
        self._save_favorites()
        self._refresh_favorites()
        self.total_fav_label.configure(
            text=f"Toplam Favori: {len(self.favorites)}"
        )
        self._resolve_urls()
        messagebox.showinfo("Başarılı", "Favorilere eklendi!")

    # ============================================================
    # FAVORİLER
    # ============================================================
    def _refresh_favorites(self):
        try:
            for widget in self.favorites_list_frame.winfo_children():
                widget.destroy()

            if not self.favorites:
                ctk.CTkLabel(
                    self.favorites_list_frame,
                    text="⭐ Henüz favori eklenmemiş",
                    font=ctk.CTkFont(family="Segoe UI", size=16),
                    text_color=self.theme["text_muted"]
                ).pack(pady=100)
                return

            for fav in self.favorites:
                card = ModernCard(self.favorites_list_frame, self.theme)
                card.pack(fill="x", pady=(0, 10))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=20, pady=15)

                ctk.CTkLabel(
                    inner,
                    text=fav.title[:50] + ("..." if len(fav.title) > 50 else ""),
                    font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                    text_color=self.theme["text_primary"]
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(5, 0))

                ctk.CTkLabel(
                    meta,
                    text=f"📅 {fav.date_added}",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.theme["text_muted"]
                ).pack(side="left")

                btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
                btn_frame.pack(side="right")

                ModernButton(
                    btn_frame, self.theme,
                    text="▶ Kullan",
                    command=lambda u=fav.url: self._use_favorite(u),
                    width=60,
                    height=28,
                    font_size=10,
                    variant="secondary"
                ).pack(side="left", padx=(0, 5))

                ModernButton(
                    btn_frame, self.theme,
                    text="✕",
                    command=lambda f=fav: self._remove_favorite(f),
                    width=30,
                    height=28,
                    font_size=10,
                    variant="danger"
                ).pack(side="left")
        except:
            pass

    def _use_favorite(self, url: str):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self.header_url.delete(0, "end")
        self.header_url.insert(0, url)
        self.show_page("home")
        self._resolve_urls()

    def _remove_favorite(self, fav: Favorite):
        if fav in self.favorites:
            self.favorites.remove(fav)
            self._save_favorites()
            self._refresh_favorites()
            self.total_fav_label.configure(
                text=f"Toplam Favori: {len(self.favorites)}"
            )
            self._resolve_urls()

    def _export_favorites(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([fav.to_dict() for fav in self.favorites], f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Başarılı", "Favoriler dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma başarısız: {e}")

    def _import_favorites(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for d in data:
                    fav = Favorite.from_dict(d)
                    if not any(f.url == fav.url for f in self.favorites):
                        self.favorites.append(fav)
                self._save_favorites()
                self._refresh_favorites()
                self.total_fav_label.configure(
                    text=f"Toplam Favori: {len(self.favorites)}"
                )
                self._resolve_urls()
                messagebox.showinfo("Başarılı", "Favoriler içe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"İçe aktarma başarısız: {e}")

    # ============================================================
    # İNDİRME
    # ============================================================
    def _start_download_from_resolved(self):
        if not self.resolved_urls:
            messagebox.showwarning("Uyarı", "İndirilecek URL yok!")
            return

        if self.is_downloading:
            messagebox.showinfo("Bilgi", "Zaten bir indirme devam ediyor!")
            return

        first_url = self.resolved_urls[0]
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, first_url)

        if len(self.resolved_urls) > 1:
            self.batch_text.delete("1.0", "end")
            self.batch_text.insert("1.0", "\n".join(self.resolved_urls))

        self._start_download()

    def _start_download(self):
        try:
            # FFmpeg kontrolü
            if not self.ffmpeg_installed:
                self.ffmpeg_path = FFmpegManager.get_ffmpeg_path()
                if self.ffmpeg_path and os.path.isfile(self.ffmpeg_path):
                    self.ffmpeg_installed = True
                    self._update_ffmpeg_status()

            # URL'leri al - önce resolved_urls varsa onu kullan
            if self.resolved_urls:
                urls = self.resolved_urls
                print(f"[DEBUG] resolved_urls kullanılıyor: {len(urls)} URL")
            else:
                urls = self._get_download_urls()
                print(f"[DEBUG] _get_download_urls kullanıldı: {len(urls)} URL")

            if not urls:
                messagebox.showwarning("Uyarı", "Lütfen bir URL girin!")
                return

            if self.is_downloading:
                return

            quality = self.quality_var.get()
            fmt = self.format_var.get().lower()
            subs = self.subtitle_var.get()
            embed_thumb = self.embed_thumbnail_var.get()
            skip_private = self.skip_private_var.get()
            skip_members = self.skip_members_var.get()
            playlist_folder = self.playlist_folder_var.get()
            print(f"[DEBUG] playlist_folder ayarı: {playlist_folder}")
            channel_folder = self.channel_folder_var.get()
            video_folder = self.video_folder_var.get()
            concurrent = int(self.concurrent_var.get()) if self.concurrent_var.get().isdigit() else 3
            speed_limit = parse_speed_limit(self.speed_combo.get() if hasattr(self, 'speed_combo') else "0 (Sınırsız)")

            os.makedirs(self.settings.download_path, exist_ok=True)

            # Hemen UI güncelle
            self.progress_card.pack(fill="x", pady=(0, 20))
            self.progress_bar.set(0)
            self.progress_info.configure(text="⏳ İndirme hazırlanıyor...")
            self.speed_label.configure(text="")
            self.status_label.configure(text="İndiriliyor...")
            self.start_download_frame.pack_forget()
            self.analyze_btn.configure(state="disabled", text="⏳")
            self.is_downloading = True
            self.update_idletasks()

            # Download item'ları oluştur
            items = []
            for url in urls:
                is_pl = "playlist" in url.lower() or "list=" in url.lower()
                item = DownloadItem(
                    url=url,
                    quality=quality,
                    format=fmt,
                    date_added=datetime.now().strftime("%d.%m.%Y %H:%M"),
                    is_playlist=is_pl,
                    playlist_title=self.playlist_names.get(url, "")
                )
                items.append(item)

            self.active_downloads = items.copy()

            # Thread'i oluştur ve başlat
            self.download_thread = DownloadThread(
                urls=urls,
                titles=self.url_titles,
                playlist_names=self.playlist_names,
                metadata=self.metadata,
                save_path=self.settings.download_path,
                fmt=quality if quality in FORMAT_MAP else "best",
                concurrent=concurrent,
                speed_limit=speed_limit,
                ffmpeg=self.ffmpeg_path,
                subtitles=subs,
                subtitle_lang="tr",
                embed_thumbnail=embed_thumb,
                skip_private=skip_private,
                skip_members=skip_members,
                file_template=self.settings.file_name_template,
                post_action=self.settings.post_action,
                notify=self.notify_var.get(),
                playlist_folder=playlist_folder,
                channel_folder=channel_folder,
                video_folder=video_folder
            )

            self.download_thread.cb_bar = self._on_download_progress
            self.download_thread.cb_speed = self._on_download_speed
            self.download_thread.cb_error = self._on_download_error
            self.download_thread.cb_done = self._on_download_done
            self.download_thread.cb_skip = self._on_download_skip
            self.download_thread.cb_progress = self._on_download_status
            self.download_thread.cb_item_complete = self._on_item_complete

            self.download_thread.start()

        except Exception as e:
            self._save_error_log(f"İndirme başlatma hatası: {e}")
            self.is_downloading = False
            self.analyze_btn.configure(state="normal", text="Analiz Et")
            self.status_label.configure(text="❌ Hata")
            messagebox.showerror("Hata", f"İndirme başlatılamadı:\n{e}")

    def _get_download_urls(self) -> List[str]:
        url = self.url_entry.get().strip()
        if url:
            return [url]
        text = self.batch_text.get("1.0", "end-1c")
        return extract_urls(text)

    def _on_download_progress(self, progress: int):
        self.after(0, lambda: self.progress_bar.set(progress / 100))

    def _on_download_speed(self, speed: str, eta: str):
        self.after(0, lambda: self.speed_label.configure(text=f"⚡ {speed} | ⏱️ {eta}"))

    def _on_download_error(self, error: str):
        self.after(0, lambda: self.progress_info.configure(text=f"❌ {error[:50]}"))
        self._save_error_log(f"Download error: {error}")

    def _on_download_skip(self, url: str, status: str, title: str):
        self.after(0, lambda: self.progress_info.configure(text=f"⏭️ Atlanan: {title[:40]}"))
        self.stats.total_skipped += 1
        self._save_stats()

    def _on_download_status(self, status: str):
        self.after(0, lambda: self.progress_info.configure(text=status[:80]))

    def _on_item_complete(self, item: DownloadItem):
        self.stats.total_downloads += 1
        self.stats.last_download = item.title
        self.stats.last_download_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        if item.size:
            size_bytes = item.size.replace(" B", "").replace(" KB", "").replace(" MB", "").replace(" GB", "")
            try:
                self.stats.total_size_bytes += int(float(size_bytes) * 1024) if "KB" in item.size else int(float(size_bytes) * 1024 * 1024) if "MB" in item.size else int(float(size_bytes) * 1024 * 1024 * 1024) if "GB" in item.size else int(size_bytes)
                self.stats.total_size_str = format_size(self.stats.total_size_bytes)
            except:
                pass

        self.completed_downloads.append(item)
        self._save_data()
        self._save_stats()

        self.after(0, lambda: self.total_dl_label.configure(
            text=f"Toplam İndirme: {self.stats.total_downloads}"
        ))
        self.after(0, lambda: self.last_dl_label.configure(
            text=f"Son İndirme: {item.title[:30] + '...' if len(item.title) > 30 else item.title}"
        ))

        if self.notify_var.get():
            try:
                notification.notify(
                    title=APP_NAME,
                    message=f"✅ {item.title[:40]} indirildi!",
                    timeout=5
                )
            except:
                pass

    def _on_download_done(self):
        def update():
            self.is_downloading = False
            self.progress_bar.set(1.0)
            self.status_label.configure(text="✅ Tamamlandı")
            self.analyze_btn.configure(state="normal", text="Analiz Et")

            if self.resolved_urls:
                self.start_download_frame.pack(fill="x", padx=30, pady=(5, 15))
                self.start_download_btn.configure(
                    text=f"▶ {len(self.resolved_urls)} URL'yi İndir",
                    state="normal"
                )

            self.active_downloads.clear()

            if self.download_thread:
                total = self.download_thread.total
                completed = self.download_thread.completed_count
                errors = self.download_thread.error_count
                skipped = self.download_thread.skipped_count

                if skipped > 0 and completed == total - skipped:
                    self.progress_info.configure(text=f"✅ {completed} video indirildi, {skipped} atlandı")
                elif completed == total:
                    self.progress_info.configure(text=f"✅ {total} video başarıyla indirildi!")
                elif completed > 0:
                    self.progress_info.configure(text=f"⚠ {completed}/{total} video indirildi, {errors} hata!")
                else:
                    self.progress_info.configure(text="❌ Tüm indirmeler başarısız!")

            self._handle_post_action()
            self._refresh_history()
            self._refresh_downloads_list()
            self.after(3000, lambda: self.progress_bar.set(0))

        self.after(0, update)

    def _handle_post_action(self):
        try:
            action = self.settings.post_action
            if action == "open_folder":
                self._open_path(self.settings.download_path)
            elif action == "shutdown" and sys.platform == "win32":
                if messagebox.askyesno("Kapat", "İndirme tamamlandı. Bilgisayarı kapatmak ister misiniz?"):
                    os.system("shutdown /s /t 10")
            elif action == "sleep" and sys.platform == "win32":
                if messagebox.askyesno("Uyku", "İndirme tamamlandı. Bilgisayarı uyku moduna almak ister misiniz?"):
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif action == "exit_app":
                self.after(2000, self.destroy)
        except:
            pass

    def _open_path(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except:
            pass

    # ============================================================
    # GEÇMİŞ
    # ============================================================
    def _refresh_history(self):
        try:
            for widget in self.history_list_frame.winfo_children():
                widget.destroy()

            if not self.completed_downloads:
                ctk.CTkLabel(
                    self.history_list_frame,
                    text="📭 Henüz indirme geçmişi yok",
                    font=ctk.CTkFont(family="Segoe UI", size=16),
                    text_color=self.theme["text_muted"]
                ).pack(pady=100)
                return

            for item in reversed(self.completed_downloads[-50:]):
                card = ModernCard(self.history_list_frame, self.theme)
                card.pack(fill="x", pady=(0, 10))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=20, pady=15)

                if item.is_members_only:
                    icon, status_text = "🔒", "Üyelik"
                elif item.is_private:
                    icon, status_text = "🔒", "Özel"
                elif item.status == "completed":
                    icon, status_text = "✅", "Tamamlandı"
                else:
                    icon, status_text = "❌", "Hata"

                ctk.CTkLabel(
                    inner,
                    text=f"{icon} {item.title[:60]}{'...' if len(item.title) > 60 else ''}",
                    font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                    text_color=self.theme["text_primary"]
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(8, 0))

                info_text = f"📅 {item.date_added} | 📂 {item.format} | {item.size if item.size else '—'}"
                if item.duration:
                    info_text += f" | ⏱️ {item.duration}"
                if item.channel:
                    info_text += f" | 📺 {item.channel[:20]}"

                ctk.CTkLabel(
                    meta,
                    text=info_text,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.theme["text_muted"]
                ).pack(side="left")

                status_color = self.theme["warning"] if item.is_members_only else self.theme["error"] if item.is_private else self.theme["success"] if item.status == "completed" else self.theme["error"]
                ctk.CTkLabel(
                    meta,
                    text=status_text,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color=status_color
                ).pack(side="right")

                if item.status == "completed" and item.file_path and os.path.exists(item.file_path):
                    ModernButton(
                        inner, self.theme,
                        text="📂 Aç",
                        command=lambda p=item.file_path: self._open_path(os.path.dirname(p)),
                        width=60,
                        height=28,
                        font_size=10,
                        variant="secondary"
                    ).pack(side="right", padx=(0, 0))
        except:
            pass

    def _clear_history(self):
        if messagebox.askyesno("Onay", "Tüm geçmişi silmek istediğinize emin misiniz?"):
            self.completed_downloads.clear()
            self._save_data()
            self._refresh_history()

    # ============================================================
    # İNDİRME LİSTESİ
    # ============================================================
    def _refresh_downloads_list(self):
        try:
            for widget in self.downloads_list_frame.winfo_children():
                widget.destroy()

            active = [item for item in self.active_downloads if item.status in ["pending", "downloading"]]
            if not active:
                ctk.CTkLabel(
                    self.downloads_list_frame,
                    text="🎉 Aktif indirme bulunmuyor",
                    font=ctk.CTkFont(family="Segoe UI", size=16),
                    text_color=self.theme["text_muted"]
                ).pack(pady=100)
                return

            for item in active:
                card = ModernCard(self.downloads_list_frame, self.theme)
                card.pack(fill="x", pady=(0, 10))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=20, pady=15)

                status_map = {
                    "pending": ("⏳", "Bekliyor"),
                    "downloading": ("⬇", "İndiriliyor"),
                }
                icon, label = status_map.get(item.status, ("⏳", "Bekliyor"))

                title_text = item.title[:40] or item.url[:40]
                if item.is_playlist and item.playlist_index > 0:
                    title_text = f"[{item.playlist_index}/{item.playlist_count}] {title_text}"

                ctk.CTkLabel(
                    inner,
                    text=f"{icon} {title_text}",
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                    text_color=self.theme["text_primary"]
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(5, 0))

                if item.status == "downloading":
                    pbar = ctk.CTkProgressBar(
                        meta,
                        width=200,
                        height=8,
                        corner_radius=4,
                        fg_color=self.theme["progress_bg"],
                        progress_color=self.theme["progress_fg"]
                    )
                    pbar.pack(side="left", padx=(0, 10))
                    pbar.set(item.progress)

                    speed_text = f"{item.speed} | ETA: {item.eta}" if item.speed else ""
                    ctk.CTkLabel(
                        meta,
                        text=speed_text,
                        font=ctk.CTkFont(family="Segoe UI", size=10),
                        text_color=self.theme["text_muted"]
                    ).pack(side="left")
        except:
            pass

    # ============================================================
    # AYARLAR
    # ============================================================
    def _change_download_path(self):
        path = filedialog.askdirectory(initialdir=self.settings.download_path)
        if path:
            self.settings.download_path = path
            self.path_label.configure(text=path[:40] + "..." if len(path) > 40 else path)
            os.makedirs(path, exist_ok=True)
            self._save_settings()

    def _save_settings_from_ui(self):
        try:
            self.settings.concurrent_downloads = int(self.concurrent_var.get()) if self.concurrent_var.get().isdigit() else 3
            self.settings.playlist_folder = self.playlist_folder_var.get()
            self.settings.channel_folder = self.channel_folder_var.get()
            self.settings.video_folder = self.video_folder_var.get()
            self.settings.skip_members_only = self.skip_members_var.get()
            self.settings.skip_private_videos = self.skip_private_var.get()
            self.settings.embed_thumbnail = self.embed_thumbnail_var.get()
            self.settings.notify_on_complete = self.notify_var.get()
            self.settings.auto_resume = self.auto_resume_var.get()
            self._save_settings()
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi:\n{e}")

    # ============================================================
    # DÖNÜŞTÜRÜCÜ
    # ============================================================
    def _select_convert_files(self):
        files = filedialog.askopenfilenames(
            title="Dönüştürülecek Dosyaları Seç",
            filetypes=[
                ("Media files", "*.mp4 *.mkv *.webm *.avi *.mov *.flv *.wmv"),
                ("Audio files", "*.mp3 *.wav *.flac *.aac *.ogg *.m4a"),
                ("All files", "*.*")
            ]
        )
        if files:
            self._convert_files = list(files)
            self.convert_files_label.configure(text=f"{len(files)} dosya seçildi")
            self.convert_progress_bar.set(0)
            self.convert_status_label.configure(text="Hazır")
            if self.ffmpeg_installed:
                self.convert_btn.configure(state="normal")

    def _select_convert_folder(self):
        folder = filedialog.askdirectory(title="Dönüştürülecek Klasörü Seç")
        if folder:
            media_exts = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv',
                          '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.m4v'}
            files = []
            for root, _, filenames in os.walk(folder):
                for f in filenames:
                    if any(f.lower().endswith(ext) for ext in media_exts):
                        files.append(os.path.join(root, f))
            if files:
                self._convert_files = files
                self.convert_files_label.configure(text=f"{len(files)} dosya bulundu")
                self.convert_progress_bar.set(0)
                self.convert_status_label.configure(text="Hazır")
                if self.ffmpeg_installed:
                    self.convert_btn.configure(state="normal")
            else:
                messagebox.showinfo("Bilgi", "Klasörde medya dosyası bulunamadı.")

    def _start_conversion(self):
        if not self._convert_files:
            messagebox.showwarning("Uyarı", "Lütfen dönüştürülecek dosyaları seçin!")
            return
        if not self.ffmpeg_installed:
            messagebox.showwarning("Uyarı", "FFmpeg yüklü değil!")
            return
        if hasattr(self, 'converter_thread') and self.converter_thread and self.converter_thread.is_alive():
            messagebox.showinfo("Bilgi", "Dönüştürme zaten devam ediyor!")
            return

        output_format = self.convert_format_var.get()
        self.convert_btn.configure(state="disabled", text="⏳ Dönüştürülüyor...")
        self.convert_progress_bar.set(0)
        self.convert_status_label.configure(text="Dönüştürme başlatılıyor...")

        # ConverterWindow'u kullan
        if hasattr(self, '_conv_win') and self._conv_win.winfo_exists():
            self._conv_win.lift()
            self._conv_win.focus_force()
        else:
            self._conv_win = ConverterWindow(self)
            self._conv_win.files = self._convert_files.copy()
            self._conv_win.out_fmt.set(output_format)
            self._conv_win._refresh_list()
            self._conv_win._start()

    # ============================================================
    # GÜNCELLEME KONTROLÜ
    # ============================================================
    def _check_updates(self):
        def check():
            try:
                url = "https://api.github.com/repos/canerergun/neotube/releases/latest"
                req = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "")
                    if latest_version and version_compare(latest_version, VERSION) > 0:
                        self.after(0, lambda: self._show_update_notification(latest_version))
            except:
                pass
        threading.Thread(target=check, daemon=True).start()

    def _show_update_notification(self, version: str):
        if self.notify_var.get():
            try:
                notification.notify(
                    title=f"{APP_NAME} - Yeni Sürüm",
                    message=f"{version} sürümü mevcut!\nGitHub'dan indirin.",
                    timeout=10
                )
            except:
                pass

    # ============================================================
    # PENCERE KAPATMA
    # ============================================================
    def _on_close(self):
        if self.settings.confirm_before_exit and self.is_downloading:
            if not messagebox.askyesno("Çıkış", "İndirme devam ediyor. Çıkmak istediğinize emin misiniz?"):
                return
            if self.download_thread:
                self.download_thread.stop()

        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()

        try:
            self.settings.window_width = self.winfo_width()
            self.settings.window_height = self.winfo_height()
            self.settings.window_x = self.winfo_x()
            self.settings.window_y = self.winfo_y()
            self._save_settings()
            self._save_data()
            self._save_stats()
        except:
            pass
        self.destroy()

# ============================================================
# 16. GİRİŞ NOKTASI
# ============================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try:
        app = NeoTubeApp()
        app.mainloop()
    except Exception as e:
        print(f"Uygulama başlatılamadı: {e}")
        import traceback
        traceback.print_exc()
        input("Devam etmek için Enter'a basın...")
