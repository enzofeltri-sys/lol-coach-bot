import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from debrief import build_debrief, render_debrief, attach_debriefs
from progress import SIGNALS

EXERCISES = {s['key']: s['exercise'] for s in SIGNALS}


def game(decisive='none', deaths_per_10=3.0, deaths=3, kp=50, role='MIDDLE', vision=0.9, share=25, dpm=700, gold_gap=0):
    base = {'win': True, 'role': role, 'duration_min': 28, 'deaths': deaths, 'deaths_per_10': deaths_per_10, 'kill_participation': kp,
            'vision_per_min': vision, 'damage_share': share, 'damage_per_min': dpm, 'opponent_champion': 'Mel',
            'timeline': [{'minute': 10, 'gold_gap': gold_gap}]}
    base['decisive_moments'] = {'early_death': None, 'first_disadvantage': None, 'vision_before_objective': [], 'advantage_conversion': None, 'advice': []} if decisive == 'none' else decisive
    return base


def full_decisive():
    return {'early_death': {'minute': 8.0, 'type': 'death'}, 'first_disadvantage': {'minute': 5.0, 'metric': 'CS', 'gap': -22},
            'vision_before_objective': [], 'advantage_conversion': {'lead': 450, 'next_gold_gap': 100, 'status': 'lost'}, 'advice': []}


class DebriefTests(unittest.TestCase):
    def test_moments_are_limited_to_three_and_sorted_by_minute(self):
        d = build_debrief(game(full_decisive()))
        self.assertEqual([m['minute'] for m in d['moments']], [5.0, 8.0, 10.0])
        self.assertIn('-22 CS', d['moments'][0]['fact'])
        self.assertIn('face à Mel', d['moments'][0]['fact'])
        self.assertIn('+450 or', d['moments'][2]['fact'])
        self.assertTrue(all(m['question'] for m in d['moments']))

    def test_main_point_is_highest_priority_moment_and_action_matches(self):
        d = build_debrief(game(full_decisive()))
        self.assertEqual(d['main']['title'], SIGNAL_BY_KEY_TITLE('deaths'))
        self.assertEqual(d['action'], EXERCISES['deaths'])

    def test_lost_conversion_without_next_point_is_not_asserted(self):
        decisive = {'early_death': None, 'first_disadvantage': None, 'vision_before_objective': [],
                    'advantage_conversion': {'lead': 450, 'next_gold_gap': None, 'status': 'lost'}, 'advice': []}
        self.assertEqual(build_debrief(game(decisive))['moments'], [])

    def test_conversion_only_moment_uses_conversion_action(self):
        decisive = {'early_death': None, 'first_disadvantage': None, 'vision_before_objective': [],
                    'advantage_conversion': {'lead': 450, 'next_gold_gap': 100, 'status': 'lost'}, 'advice': []}
        d = build_debrief(game(decisive))
        self.assertEqual(d['main']['title'], 'Convertir une avance')
        self.assertIn('objectif précis', d['action'])

    def test_missing_timeline_falls_back_to_end_of_game_flags(self):
        g = game(decisive=None, deaths_per_10=7.0, deaths=20)
        g['decisive_moments'] = None
        d = build_debrief(g)
        self.assertFalse(d['timeline'])
        self.assertEqual(d['moments'], [])
        self.assertEqual(d['main']['title'], SIGNAL_BY_KEY_TITLE('deaths'))
        self.assertEqual(d['action'], EXERCISES['deaths'])
        self.assertIn('Timeline indisponible', render_debrief(d))

    def test_nothing_to_review_and_strengths_are_capped_at_two(self):
        decisive = {'early_death': None, 'first_disadvantage': None, 'vision_before_objective': [],
                    'advantage_conversion': {'lead': 500, 'next_gold_gap': 450, 'status': 'maintained'}, 'advice': []}
        d = build_debrief(game(decisive, deaths_per_10=1.0, deaths=1, kp=70, gold_gap=500))
        self.assertIsNone(d['main'])
        self.assertEqual(len(d['strengths']), 2)
        self.assertIn('conservée', d['strengths'][0])
        self.assertIn('Aucun point à revoir', render_debrief(d))

    def test_support_has_no_participation_strength_or_flag(self):
        g = game(role='UTILITY', kp=10, deaths_per_10=3.0, vision=1.5)
        d = build_debrief(g)
        self.assertEqual(d['strengths'], [])
        self.assertIsNone(d['main'])

    def test_render_escapes_text(self):
        d = build_debrief(game(full_decisive()))
        d['main']['title'] = '<b>x</b>'
        out = render_debrief(d)
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', out)
        self.assertNotIn('<b>x</b>', out)

    def test_attach_inserts_one_debrief_per_match_card_only(self):
        card = "<article class='match win' data-result='win'><div class='match-head'>x</div><div class='score-row'>s</div></article>"
        other = "<article class='champion-card'>c</article>"
        html = card + other + card
        out = attach_debriefs(html, [game(full_decisive()), game()])
        self.assertEqual(out.count("<section class='debrief'>"), 2)
        self.assertTrue(out.index("<section class='debrief'>") < out.index("<div class='score-row'>"))
        self.assertIn(other, out)

    def test_attach_leaves_page_unchanged_when_card_count_differs(self):
        card = "<article class='match win'><div class='score-row'>s</div></article>"
        self.assertEqual(attach_debriefs(card, [game(), game()]), card)


def SIGNAL_BY_KEY_TITLE(key):
    return next(s['title'] for s in SIGNALS if s['key'] == key)


if __name__ == '__main__':
    unittest.main()
