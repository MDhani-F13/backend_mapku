import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
django.setup()

import asyncio
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from scraper_location.pipeline import run_pipeline
from scraper_location.core.logger import get_pipeline_logger



# Retrieve main logger
logger = get_pipeline_logger()

# Add console handler (scheduler only)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

# Avoid duplicate console logs
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(console_handler)

# Config
PIPELINE_TIMEOUT_SECONDS = 60 * 10   # 10 min
INTERVAL_MINUTES = 30                # interval


async def safe_run_pipeline():
    """Run pipeline safely with timeout + logging."""
    try:
        logger.info("🔄 [Scheduler] Menjalankan pipeline...")
        await asyncio.wait_for(run_pipeline(), timeout=PIPELINE_TIMEOUT_SECONDS)
        logger.info("✅ [Scheduler] Pipeline selesai.")

    except asyncio.TimeoutError:
        logger.error("⏰ Pipeline timeout setelah %s detik.", PIPELINE_TIMEOUT_SECONDS)

    except Exception as e:
        logger.exception("❌ Pipeline error: %s", e)


def job():
    asyncio.run(safe_run_pipeline())


def main():
    scheduler = BlockingScheduler()

    logger.info("🚀 Scheduler start — menjalankan pipeline pertama kali...")
    job()  # immediate run

    logger.info("📆 Scheduler interval dimulai (%s menit).", INTERVAL_MINUTES)
    scheduler.add_job(job, "interval", minutes=INTERVAL_MINUTES)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler dihentikan oleh pengguna.")


if __name__ == "__main__":
    main()
