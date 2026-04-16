import threading
import time

import schedule

from app.canvas import sync_canvas


_scheduler_started = False
_scheduler_lock = threading.Lock()


def run_scheduler(interval_minutes=60):
    def job():
        print("Running Canvas sync...")

        # run the canvas sync on the schedule
        try:
            result = sync_canvas()
            print("Sync completed")
        except Exception as e:
            print("sync failed:", e)

    job()  # run immediately on startup

    # register the repeating sync job
    schedule.every(interval_minutes).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    global _scheduler_started

    # prevent multiple scheduler threads on streamlit reruns
    with _scheduler_lock:
        if _scheduler_started:
            return

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        _scheduler_started = True
