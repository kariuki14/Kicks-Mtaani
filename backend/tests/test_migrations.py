import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "97dffbc771e7"
HEAD_REVISION = "378eafb063ce"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{self.db_path}",
        }

    def tearDown(self):
        self._tmpdir.cleanup()

    def _alembic(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND_DIR,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def _run_alembic(self, *args):
        result = self._alembic(*args)
        self.assertEqual(
            result.returncode,
            0,
            msg=f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}",
        )
        return result

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def test_upgrade_head_creates_current_schema(self):
        self._run_alembic("upgrade", "head")

        with self._connect() as con:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            columns = {row[1] for row in con.execute("PRAGMA table_info(products)")}
            version = con.execute("SELECT version_num FROM alembic_version").fetchone()

        self.assertIn("users", tables)
        self.assertIn("products", tables)
        self.assertIn("alembic_version", tables)
        self.assertTrue({"size", "condition", "colorway"} <= columns)
        self.assertEqual(version, (HEAD_REVISION,))

    def test_stamp_then_upgrade_preserves_existing_schema(self):
        self._run_alembic("upgrade", BASELINE_REVISION)

        with self._connect() as con:
            # Simulate a pre-Alembic database: schema exists, no version table.
            con.execute("DROP TABLE alembic_version")
            con.execute(
                "INSERT INTO products (name, category, price, in_stock) "
                "VALUES ('Existing', 'Shoes', 100, 1)"
            )

        self._run_alembic("stamp", BASELINE_REVISION)
        self._run_alembic("upgrade", "head")

        with self._connect() as con:
            columns = {row[1] for row in con.execute("PRAGMA table_info(products)")}
            product_count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            version = con.execute("SELECT version_num FROM alembic_version").fetchone()

        self.assertTrue({"size", "condition", "colorway"} <= columns)
        self.assertEqual(product_count, 1)
        self.assertEqual(version, (HEAD_REVISION,))

    def test_model_metadata_matches_head(self):
        self._run_alembic("upgrade", "head")
        self._run_alembic("check")
        self._run_alembic("downgrade", "base")

        with self._connect() as con:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        self.assertEqual(tables, {"alembic_version"})


if __name__ == "__main__":
    unittest.main()
