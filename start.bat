@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title 北商選課系統

rem 用法：start.bat [django^|google^|preview]，不帶參數會顯示選單
set "MODE=%~1"
if not "%MODE%"=="" goto run

echo.
echo   北商選課系統
echo   ----------------------------------------
echo   1. Django 版（Firebase + OpenAI）  http://127.0.0.1:8000
echo   2. Google 登入正式版（線上）       https://ntub-course-352781737994.asia-east1.run.app/
echo   3. 單檔預覽（重建後開 preview.html）
echo.
set "CHOICE=1"
set /p "CHOICE=  請選擇 [1]： "
if "%CHOICE%"=="1" set "MODE=django"
if "%CHOICE%"=="2" set "MODE=google"
if "%CHOICE%"=="3" set "MODE=preview"

:run
if /i "%MODE%"=="django"  goto django
if /i "%MODE%"=="google"  goto google
if /i "%MODE%"=="preview" goto preview
echo 不認得的選項：%MODE%
goto fail

rem ---------------------------------------------------------------
:django
where uv >nul 2>nul || (echo 找不到 uv，請先安裝：https://docs.astral.sh/uv/ & goto fail)
cd django_app
if not exist ".env" (
  copy /y ".env.example" ".env" >nul || goto fail
  echo 已從 .env.example 建立 django_app\.env。
  echo 網站可以開，但要登入請先在 .env 填好 Firebase 設定；要用 AI 建議請填 OPENAI_API_KEY。
  echo.
)
echo [1/2] 安裝套件（uv sync）...
uv sync || goto fail
echo [2/2] 啟動 Django：http://127.0.0.1:8000  （按 Ctrl+C 停止）
rem 背景等 2 秒再開瀏覽器，讓伺服器先啟動
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul & start http://127.0.0.1:8000"
uv run python manage.py runserver
goto end

rem ---------------------------------------------------------------
:google
rem 正式版已部署在 Cloud Run，直接開網址
start "" "https://ntub-course-352781737994.asia-east1.run.app/"
goto end

rem ---------------------------------------------------------------
:preview
python tools\build.py || goto fail
start "" "%~dp0preview.html"
goto end

:fail
echo.
echo 啟動失敗。
pause
exit /b 1

:end
endlocal
