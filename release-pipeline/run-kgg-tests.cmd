@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-kgg-tests.ps1" %*
exit /b %ERRORLEVEL%
