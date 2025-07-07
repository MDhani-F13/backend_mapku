import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
django.setup()

from apscheduler.schedulers.blocking import BlockingScheduler
import asyncio
from scraper_location.pipeline import run_pipeline



def job():
    print("🔄 [SCHEDULER] Menjalankan pipeline...")
    asyncio.run(run_pipeline())
    print("✅ [SCHEDULER] Pipeline selesai.\n")

def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'interval', minutes=30)
    print("✅ APScheduler dimulai (tiap 30 menit). Tekan CTRL+C untuk stop.")
    scheduler.start()

if __name__ == "__main__":
    main()