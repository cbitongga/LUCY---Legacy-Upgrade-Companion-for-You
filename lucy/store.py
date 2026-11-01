import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "lucy.sqlite3")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), at TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), sha256 TEXT NOT NULL, body TEXT NOT NULL);
        """)

    def save(self, project, event, artifacts=None):
        # Checkpoint, audit event and evidence commit together. Artifacts are immutable.
        with self.db:
            self.db.execute("INSERT INTO projects VALUES(?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body", (project["id"], json.dumps(project)))
            for key, body in (artifacts or {}).items():
                raw = json.dumps(body, sort_keys=True)
                digest = hashlib.sha256(raw.encode()).hexdigest()
                self.db.execute("INSERT INTO evidence VALUES(?,?,?,?)", (key, project["id"], digest, raw))
            self.db.execute("INSERT INTO events(project_id,at,body) VALUES(?,?,?)", (project["id"], now(), json.dumps(event)))

    def get(self, project_id):
        row = self.db.execute("SELECT body FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise KeyError("Project not found")
        return json.loads(row[0])

    def projects(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT body FROM projects ORDER BY rowid DESC")]

    def evidence(self, project_id):
        return [{"id": key, "sha256": digest, "body": json.loads(raw)} for key, digest, raw in self.db.execute("SELECT id,sha256,body FROM evidence WHERE project_id=? ORDER BY rowid", (project_id,))]

    def events(self, project_id):
        return [{"sequence": seq, "at": at, **json.loads(body)} for seq, at, body in self.db.execute("SELECT seq,at,body FROM events WHERE project_id=? ORDER BY seq", (project_id,))]
