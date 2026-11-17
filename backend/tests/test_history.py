import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app.main import summarize
from app.models.summarize import SummarizeRequest
from app.routes.history import delete_all_history, delete_history_entry, history, history_entry
from app.services.gemini import GeminiServiceError


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / "history.sqlite3"
        self.database_setting = patch.dict(os.environ, {"HISTORY_DB_PATH": str(self.database)})
        self.database_setting.start()

    def tearDown(self):
        self.database_setting.stop()
        self.directory.cleanup()

    def test_successful_summaries_persist_once_and_can_be_retrieved(self):
        with patch("app.main.summarize_text", return_value="First summary"):
            summarize(SummarizeRequest(text=" First source text ", length="short"))
        with patch("app.main.summarize_with_ollama", return_value="Second summary"):
            summarize(SummarizeRequest(text="Second source text", length="short", provider="ollama"))

        entries = history()
        self.assertEqual(len(entries), 2)
        self.assertEqual([entry["original_text"] for entry in entries], ["Second source text", "First source text"])
        self.assertEqual(entries[0]["summary_text"], "Second summary")
        self.assertEqual(entries[0]["summary_length"], "short")
        self.assertEqual(entries[0]["provider"], "ollama")
        self.assertEqual(entries[0]["original_word_count"], 3)
        self.assertEqual(entries[0]["summary_word_count"], 2)
        self.assertTrue(entries[0]["created_at"])
        self.assertEqual(history_entry(entries[0]["id"]), entries[0])
        self.assertTrue(self.database.exists())

    def test_failed_summary_is_not_saved(self):
        with patch("app.main.summarize_text", side_effect=GeminiServiceError("test failure")):
            with self.assertRaises(HTTPException):
                summarize(SummarizeRequest(text="A source"))
        self.assertEqual(history(), [])

    def test_delete_one_and_clear_history(self):
        with patch("app.main.summarize_text", return_value="Summary"):
            summarize(SummarizeRequest(text="First source"))
            summarize(SummarizeRequest(text="Second source"))
        entries = history()

        self.assertEqual(delete_history_entry(entries[0]["id"]).status_code, 204)
        with self.assertRaises(HTTPException) as missing:
            history_entry(entries[0]["id"])
        self.assertEqual(missing.exception.status_code, 404)
        self.assertEqual(len(history()), 1)
        self.assertEqual(delete_all_history().status_code, 204)
        self.assertEqual(history(), [])


if __name__ == "__main__":
    unittest.main()
