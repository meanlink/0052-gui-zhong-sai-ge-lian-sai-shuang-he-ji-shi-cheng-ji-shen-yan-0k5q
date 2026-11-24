from pathlib import Path

from fastapi import APIRouter
from seals_api import router as seals
from handoffs_api import router as handoffs
from bench_api import router as bench
from finishes_api import router as finishes
from standings_api import router as standings
from clock_jobs import run_job

router = APIRouter(prefix="/api")
router.include_router(seals)
router.include_router(handoffs)
router.include_router(bench)
router.include_router(finishes)
router.include_router(standings)


def seed(connection):
    connection.execute(Path(__file__).with_name("demo.sql").read_text())
