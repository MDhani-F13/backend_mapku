import os, json, logging, asyncio, signal, time, django

# ───────────────────────────────
# Django boot
# ───────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
django.setup()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper_location.pipeline import run_pipeline
from scraper_location.core.logger import get_pipeline_logger

logger = get_pipeline_logger()

STATE_FILE = "scheduler_state.json"
INTERVAL_HOURS = 0.5
MAX_RETRIES = 3  


# ───────────────────────────────
# State manager
# ───────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"last_query_index": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ───────────────────────────────
# Pipeline runner + auto restart
# ───────────────────────────────
async def run_with_retry():
    state = load_state()
    idx = state["last_query_index"]

    from scraper_location.pipeline import ALL_QUERIES
    query = [ALL_QUERIES[idx]]

    logger.info(f"🔄 Running pipeline for query #{idx+1}: {query[0]}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await run_pipeline(queries=query)
            logger.info("✅ Pipeline completed successfully")

            state["last_query_index"] = (idx + 1) % len(ALL_QUERIES)
            save_state(state)
            return

        except Exception as e:
            logger.error(f"❌ Error attempt {attempt}/{MAX_RETRIES} → {e}")

            if attempt < MAX_RETRIES:
                wait = 10 * attempt
                logger.info(f"🔁 Restarting in {wait}s...")
                await asyncio.sleep(wait)
            else:
                logger.critical("🚨 Pipeline FAILED even after auto retries!")
                return


# ───────────────────────────────
# Safe shutdown
# ───────────────────────────────
def shutdown(sig, frame):
    logger.warning("🛑 Shutdown requested → Stopping scheduler ...")
    try:
        scheduler.shutdown()
    except Exception:
        pass
    raise SystemExit(0)


# ───────────────────────────────
# Scheduler start
# ───────────────────────────────
scheduler = AsyncIOScheduler()
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

async def main():
    logger.info("🚀 Scheduler started — running first query now...")
    await run_with_retry()

    logger.info(f"⏳ Next jobs will run every {INTERVAL_HOURS} hours")

    scheduler.add_job(
        run_with_retry,
        "interval",
        hours=INTERVAL_HOURS,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    logger.info("📌 Press CTRL + C to stop scheduler")

    # ✅ LOOP ASYNC AGAR TIDAK MATI
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
