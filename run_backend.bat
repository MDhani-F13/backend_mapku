@echo off
title Backend Mapku - Django + Celery + Redis

REM Aktifkan virtual environment (karena venv berada di luar folder ini)
call ..\venv_backend\Scripts\activate

REM Buka terminal untuk Redis
start cmd /k redis-server

REM Buka terminal untuk Celery Worker
start cmd /k celery -A backend_mapku worker --loglevel=info --pool=solo

REM Buka terminal untuk Celery Beat
start cmd /k celery -A backend_mapku beat --loglevel=info

REM Jalankan Django Server di terminal utama
python manage.py runserver 0.0.0.0:8000

pause

