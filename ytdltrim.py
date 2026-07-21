"""
ytdltrim — YouTube Downloader & Trimmer (Desktop App)
Dibangun dengan CustomTkinter + yt-dlp.
"""

import os
import re
import sys
import shutil
import queue
import threading
import subprocess
import urllib.parse
import time

import customtkinter as ctk
from tkinter import filedialog
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

APP_NAME = "ytdltrim"
APP_VERSION = "1.0.0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palet warna kustom senada dengan versi CLI (cyan / magenta)
COL_BG = "#111318"
COL_CARD = "#181b22"
COL_ACCENT = "#22d3ee"     # cyan
COL_ACCENT2 = "#d640b0"    # magenta
COL_SUCCESS = "#22c55e"
COL_ERROR = "#ef4444"
COL_WARNING = "#eab308"
COL_MUTED = "#8b93a1"
COL_TEXT = "#e8eaed"

FONT_FAMILY = "Segoe UI"


def resource_path(relative_path):
    """Dapatkan path resource, kompatibel dengan mode PyInstaller (--onefile)."""
    try:
        base_path = sys._MEIPASS  # noqa
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', '', title).strip()


def is_valid_youtube_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain in ('youtube.com', 'youtu.be', 'm.youtube.com', 'music.youtube.com')
    except Exception:
        return False


def parse_time_to_seconds(time_str):
    time_str = (time_str or "").strip()
    if not time_str:
        return None
    if not re.match(r'^[\d:]+$', time_str):
        raise ValueError("Format waktu salah. Gunakan angka dan (:) saja.")
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError("Format waktu terlalu panjang.")


def format_seconds(total_seconds):
    if total_seconds is None or total_seconds == float('inf'):
        return "Tidak diketahui"
    total_seconds = int(total_seconds)
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class YtDlTrimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME}")
        self.geometry("860x680")
        self.minsize(760, 620)
        self.configure(fg_color=COL_BG)

        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.output_dir = os.path.abspath("download")
        os.makedirs(self.output_dir, exist_ok=True)

        self.ui_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False

        self._build_layout()
        self._poll_queue()
        self._check_ffmpeg()

    # ---------------- UI LAYOUT ----------------
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            header, text="ytdltrim",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=COL_ACCENT,
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        subtitle_lbl = ctk.CTkLabel(
            header, text="YouTube Downloader & Trimmer",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COL_MUTED,
        )
        subtitle_lbl.grid(row=1, column=0, sticky="w")

        self.folder_btn = ctk.CTkButton(
            header, text="📁  Buka Folder", width=140, height=34,
            fg_color="transparent", border_width=1, border_color=COL_MUTED,
            hover_color="#22262f", text_color=COL_TEXT,
            command=self.open_output_folder,
        )
        self.folder_btn.grid(row=0, column=1, rowspan=2, sticky="e")

        # --- Body scrollable ---
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=0)
        body.grid_columnconfigure(0, weight=1)

        # Card: URL
        card_url = self._card(body, "🔗  Link Video YouTube")
        card_url.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        card_url.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            card_url, placeholder_text="https://www.youtube.com/watch?v=...",
            height=40, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 16))

        # Card: Format & kualitas
        card_fmt = self._card(body, "🎯  Format & Kualitas")
        card_fmt.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        card_fmt.grid_columnconfigure((0, 1), weight=1)

        self.format_var = ctk.StringVar(value="mp4")
        self.format_seg = ctk.CTkSegmentedButton(
            card_fmt, values=["🎬  MP4 (Video)", "🎵  MP3 (Audio)"],
            command=self._on_format_change,
            selected_color=COL_ACCENT2, selected_hover_color=COL_ACCENT2,
        )
        self.format_seg.set("🎬  MP4 (Video)")
        self.format_seg.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 12))

        self.quality_label = ctk.CTkLabel(
            card_fmt, text="Kualitas Video", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COL_MUTED, anchor="w",
        )
        self.quality_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=16)

        self.quality_var = ctk.StringVar(value="720p (HD)")
        self.quality_menu = ctk.CTkOptionMenu(
            card_fmt, variable=self.quality_var,
            values=["1080p (Full HD)", "720p (HD)", "360p (SD)"],
            fg_color=COL_CARD, button_color=COL_ACCENT, button_hover_color=COL_ACCENT2,
        )
        self.quality_menu.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 16))

        # Card: Trimming
        card_trim = self._card(body, "✂️  Potong Waktu (opsional)")
        card_trim.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        card_trim.grid_columnconfigure((0, 1), weight=1)

        hint = ctk.CTkLabel(
            card_trim, text="Format: SS, MM:SS, atau HH:MM:SS  •  Kosongkan untuk video penuh",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=COL_MUTED, anchor="w",
        )
        hint.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(2, 8))

        start_lbl = ctk.CTkLabel(card_trim, text="Mulai (Start)", font=ctk.CTkFont(size=12), text_color=COL_MUTED)
        start_lbl.grid(row=2, column=0, sticky="w", padx=16)
        end_lbl = ctk.CTkLabel(card_trim, text="Akhir (End)", font=ctk.CTkFont(size=12), text_color=COL_MUTED)
        end_lbl.grid(row=2, column=1, sticky="w", padx=16)

        self.start_entry = ctk.CTkEntry(card_trim, placeholder_text="00:00", height=36)
        self.start_entry.grid(row=3, column=0, sticky="ew", padx=(16, 8), pady=(2, 16))
        self.end_entry = ctk.CTkEntry(card_trim, placeholder_text="kosong = akhir", height=36)
        self.end_entry.grid(row=3, column=1, sticky="ew", padx=(8, 16), pady=(2, 16))

        # Card: Info video (terisi setelah proses berjalan)
        self.info_card = self._card(body, "🎞️  Info Video")
        self.info_card.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.info_card.grid_columnconfigure(0, weight=1)
        self.info_card.grid_remove()  # sembunyikan sampai ada data

        self.info_label = ctk.CTkLabel(
            self.info_card, text="", justify="left", anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COL_TEXT,
        )
        self.info_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 16))

        # Card: Log
        card_log = self._card(body, "📜  Log Proses")
        card_log.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        card_log.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(
            card_log, height=140, fg_color="#0c0e12", text_color=COL_MUTED,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.log_box.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 16))
        self.log_box.configure(state="disabled")

        # --- Footer: progress + tombol ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(6, 18))
        footer.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            footer, text="Siap mengunduh.", font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COL_MUTED, anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(footer, progress_color=COL_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew")
        btn_row.grid_columnconfigure(0, weight=1)

        self.download_btn = ctk.CTkButton(
            btn_row, text="⬇  Unduh Sekarang", height=44,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=COL_ACCENT2, hover_color="#b8348f",
            command=self.start_download,
        )
        self.download_btn.grid(row=0, column=0, sticky="ew")

        self._on_format_change(self.format_seg.get())

    def _card(self, parent, title_text):
        card = ctk.CTkFrame(parent, fg_color=COL_CARD, corner_radius=12)
        card.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(
            card, text=title_text, anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COL_TEXT,
        )
        title.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 2))
        return card

    def _on_format_change(self, value):
        if value.startswith("🎬"):
            self.format_var.set("mp4")
            self.quality_label.configure(text="Kualitas Video")
            self.quality_menu.configure(values=["1080p (Full HD)", "720p (HD)", "360p (SD)"])
            self.quality_var.set("720p (HD)")
        else:
            self.format_var.set("mp3")
            self.quality_label.configure(text="Bitrate Audio")
            self.quality_menu.configure(values=["320 kbps (Sangat Tinggi)", "192 kbps (Standar)"])
            self.quality_var.set("320 kbps (Sangat Tinggi)")
        self.quality_menu.set(self.quality_var.get())

    # ---------------- LOG / STATUS HELPERS ----------------
    def log(self, text, level="info"):
        self.ui_queue.put(("log", (text, level)))

    def set_status(self, text):
        self.ui_queue.put(("status", text))

    def set_progress(self, value):
        self.ui_queue.put(("progress", value))

    def show_info(self, info_dict):
        self.ui_queue.put(("info", info_dict))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()
                if kind == "log":
                    text, level = payload
                    colors = {
                        "info": COL_MUTED, "success": COL_SUCCESS,
                        "error": COL_ERROR, "warning": COL_WARNING,
                    }
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", f"{text}\n")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                elif kind == "status":
                    self.status_label.configure(text=payload)
                elif kind == "progress":
                    self.progress_bar.set(payload)
                elif kind == "info":
                    self._render_info(payload)
                elif kind == "done":
                    self._on_finished(payload)
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _render_info(self, d):
        self.info_card.grid()
        lines = [
            f"Judul     : {d.get('title', '-')}",
            f"Channel   : {d.get('uploader', 'Tidak diketahui')}  ({d.get('views', 0):,} tayangan)",
            f"Durasi    : {format_seconds(d.get('duration'))}",
        ]
        if d.get('cut_range'):
            lines.append(f"Potongan  : {d['cut_range']}")
        self.info_label.configure(text="\n".join(lines))

    def _on_finished(self, success):
        self.is_running = False
        self.download_btn.configure(state="normal", text="⬇  Unduh Sekarang")
        if success:
            self.progress_bar.set(1)
            self.set_status("✅ Selesai — file tersimpan di folder download.")
        else:
            self.set_status("❌ Proses dihentikan karena terjadi error.")

    # ---------------- ACTIONS ----------------
    def _check_ffmpeg(self):
        if shutil.which("ffmpeg") is None:
            self.log("⚠️  FFmpeg tidak ditemukan di PATH. Trimming/convert bisa gagal.", "warning")
            self.log("    Letakkan ffmpeg.exe di folder yang sama dengan ytdltrim.exe, atau tambahkan ke PATH.", "warning")

    def open_output_folder(self):
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(self.output_dir)  # noqa
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.output_dir])
            else:
                subprocess.Popen(["xdg-open", self.output_dir])
        except Exception as ex:
            self.log(f"❌  Tidak bisa membuka folder: {ex}", "error")

    def start_download(self):
        if self.is_running:
            return

        url = self.url_entry.get().strip()
        if not url:
            self.log("❌  Link tidak boleh kosong!", "error")
            return
        if not is_valid_youtube_url(url):
            self.log("❌  URL sepertinya bukan link YouTube yang valid.", "error")
            return

        try:
            start_seconds = parse_time_to_seconds(self.start_entry.get())
            end_seconds = parse_time_to_seconds(self.end_entry.get())
        except ValueError as e:
            self.log(f"❌  {e}", "error")
            return

        self.is_running = True
        self.download_btn.configure(state="disabled", text="⏳  Memproses...")
        self.progress_bar.set(0)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.info_card.grid_remove()
        self.set_status("Memulai proses...")

        params = {
            "url": url,
            "format_choice": self.format_var.get(),
            "quality_choice": self.quality_var.get(),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
        }

        self.worker_thread = threading.Thread(target=self._run_download, args=(params,), daemon=True)
        self.worker_thread.start()

    def _run_download(self, params):
        success = False
        try:
            self._download_worker(params)
            success = True
        except DownloadError as de:
            self.log(f"❌  Download gagal: {de}", "error")
        except Exception as ex:
            self.log(f"❌  Terjadi kesalahan sistem: {ex}", "error")
        finally:
            self.ui_queue.put(("done", success))

    def _download_worker(self, params):
        url = params["url"]
        fmt = params["format_choice"]
        quality = params["quality_choice"]
        start_seconds = params["start_seconds"]
        end_seconds = params["end_seconds"]

        def progress_hook(d):
            status = d.get("status")
            if status == "downloading":
                percent_str = (d.get("_percent_str") or "").strip()
                percent_str_clean = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).replace('%', '')
                try:
                    frac = max(0.0, min(1.0, float(percent_str_clean) / 100))
                    self.set_progress(frac)
                except ValueError:
                    pass
                speed = re.sub(r'\x1b\[[0-9;]*m', '', (d.get("_speed_str") or "").strip())
                downloaded = d.get("downloaded_bytes", 0) / (1024 * 1024)
                total = (d.get("total_bytes") or d.get("total_bytes_estimate") or 0) / (1024 * 1024)
                size_str = f"{downloaded:.1f}MB/{total:.1f}MB" if total else f"{downloaded:.1f}MB"
                self.set_status(f"Mengunduh {percent_str} · {size_str} ({speed})")
            elif status == "finished":
                self.set_status("Selesai mengunduh, memproses file...")

        def pp_hook(d):
            if d.get("status") == "started":
                name = d.get("postprocessor", "Converter")
                self.set_status(f"Merakit format ({name})...")

        ydl_opts = {
            "extractor_args": {"youtube": {"player_client": ["android", "web"], "skip": ["dash", "hls"]}},
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [pp_hook],
            "http_chunk_size": 10485760,
        }

        target_ext = "mp4" if fmt == "mp4" else "mp3"

        if fmt == "mp4":
            resolution = {"1080p (Full HD)": "1080", "720p (HD)": "720", "360p (SD)": "360"}.get(quality, "720")
            ydl_opts["format"] = f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            ydl_opts["merge_output_format"] = "mp4"
        else:
            bitrate = "320" if quality.startswith("320") else "192"
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }]

        self.set_status("Mengekstrak metadata YouTube...")
        probe_opts = ydl_opts.copy()
        probe_opts["skip_download"] = True
        with YoutubeDL(probe_opts) as ydl_probe:
            info = ydl_probe.extract_info(url, download=False)

        clean_title = clean_filename(info.get("title", "Downloaded_Video"))
        original_duration = info.get("duration")

        s, e, cut_range = None, None, None
        if start_seconds is not None or end_seconds is not None:
            s = start_seconds if start_seconds is not None else 0
            e = end_seconds if end_seconds is not None else float("inf")

            if original_duration:
                if s >= original_duration:
                    raise ValueError(
                        f"Waktu mulai ({format_seconds(s)}) melebihi durasi video ({format_seconds(original_duration)})!"
                    )
                if e > original_duration:
                    e = original_duration
            if s >= e:
                raise ValueError("Waktu mulai tidak boleh lebih besar atau sama dengan waktu akhir!")

            ydl_opts["download_ranges"] = lambda info_dict, ydl: [{"start_time": s, "end_time": e}]
            cut_range = f"{format_seconds(s)} → {format_seconds(e)}  (durasi {format_seconds(e - s)})"

        base_path = os.path.join(self.output_dir, clean_title)
        if os.path.exists(f"{base_path}.{target_ext}"):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            unique_title = f"{clean_title}_{timestamp}"
        else:
            unique_title = clean_title

        ydl_opts["outtmpl"] = os.path.join(self.output_dir, f"{unique_title}.%(ext)s")
        ydl_opts["windowsfilenames"] = True

        self.show_info({
            "title": info.get("title", "-"),
            "uploader": info.get("uploader", "Tidak diketahui"),
            "views": info.get("view_count", 0),
            "duration": original_duration,
            "cut_range": cut_range,
        })

        self.log(f"🎞️  {info.get('title', '-')}", "info")
        self.log(f"📺  {info.get('uploader', 'Tidak diketahui')} · {info.get('view_count', 0):,} tayangan", "info")
        if cut_range:
            self.log(f"✂️  Memotong: {cut_range}", "info")

        self.set_status("Mengunduh...")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_name = f"{unique_title}.{target_ext}"
        self.log(f"✅  Berhasil disimpan sebagai: {final_name}", "success")


def main():
    app = YtDlTrimApp()
    app.mainloop()


if __name__ == "__main__":
    main()
