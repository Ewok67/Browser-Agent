@echo off
REM Startet llama.cpp Server für AI Search Guard
REM === Pfad zu llama.cpp anpassen! ===

set LLAMA_PATH=C:\Pfad\zu\llama.cpp\build\bin
set MODEL=models\qwen2.5-0.5b-instruct-q4_k_m.gguf

echo Starte llama.cpp Server auf Port 8080...
"%LLAMA_PATH%\llama-server.exe" -m "%MODEL%" --port 8080 -c 2048 --host 0.0.0.0

pause
