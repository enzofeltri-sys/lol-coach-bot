from html import escape
from statistics import mean

MIN_PERIOD_GAMES = 5
MIN_FLAGGED = 3
CHANGE_THRESHOLD = 0.2

TREND_LABELS = {'improving': 'En progrès', 'stable': 'Stable', 'worsening': 'En régression', 'insufficient': 'Données insuffisantes'}
TREND_CLASSES = {'improving': 'good', 'stable': 'neutral', 'worsening': 'bad', 'insufficient': 'neutral'}
MAIN_ROLES = {'TOP', 'MIDDLE', 'BOTTOM', 'JUNGLE'}


def point10(game):
    return next((p for p in game.get('timeline', []) if p.get('minute') == 10), None)


SIGNALS = [
    {'key': 'early_gold', 'title': 'Sécuriser les 10 premières minutes', 'rule': 'un retard de 400 or ou plus à 10 minutes',
     'applies': lambda g: point10(g) is not None, 'value': lambda g: point10(g)['gold_gap'], 'flag': lambda g: point10(g)['gold_gap'] <= -400,
     'unit': lambda v: f'{v:+.0f} or à 10 min',
     'exercise': 'Après une mort, une vague perdue ou un recall, retourne d’abord sécuriser une ressource : vague, camp ou ward défensive. Ne cherche pas un trade avant d’avoir une information ou un avantage.'},
    {'key': 'deaths', 'title': 'Réduire les morts évitables', 'rule': 'au moins 5 morts par 10 minutes',
     'applies': lambda g: g['duration_min'] >= 10, 'value': lambda g: g['deaths_per_10'], 'flag': lambda g: g['deaths_per_10'] >= 5,
     'unit': lambda v: f'{v:.1f} morts/10 min',
     'exercise': 'Avant chaque engagement, vérifie trois choses : vision, position de tes alliés et sortie possible. Si une condition manque, farm ou contrôle la vision.'},
    {'key': 'participation', 'title': 'Être présent sur les combats utiles', 'rule': 'une participation aux kills sous 45 %',
     'applies': lambda g: g['role'] != 'UTILITY', 'value': lambda g: g['kill_participation'], 'flag': lambda g: g['kill_participation'] < 45,
     'unit': lambda v: f'{v:.0f} % de participation',
     'exercise': 'Dès que ta vague est poussée, regarde la map et prépare une rotation vers le prochain combat ou objectif.'},
    {'key': 'vision', 'title': 'Mieux contrôler la vision', 'rule': 'une vision faible pour ton rôle (moins de 1 par minute en support, moins de 0,5 sinon)',
     'applies': lambda g: True, 'value': lambda g: g['vision_per_min'],
     'flag': lambda g: g['vision_per_min'] < (1 if g['role'] == 'UTILITY' else 0.5),
     'unit': lambda v: f'{v:.2f} vision/min',
     'exercise': 'Avant chaque objectif ou déplacement vers une rivière, place une ward sur l’entrée ou la zone de passage.'},
    {'key': 'damage', 'title': 'Améliorer la contribution en combat', 'rule': 'moins de 18 % des dégâts d’équipe et moins de 500 dégâts par minute',
     'applies': lambda g: g['role'] in MAIN_ROLES, 'value': lambda g: g['damage_share'], 'flag': lambda g: g['damage_share'] < 18 and g['damage_per_min'] < 500,
     'unit': lambda v: f'{v:.1f} % des dégâts d’équipe',
     'exercise': 'En combat, reste à portée utile de la cible prioritaire sans être la première personne exposée.'},
]


def period_stats(items, signal):
    rows = [g for g in items if signal['applies'](g)]
    flagged = [g for g in rows if signal['flag'](g)]
    values = [signal['value'](g) for g in rows]
    return {'applicable': len(rows), 'flagged': len(flagged), 'average': mean(values) if values else None}


def trend_of(recent, previous):
    if recent['applicable'] < MIN_PERIOD_GAMES or previous['applicable'] < MIN_PERIOD_GAMES:
        return 'insufficient'
    delta = recent['flagged'] / recent['applicable'] - previous['flagged'] / previous['applicable']
    if delta <= -CHANGE_THRESHOLD:
        return 'improving'
    if delta >= CHANGE_THRESHOLD:
        return 'worsening'
    return 'stable'


def win_rate(items):
    return round(100 * sum(bool(g['win']) for g in items) / len(items))


def build_progress(games):
    half = len(games) // 2
    recent, previous = games[:half], games[half:2 * half]
    entries = []
    for signal in SIGNALS:
        total = period_stats(games, signal)
        if total['flagged'] == 0:
            continue
        now, before = period_stats(recent, signal), period_stats(previous, signal)
        trend = trend_of(now, before)
        rows = [g for g in games if signal['applies'](g)]
        hit = [g for g in rows if signal['flag'](g)]
        rest = [g for g in rows if not signal['flag'](g)]
        evidence = f"{total['flagged']} partie(s) sur {total['applicable']} avec {signal['rule']}."
        if len(hit) >= MIN_PERIOD_GAMES and len(rest) >= MIN_PERIOD_GAMES:
            evidence += f" Winrate : {win_rate(hit)} % dans ces {len(hit)} parties contre {win_rate(rest)} % dans les {len(rest)} autres — simple comparaison, pas une preuve de cause."
        fmt = lambda stats: signal['unit'](stats['average']) if stats['average'] is not None else '—'
        if now['applicable'] < MIN_PERIOD_GAMES:
            target = 'Pas assez de parties récentes pour fixer un objectif chiffré.'
        elif now['flagged'] == 0:
            target = f"Maintenir 0 partie concernée sur {now['applicable']}."
        else:
            target = f"Passer de {now['flagged']} à {now['flagged'] - 1} partie(s) concernée(s) sur {now['applicable']} dans la prochaine période."
        entries.append({'key': signal['key'], 'title': signal['title'], 'flagged_total': total['flagged'], 'applicable_total': total['applicable'],
                        'recent': now, 'previous': before, 'trend': trend, 'trend_label': TREND_LABELS[trend], 'evidence': evidence,
                        'exercise': signal['exercise'], 'target': target, 'average_recent': fmt(now), 'average_previous': fmt(before),
                        'rate': total['flagged'] / total['applicable']})
    entries.sort(key=lambda e: (-e['flagged_total'], -e['rate']))
    recurring = [e for e in entries if e['flagged_total'] >= MIN_FLAGGED]
    return {'games': len(games), 'recent_count': len(recent), 'previous_count': len(previous),
            'priority': recurring[0] if recurring else None,
            'others': [e for e in entries if not recurring or e is not recurring[0]][:3]}


def render_plan(progress):
    def e(value):
        return escape(str(value), quote=True)
    def count(period):
        return f"{period['flagged']} sur {period['applicable']}"
    note = f"Période récente : les {progress['recent_count']} parties les plus récentes. Période précédente : les {progress['previous_count']} parties d’avant. Seuils indicatifs, pas des tests statistiques : l’évolution est « en progrès » ou « en régression » à partir de {int(CHANGE_THRESHOLD * 100)} points d’écart, et il faut au moins {MIN_PERIOD_GAMES} parties par période."
    top = progress['priority']
    if top:
        body = (f'<section class="section panel"><div class="section-head"><h2>Priorité de progression</h2><p>Une seule priorité à travailler, suivie sur tes parties récentes</p></div>'
                f'<div class="match-head"><h2>{e(top["title"])}</h2><span class="pill {TREND_CLASSES[top["trend"]]}">{e(top["trend_label"])}</span></div>'
                f'<div class="advice-box"><small>Preuve dans tes parties</small><p>{e(top["evidence"])}</p></div>'
                f'<div class="advice-box"><small>Exercice pour les prochaines parties</small><p>{e(top["exercise"])}</p></div>'
                f'<div class="metric-grid"><div><small>Parties concernées · récentes</small><strong>{e(count(top["recent"]))}</strong></div>'
                f'<div><small>Parties concernées · précédentes</small><strong>{e(count(top["previous"]))}</strong></div>'
                f'<div><small>Moyenne récente</small><strong>{e(top["average_recent"])}</strong></div>'
                f'<div><small>Moyenne précédente</small><strong>{e(top["average_previous"])}</strong></div></div>'
                f'<p class="hint">Objectif : {e(top["target"])}</p><p class="hint">{e(note)}</p></section>')
    else:
        body = (f'<section class="section panel"><div class="section-head"><h2>Priorité de progression</h2></div>'
                f'<p>Aucun problème récurrent détecté : il faut au moins {MIN_FLAGGED} parties concernées par un même indicateur sur les {progress["games"]} parties analysées.</p>'
                f'<p class="hint">{e(note)}</p></section>')
    others = ''.join(f'<li><b>{e(o["title"])}</b> — {e(o["flagged_total"])} partie(s) sur {e(o["applicable_total"])} · récentes {e(count(o["recent"]))} · précédentes {e(count(o["previous"]))} · {e(o["trend_label"])}</li>' for o in progress['others'])
    second = f'<section class="section panel"><h2>Autres signaux</h2><ul>{others or "<li>Aucun autre signal dans les parties analysées.</li>"}</ul></section>'
    return '<div id="plan" class="tab-panel" role="tabpanel" aria-labelledby="tab-plan" hidden>\n' + body + '\n' + second + '\n</div>\n'


def attach_plan(html, progress):
    start = html.index('<div id="plan"')
    end = html.index('<div id="matchups"', start)
    return html[:start] + render_plan(progress) + html[end:]
