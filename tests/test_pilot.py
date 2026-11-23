import unittest

from pilot import DEMOS, GOALS, guess, load, race, split


class PilotTests(unittest.TestCase):
    def test_data_and_split(self):
        self.assertEqual(len(load()), 93)
        history, test = split(491)
        self.assertIn(len(test), (20, 21))
        self.assertEqual(len(history) + len(test), 93)
        self.assertFalse({row["idX"] for row in history} & {row["idX"] for row in test})

    def test_estimate_ignores_actual_held_out_goals(self):
        history, test = split(491)
        altered = dict(test[0], **dict.fromkeys(GOALS, 999_999))
        self.assertEqual(guess(history, test), guess(history, [altered]))

    def test_all_demos(self):
        for seed in (491, 492, 493):
            for name, demo in DEMOS.items():
                with self.subTest(seed=seed, skill=name):
                    self.assertTrue(demo(*split(seed)))

    def test_race_has_equal_review_budgets(self):
        result = race(*split(491))
        for hits in result["hits"].values():
            self.assertIn(hits, range(result["review_budget"] + 1))
