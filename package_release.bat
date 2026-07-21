@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Package ytdltrim Release
echo ==========================================
echo   Package ytdltrim ^-^> release ZIP
echo ==========================================
echo   Bekerja di folder: %cd%
echo ==========================================
echo.

if not exist "dist\ytdltrim.exe" (
    echo [X] dist\ytdltrim.exe belum ada. Jalankan build.bat terlebih dahulu.
    pause
    exit /b 1
)

set VERSION=1.2.0
set RELEASE_NAME=ytdltrim-v%VERSION%-win64
set RELEASE_DIR=release\%RELEASE_NAME%

echo [1/4] Menyiapkan folder release...
if exist "release\" (
    rmdir /s /q "release"
) else if exist "release" (
    del /f /q "release"
)
mkdir "%RELEASE_DIR%" 2>nul
if not exist "%RELEASE_DIR%" (
    echo.
    echo [X] GAGAL membuat folder "%RELEASE_DIR%".
    echo     Kemungkinan penyebab: folder project ada di dalam OneDrive
    echo     ^(Files On-Demand sering bikin error "directory name is invalid"^).
    echo     Coba pindahkan folder project ini ke lokasi lokal biasa,
    echo     misal C:\Projects\ytdltrim, lalu jalankan lagi script ini.
    echo.
    pause
    exit /b 1
)

echo [2/4] Menyalin ytdltrim.exe...
copy /y "dist\ytdltrim.exe" "%RELEASE_DIR%\" >nul
if not exist "%RELEASE_DIR%\ytdltrim.exe" (
    echo [X] Gagal menyalin ytdltrim.exe ke folder release.
    pause
    exit /b 1
)

echo [3/4] Menyalin FFmpeg (jika ada di folder ffmpeg\)...
if exist "ffmpeg\ffmpeg.exe" (
    copy /y "ffmpeg\ffmpeg.exe" "%RELEASE_DIR%\" >nul
    
    if exist "ffmpeg\ffprobe.exe" (
        copy /y "ffmpeg\ffprobe.exe" "%RELEASE_DIR%\" >nul
    )
    
    if exist "ffmpeg\avcodec-62.dll" (
        copy /y "ffmpeg\avcodec-62.dll" "%RELEASE_DIR%\" >nul
    )
    
    if exist "ffmpeg\LICENSE.txt" (
        copy /y "ffmpeg\LICENSE.txt" "%RELEASE_DIR%\LICENSE-FFmpeg.txt" >nul
    ) else if exist "ffmpeg\LICENSE" (
        copy /y "ffmpeg\LICENSE" "%RELEASE_DIR%\LICENSE-FFmpeg.txt" >nul
    ) else (
        echo   [!] File lisensi FFmpeg tidak ditemukan di folder ffmpeg\ —
        echo       download ulang paket FFmpeg yang menyertakan file LICENSE,
        echo       lalu letakkan di folder ffmpeg\.
    )
    copy /y "NOTICE.txt" "%RELEASE_DIR%\" >nul
) else (
    echo   [!] ffmpeg\ffmpeg.exe tidak ditemukan.
    echo       Download dari https://www.gyan.dev/ffmpeg/builds/
    echo       ^(pilih varian "LGPL shared" untuk kewajiban lisensi paling ringan^),
    echo       extract, lalu letakkan ffmpeg.exe + LICENSE ke folder ffmpeg\ di sini,
    echo       kemudian jalankan ulang script ini.
    echo       Melanjutkan tanpa FFmpeg...
)

copy /y "README.md" "%RELEASE_DIR%\" >nul 2>nul

echo [4/4] Membuat file ZIP...
powershell -NoProfile -Command ^
  "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath 'release\%RELEASE_NAME%.zip' -Force"

if not exist "release\%RELEASE_NAME%.zip" (
    echo.
    echo [X] Gagal membuat file ZIP. Lihat pesan error PowerShell di atas.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  SELESAI!
echo  Zip siap upload ke GitHub Releases:
echo  release\%RELEASE_NAME%.zip
echo ==========================================
echo.
pause