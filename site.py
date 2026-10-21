from html import escape
from datetime import datetime, timezone
from collections import defaultdict


def build_html(riot_id, analysis):
    def e(value):
        return escape(str(value), quote=True)

    games = analysis['games']
    updated = datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')
    cards = ''
    champions = defaultdict(lambda: [0, 0])
    for g in games:
        won = bool(g['win'])
        result = 'Victoire' if won else 'Défaite'
        state = 'win' if won else 'loss'
        champions[g['champion']][0] += 1
        champions[g['champion']][1] += int(won)
        cards += f"<article class='match {state}' data-result='{state}'><div><b>{e(g['champion'])}</b><small>{e(g['role'])} · {e(g.get('duration_min', '?'))} min</small></div><span class='badge'>{result}</span><div class='score'>{e(g['kills'])} / {e(g['deaths'])} / {e(g['assists'])}<small>K / D / A</small></div><div class='metrics'><span>{e(g['cs_per_min'])} CS/min</span><span>{e(g['wards_per_min'])} wards/min</span><span>{e(g['kda'])} KDA</span></div></article>"
    champion_rows = ''.join(f"<li><b>{e(name)}</b><span>{count} partie(s) · {wins}/{count} victoire(s)</span></li>" for name, (count, wins) in sorted(champions.items(), key=lambda item: -item[1][0]))
    stat_defs = [('Victoires', str(analysis['win_rate']) + '%'), ('KDA moyen', analysis['avg_kda']), ('CS / minute', analysis['avg_cs_per_min']), ('Wards / minute', analysis['avg_wards_per_min']), ('Morts / partie', analysis['avg_deaths'])]
    stats = ''.join(f'<div class="stat"><small>{e(label)}</small><strong>{e(value)}</strong></div>' for label, value in stat_defs)
    css = '''
:root{color-scheme:dark;--muted:#a9b7ca}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top right,#17314e,#080f1c 65%);color:#edf4ff;font:16px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 20px}header{padding:26px 0}h1{font-size:clamp(28px,6vw,46px);margin:8px 0}h2{font-size:21px}small,.muted{color:var(--muted)}small{display:block}a{color:#83d9ff}nav{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}nav a,button{border:1px solid #38516d;border-radius:10px;padding:10px 14px;background:#152438;color:#eaf4ff;text-decoration:none;cursor:pointer;font:inherit}button[aria-pressed=true]{background:#24556e;border-color:#78dbff}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px}.stat,.panel,.match{background:#101d2ee8;border:1px solid #2b3c54;border-radius:16px;padding:20px}.stat strong{font-size:30px;color:#83d9ff}.columns{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}.panel ul{padding-left:20px}.note{border-left:3px solid #eac579;padding:12px 16px;background:#302b213d;border-radius:6px}.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.match{display:grid;grid-template-columns:1fr auto;gap:16px;margin-bottom:12px;border-left:4px solid #fc8a98}.match.win{border-left-color:#69e3b0}.badge{font-size:14px;color:#fc9fab}.win .badge{color:#69e3b0}.score{font-size:22px;font-weight:700}.score small{font-size:12px;font-weight:400}.metrics{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:flex-end;color:var(--muted);font-size:14px}.champions{list-style:none;padding:0!important}.champions li{display:flex;justify-content:space-between;gap:15px;padding:10px 0;border-bottom:1px solid #2b3c54}.champions span{color:var(--muted)}footer{margin-top:32px;color:var(--muted);font-size:13px}[hidden]{display:none!important}@media(max-width:650px){.columns{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.metrics{justify-content:flex-start;grid-column:1/-1}.champions li{flex-direction:column;gap:0}main{padding:20px 14px}}
'''
    issues = ''.join(f'<li>{e(item)}</li>' for item in analysis['issues'])
    strengths = ''.join(f'<li>{e(item)}</li>' for item in analysis['strengths'])
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#080f1c"><title>{e(riot_id)} · LoL Coach</title><style>{css}</style></head><body><main>
<header><small>LOL COACH · EUW · SOLO/DUO</small><h1>{e(riot_id)}</h1><p class="muted">Ton bilan sur {len(games)} parties récentes, pour préparer la suivante.</p><small>Rapport généré le {updated}</small><nav><a href="#matches">Mes parties</a><a href="https://github.com/enzofeltri-sys/lol-coach-bot/actions/workflows/analyze.yml" target="_blank" rel="noopener">Ouvrir le workflow ↗</a></nav><small>Mise à jour horaire prévue, sous réserve d’une clé Riot valide. Ce lien ouvre GitHub et ne lance pas l’analyse à lui seul.</small></header>
<section class="stats" aria-label="Statistiques globales">{stats}</section>
<p class="note">Lecture prudente : ces moyennes ne prouvent pas des erreurs de décision. Les repères actuels ne sont pas adaptés à chaque rôle ; notamment, le farm d’un support ne se juge pas comme celui d’un carry. Le KDA ne mesure pas à lui seul l’impact.</p>
<div class="columns"><section class="panel"><h2>Pistes à vérifier</h2><ul>{issues}</ul></section><section class="panel"><h2>Indicateurs favorables</h2><ul>{strengths}</ul></section></div>
<section class="panel"><h2>Champions joués</h2><ul class="champions">{champion_rows}</ul></section>
<section id="matches"><h2>Dernières parties · ordre de récupération Riot</h2><div class="filters" role="group" aria-label="Filtrer les parties"><button type="button" data-filter="all" aria-pressed="true">Toutes</button><button type="button" data-filter="win" aria-pressed="false">Victoires</button><button type="button" data-filter="loss" aria-pressed="false">Défaites</button></div><p id="match-count" class="muted" aria-live="polite">{len(games)} partie(s) affichée(s)</p>{cards}</section>
<footer>Analyse statistique post-match, sans analyse vidéo ni diagnostic certain des décisions. Projet personnel non affilié à Riot Games. Aucune clé API n’est incluse dans cette page.</footer>
</main><script>document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));let count=0;document.querySelectorAll('[data-result]').forEach(card=>{{card.hidden=button.dataset.filter!=='all'&&card.dataset.result!==button.dataset.filter;if(!card.hidden)count++;}});document.getElementById('match-count').textContent=count+' partie(s) affichée(s)';}}));</script></body></html>'''
