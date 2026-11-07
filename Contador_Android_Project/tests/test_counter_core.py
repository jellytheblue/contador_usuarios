import json
import tempfile
import unittest
from pathlib import Path

from counter_core import default_data, normalize_data, load_data, save_data, count_users, reset_if_due


class CounterCoreTests(unittest.TestCase):
    def test_counts_all_groups(self):
        data = default_data()
        data["groups"][0]["users"] = [
            {"id": "1", "name": "A", "active": True},
            {"id": "2", "name": "B", "active": False},
        ]
        data["groups"].append({"id": "g2", "name": "Otro", "users": [
            {"id": "3", "name": "C", "active": True}
        ]})
        self.assertEqual(count_users(data), (2, 3))

    def test_reset_every_group_and_preserve_schedule(self):
        data = default_data()
        due = data["next_reset_at"]
        data["groups"][0]["users"] = [{"id": "1", "name": "A", "active": True}]
        data["groups"].append({"id": "g2", "name": "Otro", "users": [
            {"id": "2", "name": "B", "active": True}
        ]})
        self.assertTrue(reset_if_due(data, now=due + 1))
        self.assertEqual(count_users(data), (0, 2))
        self.assertGreater(data["next_reset_at"], due + 1)
        self.assertFalse(reset_if_due(data, now=due + 2))

    def test_json_round_trip(self):
        data = default_data()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            save_data(path, data)
            loaded, warning = load_data(path)
            self.assertIsNone(warning)
            self.assertEqual(loaded["selected_group_id"], data["selected_group_id"])

    def test_normalization_discards_invalid_user_rows(self):
        data = default_data()
        data["groups"][0]["users"] = [None, {"name": "A"}]
        cleaned = normalize_data(data)
        self.assertEqual(len(cleaned["groups"][0]["users"]), 1)
        self.assertIn("id", cleaned["groups"][0]["users"][0])


if __name__ == "__main__":
    unittest.main()
