# ytdltrim

Aplikasi desktop sederhana untuk **download & trim video/audio YouTube**, dibangun dengan Python + CustomTkinter + yt-dlp.

## ✨ Fitur

- Download video (MP4: 1080p/720p/360p) atau audio (MP3: 320/192 kbps)
- Potong (trim) video/audio berdasarkan waktu mulai & akhir
- Progress bar & log proses real-time
- Tampilan modern, dark theme
- Tombol buka folder hasil download langsung dari app

## 📦 Menjalankan langsung dari source (semua OS)

Butuh **Python 3.9+** dan **FFmpeg** terpasang di sistem.

```bash
pip install -r requirements.txt
python ytdltrim.py
```

## 🪟 Membangun jadi `ytdltrim.exe` (Windows, tanpa perlu install Python)

1. Pastikan **Python 3.9+** sudah terpasang di komputer Windows (cek dengan `python --version` di CMD). Kalau belum ada, install dulu dari https://python.org (saat instalasi, centang "Add python.exe to PATH").
2. Salin seluruh folder `ytdltrim` ini ke komputer Windows.
3. Double-click file **`build.bat`**.
   - Script ini otomatis: membuat virtual environment, install semua dependency, generate icon, lalu menjalankan PyInstaller.
4. Setelah selesai, file jadi ada di:
   ```
   dist\ytdltrim.exe
   ```
5. Salin `ytdltrim.exe` itu ke folder mana saja — sudah bisa dijalankan tanpa perlu Python terpasang lagi.

### ⚠️ Penting soal FFmpeg

`ytdltrim.exe` **tidak membundel FFmpeg** (agar ukuran file tetap kecil & legal-friendly, karena FFmpeg punya lisensi & build sendiri).
Supaya fitur convert MP3 & trimming berjalan, lakukan salah satu:

- **Opsi A (disarankan):** Download FFmpeg build untuk Windows dari https://www.gyan.dev/ffmpeg/builds/ (pilih "release essentials"), extract, lalu copy `ffmpeg.exe` ke folder yang sama dengan `ytdltrim.exe`.
- **Opsi B:** Tambahkan folder FFmpeg ke PATH sistem Windows (Environment Variables), lalu restart aplikasi.

Aplikasi akan otomatis menampilkan peringatan di kolom **Log** kalau FFmpeg tidak terdeteksi.

## 🗂️ Struktur folder

```
ytdltrim/
├── ytdltrim.py        # source code aplikasi
├── make_icon.py        # generator icon.ico
├── requirements.txt    # daftar dependency Python
├── build.bat            # script build otomatis ke .exe (Windows)
└── README.md            # dokumen ini
```

Hasil download akan otomatis tersimpan di folder `download/` yang dibuat di sebelah file exe / script.

## 🚀 Merilis ke GitHub (exe + FFmpeg dalam satu ZIP)

1. Jalankan `build.bat` seperti biasa → hasil `dist\ytdltrim.exe`.
2. Download FFmpeg untuk Windows dari https://www.gyan.dev/ffmpeg/builds/
   - Disarankan pilih varian **"LGPL shared"** (bukan "GPL essentials"), supaya kewajiban lisensinya lebih ringan.
   - Extract, lalu ambil `bin\ffmpeg.exe` dan file `LICENSE`/`LICENSE.txt` di dalamnya.
3. Buat folder `ffmpeg\` di sebelah `build.bat`, isi dengan `ffmpeg.exe` + `LICENSE.txt` tadi.
4. Jalankan **`package_release.bat`**.
   - Otomatis membuat `release\ytdltrim-v1.0.0-win64.zip` yang isinya:
     ```
     ytdltrim.exe
     ffmpeg.exe
     LICENSE-FFmpeg.txt
     NOTICE.txt
     README.md
     ```
5. Upload file zip itu ke halaman **GitHub Releases** repo kamu.

> ⚖️ **Kenapa harus ada NOTICE.txt & LICENSE-FFmpeg.txt?**
> FFmpeg berlisensi GPL/LGPL. Karena hanya diletakkan berdampingan (bukan digabung jadi satu binary), kode `ytdltrim` sendiri tidak ikut terikat GPL — tapi kamu tetap wajib menyertakan teks lisensi & atribusi FFmpeg saat mendistribusikan ulang binarinya. Detail lengkap ada di `NOTICE.txt`.

Kalau mau lebih ringan (tanpa urus lisensi FFmpeg sama sekali), alternatifnya: jangan bundling FFmpeg, cukup cantumkan instruksi di README rilis GitHub bahwa user perlu download FFmpeg sendiri dan taruh di folder yang sama.



Kalau source code (`ytdltrim.py`) diperbarui, cukup jalankan ulang `build.bat` untuk membuat `.exe` versi terbaru.
