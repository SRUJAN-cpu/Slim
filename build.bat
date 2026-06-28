@echo off
REM Build the standalone Windows executable: dist\slim.exe
REM tiktoken and its vocab are bundled so the .exe needs no Python and runs offline.

echo [slim] Ensuring build deps (PyInstaller + tiktoken)...
python -m pip install --quiet --upgrade pyinstaller tiktoken || goto :error

echo [slim] Pre-downloading the tiktoken vocab to bundle (offline support)...
set "TIKTOKEN_CACHE_DIR=%~dp0vendor\tiktoken_cache"
python -c "import tiktoken; tiktoken.get_encoding('o200k_base')" || goto :error

echo [slim] Building dist\slim.exe ...
python -m PyInstaller --onefile --clean --name slim ^
    --collect-submodules filters ^
    --collect-all tiktoken ^
    --hidden-import tiktoken_ext ^
    --hidden-import tiktoken_ext.openai_public ^
    --add-data "%~dp0vendor\tiktoken_cache;tiktoken_cache" ^
    slim.py || goto :error

echo.
echo [slim] Done. Your executable is at:  dist\slim.exe
echo [slim] Try it:  dist\slim.exe doctor
goto :eof

:error
echo [slim] BUILD FAILED.
exit /b 1
