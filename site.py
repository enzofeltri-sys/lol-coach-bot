from html import escape
from datetime import datetime, timezone


def fmt_gap(value):
    try:
        return f"{float(value):+.1f}"
    except (TypeError, ValueError):
        return '—'


def gap_class(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ''
    return 'positive' if value > 0 else 'negative' if value < 0 else 'neutral'


def build_html(riot_id, analysis):
    def e(value):
        return escape(str(value), quote=True)

    games = analysis['games']
    updated = datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')
    plan = analysis.get('progression_plan') or {}
    if not plan.get('priority'):
        plan = {'priority': 'Continuer la progression', 'why': 'Le plan n’a pas pu être calculé à partir des données disponibles.', 'evidence': 'Relance une analyse après quelques nouvelles parties.', 'exercise': 'Choisis un objectif simple : moins de morts, plus de vision ou de meilleures premières minutes.', 'metric': 'À définir', 'current': '—', 'target': 'Jouer quelques parties supplémentaires.', 'affected_games': 0, 'secondary': []}
    cards = ''
    for g in games:
        won = bool(g['win'])
        result = 'Victoire' if won else 'Défaite'
        state = 'win' if won else 'loss'
        opponent = g.get('opponent_champion') or 'Adversaire inconnu'
        timeline_rows = ''.join(f"<tr><td>{e(p['minute'])} min</td><td class='{gap_class(p['gold_gap'])}'>{fmt_gap(p['gold_gap'])}</td><td class='{gap_class(p['xp_gap'])}'>{fmt_gap(p['xp_gap'])}</td><td class='{gap_class(p['cs_gap'])}'>{fmt_gap(p['cs_gap'])}</td></tr>" for p in g.get('timeline', []))
        timeline_block = f"<details class='drawer'><summary>Timeline vs {e(opponent)}</summary><div class='table-wrap'><table><thead><tr><th>Repère</th><th>Or</th><th>XP</th><th>CS</th></tr></thead><tbody>{timeline_rows}</tbody></table></div><p class='hint'>Positif = avantage.</p></details>" if timeline_rows else '<p class="hint">Timeline indisponible pour cette partie.</p>'
        objectives = g.get('objectives', {})
        champion_items = ''.join(f'<li>{e(item)}</li>' for item in g.get('advice', []))
        matchup_items = ''.join(f'<li>{e(item)}</li>' for item in g.get('matchup_advice', []))
        cards += f"""
<article class='match {state}' data-result='{state}' data-role='{e(g['role'])}' data-champion='{e(g['champion'])}'>
  <div class='match-head'><div><div class='champion'>{e(g['champion'])} <span class='vs'>vs</span> {e(opponent)}</div><div class='meta'>{e(g['role'])} · {e(g['duration_min'])} min · patch {e(g['patch'])}</div></div><span class='badge {state}'>{result}</span></div>
  <div class='score-row'><div class='score'>{e(g['kills'])}<small>/</small>{e(g['deaths'])}<small>/</small>{e(g['assists'])}</div><div class='score-label'>K / D / A · KDA {e(g['kda'])}</div></div>
  <div class='metric-grid'><div><small>CS/min</small><strong>{e(g['cs_per_min'])}</strong></div><div><small>Dégâts/min</small><strong>{e(g['damage_per_min'])}</strong></div><div><small>Dégâts subis/min</small><strong>{e(g['damage_taken_per_min'])}</strong></div><div><small>Or/min</small><strong>{e(g['gold_per_min'])}</strong></div><div><small>Vision/min</small><strong>{e(g['vision_per_min'])}</strong></div><div><small>KP</small><strong>{e(g['kill_participation'])}%</strong></div></div>
  {timeline_block}
  <details class='drawer advice'><summary>Que faire mieux dans cette partie</summary><ul>{champion_items}</ul></details>
  <details class='drawer advice'><summary>Plan contre {e(opponent)}</summary><ul>{matchup_items}</ul></details>
  <details class='drawer'><summary>Détails et objectifs</summary><div class='detail-grid'><div><small>Dégâts subis</small><strong>{e(g['damage_taken'])}</strong></div><div><small>Or total</small><strong>{e(g['gold'])}</strong></div><div><small>Vision score</small><strong>{e(g['vision_score'])}</strong></div><div><small>CC infligé</small><strong>{e(g['cc_score'])} s</strong></div><div><small>Tours</small><strong>{e(objectives.get('towers', 0))}</strong></div><div><small>Dragons</small><strong>{e(objectives.get('dragons', 0))}</strong></div><div><small>Barons</small><strong>{e(objectives.get('barons', 0))}</strong></div><div><small>Hérauts</small><strong>{e(objectives.get('heralds', 0))}</strong></div></div></details>
</article>"""
    champion_blocks = ''
    for champion, data in analysis.get('champion_aggregates', {}).items():
        advice_items = ''.join(f'<li>{e(item)}</li>' for item in data['advice'])
        champion_blocks += f"<article class='champion-card'><div class='match-head'><div><div class='champion'>{e(champion)}</div><div class='meta'>{e(data['role'])} · {data['games']} partie(s)</div></div><span class='pill {'good' if data['win_rate'] >= 50 else 'bad'}'>{e(data['win_rate'])}% victoires</span></div><div class='metric-grid'><div><small>KDA</small><strong>{e(data['avg_kda'])}</strong></div><div><small>Morts/10</small><strong>{e(data['avg_deaths_per_10'])}</strong></div><div><small>Dégâts/min</small><strong>{e(data['avg_damage_per_min'])}</strong></div><div><small>Vision/min</small><strong>{e(data['avg_vision_per_min'])}</strong></div></div><div class='advice-box'><small>À faire mieux</small><ul>{advice_items}</ul></div></article>"
    filters = analysis.get('matchup_filters', {'roles': [], 'champions': []})
    role_buttons = ''.join(f"<button type='button' class='filter' data-match-filter='role' data-value='{e(role)}'>{e(role)}</button>" for role in filters['roles'])
    champion_options = ''.join(f"<option value='{e(champion)}'>{e(champion)}</option>" for champion in filters['champions'])
    matchup_blocks = ''
    for matchup, data in analysis.get('matchup_aggregates', {}).items():
        advice_items = ''.join(f'<li>{e(item)}</li>' for item in data['advice'])
        matchup_blocks += f"<article class='matchup-card' data-role='{e(data['role'])}' data-champion='{e(data['champion'])}' data-performance='{e(data['performance'])}'><div class='match-head'><div><div class='champion'>{e(matchup)}</div><div class='meta'>{e(data['role'])} · {data['games']} partie(s)</div></div><span class='pill {e(data['performance'])}'>{e(data['win_rate'])}% victoires</span></div><div class='advice-box'><small>Plan de jeu</small><ul>{advice_items}</ul></div></article>"
    gaps = analysis.get('timeline_gaps', {})
    gap10 = gaps.get(10) or {}
    stat_defs = [('Winrate', str(analysis['win_rate']) + '%', analysis['win_rate']), ('KDA moyen', analysis['avg_kda'], None), ('CS / minute', analysis['avg_cs_per_min'], None), ('Dégâts / minute', analysis['avg_damage_per_min'], None), ('Or / minute', analysis['avg_gold_per_min'], None), ('Vision / minute', analysis['avg_vision_per_min'], None), ('Participation kills', str(analysis['avg_kill_participation']) + '%', analysis['avg_kill_participation']), ('Écart or à 10 min', fmt_gap(gap10.get('gold_gap')), None)]
    stats = ''.join(f"<div class='stat'><small>{e(label)}</small><strong>{e(value)}</strong>" + (f"<div class='bar'><span style='width:{max(0, min(100, float(progress)))}%'></span></div>" if progress is not None else '') + '</div>' for label, value, progress in stat_defs)
    gap_rows = ''.join(f"<tr><td>{e(minute)} min</td><td>{e((gaps.get(minute) or {}).get('games', 0))}</td><td class='{gap_class((gaps.get(minute) or {}).get('gold_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('gold_gap'))}</td><td class='{gap_class((gaps.get(minute) or {}).get('xp_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('xp_gap'))}</td><td class='{gap_class((gaps.get(minute) or {}).get('cs_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('cs_gap'))}</td></tr>" for minute in (5, 10, 15, 20))
    role_rows = ''.join(f"<tr><td><b>{e(role)}</b></td><td>{e(data['games'])}</td><td>{e(data['win_rate'])}%</td><td>{e(data['avg_kda'])}</td><td>{e(data['avg_deaths_per_10'])}</td><td>{e(data['avg_cs_per_min'])}</td><td>{e(data['avg_damage_per_min'])}</td><td>{e(data['avg_vision_per_min'])}</td><td>{e(data['avg_kill_participation'])}%</td></tr>" for role, data in analysis.get('role_aggregates', {}).items())
    secondary = ''.join(f"<li><b>{e(s['title'])}</b> — {e(s['count'])} partie(s) · {e(s['metric'])} : {e(s['current'])}</li>" for s in plan.get('secondary', []))
    css = '''
:root{color-scheme:dark;--bg:#070d18;--panel:#101c2d;--line:#26374f;--text:#eef5ff;--muted:#9fb0c6;--accent:#67d4ff;--good:#4ade80;--bad:#fb7185;--warn:#fbbf24}*{box-sizing:border-box}html,body{overscroll-behavior-y:auto!important;touch-action:pan-y}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(900px 500px at 85% -10%,#1d3d61,transparent),var(--bg);color:var(--text);font:15px/1.55 system-ui,sans-serif;padding-bottom:76px}main{max-width:1180px;margin:auto;padding:0 18px 24px}.topbar{position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);background:#070d18d9;border-bottom:1px solid var(--line)}.topbar-inner{max-width:1180px;margin:auto;display:flex;justify-content:space-between;align-items:center;gap:14px;padding:12px 18px}.brand{display:flex;align-items:center;gap:10px;font-weight:750}.brand-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);box-shadow:0 0 14px var(--accent)}.refresh-btn{border:1px solid var(--line);background:var(--panel);color:var(--text);font:inherit;font-size:16px;line-height:1;padding:8px 11px;border-radius:999px;cursor:pointer}.refresh-btn:active{transform:scale(.96)}.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:40;background:#070d18f2;border-top:1px solid var(--line);backdrop-filter:blur(16px)}.tabbar-inner{max-width:1180px;margin:auto;display:grid;grid-template-columns:repeat(6,1fr);gap:2px;padding:8px 6px calc(8px + env(safe-area-inset-bottom))}.tab{border:0;background:transparent;color:var(--muted);font:inherit;font-size:10px;padding:6px 2px;border-radius:12px;cursor:pointer;display:grid;gap:3px;justify-items:center}.tab span{font-size:18px;line-height:1}.tab[aria-selected=true]{color:var(--accent);background:#12283c;font-weight:700}.tab-panel[hidden]{display:none!important}header.hero{padding:34px 0 22px}.eyebrow{display:inline-flex;padding:6px 11px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--muted);font-size:12px;text-transform:uppercase}.h1,h1{font-size:clamp(30px,6vw,50px);margin:16px 0 8px}.hero p{max-width:660px;color:var(--muted)}.hero-meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.chip{padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel);font-size:13px;color:var(--muted)}.section{margin-top:26px}.section-head{margin-bottom:14px}.section-head h2{margin:0;font-size:22px}.section-head p{margin:4px 0 0;color:var(--muted);font-size:14px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px}.stat,.panel,.match,.champion-card,.matchup-card{background:linear-gradient(180deg,#111f31,#0e1928);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 12px 30px #0004}.stat small{display:block;color:var(--muted);font-size:12px;margin-bottom:6px}.stat strong{font-size:25px;color:var(--accent)}.bar{height:5px;border-radius:99px;background:#22344c;margin-top:10px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#8be9ff)}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.panel h2{margin:0 0 12px;font-size:19px}.panel ul{margin:0;padding-left:20px}.panel li{margin:8px 0}.note{border-left:3px solid var(--warn);background:#2b241766;border-radius:10px;padding:12px 14px;color:#f5e2b8;font-size:14px}.hint{color:var(--muted);font-size:13px;margin:8px 0 0}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}table{width:100%;border-collapse:collapse;font-size:14px;min-width:560px}th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{color:var(--muted);font-size:12px;text-transform:uppercase;background:#0d1827}.positive{color:var(--good);font-weight:700}.negative{color:var(--bad);font-weight:700}.neutral{color:var(--muted)}.match,.champion-card,.matchup-card{display:grid;gap:14px;border-left:4px solid var(--bad);margin-bottom:12px}.match.win{border-left-color:var(--good)}.champion-card{border-left-color:var(--accent)}.matchup-card{border-left-color:var(--warn)}.matchup-card[data-performance=good]{border-left-color:var(--good)}.match-head{display:flex;justify-content:space-between;align-items:start;gap:12px}.champion{font-size:20px;font-weight:750}.vs{color:var(--muted);font-size:15px;font-weight:500}.meta{color:var(--muted);font-size:13px;margin-top:3px}.badge{padding:6px 11px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid}.badge.win{color:var(--good);border-color:#2f6b4c;background:#12301f}.badge.loss{color:var(--bad);border-color:#6b3441;background:#331721}.pill{padding:5px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid}.pill.good{color:var(--good);border-color:#2f6b4c;background:#12301f}.pill.bad{color:var(--bad);border-color:#6b3441;background:#331721}.score-row{display:flex;align-items:baseline;gap:12px}.score{font-size:28px;font-weight:800}.score small{color:var(--muted);font-size:18px;margin:0 3px}.score-label{color:var(--muted);font-size:13px}.metric-grid,.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}.metric-grid div,.detail-grid div{background:#0d1827;border:1px solid var(--line);border-radius:11px;padding:10px}.metric-grid small,.detail-grid small{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}.metric-grid strong,.detail-grid strong{font-size:16px}.drawer{border-top:1px solid var(--line);padding-top:10px}summary{cursor:pointer;color:var(--accent);font-weight:650;font-size:14px}.drawer[open] summary{margin-bottom:10px}.advice ul{margin:0;padding-left:20px}.advice li{margin:6px 0}.advice-box{background:#0d1827;border:1px solid var(--line);border-radius:12px;padding:12px}.advice-box small{display:block;color:var(--accent);font-weight:700;margin-bottom:6px}.advice-box ul{margin:0;padding-left:20px}.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}.filters button,.filters select{border:1px solid var(--line);border-radius:999px;padding:8px 14px;background:var(--panel);color:var(--text);cursor:pointer;font:inherit;font-size:13px}.filters button[aria-pressed=true],.filters button.active{background:#1d4a63;border-color:var(--accent)}footer{margin-top:28px;padding:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}[hidden]{display:none!important}@media(max-width:760px){.grid-2{grid-template-columns:1fr}.hero{padding:24px 0 18px}.score{font-size:24px}.section-head h2{font-size:20px}}
'''
    issues = ''.join(f'<li>{e(item)}</li>' for item in analysis['issues'])
    strengths = ''.join(f'<li>{e(item)}</li>' for item in analysis['strengths'])
    timeline_items = ''.join(f'<li>{e(item)}</li>' for item in analysis.get('timeline_insights', []))
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(riot_id)} · LoL Coach</title><style>{css}</style></head><body>
<div class="topbar"><div class="topbar-inner"><div class="brand"><span class="brand-dot"></span>LoL Coach</div><div style="display:flex;align-items:center;gap:8px"><span class="chip">{len(games)} parties</span><button type="button" id="refresh-btn" class="refresh-btn" aria-label="Rafraîchir les données">🔄</button></div></div></div></div>
<main>
<div id="overview" class="tab-panel" role="tabpanel" aria-labelledby="tab-overview">
<header class="hero"><span class="eyebrow">EUW · Solo/Duo</span><h1>{e(riot_id)}</h1><p>Ton bilan sur {len(games)} parties récentes, avec des conseils calculés à partir de tes timelines et de tes performances.</p><div class="hero-meta"><span class="chip">Rapport du {updated}</span><span class="chip">{len(games)} parties analysées</span></div></header>
<section class="section stats">{stats}</section>
<p class="note">Lecture prudente : les conseils sont des repères d’amélioration calculés sur tes parties. Adapte-les au patch, aux objets, aux summons et au déroulement réel.</p>
<div class="grid-2 section"><section class="panel"><h2>Pistes à vérifier</h2><ul>{issues}</ul></section><section class="panel"><h2>Indicateurs favorables</h2><ul>{strengths}</ul></section></div>
</div>
<div id="plan" class="tab-panel" role="tabpanel" aria-labelledby="tab-plan" hidden>
<section class="section panel"><div class="section-head"><h2>Priorité de progression</h2><p>Un seul objectif à travailler lors de tes prochaines parties</p></div><h2>{e(plan.get('priority'))}</h2><p>{e(plan.get('why', ''))}</p><div class="advice-box"><small>Preuve dans tes parties</small><p>{e(plan.get('evidence', ''))}</p></div><div class="advice-box"><small>Exercice pour les prochaines games</small><p>{e(plan.get('exercise', ''))}</p></div><div class="metric-grid"><div><small>Indicateur</small><strong>{e(plan.get('metric', '—'))}</strong></div><div><small>Niveau actuel</small><strong>{e(plan.get('current', '—'))}</strong></div><div><small>Objectif</small><strong>{e(plan.get('target', '—'))}</strong></div><div><small>Parties concernées</small><strong>{e(plan.get('affected_games', 0))}</strong></div></div></section>
<section class="section panel"><h2>Signaux secondaires</h2><ul>{secondary or '<li>Aucun autre signal suffisamment fort pour l’instant.</li>'}</ul></section>
</div>
<div id="matchups" class="tab-panel" role="tabpanel" aria-labelledby="tab-matchups" hidden>
<section class="section"><div class="section-head"><h2>Matchups</h2><p>Filtre par rôle, champion et performance pour trouver un plan de jeu concret</p></div><div class="filters"><button type='button' class='filter active' data-match-filter='role' data-value='all'>Tous rôles</button>{role_buttons}<select id='matchup-champion'><option value='all'>Tous champions</option>{champion_options}</select><button type='button' class='filter active' data-match-filter='performance' data-value='all'>Toutes performances</button><button type='button' class='filter' data-match-filter='performance' data-value='good'>Favorables</button><button type='button' class='filter' data-match-filter='performance' data-value='bad'>À travailler</button></div><div id='matchup-list'>{matchup_blocks}</div></section>
</div>
<div id="champions" class="tab-panel" role="tabpanel" aria-labelledby="tab-champions" hidden>
<section class="section"><div class="section-head"><h2>Champions</h2><p>Conseils calculés sur tes parties récentes</p></div>{champion_blocks}</section>
</div>
<div id="timeline" class="tab-panel" role="tabpanel" aria-labelledby="tab-timeline" hidden>
<section class="section panel"><div class="section-head"><h2>Écarts moyens timeline</h2><p>Positif = avantage face à l’adversaire du même rôle</p></div><div class="table-wrap"><table><thead><tr><th>Repère</th><th>Parties</th><th>Or</th><th>XP</th><th>CS</th></tr></thead><tbody>{gap_rows}</tbody></table></div></section>
<section class="section panel"><h2>Repères timeline</h2><ul>{timeline_items}</ul></section>
<section class="section panel"><h2>Moyennes par rôle</h2><div class="table-wrap"><table><thead><tr><th>Rôle</th><th>Parties</th><th>Winrate</th><th>KDA</th><th>Morts/10</th><th>CS/min</th><th>Dégâts/min</th><th>Vision/min</th><th>KP</th></tr></thead><tbody>{role_rows}</tbody></table></div></section>
</div>
<div id="matches" class="tab-panel" role="tabpanel" aria-labelledby="tab-matches" hidden>
<section class="section"><div class="section-head"><h2>Dernières parties</h2><p>Ouvre chaque partie pour voir ce qu’il faut faire mieux</p></div><div class="filters"><button type="button" data-filter="all" aria-pressed="true">Toutes</button><button type="button" data-filter="win" aria-pressed="false">Victoires</button><button type="button" data-filter="loss" aria-pressed="false">Défaites</button></div><p id="match-count" class="hint">{len(games)} partie(s) affichée(s)</p>{cards}</section>
</div>
<footer>Analyse statistique et timeline post-match. Projet personnel non affilié à Riot Games.</footer>
</main>
<nav class="tabbar" aria-label="Navigation principale"><div class="tabbar-inner"><button class="tab" role="tab" id="tab-overview" aria-controls="overview" aria-selected="true" data-tab="overview"><span>📊</span>Bilan</button><button class="tab" role="tab" id="tab-plan" aria-controls="plan" aria-selected="false" data-tab="plan"><span>🎯</span>Plan</button><button class="tab" role="tab" id="tab-matchups" aria-controls="matchups" aria-selected="false" data-tab="matchups"><span>⚔️</span>Matchups</button><button class="tab" role="tab" id="tab-champions" aria-controls="champions" aria-selected="false" data-tab="champions"><span>🧠</span>Champions</button><button class="tab" role="tab" id="tab-timeline" aria-controls="timeline" aria-selected="false" data-tab="timeline"><span>⏱️</span>Timeline</button><button class="tab" role="tab" id="tab-matches" aria-controls="matches" aria-selected="false" data-tab="matches"><span>🎮</span>Parties</button></div></nav>
<script>
(() => {{
  const tabs = Array.from(document.querySelectorAll('.tab'));
  const panels = Array.from(document.querySelectorAll('.tab-panel'));
  function showTab(name) {{
    tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.tab === name)));
    panels.forEach(panel => {{panel.hidden = panel.id !== name;}});
    if (history.replaceState) history.replaceState(null, '', '#' + name);
    window.scrollTo({{top: 0, behavior: 'smooth'}});
  }}
  tabs.forEach(tab => tab.addEventListener('click', () => showTab(tab.dataset.tab)));
  const initial = location.hash.slice(1);
  if (panels.some(panel => panel.id === initial)) showTab(initial);
  document.getElementById('refresh-btn').addEventListener('click', () => {{
    const url = new URL(window.location.href);
    url.searchParams.set('refresh', Date.now());
    window.location.replace(url.toString());
  }});
  const roleFilters = Array.from(document.querySelectorAll("[data-match-filter='role']"));
  const performanceFilters = Array.from(document.querySelectorAll("[data-match-filter='performance']"));
  const championSelect = document.getElementById('matchup-champion');
  function applyMatchupFilters() {{
    const role = roleFilters.find(b => b.classList.contains('active'))?.dataset.value || 'all';
    const performance = performanceFilters.find(b => b.classList.contains('active'))?.dataset.value || 'all';
    const champion = championSelect.value;
    document.querySelectorAll('#matchup-list .matchup-card').forEach(card => {{
      card.hidden = !((role === 'all' || card.dataset.role === role) && (performance === 'all' || card.dataset.performance === performance) && (champion === 'all' || card.dataset.champion === champion));
    }});
  }}
  roleFilters.forEach(button => button.addEventListener('click', () => {{roleFilters.forEach(b => b.classList.remove('active')); button.classList.add('active'); applyMatchupFilters();}}));
  performanceFilters.forEach(button => button.addEventListener('click', () => {{performanceFilters.forEach(b => b.classList.remove('active')); button.classList.add('active'); applyMatchupFilters();}}));
  championSelect.addEventListener('change', applyMatchupFilters);
  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {{
    document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    let count = 0;
    document.querySelectorAll('[data-result]').forEach(card => {{
      card.hidden = button.dataset.filter !== 'all' && card.dataset.result !== button.dataset.filter;
      if (!card.hidden) count++;
    }});
    document.getElementById('match-count').textContent = count + ' partie(s) affichée(s)';
  }}));
}})();
</script>
</body></html>'''
