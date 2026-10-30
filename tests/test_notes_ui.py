import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from notes_ui import attach_notes, game_form


def page(cards=2, plan=True, versus=True):
    card = "<article class='match win'><div class='match-head'>x</div><section class='debrief'>d</section><div class='score-row'>s</div></article>"
    plan_html = '<div id="plan" class="tab-panel" hidden>\n<section>p</section>\n</div>\n<div id="matchups" hidden></div>' if plan else '<div id="matchups"></div>'
    other = "<article class='champion-card'>c</article>"
    note = '<p id="classic-versus-note" class="hint"></p>' if versus else ''
    return '<html><head></head><body>' + plan_html + card * cards + other + note + '</body></html>'


GAMES = [{'match_id': 'EUW1_1'}, {'match_id': 'EUW1_2'}]


class NotesUiTests(unittest.TestCase):
    def test_everything_is_attached_once(self):
        out = attach_notes(page(), GAMES)
        self.assertEqual(out.count('id="session-goal"'), 1)
        self.assertEqual(out.count('class="drawer notes note-form"'), 2)
        self.assertEqual(out.count('id="opp-notes"'), 1)
        self.assertEqual(out.count('<style>'), 1)
        self.assertEqual(out.count('lolcoach.notes.v1'), 1)
        self.assertEqual(out.count('<script>'), 1)

    def test_session_blocks_are_inside_the_plan_tab(self):
        out = attach_notes(page(), GAMES)
        self.assertTrue(out.index('<div id="plan"') < out.index('id="session-goal"') < out.index('<div id="matchups"'))

    def test_form_is_placed_after_the_debrief_and_before_the_score_row(self):
        out = attach_notes(page(cards=1), GAMES[:1])
        self.assertTrue(out.index("<section class='debrief'>") < out.index('note-form') < out.index("<div class='score-row'>"))

    def test_champion_cards_are_untouched(self):
        self.assertIn("<article class='champion-card'>c</article>", attach_notes(page(), GAMES))

    def test_card_count_mismatch_skips_forms_only(self):
        out = attach_notes(page(cards=1), GAMES)
        self.assertNotIn('note-form" data-match-id', out)
        self.assertIn('id="session-goal"', out)

    def test_missing_anchors_do_not_crash(self):
        out = attach_notes(page(plan=False, versus=False), GAMES)
        self.assertNotIn('id="session-goal"', out)
        self.assertNotIn('id="opp-notes"', out)
        self.assertIn('lolcoach.notes.v1', out)

    def test_match_id_is_escaped(self):
        self.assertNotIn('"><script', game_form('"><script>alert(1)</script>'))
        self.assertIn('&quot;&gt;&lt;script&gt;', game_form('"><script>alert(1)</script>'))


if __name__ == '__main__':
    unittest.main()
