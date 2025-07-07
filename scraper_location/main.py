import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
django.setup()

import asyncio
from scraper_location.pipeline import run_pipeline

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    asyncio.run(run_pipeline())