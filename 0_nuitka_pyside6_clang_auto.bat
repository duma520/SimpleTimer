nuitka --standalone ^
    --enable-plugin=pyside6 ^
    --include-qt-plugins=multimedia ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=icon.ico ^
    --include-data-files=icon.ico=icon.ico ^
    --jobs=4 ^
    --remove-output ^
    --output-dir=build_output ^
    SimpleTimer.py

REM ===== 复制 FFmpeg DLL 到输出目录（多媒体播放必需） =====
set "PYTHON_DIR=D:\Program Files\Python310"
set "PYSIDE6_DIR=%PYTHON_DIR%\lib\site-packages\PySide6"
set "OUTPUT_DIR=build_output\SimpleTimer.dist"

echo 正在复制 FFmpeg 多媒体 DLL...
copy "%PYSIDE6_DIR%\avcodec-61.dll" "%OUTPUT_DIR%\" >nul 2>&1
copy "%PYSIDE6_DIR%\avformat-61.dll" "%OUTPUT_DIR%\" >nul 2>&1
copy "%PYSIDE6_DIR%\avutil-59.dll" "%OUTPUT_DIR%\" >nul 2>&1
copy "%PYSIDE6_DIR%\swresample-5.dll" "%OUTPUT_DIR%\" >nul 2>&1
echo FFmpeg DLL 复制完成！
