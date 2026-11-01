import functools
from django.core.cache import cache


def single_instance_task(timeout):
    """
    Only one instance of the task runs at a time (across workers, the lock is in the shared cache).
    A call made while it's running isn't dropped: it marks the task as pending and the running instance runs once more
    when done, so e.g. two torrents finishing close together are both processed. Pending calls are coalesced.
    """
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            pending_id = "celery-single-instance-pending-" + func.__name__
            # Set before trying the lock: either we get the lock, or the holder sees the flag after its run.
            cache.set(pending_id, "true", timeout)
            while cache.get(pending_id):
                if not cache.add(lock_id, "true", timeout):
                    return
                try:
                    cache.delete(pending_id)
                    func(*args, **kwargs)
                finally:
                    cache.delete(lock_id)
        return wrapper
    return task_exc