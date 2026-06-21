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
from tkinter import filedialog, messagebox
from tkinter import Tk, Label, ttk

# ============================================================
# 1. BAĞIMLILIK KONTROLÜ VE OTOMATİK KURULUM
# ============================================================
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])

def check_and_install_dependencies():
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
    root.geometry("400x150")
    root.configure(bg='#2b2b2b')
    lbl = Label(
        root,
        text=f"Eksik paketler: {', '.join(missing)}\nKurulum yapılıyor...",
        fg='white', bg='#2b2b2b', font=('Arial', 10)
    )
    lbl.pack(pady=20)
    progress = ttk.Progressbar(root, length=300, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()
    root.update()

    try:
        for pkg in missing:
            install_package(pkg)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        root.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        root.destroy()
        messagebox.showerror(
            "Kurulum Hatası",
            f"Paket kurulumu başarısız:\n{e}\n\n"
            "Lütfen elle yükleyin:\npip install customtkinter yt-dlp plyer"
        )
        sys.exit(1)

check_and_install_dependencies()

import customtkinter as ctk
import yt_dlp
from plyer import notification
from yt_dlp.utils import sanitize_filename

# ============================================================
# 2. FFMPEG OTOMATİK BULMA VE İNDİRME
# ============================================================
def find_system_ffmpeg():
    """Sistemde yüklü FFmpeg'i bul (PATH + yaygın dizinler)"""
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path

    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
        os.path.expanduser(r"~\AppData\Local\ffmpeg\bin\ffmpeg.exe"),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path

    ffmpeg_home = os.environ.get('FFMPEG_HOME', '')
    if ffmpeg_home:
        candidate = os.path.join(ffmpeg_home, 'bin', 'ffmpeg.exe')
        if os.path.isfile(candidate):
            return candidate

    return None

def get_ffmpeg_path():
    """FFmpeg'i bul veya indir; bulunamazsa None döner."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_dir = os.path.join(base_dir, "ffmpeg", "bin")
    ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")

    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe

    system_ffmpeg = find_system_ffmpeg()
    if system_ffmpeg:
        print(f"✅ Sistem FFmpeg'i bulundu: {system_ffmpeg}")
        return system_ffmpeg

    # İnternet bağlantısı kontrolü
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
    except OSError:
        messagebox.showerror(
            "Bağlantı Hatası",
            "FFmpeg indirilemedi. Lütfen internet bağlantınızı kontrol edin."
        )
        return None

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(base_dir, "ffmpeg_temp.zip")

    win = ctk.CTkToplevel()
    win.title("NeoTube Kurulumu")
    win.geometry("420x160")
    win.attributes('-topmost', True)
    win.resizable(False, False)

    ctk.CTkLabel(
        win,
        text="FFmpeg indiriliyor, lütfen bekleyin...\n(Bu işlem birkaç dakika sürebilir)",
        font=ctk.CTkFont(size=12)
    ).pack(pady=20)

    prog = ctk.CTkProgressBar(win, width=320)
    prog.pack(pady=10)
    prog.set(0)
    win.update()

    def report_hook(block_num, block_size, total_size):
        if total_size > 0:
            pct = min(1.0, block_num * block_size / total_size)
            try:
                prog.set(pct)
                win.update()
            except Exception:
                pass

    try:
        urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            extracted_member = None
            for member in zf.namelist():
                if member.endswith("ffmpeg.exe"):
                    zf.extract(member, base_dir)
                    extracted_member = os.path.join(base_dir, member)
                    break

        if extracted_member and os.path.isfile(extracted_member):
            os.makedirs(ffmpeg_dir, exist_ok=True)
            shutil.move(extracted_member, ffmpeg_exe)

        # Geçici zip ve boş klasörleri temizle
        if os.path.exists(zip_path):
            os.remove(zip_path)

        win.destroy()
        return ffmpeg_exe if os.path.isfile(ffmpeg_exe) else None

    except Exception as e:
        try:
            win.destroy()
        except Exception:
            pass
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                pass
        messagebox.showerror(
            "FFmpeg Hatası",
            f"FFmpeg indirilemedi:\n{e}\n\n"
            "Lütfen https://ffmpeg.org/ adresinden manuel olarak indirip\n"
            f"{ffmpeg_exe} konumuna kopyalayın veya PATH'e ekleyin."
        )
        return None

# ============================================================
# 3. YARDIMCI FONKSİYONLAR
# ============================================================
def is_private_video(info: dict) -> bool:
    """Videonun özel olup olmadığını kontrol et."""
    if info.get('availability') == 'private':
        return True
    if info.get('live_status') == 'is_upcoming' and info.get('release_timestamp'):
        return True
    return False

def format_duration(seconds) -> str:
    """Saniyeyi MM:SS formatına dönüştür."""
    try:
        secs = int(seconds)
        m, s = divmod(secs, 60)
        return f"{m}:{s:02d}"
    except (TypeError, ValueError):
        return "??"

def clean_title(title: str) -> str:
    """Emoji öneklerini temizler."""
    for prefix in ("📁 ", "🎬 ", "⚠️ ", "❌ ", "🔒 "):
        title = title.replace(prefix, "")
    return sanitize_filename(title, restricted=False).replace('_', '-')

def parse_speed_limit(spd_str: str):
    """Hız limitini MB/s olarak çözümle. Limitsiz ise None döner."""
    if spd_str.startswith("0"):
        return None
    try:
        return int(spd_str.split()[0])
    except (ValueError, IndexError):
        return None

# ============================================================
# 4. TitleResolverThread
# ============================================================
class TitleResolverThread(threading.Thread):
    def __init__(self, urls, callback, progress_callback=None):
        super().__init__(daemon=True)
        self.urls = urls
        self.callback = callback
        self.progress_callback = progress_callback
        self._stop_flag = False

    def run(self):
        results = {}
        ydl_opts = {
            'quiet': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'socket_timeout': 30,
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
                        results[url] = f"⚠️ {url} (Çözümlenemedi)"
                        continue

                    if is_private_video(info):
                        results[url] = f"🔒 {url} (Özel video - atlandı)"
                        continue

                    title = info.get("title") or url

                    if 'entries' in info:
                        entries = info.get('entries') or []
                        count = len(list(entries))
                        results[url] = f"📁 {title} (Playlist - {count} video)"
                    else:
                        dur = info.get('duration')
                        if dur:
                            results[url] = f"🎬 {title} ({format_duration(dur)})"
                        else:
                            results[url] = f"🎬 {title}"

            except Exception as exc:
                err = str(exc).lower()
                if "private" in err or "sign in" in err:
                    results[url] = f"🔒 {url} (Özel video - erişim yok)"
                else:
                    results[url] = f"❌ {url} (Hata: {str(exc)[:40]})"

        self.callback(results)

    def stop(self):
        self._stop_flag = True

# ============================================================
# 5. DownloadThread
# ============================================================
FORMAT_MAP = {
    "best":         "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p":        "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "720p":         "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
    "480p":         "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
    "MP3 (128k)":   "bestaudio/best",
    "MP3 (320k)":   "bestaudio/best",
    "video_only":   "bestvideo[ext=mp4]",
}

class DownloadThread(threading.Thread):
    def __init__(self, urls, titles, save_path, fmt="best",
                 concurrent=3, proxy=None, speed_limit=None, ffmpeg=None):
        super().__init__(daemon=True)
        self.urls = urls
        self.titles = titles
        self.save_path = save_path
        self.fmt = fmt
        self.concurrent = concurrent if ffmpeg else 1
        self.proxy = proxy
        self.speed_limit = speed_limit  # MB/s (int) veya None
        self.ffmpeg = ffmpeg

        self._pause = False
        self._stop = False
        self.idx = 0
        self.total = len(urls)
        self.start_time = None

        # Geri çağırma fonksiyonları
        self.cb_progress = None   # (str) -> None
        self.cb_status   = None   # (url, status_str, title) -> None
        self.cb_done     = None   # () -> None
        self.cb_current  = None   # (url, clean_title) -> None
        self.cb_bar      = None   # (int 0-100) -> None
        self.cb_error    = None   # (str) -> None
        self.cb_speed    = None   # (speed_str, eta_str) -> None
        self.cb_queue    = None   # (cur, total, title) -> None

    # ---- yardımcı: progress hook ----
    def _make_hook(self):
        def hook(d):
            if self._stop:
                raise yt_dlp.utils.DownloadCancelled()
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
            elif d['status'] == 'finished':
                if self.cb_bar:
                    self.cb_bar(100)
        return hook

    # ---- yardımcı: ydl seçenekleri ----
    def _build_opts(self, folder, outtmpl, selector, post_processors):
        opts = {
            "outtmpl":                       outtmpl,
            "format":                        selector,
            "quiet":                         True,
            "no_warnings":                   True,
            "ignoreerrors":                  True,
            "progress_hooks":                [self._make_hook()],
            "noplaylist":                    False,
            "continuedl":                    True,
            "retries":                       10,
            "fragment_retries":              10,
            "concurrent_fragment_downloads": self.concurrent,
            "postprocessors":                post_processors,
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "verbose":    False,
            "no_progress": True,
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        if self.speed_limit:
            opts["ratelimit"] = int(self.speed_limit * 1024 * 1024)
        if self.ffmpeg:
            opts["ffmpeg_location"] = self.ffmpeg
        return opts

    def run(self):
        self.start_time = time.time()

        for i, url in enumerate(self.urls, start=1):
            self.idx = i
            if self._stop:
                break

            # Duraklama döngüsü
            while self._pause and not self._stop:
                time.sleep(0.2)
            if self._stop:
                break

            raw_title = self.titles.get(url, f"URL {i}")

            # Özel veya hatalı videolar
            if raw_title.startswith("🔒"):
                if self.cb_status:
                    self.cb_status(url, "private", raw_title)
                continue
            if raw_title.startswith("❌"):
                if self.cb_status:
                    self.cb_status(url, "error", raw_title)
                continue

            clean = clean_title(raw_title)

            if self.cb_current:
                self.cb_current(url, clean)
            if self.cb_queue:
                self.cb_queue(i, self.total, clean)
            if self.cb_progress:
                self.cb_progress(f"📥 {i}/{self.total} - İndiriliyor: {clean}")

            # Klasör
            folder = os.path.join(self.save_path, clean)
            os.makedirs(folder, exist_ok=True)

            # Format seçimi
            fmt = self.fmt
            selector = FORMAT_MAP.get(fmt, FORMAT_MAP["best"])
            post_processors = []

            is_audio = fmt in ("MP3 (128k)", "MP3 (320k)")
            if is_audio and self.ffmpeg:
                quality = "0" if fmt == "MP3 (320k)" else "5"
                post_processors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }]
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")

            opts = self._build_opts(folder, outtmpl, selector, post_processors)

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                if self.cb_status:
                    self.cb_status(url, "completed", clean)

            except yt_dlp.utils.DownloadCancelled:
                break

            except Exception as exc:
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
                    if self.cb_error:
                        self.cb_error(f"Hata ({clean}):\n{str(exc)[:120]}")

                if self.cb_progress:
                    self.cb_progress(log)
                if self.cb_status:
                    self.cb_status(url, status, clean)

        if self.cb_done:
            self.cb_done()

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def stop(self):
        self._stop = True

# ============================================================
# 6. URLItem - Liste satırı bileşeni
# ============================================================
STATUS_COLORS = {
    "downloading": "#ffcc00",
    "completed":   "#28a745",
    "skipped":     "#007bff",
    "private":     "#6c757d",
    "error":       "#dc3545",
    "waiting":     ("gray70", "gray25"),
}
STATUS_ICONS = {
    "downloading": "⏬",
    "completed":   "✅",
    "skipped":     "⏭️",
    "private":     "🔒",
    "error":       "❌",
    "waiting":     "⏳",
}

class URLItem(ctk.CTkFrame):
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
        """Widget hâlâ geçerliyse after_idle ile çalıştır."""
        try:
            if self.winfo_exists():
                self.after_idle(fn)
        except Exception:
            pass

    def set_status(self, status: str):
        color = STATUS_COLORS.get(status, ("gray70", "gray25"))
        icon  = STATUS_ICONS.get(status, "⏳")

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
# 7. ConverterWindow
# ============================================================
AUDIO_CODEC_MAP = {
    "mp3":  ["-acodec", "libmp3lame", "-ab", "192k"],
    "wma":  ["-acodec", "wmav2", "-ab", "192k"],
    "aac":  ["-acodec", "aac", "-b:a", "192k"],
    "flac": ["-acodec", "flac", "-compression_level", "5"],
    "ogg":  ["-acodec", "libvorbis", "-qscale:a", "5"],
    "m4a":  ["-acodec", "aac", "-b:a", "192k", "-f", "ipod"],
    "wav":  ["-acodec", "pcm_s16le"],
}

class ConverterWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("NeoTube Dönüştürücü")
        self.geometry("820x680")
        self.minsize(700, 560)
        self.resizable(True, True)

        self.master_app = master
        self.files: list[str] = []
        self.out_fmt = ctk.StringVar(value="mp3")
        self.out_dir = ""
        self.trim_silence = ctk.BooleanVar(value=False)
        self.file_widgets: list[tuple] = []  # (label_widget, filepath)

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
        self.grid_rowconfigure(5, weight=1)

        # Başlık
        ctk.CTkLabel(
            self, text="🔄 Medya Dönüştürücü",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

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
        ctk.CTkButton(btn_row, text="📁 Dosya",  width=90, command=self._add_files).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="📂 Klasör", width=90, command=self._add_folder).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑️ Temizle", width=80,
                      fg_color="gray", command=self._clear).pack(side="left", padx=2)

        # Format & Sessizlik
        fmt_row = ctk.CTkFrame(self)
        fmt_row.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(fmt_row, text="🎵 Format:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.format_menu = ctk.CTkOptionMenu(
            fmt_row,
            values=["mp3", "wma", "aac", "flac", "ogg", "m4a", "wav", "WAV (22050 Hz)"],
            variable=self.out_fmt, width=150
        )
        self.format_menu.pack(side="left", padx=10)

        ctk.CTkCheckBox(
            fmt_row, text="✂️ Sessizlikleri kes (deneysel)",
            variable=self.trim_silence
        ).pack(side="left", padx=20)

        # Çıktı klasörü
        out_row = ctk.CTkFrame(self)
        out_row.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        out_row.grid_columnconfigure(0, weight=1)

        self.out_lbl = ctk.CTkLabel(
            out_row, text="Varsayılan: Kaynak ile aynı klasör", height=30,
            fg_color=("gray75", "gray25"), corner_radius=5, anchor="w"
        )
        self.out_lbl.grid(row=0, column=0, sticky="ew", padx=(8, 8), pady=5)
        ctk.CTkButton(out_row, text="📁 Değiştir", width=110,
                      command=self._pick_out).grid(row=0, column=1, padx=8, pady=5)

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

    def _build_ffmpeg_cmd(self, input_path: str, output_path: str, fmt: str) -> list[str]:
        """FFmpeg komut listesini oluştur."""
        is_wav22050 = (fmt == "WAV (22050 Hz)")
        ffmpeg = self.ffmpeg_path

        cmd = [ffmpeg, "-i", input_path, "-y"]

        if is_wav22050:
            cmd += ["-acodec", "pcm_s16le", "-ac", "1", "-ar", "22050"]
        else:
            cmd += ["-vn"]
            codec_args = AUDIO_CODEC_MAP.get(fmt, ["-acodec", "copy"])
            cmd += codec_args

        # Sessizlik filtresi
        if self.trim_silence.get():
            cmd += ["-af", "silenceremove=start_periods=1:start_threshold=0.1:start_duration=0.1"
                           ":stop_periods=-1:stop_threshold=0.1:stop_duration=0.1"]

        cmd.append(output_path)
        return cmd

    def _convert_worker(self):
        fmt = self.out_fmt.get()
        is_wav22050 = (fmt == "WAV (22050 Hz)")
        ext = "wav" if is_wav22050 else fmt
        total = len(self.file_widgets)

        for i, (slbl, path) in enumerate(self.file_widgets):
            self.after(0, lambda s=slbl: s.configure(text="🔄 dönüşüyor", fg_color="#ffcc00"))

            base_name  = os.path.splitext(os.path.basename(path))[0]
            target_dir = self.out_dir or os.path.dirname(path)
            out_path   = os.path.join(target_dir, f"{base_name}.{ext}")

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
                        cmd_nf = self._build_ffmpeg_cmd.__func__(self, path, out_path, fmt)
                        # trim_silence geçici olarak False
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
# 8. NeoTubeApp - Ana uygulama
# ============================================================
class NeoTubeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NeoTube Pro v4.0 — İndirici & Dönüştürücü")
        self.geometry("1500x900")
        self.minsize(1200, 700)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Uygulama durumu
        self.url_titles:  dict[str, str]  = {}
        self.url_items:   list[URLItem]   = []
        self.download_thread: DownloadThread | None    = None
        self.resolver_thread: TitleResolverThread | None = None
        self.download_folder = ""
        self.is_downloading  = False
        self.favorites: set[str]   = set()
        self.history:   list[dict] = []
        self._resolve_id = None

        self.ffmpeg_path = get_ffmpeg_path()

        self._build_ui()
        self.after(500, self._check_ffmpeg_ui)

    def _on_close(self):
        if self.is_downloading:
            if not messagebox.askyesno("Çıkış", "İndirme devam ediyor. Çıkmak istiyor musunuz?"):
                return
            if self.download_thread:
                self.download_thread.stop()
        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()
        self.destroy()

    # ============================================================
    # UI inşa
    # ============================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # ---- Başlık ----
        top = ctk.CTkFrame(self, fg_color="transparent", height=60)
        top.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="🎬 NeoTube Pro",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#ffcc00"
        ).grid(row=0, column=0, sticky="w")

        self.req_lbl = ctk.CTkLabel(
            top, text="🔍 Kontrol ediliyor...",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.req_lbl.grid(row=0, column=1, sticky="e")

        # ---- Sol panel ----
        left = ctk.CTkFrame(self)
        left.grid(row=1, column=0, rowspan=6, padx=(20, 10), pady=10, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(4, weight=1)

        # URL girişi
        inp = ctk.CTkFrame(left)
        inp.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        inp.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inp, text="📋 URL'ler (her satır bir URL):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        self.url_box = ctk.CTkTextbox(inp, height=100)
        self.url_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.url_box.bind("<<Modified>>", self._on_url_modified)

        self.clr_btn = ctk.CTkButton(
            inp, text="🗑️ Temizle", width=100, fg_color="#6c757d",
            command=self.clear_all
        )
        self.clr_btn.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="n")

        # Ayarlar satırı
        setf = ctk.CTkFrame(left)
        setf.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        for c in range(6):
            setf.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(setf, text="📊 Kalite:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.fmt_var = ctk.StringVar(value="best")
        self.fmt_menu = ctk.CTkOptionMenu(
            setf,
            values=["best", "1080p", "720p", "480p", "MP3 (128k)", "MP3 (320k)", "video_only"],
            variable=self.fmt_var, width=120
        )
        self.fmt_menu.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(setf, text="⚡ Eşzamanlı:").grid(row=0, column=2, padx=5, pady=10, sticky="w")
        self.conc_var = ctk.IntVar(value=3)
        ctk.CTkEntry(setf, width=45, textvariable=self.conc_var).grid(
            row=0, column=3, padx=5, pady=10, sticky="w"
        )

        ctk.CTkLabel(setf, text="🚀 Hız Limiti:").grid(row=0, column=4, padx=5, pady=10, sticky="w")
        self.spd_var = ctk.StringVar(value="0 (Sınırsız)")
        ctk.CTkOptionMenu(
            setf,
            values=["0 (Sınırsız)", "1 MB/s", "5 MB/s", "10 MB/s", "50 MB/s"],
            variable=self.spd_var, width=110
        ).grid(row=0, column=5, padx=5, pady=10, sticky="w")

        # Klasör seçimi
        fold = ctk.CTkFrame(left)
        fold.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        fold.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fold, text="📂 Klasör:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )
        self.fold_lbl = ctk.CTkLabel(
            fold, text="Henüz seçilmedi", height=32,
            fg_color=("gray75", "gray25"), corner_radius=5, anchor="w"
        )
        self.fold_lbl.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        ctk.CTkButton(
            fold, text="📁 Gözat", width=100,
            fg_color="#ffcc00", text_color="black",
            command=self._pick_folder
        ).grid(row=0, column=2, padx=10, pady=8)

        # Liste başlığı
        lh = ctk.CTkFrame(left, fg_color="transparent")
        lh.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")

        ctk.CTkLabel(lh, text="📋 URL Listesi", font=ctk.CTkFont(size=15, weight="bold")).pack(
            side="left", padx=10, pady=5
        )
        self.stat_lbl = ctk.CTkLabel(lh, text="", font=ctk.CTkFont(size=12))
        self.stat_lbl.pack(side="left", padx=20)

        # Kaydırılabilir URL listesi
        self.url_frame = ctk.CTkScrollableFrame(left, corner_radius=8)
        self.url_frame.grid(row=4, column=0, padx=10, pady=8, sticky="nsew")

        # İlerleme & hız
        stf = ctk.CTkFrame(left)
        stf.grid(row=5, column=0, padx=10, pady=8, sticky="ew")
        stf.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            stf, text="⏸️ Hazır",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00ffcc"
        )
        self.status_lbl.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        self.spd_lbl = ctk.CTkLabel(stf, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.spd_lbl.grid(row=0, column=1, padx=10, pady=(8, 4), sticky="e")

        self.eta_lbl = ctk.CTkLabel(stf, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.eta_lbl.grid(row=0, column=2, padx=10, pady=(8, 4), sticky="e")

        self.pbar = ctk.CTkProgressBar(stf)
        self.pbar.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.pbar.set(0)

        # Kontrol butonları
        btnf = ctk.CTkFrame(left)
        btnf.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        for c in range(4):
            btnf.grid_columnconfigure(c, weight=1)

        self.dl_btn = ctk.CTkButton(
            btnf, text="▶️ Başlat", fg_color="#28a745", height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_download
        )
        self.dl_btn.grid(row=0, column=0, padx=3, pady=6, sticky="ew")

        self.ps_btn = ctk.CTkButton(
            btnf, text="⏸️ Duraklat", fg_color="#dc3545", height=42,
            state="disabled", command=self.pause_download
        )
        self.ps_btn.grid(row=0, column=1, padx=3, pady=6, sticky="ew")

        self.rs_btn = ctk.CTkButton(
            btnf, text="▶️ Devam", fg_color="#007bff", height=42,
            state="disabled", command=self.resume_download
        )
        self.rs_btn.grid(row=0, column=2, padx=3, pady=6, sticky="ew")

        self.sp_btn = ctk.CTkButton(
            btnf, text="⏹️ Durdur", fg_color="#6c757d", height=42,
            state="disabled", command=self.stop_download
        )
        self.sp_btn.grid(row=0, column=3, padx=3, pady=6, sticky="ew")

        # ---- Sağ panel ----
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, rowspan=5, padx=(10, 20), pady=10, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        # Kuyruk
        qf = ctk.CTkFrame(right)
        qf.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        ctk.CTkLabel(qf, text="📋 Kuyruk", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6, 0))
        self.q_frame = ctk.CTkScrollableFrame(qf, height=150)
        self.q_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Favoriler
        ff = ctk.CTkFrame(right)
        ff.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(ff, text="⭐ Favoriler", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6, 0))
        self.fav_frame = ctk.CTkScrollableFrame(ff, height=110)
        self.fav_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # İstatistikler
        sf = ctk.CTkFrame(right)
        sf.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(sf, text="📊 İstatistikler", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6, 0))
        self.stat_box = ctk.CTkTextbox(sf, height=110, state="disabled")
        self.stat_box.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(
            right, text="🔄 Dönüştürücüyü Aç",
            fg_color="#ff8c00", height=38,
            command=self.open_converter
        ).grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # ---- Alt bilgi ----
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=7, column=0, columnspan=2, padx=20, pady=6, sticky="ew")

        ctk.CTkLabel(
            bot,
            text="© 2026 NeoTube Pro v4.0 | Geliştirici: Caner Ergün",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(side="left", padx=5)

        social = [
            ("LinkedIn",  "#0A66C2", "https://linkedin.com/in/devseu/"),
            ("GitHub",    "#333333", "https://github.com/canerergun"),
            ("Instagram", "#C13584", "https://instagram.com/devseu"),
            ("Twitch",    "#9146FF", "https://twitch.tv/devseu"),
        ]
        for name, color, url in reversed(social):
            ctk.CTkButton(
                bot, text=name, fg_color=color, hover_color=color,
                width=78, height=26,
                command=lambda u=url: webbrowser.open(u)
            ).pack(side="right", padx=2)

        self._refresh_fav()
        self._refresh_stats()

    # ============================================================
    # FFmpeg durum göstergesi
    # ============================================================
    def _check_ffmpeg_ui(self):
        ok = bool(self.ffmpeg_path and os.path.isfile(self.ffmpeg_path))
        if ok:
            self.req_lbl.configure(text=f"✅ FFmpeg Hazır → {self.ffmpeg_path}")
        else:
            self.req_lbl.configure(text="❌ FFmpeg bulunamadı (MP3 & birleştirme çalışmaz)")
            safe_values = ["best", "720p", "480p", "video_only"]
            self.fmt_menu.configure(values=safe_values)
            if self.fmt_var.get() not in safe_values:
                self.fmt_var.set("best")

    # ============================================================
    # URL Çözümleme
    # ============================================================
    def _on_url_modified(self, _event=None):
        self.url_box.edit_modified(False)
        if self._resolve_id:
            self.after_cancel(self._resolve_id)
        self._resolve_id = self.after(800, self._resolve)

    def _resolve(self):
        self._resolve_id = None
        raw = [
            u.strip()
            for u in self.url_box.get("1.0", "end-1c").splitlines()
            if u.strip()
        ]
        if not raw:
            self._clear_url_list()
            return

        # Önceki çözümleyiciyi durdur
        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()
            self.resolver_thread.join(timeout=1)

        self.url_titles.clear()
        self.status_lbl.configure(text="⏳ URL'ler çözümleniyor...")

        self.resolver_thread = TitleResolverThread(
            raw,
            callback=self._on_resolved,
            progress_callback=self._on_resolve_progress
        )
        self.resolver_thread.start()

    def _on_resolve_progress(self, cur: int, tot: int, msg: str):
        self.after(0, lambda: self.status_lbl.configure(text=f"⏳ {msg} ({cur}/{tot})"))

    def _on_resolved(self, results: dict):
        def update():
            self.url_titles = results
            self._clear_url_list()
            self.url_items.clear()

            ok_count      = 0
            private_count = 0
            error_count   = 0

            for idx, (url, title) in enumerate(results.items(), 1):
                item = URLItem(self.url_frame, idx, title, url)
                item.pack(fill="x", padx=5, pady=2)

                if url in self.favorites:
                    item.set_fav(True)

                # Çift tıkla favori ekle/çıkar
                item.bind("<Double-Button-1>", lambda _e, u=url: self._toggle_fav(u))

                if title.startswith("🔒"):
                    item.set_status("private")
                    private_count += 1
                elif title.startswith("❌"):
                    item.set_status("error")
                    error_count += 1
                elif title.startswith("⚠️"):
                    item.set_status("skipped")
                    error_count += 1
                else:
                    item.set_status("waiting")
                    ok_count += 1

                self.url_items.append(item)

            parts = [f"Toplam: {len(results)}", f"Hazır: {ok_count}"]
            if private_count:
                parts.append(f"Özel: {private_count}")
            if error_count:
                parts.append(f"Hatalı: {error_count}")
            self.stat_lbl.configure(text=" | ".join(parts))
            self.status_lbl.configure(text=f"✅ {ok_count} URL hazır.")
            self._refresh_stats()

        self.after(0, update)

    def _clear_url_list(self):
        for item in self.url_items:
            try:
                if item.winfo_exists():
                    item.destroy()
            except Exception:
                pass
        self.url_items.clear()

        for widget in self.url_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def clear_all(self):
        self.url_box.delete("1.0", "end")
        self.url_titles.clear()
        self._clear_url_list()
        self.stat_lbl.configure(text="")
        self.status_lbl.configure(text="⏸️ Hazır")
        self.pbar.set(0)

    # ============================================================
    # Klasör
    # ============================================================
    def _pick_folder(self):
        d = filedialog.askdirectory(title="İndirme klasörü seç")
        if d:
            self.download_folder = d
            self.fold_lbl.configure(text=d, text_color="white")

    # ============================================================
    # Favoriler
    # ============================================================
    def _toggle_fav(self, url: str):
        if url in self.favorites:
            self.favorites.discard(url)
        else:
            self.favorites.add(url)

        for i, (u, _) in enumerate(self.url_titles.items()):
            if u == url and i < len(self.url_items):
                it = self.url_items[i]
                if it.winfo_exists():
                    it.set_fav(url in self.favorites)
                break

        self._refresh_fav()
        self._refresh_stats()

    def _refresh_fav(self):
        for w in self.fav_frame.winfo_children():
            w.destroy()

        for url in self.favorites:
            fr = ctk.CTkFrame(self.fav_frame)
            fr.pack(fill="x", padx=2, pady=1)
            lbl = ctk.CTkLabel(
                fr, text=f"★ {url[:48]}",
                anchor="w", fg_color=("gray60", "gray30"),
                corner_radius=3, height=22
            )
            lbl.pack(fill="x", padx=2, pady=1)
            lbl.bind("<Button-1>", lambda _e, u=url: self._add_fav_url(u))

    def _add_fav_url(self, url: str):
        current = self.url_box.get("1.0", "end-1c").strip()
        self.url_box.insert("end", f"\n{url}" if current else url)

    # ============================================================
    # İstatistikler
    # ============================================================
    def _refresh_stats(self):
        lines = [
            "Bu Oturum:",
            f"📥 İndirilen : {len(self.history)}",
            f"⭐ Favori   : {len(self.favorites)}",
        ]
        if self.history:
            last = self.history[-1].get('title', '')[:32]
            lines += ["", "Son İndirme:", last]

        self.stat_box.configure(state="normal")
        self.stat_box.delete("1.0", "end")
        self.stat_box.insert("1.0", "\n".join(lines))
        self.stat_box.configure(state="disabled")

    # ============================================================
    # Kuyruk güncelleme
    # ============================================================
    def _update_queue(self, cur: int, tot: int, title: str):
        def update():
            for w in self.q_frame.winfo_children():
                w.destroy()
            for i in range(cur, min(tot + 1, cur + 8)):  # En fazla 8 satır göster
                label_text = f"{'▶ ' if i == cur else '  '}{i}. {title if i == cur else 'Sırada...'}"
                fr = ctk.CTkFrame(self.q_frame)
                fr.pack(fill="x", padx=2, pady=1)
                ctk.CTkLabel(
                    fr, text=label_text, anchor="w",
                    fg_color=("#ffcc00", "#806600") if i == cur else ("gray60", "gray30"),
                    text_color="black" if i == cur else ("white", "white"),
                    corner_radius=3
                ).pack(fill="x", padx=2, pady=1)
        self.after(0, update)

    # ============================================================
    # İndirme yönetimi
    # ============================================================
    def start_download(self):
        # Çözümleme sürüyorsa beklet
        if self.resolver_thread and self.resolver_thread.is_alive():
            messagebox.showinfo("Bilgi", "URL'ler çözümleniyor, lütfen bekleyin.")
            return

        if not self.url_titles:
            messagebox.showwarning("Uyarı", "Lütfen URL ekleyin ve çözümlenmesini bekleyin.")
            return

        if not self.download_folder:
            messagebox.showwarning("Uyarı", "Lütfen indirme klasörü seçin.")
            return

        if self.is_downloading:
            messagebox.showinfo("Bilgi", "İndirme zaten devam ediyor.")
            return

        # Geçerli URL'leri filtrele
        valid_urls = [
            url for url, title in self.url_titles.items()
            if not title.startswith(("🔒", "❌", "⚠️"))
        ]
        if not valid_urls:
            messagebox.showinfo("Bilgi", "İndirilecek geçerli video bulunamadı.\n"
                                         "(Özel veya hatalı videolar atlanır.)")
            return

        # FFmpeg gerekliliği kontrolü
        fmt = self.fmt_var.get()
        needs_ffmpeg = fmt.startswith("MP3") or fmt in ("best", "1080p")
        if needs_ffmpeg and (not self.ffmpeg_path or not os.path.isfile(self.ffmpeg_path)):
            if not messagebox.askyesno(
                "FFmpeg Yok",
                f"'{fmt}' kalitesi için FFmpeg gereklidir.\n"
                "FFmpeg olmadan devam etmek ister misiniz? (Kalite düşebilir)"
            ):
                return

        # UI kilitle
        self.is_downloading = True
        self.url_box.configure(state="disabled")
        self.dl_btn.configure(state="disabled")
        self.ps_btn.configure(state="normal")
        self.sp_btn.configure(state="normal")
        self.clr_btn.configure(state="disabled")
        self.pbar.set(0)
        self.spd_lbl.configure(text="")
        self.eta_lbl.configure(text="")

        # Tüm öğeleri "waiting" yap
        for item in self.url_items:
            if item.winfo_exists():
                item.set_status("waiting")

        # Özel videoları hemen işaretle
        for url, title in self.url_titles.items():
            if title.startswith("🔒"):
                self._set_url_status(url, "private", title)

        speed_limit = parse_speed_limit(self.spd_var.get())

        self.download_thread = DownloadThread(
            urls=valid_urls,
            titles=self.url_titles,
            save_path=self.download_folder,
            fmt=fmt,
            concurrent=self.conc_var.get(),
            proxy=None,
            speed_limit=speed_limit,
            ffmpeg=self.ffmpeg_path,
        )

        # Geri çağırmaları bağla
        self.download_thread.cb_progress = lambda m: self.after(
            0, lambda msg=m: self.status_lbl.configure(text=msg)
        )
        self.download_thread.cb_bar = lambda v: self.after(
            0, lambda val=v: self.pbar.set(val / 100)
        )
        self.download_thread.cb_speed = lambda s, e: self.after(0, lambda spd=s, eta=e: (
            self.spd_lbl.configure(text=f"⚡ {spd}"),
            self.eta_lbl.configure(text=f"⏱️ {eta}")
        ))
        self.download_thread.cb_current  = lambda u, t: self.after(0, lambda url=u: self._highlight_url(url))
        self.download_thread.cb_status   = lambda u, s, t: self.after(0, lambda url=u, st=s, ti=t: self._set_url_status(url, st, ti))
        self.download_thread.cb_done     = lambda: self.after(0, self._on_download_done)
        self.download_thread.cb_error    = lambda m: self.after(0, lambda msg=m: self._on_download_error(msg))
        self.download_thread.cb_queue    = self._update_queue

        self.download_thread.start()

    def _highlight_url(self, url: str):
        for i, (u, _) in enumerate(self.url_titles.items()):
            if u == url and i < len(self.url_items):
                it = self.url_items[i]
                if it.winfo_exists():
                    it.set_status("downloading")
                break

    def _set_url_status(self, url: str, status: str, title: str = None):
        for i, (u, _) in enumerate(self.url_titles.items()):
            if u == url and i < len(self.url_items):
                it = self.url_items[i]
                if it.winfo_exists():
                    it.set_status(status)
                break

        if status == "completed" and title:
            self.history.append({
                "url":    url,
                "title":  title,
                "format": self.fmt_var.get(),
            })
            self._refresh_stats()

    def pause_download(self):
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.pause()
            self.status_lbl.configure(text="⏸️ Duraklatıldı")
            self.ps_btn.configure(state="disabled")
            self.rs_btn.configure(state="normal")

    def resume_download(self):
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.resume()
            self.status_lbl.configure(text="▶️ Devam ediyor...")
            self.ps_btn.configure(state="normal")
            self.rs_btn.configure(state="disabled")

    def stop_download(self):
        if self.download_thread and self.download_thread.is_alive():
            if messagebox.askyesno("Onay", "İndirmeyi durdurmak istediğinize emin misiniz?"):
                self.download_thread.stop()
                self.status_lbl.configure(text="⏹️ Durduruldu")
                self._reset_ui()

    def _on_download_done(self):
        elapsed = time.time() - (self.download_thread.start_time or time.time())
        m, s = divmod(int(elapsed), 60)
        self.status_lbl.configure(text=f"✅ Tamamlandı! ({m}dk {s}sn)")
        self.pbar.set(1.0)

        try:
            notification.notify(
                title="NeoTube Pro",
                message=f"İndirme tamamlandı! ({len(self.url_titles)} öğe)",
                timeout=6
            )
        except Exception:
            pass

        messagebox.showinfo("Başarılı", f"Tüm indirmeler tamamlandı!\nGeçen süre: {m} dakika {s} saniye")
        self._reset_ui()

    def _on_download_error(self, msg: str):
        self.status_lbl.configure(text="❌ Hata oluştu")
        messagebox.showerror("İndirme Hatası", msg)

    def _reset_ui(self):
        self.is_downloading = False
        self.url_box.configure(state="normal")
        self.dl_btn.configure(state="normal")
        self.ps_btn.configure(state="disabled")
        self.rs_btn.configure(state="disabled")
        self.sp_btn.configure(state="disabled")
        self.clr_btn.configure(state="normal")
        for w in self.q_frame.winfo_children():
            w.destroy()

    # ============================================================
    # Dönüştürücü
    # ============================================================
    def open_converter(self):
        if hasattr(self, '_conv_win') and self._conv_win.winfo_exists():
            self._conv_win.lift()
            self._conv_win.focus_force()
        else:
            self._conv_win = ConverterWindow(self)

# ============================================================
# 9. GİRİŞ NOKTASI
# ============================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try:
        app = NeoTubeApp()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı:\n{exc}")
        sys.exit(1)