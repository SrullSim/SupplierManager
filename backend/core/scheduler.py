"""
Background scheduler that periodically runs lock-time finalization and
pre-lock reminders. Started/stopped by the app lifespan.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings
from orders.finalization import run_scheduled_tasks

logger = logging.getLogger("scheduler")

_scheduler: AsyncIOScheduler | None = None


async def _tick() -> None:
    try:
        result = await run_scheduled_tasks()
        if result["finalized_deliveries"] or result["reminders_sent"]:
            logger.info("Scheduler tick: %s", result)
    except Exception as exc:  # keep the scheduler alive on errors
        logger.exception("Scheduler tick failed: %s", exc)


def start_scheduler() -> None:
    global _scheduler
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled by config.")
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(_tick, "interval", minutes=settings.scheduler_interval_minutes, id="finalize_and_remind")
    _scheduler.start()
    logger.info("Scheduler started (every %d min).", settings.scheduler_interval_minutes)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
