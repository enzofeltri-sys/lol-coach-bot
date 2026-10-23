import json
from build_data import fetch_json, DDRAGON_BASE
from rune_parser import recommended_page

ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']


def prepare_duels(games, data):
    spells = {}
    try:
        raw = fetch_json(DDRAGON_BASE.format(version=data['version']) + '/summoner.json')['data']
        spells = {str(s['key']): s['name'] for s in raw.values()}
    except Exception as error:
        print('Summoner metadata unavailable: ' + type(error).__name__)
    recommendations = data.get('rune_recommendations', [])
    entries = {str(e.get('championId')): e for e in recommendations if isinstance(e, dict)} if isinstance(recommendations, list) else {}
    builds = []
    for key, champion in sorted(data['champions'].items(), key=lambda pair: pair[1]['name']):
        pages = {}
        entry = entries.get(str(champion['key']), {})
        for role in ROLES:
            try:
                runes = recommended_page(key, role, data)
            except (ValueError, KeyError, TypeError) as error:
                print('Rune page unavailable for ' + key + '/' + role + ': ' + str(error))
                runes = None
            if not runes:
                continue
            position = {'MIDDLE': 'mid', 'UTILITY': 'support'}.get(role, role.lower())
            aliases = {'middle': 'mid', 'utility': 'support', 'adc': 'bottom'}
            source_pages = [p for p in entry.get('runeRecommendations', []) if str(p.get('mapId')) == '11' and aliases.get(str(p.get('position', '')).lower(), str(p.get('position', '')).lower()) == position]
            pages[role] = {'runes': runes, 'summoners': []}
            if len(source_pages) == 1:
                ids = source_pages[0].get('summonerSpellIds', [])
                if len(ids) == 2 and all(str(i) in spells for i in ids):
                    pages[role]['summoners'] = [spells[str(i)] for i in ids]
        fallback = {'primary': 'Indisponible', 'secondary': 'Indisponible', 'primary_runes': [], 'shards': 'Indisponibles', 'source': 'CommunityDragon'}
        builds.append({'key': key, 'champion': champion['name'], 'patch': data['version'], 'pages': pages, 'runes': next(iter(pages.values()))['runes'] if pages else fallback, 'portrait': 'https://ddragon.leagueoflegends.com/cdn/' + data['version'] + '/img/champion/' + champion['image']['full']})
    return builds


def attach_duels(html, builds):
    payload = json.dumps(builds, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    panel = '''<div id="build" class="tab-panel" role="tabpanel" aria-labelledby="tab-build" hidden>
<section class="section panel">
<h2>Build classique</h2>
<div class="filters"><label for="classic-champion">Champion</label><select id="classic-champion" style="max-width:100%"></select><label for="classic-role">Rôle</label><select id="classic-role"></select></div>
<div style="display:flex;align-items:center;gap:12px"><img id="classic-portrait" width="64" height="64" alt=""><div><h2 id="classic-title"></h2><p id="classic-patch" class="hint"></p></div></div>
<section class="section"><h3>Runes de base</h3><p id="classic-rune-status" class="hint"></p><h4 id="classic-primary"></h4><div id="classic-main-runes" class="rune-grid"></div><h4 id="classic-secondary"></h4><div id="classic-sub-runes" class="rune-grid"></div><p id="classic-shards" class="hint"></p></section>
<section class="section"><h3>Sorts d’invocateur</h3><p id="classic-spells"></p></section>
<section class="section"><h3>Objets et compétences</h3><p class="hint">Build d’objets et ordre des compétences indisponibles : aucune source vérifiée n’est encore intégrée. Les anciennes valeurs génériques ont été retirées.</p></section>
<section class="section"><h3>Adapter au versus</h3><div class="filters"><label for="classic-opponent">Contre qui ?</label><select id="classic-opponent" style="max-width:100%"></select></div><p id="classic-versus-note" class="hint"></p></section>
</section></div>
'''
    start = html.index('<div id="build"')
    end = html.index('<div id="champions"', start)
    html = html[:start] + panel + html[end:]
    script = '''<script type="application/json" id="classic-data">PAYLOAD</script>
<script>
(() => {
  const data = JSON.parse(document.getElementById('classic-data').textContent);
  const el = id => document.getElementById('classic-' + id);
  const champion = el('champion'), role = el('role'), opponent = el('opponent');
  const roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
  const option = (value, label) => { const o = document.createElement('option'); o.value = value; o.textContent = label; return o; };
  data.forEach(b => champion.append(option(b.key, b.champion)));
  roles.forEach(r => role.append(option(r, r)));
  opponent.append(option('', 'Aucun — build classique'));
  data.forEach(b => opponent.append(option(b.key, b.champion)));
  const cards = (id, runes) => {
    el(id).replaceChildren();
    (runes || []).forEach(r => {
      const card = document.createElement('div'); card.className = 'rune-detail';
      const img = document.createElement('img'); img.className = 'rune-icon small'; img.src = r.icon; img.alt = ''; img.loading = 'lazy';
      const name = document.createElement('span'); name.textContent = r.name;
      card.append(img, name); el(id).append(card);
    });
  };
  const versus = () => {
    const own = data.find(b => b.key === champion.value);
    const enemy = data.find(b => b.key === opponent.value);
    el('versus-note').textContent = !enemy ? 'Choisis un adversaire après avoir consulté le build classique.' : own.key === enemy.key ? 'Tu as sélectionné un duel miroir. Aucune adaptation spécifique vérifiée ; le build de base est conservé.' : own.champion + ' contre ' + enemy.champion + ' : aucune adaptation spécifique vérifiée pour ce duel. Le build classique reste inchangé.';
  };
  const update = (changedChampion = false) => {
    const b = data.find(b => b.key === champion.value);
    if (!b) return;
    if (changedChampion && !b.pages[role.value]) role.value = Object.keys(b.pages)[0] || 'MIDDLE';
    el('title').textContent = b.champion + ' · ' + role.value;
    el('patch').textContent = 'Patch ' + b.patch;
    el('portrait').src = b.portrait; el('portrait').alt = b.champion;
    const page = b.pages[role.value]; const runes = page ? page.runes : null;
    el('rune-status').textContent = runes ? 'CommunityDragon · recommandations par champion et rôle, indépendantes du versus.' : 'Aucune page de runes valide disponible pour ce champion à ce rôle.';
    el('primary').textContent = runes ? runes.primary : '';
    el('secondary').textContent = runes ? runes.secondary : '';
    cards('main-runes', runes && runes.primary_runes); cards('sub-runes', runes && runes.secondary_runes);
    el('shards').textContent = runes ? 'Shards — ' + runes.shards : '';
    el('spells').textContent = page && page.summoners.length ? page.summoners.join(' + ') : 'Recommandation indisponible pour cette sélection.';
    versus();
  };
  champion.addEventListener('change', () => { opponent.value = ''; update(true); });
  role.addEventListener('change', () => update());
  opponent.addEventListener('change', versus);
  update(true);
})();
</script>'''.replace('PAYLOAD', payload)
    return html.replace('</body>', script + '</body>', 1)
