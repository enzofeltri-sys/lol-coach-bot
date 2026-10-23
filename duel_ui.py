from html import escape
from rune_parser import champion_build


def prepare_duels(games, data):
    lookup = {}
    for key, champion in data['champions'].items():
        for name in (key, champion.get('name'), champion.get('id')):
            if name:
                lookup[name] = key
    builds = []
    seen = set()
    for game in games:
        champion = lookup.get(game['champion'])
        opponent = lookup.get(game.get('opponent_champion'))
        role = game['role']
        identity = (champion, role, opponent)
        if not champion or not opponent or identity in seen:
            continue
        seen.add(identity)
        builds.append(champion_build(champion, role, opponent, data))
    return builds


def render_duels(builds):
    def e(value):
        return escape(str(value), quote=True)
    def listing(items):
        return '<ul>' + ''.join('<li>' + e(item) + '</li>' for item in items) + '</ul>'
    def rune_cards(items):
        return '<div class="rune-grid">' + ''.join('<div class="rune-detail"><img class="rune-icon small" loading="lazy" src="' + e(item['icon']) + '" alt=""><span>' + e(item['name']) + '</span></div>' for item in items) + '</div>'
    options = []
    panels = []
    for i, build in enumerate(builds):
        label = build['champion'] + ' vs ' + build['opponent'] + ' · ' + build['role']
        options.append('<option value="' + str(i) + '">' + e(label) + '</option>')
        runes = build['runes']
        content = '<h2>' + e(label) + '</h2><p class="hint">Patch ' + e(build['patch']) + '</p>'
        content += '<section class="panel"><h2>Runes recommandées</h2><h3>' + e(runes['primary']) + '</h3>' + rune_cards(runes.get('primary_runes', []))
        content += '<h3>' + e(runes['secondary']) + '</h3>' + rune_cards(runes.get('secondary_runes', []))
        content += '<p>' + e(runes['shards']) + '</p><p class="hint">' + e(runes['source']) + '</p></section>'
        content += '<section class="panel section"><h2>Plan contre ' + e(build['opponent']) + '</h2>' + listing(build.get('matchup_plan', [])) + '</section>'
        content += '<details class="panel section"><summary>Repères génériques — non validés pour ce duel</summary><p>Sorts : ' + e(' + '.join(build.get('summoners', []))) + '</p><p>Compétences : ' + e(build.get('skill_order', '')) + '</p>'
        content += listing(build.get('core_items', []) + build.get('situational_items', [])) + '</details>'
        panels.append('<article data-duel-panel="' + str(i) + '"' + (' hidden' if i else '') + '>' + content + '</article>')
    empty = '<p>Aucun duel avec adversaire identifié dans les parties analysées.</p>'
    return '<div id="build" class="tab-panel" role="tabpanel" aria-labelledby="tab-build" hidden><section class="section panel"><h2>Build par duel</h2><p class="hint">Duels des parties analysées. Runes par champion et rôle, pas par adversaire.</p><div class="filters"><label for="build-duel">Duel</label><select id="build-duel" style="max-width:100%">' + ''.join(options) + '</select></div><div id="build-content">' + (''.join(panels) or empty) + '</div></section></div>\n'


def attach_duels(html, builds):
    start = html.index('<div id="build"')
    end = html.index('<div id="champions"', start)
    html = html[:start] + render_duels(builds) + html[end:]
    script = '''<script>
(() => {
  const select = document.getElementById('build-duel');
  if (!select) return;
  const panels = document.querySelectorAll('[data-duel-panel]');
  const update = () => panels.forEach(panel => {
    panel.hidden = panel.dataset.duelPanel !== select.value;
  });
  select.addEventListener('change', update);
  update();
})();
</script>'''
    return html.replace('</body>', script + '</body>', 1)
