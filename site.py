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
<article class='match {state}' data-result='{state}'>
  <div class='match-head'><div><div class='champion'>{e(g['champion'])} <span class='vs'>vs</span> {e(opponent)}</div><div class='meta'>{e(g['role'])} · {e(g['duration_min'])} min · patch {e(g['patch'])}</div></div><span class='badge {state}'>{result}</span></div>
  <div class='score-row'><div class='score'>{e(g['kills'])}<small>/</small>{e(g['deaths'])}<small>/</small>{e(g['assists'])}</div><div class='score-label'>K / D / A · KDA {e(g['kda'])}</div></div>
  <div class='metric-grid'><div><small>CS/min</small><strong>{e(g['cs_per_min'])}</strong></div><div><small>Dégâts/min</small><strong>{e(g['damage_per_min'])}</strong></div><div><small>Dégâts subis/min</small><strong>{e(g['damage_taken_per_min'])}</strong></div><div><small>Or/min</small><strong>{e(g['gold_per_min'])}</strong></div><div><small>Vision/min</small><strong>{e(g['vision_per_min'])}</strong></div><div><small>KP</small><strong>{e(g['kill_participation'])}%</strong></div></div>
  {timeline_block}
  <details class='drawer advice'><summary>Conseils matchup : {e(g['champion'])} vs {e(opponent)}</summary><ul>{matchup_items}</ul></details>
  <details class='drawer advice'><summary>Conseils {e(g['champion'])}</summary><ul>{champion_items}</ul></details>
  <details class='drawer'><summary>Détails et objectifs</summary><div class='detail-grid'><div><small>Dégâts subis</small><strong>{e(g['damage_taken'])}</strong></div><div><small>Or total</small><strong>{e(g['gold'])}</strong></div><div><small>Vision score</small><strong>{e(g['vision_score'])}</strong></div><div><small>CC infligé</small><strong>{e(g['cc_score'])} s</strong></div><div><small>Tours</small><strong>{e(objectives.get('towers', 0))}</strong></div><div><small>Dragons</small><strong>{e(objectives.get('dragons', 0))}</strong></div><div><small>Barons</small><strong>{e(objectives.get('barons', 0))}</strong></div><div><small>Hérauts</small><strong>{e(objectives.get('heralds', 0))}</strong></div></div></details>
</article>"""
    champion_blocks = ''
    for champion, data in analysis.get('champion_aggregates', {}).items():
        advice_items = ''.join(f'<li>{e(item)}</li>' for item in data['advice'])
        champion_blocks += f"<article class='champion-card'><div class='match-head'><div><div class='champion'>{e(champion)}</div><div class='meta'>{e(data['role'])} · {data['games']} partie(s)</div></div><span class='pill {'good' if data['win_rate'] >= 50 else 'bad'}'>{e(data['win_rate'])}% victoires</span></div><div class='metric-grid'><div><small>KDA</small><strong>{e(data['avg_kda'])}</strong></div><div><small>Morts/10</small><strong>{e(data['avg_deaths_per_10'])}</strong></div><div><small>Dégâts/min</small><strong>{e(data['avg_damage_per_min'])}</strong></div><div><small>Vision/min</small><strong>{e(data['avg_vision_per_min'])}</strong></div></div><div class='advice-box'><small>Conseils personnalisés</small><ul>{advice_items}</ul></div></article>"
    matchup_blocks = ''
    for matchup, data in analysis.get('matchup_aggregates', {}).items():
        advice_items = ''.join(f'<li>{e(item)}</li>' for item in data['advice'])
        matchup_blocks += f"<article class='matchup-card'><div class='match-head'><div><div class='champion'>{e(matchup)}</div><div class='meta'>{e(data['role'])} · {data['games']} partie(s)</div></div><span class='pill {'good' if data['win_rate'] >= 50 else 'bad'}'>{e(data['win_rate'])}% victoires</span></div><div class='advice-box'><small>Plan de jeu matchup</small><ul>{advice_items}</ul></div></article>"
    gaps = analysis.get('timeline_gaps', {})
    gap10 = gaps.get(10) or {}
    stat_defs = [('Winrate', str(analysis['win_rate']) + '%', analysis['win_rate']), ('KDA moyen', analysis['avg_kda'], None), ('CS / minute', analysis['avg_cs_per_min'], None), ('Dégâts / minute', analysis['avg_damage_per_min'], None), ('Or / minute', analysis['avg_gold_per_min'], None), ('Vision / minute', analysis['avg_vision_per_min'], None), ('Participation kills', str(analysis['avg_kill_participation']) + '%', analysis['avg_kill_participation']), ('Écart or à 10 min', fmt_gap(gap10.get('gold_gap')), None)]
    stats = ''.join(f"<div class='stat'><small>{e(label)}</small><strong>{e(value)}</strong>" + (f"<div class='bar'><span style='width:{max(0, min(100, float(progress)))}%'></span></div>" if progress is not None else '') + '</div>' for label, value, progress in stat_defs)
    gap_rows = ''.join(f"<tr><td>{e(minute)} min</td><td>{e((gaps.get(minute) or {}).get('games', 0))}</td><td class='{gap_class((gaps.get(minute) or {}).get('gold_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('gold_gap'))}</td><td class='{gap_class((gaps.get(minute) or {}).get('xp_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('xp_gap'))}</td><td class='{gap_class((gaps.get(minute) or {}).get('cs_gap'))}'>{fmt_gap((gaps.get(minute) or {}).get('cs_gap'))}</td></tr>" for minute in (5, 10, 15, 20))
    role_rows = ''.join(f"<tr><td><b>{e(role)}</b></td><td>{e(data['games'])}</td><td>{e(data['win_rate'])}%</td><td>{e(data['avg_kda'])}</td><td>{e(data['avg_deaths_per_10'])}</td><td>{e(data['avg_cs_per_min'])}</td><td>{e(data['avg_damage_per_min'])}</td><td>{e(data['avg_vision_per_min'])}</td><td>{e(data['avg_kill_participation'])}%</td></tr>" for role, data in analysis.get('role_aggregates', {}).items())
    css = '''
:root{color-scheme:dark;--bg:#070d18;--panel:#101c2d;--line:#26374f;--text:#eef5ff;--muted:#9fb0c6;--accent:#67d4ff;--good:#4ade80;--bad:#fb7185;--warn:#fbbf24}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(900px 500px at 85% -10%,#1d3d61,transparent),var(--bg);color:var(--text);font:15px/1.55 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:0 18px 48px}.topbar{position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);background:#070d18d9;border-bottom:1px solid var(--line)}.topbar-inner{max-width:1180px;margin:auto;display:flex;justify-content:space-between;align-items:center;gap:14px;padding:12px 18px}.brand{display:flex;align-items:center;gap:10px;font-weight:750}.brand-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);box-shadow:0 0 14px var(--accent)}.topbar nav{display:flex;gap:8px;flex-wrap:wrap}.topbar nav a{padding:7px 11px;border:1px solid var(--line);border-radius:999px;background:#101c2db3;color:var(--text);font-size:13px}header.hero{padding:42px 0 26px}.eyebrow{display:inline-flex;padding:6px 11px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--muted);font-size:12px;text-transform:uppercase}.h1,h1{font-size:clamp(30px,6vw,50px);margin:16px 0 8px}.hero p{max-width:660px;color:var(--muted)}.hero-meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.chip{padding:7px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel);font-size:13px;color:var(--muted)}.section{margin-top:34px}.section-head{margin-bottom:14px}.section-head h2{margin:0;font-size:22px}.section-head p{margin:4px 0 0;color:var(--muted);font-size:14px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px}.stat,.panel,.match,.champion-card,.matchup-card{background:linear-gradient(180deg,#111f31,#0e1928);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 12px 30px #0004}.stat small{display:block;color:var(--muted);font-size:12px;margin-bottom:6px}.stat strong{font-size:25px;color:var(--accent)}.bar{height:5px;border-radius:99px;background:#22344c;margin-top:10px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#8be9ff)}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.panel h2{margin:0 0 12px;font-size:19px}.panel ul{margin:0;padding-left:20px}.panel li{margin:8px 0}.note{border-left:3px solid var(--warn);background:#2b241766;border-radius:10px;padding:12px 14px;color:#f5e2b8;font-size:14px}.hint{color:var(--muted);font-size:13px;margin:8px 0 0}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}table{width:100%;border-collapse:collapse;font-size:14px;min-width:560px}th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{color:var(--muted);font-size:12px;text-transform:uppercase;background:#0d1827}.positive{color:var(--good);font-weight:700}.negative{color:var(--bad);font-weight:700}.neutral{color:var(--muted)}.match,.champion-card,.matchup-card{display:grid;gap:14px;border-left:4px solid var(--bad);margin-bottom:12px}.match.win{border-left-color:var(--good)}.champion-card{border-left-color:var(--accent)}.matchup-card{border-left-color:var(--warn)}.match-head{display:flex;justify-content:space-between;align-items:start;gap:12px}.champion{font-size:20px;font-weight:750}.vs{color:var(--muted);font-size:15px;font-weight:500}.meta{color:var(--muted);font-size:13px;margin-top:3px}.badge{padding:6px 11px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid}.badge.win{color:var(--good);border-color:#2f6b4c;background:#12301f}.badge.loss{color:var(--bad);border-color:#6b3441;background:#331721}.pill{padding:5px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid}.pill.good{color:var(--good);border-color:#2f6b4c;background:#12301f}.pill.bad{color:var(--bad);border-color:#6b3441;background:#331721}.score-row{display:flex;align-items:baseline;gap:12px}.score{font-size:28px;font-weight:800}.score small{color:var(--muted);font-size:18px;margin:0 3px}.score-label{color:var(--muted);font-size:13px}.metric-grid,.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}.metric-grid div,.detail-grid div{background:#0d1827;border:1px solid var(--line);border-radius:11px;padding:10px}.metric-grid small,.detail-grid small{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}.metric-grid strong,.detail-grid strong{font-size:16px}.drawer{border-top:1px solid var(--line);padding-top:10px}summary{cursor:pointer;color:var(--accent);font-weight:650;font-size:14px}.drawer[open] summary{margin-bottom:10px}.advice ul{margin:0;padding-left:20px}.advice li{margin:6px 0}.advice-box{background:#0d1827;border:1px solid var(--line);border-radius:12px;padding:12px}.advice-box small{display:block;color:var(--accent);font-weight:700;margin-bottom:6px}.advice-box ul{margin:0;padding-left:20px}.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.filters button{border:1px solid var(--line);border-radius:999px;padding:8px 14px;background:var(--panel);color:var(--text);cursor:pointer;font:inherit;font-size:13px}.filters button[aria-pressed=true]{background:#1d4a63;border-color:var(--accent)}footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}[hidden]{display:none!important}@media(max-width:760px){.topbar nav{display:none}.grid-2{grid-template-columns:1fr}.hero{padding:30px 0 20px}.score{font-size:24px}}
'''
    issues = ''.join(f'<li>{e(item)}</li>' for item in analysis['issues'])
    strengths = ''.join(f'<li>{e(item)}</li>' for item in analysis['strengths'])
    timeline_items = ''.join(f'<li>{e(item)}</li>' for item in analysis.get('timeline_insights', []))
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(riot_id)} · LoL Coach</title><style>{css}</style></head><body>
<div class="topbar"><div class="topbar-inner"><div class="brand"><span class="brand-dot"></span>LoL Coach</div><nav><a href="#overview">Bilan</a><a href="#matchups">Matchups</a><a href="#champions">Champions</a><a href="#timeline">Timeline</a><a href="#matches">Parties</a></nav></div></div></div>
<main>
<header class="hero" id="overview"><span class="eyebrow">EUW · Solo/Duo</span><h1>{e(riot_id)}</h1><p>Ton bilan sur {len(games)} parties récentes, avec des conseils par champion et par matchup.</p><div class="hero-meta"><span class="chip">Rapport du {updated}</span><span class="chip">{len(games)} parties analysées</span></div></header>
<section class="section stats">{stats}</section>
<p class="note">Lecture prudente : les conseils sont des repères d’amélioration. Adapte-les au patch, aux objets, aux summons et au déroulement réel de la partie.</p>
<div class="grid-2 section"><section class="panel"><h2>Pistes à vérifier</h2><ul>{issues}</ul></section><section class="panel"><h2>Indicateurs favorables</h2><ul>{strengths}</ul></section></div>
<section class="section" id="matchups"><div class="section-head"><h2>Conseils par matchup</h2><p>Plan de jeu selon ton champion et l’adversaire du même rôle</p></div>{matchup_blocks}</section>
<section class="section" id="champions"><div class="section-head"><h2>Conseils par champion</h2><p>Basés sur le champion, ton rôle principal et tes parties récentes</p></div>{champion_blocks}</section>
<section class="section panel" id="timeline"><div class="section-head"><h2>Écarts moyens timeline</h2><p>Positif = avantage face à l’adversaire du même rôle</p></div><div class="table-wrap"><table><thead><tr><th>Repère</th><th>Parties</th><th>Or</th><th>XP</th><th>CS</th></tr></thead><tbody>{gap_rows}</tbody></table></div></section>
<section class="section panel"><h2>Moyennes par rôle</h2><div class="table-wrap"><table><thead><tr><th>Rôle</th><th>Parties</th><th>Winrate</th><th>KDA</th><th>Morts/10</th><th>CS/min</th><th>Dégâts/min</th><th>Vision/min</th><th>KP</th></tr></thead><tbody>{role_rows}</tbody></table></div></section>
<section class="section panel"><h2>Repères timeline</h2><ul>{timeline_items}</ul></section>
<section class="section" id="matches"><div class="section-head"><h2>Dernières parties</h2><p>Ouvre chaque partie pour voir le matchup, la timeline et les conseils</p></div><div class="filters"><button type="button" data-filter="all" aria-pressed="true">Toutes</button><button type="button" data-filter="win" aria-pressed="false">Victoires</button><button type="button" data-filter="loss" aria-pressed="false">Défaites</button></div><p id="match-count" class="hint">{len(games)} partie(s) affichée(s)</p>{cards}</section>
<footer>Analyse statistique et timeline post-match. Projet personnel non affilié à Riot Games.</footer>
</main>
<script>document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));let count=0;document.querySelectorAll('[data-result]').forEach(card=>{{card.hidden=button.dataset.filter!=='all'&&card.dataset.result!==button.dataset.filter;if(!card.hidden)count++;}});document.getElementById('match-count').textContent=count+' partie(s) affichée(s)';}}));</script>
</body></html>'''
