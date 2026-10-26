import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from progress import build_progress, attach_plan


def game(deaths=2.0, win=True, role='MIDDLE', gold_gap=0, kp=60, vision=0.9, share=25, dpm=700):
    return {'win': win, 'role': role, 'duration_min': 28, 'deaths_per_10': deaths, 'kill_participation': kp, 'vision_per_min': vision,
            'damage_share': share, 'damage_per_min': dpm, 'timeline': [{'minute': 10, 'gold_gap': gold_gap}]}


class ProgressTests(unittest.TestCase):
    def test_fewer_games_than_two_periods_is_insufficient(self):
        games = [game(deaths=6) for _ in range(8)]
        top = build_progress(games)['priority']
        self.assertEqual(top['key'], 'deaths')
        self.assertEqual(top['trend'], 'insufficient')

    def test_recent_games_come_first_and_improvement_is_detected_even_with_zero_recent_problems(self):
        recent = [game(deaths=2) for _ in range(10)]
        previous = [game(deaths=7) for _ in range(6)] + [game(deaths=2) for _ in range(4)]
        top = build_progress(recent + previous)['priority']
        self.assertEqual(top['key'], 'deaths')
        self.assertEqual(top['trend'], 'improving')
        self.assertEqual((top['recent']['flagged'], top['recent']['applicable']), (0, 10))
        self.assertEqual((top['previous']['flagged'], top['previous']['applicable']), (6, 10))

    def test_worsening_and_stable(self):
        worse = [game(deaths=7) for _ in range(6)] + [game() for _ in range(4)] + [game() for _ in range(10)]
        self.assertEqual(build_progress(worse)['priority']['trend'], 'worsening')
        same = [game(deaths=7) for _ in range(3)] + [game() for _ in range(7)]
        self.assertEqual(build_progress(same + same)['priority']['trend'], 'stable')

    def test_no_priority_below_three_flagged_games(self):
        games = [game(deaths=7), game(deaths=7)] + [game() for _ in range(18)]
        result = build_progress(games)
        self.assertIsNone(result['priority'])
        self.assertEqual(result['others'][0]['key'], 'deaths')

    def test_priority_is_signal_with_most_flagged_games(self):
        games = [game(deaths=7, vision=0.2) for _ in range(4)] + [game(vision=0.2) for _ in range(4)] + [game() for _ in range(12)]
        self.assertEqual(build_progress(games)['priority']['key'], 'vision')

    def test_winrate_comparison_needs_five_games_in_each_group(self):
        games = [game(deaths=7, win=False) for _ in range(5)] + [game(win=True) for _ in range(15)]
        self.assertIn('Winrate : 0 %', build_progress(games)['priority']['evidence'])
        few = [game(deaths=7, win=False) for _ in range(3)] + [game(win=True) for _ in range(17)]
        self.assertNotIn('Winrate', build_progress(few)['priority']['evidence'])

    def test_support_is_excluded_from_participation_and_damage(self):
        games = [game(role='UTILITY', kp=20, share=5, dpm=200) for _ in range(20)]
        result = build_progress(games)
        keys = {o['key'] for o in result['others']} | ({result['priority']['key']} if result['priority'] else set())
        self.assertNotIn('participation', keys)
        self.assertNotIn('damage', keys)

    def test_attach_plan_replaces_only_the_plan_tab_and_escapes_text(self):
        html = '<div id="overview"></div><div id="plan" class="tab-panel" hidden>ancien</div>\n<div id="matchups">suite</div>'
        games = [game(deaths=7) for _ in range(6)] + [game() for _ in range(14)]
        progress = build_progress(games)
        progress['priority']['title'] = '<b>x</b>'
        out = attach_plan(html, progress)
        self.assertIn('<div id="overview"></div>', out)
        self.assertIn('<div id="matchups">suite</div>', out)
        self.assertNotIn('ancien', out)
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', out)
        self.assertIn('Parties concernées · récentes', out)
        self.assertIn('hidden>', out)


if __name__ == '__main__':
    unittest.main()
