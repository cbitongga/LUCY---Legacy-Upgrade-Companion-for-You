"""Standalone worker with bounded provider child processes and durable leases."""
import multiprocessing
import signal
import threading
import time
import uuid

from .jobs import Jobs
from .providers import ProviderError, run_review
from .store import Store

TASK_TIMEOUT_SECONDS = 60


def provider_child(connection, requirements, config):
    try:
        connection.send({"result": run_review(requirements, config)})
    except ProviderError as exc:
        connection.send({"error": str(exc)})
    except Exception:
        connection.send({"error": "Provider failed; inspect configuration. Raw error details are not retained."})
    finally:
        connection.close()


def execute(jobs, job, owner, stop, timeout=TASK_TIMEOUT_SECONDS):
    # Spawn avoids sharing SQLite connections or server state with the provider.
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=provider_child, args=(sender, job["requirements"], job["config"]), daemon=True)
    started = time.monotonic()
    heartbeat_at = started
    try:
        process.start()
        sender.close()
        while not stop.is_set():
            current = jobs.get(job["id"])
            if current["status"] != "running" or current["owner"] != owner:
                return  # Cancellation or expired ownership: discard any late response.
            if time.monotonic() - started > timeout:
                jobs.finish(job["id"], owner, error="Review exceeded the 60-second task deadline; no automatic retry")
                return
            if time.monotonic() - heartbeat_at > 5:
                if not jobs.heartbeat(job["id"], owner):
                    return
                heartbeat_at = time.monotonic()
            if receiver.poll(0.2):
                try:
                    outcome = receiver.recv()
                except EOFError:
                    outcome = {"error": "Provider process exited without a report"}
                jobs.finish(job["id"], owner, **outcome)
                return
            if not process.is_alive():
                jobs.finish(job["id"], owner, error="Provider process exited without a report")
                return
        jobs.finish(job["id"], owner, error="Worker stopped; retry requires operator action")
    finally:
        sender.close()
        receiver.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join(timeout=2)
            process.close()


def worker(root, once=False):
    stop = threading.Event()
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, lambda *_: stop.set())
    store = Store(root)
    jobs = Jobs(store)
    owner = uuid.uuid4().hex
    try:
        while not stop.is_set():
            job = jobs.claim(owner)
            if job:
                try:
                    execute(jobs, job, owner, stop)
                except Exception:
                    jobs.finish(job["id"], owner, error="Worker execution failed; retry requires operator action")
            if once:
                break
            stop.wait(1)
    finally:
        store.db.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
