import tempfile
import time
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
