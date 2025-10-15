from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import pytz
from tzlocal import get_localzone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

import pandas as pd
import streamlit as st

from src.clean.io import fetch_base_data, write_cleaned_to_db
from src.clean.cleaner import clean_base_data, to_base_filtrada_schema

# --- Zona horaria por defecto (puedes forzar "America/Mexico_City")
DEFAULT_TZ = os.environ.get("APP_TZ", "America/Mexico_City")

# --- Persistencia del scheduler (SQLite local por defecto)
# Si quieres usar Postgres para los jobs, pon la URL en APP_SCHEDULER_DB_URL
# Ejemplo: postgresql+psycopg2://user:pass@host:5432/dbname
JOBSTORE_URL = os.environ.get("APP_SCHEDULER_DB_URL", "sqlite:///scheduler_jobs.db")


@st.cache_resource(show_spinner=False)
def get_scheduler() -> BackgroundScheduler:
    """
    Singleton de APScheduler con jobstore persistente.
    """
    jobstores = {"default": SQLAlchemyJobStore(url=JOBSTORE_URL)}
    tz = pytz.timezone(DEFAULT_TZ)
    scheduler = BackgroundScheduler(jobstores=jobstores, timezone=tz)
    if not scheduler.running:
        scheduler.start(paused=False)
    return scheduler


def _cleanup_job(edo_min: int, edo_max: int, adm_min: int, adm_max: int) -> Dict[str, Any]:
    """
    Función que corre el pipeline de limpieza y sube resultados a data.base_filtrada.
    Devuelve resumen ejecutado para logging/monitoring.
    """
    raw = fetch_base_data(edo_min, edo_max, adm_min, adm_max)
    if raw.empty:
        return {"status": "no_data", "rows": 0, "edo_min": edo_min, "edo_max": edo_max,
                "adm_min": adm_min, "adm_max": adm_max}

    clean = clean_base_data(raw)
    out_db = to_base_filtrada_schema(clean)

    ok, err = write_cleaned_to_db(out_db)
    if ok:
        return {"status": "ok", "rows": len(out_db), "edo_min": edo_min, "edo_max": edo_max,
                "adm_min": adm_min, "adm_max": adm_max}
    else:
        return {"status": "error", "error": err, "rows": len(out_db),
                "edo_min": edo_min, "edo_max": edo_max, "adm_min": adm_min, "adm_max": adm_max}


def schedule_weekly_cleanup(*,
                            job_id: Optional[str],
                            day_of_week: str,
                            hour: int,
                            minute: int,
                            edo_min: int, edo_max: int,
                            adm_min: int, adm_max: int) -> str:
    """
    Programa una limpieza semanal con CronTrigger.
    day_of_week: 'sun','mon','tue','wed','thu','fri','sat' (o '0-6')
    hour/minute: hora local según DEFAULT_TZ
    Devuelve el job_id final.
    """
    scheduler = get_scheduler()

    # Si ya existe un job con ese ID, lo reemplazamos
    if job_id:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
    else:
        job_id = f"cleanup_{day_of_week}_{hour:02d}{minute:02d}_e{edo_min}-{edo_max}_a{adm_min}-{adm_max}"

    trigger = CronTrigger(
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        timezone=scheduler.timezone
    )

    scheduler.add_job(
        func=_cleanup_job,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs={
            "edo_min": int(edo_min),
            "edo_max": int(edo_max),
            "adm_min": int(adm_min),
            "adm_max": int(adm_max),
        },
        misfire_grace_time=3600,   # 1h de tolerancia si la app estaba caída
        coalesce=True,             # junta ejecuciones perdidas en una
        max_instances=1,           # evita solapamientos
    )
    return job_id


def list_jobs() -> List[Dict[str, Any]]:
    """
    Lista los jobs programados.
    """
    scheduler = get_scheduler()
    out = []
    for j in scheduler.get_jobs():
        next_run = j.next_run_time.astimezone(scheduler.timezone) if j.next_run_time else None
        data = {
            "job_id": j.id,
            "next_run_time": next_run,
            "trigger": str(j.trigger),
        }
        # extrae kwargs que nos interesan
        try:
            data.update({
                "edo_min": j.kwargs.get("edo_min"),
                "edo_max": j.kwargs.get("edo_max"),
                "adm_min": j.kwargs.get("adm_min"),
                "adm_max": j.kwargs.get("adm_max"),
            })
        except Exception:
            pass
        out.append(data)
    return out


def remove_job(job_id: str) -> bool:
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception:
        return False


def run_job_now(job_id: str) -> bool:
    """
    Dispara una ejecución inmediata del job existente (sincronizando el next_run_time a ahora).
    """
    scheduler = get_scheduler()
    try:
        scheduler.modify_job(job_id, next_run_time=datetime.now(scheduler.timezone))
        return True
    except Exception:
        return False


def run_ad_hoc_once(edo_min: int, edo_max: int, adm_min: int, adm_max: int) -> Dict[str, Any]:
    """
    Ejecuta una limpieza ad-hoc inmediata (sin crear job recurrente).
    """
    return _cleanup_job(edo_min, edo_max, adm_min, adm_max)
