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
║   🚀 NeoTube Pro v9.0 – Ultimate Video Downloader & Converter                ║
║   🎨 Modern Arayüz | 📋 Kuyruk | ⏸️ Duraklat | 🎵 Format Seçimi              ║
║                                                                               ║
║   📌 Geliştirici: Caner Ergün                                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import importlib
import os
import re
import threading
import time
import urllib.request
import zipfile
import shutil
import socket
import json
import random
import tempfile
import platform
import glob
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from tkinter import filedialog, messagebox
from tkinter import Tk, Label, ttk

# ============================================================
# 1. BAĞIMLILIK KONTROLÜ
# ============================================================
def install_package(package: str) -> bool:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


def check_dependencies():
    required = ['customtkinter', 'yt_dlp', 'plyer']
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    root = Tk()
    root.title("NeoTube Kurulumu")
    root.geometry("450x180")
    root.configure(bg='#2b2b2b')
    root.attributes('-topmost', True)

    Label(
        root,
        text=f"Eksik paketler: {', '.join(missing)}\nKurulum yapılıyor...\nLütfen bekleyin.",
        fg='white', bg='#2b2b2b', font=('Arial', 11), justify='center'
    ).pack(pady=25)

    progress = ttk.Progressbar(root, length=350, mode='indeterminate')
    progress.pack(pady=15)
    progress.start()
    root.update()

    try:
        for pkg in missing:
            install_package(pkg)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        progress.stop()
        progress.destroy()
        Label(
            root, text="✅ Kurulum tamamlandı!",
            fg='#34D399', bg='#2b2b2b', font=('Arial', 11)
        ).pack(pady=15)
        root.update()
        time.sleep(1.5)
        root.destroy()
    except Exception as e:
        root.destroy()
        messagebox.showerror(
            "Kurulum Hatası",
            f"Paket kurulumu başarısız:\n{e}\n\n"
            "Elle yükleyin: pip install customtkinter yt-dlp plyer"
        )
        sys.exit(1)


check_dependencies()

# ============================================================
# 2. İTHALATLAR
# ============================================================
import customtkinter as ctk
import yt_dlp
from plyer import notification
from yt_dlp.utils import DownloadCancelled

# ============================================================
# 3. SABİTLER
# ============================================================
VERSION = "v9.0.0"
APP_NAME = "NeoTube Pro"
AUTHOR = "Caner Ergün"
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "NeoTube")
MAX_HISTORY_SIZE = 500

# ============================================================
# 4. DATACLASSES
# ============================================================
@dataclass
class DownloadItem:
    url: str
    title: str = ""
    status: str = "pending"
    format: str = "mp4"
    size: str = ""
    duration: str = ""
    channel: str = ""
    date_added: str = ""
    file_path: str = ""
    folder_path: str = ""
    playlist_title: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadItem":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})


@dataclass
class QueueItem:
    url: str
    title: str = ""
    quality: str = "best"
    format: str = "mp4"
    added_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})


@dataclass
class Settings:
    theme: str = "dark"
    download_path: str = DEFAULT_DOWNLOAD_PATH
    default_quality: str = "best"
    default_format: str = "mp4"
    concurrent_downloads: int = 3
    skip_members_only: bool = True
    skip_private_videos: bool = True
    embed_thumbnail: bool = True
    notify_on_complete: bool = True
    auto_cleanup: bool = True
    playlist_folder: bool = True
    channel_folder: bool = False
    video_folder: bool = False
    proxy: str = ""
    speed_limit: int = 0
    normalize_audio: bool = False
    sound_on_complete: bool = False
    file_template: str = "%(title)s"
    window_width: int = 1400
    window_height: int = 880
    window_x: int = -1
    window_y: int = -1

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
    date_added: str = ""

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
    total_errors: int = 0
    total_skipped: int = 0
    last_download: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Stats":
        fields = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        fields.update(data)
        return cls(**{k: v for k, v in fields.items() if k in cls.__dataclass_fields__})


# ============================================================
# 5. YARDIMCI FONKSİYONLAR
# ============================================================
def format_duration(seconds) -> str:
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


def format_size(bytes_val: int) -> str:
    if not bytes_val:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    val = float(bytes_val)
    while val >= 1024 and i < len(units) - 1:
        val /= 1024
        i += 1
    return f"{val:.1f} {units[i]}"


def sanitize_filename(filename: str) -> str:
    if not filename:
        return "Unknown"
    for char in '<>:"/\\|?*':
        filename = filename.replace(char, '')
    filename = ''.join(c for c in filename if ord(c) >= 32).strip()
    return filename[:200] if filename else "Unknown"


def clean_title(title: str) -> str:
    if not title:
        return "Unknown"
    for prefix in ("📁 ", "🎬 ", "⚠️ ", "❌ ", "🔒 ", "✅ "):
        title = title.replace(prefix, "")
    return sanitize_filename(title)


def extract_urls(text: str) -> List[str]:
    return re.findall(r'https?://[^\s]+', text)


def get_random_user_agent() -> str:
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]
    return random.choice(agents)


# ============================================================
# 6. TEMİZLEYİCİ
# ============================================================
class TempCleaner:
    TEMP_PATTERNS = [
        "*.part", "*.ytdl", "*.temp",
        "*.part-Frag*",
        "*.f*.mp4", "*.f*.webm", "*.f*.m4a", "*.f*.opus", "*.f*.aac",
    ]

    @staticmethod
    def clean_folder(folder: str, recursive: bool = True) -> int:
        if not os.path.exists(folder):
            return 0
        removed = 0
        try:
            if recursive:
                for root, _, _ in os.walk(folder):
                    removed += TempCleaner._clean_dir(root)
            else:
                removed = TempCleaner._clean_dir(folder)
        except Exception:
            pass
        return removed

    @staticmethod
    def _clean_dir(folder: str) -> int:
        removed = 0
        for pattern in TempCleaner.TEMP_PATTERNS:
            for filepath in glob.glob(os.path.join(folder, pattern)):
                try:
                    os.remove(filepath)
                    removed += 1
                except Exception:
                    pass
        return removed


# ============================================================
# 7. FFMPEG YÖNETİCİSİ
# ============================================================
class FFmpegManager:
    @staticmethod
    def find_system_ffmpeg() -> Optional[str]:
        # 1. PATH'te ara
        path = shutil.which('ffmpeg')
        if path:
            return path

        # 2. Yaygın klasörler
        common = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
        ]
        for p in common:
            if os.path.isfile(p):
                return p
        return None

    @staticmethod
    def get_ffmpeg_path() -> Optional[str]:
        # 1. Uygulama klasörü
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_exe = os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_exe):
            return local_exe

        # 2. Sistem PATH
        system_path = FFmpegManager.find_system_ffmpeg()
        if system_path:
            return system_path

        # 3. İndirmeyi dene
        if platform.system() != "Windows":
            return None

        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
        except OSError:
            return None

        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(base_dir, "ffmpeg_temp.zip")

        try:
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                extracted = None
                for member in zf.namelist():
                    if member.endswith("ffmpeg.exe"):
                        zf.extract(member, base_dir)
                        extracted = os.path.join(base_dir, member)
                        break

            if extracted and os.path.isfile(extracted):
                os.makedirs(os.path.dirname(local_exe), exist_ok=True)
                shutil.move(extracted, local_exe)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                return local_exe
        except Exception as e:
            print(f"FFmpeg indirme hatası: {e}")
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
        return None


# ============================================================
# 8. TITLE RESOLVER
# ============================================================
class TitleResolver(threading.Thread):
    def __init__(self, urls, callback, progress_cb=None,
                 skip_private=True, skip_members=True):
        super().__init__(daemon=True)
        self.urls = urls
        self.callback = callback
        self.progress_cb = progress_cb
        self.skip_private = skip_private
        self.skip_members = skip_members
        self._stop = False
        self.results = {}
        self.playlists = {}
        self.metadata = {}

    def run(self):
        opts = {
            'quiet': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'user_agent': get_random_user_agent(),
            'playlistend': 200,
        }

        for i, url in enumerate(self.urls, 1):
            if self._stop:
                break

            if self.progress_cb:
                self.progress_cb(i, len(self.urls), url)

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    if not info:
                        self.results[url] = f"⚠️ {url}"
                        continue

                    if self.skip_private and info.get('availability') == 'private':
                        self.results[url] = f"🔒 {url} (Özel)"
                        continue
                    if self.skip_members and info.get('availability') in (
                        'premium', 'subscriber_only', 'members_only'
                    ):
                        self.results[url] = f"🔒 {url} (Üyelik)"
                        continue

                    if info.get('_type') == 'playlist':
                        pl_title = info.get('title') or 'Playlist'
                        pl_title = re.sub(r'\s*\(Playlist\s*-\s*\d+\s*video\)\s*$', '', pl_title, flags=re.I)
                        pl_title = re.sub(r'\s*\(\d+\s*video\)\s*$', '', pl_title).strip()

                        entries = info.get('entries') or []
                        count = len(entries)
                        self.playlists[url] = pl_title
                        self.results[url] = f"📁 {pl_title} ({count} video)"
                        self.metadata[url] = info
                    else:
                        title = info.get('title', url)
                        dur = info.get('duration')
                        if dur:
                            self.results[url] = f"🎬 {title} ({format_duration(dur)})"
                        else:
                            self.results[url] = f"🎬 {title}"
                        self.metadata[url] = info

            except Exception as e:
                err = str(e).lower()
                if "private" in err:
                    self.results[url] = f"🔒 {url} (Özel)"
                elif "members" in err:
                    self.results[url] = f"🔒 {url} (Üyelik)"
                else:
                    self.results[url] = f"❌ {url} ({str(e)[:40]})"

        try:
            self.callback(self.results, self.playlists, self.metadata)
        except Exception as e:
            print(f"Callback hatası: {e}")

    def stop(self):
        self._stop = True


# ============================================================
# 9. DOWNLOAD THREAD
# ============================================================
FORMAT_MAP = {
    "best":   "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p":  "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "720p":   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
    "480p":   "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
    "360p":   "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
}

AUDIO_CODECS = ["mp3", "m4a", "flac", "wav", "aac", "ogg", "opus", "wma"]

AUDIO_QUALITY_MAP = {
    "mp3":  ["-acodec", "libmp3lame", "-ab", "192k"],
    "m4a":  ["-acodec", "aac", "-b:a", "192k"],
    "flac": ["-acodec", "flac"],
    "wav":  ["-acodec", "pcm_s16le"],
    "aac":  ["-acodec", "aac", "-b:a", "192k"],
    "ogg":  ["-acodec", "libvorbis", "-qscale:a", "5"],
    "opus": ["-acodec", "libopus", "-b:a", "192k"],
    "wma":  ["-acodec", "wmav2", "-ab", "192k"],
}


class DownloadThread(threading.Thread):
    def __init__(self, urls, titles, playlists, metadata, save_path,
                 quality="best", out_format="mp4", concurrent=3, ffmpeg=None,
                 skip_private=True, skip_members=True,
                 playlist_folder=True, channel_folder=False,
                 video_folder=False, auto_cleanup=True, notify=True,
                 proxy="", speed_limit=0, normalize_audio=False,
                 sound_on_complete=False, file_template="%(title)s",
                 embed_thumbnail=True):
        super().__init__(daemon=True)

        self.urls = [u for u in urls if titles.get(u, '').startswith(('🎬', '📁'))]
        self.titles = titles
        self.playlists = playlists
        self.metadata = metadata
        self.save_path = save_path
        self.quality = quality
        self.out_format = out_format.lower()
        self.ffmpeg = ffmpeg
        self.skip_private = skip_private
        self.skip_members = skip_members
        self.playlist_folder = playlist_folder
        self.channel_folder = channel_folder
        self.video_folder = video_folder
        self.auto_cleanup = auto_cleanup
        self.notify = notify
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.normalize_audio = normalize_audio
        self.sound_on_complete = sound_on_complete
        self.file_template = file_template
        self.embed_thumbnail = embed_thumbnail

        # Çıktı formatı ses mi?
        self.is_audio_output = self.out_format in AUDIO_CODECS
        self.concurrent = 1 if self.is_audio_output else (concurrent if ffmpeg else 1)

        # Kontrol
        self._pause = False
        self._stop = False
        self._pause_event = threading.Event()
        self._pause_event.set()

        # İstatistik
        self.total = len(self.urls)
        self.completed_count = 0
        self.error_count = 0
        self.skipped_count = 0

        # Callbacks
        self.cb_bar = None
        self.cb_speed = None
        self.cb_status = None
        self.cb_done = None
        self.cb_error = None
        self.cb_item = None
        self.cb_pause = None

    def pause(self):
        self._pause = True
        self._pause_event.clear()
        if self.cb_pause:
            self.cb_pause(True)

    def resume(self):
        self._pause = False
        self._pause_event.set()
        if self.cb_pause:
            self.cb_pause(False)

    def is_paused(self) -> bool:
        return self._pause

    def stop(self):
        self._stop = True
        self._pause_event.set()

    def _make_hook(self):
        def hook(d):
            while self._pause and not self._stop:
                time.sleep(0.3)

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
                    eta_str = f"{eta // 60}:{eta % 60:02d}" if eta > 0 else "??:??"
                    self.cb_speed(f"{mb:.1f} MB/s", eta_str)

            elif d['status'] == 'finished':
                if self.cb_bar:
                    self.cb_bar(100)
        return hook

    def _get_folder(self, url: str, title: str) -> str:
        folder = self.save_path
        if self.playlist_folder and url in self.playlists:
            folder = os.path.join(folder, sanitize_filename(self.playlists[url]))
        if self.channel_folder and url in self.metadata:
            ch = self.metadata[url].get('uploader', '')
            if ch:
                folder = os.path.join(folder, sanitize_filename(ch))
        if self.video_folder:
            folder = os.path.join(folder, title)
        return folder

    def _build_opts(self, outtmpl, selector, post_processors) -> dict:
        opts = {
            "outtmpl": outtmpl,
            "format": selector,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "progress_hooks": [self._make_hook()],
            "noplaylist": False,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": self.concurrent,
            "postprocessors": post_processors,
            "user_agent": get_random_user_agent(),
            "socket_timeout": 30,
            "nopart": False,
            "keepvideo": False,
            "keepfragments": False,
            "trim_file_name": 200,
            "paths": {"temp": tempfile.gettempdir()},
            "postprocessor_args": {"ffmpeg": ["-y"]},
        }

        if self.proxy:
            opts["proxy"] = self.proxy
        if self.speed_limit > 0:
            opts["ratelimit"] = int(self.speed_limit * 1024 * 1024)
        if self.ffmpeg and os.path.isfile(self.ffmpeg):
            opts["ffmpeg_location"] = self.ffmpeg

        return opts

    def _manual_convert(self, raw_path: str, target_fmt: str) -> Optional[str]:
        """Post-processor başarısız olursa manuel ffmpeg dönüşümü."""
        if not self.ffmpeg or not os.path.isfile(self.ffmpeg):
            return None
        if not os.path.exists(raw_path):
            return None

        base = os.path.splitext(raw_path)[0]
        target = f"{base}.{target_fmt}"

        if os.path.exists(target):
            return target

        try:
            codec_args = AUDIO_QUALITY_MAP.get(target_fmt, ["-acodec", "libmp3lame", "-ab", "192k"])
            cmd = [self.ffmpeg, "-i", raw_path, "-vn"] + codec_args + ["-y", target]
            result = subprocess.run(cmd, capture_output=True, timeout=900)

            if result.returncode == 0 and os.path.exists(target):
                try:
                    os.remove(raw_path)
                except Exception:
                    pass
                return target
        except Exception as e:
            print(f"Manuel dönüşüm hatası: {e}")
        return None

    def _build_template(self, ext_placeholder: str) -> str:
        template = self.file_template
        template = template.replace("{title}", "%(title)s")
        template = template.replace("{channel}", "%(uploader)s")
        template = template.replace("{date}", "%(upload_date)s")
        template = template.replace("{id}", "%(id)s")
        return template + ext_placeholder

    def run(self):
        if not self.urls:
            if self.cb_done:
                self.cb_done()
            return

        for i, url in enumerate(self.urls, start=1):
            if self._stop:
                break

            while self._pause and not self._stop:
                time.sleep(0.3)

            if self._stop:
                break

            raw_title = self.titles.get(url, f"URL {i}")
            clean = clean_title(raw_title)

            if self.cb_status:
                self.cb_status(f"📥 {i}/{self.total} - {clean}")

            try:
                folder = self._get_folder(url, clean)
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                self.error_count += 1
                if self.cb_error:
                    self.cb_error(f"Klasör hatası: {e}")
                continue

            # ============ FORMAT AYARLARI ============
            quality = self.quality
            out_fmt = self.out_format

            if self.is_audio_output:
                # SES ÇIKTISI
                audio_fmt = out_fmt
                # Kaliteden bit rate
                if quality == "MP3 (320k)":
                    q_val = "320"
                elif quality == "MP3 (128k)":
                    q_val = "128"
                else:
                    q_val = "192"

                selector = "bestaudio/best"

                post_processors = [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_fmt,
                        'preferredquality': q_val,
                        'nopostoverwrites': False,
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                ]

                if self.embed_thumbnail:
                    post_processors.append({'key': 'EmbedThumbnail'})

                template = self._build_template(f".{audio_fmt}")
                outtmpl = os.path.join(folder, template)

            else:
                # VİDEO ÇIKTISI
                if out_fmt == "mkv":
                    selector = "bestvideo+bestaudio/best"
                    merge_fmt = "mkv"
                elif out_fmt == "webm":
                    selector = "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]"
                    merge_fmt = "webm"
                else:  # mp4
                    selector = FORMAT_MAP.get(quality, FORMAT_MAP["best"])
                    merge_fmt = "mp4"

                post_processors = []
                if self.embed_thumbnail:
                    post_processors.append({'key': 'EmbedThumbnail'})
                    post_processors.append({'key': 'FFmpegMetadata', 'add_metadata': True})

                template = self._build_template(".%(ext)s")
                outtmpl = os.path.join(folder, template)

            # İNDİR
            try:
                opts = self._build_opts(outtmpl, selector, post_processors)

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                if not info or self._stop:
                    continue

                # Dosya yolu
                real_path = ""
                try:
                    raw_path = ydl.prepare_filename(info)
                    if self.is_audio_output:
                        base = os.path.splitext(raw_path)[0]
                        target = f"{base}.{out_fmt}"
                        if os.path.exists(target):
                            real_path = target
                        elif os.path.exists(raw_path):
                            converted = self._manual_convert(raw_path, out_fmt)
                            real_path = converted if converted else raw_path
                    else:
                        real_path = raw_path
                except Exception:
                    pass

                item = DownloadItem(
                    url=url,
                    title=info.get('title', clean),
                    status="completed",
                    format=out_fmt if self.is_audio_output else info.get('ext', out_fmt),
                    channel=info.get('uploader', ''),
                    duration=format_duration(info.get('duration', 0)),
                    folder_path=folder,
                    playlist_title=self.playlists.get(url, ''),
                    date_added=datetime.now().strftime("%d.%m.%Y %H:%M"),
                )

                if real_path and os.path.exists(real_path):
                    item.size = format_size(os.path.getsize(real_path))
                    item.file_path = real_path

                self.completed_count += 1
                if self.cb_item:
                    self.cb_item(item)

                if self.auto_cleanup:
                    TempCleaner.clean_folder(folder, recursive=True)

            except DownloadCancelled:
                break
            except Exception as e:
                if self._stop:
                    break

                if self.cb_bar:
                    self.cb_bar(0)

                err = str(e).lower()
                if "private" in err:
                    self.skipped_count += 1
                    msg = f"🔒 Özel atlandı: {clean}"
                elif "members" in err:
                    self.skipped_count += 1
                    msg = f"⚠️ Üyelik: {clean}"
                else:
                    self.error_count += 1
                    msg = f"❌ Hata: {clean} - {str(e)[:60]}"

                if self.cb_status:
                    self.cb_status(msg)

        if self.auto_cleanup:
            TempCleaner.clean_folder(self.save_path, recursive=True)

        if self.cb_done:
            self.cb_done()


# ============================================================
# 10. CONVERTER WINDOW
# ============================================================
class ConverterWindow(ctk.CTkToplevel):
    AUDIO_CMD = {
        "mp3":  ["-acodec", "libmp3lame", "-ab", "192k"],
        "wma":  ["-acodec", "wmav2", "-ab", "192k"],
        "aac":  ["-acodec", "aac", "-b:a", "192k"],
        "flac": ["-acodec", "flac"],
        "ogg":  ["-acodec", "libvorbis", "-qscale:a", "5"],
        "m4a":  ["-acodec", "aac", "-b:a", "192k", "-f", "ipod"],
        "wav":  ["-acodec", "pcm_s16le"],
    }

    def __init__(self, master, theme: dict, ffmpeg_path: Optional[str]):
        super().__init__(master)
        self.title("🔄 Medya Dönüştürücü")
        self.geometry("820x680")
        self.minsize(700, 560)
        self.theme = theme
        self.ffmpeg_path = ffmpeg_path
        self.files: List[str] = []
        self.out_fmt = ctk.StringVar(value="mp3")
        self.out_dir = ""
        self.file_widgets: List[Tuple[ctk.CTkLabel, str]] = []

        self.configure(fg_color=theme["bg_primary"])
        self._build()
        self._check_ffmpeg()
        self.lift()
        self.focus_force()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")

        ctk.CTkLabel(
            header, text="🔄  Medya Dönüştürücü",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        self.ffmpeg_lbl = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.ffmpeg_lbl.pack(side="right")

        # Kaynak
        src_card = ctk.CTkFrame(
            self, fg_color=self.theme["bg_card"],
            corner_radius=16, border_width=1, border_color=self.theme["border"]
        )
        src_card.grid(row=1, column=0, padx=25, pady=10, sticky="ew")
        src_card.grid_columnconfigure(0, weight=1)

        self.src_lbl = ctk.CTkLabel(
            src_card, text="📁  Henüz dosya seçilmedi",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"],
            anchor="w", height=40
        )
        self.src_lbl.grid(row=0, column=0, padx=15, pady=12, sticky="ew")

        btn_box = ctk.CTkFrame(src_card, fg_color="transparent")
        btn_box.grid(row=0, column=1, padx=10, pady=10)

        self._btn(btn_box, "📄 Dosya", self._add_files, "secondary", 100).pack(side="left", padx=3)
        self._btn(btn_box, "📂 Klasör", self._add_folder, "secondary", 100).pack(side="left", padx=3)
        self._btn(btn_box, "🗑️ Temizle", self._clear, "danger", 90).pack(side="left", padx=3)

        # Format
        fmt_card = ctk.CTkFrame(
            self, fg_color=self.theme["bg_card"],
            corner_radius=16, border_width=1, border_color=self.theme["border"]
        )
        fmt_card.grid(row=2, column=0, padx=25, pady=10, sticky="ew")

        fmt_inner = ctk.CTkFrame(fmt_card, fg_color="transparent")
        fmt_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            fmt_inner, text="🎵 Format:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkOptionMenu(
            fmt_inner,
            values=["mp3", "wma", "aac", "flac", "ogg", "m4a", "wav"],
            variable=self.out_fmt, width=130, height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            button_color=self.theme["accent"],
            dropdown_fg_color=self.theme["bg_card"],
        ).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            fmt_inner, text="📂 Çıktı:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left", padx=(0, 10))

        self.out_lbl = ctk.CTkLabel(
            fmt_inner, text="Kaynak klasör",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        )
        self.out_lbl.pack(side="left", fill="x", expand=True)

        self._btn(fmt_inner, "📁 Seç", self._pick_out, "secondary", 80).pack(side="right")

        # Liste
        list_card = ctk.CTkFrame(
            self, fg_color=self.theme["bg_card"],
            corner_radius=16, border_width=1, border_color=self.theme["border"]
        )
        list_card.grid(row=4, column=0, padx=25, pady=10, sticky="nsew")
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            list_card, text="📋  Dosya Listesi",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.listbox = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.listbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")

        # Alt
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=5, column=0, padx=25, pady=(10, 20), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.pbar = ctk.CTkProgressBar(
            bottom, height=10, corner_radius=5,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["accent"]
        )
        self.pbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.pbar.set(0)

        self.stat_lbl = ctk.CTkLabel(
            bottom, text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.stat_lbl.grid(row=1, column=0, sticky="w")

        self.conv_btn = self._btn(bottom, "🔄  Dönüştürmeyi Başlat", self._start, "success", 240, 46)
        self.conv_btn.grid(row=2, column=0, sticky="ew", pady=(15, 0))

    def _btn(self, parent, text, cmd, variant, width=100, height=36):
        colors = {
            "primary": (self.theme["button_bg"], self.theme["button_hover"]),
            "secondary": (self.theme["bg_input"], self.theme["bg_hover"]),
            "success": ("#10B981", "#059669"),
            "danger": ("#EF4444", "#DC2626"),
        }
        bg, hover = colors.get(variant, colors["primary"])
        return ctk.CTkButton(
            parent, text=text, command=cmd,
            width=width, height=height, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=bg, hover_color=hover,
            text_color="white" if variant in ("primary", "success", "danger") else self.theme["text_primary"]
        )

    def _check_ffmpeg(self):
        ok = bool(self.ffmpeg_path and os.path.isfile(self.ffmpeg_path))
        if ok:
            self.ffmpeg_lbl.configure(text="✅ FFmpeg hazır", text_color="#10B981")
        else:
            self.ffmpeg_lbl.configure(text="❌ FFmpeg yok", text_color="#EF4444")
            self.conv_btn.configure(state="disabled")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            parent=self, title="Medya dosyaları seç",
            filetypes=[("Medya", "*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.ogg *.m4a *.wma *.aac"), ("Tümü", "*.*")]
        )
        if paths:
            self.files.extend(paths)
            self._refresh()
        self.lift()
        self.focus_force()

    def _add_folder(self):
        d = filedialog.askdirectory(parent=self, title="Klasör seç")
        if d:
            exts = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.mp3', '.wav',
                    '.flac', '.ogg', '.m4a', '.wma', '.aac')
            self.files = []
            for root, _, names in os.walk(d):
                for n in names:
                    if n.lower().endswith(exts):
                        self.files.append(os.path.join(root, n))
            self.src_lbl.configure(text=f"📂  {d}")
            self._refresh()
        self.lift()
        self.focus_force()

    def _clear(self):
        self.files.clear()
        self.src_lbl.configure(text="📁  Henüz dosya seçilmedi")
        self._refresh()

    def _refresh(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self.file_widgets.clear()

        for i, path in enumerate(self.files):
            row = ctk.CTkFrame(self.listbox, fg_color=self.theme["bg_input"], corner_radius=8)
            row.pack(fill="x", padx=3, pady=3)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row, text=f"{i+1}.  {os.path.basename(path)}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self.theme["text_primary"],
                anchor="w"
            ).grid(row=0, column=0, padx=10, pady=6, sticky="ew")

            sl = ctk.CTkLabel(
                row, text="⏳ bekliyor", width=110, height=24,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                fg_color=("#4A4A4A", "#2A2A2A"),
                text_color=self.theme["text_secondary"],
                corner_radius=6
            )
            sl.grid(row=0, column=1, padx=10, pady=6)
            self.file_widgets.append((sl, path))

        self.stat_lbl.configure(text=f"{len(self.files)} dosya")

    def _pick_out(self):
        d = filedialog.askdirectory(parent=self, title="Çıktı klasörü seç")
        if d:
            self.out_dir = d
            self.out_lbl.configure(text=d[:40] + ("..." if len(d) > 40 else ""))
        self.lift()
        self.focus_force()

    def _start(self):
        if not self.files:
            messagebox.showwarning("Uyarı", "Dosya seçin!", parent=self)
            return
        if not self.ffmpeg_path or not os.path.isfile(self.ffmpeg_path):
            messagebox.showerror("Hata", "FFmpeg yok!", parent=self)
            return
        self.conv_btn.configure(state="disabled", text="⏳ Dönüştürülüyor...")
        self.pbar.set(0)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        fmt = self.out_fmt.get()
        total = len(self.file_widgets)

        for i, (slbl, path) in enumerate(self.file_widgets):
            self.after(0, lambda s=slbl: s.configure(
                text="🔄 dönüşüyor",
                fg_color=("#FFAA00", "#806600")
            ))

            base = os.path.splitext(os.path.basename(path))[0]
            target_dir = self.out_dir or os.path.dirname(path)
            out_path = os.path.join(target_dir, f"{base}.{fmt}")

            counter = 1
            while os.path.exists(out_path):
                out_path = os.path.join(target_dir, f"{base}_{counter}.{fmt}")
                counter += 1

            try:
                codec_args = self.AUDIO_CMD.get(fmt, ["-acodec", "libmp3lame", "-ab", "192k"])
                cmd = [self.ffmpeg_path, "-i", path, "-vn"] + codec_args + ["-y", out_path]
                result = subprocess.run(cmd, capture_output=True, timeout=900)

                if result.returncode == 0 and os.path.exists(out_path):
                    self.after(0, lambda s=slbl: s.configure(
                        text="✅ tamam", fg_color=("#10B981", "#059669")
                    ))
                else:
                    err_raw = result.stderr or "FFmpeg hatası"
                    if isinstance(err_raw, bytes):
                        err_raw = err_raw.decode('utf-8', errors='replace')
                    self.after(0, lambda s=slbl: s.configure(
                        text="❌ hata", fg_color=("#EF4444", "#DC2626")
                    ))
            except Exception:
                self.after(0, lambda s=slbl: s.configure(
                    text="❌ hata", fg_color=("#EF4444", "#DC2626")
                ))

            self.after(0, lambda v=(i + 1) / total: self.pbar.set(v))

        self.after(0, self._done)

    def _done(self):
        self.conv_btn.configure(state="normal", text="🔄  Dönüştürmeyi Başlat")
        self.stat_lbl.configure(text="✅ Tamamlandı!")
        self.pbar.set(1.0)
        messagebox.showinfo("Bitti", f"{len(self.files)} dosya dönüştürüldü.", parent=self)
        self.lift()
        self.focus_force()


# ============================================================
# 11. TEMALAR
# ============================================================
THEMES = {
    "dark": {
        "bg_primary": "#0F0F1E",
        "bg_secondary": "#16162E",
        "bg_card": "#1C1C3A",
        "bg_input": "#26264A",
        "bg_hover": "#32325E",
        "text_primary": "#F8F8FF",
        "text_secondary": "#B0B0D0",
        "text_muted": "#7070A0",
        "accent": "#8B5CF6",
        "accent_hover": "#A78BFA",
        "accent_light": "#2D1F5E",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "border": "#2E2E5A",
        "sidebar_bg": "#0A0A18",
        "header_bg": "#16162E",
        "button_bg": "#8B5CF6",
        "button_hover": "#7C3AED",
        "progress_bg": "#1C1C3A",
        "progress_fg": "#8B5CF6",
    },
    "light": {
        "bg_primary": "#F5F3FF",
        "bg_secondary": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_input": "#F0EEFF",
        "bg_hover": "#E8E5FF",
        "text_primary": "#1A1A2E",
        "text_secondary": "#5A5A7A",
        "text_muted": "#9090A8",
        "accent": "#8B5CF6",
        "accent_hover": "#7C3AED",
        "accent_light": "#EDE9FE",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "border": "#E8E5FF",
        "sidebar_bg": "#FFFFFF",
        "header_bg": "#FFFFFF",
        "button_bg": "#8B5CF6",
        "button_hover": "#7C3AED",
        "progress_bg": "#E8E5FF",
        "progress_fg": "#8B5CF6",
    },
}


# ============================================================
# 12. ANA UYGULAMA
# ============================================================
class NeoTubeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1400x880")
        self.minsize(1100, 700)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Veri
        self.settings = Settings()
        self.history: List[DownloadItem] = []
        self.favorites: List[Favorite] = []
        self.queue: List[QueueItem] = []
        self.stats = Stats()
        self.url_titles: Dict[str, str] = {}
        self.playlists: Dict[str, str] = {}
        self.metadata: Dict[str, dict] = {}
        self.resolved_urls: List[str] = []
        self.url_widgets: List = []

        # Durum
        self.is_downloading = False
        self.is_paused = False
        self.download_thread: Optional[DownloadThread] = None
        self.resolver_thread: Optional[TitleResolver] = None
        self.converter_window: Optional[ConverterWindow] = None
        self._resolve_timer = None

        # FFmpeg
        self.ffmpeg_path = FFmpegManager.get_ffmpeg_path()
        self.ffmpeg_ok = bool(self.ffmpeg_path and os.path.isfile(self.ffmpeg_path))

        # Yükle
        self._load_all()

        # Tema
        self.current_theme = self.settings.theme
        self.theme = THEMES[self.current_theme]
        ctk.set_appearance_mode(self.current_theme)

        # Değişkenler
        self.quality_var = ctk.StringVar(value=self.settings.default_quality)
        self.format_var = ctk.StringVar(value=self.settings.default_format)
        self.subtitle_var = ctk.BooleanVar(value=False)
        self.playlist_folder_var = ctk.BooleanVar(value=self.settings.playlist_folder)
        self.channel_folder_var = ctk.BooleanVar(value=self.settings.channel_folder)
        self.video_folder_var = ctk.BooleanVar(value=self.settings.video_folder)
        self.skip_members_var = ctk.BooleanVar(value=self.settings.skip_members_only)
        self.skip_private_var = ctk.BooleanVar(value=self.settings.skip_private_videos)
        self.embed_thumb_var = ctk.BooleanVar(value=self.settings.embed_thumbnail)
        self.notify_var = ctk.BooleanVar(value=self.settings.notify_on_complete)
        self.cleanup_var = ctk.BooleanVar(value=self.settings.auto_cleanup)
        self.concurrent_var = ctk.StringVar(value=str(self.settings.concurrent_downloads))
        self.proxy_var = ctk.StringVar(value=self.settings.proxy)
        self.speed_var = ctk.StringVar(value=str(self.settings.speed_limit))
        self.normalize_var = ctk.BooleanVar(value=self.settings.normalize_audio)
        self.sound_var = ctk.BooleanVar(value=self.settings.sound_on_complete)
        self.template_var = ctk.StringVar(value=self.settings.file_template)

        os.makedirs(self.settings.download_path, exist_ok=True)

        # UI
        self._build_ui()
        self._update_ffmpeg_status()
        self._setup_shortcuts()

        if self.settings.auto_cleanup:
            self.after(2000, self._initial_cleanup)

        if not self.ffmpeg_ok:
            self.after(1000, self._download_ffmpeg_bg)

    # ============================================================
    # VERİ
    # ============================================================
    def _base_dir(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _load_all(self):
        for loader in [
            self._load_settings, self._load_history, self._load_favorites,
            self._load_stats, self._load_queue,
        ]:
            try:
                loader()
            except Exception:
                pass

    def _load_settings(self):
        path = os.path.join(self._base_dir(), "neotube_settings.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.settings = Settings.from_dict(json.load(f))

    def _save_settings(self):
        path = os.path.join(self._base_dir(), "neotube_settings.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_history(self):
        path = os.path.join(self._base_dir(), "neotube_data.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.history = [DownloadItem.from_dict(d) for d in data.get("history", [])]

    def _save_history(self):
        path = os.path.join(self._base_dir(), "neotube_data.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"history": [d.to_dict() for d in self.history[-MAX_HISTORY_SIZE:]]},
                          f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_favorites(self):
        path = os.path.join(self._base_dir(), "neotube_favorites.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.favorites = [Favorite.from_dict(d) for d in json.load(f)]

    def _save_favorites(self):
        path = os.path.join(self._base_dir(), "neotube_favorites.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([f.to_dict() for f in self.favorites], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_stats(self):
        path = os.path.join(self._base_dir(), "neotube_stats.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.stats = Stats.from_dict(json.load(f))

    def _save_stats(self):
        path = os.path.join(self._base_dir(), "neotube_stats.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.stats.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_queue(self):
        path = os.path.join(self._base_dir(), "neotube_queue.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.queue = [QueueItem.from_dict(d) for d in json.load(f)]

    def _save_queue(self):
        path = os.path.join(self._base_dir(), "neotube_queue.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([q.to_dict() for q in self.queue], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ============================================================
    # TEMİZLİK / FFMPEG
    # ============================================================
    def _initial_cleanup(self):
        def worker():
            try:
                removed = TempCleaner.clean_folder(self.settings.download_path, recursive=True)
                if removed > 0:
                    self.after(0, lambda: self._set_status(f"🧹 {removed} geçici dosya temizlendi"))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _cleanup_now(self):
        def worker():
            try:
                removed = TempCleaner.clean_folder(self.settings.download_path, recursive=True)
                self.after(0, lambda: messagebox.showinfo("Temizlik", f"{removed} geçici dosya silindi."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Hata", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _update_ffmpeg_status(self):
        try:
            if self.ffmpeg_ok:
                self.ffmpeg_lbl.configure(text="✅ FFmpeg", text_color=self.theme["success"])
            else:
                self.ffmpeg_lbl.configure(text="⏳ FFmpeg...", text_color=self.theme["warning"])
        except Exception:
            pass

    def _download_ffmpeg_bg(self):
        def worker():
            try:
                path = FFmpegManager.get_ffmpeg_path()
                if path and os.path.isfile(path):
                    self.ffmpeg_path = path
                    self.ffmpeg_ok = True
                    self.after(0, self._update_ffmpeg_status)
                else:
                    self.after(0, lambda: self.ffmpeg_lbl.configure(
                        text="❌ FFmpeg yok", text_color=self.theme["error"]
                    ))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    # ============================================================
    # UI OLUŞTURMA
    # ============================================================
    def _build_ui(self):
        self.configure(fg_color=self.theme["bg_primary"])

        self._build_sidebar()

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

        self._build_header()

        self.pages = {}
        self.current_page = None
        self._build_home_page()
        self._build_downloads_page()
        self._build_queue_page()
        self._build_history_page()
        self._build_favorites_page()
        self._build_settings_page()
        self._build_about_page()
        self.show_page("home")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, fg_color=self.theme["sidebar_bg"],
            width=100, corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_box = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=110)
        logo_box.pack(fill="x", padx=15, pady=(25, 15))
        logo_box.pack_propagate(False)

        logo_inner = ctk.CTkFrame(
            logo_box, fg_color=self.theme["accent_light"],
            width=64, height=64, corner_radius=20
        )
        logo_inner.place(relx=0.5, rely=0.5, anchor="center")
        logo_inner.pack_propagate(False)

        ctk.CTkLabel(
            logo_inner, text="▶",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.theme["accent"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Navigasyon
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=18, pady=10)

        self.nav_buttons = {}
        items = [
            ("home", "🏠", "Ana Sayfa"),
            ("downloads", "⬇", "İndirmeler"),
            ("queue", "📋", "Kuyruk"),
            ("history", "📜", "Geçmiş"),
            ("favorites", "⭐", "Favoriler"),
            ("settings", "⚙", "Ayarlar"),
            ("about", "ℹ", "Hakkında"),
        ]

        for pid, icon, tip in items:
            btn = ctk.CTkButton(
                nav, text=icon, width=64, height=64, corner_radius=20,
                font=ctk.CTkFont(family="Segoe UI", size=26),
                fg_color="transparent",
                hover_color=self.theme["accent_light"],
                text_color=self.theme["text_secondary"],
                command=lambda p=pid: self.show_page(p)
            )
            btn.pack(pady=6)
            self.nav_buttons[pid] = btn

        # Alt
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=18, pady=25)

        ctk.CTkButton(
            bottom, text="🔄", width=64, height=64, corner_radius=20,
            font=ctk.CTkFont(family="Segoe UI", size=26),
            fg_color="transparent",
            hover_color=self.theme["accent_light"],
            text_color=self.theme["text_secondary"],
            command=self._open_converter
        ).pack(pady=6)

        ctk.CTkButton(
            bottom, text="🧹", width=64, height=64, corner_radius=20,
            font=ctk.CTkFont(family="Segoe UI", size=26),
            fg_color="transparent",
            hover_color=self.theme["accent_light"],
            text_color=self.theme["text_secondary"],
            command=self._cleanup_now
        ).pack(pady=6)

        self.theme_btn = ctk.CTkButton(
            bottom,
            text="🌙" if self.current_theme == "dark" else "☀",
            width=64, height=64, corner_radius=20,
            font=ctk.CTkFont(family="Segoe UI", size=26),
            fg_color=self.theme["accent_light"],
            hover_color=self.theme["accent"],
            text_color=self.theme["accent"],
            command=self._toggle_theme
        )
        self.theme_btn.pack(pady=(6, 12))

        self.ffmpeg_lbl = ctk.CTkLabel(
            bottom, text="⏳ FFmpeg",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"]
        )
        self.ffmpeg_lbl.pack()

    def _build_header(self):
        self.header = ctk.CTkFrame(
            self.content, fg_color=self.theme["header_bg"],
            height=90, corner_radius=0
        )
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=30, pady=18)

        ctk.CTkLabel(
            title_box, text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text=VERSION,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w")

        url_box = ctk.CTkFrame(self.header, fg_color="transparent")
        url_box.pack(side="left", fill="x", expand=True, padx=25, pady=22)

        self.header_url = ctk.CTkEntry(
            url_box,
            placeholder_text="🔗  YouTube URL yapıştır...",
            height=46, corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            placeholder_text_color=self.theme["text_muted"],
            border_color=self.theme["border"],
            border_width=1,
        )
        self.header_url.pack(side="left", fill="x", expand=True)
        self.header_url.bind("<Return>", lambda e: self._quick_analyze())

        ctk.CTkButton(
            url_box, text="📋", width=46, height=46, corner_radius=14,
            font=ctk.CTkFont(size=18),
            fg_color=self.theme["bg_input"],
            hover_color=self.theme["bg_hover"],
            text_color=self.theme["text_primary"],
            command=self._paste
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            url_box, text="🔍 Analiz", width=110, height=46, corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            command=self._quick_analyze
        ).pack(side="left", padx=(10, 0))

        self.status_label = ctk.CTkLabel(
            self.header, text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"]
        )
        self.status_label.pack(side="right", padx=30)

    def _card(self, parent, **kw):
        return ctk.CTkFrame(
            parent, fg_color=self.theme["bg_card"],
            corner_radius=18, border_width=1,
            border_color=self.theme["border"], **kw
        )

    def _btn(self, parent, text, cmd, variant="primary", width=120, height=40, font_size=13):
        colors = {
            "primary": (self.theme["button_bg"], self.theme["button_hover"]),
            "secondary": (self.theme["bg_input"], self.theme["bg_hover"]),
            "success": ("#10B981", "#059669"),
            "danger": ("#EF4444", "#DC2626"),
            "warning": ("#F59E0B", "#D97706"),
        }
        bg, hover = colors.get(variant, colors["primary"])
        return ctk.CTkButton(
            parent, text=text, command=cmd,
            width=width, height=height, corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"),
            fg_color=bg, hover_color=hover,
            text_color="white" if variant in ("primary", "success", "danger", "warning") else self.theme["text_primary"]
        )

    def _build_home_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["home"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        # ===== URL KARTI =====
        url_card = self._card(scroll)
        url_card.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(url_card, fg_color="transparent")
        inner.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            inner, text="🔗  Video URL'leri",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        single_row = ctk.CTkFrame(inner, fg_color="transparent")
        single_row.pack(fill="x", pady=(14, 0))

        self.url_entry = ctk.CTkEntry(
            single_row,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=48, corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            placeholder_text_color=self.theme["text_muted"],
            border_color=self.theme["border"],
            border_width=1,
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<KeyRelease>", lambda e: self._on_url_change())

        self._btn(single_row, "🔍 Analiz Et", self._analyze_url, "primary", 140, 48).pack(side="left", padx=(12, 0))
        self._btn(single_row, "⭐", self._add_fav_from_url, "secondary", 48, 48, 18).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            inner, text="📋  Toplu URL (her satıra bir URL)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["text_secondary"]
        ).pack(anchor="w", pady=(20, 6))

        self.batch_text = ctk.CTkTextbox(
            inner, height=95, corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            border_color=self.theme["border"],
            border_width=1,
        )
        self.batch_text.pack(fill="x")
        self.batch_text.bind("<KeyRelease>", self._on_batch_change)

        batch_btns = ctk.CTkFrame(inner, fg_color="transparent")
        batch_btns.pack(fill="x", pady=(12, 0))

        self._btn(batch_btns, "📁 Dosyadan", self._import_from_file, "secondary", 140, 36, 11).pack(side="left", padx=(0, 10))
        self._btn(batch_btns, "🗑️ Temizle", self._clear_batch, "secondary", 120, 36, 11).pack(side="left")

        self.url_count_lbl = ctk.CTkLabel(
            batch_btns, text="0 URL",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.theme["text_muted"]
        )
        self.url_count_lbl.pack(side="right")

        # Resolving
        self.resolve_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        self.resolve_frame.pack(fill="x", padx=28, pady=(0, 18))
        self.resolve_frame.pack_forget()

        self.resolve_lbl = ctk.CTkLabel(
            self.resolve_frame, text="🔍 URL'ler çözümleniyor...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.resolve_lbl.pack(anchor="w")

        self.resolve_bar = ctk.CTkProgressBar(
            self.resolve_frame, height=8, corner_radius=4,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["accent"]
        )
        self.resolve_bar.pack(fill="x", pady=(10, 0))
        self.resolve_bar.set(0)

        self.url_list = ctk.CTkScrollableFrame(url_card, height=160, fg_color="transparent")
        self.url_list.pack(fill="x", padx=28, pady=(0, 18))

        self.start_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        self.start_frame.pack(fill="x", padx=28, pady=(0, 22))
        self.start_frame.pack_forget()

        self.start_btn = self._btn(self.start_frame, "▶  İndirmeyi Başlat", self._start_download, "success", 240, 50, 14)
        self.start_btn.pack(side="left", padx=(0, 12))

        self._btn(
            self.start_frame, "➕  Kuyruğa Ekle", self._add_to_queue,
            "primary", 200, 50, 14
        ).pack(side="left")

        # ===== İLERLEME KARTI =====
        self.progress_card = self._card(scroll)
        self.progress_card.pack(fill="x", pady=(0, 15))
        self.progress_card.pack_forget()

        p_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        p_inner.pack(fill="x", padx=28, pady=25)

        p_head = ctk.CTkFrame(p_inner, fg_color="transparent")
        p_head.pack(fill="x")

        ctk.CTkLabel(
            p_head, text="📊  İndirme Durumu",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        self.speed_lbl = ctk.CTkLabel(
            p_head, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["accent"]
        )
        self.speed_lbl.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            p_inner, height=16, corner_radius=8,
            fg_color=self.theme["progress_bg"],
            progress_color=self.theme["accent"]
        )
        self.progress_bar.pack(fill="x", pady=(18, 10))
        self.progress_bar.set(0)

        self.progress_info = ctk.CTkLabel(
            p_inner, text="Hazır",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.progress_info.pack(anchor="w")

        ctrl_box = ctk.CTkFrame(p_inner, fg_color="transparent")
        ctrl_box.pack(fill="x", pady=(20, 0))

        self.pause_btn = self._btn(ctrl_box, "⏸  Duraklat", self._toggle_pause, "warning", 180, 50, 13)
        self.pause_btn.pack(side="left", padx=(0, 12))

        self.stop_btn = self._btn(ctrl_box, "⏹  Durdur", self._stop_download, "danger", 150, 50, 13)
        self.stop_btn.pack(side="left")

        # ===== SEÇENEKLER =====
        opt_card = self._card(scroll)
        opt_card.pack(fill="x", pady=(0, 15))

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            opt_inner, text="⚙  İndirme Seçenekleri",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        opt_grid = ctk.CTkFrame(opt_inner, fg_color="transparent")
        opt_grid.pack(fill="x", pady=(18, 0))

        # Kalite
        q_box = ctk.CTkFrame(opt_grid, fg_color="transparent")
        q_box.pack(side="left", padx=(0, 22))

        ctk.CTkLabel(
            q_box, text="Kalite",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w")

        ctk.CTkOptionMenu(
            q_box,
            values=["best", "1080p", "720p", "480p", "360p",
                    "MP3 (320k)", "MP3 (128k)"],
            variable=self.quality_var, width=150, height=42,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            button_color=self.theme["accent"],
            dropdown_fg_color=self.theme["bg_card"],
            corner_radius=12,
        ).pack(pady=(6, 0))

        # FORMAT SEÇİMİ
        f_box = ctk.CTkFrame(opt_grid, fg_color="transparent")
        f_box.pack(side="left", padx=(0, 22))

        ctk.CTkLabel(
            f_box, text="Format",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w")

        ctk.CTkOptionMenu(
            f_box,
            values=["mp4", "mkv", "webm", "mp3", "m4a", "flac", "wav", "aac", "ogg"],
            variable=self.format_var, width=130, height=42,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            button_color=self.theme["accent"],
            dropdown_fg_color=self.theme["bg_card"],
            corner_radius=12,
        ).pack(pady=(6, 0))

        # Altyazı
        s_box = ctk.CTkFrame(opt_grid, fg_color="transparent")
        s_box.pack(side="left", padx=(0, 22))

        ctk.CTkLabel(
            s_box, text="Altyazı",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w")

        ctk.CTkCheckBox(
            s_box, text="İndir", variable=self.subtitle_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(pady=(14, 0))

        # Küçük resim
        t_box = ctk.CTkFrame(opt_grid, fg_color="transparent")
        t_box.pack(side="left", padx=(0, 22))

        ctk.CTkLabel(
            t_box, text="Küçük Resim",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w")

        ctk.CTkCheckBox(
            t_box, text="Ekle", variable=self.embed_thumb_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(pady=(14, 0))

        # ===== İSTATİSTİK =====
        stat_card = self._card(scroll)
        stat_card.pack(fill="x", pady=(0, 15))

        stat_inner = ctk.CTkFrame(stat_card, fg_color="transparent")
        stat_inner.pack(fill="x", padx=28, pady=22)

        ctk.CTkLabel(
            stat_inner, text="📈  İstatistikler",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        stat_row = ctk.CTkFrame(stat_inner, fg_color="transparent")
        stat_row.pack(fill="x", pady=(14, 0))

        self.stat_dl_lbl = ctk.CTkLabel(
            stat_row, text=f"📥  Toplam: {self.stats.total_downloads}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.stat_dl_lbl.pack(side="left", padx=(0, 30))

        self.stat_fav_lbl = ctk.CTkLabel(
            stat_row, text=f"⭐  Favori: {len(self.favorites)}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.stat_fav_lbl.pack(side="left", padx=(0, 30))

        self.stat_last_lbl = ctk.CTkLabel(
            stat_row, text=f"🕐  Son: {self.stats.last_download[:40] or '—'}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        )
        self.stat_last_lbl.pack(side="left")

    def _build_downloads_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["downloads"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            scroll, text="⬇  Aktif İndirmeler",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 18))

        self.dl_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.dl_list_frame.pack(fill="x")

        ctk.CTkLabel(
            self.dl_list_frame, text="🎉  Aktif indirme yok",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=self.theme["text_muted"]
        ).pack(pady=80)

    def _build_queue_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["queue"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            head, text="📋  İndirme Kuyruğu",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        btn_box = ctk.CTkFrame(head, fg_color="transparent")
        btn_box.pack(side="right")

        self._btn(btn_box, "▶  Kuyruğu Başlat", self._start_queue, "success", 180, 40, 12).pack(side="left", padx=(0, 8))
        self._btn(btn_box, "🗑  Temizle", self._clear_queue, "danger", 120, 40, 12).pack(side="left")

        self.queue_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.queue_frame.pack(fill="x")
        self._refresh_queue()

    def _build_history_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["history"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            head, text="📜  İndirme Geçmişi",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        self._btn(head, "🗑  Temizle", self._clear_history, "danger", 130, 38, 12).pack(side="right")

        self.history_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.history_frame.pack(fill="x")
        self._refresh_history()

    def _build_favorites_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["favorites"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            head, text="⭐  Favoriler",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(side="left")

        btn_box = ctk.CTkFrame(head, fg_color="transparent")
        btn_box.pack(side="right")

        self._btn(btn_box, "📤  Dışa", self._export_favs, "secondary", 110, 38, 12).pack(side="left", padx=(0, 8))
        self._btn(btn_box, "📥  İçe", self._import_favs, "secondary", 110, 38, 12).pack(side="left")

        self.favs_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.favs_frame.pack(fill="x")
        self._refresh_favorites()

    def _build_settings_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["settings"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            scroll, text="⚙  Ayarlar",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 18))

        # Genel
        c1 = self._card(scroll)
        c1.pack(fill="x", pady=(0, 15))

        i1 = ctk.CTkFrame(c1, fg_color="transparent")
        i1.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i1, text="📁  Genel",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w")

        pr = ctk.CTkFrame(i1, fg_color="transparent")
        pr.pack(fill="x", pady=(18, 0))

        ctk.CTkLabel(
            pr, text="İndirme Klasörü:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        self.path_lbl = ctk.CTkLabel(
            pr, text=self.settings.download_path,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_primary"]
        )
        self.path_lbl.pack(side="left", padx=(15, 0), fill="x", expand=True)

        self._btn(pr, "📂 Değiştir", self._change_path, "secondary", 120, 36, 11).pack(side="right")

        cr = ctk.CTkFrame(i1, fg_color="transparent")
        cr.pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(
            cr, text="Eşzamanlı İndirme:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        ctk.CTkOptionMenu(
            cr, values=["1", "2", "3", "4", "5", "8", "10"],
            variable=self.concurrent_var, width=90, height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            button_color=self.theme["accent"],
            dropdown_fg_color=self.theme["bg_card"],
            corner_radius=10,
        ).pack(side="left", padx=(15, 0))

        clr = ctk.CTkFrame(i1, fg_color="transparent")
        clr.pack(fill="x", pady=(18, 0))

        ctk.CTkCheckBox(
            clr, text="🧹  Otomatik geçici dosya temizliği",
            variable=self.cleanup_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w")

        # Ağ
        c2 = self._card(scroll)
        c2.pack(fill="x", pady=(0, 15))

        i2 = ctk.CTkFrame(c2, fg_color="transparent")
        i2.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i2, text="🌐  Ağ Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        prx = ctk.CTkFrame(i2, fg_color="transparent")
        prx.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            prx, text="Proxy:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        ctk.CTkEntry(
            prx, textvariable=self.proxy_var,
            placeholder_text="http://ip:port  veya  socks5://ip:port",
            height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            placeholder_text_color=self.theme["text_muted"],
            border_color=self.theme["border"],
        ).pack(side="left", padx=(15, 0), fill="x", expand=True)

        spd = ctk.CTkFrame(i2, fg_color="transparent")
        spd.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            spd, text="Hız Limiti (MB/s):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"]
        ).pack(side="left")

        ctk.CTkOptionMenu(
            spd, values=["0", "1", "2", "5", "10", "20", "50"],
            variable=self.speed_var, width=100, height=38,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.theme["bg_input"],
            button_color=self.theme["accent"],
            dropdown_fg_color=self.theme["bg_card"],
            corner_radius=10,
        ).pack(side="left", padx=(15, 0))

        ctk.CTkLabel(
            spd, text="  (0 = sınırsız)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"]
        ).pack(side="left")

        # Ses
        c3 = self._card(scroll)
        c3.pack(fill="x", pady=(0, 15))

        i3 = ctk.CTkFrame(c3, fg_color="transparent")
        i3.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i3, text="🎵  Ses Ayarları",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkCheckBox(
            i3, text="🔊  Ses seviyesini normalize et (loudnorm)",
            variable=self.normalize_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkCheckBox(
            i3, text="🔔  İndirme bitince sesli bildirim",
            variable=self.sound_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w", pady=(8, 0))

        # Şablon
        c4 = self._card(scroll)
        c4.pack(fill="x", pady=(0, 15))

        i4 = ctk.CTkFrame(c4, fg_color="transparent")
        i4.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i4, text="📝  Dosya Adı Şablonu",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            i4, text="Değişkenler: {title}  {channel}  {date}  {id}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkEntry(
            i4, textvariable=self.template_var,
            placeholder_text="%(title)s",
            height=40, corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=self.theme["bg_input"],
            text_color=self.theme["text_primary"],
            placeholder_text_color=self.theme["text_muted"],
            border_color=self.theme["border"],
        ).pack(fill="x")

        # Klasör
        c5 = self._card(scroll)
        c5.pack(fill="x", pady=(0, 15))

        i5 = ctk.CTkFrame(c5, fg_color="transparent")
        i5.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i5, text="📁  Klasör Yapısı",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        for txt, var in [
            ("Playlist klasörü oluştur", self.playlist_folder_var),
            ("Kanal klasörü oluştur", self.channel_folder_var),
            ("Video klasörü oluştur", self.video_folder_var),
        ]:
            ctk.CTkCheckBox(
                i5, text=txt, variable=var,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.theme["text_primary"],
                fg_color=self.theme["accent"],
                hover_color=self.theme["accent_hover"],
                border_color=self.theme["border"],
                corner_radius=6
            ).pack(anchor="w", pady=(5, 0))

        # Atlama
        c6 = self._card(scroll)
        c6.pack(fill="x", pady=(0, 15))

        i6 = ctk.CTkFrame(c6, fg_color="transparent")
        i6.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i6, text="🔒  Atlama",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        for txt, var in [
            ("Üyelik gerektiren videoları atla", self.skip_members_var),
            ("Özel videoları atla", self.skip_private_var),
        ]:
            ctk.CTkCheckBox(
                i6, text=txt, variable=var,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.theme["text_primary"],
                fg_color=self.theme["accent"],
                hover_color=self.theme["accent_hover"],
                border_color=self.theme["border"],
                corner_radius=6
            ).pack(anchor="w", pady=(5, 0))

        # Bildirim
        c7 = self._card(scroll)
        c7.pack(fill="x", pady=(0, 15))

        i7 = ctk.CTkFrame(c7, fg_color="transparent")
        i7.pack(fill="x", padx=28, pady=25)

        ctk.CTkLabel(
            i7, text="🔔  Bildirim",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkCheckBox(
            i7, text="İndirme tamamlandığında bildirim göster",
            variable=self.notify_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_primary"],
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            border_color=self.theme["border"],
            corner_radius=6
        ).pack(anchor="w")

        self._btn(scroll, "💾  Ayarları Kaydet", self._save_settings_ui, "primary", 220, 48, 13).pack(anchor="w", pady=(5, 20))

    def _build_about_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["about"] = page

        scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=25, pady=20)

        c1 = self._card(scroll)
        c1.pack(fill="x", pady=(0, 15))

        i1 = ctk.CTkFrame(c1, fg_color="transparent")
        i1.pack(fill="x", padx=35, pady=35)

        ctk.CTkLabel(
            i1, text="🎬  NeoTube Pro",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=self.theme["accent"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            i1, text=f"Versiyon {VERSION}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w", pady=(6, 20))

        ctk.CTkLabel(
            i1,
            text="YouTube, Vimeo ve diğer platformlardan video ve ses indirmek için\n"
                 "geliştirilmiş modern, hızlı ve kullanıcı dostu bir araçtır.\n\n"
                 "📋 Kuyruk   •   ⏸ Duraklat/Devam   •   🎵 Format Seçimi\n"
                 "🌐 Proxy   •   ⏱ Hız Limiti   •   🧹 Otomatik Temizlik",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.theme["text_secondary"],
            justify="left"
        ).pack(anchor="w")

        ctk.CTkLabel(
            i1, text=f"© 2026  •  {AUTHOR}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_muted"]
        ).pack(anchor="w", pady=(25, 0))

    # ============================================================
    # KISAYOLLAR
    # ============================================================
    def _setup_shortcuts(self):
        self.bind("<Control-d>", lambda e: self._quick_analyze())
        self.bind("<Control-v>", lambda e: self._paste())
        self.bind("<Control-f>", lambda e: self._add_fav_from_url())
        self.bind("<Control-t>", lambda e: self._toggle_theme())
        self.bind("<Control-p>", lambda e: self._toggle_pause() if self.is_downloading else None)
        self.bind("<Control-s>", lambda e: self._stop_download() if self.is_downloading else None)
        self.bind("<space>", lambda e: self._toggle_pause() if self.is_downloading else None)
        self.bind("<Escape>", lambda e: self.focus_set())

    # ============================================================
    # SAYFA GEÇİŞ
    # ============================================================
    def show_page(self, pid: str):
        try:
            if self.current_page:
                self.pages[self.current_page].pack_forget()
                for k, b in self.nav_buttons.items():
                    b.configure(fg_color="transparent", text_color=self.theme["text_secondary"])

            self.current_page = pid
            self.pages[pid].pack(fill="both", expand=True)

            if pid in self.nav_buttons:
                self.nav_buttons[pid].configure(
                    fg_color=self.theme["accent_light"],
                    text_color=self.theme["accent"]
                )

            if pid == "history":
                self._refresh_history()
            elif pid == "favorites":
                self._refresh_favorites()
            elif pid == "queue":
                self._refresh_queue()
        except Exception:
            pass

    # ============================================================
    # TEMA
    # ============================================================
    def _toggle_theme(self):
        if self.is_downloading:
            messagebox.showwarning("Uyarı", "İndirme devam ederken tema değiştirilemez!")
            return

        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme = THEMES[self.current_theme]
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

            for p in list(self.pages.values()):
                p.destroy()
            self.pages = {}
            self._build_home_page()
            self._build_downloads_page()
            self._build_queue_page()
            self._build_history_page()
            self._build_favorites_page()
            self._build_settings_page()
            self._build_about_page()

            if self.current_page:
                self.show_page(self.current_page)

            self._update_ffmpeg_status()
        except Exception as e:
            print(f"Tema hatası: {e}")

    # ============================================================
    # DURUM
    # ============================================================
    def _set_status(self, text: str):
        self.status_label.configure(text=text[:80])

    # ============================================================
    # URL İŞLEMLERİ
    # ============================================================
    def _paste(self):
        try:
            txt = self.clipboard_get()
            if txt:
                self.header_url.delete(0, "end")
                self.header_url.insert(0, txt)
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, txt)
                self._on_url_change()
        except Exception:
            pass

    def _on_url_change(self):
        if self._resolve_timer:
            self.after_cancel(self._resolve_timer)
        self._resolve_timer = self.after(800, self._resolve_urls)

    def _on_batch_change(self, event=None):
        if self._resolve_timer:
            self.after_cancel(self._resolve_timer)
        self._resolve_timer = self.after(800, self._resolve_urls)
        self._update_count()

    def _update_count(self):
        try:
            txt = self.batch_text.get("1.0", "end-1c")
            n = len(extract_urls(txt))
            self.url_count_lbl.configure(text=f"{n} URL")
        except Exception:
            pass

    def _import_from_file(self):
        path = filedialog.askopenfilename(
            title="URL Dosyası Seç",
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.batch_text.delete("1.0", "end")
                    self.batch_text.insert("1.0", f.read())
                self._update_count()
                self._resolve_urls()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def _clear_batch(self):
        self.batch_text.delete("1.0", "end")
        self._update_count()
        self.url_titles.clear()
        self.playlists.clear()
        self.metadata.clear()
        self.resolved_urls.clear()
        self._clear_url_list()
        self.resolve_frame.pack_forget()
        self.start_frame.pack_forget()

    def _quick_analyze(self):
        url = self.header_url.get().strip()
        if url:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self.show_page("home")
            self._resolve_urls()
        else:
            messagebox.showwarning("Uyarı", "URL girin!")

    def _analyze_url(self):
        if not self.url_entry.get().strip():
            messagebox.showwarning("Uyarı", "URL girin!")
            return
        self._resolve_urls()

    # ============================================================
    # URL ÇÖZÜMLEME
    # ============================================================
    def _resolve_urls(self):
        raw = []
        txt = self.batch_text.get("1.0", "end-1c")
        raw.extend(extract_urls(txt))

        url = self.url_entry.get().strip()
        if url.startswith(("http://", "https://")):
            raw.append(url)

        if not raw:
            self._clear_url_list()
            self.resolve_frame.pack_forget()
            self.start_frame.pack_forget()
            self._set_status("Hazır")
            self.resolved_urls = []
            return

        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()
            self.resolver_thread.join(timeout=1)

        self.url_titles.clear()
        self.playlists.clear()
        self.metadata.clear()
        self.resolved_urls = []
        self._set_status("Analiz ediliyor...")

        self.resolve_frame.pack(fill="x", padx=28, pady=(0, 18))
        self.start_frame.pack_forget()
        self.resolve_lbl.configure(text=f"🔍 Çözümleniyor... (0/{len(raw)})", text_color=self.theme["accent"])
        self.resolve_bar.set(0)

        try:
            self.resolver_thread = TitleResolver(
                raw, callback=self._on_resolved,
                progress_cb=self._on_resolve_progress,
                skip_private=self.skip_private_var.get(),
                skip_members=self.skip_members_var.get()
            )
            self.resolver_thread.start()
        except Exception as e:
            self.resolve_frame.pack_forget()
            self._set_status(f"❌ {str(e)[:50]}")

    def _on_resolve_progress(self, cur, tot, msg):
        def update():
            try:
                self.resolve_bar.set(cur / tot)
                self.resolve_lbl.configure(text=f"🔍 Çözümleniyor... ({cur}/{tot})")
                self._set_status(f"⏳ {cur}/{tot}")
            except Exception:
                pass
        self.after(0, update)

    def _on_resolved(self, results, playlists, metadata):
        def update():
            try:
                self.url_titles = results
                self.playlists = playlists
                self.metadata = metadata
                self._clear_url_list()
                self.resolved_urls = list(results.keys())

                ok = 0
                priv = 0
                err = 0
                mem = 0

                for url, title in results.items():
                    frame = ctk.CTkFrame(
                        self.url_list, fg_color=self.theme["bg_input"], corner_radius=12
                    )
                    frame.pack(fill="x", padx=2, pady=4)
                    frame.grid_columnconfigure(0, weight=1)

                    icon = "🔄"
                    if title.startswith("🔒"):
                        icon = "🔒"
                        if "Üyelik" in title:
                            mem += 1
                        else:
                            priv += 1
                    elif title.startswith("❌") or title.startswith("⚠️"):
                        icon = "❌"
                        err += 1
                    else:
                        ok += 1

                    ctk.CTkLabel(
                        frame, text=f"{icon}  {title}",
                        font=ctk.CTkFont(family="Segoe UI", size=12),
                        text_color=self.theme["text_primary"],
                        anchor="w", justify="left", wraplength=850
                    ).grid(row=0, column=0, padx=14, pady=10, sticky="w")

                    is_fav = any(f.url == url for f in self.favorites)
                    ctk.CTkButton(
                        frame, text="★" if is_fav else "☆",
                        width=36, height=32, corner_radius=10,
                        font=ctk.CTkFont(size=18),
                        fg_color="transparent",
                        hover_color=self.theme["accent_light"],
                        text_color="#FFD700" if is_fav else self.theme["text_muted"],
                        command=lambda u=url: self._toggle_favorite(u)
                    ).grid(row=0, column=1, padx=10, pady=8)

                    self.url_widgets.append((url, title, frame))

                parts = [f"Toplam: {len(results)}", f"✅ {ok}"]
                if mem:
                    parts.append(f"🔒 {mem}")
                if priv:
                    parts.append(f"🔐 {priv}")
                if err:
                    parts.append(f"❌ {err}")
                self.url_count_lbl.configure(text="  |  ".join(parts))

                if ok > 0:
                    self.resolve_lbl.configure(
                        text=f"✅ {ok} URL hazır!",
                        text_color=self.theme["success"]
                    )
                    self.resolve_bar.set(1.0)
                    self.start_frame.pack(fill="x", padx=28, pady=(0, 22))
                    self.start_btn.configure(text=f"▶  {ok} URL'yi İndir")
                    self._set_status(f"✅ {ok} URL hazır")
                else:
                    self.resolve_lbl.configure(
                        text="⚠ Geçerli URL yok",
                        text_color=self.theme["error"]
                    )
                    self._set_status("⚠ Geçerli URL yok")

                self.after(3000, lambda: self.resolve_frame.pack_forget())

            except Exception as e:
                self._set_status(f"❌ {str(e)[:50]}")

        self.after(0, update)

    def _clear_url_list(self):
        for _, _, f in self.url_widgets:
            try:
                if f.winfo_exists():
                    f.destroy()
            except Exception:
                pass
        self.url_widgets.clear()

    def _toggle_favorite(self, url: str):
        if any(f.url == url for f in self.favorites):
            self.favorites = [f for f in self.favorites if f.url != url]
        else:
            self.favorites.append(Favorite(
                url=url,
                title=self.url_titles.get(url, url),
                date_added=datetime.now().strftime("%d.%m.%Y %H:%M")
            ))
        self._save_favorites()
        self._refresh_favorites()
        self.stat_fav_lbl.configure(text=f"⭐  Favori: {len(self.favorites)}")
        self._resolve_urls()

    def _add_fav_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "URL girin!")
            return
        if any(f.url == url for f in self.favorites):
            messagebox.showinfo("Bilgi", "Zaten favorilerde!")
            return

        title = url
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', url)
        except Exception:
            pass

        self.favorites.append(Favorite(
            url=url, title=title,
            date_added=datetime.now().strftime("%d.%m.%Y %H:%M")
        ))
        self._save_favorites()
        self._refresh_favorites()
        self.stat_fav_lbl.configure(text=f"⭐  Favori: {len(self.favorites)}")
        messagebox.showinfo("Başarılı", "Favorilere eklendi!")

    # ============================================================
    # FAVORİLER
    # ============================================================
    def _refresh_favorites(self):
        try:
            for w in self.favs_frame.winfo_children():
                w.destroy()

            if not self.favorites:
                ctk.CTkLabel(
                    self.favs_frame, text="⭐  Henüz favori yok",
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=self.theme["text_muted"]
                ).pack(pady=80)
                return

            for fav in self.favorites:
                card = self._card(self.favs_frame)
                card.pack(fill="x", pady=(0, 12))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=22, pady=18)

                ctk.CTkLabel(
                    inner, text=fav.title,
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                    text_color=self.theme["text_primary"],
                    anchor="w", justify="left", wraplength=750
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(8, 0))

                ctk.CTkLabel(
                    meta, text=f"📅 {fav.date_added}",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.theme["text_muted"]
                ).pack(side="left")

                bb = ctk.CTkFrame(inner, fg_color="transparent")
                bb.pack(side="right")

                self._btn(bb, "▶", lambda u=fav.url: self._use_fav(u), "secondary", 44, 34, 14).pack(side="left", padx=(0, 6))
                self._btn(bb, "✕", lambda f=fav: self._remove_fav(f), "danger", 44, 34, 14).pack(side="left")
        except Exception:
            pass

    def _use_fav(self, url):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self.header_url.delete(0, "end")
        self.header_url.insert(0, url)
        self.show_page("home")
        self._resolve_urls()

    def _remove_fav(self, fav):
        if fav in self.favorites:
            self.favorites.remove(fav)
            self._save_favorites()
            self._refresh_favorites()
            self.stat_fav_lbl.configure(text=f"⭐  Favori: {len(self.favorites)}")
            self._resolve_urls()

    def _export_favs(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([x.to_dict() for x in self.favorites], f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Başarılı", "Dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def _import_favs(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for d in json.load(f):
                        fav = Favorite.from_dict(d)
                        if not any(x.url == fav.url for x in self.favorites):
                            self.favorites.append(fav)
                self._save_favorites()
                self._refresh_favorites()
                self.stat_fav_lbl.configure(text=f"⭐  Favori: {len(self.favorites)}")
                messagebox.showinfo("Başarılı", "İçe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    # ============================================================
    # KUYRUK
    # ============================================================
    def _add_to_queue(self):
        if not self.resolved_urls:
            messagebox.showwarning("Uyarı", "Önce URL çözümleyin!")
            return

        quality = self.quality_var.get()
        fmt = self.format_var.get()
        added = 0

        for url in self.resolved_urls:
            if not any(q.url == url for q in self.queue):
                self.queue.append(QueueItem(
                    url=url,
                    title=self.url_titles.get(url, url),
                    quality=quality,
                    format=fmt,
                    added_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
                ))
                added += 1

        self._save_queue()
        self._refresh_queue()
        self._set_status(f"➕ {added} URL kuyruğa eklendi")
        messagebox.showinfo("Kuyruk", f"{added} URL kuyruğa eklendi.\n\nToplam: {len(self.queue)}")

    def _refresh_queue(self):
        try:
            for w in self.queue_frame.winfo_children():
                w.destroy()

            if not self.queue:
                ctk.CTkLabel(
                    self.queue_frame, text="📋  Kuyruk boş",
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=self.theme["text_muted"]
                ).pack(pady=80)
                return

            for i, item in enumerate(self.queue):
                card = self._card(self.queue_frame)
                card.pack(fill="x", pady=(0, 10))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=20, pady=14)

                ctk.CTkLabel(
                    inner, text=f"{i+1}.  {item.title}",
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color=self.theme["text_primary"],
                    anchor="w", justify="left", wraplength=700
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(6, 0))

                ctk.CTkLabel(
                    meta, text=f"🎯 {item.quality}  •  📦 {item.format}  •  🕐 {item.added_at}",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.theme["text_muted"]
                ).pack(side="left")

                self._btn(
                    inner, "🗑", lambda q=item: self._remove_from_queue(q),
                    "danger", 40, 28, 11
                ).pack(side="right")

        except Exception:
            pass

    def _remove_from_queue(self, item: QueueItem):
        if item in self.queue:
            self.queue.remove(item)
            self._save_queue()
            self._refresh_queue()

    def _clear_queue(self):
        if messagebox.askyesno("Onay", "Kuyruk temizlensin mi?"):
            self.queue.clear()
            self._save_queue()
            self._refresh_queue()

    def _start_queue(self):
        if not self.queue:
            messagebox.showwarning("Uyarı", "Kuyruk boş!")
            return
        if self.is_downloading:
            messagebox.showinfo("Bilgi", "Zaten indirme devam ediyor!")
            return

        urls = [q.url for q in self.queue]
        first = self.queue[0]
        self.quality_var.set(first.quality)
        self.format_var.set(first.format)
        self.resolved_urls = urls

        # Kuyruktaki title'ları url_titles'a ekle
        for q in self.queue:
            if q.url not in self.url_titles:
                self.url_titles[q.url] = q.title

        self.show_page("home")
        self._start_download()

    # ============================================================
    # İNDİRME
    # ============================================================
    def _start_download(self):
        if self.is_downloading:
            messagebox.showinfo("Bilgi", "Zaten indirme devam ediyor!")
            return

        urls = self.resolved_urls if self.resolved_urls else self._get_urls()
        if not urls:
            messagebox.showwarning("Uyarı", "URL yok!")
            return

        try:
            os.makedirs(self.settings.download_path, exist_ok=True)

            self.progress_card.pack(fill="x", pady=(0, 15))
            self.progress_bar.set(0)
            self.progress_info.configure(text="⏳ Hazırlanıyor...")
            self.speed_lbl.configure(text="")
            self._set_status("İndiriliyor...")
            self.start_frame.pack_forget()
            self.pause_btn.configure(text="⏸  Duraklat", fg_color="#F59E0B")
            self.stop_btn.configure(state="normal")
            self.update_idletasks()

            self.download_thread = DownloadThread(
                urls=urls,
                titles=self.url_titles,
                playlists=self.playlists,
                metadata=self.metadata,
                save_path=self.settings.download_path,
                quality=self.quality_var.get(),
                out_format=self.format_var.get(),
                concurrent=int(self.concurrent_var.get()) if self.concurrent_var.get().isdigit() else 3,
                ffmpeg=self.ffmpeg_path,
                skip_private=self.skip_private_var.get(),
                skip_members=self.skip_members_var.get(),
                playlist_folder=self.playlist_folder_var.get(),
                channel_folder=self.channel_folder_var.get(),
                video_folder=self.video_folder_var.get(),
                auto_cleanup=self.cleanup_var.get(),
                notify=self.notify_var.get(),
                proxy=self.proxy_var.get(),
                speed_limit=int(self.speed_var.get()) if self.speed_var.get().isdigit() else 0,
                normalize_audio=self.normalize_var.get(),
                sound_on_complete=self.sound_var.get(),
                file_template=self.template_var.get(),
                embed_thumbnail=self.embed_thumb_var.get(),
            )

            self.download_thread.cb_bar = self._on_bar
            self.download_thread.cb_speed = self._on_speed
            self.download_thread.cb_status = self._on_status
            self.download_thread.cb_error = self._on_error
            self.download_thread.cb_done = self._on_done
            self.download_thread.cb_item = self._on_item
            self.download_thread.cb_pause = self._on_pause_state

            self.download_thread.start()
            self.is_downloading = True
            self.is_paused = False

        except Exception as e:
            self.is_downloading = False
            messagebox.showerror("Hata", f"Başlatılamadı:\n{e}")

    def _get_urls(self) -> List[str]:
        urls = []
        u = self.url_entry.get().strip()
        if u:
            urls.append(u)
        urls.extend(extract_urls(self.batch_text.get("1.0", "end-1c")))
        return urls

    # ============================================================
    # DURAKLAT / DEVAM / DURDUR
    # ============================================================
    def _toggle_pause(self):
        if not self.download_thread or not self.is_downloading:
            return

        if self.download_thread.is_paused():
            self.download_thread.resume()
            self.is_paused = False
            self.pause_btn.configure(text="⏸  Duraklat", fg_color="#F59E0B")
            self._set_status("▶ Devam ediliyor")
            self.progress_info.configure(text="▶ İndirme devam ediyor...")
        else:
            self.download_thread.pause()
            self.is_paused = True
            self.pause_btn.configure(text="▶  Devam Et", fg_color="#10B981")
            self._set_status("⏸ Duraklatıldı")
            self.progress_info.configure(text="⏸ Duraklatıldı — devam etmek için butona basın")

    def _on_pause_state(self, paused: bool):
        def update():
            self.is_paused = paused
            if paused:
                self.pause_btn.configure(text="▶  Devam Et", fg_color="#10B981")
                self._set_status("⏸ Duraklatıldı")
            else:
                self.pause_btn.configure(text="⏸  Duraklat", fg_color="#F59E0B")
                self._set_status("▶ Devam ediliyor")
        self.after(0, update)

    def _stop_download(self):
        if not self.download_thread or not self.is_downloading:
            return
        if messagebox.askyesno("Durdur", "İndirmeyi tamamen durdurmak istiyor musunuz?\n\n(Geçici dosyalar temizlenecek)"):
            self.download_thread.stop()
            self.is_downloading = False
            self.is_paused = False
            self.progress_info.configure(text="⏹ Durduruldu")
            self._set_status("⏹ Durduruldu")
            self.pause_btn.configure(text="⏸  Duraklat", fg_color="#F59E0B")
            self.stop_btn.configure(state="disabled")

            def cleanup():
                TempCleaner.clean_folder(self.settings.download_path, recursive=True)
            threading.Thread(target=cleanup, daemon=True).start()

    # ============================================================
    # CALLBACKS
    # ============================================================
    def _on_bar(self, pct):
        self.after(0, lambda: self.progress_bar.set(pct / 100))

    def _on_speed(self, speed, eta):
        self.after(0, lambda: self.speed_lbl.configure(text=f"⚡ {speed}  •  ⏱ {eta}"))

    def _on_status(self, text):
        self.after(0, lambda: self.progress_info.configure(text=text[:100]))

    def _on_error(self, msg):
        pass

    def _on_item(self, item: DownloadItem):
        self.stats.total_downloads += 1
        self.stats.last_download = item.title

        self.history.append(item)
        self._save_history()
        self._save_stats()

        self.after(0, lambda: self.stat_dl_lbl.configure(
            text=f"📥  Toplam: {self.stats.total_downloads}"
        ))
        self.after(0, lambda: self.stat_last_lbl.configure(
            text=f"🕐  Son: {item.title[:40]}"
        ))

        if self.notify_var.get():
            try:
                notification.notify(
                    title=APP_NAME,
                    message=f"✅ {item.title[:50]}",
                    timeout=4
                )
            except Exception:
                pass

        if self.sound_var.get():
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                else:
                    print("\a")
            except Exception:
                pass

    def _on_done(self):
        def update():
            self.is_downloading = False
            self.is_paused = False
            self.progress_bar.set(1.0)
            self._set_status("✅ Tamamlandı")
            self.pause_btn.configure(text="⏸  Duraklat", fg_color="#F59E0B")
            self.stop_btn.configure(state="disabled")

            if self.resolved_urls:
                self.start_frame.pack(fill="x", padx=28, pady=(0, 22))

            if self.download_thread:
                c = self.download_thread.completed_count
                e = self.download_thread.error_count
                s = self.download_thread.skipped_count
                msg = f"✅ {c} indirildi"
                if s:
                    msg += f", ⏭ {s} atlandı"
                if e:
                    msg += f", ❌ {e} hata"
                self.progress_info.configure(text=msg)

            if self.cleanup_var.get():
                def final_cleanup():
                    TempCleaner.clean_folder(self.settings.download_path, recursive=True)
                threading.Thread(target=final_cleanup, daemon=True).start()

            self._refresh_history()
            self.after(3000, lambda: self.progress_bar.set(0))

        self.after(0, update)

    # ============================================================
    # GEÇMİŞ
    # ============================================================
    def _refresh_history(self):
        try:
            for w in self.history_frame.winfo_children():
                w.destroy()

            if not self.history:
                ctk.CTkLabel(
                    self.history_frame, text="📭  Geçmiş yok",
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=self.theme["text_muted"]
                ).pack(pady=80)
                return

            for item in reversed(self.history[-50:]):
                card = self._card(self.history_frame)
                card.pack(fill="x", pady=(0, 12))

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=22, pady=18)

                icon = "✅" if item.status == "completed" else "❌"

                ctk.CTkLabel(
                    inner, text=f"{icon}  {item.title}",
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                    text_color=self.theme["text_primary"],
                    anchor="w", justify="left", wraplength=750
                ).pack(anchor="w")

                meta = ctk.CTkFrame(inner, fg_color="transparent")
                meta.pack(fill="x", pady=(8, 0))

                info = f"📅 {item.date_added}  •  📂 {item.format}  •  {item.size or '—'}"
                if item.duration:
                    info += f"  •  ⏱ {item.duration}"
                if item.channel:
                    info += f"  •  📺 {item.channel[:25]}"

                ctk.CTkLabel(
                    meta, text=info,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=self.theme["text_muted"]
                ).pack(side="left")

                if item.file_path and os.path.exists(item.file_path):
                    self._btn(
                        inner, "📂 Aç",
                        lambda p=item.file_path: self._open_path(os.path.dirname(p)),
                        "secondary", 80, 32, 11
                    ).pack(side="right")
        except Exception:
            pass

    def _clear_history(self):
        if messagebox.askyesno("Onay", "Tüm geçmiş silinsin mi?"):
            self.history.clear()
            self._save_history()
            self._refresh_history()

    # ============================================================
    # AYARLAR
    # ============================================================
    def _change_path(self):
        path = filedialog.askdirectory(initialdir=self.settings.download_path)
        if path:
            self.settings.download_path = path
            self.path_lbl.configure(text=path)
            os.makedirs(path, exist_ok=True)
            self._save_settings()

    def _save_settings_ui(self):
        try:
            self.settings.default_quality = self.quality_var.get()
            self.settings.default_format = self.format_var.get()
            self.settings.concurrent_downloads = int(self.concurrent_var.get())
            self.settings.playlist_folder = self.playlist_folder_var.get()
            self.settings.channel_folder = self.channel_folder_var.get()
            self.settings.video_folder = self.video_folder_var.get()
            self.settings.skip_members_only = self.skip_members_var.get()
            self.settings.skip_private_videos = self.skip_private_var.get()
            self.settings.embed_thumbnail = self.embed_thumb_var.get()
            self.settings.notify_on_complete = self.notify_var.get()
            self.settings.auto_cleanup = self.cleanup_var.get()
            self.settings.proxy = self.proxy_var.get()
            self.settings.speed_limit = int(self.speed_var.get()) if self.speed_var.get().isdigit() else 0
            self.settings.normalize_audio = self.normalize_var.get()
            self.settings.sound_on_complete = self.sound_var.get()
            self.settings.file_template = self.template_var.get()
            self._save_settings()
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # ============================================================
    # DÖNÜŞTÜRÜCÜ
    # ============================================================
    def _open_converter(self):
        if self.converter_window and self.converter_window.winfo_exists():
            self.converter_window.lift()
            self.converter_window.focus_force()
            return
        self.converter_window = ConverterWindow(self, self.theme, self.ffmpeg_path)

    # ============================================================
    # YARDIMCI
    # ============================================================
    def _open_path(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _on_close(self):
        if self.is_downloading:
            if not messagebox.askyesno("Çıkış", "İndirme devam ediyor. Çıkmak istiyor musunuz?"):
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
            self._save_history()
            self._save_stats()
            self._save_queue()
        except Exception:
            pass
        self.destroy()


# ============================================================
# GİRİŞ
# ============================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try:
        app = NeoTubeApp()
        app.mainloop()
    except Exception as e:
        print(f"Başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        input("Enter'a basın...")