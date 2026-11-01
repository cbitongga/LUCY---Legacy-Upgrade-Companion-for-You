import tempfile
import time
import subprocess
import sys
from pathlib import Path
from lucy.delegation import plan
import unittest

from lucy.activity import project_activity
from lucy.engine import Engine, digest
from lucy.jobs import Jobs
from lucy.providers import run_review
from lucy.store import Store


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.engine = Engine(self.store)
        self.jobs = Jobs(self.store)
        self.project = self.engine.start_interview('Activity test')

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def activity(self, **kwargs):
        return project_activity(self.store.get(self.project['id']), self.jobs.list(self.project['id']), **kwargs)

    def enqueue(self):
        return self.jobs.enqueue(self.project['id'], 'offline', digest(self.project['requirements']), 'activity-review')

    def test_planning_is_not_fake_execution(self):
        activity = self.activity()
        self.assertEqual(len(activity['agents']), 18)
        self.assertEqual(activity['counts']['working'], 0)
        self.assertEqual(activity['workflow']['remaining'], 3)
        self.assertIsNone(activity['migration_remaining_steps'])

    def test_real_checkpoints_and_ownership(self):
        job = self.enqueue()
        self.assertEqual(self.activity()['workflow']['remaining'], 4)
        claimed = self.jobs.claim('worker')
        activity = self.activity()
        self.assertEqual(activity['workflow']['remaining'], 3)
        self.assertEqual([a['id'] for a in activity['agents'] if a['status'] == 'working'], ['interviewer'])
        self.assertFalse(self.jobs.advance(job['id'], 'other', 'validating'))
        with self.assertRaises(ValueError):
            self.jobs.advance(job['id'], 'worker', 'saving')
        self.assertTrue(self.jobs.advance(job['id'], 'worker', 'validating'))
        self.assertEqual(self.activity()['workflow']['remaining'], 2)
        self.assertTrue(self.jobs.advance(job['id'], 'worker', 'saving'))
        self.assertEqual(self.activity()['workflow']['remaining'], 1)
        self.jobs.finish(job['id'], 'worker', result=run_review(claimed['requirements'], claimed['config']))
        self.assertEqual(self.activity()['workflow']['remaining'], 0)
        self.assertEqual(self.activity()['counts']['working'], 0)
        self.engine.interview(self.project['id'], {'target': 'New target'})
        self.assertFalse(self.activity()['workflow']['current_contract'])
        self.assertEqual(self.activity()['counts']['stale'], 4)

    def test_stopped_work_and_retry_never_show_false_completion(self):
        job = self.enqueue()
        self.jobs.control(job['id'], 'pause')
        self.assertEqual(self.activity()['counts']['paused'], 1)
        self.jobs.control(job['id'], 'resume')
        self.jobs.claim('worker')
        expired = self.activity(timestamp=time.time() + 1000)
        self.assertEqual(expired['counts']['working'], 0)
        self.assertEqual(expired['counts']['interrupted'], 1)
        self.jobs.finish(job['id'], 'worker', error='test failure')
        self.assertEqual(self.activity()['workflow']['remaining'], 3)
        self.assertEqual(self.activity()['counts']['failed'], 1)
        self.jobs.control(job['id'], 'retry')
        self.assertEqual(self.activity()['workflow']['remaining'], 4)
        self.jobs.claim('worker')
        self.jobs.control(job['id'], 'cancel')
        self.assertFalse(self.jobs.advance(job['id'], 'worker', 'validating'))
        self.assertEqual(self.activity()['counts']['working'], 0)
        self.assertEqual(self.activity()['counts']['cancelled'], 1)

    def test_decomposition_covers_contract_once_and_adapts(self):
        from lucy.agents import QUESTIONNAIRE
        base = plan(self.project['requirements'])
        self.assertEqual(len(base), 3)
        supplied = {'version': 2, 'answers': {'security': 'SSO', 'deployment': 'On premise'}}
        detailed = plan(supplied)
        self.assertEqual(len(detailed), 5)
        keys = [key for child in detailed for key in child['keys']]
        self.assertCountEqual(keys, [q[0] for q in QUESTIONNAIRE])
        self.assertEqual(len(keys), len(set(keys)))

    def test_delegated_worker_persists_children_and_totals(self):
        job = self.jobs.enqueue(self.project['id'], 'offline', digest(self.project['requirements']), 'delegated-job', delegate=True)
        self.assertEqual(self.activity()['subagent_count'], 3)
        self.assertEqual(self.activity()['workflow']['remaining'], 6)
        result = subprocess.run([sys.executable, '-m', 'lucy', '--data', self.temp.name, 'worker', '--once'],
                                cwd=Path(__file__).resolve().parent.parent, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        job = self.jobs.detail(job['id'])
        self.assertEqual(job['status'], 'completed')
        self.assertTrue(all(c['status'] == 'completed' and c['result'] for c in job['children']))
        self.assertEqual(len(job['result']['report']['questions']), 12)
        self.assertEqual(self.activity()['workflow']['remaining'], 0)
        self.assertEqual(self.activity()['counts']['working'], 0)
        self.assertEqual(len(job['events']), 11)

    def test_child_cancel_lease_and_retry_projection(self):
        job = self.jobs.enqueue(self.project['id'], 'offline', digest(self.project['requirements']), 'delegated-job', delegate=True)
        self.jobs.claim('one')
        self.assertFalse(self.jobs.child_update(job['id'], 'other', 'scope'))
        self.assertTrue(self.jobs.child_update(job['id'], 'one', 'scope'))
        self.assertEqual(self.activity()['counts']['working'], 1)
        self.assertEqual(self.activity()['subagents'][0]['status'], 'working')
        with self.assertRaises(ValueError):
            self.jobs.child_update(job['id'], 'one', 'behavior')
        self.assertEqual(self.activity(timestamp=time.time()+1000)['subagents'][0]['status'], 'interrupted')
        self.jobs.finish(job['id'], 'one', error='test failure')
        self.assertEqual(self.activity()['subagents'][0]['status'], 'failed')
        self.jobs.control(job['id'], 'retry')
        self.assertEqual(self.activity()['workflow']['remaining'], 6)
        self.jobs.claim('one')
        self.jobs.child_update(job['id'], 'one', 'scope')
        self.jobs.control(job['id'], 'cancel')
        self.assertFalse(self.jobs.child_update(job['id'], 'one', 'scope', {'report': {}}))
        self.assertEqual(self.activity()['counts']['working'], 0)
        self.assertTrue(all(c['status'] == 'cancelled' for c in self.activity()['subagents']))
