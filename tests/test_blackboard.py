import unittest

from shared.blackboard import Blackboard

class TestBlackboard(unittest.TestCase):

    def setUp(self):
        self.blackboard = Blackboard()

    def test_set_and_get(self):
        self.blackboard.set("key1", "value1")
        self.assertEqual(self.blackboard.get("key1"), "value1")

    def test_get_non_existent_key(self):
        self.assertIsNone(self.blackboard.get("non_existent_key"))

    def test_get_with_default(self):
        self.assertEqual(self.blackboard.get("non_existent_key", "default_value"), "default_value")

if __name__ == "__main__":
    unittest.main()
