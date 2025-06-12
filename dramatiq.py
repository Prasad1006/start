import dramatiq
from backend.tasks import redis_broker

# This line ensures the worker process knows about your tasks file.
from backend import tasks

dramatiq.set_broker(redis_broker)