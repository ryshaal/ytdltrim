@echo off
setlocal
cd /d "%~dp0"
title Build ytdltrim.exe
echo ==========================================
echo   Build ytdltrim menjadi file .exe
echo ==========================================
echo   Bekerja di folder: %cd%
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python tidak ditemukan. Install Python dari https://python.org lalu ulangi.
    pause
    exit /b 1
)

echo [1/4] Membuat virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Menginstall dependencies...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

echo [3/4] Membuat ulang icon (opsional, aman diabaikan jika gagal)...
python make_icon.py

echo [4/4] Membangun ytdltrim.exe dengan PyInstaller...
pyinstaller --noconfirm --onefile --windowed ^
    --name ytdltrim ^
    --icon icon.ico ^
    --add-data "icon.ico;." ^
    ytdltrim.py

echo.
echo ==========================================
echo  SELESAI!
echo  File exe ada di: dist\ytdltrim.exe
echo ==========================================
echo.
echo Catatan: agar fitur konversi/trim berjalan, letakkan ffmpeg.exe
echo di folder yang sama dengan ytdltrim.exe, atau pastikan ffmpeg
echo sudah ada di PATH sistem Windows.
echo.
pause