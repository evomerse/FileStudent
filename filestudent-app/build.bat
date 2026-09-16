@echo off
REM Construit FileStudent.exe sur Windows (ticket APP-14).
REM Prerequis : Python 3.10 ou plus recent installe et sur le PATH.

setlocal
cd /d %~dp0

if not exist .venv-build (
    python -m venv .venv-build
)
call .venv-build\Scripts\activate.bat

pip install --upgrade pip
pip install -e ".[build]"

pyinstaller filestudent.spec --noconfirm

echo.
echo Build terminee : dist\FileStudent.exe
pause
