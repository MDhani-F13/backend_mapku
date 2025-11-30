import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
django.setup()

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler   # ⬅ ganti scheduler
from scraper_location.pipeline import run_pipeline
from scraper_location.core.logger import get_pipeline_logger


# Retrieve main logger
logger = get_pipeline_logger()

# Add console handler (avoid duplicate)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(console_handler)

# Config
PIPELINE_TIMEOUT_SECONDS = 60 * 10   # 10 minutes
INTERVAL_MINUTES = 60                # schedule repeat interval


async def safe_run_pipeline():
    try:
        logger.info("🔄 [Scheduler] Menjalankan pipeline...")
        await asyncio.wait_for(run_pipeline(), timeout=PIPELINE_TIMEOUT_SECONDS)
        logger.info("✅ [Scheduler] Pipeline selesai.")
    except asyncio.TimeoutError:
        logger.error("⏰ Pipeline timeout setelah %s detik.", PIPELINE_TIMEOUT_SECONDS)
    except Exception as e:
        logger.exception("❌ Pipeline error: %s", e)


def job():
    asyncio.create_task(safe_run_pipeline())  # ⬅ tidak lagi blocking


async def main():
    scheduler = AsyncIOScheduler()

    logger.info("🚀 Scheduler mulai — running pertama langsung...")
    job()  # run immediately

    logger.info(f"📆 Scheduler interval setiap {INTERVAL_MINUTES} menit.")
    scheduler.add_job(job, "interval", minutes=INTERVAL_MINUTES)

    scheduler.start()

    try:
        await asyncio.Event().wait()   # keep running, CTRL+C will break
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("🛑 Scheduler dihentikan oleh pengguna.")


if __name__ == "__main__":
    asyncio.run(main())
