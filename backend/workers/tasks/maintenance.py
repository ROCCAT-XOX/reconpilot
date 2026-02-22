import logging
import subprocess

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="maintenance.cleanup_results")
def cleanup_expired_results():
    """Clean up expired Celery task results from Redis."""
    try:
        backend = celery_app.backend
        if hasattr(backend, "cleanup"):
            backend.cleanup()
            logger.info("Celery result cleanup completed")
        else:
            logger.info("Backend does not support cleanup, skipping")
    except Exception as e:
        logger.error(f"Result cleanup failed: {e}")


@celery_app.task(name="maintenance.database_backup")
def database_backup():
    """Run the database backup script."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["/app/scripts/backup.sh"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            logger.info(f"Database backup completed: {result.stdout.strip()}")
        else:
            logger.error(f"Database backup failed: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        logger.error("Database backup timed out after 600s")
    except FileNotFoundError:
        logger.warning("Backup script not found at /app/scripts/backup.sh")
    except Exception as e:
        logger.error(f"Database backup error: {e}")
