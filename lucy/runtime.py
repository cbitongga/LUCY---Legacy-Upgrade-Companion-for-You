"""Standalone worker with bounded provider child processes and durable leases."""
import multiprocessing
import signal
import threading
import time
import uuid

from .jobs import Jobs
from .providers import ProviderError, run_review, validate_report
from .store import Store
from .delegation import merge

TASK_TIMEOUT_SECONDS = 60


def provider_child(connection, requirements, config, assignment=None):
    try:
        connection.send({"result": run_review(requirements, config, assignment)})
    except ProviderError as exc:
        connection.send({"error": str(exc)})
    except Exception:
        connection.send({"error": "Provider failed; inspect configuration. Raw error details are not retained."})
    finally:
        connection.close()


def execute_one(jobs, job, owner, stop, timeout=TASK_TIMEOUT_SECONDS, assignment=None):
    # Spawn avoids sharing SQLite connections or server state with the provider.
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=provider_child, args=(sender, job["requirements"], job["config"], assignment), daemon=True)
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
                if assignment is not None and "result" in outcome:
                    validate_report(outcome["result"]["report"])
                    return outcome["result"]
                if "result" in outcome:
                    if not jobs.advance(job["id"], owner, "validating"):
                        return
                    validate_report(outcome["result"]["report"])
                    if not jobs.advance(job["id"], owner, "saving"):
                        return
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


def execute(jobs, job, owner, stop, timeout=TASK_TIMEOUT_SECONDS):
    if not job.get('delegate'):
        return execute_one(jobs, job, owner, stop, timeout)
    for child in job['children']:
        if not jobs.child_update(job['id'], owner, child['id']):
            return
        assignment = {key: child[key] for key in ('id', 'name', 'keys', 'objective', 'reason')}
        result = execute_one(jobs, job, owner, stop, timeout, assignment)
        if result is None or not jobs.child_update(job['id'], owner, child['id'], result):
            return
    current = jobs.get(job['id'])
    if not jobs.advance(job['id'], owner, 'validating'):
        return
    result = merge(current['children'], job['provider'], job['config']['model'])
    validate_report(result['report'])
    if jobs.advance(job['id'], owner, 'saving'):
        jobs.finish(job['id'], owner, result=result)


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
