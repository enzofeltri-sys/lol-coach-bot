from html import escape
from progress import SIGNALS

SIGNAL_BY_KEY = {s['key']: s for s in SIGNALS}
FLAG_ORDER = ['deaths', 'early_gold', 'vision', 'participation', 'damage']
MAX_MOMENTS = 3
CONVERSION_TITLE = 'Convertir une avance'
CONVERSION_EXERCISE = 'Quand tu prends de l’avance, choisis un objectif précis (tour, Héraut ou dragon) avant de retourner farm, et pars-y dès que ta vague est poussée.'


def fmt_minute(value):
    return f'{value:.1f}'.replace('.', ',') + ' min'


def build_moments(game):
    decisive = game.get('decisive_moments')
    if not decisive:
        return []
    opponent = game.get('opponent_champion') or 'ton adversaire direct'
    moments = []
    death = decisive.get('early_death')
    if death:
        moments.append({'priority': 1, 'minute': death['minute'], 'signal': 'deaths', 'title': SIGNAL_BY_KEY['deaths']['title'],
                        'fact': f"Première mort à {fmt_minute(death['minute'])} (avant 14 min).",
                        'question': 'Que savais-tu de la position de ton adversaire et de son jungler juste avant ? Avais-tu une sortie ?'})
    gap = decisive.get('first_disadvantage')
    if gap:
        moments.append({'priority': 2, 'minute': gap['minute'], 'signal': 'early_gold', 'title': SIGNAL_BY_KEY['early_gold']['title'],
                        'fact': f"Premier repère en désavantage : {gap['gap']:+.0f} {gap['metric']} à {fmt_minute(gap['minute'])} face à {opponent}.",
                        'question': 'Que s’est-il passé dans les 5 minutes avant ce repère : vague perdue, rotation, échange ou mort ?'})
    conversion = decisive.get('advantage_conversion')
    if conversion and conversion.get('status') == 'lost' and conversion.get('next_gold_gap') is not None:
        moments.append({'priority': 3, 'minute': 10.0, 'signal': None, 'title': CONVERSION_TITLE,
                        'fact': f"{conversion['lead']:+.0f} or d’avance à 10 min, puis {conversion['next_gold_gap']:+.0f} au repère suivant (écart réduit de plus de moitié).",
                        'question': 'Qu’as-tu fait de cette avance : tour, objectif, pression de lane ou retour au farm ?'})
    return sorted(sorted(moments, key=lambda m: m['priority'])[:MAX_MOMENTS], key=lambda m: m['minute'])


def build_strengths(game):
    strengths = []
    decisive = game.get('decisive_moments') or {}
    conversion = decisive.get('advantage_conversion')
    if conversion and conversion.get('status') == 'maintained':
        strengths.append(f"Avance de {conversion['lead']:+.0f} or à 10 min conservée au repère suivant.")
    if game['deaths_per_10'] <= 2 and game['duration_min'] >= 10:
        strengths.append(f"{game['deaths']} mort(s) en {game['duration_min']:.0f} min ({game['deaths_per_10']:.1f} pour 10 min).")
    if game['role'] != 'UTILITY' and game['kill_participation'] >= 60:
        strengths.append(f"Participation aux kills de {game['kill_participation']:.0f} %.")
    return strengths[:2]


def build_debrief(game):
    moments = build_moments(game)
    main = None
    action = None
    if moments:
        first = min(moments, key=lambda m: m['priority'])
        main = {'title': first['title'], 'why': first['fact']}
        action = SIGNAL_BY_KEY[first['signal']]['exercise'] if first['signal'] else CONVERSION_EXERCISE
    else:
        for key in FLAG_ORDER:
            signal = SIGNAL_BY_KEY[key]
            if signal['applies'](game) and signal['flag'](game):
                main = {'title': signal['title'], 'why': f"Cette partie correspond au critère : {signal['rule']}."}
                action = signal['exercise']
                break
    return {'timeline': game.get('decisive_moments') is not None, 'strengths': build_strengths(game), 'moments': moments, 'main': main, 'action': action}


def render_debrief(debrief):
    def e(value):
        return escape(str(value), quote=True)
    parts = ["<section class='debrief'><h3>Débrief</h3>"]
    if not debrief['timeline']:
        parts.append("<p class='hint'>Timeline indisponible pour cette partie : seuls les indicateurs de fin de partie sont utilisés.</p>")
    strengths = ''.join(f'<li>{e(item)}</li>' for item in debrief['strengths']) or '<li>Aucun point fort net dans les indicateurs suivis.</li>'
    parts.append(f"<div class='advice-box'><small>Points forts (données du match)</small><ul>{strengths}</ul></div>")
    if debrief['moments']:
        items = ''.join(f"<li><b>{e(fmt_minute(m['minute']))}</b> — {e(m['fact'])}<br>Question à te poser : {e(m['question'])}</li>" for m in debrief['moments'])
        parts.append(f"<div class='advice-box'><small>Passages à revoir</small><ul>{items}</ul></div>")
    if debrief['main']:
        parts.append(f"<div class='advice-box'><small>Priorité de cette partie</small><p><b>{e(debrief['main']['title'])}</b> — {e(debrief['main']['why'])}</p></div>")
        parts.append(f"<div class='advice-box'><small>Action pour la prochaine partie</small><p>{e(debrief['action'])}</p></div>")
    else:
        parts.append("<div class='advice-box'><small>Priorité de cette partie</small><p>Aucun point à revoir détecté dans les indicateurs suivis.</p></div>")
    parts.append("<p class='hint'>Les faits viennent des données du match. Les questions sont des pistes de relecture, pas des conclusions.</p></section>")
    return ''.join(parts)


def attach_debriefs(html, games):
    marker = "<article class='match "
    starts = []
    position = html.find(marker)
    while position >= 0:
        starts.append(position)
        position = html.find(marker, position + 1)
    if len(starts) != len(games):
        print(f'::warning::Débriefs ignorés : {len(starts)} cartes de parties pour {len(games)} parties analysées')
        return html
    for start, game in reversed(list(zip(starts, games))):
        end = html.index('</article>', start)
        anchor = html.find("<div class='score-row'>", start, end)
        insert_at = anchor if anchor >= 0 else end
        html = html[:insert_at] + render_debrief(build_debrief(game)) + html[insert_at:]
    return html
