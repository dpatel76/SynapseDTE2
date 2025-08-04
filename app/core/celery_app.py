"""
Celery application configuration for background tasks
"""
import os
from celery import Celery
from kombu import Exchange, Queue
from app.core.config import settings

# Create Celery app
celery_app = Celery('synapse_dte')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Define task queues
celery_app.conf.task_routes = {
    'app.tasks.llm.*': {'queue': 'llm'},
    'app.tasks.reports.*': {'queue': 'reports'},
    'app.tasks.notifications.*': {'queue': 'notifications'},
    'app.tasks.data_processing.*': {'queue': 'data_processing'},
    'app.tasks.testing.*': {'queue': 'testing'},
}

# Define exchanges and queues
default_exchange = Exchange('default', type='direct')
llm_exchange = Exchange('llm', type='direct')
reports_exchange = Exchange('reports', type='direct')

celery_app.conf.task_queues = (
    Queue('celery', default_exchange, routing_key='celery'),
    Queue('llm', llm_exchange, routing_key='llm'),
    Queue('reports', reports_exchange, routing_key='reports'),
    Queue('notifications', default_exchange, routing_key='notifications'),
    Queue('data_processing', default_exchange, routing_key='data_processing'),
    Queue('testing', default_exchange, routing_key='testing'),
)

# Default queue
celery_app.conf.task_default_queue = 'celery'
celery_app.conf.task_default_exchange = 'default'
celery_app.conf.task_default_exchange_type = 'direct'
celery_app.conf.task_default_routing_key = 'celery'

# Import task modules
celery_app.conf.imports = [
    'app.tasks.data_profiling_tasks',
    'app.tasks.test_execution_tasks',
    # Temporarily disabled due to import errors
    # 'app.tasks.llm_tasks',
    # 'app.tasks.report_tasks',
    # 'app.tasks.notification_tasks',
    # 'app.tasks.data_processing_tasks',
    # 'app.tasks.testing_tasks',
]

# Beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Check SLA violations every 15 minutes
    'check-sla-violations': {
        'task': 'app.tasks.sla_tasks.check_sla_violations',
        'schedule': crontab(minute='*/15'),
    },
    # Send daily digest emails at 8 AM UTC
    'send-daily-digest': {
        'task': 'app.tasks.notification_tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),
    },
    # Clean up old tasks daily at 2 AM UTC
    'cleanup-old-tasks': {
        'task': 'app.tasks.maintenance_tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),
    },
    # Generate metrics reports weekly on Monday at 9 AM UTC
    'generate-weekly-metrics': {
        'task': 'app.tasks.report_tasks.generate_weekly_metrics',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}

# Celery signals for monitoring
from celery.signals import task_prerun, task_postrun, task_failure
import logging

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log when a task starts"""
    logger.info(f"Task {task.name} [{task_id}] started")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
    """Log when a task completes"""
    logger.info(f"Task {task.name} [{task_id}] completed with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Log task failures"""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")

# Initialize Celery app when module is imported
if __name__ == '__main__':
    celery_app.start()