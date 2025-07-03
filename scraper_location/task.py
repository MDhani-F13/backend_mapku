from celery import shared_task
import asyncio
from scraper_location.pipeline import run_pipeline

@shared_task
def scheduled_scraping():
    """
    Dipanggil otomatis oleh Celery Beat.
    Menjalankan scraper + preprocessing pipeline.
    """
    print("[TASK] 🔄 Running scheduled scraping pipeline...")
    asyncio.run(run_pipeline())
    print("[TASK] ✅ Scheduled scraping finished.")