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
from tkinter import filedialog, messagebox
from tkinter import Tk, Label, ttk
import socket

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
    if missing:
        # Geçici bir pencere göster (standart tkinter kullan)
        root = Tk()
        root.title("NeoTube Kurulumu")
        root.geometry("400x150")
        root.configure(bg='#2b2b2b')
        lbl = Label(root, text=f"Eksik paketler: {', '.join(missing)}\nKurulum yapılıyor...", 
                    fg='white', bg='#2b2b2b', font=('Arial', 10))
        lbl.pack(pady=20)
        progress = ttk.Progressbar(root, length=300, mode='indeterminate')
        progress.pack(pady=10)
        progress.start()
        root.update()
        
        try:
            for pkg in missing:
                install_package(pkg)
            # yt-dlp özelinde güncelleme
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            root.destroy()
            # Uygulamayı yeniden başlat
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            root.destroy()
            messagebox.showerror("Kurulum Hatası", f"Paket kurulumu başarısız:\n{e}\n\nLütfen elle yükleyin:\npip install customtkinter yt-dlp plyer")
            sys.exit(1)

# İlk çalıştırmada bağımlılıkları kontrol et
check_and_install_dependencies()

# Şimdi güvenle import yapabiliriz
import customtkinter as ctk
import yt_dlp
from plyer import notification

# ============================================================
# 2. FFMPEG OTOMATİK İNDİRME (WINDOWS)
# ============================================================
def get_ffmpeg_path():
    """FFmpeg yolunu döndürür, yoksa indirip kurar."""
    # Uygulama klasörü altında ffmpeg/bin/ffmpeg.exe
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_dir = os.path.join(base_dir, "ffmpeg", "bin")
    ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe
    
    # İnternet bağlantısı kontrolü
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
    except OSError:
        messagebox.showerror("Bağlantı Hatası", "FFmpeg indirilemedi. Lütfen internet bağlantınızı kontrol edin.")
        return None
    
    # İndirme işlemi
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(base_dir, "ffmpeg_temp.zip")
    
    # Bilgilendirme penceresi (customtkinter henüz kurulu, kullanabiliriz)
    win = ctk.CTkToplevel()
    win.title("NeoTube Kurulumu")
    win.geometry("400x150")
    win.attributes('-topmost', True)
    ctk.CTkLabel(win, text="FFmpeg indiriliyor, lütfen bekleyin...\n(Bu işlem birkaç dakika sürebilir)",
                 font=ctk.CTkFont(size=12)).pack(pady=20)
    prog = ctk.CTkProgressBar(win, width=300)
    prog.pack(pady=10)
    prog.set(0)
    win.update()
    
    def report_hook(block, blocksize, total):
        if total > 0:
            percent = min(1.0, block * blocksize / total)
            prog.set(percent)
            win.update()
    
    try:
        urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)
        # Zip'i aç
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # İçinde ffmpeg.exe hangi klasörde? ffmpeg-xxxx/bin/ffmpeg.exe
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe"):
                    # Çıkart
                    zip_ref.extract(member, base_dir)
                    extracted = os.path.join(base_dir, member)
                    os.makedirs(ffmpeg_dir, exist_ok=True)
                    shutil.move(extracted, ffmpeg_exe)
                    break
        os.remove(zip_path)
        win.destroy()
        return ffmpeg_exe
    except Exception as e:
        win.destroy()
        messagebox.showerror("FFmpeg Hatası", f"FFmpeg indirilemedi:\n{e}\n\nLütfen https://ffmpeg.org/ adresinden manuel olarak indirip\n{ffmpeg_exe} konumuna kopyalayın.")
        return None

# ============================================================
# 3. TitleResolverThread (değişmedi)
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
        opts = {
            'quiet': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'no_warnings': True
        }
        for i, url in enumerate(self.urls):
            if self._stop_flag:
                break
            if self.progress_callback:
                self.progress_callback(i + 1, len(self.urls), f"Çözümleniyor: {url[:50]}...")
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        title = info.get("title", url)
                        if 'entries' in info:
                            count = len(info['entries']) if info['entries'] else 0
                            title = f"📁 {title} (Playlist - {count} video)"
                        else:
                            dur = info.get('duration', 0)
                            if dur:
                                m, s = divmod(int(dur), 60)
                                title = f"🎬 {title} ({m}:{s:02d})"
                            else:
                                title = f"🎬 {title}"
                        results[url] = re.sub(r'[<>:"/\\|?*]', '-', title)
                    else:
                        results[url] = f"⚠️ {url} (Çözümlenemedi)"
            except Exception as e:
                results[url] = f"❌ {url} (Hata: {str(e)[:30]})"
        self.callback(results)

    def stop(self):
        self._stop_flag = True

# ============================================================
# 4. DownloadThread (değişmedi, ffmpeg yolu dinamik)
# ============================================================
class DownloadThread(threading.Thread):
    def __init__(self, urls, titles, save_path, fmt="best", concurrent=3, proxy=None, speed_limit=None, ffmpeg=None):
        super().__init__(daemon=True)
        self.urls = urls
        self.titles = titles
        self.save_path = save_path
        self.fmt = fmt
        self.concurrent = concurrent
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.ffmpeg = ffmpeg
        self._pause = False
        self._stop = False
        self.idx = 0
        self.total = len(urls)
        self.start_time = None

        self.cb_progress = None
        self.cb_status = None
        self.cb_done = None
        self.cb_current = None
        self.cb_bar = None
        self.cb_error = None
        self.cb_speed = None
        self.cb_queue = None

    def run(self):
        self.start_time = time.time()
        for i, url in enumerate(self.urls, start=1):
            self.idx = i
            if self._stop:
                break
            while self._pause:
                time.sleep(0.2)

            title = self.titles.get(url, f"URL {i}")
            clean = re.sub(r'[<>:"/\\|?*]', '-',
                           title.replace("📁 ", "").replace("🎬 ", "").replace("⚠️ ", "").replace("❌ ", ""))

            if self.cb_current:
                self.cb_current(url, clean)
            if self.cb_queue:
                self.cb_queue(i, self.total, clean)

            def hook(d):
                if self._stop:
                    raise Exception("İndirme durduruldu")
                if d['status'] == 'downloading':
                    if d.get('total_bytes'):
                        pct = d['downloaded_bytes'] / d['total_bytes'] * 100
                    elif d.get('total_bytes_estimate'):
                        pct = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                    else:
                        pct = 0
                    if self.cb_bar:
                        self.cb_bar(int(pct))
                    spd = d.get('speed', 0)
                    if spd and self.cb_speed:
                        mb = spd / 1024 / 1024
                        eta = d.get('eta', 0)
                        eta_str = f"{eta//60}:{eta%60:02d}" if eta else "??"
                        self.cb_speed(f"{mb:.1f} MB/s", eta_str)
                elif d['status'] == 'finished':
                    if self.cb_bar:
                        self.cb_bar(100)

            try:
                if self.cb_progress:
                    self.cb_progress(f"📥 {i}/{self.total} - İndiriliyor: {clean}")

                fmt_map = {
                    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
                    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
                    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
                    "MP3 (128k)": "bestaudio/best",
                    "MP3 (320k)": "bestaudio/best",
                    "video_only": "bestvideo[ext=mp4]"
                }
                if self.fmt == "audio":
                    self.fmt = "MP3 (128k)"
                elif self.fmt == "audio_320":
                    self.fmt = "MP3 (320k)"

                selector = fmt_map.get(self.fmt, fmt_map["best"])
                folder = os.path.join(self.save_path, clean)
                os.makedirs(folder, exist_ok=True)

                post = []
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")
                if self.fmt in ("MP3 (128k)", "MP3 (320k)") and self.ffmpeg:
                    q = "5" if self.fmt == "MP3 (128k)" else "0"
                    post = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': q}]
                    outtmpl = os.path.join(folder, "%(title)s.mp3")

                ydl_opts = {
                    "outtmpl": outtmpl,
                    "format": selector,
                    "quiet": True,
                    "no_warnings": True,
                    "ignoreerrors": True,
                    "progress_hooks": [hook],
                    "noplaylist": False,
                    "continuedl": True,
                    "retries": 10,
                    "fragment_retries": 10,
                    "concurrent_fragment_downloads": self.concurrent,
                    "postprocessors": post,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                if self.proxy:
                    ydl_opts["proxy"] = self.proxy
                if self.speed_limit:
                    ydl_opts["ratelimit"] = self.speed_limit * 1024 * 1024
                if self.ffmpeg:
                    ydl_opts["ffmpeg_location"] = self.ffmpeg

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                if self.cb_status:
                    self.cb_status(url, "completed", clean)

            except Exception as e:
                if self.cb_bar:
                    self.cb_bar(0)
                msg = str(e)
                if "members" in msg.lower() or "private" in msg.lower():
                    if self.cb_progress:
                        self.cb_progress(f"⚠️ {i}/{self.total} - Atlandı (Özel): {clean}")
                    if self.cb_status:
                        self.cb_status(url, "skipped", clean)
                else:
                    if self.cb_progress:
                        self.cb_progress(f"❌ {i}/{self.total} - Hata: {clean}")
                    if self.cb_status:
                        self.cb_status(url, "error", clean)
                    if self.cb_error:
                        self.cb_error(f"Hata: {msg[:100]}...")

        if self.cb_done:
            self.cb_done()

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def stop(self):
        self._stop = True

# ============================================================
# 5. URLItem (değişmedi)
# ============================================================
class URLItem(ctk.CTkFrame):
    def __init__(self, master, index, title, url, **kwargs):
        super().__init__(master, height=40, **kwargs)
        self.pack_propagate(False)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)

        ctk.CTkLabel(self, text=f"{index}.", width=30, anchor="e",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self, text=title, anchor="w").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(self, text=url, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.status_lbl = ctk.CTkLabel(self, text="⏳", width=30, font=ctk.CTkFont(size=16))
        self.status_lbl.grid(row=0, column=3, padx=5)
        self.fav_lbl = ctk.CTkLabel(self, text="☆", width=20, font=ctk.CTkFont(size=16))
        self.fav_lbl.grid(row=0, column=4, padx=5)
        self.set_status("waiting")

    def set_status(self, status):
        colors = {
            "downloading": "#ffcc00", "completed": "#28a745",
            "skipped": "#007bff", "error": "#dc3545", "waiting": ("gray70", "gray20")
        }
        icons = {
            "downloading": "⏬", "completed": "✅",
            "skipped": "⏭️", "error": "❌", "waiting": "⏳"
        }
        self.configure(fg_color=colors.get(status, ("gray70", "gray20")))
        self.status_lbl.configure(text=icons.get(status, "⏳"))

    def set_fav(self, fav):
        self.fav_lbl.configure(text="★" if fav else "☆",
                               text_color="#ffcc00" if fav else "gray")

# ============================================================
# 6. ConverterWindow (ffmpeg yolu dinamik)
# ============================================================
class ConverterWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("NeoTube Dönüştürücü - WAV 22050 Hz")
        self.geometry("800x650")
        self.minsize(700, 550)
        self.master_app = master

        self.files = []
        self.out_fmt = ctk.StringVar(value="wav_22050")
        self.out_dir = ""
        self.trim_silence = ctk.BooleanVar(value=False)

        self.build_ui()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', True))

        self.ffmpeg_path = master.ffmpeg_path
        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            self.conv_btn.configure(state="disabled", text="❌ FFmpeg Yok")
            self.stat_lbl.configure(text=f"HATA: FFmpeg bulunamadı")
        else:
            self.conv_btn.configure(state="normal", text="🔄 Başlat")

    def bring_to_front(self):
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', True))

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self, text="🔄 Medya Dönüştürücü (WAV 22050 Hz)",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=10)

        inp = ctk.CTkFrame(self)
        inp.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        inp.grid_columnconfigure(0, weight=1)

        self.src_lbl = ctk.CTkLabel(inp, text="Hiçbir dosya seçilmedi", height=30,
                                    fg_color=("gray75", "gray25"), corner_radius=5, anchor="w")
        self.src_lbl.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        bf = ctk.CTkFrame(inp, fg_color="transparent")
        bf.grid(row=0, column=1)
        ctk.CTkButton(bf, text="📁 Dosya", width=90, command=self.add_files).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="📂 Klasör", width=90, command=self.add_folder).pack(side="left", padx=2)
        ctk.CTkButton(bf, text="🗑️ Temizle", width=80, fg_color="gray", command=self.clear).pack(side="left", padx=2)

        fmt = ctk.CTkFrame(self)
        fmt.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(fmt, text="🎵 Format:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.format_menu = ctk.CTkOptionMenu(fmt,
                                             values=["mp3", "wma", "aac", "flac", "ogg", "m4a", "wav",
                                                     "WAV (22050 Hz)"],
                                             variable=self.out_fmt, width=140)
        self.format_menu.pack(side="left", padx=10)

        self.trim_cb = ctk.CTkCheckBox(fmt, text="✂️ Sessizlikleri kes (deneysel)",
                                       variable=self.trim_silence, onvalue=True, offvalue=False)
        self.trim_cb.pack(side="left", padx=20)

        out = ctk.CTkFrame(self)
        out.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        out.grid_columnconfigure(0, weight=1)
        self.out_lbl = ctk.CTkLabel(out, text="Varsayılan: Kaynak ile aynı", height=30,
                                    fg_color=("gray75", "gray25"), corner_radius=5, anchor="w")
        self.out_lbl.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(out, text="📁 Değiştir", width=100, command=self.pick_out).grid(row=0, column=1, padx=10)

        ctk.CTkLabel(self, text="📋 Dosyalar:", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, padx=20,
                                                                                     pady=(10, 0), sticky="w")
        self.listbox = ctk.CTkScrollableFrame(self, height=200)
        self.listbox.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.file_widgets = []

        self.pbar = ctk.CTkProgressBar(self)
        self.pbar.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        self.pbar.set(0)
        self.stat_lbl = ctk.CTkLabel(self, text="Hazır")
        self.stat_lbl.grid(row=7, column=0, padx=20)
        self.conv_btn = ctk.CTkButton(self, text="🔄 Başlat", fg_color="#28a745", height=40, command=self.start)
        self.conv_btn.grid(row=8, column=0, padx=20, pady=20)

    def add_files(self):
        self.bring_to_front()
        f = filedialog.askopenfilenames(
            title="Medya dosyaları",
            filetypes=[("Medya", "*.mp4;*.mkv;*.avi;*.mov;*.mp3;*.wav;*.flac;*.ogg;*.m4a;*.wma;*.aac"), ("Tümü", "*.*")]
        )
        if f:
            self.files.extend(f)
            self.refresh()
        self.bring_to_front()

    def add_folder(self):
        self.bring_to_front()
        d = filedialog.askdirectory(title="Klasör seçin")
        if d:
            exts = ('.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma', '.aac')
            found = []
            for root, _, names in os.walk(d):
                for n in names:
                    if n.lower().endswith(exts):
                        found.append(os.path.join(root, n))
            self.files = found
            self.src_lbl.configure(text=f"Klasör: {d}")
            self.refresh()
        self.bring_to_front()

    def clear(self):
        self.files = []
        self.src_lbl.configure(text="Hiçbir dosya seçilmedi")
        self.refresh()
        self.bring_to_front()

    def refresh(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        self.file_widgets = []
        for i, p in enumerate(self.files):
            fr = ctk.CTkFrame(self.listbox)
            fr.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(fr, text=f"{i + 1}. {os.path.basename(p)}", anchor="w").pack(side="left", fill="x", expand=True)
            sl = ctk.CTkLabel(fr, text="⏳ bekliyor", width=90, fg_color=("gray70", "gray20"), corner_radius=3)
            sl.pack(side="right", padx=5)
            self.file_widgets.append((sl, p))
        self.stat_lbl.configure(text=f"{len(self.files)} dosya")

    def pick_out(self):
        self.bring_to_front()
        d = filedialog.askdirectory()
        if d:
            self.out_dir = d
            self.out_lbl.configure(text=d)
        self.bring_to_front()

    def start(self):
        self.bring_to_front()
        if not self.files:
            messagebox.showwarning("Uyarı", "Dosya ekleyin.")
            return
        if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
            messagebox.showerror("Hata", "FFmpeg bulunamadı. Kurulum otomatik yapılmalıydı.\nLütfen uygulamayı yeniden başlatın.")
            return
        self.conv_btn.configure(state="disabled", text="🔄 Dönüştürülüyor...")
        self.stat_lbl.configure(text="Dönüştürülüyor...")
        threading.Thread(target=self._convert, daemon=True).start()

    def _convert(self):
        total = len(self.files)
        fmt = self.out_fmt.get()
        ffmpeg = self.ffmpeg_path
        trim_requested = self.trim_silence.get()

        is_wav22050 = (fmt == "WAV (22050 Hz)")
        ext = "wav" if is_wav22050 else fmt

        for i, (slbl, path) in enumerate(self.file_widgets):
            self.after(0, lambda s=slbl: s.configure(text="🔄 dönüşüyor", fg_color="#ffcc00"))

            base = os.path.splitext(os.path.basename(path))[0]
            out_dir = self.out_dir or os.path.dirname(path)
            out = os.path.join(out_dir, f"{base}.{ext}")
            c = 1
            while os.path.exists(out):
                out = os.path.join(out_dir, f"{base}_{c}.{ext}")
                c += 1

            try:
                if is_wav22050:
                    cmd = [ffmpeg, "-i", path, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "22050"]
                    if trim_requested:
                        cmd += ["-af", "silenceremove=1:0.1:0.1:-1:0.1:0.1"]
                    cmd += [out, "-y"]
                else:
                    cmd = [ffmpeg, "-i", path, "-vn"]
                    if fmt == "mp3":
                        cmd += ["-acodec", "libmp3lame", "-ab", "192k"]
                    elif fmt == "wma":
                        cmd += ["-acodec", "wmav2", "-ab", "192k"]
                    elif fmt == "aac":
                        cmd += ["-acodec", "aac", "-b:a", "192k"]
                    elif fmt == "flac":
                        cmd += ["-acodec", "flac", "-compression_level", "5"]
                    elif fmt == "ogg":
                        cmd += ["-acodec", "libvorbis", "-qscale:a", "5"]
                    elif fmt == "m4a":
                        cmd += ["-acodec", "aac", "-b:a", "192k", "-f", "ipod"]
                    elif fmt == "wav":
                        cmd += ["-acodec", "pcm_s16le"]
                    else:
                        cmd += ["-acodec", "copy"]
                    if trim_requested:
                        cmd += ["-af", "silenceremove=1:0.1:0.1:-1:0.1:0.1"]
                    cmd += [out, "-y"]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    self.after(0, lambda s=slbl: s.configure(text="✅ tamam", fg_color="#28a745"))
                else:
                    err = result.stderr[:60] if result.stderr else "FFmpeg hatası"
                    self.after(0, lambda s=slbl, e=err: s.configure(text=f"❌ {e}", fg_color="#dc3545"))
                    if trim_requested and "silenceremove" in result.stderr:
                        cmd2 = [ffmpeg, "-i", path]
                        if is_wav22050:
                            cmd2 += ["-acodec", "pcm_s16le", "-ac", "1", "-ar", "22050", out, "-y"]
                        else:
                            cmd2 += ["-vn"]
                            if fmt == "mp3":
                                cmd2 += ["-acodec", "libmp3lame", "-ab", "192k"]
                            elif fmt == "wav":
                                cmd2 += ["-acodec", "pcm_s16le"]
                            else:
                                cmd2 += ["-acodec", "copy"]
                            cmd2 += [out, "-y"]
                        retry = subprocess.run(cmd2, capture_output=True, text=True)
                        if retry.returncode == 0:
                            self.after(0, lambda s=slbl: s.configure(text="✅ tamam (filtresiz)", fg_color="#28a745"))
                        else:
                            self.after(0, lambda s=slbl: s.configure(text="❌ hata", fg_color="#dc3545"))
            except subprocess.TimeoutExpired:
                self.after(0, lambda s=slbl: s.configure(text="❌ zaman aşımı", fg_color="#dc3545"))
            except Exception as e:
                self.after(0, lambda s=slbl, err=str(e)[:40]: s.configure(text=f"❌ {err}", fg_color="#dc3545"))

            self.after(0, lambda v=(i + 1) / total: self.pbar.set(v))

        self.after(0, self._done)

    def _done(self):
        self.conv_btn.configure(state="normal", text="🔄 Başlat")
        self.stat_lbl.configure(text="Tamamlandı!")
        self.pbar.set(1.0)
        messagebox.showinfo("Bitti", f"{len(self.files)} dosya dönüştürüldü.")
        self.bring_to_front()

# ============================================================
# 7. NeoTubeApp (ana uygulama, ffmpeg yolu dinamik)
# ============================================================
class NeoTubeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NeoTube Pro v4.0 — İndirici & Dönüştürücü")
        self.geometry("1500x900")
        self.minsize(1300, 700)

        self.url_titles = {}
        self.url_items = []
        self.download_thread = None
        self.resolver_thread = None
        self.download_folder = ""
        self.is_downloading = False
        self.favorites = set()
        self.history = []

        # FFmpeg yolunu otomatik bul veya indir
        self.ffmpeg_path = get_ffmpeg_path()
        if not self.ffmpeg_path:
            # Uyarı ver ama devam et, indirme işlemleri (MP3 hariç) çalışabilir
            pass

        self._resolve_id = None

        self.build_ui()
        self.after(1000, self.check_ffmpeg)

    def check_ffmpeg(self):
        ok = self.ffmpeg_path and os.path.exists(self.ffmpeg_path)
        if ok:
            self.req_lbl.configure(text="✅ FFmpeg Hazır")
        else:
            self.req_lbl.configure(text=f"❌ FFmpeg bulunamadı (MP3 çalışmaz)")
            # MP3 seçeneklerini devre dışı bırak
            self.fmt_menu.configure(values=["best", "1080p", "720p", "480p", "video_only"])
            if self.fmt_var.get().startswith("MP3"):
                self.fmt_var.set("best")

    def build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent", height=70)
        top.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="🎬 NeoTube Pro", font=ctk.CTkFont(size=36, weight="bold"),
                     text_color="#ffcc00").grid(row=0, column=0, sticky="w")
        self.req_lbl = ctk.CTkLabel(top, text="🔍 Kontrol ediliyor...", font=ctk.CTkFont(size=12), text_color="gray")
        self.req_lbl.grid(row=0, column=1, sticky="e")

        left = ctk.CTkFrame(self)
        left.grid(row=1, column=0, rowspan=5, padx=(20, 10), pady=10, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(4, weight=1)

        inp = ctk.CTkFrame(left)
        inp.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        inp.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(inp, text="📋 URL'ler (her satır bir URL):", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.url_box = ctk.CTkTextbox(inp, height=100)
        self.url_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.url_box.bind("<<Modified>>", self._on_mod)

        rbf = ctk.CTkFrame(inp, fg_color="transparent")
        rbf.grid(row=1, column=1, padx=10, pady=10, sticky="n")
        self.clr_btn = ctk.CTkButton(rbf, text="🗑️ Temizle", width=100, fg_color="#6c757d", command=self.clear_all)
        self.clr_btn.pack(pady=5)

        setf = ctk.CTkFrame(left)
        setf.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        for c in range(6):
            setf.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(setf, text="📊 Kalite:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.fmt_var = ctk.StringVar(value="best")
        self.fmt_menu = ctk.CTkOptionMenu(setf, values=["best", "1080p", "720p", "480p", "MP3 (128k)", "MP3 (320k)", "video_only"],
                                          variable=self.fmt_var, width=110)
        self.fmt_menu.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(setf, text="⚡ Eşzamanlı:").grid(row=0, column=2, padx=5, pady=10, sticky="w")
        self.conc_var = ctk.IntVar(value=3)
        ctk.CTkEntry(setf, width=40, textvariable=self.conc_var).grid(row=0, column=3, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(setf, text="🚀 Hız Limiti:").grid(row=0, column=4, padx=5, pady=10, sticky="w")
        self.spd_var = ctk.StringVar(value="0 (Sınırsız)")
        ctk.CTkOptionMenu(setf, values=["0 (Sınırsız)", "1 MB/s", "5 MB/s", "10 MB/s", "50 MB/s"],
                          variable=self.spd_var, width=90).grid(row=0, column=5, padx=5, pady=10, sticky="w")

        fold = ctk.CTkFrame(left)
        fold.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        fold.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fold, text="📂 Klasör:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.fold_lbl = ctk.CTkLabel(fold, text="Henüz seçilmedi", height=32, fg_color=("gray75", "gray25"), corner_radius=5, anchor="w")
        self.fold_lbl.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(fold, text="📁 Gözat", width=100, fg_color="#ffcc00", text_color="black",
                      command=self.pick_folder).grid(row=0, column=2, padx=10, pady=10)

        lh = ctk.CTkFrame(left)
        lh.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(lh, text="📋 URL Listesi", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=10, pady=5)
        self.stat_lbl = ctk.CTkLabel(lh, text="", font=ctk.CTkFont(size=12))
        self.stat_lbl.pack(side="left", padx=20)

        self.url_frame = ctk.CTkScrollableFrame(left, corner_radius=10)
        self.url_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, rowspan=4, padx=(10, 20), pady=10, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        qf = ctk.CTkFrame(right)
        qf.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        ctk.CTkLabel(qf, text="📋 Kuyruk", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 0))
        self.q_frame = ctk.CTkScrollableFrame(qf, height=150)
        self.q_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ff = ctk.CTkFrame(right)
        ff.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(ff, text="⭐ Favoriler", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 0))
        self.fav_frame = ctk.CTkScrollableFrame(ff, height=100)
        self.fav_frame.pack(fill="both", expand=True, padx=5, pady=5)

        sf = ctk.CTkFrame(right)
        sf.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(sf, text="📊 İstatistikler", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 0))
        self.stat_box = ctk.CTkTextbox(sf, height=100, state="disabled")
        self.stat_box.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(right, text="🔄 Dönüştürücüyü Aç", fg_color="#ff8c00", height=35,
                      command=self.open_converter).grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        stf = ctk.CTkFrame(left)
        stf.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        stf.grid_columnconfigure(0, weight=1)
        self.status_lbl = ctk.CTkLabel(stf, text="⏸️ Hazır", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00ffcc")
        self.status_lbl.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.spd_lbl = ctk.CTkLabel(stf, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.spd_lbl.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="e")
        self.eta_lbl = ctk.CTkLabel(stf, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.eta_lbl.grid(row=0, column=2, padx=10, pady=(10, 5), sticky="e")
        self.pbar = ctk.CTkProgressBar(stf)
        self.pbar.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.pbar.set(0)

        btnf = ctk.CTkFrame(left)
        btnf.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        for c in range(4):
            btnf.grid_columnconfigure(c, weight=1)
        self.dl_btn = ctk.CTkButton(btnf, text="▶️ Başlat", fg_color="#28a745", height=40, command=self.start_dl)
        self.dl_btn.grid(row=0, column=0, padx=2, pady=5, sticky="ew")
        self.ps_btn = ctk.CTkButton(btnf, text="⏸️ Duraklat", fg_color="#dc3545", height=40, state="disabled", command=self.pause_dl)
        self.ps_btn.grid(row=0, column=1, padx=2, pady=5, sticky="ew")
        self.rs_btn = ctk.CTkButton(btnf, text="▶️ Devam", fg_color="#007bff", height=40, state="disabled", command=self.resume_dl)
        self.rs_btn.grid(row=0, column=2, padx=2, pady=5, sticky="ew")
        self.sp_btn = ctk.CTkButton(btnf, text="⏹️ Durdur", fg_color="#6c757d", height=40, state="disabled", command=self.stop_dl)
        self.sp_btn.grid(row=0, column=3, padx=2, pady=5, sticky="ew")

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=7, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(bot, text="© 2026 NeoTube Pro v4.0 | Geliştirici: Caner Ergün",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(side="left", padx=5)
        for name, col, url in [("LinkedIn", "#0A66C2", "https://linkedin.com/in/devseu/"),
                               ("GitHub", "#333", "https://github.com/canerergun"),
                               ("Instagram", "#C13584", "https://instagram.com/devseu"),
                               ("Twitch", "#9146FF", "https://twitch.tv/devseu")]:
            ctk.CTkButton(bot, text=name, fg_color=col, hover_color=col, width=70, height=25,
                          command=lambda u=url: webbrowser.open(u)).pack(side="right", padx=2)

        self.refresh_fav()
        self.refresh_stats()

    def _on_mod(self, e):
        self.url_box.edit_modified(False)
        if self._resolve_id:
            self.after_cancel(self._resolve_id)
        self._resolve_id = self.after(800, self.resolve)

    def resolve(self):
        raw = [u.strip() for u in self.url_box.get("1.0", "end-1c").splitlines() if u.strip()]
        if not raw:
            self.clear_list()
            return
        if self.resolver_thread and self.resolver_thread.is_alive():
            self.resolver_thread.stop()
        self.url_titles.clear()
        self.status_lbl.configure(text="⏳ URL'ler çözümleniyor...")
        self.resolver_thread = TitleResolverThread(raw, self.on_resolved, self.on_resolve_prog)
        self.resolver_thread.start()
        self._resolve_id = None

    def on_resolve_prog(self, cur, tot, msg):
        self.status_lbl.configure(text=f"⏳ {msg} ({cur}/{tot})")

    def on_resolved(self, results):
        self.url_titles = results
        self.clear_list()
        self.url_items.clear()
        ok = sum(1 for v in results.values() if not v.startswith(("❌", "⚠️")))
        for idx, (url, title) in enumerate(results.items(), 1):
            it = URLItem(self.url_frame, idx, title, url)
            it.pack(fill="x", padx=5, pady=2)
            if url in self.favorites:
                it.set_fav(True)
            it.bind("<Double-Button-1>", lambda e, u=url: self.toggle_fav(u))
            self.url_items.append(it)
            if title.startswith("❌"):
                it.set_status("error")
            elif title.startswith("⚠️"):
                it.set_status("skipped")
            else:
                it.set_status("waiting")
        self.stat_lbl.configure(text=f"Toplam: {len(results)} | Hazır: {ok}")
        self.status_lbl.configure(text=f"✅ {ok} URL hazır.")
        self.refresh_stats()

    def clear_list(self):
        for it in self.url_items[:]:
            try:
                it.destroy()
            except:
                pass
        self.url_items.clear()
        for w in self.url_frame.winfo_children():
            try:
                w.destroy()
            except:
                pass

    def clear_all(self):
        self.url_box.delete("1.0", "end")
        self.url_titles.clear()
        self.clear_list()
        self.stat_lbl.configure(text="")
        self.status_lbl.configure(text="⏸️ Hazır")

    def pick_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.download_folder = d
            self.fold_lbl.configure(text=d, text_color="white")

    def toggle_fav(self, url):
        if url in self.favorites:
            self.favorites.remove(url)
        else:
            self.favorites.add(url)
        for it, (u, _) in zip(self.url_items, self.url_titles.items()):
            if u == url:
                it.set_fav(url in self.favorites)
                break
        self.refresh_fav()
        self.refresh_stats()

    def refresh_fav(self):
        for w in self.fav_frame.winfo_children():
            w.destroy()
        for url in list(self.favorites)[-10:]:
            fr = ctk.CTkFrame(self.fav_frame)
            fr.pack(fill="x", padx=2, pady=1)
            lbl = ctk.CTkLabel(fr, text=f"★ {url[:50]}...", anchor="w", fg_color=("gray60", "gray30"), corner_radius=3, height=20)
            lbl.pack(fill="x", padx=2, pady=1)
            lbl.bind("<Button-1>", lambda e, u=url: self.add_fav_url(u))

    def add_fav_url(self, url):
        cur = self.url_box.get("1.0", "end-1c")
        self.url_box.insert("end", f"\n{url}" if cur else url)

    def refresh_stats(self):
        txt = f"Bu Oturum:\n📥 İndirilen: {len(self.history)}\n⭐ Favori: {len(self.favorites)}\n"
        if self.history:
            txt += f"\nSon İndirme:\n{self.history[-1].get('title','')[:30]}..."
        self.stat_box.configure(state="normal")
        self.stat_box.delete("1.0", "end")
        self.stat_box.insert("1.0", txt)
        self.stat_box.configure(state="disabled")

    def update_queue(self, cur, tot, title):
        for w in self.q_frame.winfo_children():
            w.destroy()
        for i in range(cur, tot + 1):
            txt = f"{i}. {title}" if i == cur else f"{i}. Sırada..."
            fr = ctk.CTkFrame(self.q_frame)
            fr.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(fr, text=txt, anchor="w", fg_color=("gray60", "gray30"), corner_radius=3).pack(fill="x", padx=2, pady=1)

    def start_dl(self):
        urls = list(self.url_titles.keys())
        if not urls:
            messagebox.showwarning("Uyarı", "En az bir URL girin.")
            return
        if not self.download_folder:
            messagebox.showwarning("Uyarı", "Klasör seçin.")
            return
        if self.is_downloading:
            messagebox.showinfo("Bilgi", "İndirme devam ediyor.")
            return

        fmt = self.fmt_var.get()
        if fmt.startswith("MP3") and (not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path)):
            messagebox.showerror("Hata", "MP3 indirmek için FFmpeg gerekli.\nOtomatik kurulum başarısız oldu, lütfen uygulamayı yeniden başlatın.")
            return

        spd = self.spd_var.get()
        limit = None
        if spd != "0 (Sınırsız)":
            try:
                limit = int(spd.split()[0])
            except:
                pass

        self.is_downloading = True
        self.url_box.configure(state="disabled")
        self.dl_btn.configure(state="disabled")
        self.ps_btn.configure(state="normal")
        self.sp_btn.configure(state="normal")
        self.clr_btn.configure(state="disabled")
        self.pbar.set(0)
        self.spd_lbl.configure(text="")
        self.eta_lbl.configure(text="")

        for it in self.url_items:
            it.set_status("waiting")

        self.download_thread = DownloadThread(
            urls, self.url_titles, self.download_folder, fmt,
            self.conc_var.get(), None, limit, self.ffmpeg_path
        )
        self.download_thread.cb_progress = lambda m: self.status_lbl.configure(text=m)
        self.download_thread.cb_bar = lambda v: self.pbar.set(v / 100)
        self.download_thread.cb_speed = lambda s, e: (self.spd_lbl.configure(text=f"⚡ {s}"), self.eta_lbl.configure(text=f"⏱️ {e}"))
        self.download_thread.cb_current = lambda u, t: self.highlight(u)
        self.download_thread.cb_status = lambda u, s, t: self.set_url_status(u, s, t)
        self.download_thread.cb_done = self.on_done
        self.download_thread.cb_error = lambda m: self.on_error(m)
        self.download_thread.cb_queue = self.update_queue
        self.download_thread.start()

    def highlight(self, url):
        for i, (u, _) in enumerate(self.url_titles.items()):
            if i < len(self.url_items) and u == url:
                self.url_items[i].set_status("downloading")
                break

    def set_url_status(self, url, status, title=None):
        for i, (u, _) in enumerate(self.url_titles.items()):
            if i < len(self.url_items) and u == url:
                self.url_items[i].set_status(status)
                break
        if status == "completed" and title:
            self.history.append({"url": url, "title": title, "format": self.fmt_var.get()})
            self.refresh_stats()

    def pause_dl(self):
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.pause()
            self.status_lbl.configure(text="⏸️ Duraklatıldı")
            self.ps_btn.configure(state="disabled")
            self.rs_btn.configure(state="normal")

    def resume_dl(self):
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.resume()
            self.status_lbl.configure(text="▶️ Devam ediyor...")
            self.ps_btn.configure(state="normal")
            self.rs_btn.configure(state="disabled")

    def stop_dl(self):
        if self.download_thread and self.download_thread.is_alive():
            if messagebox.askyesno("Onay", "Durdurmak istediğinize emin misiniz?"):
                self.download_thread.stop()
                self.status_lbl.configure(text="⏹️ Durduruldu")
                self.reset_ui()

    def on_done(self):
        elapsed = time.time() - (self.download_thread.start_time or time.time())
        m, s = divmod(int(elapsed), 60)
        self.status_lbl.configure(text=f"✅ Tamamlandı! ({m}d {s}s)")
        self.pbar.set(1.0)
        try:
            notification.notify(title="NeoTube Pro", message=f"{len(self.url_titles)} öğe indirildi!", timeout=5)
        except:
            pass
        messagebox.showinfo("Başarılı", f"Süre: {m} dakika {s} saniye")
        self.reset_ui()

    def on_error(self, msg):
        self.status_lbl.configure(text="❌ Hata")
        messagebox.showerror("Hata", msg)

    def reset_ui(self):
        self.is_downloading = False
        self.url_box.configure(state="normal")
        self.dl_btn.configure(state="normal")
        self.ps_btn.configure(state="disabled")
        self.rs_btn.configure(state="disabled")
        self.sp_btn.configure(state="disabled")
        self.clr_btn.configure(state="normal")
        for w in self.q_frame.winfo_children():
            w.destroy()

    def open_converter(self):
        if not hasattr(self, 'conv_win') or not self.conv_win.winfo_exists():
            self.conv_win = ConverterWindow(self)
        else:
            self.conv_win.focus()
            self.conv_win.bring_to_front()

# ============================================================
# 8. ANA ÇALIŞTIRMA
# ============================================================
if __name__ == "__main__":
    try:
        app = NeoTubeApp()
        app.mainloop()
    except Exception as e:
        # En genel hata yakalama
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı:\n{str(e)}")
