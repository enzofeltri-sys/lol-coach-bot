import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import duel_ui
from rune_parser import recommended_page


def style(style_id, name, slot_ids):
    return {'id': style_id, 'name': name, 'icon': 'perk-images/Styles/' + str(style_id) + '.png',
            'slots': [{'runes': [{'id': i, 'name': 'Rune ' + str(i), 'icon': 'perk-images/' + str(i) + '.png'} for i in ids]} for ids in slot_ids]}


PRIMARY = style(8000, 'Précision', [[8005, 8008], [9111, 9101], [9104, 9105], [8014, 8017]])
SECONDARY = style(8100, 'Domination', [[8112], [8126, 8139], [8138, 8135], [8105, 8106]])


def page(position='mid', perk_ids=None, map_id=11):
    return {'position': position, 'mapId': map_id, 'primaryPerkStyleId': 8000, 'secondaryPerkStyleId': 8100,
            'perkIds': perk_ids or [8005, 9111, 9104, 8014, 8126, 8135, 5008, 5008, 5011], 'summonerSpellIds': [4, 12]}


def make_data(pages=None, recommendations=None):
    data = {
        'version': '16.21.1',
        'champions': {
            'Yone': {'key': '777', 'name': 'Yone', 'id': 'Yone', 'image': {'full': 'Yone.png'}},
            'Mel': {'key': '800', 'name': 'Mel', 'id': 'Mel', 'image': {'full': 'Mel.png'}},
        },
        'runes': [PRIMARY, SECONDARY],
        'perk_names': {'5008': 'Force adaptative', '5011': 'Vie'},
        'sources': [{'name': 'Data Dragon', 'ok': True, 'detail': 'OK'}, {'name': 'CommunityDragon', 'ok': False, 'detail': 'HTTPError 403'}],
        'generated_at': '23/10/2026 à 16:00 UTC',
    }
    data['rune_recommendations'] = recommendations if recommendations is not None else [{'championId': 777, 'runeRecommendations': pages or [page()]}]
    return data


class RunePageTests(unittest.TestCase):
    def test_valid_page_has_four_primary_two_secondary_and_named_shards(self):
        result = recommended_page('Yone', 'MIDDLE', make_data())
        self.assertEqual(len(result['primary_runes']), 4)
        self.assertEqual(len(result['secondary_runes']), 2)
        self.assertEqual(result['shards'], 'Force adaptative / Force adaptative / Vie')

    def test_unknown_shard_falls_back_to_identifier(self):
        data = make_data()
        data['perk_names'] = {}
        self.assertEqual(recommended_page('Yone', 'MIDDLE', data)['shards'], 'Éclat 5008 / Éclat 5008 / Éclat 5011')

    def test_role_without_page_returns_none(self):
        self.assertIsNone(recommended_page('Yone', 'TOP', make_data()))

    def test_other_map_is_ignored(self):
        self.assertIsNone(recommended_page('Yone', 'MIDDLE', make_data(pages=[page(map_id=12)])))

    def test_two_runes_in_one_slot_are_rejected(self):
        broken = page(perk_ids=[8005, 9111, 9101, 8014, 8126, 8135, 5008, 5008, 5011])
        with self.assertRaises(ValueError):
            recommended_page('Yone', 'MIDDLE', make_data(pages=[broken]))

    def test_valid_page_is_chosen_after_invalid_one(self):
        broken = page(perk_ids=[8005, 9111, 9101, 8014, 8126, 8135, 5008, 5008, 5011])
        result = recommended_page('Yone', 'MIDDLE', make_data(pages=[broken, page()]))
        self.assertEqual(len(result['primary_runes']), 4)


SUMMONERS = {'data': {'SummonerFlash': {'key': '4', 'name': 'Saut éclair'}, 'SummonerTeleport': {'key': '12', 'name': 'Téléportation'}}}


class DuelUiTests(unittest.TestCase):
    def setUp(self):
        patcher = patch('duel_ui.fetch_json', return_value=SUMMONERS)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_every_champion_is_listed_and_diagnostics_are_recorded(self):
        data = make_data()
        builds = duel_ui.prepare_duels([], data)
        self.assertEqual([b['champion'] for b in builds], ['Mel', 'Yone'])
        self.assertEqual(data['diagnostics'], {'champions': 2, 'with_runes': 1, 'pages': 1, 'missing': ['Mel']})
        yone = next(b for b in builds if b['key'] == 'Yone')
        self.assertEqual(yone['pages']['MIDDLE']['summoners'], ['Saut éclair', 'Téléportation'])

    def test_empty_recommendations_do_not_crash(self):
        data = make_data(recommendations=[])
        builds = duel_ui.prepare_duels([], data)
        self.assertEqual(data['diagnostics']['with_runes'], 0)
        self.assertTrue(all(b['pages'] == {} for b in builds))

    def test_attach_shows_status_and_escapes_payload(self):
        data = make_data()
        data['champions']['Yone']['name'] = '</script><b>Yone'
        builds = duel_ui.prepare_duels([], data)
        html = '<html><body><div id="build" hidden></div><div id="champions"></div></body></html>'
        result = duel_ui.attach_duels(html, builds, data)
        self.assertEqual(result.count('</script>'), 2)
        self.assertIn('✗ CommunityDragon — HTTPError 403', result)
        self.assertIn('23/10/2026 à 16:00 UTC', result)
        self.assertIn('1 champions sur 2', result)


if __name__ == '__main__':
    unittest.main()
