import asyncio
from pipeline import run_pipeline

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    asyncio.run(run_pipeline())