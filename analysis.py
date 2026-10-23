from statistics import mean
from collections import defaultdict

TIMELINE_MINUTES = (5, 10, 15, 20)

ROLE_ADVICE = {
    'TOP': 'Sur la top lane, privilégie une vague sûre et une sortie avant chaque rotation.',
    'MIDDLE': 'Au mid, transforme l’avantage de vague en pression sur un côté plutôt qu’en attente au centre.',
    'JUNGLE': 'Au jungle, planifie la route autour du prochain objectif et évite les contestations sans information.',
    'BOTTOM': 'À l’ADC, trade uniquement lorsque la position du support et la vague te donnent un avantage.',
    'UTILITY': 'En support, place la vision avant les rotations et accompagne le carry sans t’exposer sans sortie.',
    'UNKNOWN': 'Choisis une priorité simple : vision, vague ou positionnement.',
}


def find_player(match, puuid):
    return next(p for p in match['info']['participants'] if p['puuid'] == puuid)


def find_opponent(match, player):
    candidates = [p for p in match['info']['participants'] if p['teamId'] != player['teamId'] and p.get('teamPosition') == player.get('teamPosition')]
    return candidates[0] if len(candidates) == 1 else None


def team_objectives(match, player):
    team = next((t for t in match['info']['teams'] if t['teamId'] == player['teamId']), {})
    objectives = team.get('objectives', {})
    return {k: objectives.get(key, {}).get('kills', 0) for k, key in [('towers', 'tower'), ('dragons', 'dragon'), ('barons', 'baron'), ('heralds', 'riftHerald'), ('inhibitors', 'inhibitor')]}


def participant_metrics(match, player, minutes):
    team_damage = sum(p.get('totalDamageDealtToChampions', 0) for p in match['info']['participants'] if p['teamId'] == player['teamId'])
    team_kills = sum(p.get('kills', 0) for p in match['info']['participants'] if p['teamId'] == player['teamId'])
    cs = player.get('totalMinionsKilled', 0) + player.get('neutralMinionsKilled', 0)
    damage = player.get('totalDamageDealtToChampions', 0)
    kills, deaths, assists = player.get('kills', 0), player.get('deaths', 0), player.get('assists', 0)
    return {
        'champion': player.get('championName', 'Inconnu'), 'role': player.get('teamPosition') or 'UNKNOWN', 'win': player.get('win', False),
        'kills': kills, 'deaths': deaths, 'assists': assists, 'kda': round((kills + assists) / max(deaths, 1), 2),
        'cs': cs, 'cs_per_min': round(cs / minutes, 2), 'gold': player.get('goldEarned', 0), 'gold_per_min': round(player.get('goldEarned', 0) / minutes, 2),
        'damage': damage, 'damage_per_min': round(damage / minutes, 2), 'damage_share': round(100 * damage / team_damage, 1) if team_damage else 0,
        'damage_taken': player.get('totalDamageTaken', 0), 'damage_taken_per_min': round(player.get('totalDamageTaken', 0) / minutes, 2),
        'wards': player.get('wardsPlaced', 0), 'wards_per_min': round(player.get('wardsPlaced', 0) / minutes, 2),
        'vision_score': player.get('visionScore', 0), 'vision_per_min': round(player.get('visionScore', 0) / minutes, 2),
        'cc_score': player.get('timeCCingOthers', 0), 'cc_per_min': round(player.get('timeCCingOthers', 0) / minutes, 2),
        'kill_participation': round(100 * (kills + assists) / team_kills, 1) if team_kills else 0,
        'first_blood': bool(player.get('firstBloodKill') or player.get('firstBloodAssist')),
        'duration_min': round(minutes, 2), 'deaths_per_10': round(deaths * 10 / minutes, 2),
    }


def timeline_points(timeline, player, opponent):
    frames = timeline.get('info', {}).get('frames', [])
    points = []
    for target in TIMELINE_MINUTES:
        usable = [f for f in frames if f.get('timestamp', 0) <= target * 60000]
        if not usable:
            continue
        frame = usable[-1]
        mine = frame.get('participantFrames', {}).get(str(player['participantId']))
        theirs = frame.get('participantFrames', {}).get(str(opponent['participantId']))
        if not mine or not theirs:
            continue
        cs = mine.get('minionsKilled', 0) + mine.get('jungleMinionsKilled', 0)
        opp_cs = theirs.get('minionsKilled', 0) + theirs.get('jungleMinionsKilled', 0)
        points.append({'minute': round(frame['timestamp'] / 60000, 1), 'gold': mine.get('totalGold', 0), 'opp_gold': theirs.get('totalGold', 0), 'gold_gap': mine.get('totalGold', 0) - theirs.get('totalGold', 0), 'xp': mine.get('xp', 0), 'opp_xp': theirs.get('xp', 0), 'xp_gap': mine.get('xp', 0) - theirs.get('xp', 0), 'cs': cs, 'opp_cs': opp_cs, 'cs_gap': cs - opp_cs})
    return points


def personalized_advice(game, point=None):
    advice = []
    role = game['role']
    if point:
        gold_gap, xp_gap, cs_gap = point['gold_gap'], point['xp_gap'], point['cs_gap']
        if gold_gap <= -400:
            advice.append(f"À 10 minutes, tu avais {abs(gold_gap)} or de retard sur {game.get('opponent_champion') or 'ton vis-à-vis'}. Revois les 10 premières minutes et identifie la première vague, mort ou rotation qui a fait basculer l’écart.")
        elif gold_gap >= 400:
            advice.append(f"À 10 minutes, tu menais de {gold_gap} or. Cherche comment convertir cet avantage : pression sur un objectif, accompagnement d’un allié ou contrôle de vision avant de retourner farm.")
        if role != 'UTILITY' and cs_gap <= -20:
            advice.append(f"Tu avais {abs(cs_gap)} CS de retard à 10 minutes. Repère une vague précise perdue : positionnement, recall trop tardif, rotation ou temps mort après un combat.")
        if xp_gap <= -500:
            advice.append(f"Ton retard d’expérience était de {abs(xp_gap)} XP à 10 minutes. Revois les moments où tu n’étais pas sur une voie ou un camp exploitable, surtout après une mort ou une rotation.")
    if game['deaths_per_10'] >= 5:
        advice.append(f"Tu es mort {game['deaths']} fois, soit {game['deaths_per_10']} morts/10 min. Pour la prochaine partie, choisis une règle simple : ne engage pas sans vision, sans avantage de vague ou sans savoir où sont deux ennemis.")
    if game['kill_participation'] < 45 and role != 'UTILITY':
        advice.append(f"Ta participation aux kills était de {game['kill_participation']}%. Repère un combat ou un objectif où tu étais trop loin : anticipe la rotation dès que la vague est poussée.")
    if role == 'UTILITY' and game['vision_per_min'] < 1:
        advice.append(f"Ton score de vision était de {game['vision_per_min']} par minute. Avant chaque objectif, place une ward sur l’entrée ou la rivière plutôt qu’au dernier moment.")
    elif role != 'UTILITY' and game['vision_per_min'] < 0.5:
        advice.append(f"Ton score de vision était de {game['vision_per_min']} par minute. Ajoute une ward défensive avant de pusher ou de t’éloigner de ta tour.")
    if role in {'TOP', 'MIDDLE', 'BOTTOM', 'JUNGLE'} and game['damage_share'] < 18 and game['damage_per_min'] < 500:
        advice.append(f"Tu as infligé seulement {game['damage_share']}% des dégâts de ton équipe. Revois ton positionnement en combat : reste à portée utile sans être la première cible.")
    if game['damage_taken_per_min'] > game['damage_per_min'] * 1.5 and game['damage_taken_per_min'] > 700:
        advice.append(f"Tu as subi beaucoup plus de dégâts que tu en as infligé ({game['damage_taken_per_min']} contre {game['damage_per_min']} par minute). Revois les engagements où tu es entré le premier sans sortie ni suivi.")
    if not advice:
        advice.append(f"Aucun signal majeur dans les repères disponibles. Continue à prioriser : {ROLE_ADVICE.get(role, ROLE_ADVICE['UNKNOWN'])}")
    return advice[:4]


def matchup_advice(game, point=None):
    opponent = game.get('opponent_champion')
    if not opponent:
        return ['Adversaire indisponible : concentre-toi sur le contrôle de vague, la vision et le positionnement.']
    advice = []
    if point:
        if point['gold_gap'] < 0:
            advice.append(f"Contre {opponent}, tu étais en retard de {abs(point['gold_gap'])} or à {point['minute']} minutes. Ne cherche pas un trade tant que tu n’as pas récupéré une vague, une ward défensive ou un avantage de position.")
        else:
            advice.append(f"Contre {opponent}, tu menais de {point['gold_gap']} or à {point['minute']} minutes. Utilise cet avantage pour contrôler la rivière ou accompagner un objectif, sans t’exposer seul.")
        if point['cs_gap'] < -10 and game['role'] != 'UTILITY':
            advice.append(f"Tu avais {abs(point['cs_gap'])} CS de retard contre {opponent}. Revois la vague juste avant ton premier désavantage : position, recall ou temps passé hors de la voie.")
    advice.append(f"Contre {opponent}, identifie sa compétence clé et garde une sortie pour répondre à son engagement.")
    advice.append(ROLE_ADVICE.get(game['role'], ROLE_ADVICE['UNKNOWN']))
    return advice[:4]


def progression_plan(games):
    def split_games(items):
        cut = max(1, len(items) // 2)
        return items[:cut], items[cut:]

    def win_rate(sample):
        return round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1) if sample else None

    def point10(game):
        return next((p for p in game.get('timeline', []) if p['minute'] == 10), None)

    recent_games, previous_games = split_games(games)
    signals = []

    def add_signal(key, title, condition, value_fn, format_fn, evidence_fn, exercise, metric, target, severity_fn):
        affected = [g for g in games if condition(g)]
        if not affected:
            return
        recent = [g for g in recent_games if condition(g)]
        previous = [g for g in previous_games if condition(g)]
        current_value = value_fn(affected)
        recent_value = value_fn(recent) if recent else None
        previous_value = value_fn(previous) if previous else None
        evolution = 'Pas assez de parties pour comparer les deux périodes.'
        if recent_value is not None and previous_value is not None:
            evolution = f"Évolution récente : {format_fn(previous_value)} → {format_fn(recent_value)} sur les parties concernées."
        affected_wr = win_rate(affected)
        others = [g for g in games if not condition(g)]
        others_wr = win_rate(others)
        impact = 'Impact non calculable avec l’échantillon actuel.'
        if affected_wr is not None and others_wr is not None:
            impact = f"Winrate : {affected_wr}% dans les parties concernées contre {others_wr}% dans les autres."
        signals.append({
            'key': key, 'title': title, 'count': len(affected),
            'evidence': f"{evidence_fn(affected)} {evolution} {impact}",
            'exercise': exercise, 'metric': metric,
            'current': format_fn(recent_value if recent_value is not None else current_value),
            'target': target, 'severity': severity_fn(affected),
        })

    def early_condition(g):
        point = point10(g)
        return bool(point and point['gold_gap'] <= -400)

    def early_value(sample):
        points = [point10(g) for g in sample if point10(g)]
        return mean(p['gold_gap'] for p in points) if points else None

    add_signal(
        'early_gold', 'Sécuriser les 10 premières minutes', early_condition, early_value,
        lambda value: f"{value:+.0f} or à 10 min",
        lambda affected: f"Retard moyen de {abs(round(mean(point10(g)['gold_gap'] for g in affected if point10(g)))):.0f} or à 10 minutes dans {len(affected)} partie(s).",
        'Après une mort, une vague perdue ou un recall, retourne d’abord sécuriser une ressource : vague, camp ou ward défensive. Ne cherche pas un trade avant d’avoir une information ou un avantage.',
        'Écart d’or à 10 minutes',
        'Réduire le retard moyen et avoir moins de parties sous -400 or.',
        lambda affected: abs(mean(point10(g)['gold_gap'] for g in affected if point10(g))),
    )

    add_signal(
        'deaths', 'Réduire les morts évitables',
        lambda g: g['deaths_per_10'] >= 5,
        lambda sample: mean(g['deaths_per_10'] for g in sample),
        lambda value: f"{value:.1f} morts/10 min",
        lambda affected: f"{len(affected)} partie(s) avec au moins 5 morts par 10 minutes ; moyenne de {mean(g['deaths_per_10'] for g in affected):.1f} dans ces parties.",
        'Avant chaque engagement, vérifie trois choses : vision, position de tes alliés et sortie possible. Si une condition manque, farm ou contrôle la vision.',
        'Morts par 10 minutes',
        'Faire baisser la moyenne de morts/10 min sur les prochaines parties.',
        lambda affected: mean(g['deaths_per_10'] for g in affected),
    )

    add_signal(
        'participation', 'Être présent sur les combats utiles',
        lambda g: g['role'] != 'UTILITY' and g['kill_participation'] < 45,
        lambda sample: mean(g['kill_participation'] for g in sample),
        lambda value: f"{value:.1f}% de participation",
        lambda affected: f"Participation aux kills sous 45% dans {len(affected)} partie(s).",
        'Dès que ta vague est poussée, regarde la map et prépare une rotation vers le prochain combat ou objectif.',
        'Participation aux kills',
        'Augmenter la participation aux kills sans abandonner tes ressources.',
        lambda affected: 45 - mean(g['kill_participation'] for g in affected),
    )

    def vision_condition(g):
        return (g['role'] == 'UTILITY' and g['vision_per_min'] < 1) or (g['role'] != 'UTILITY' and g['vision_per_min'] < 0.5)

    add_signal(
        'vision', 'Mieux contrôler la vision', vision_condition,
        lambda sample: mean(g['vision_per_min'] for g in sample),
        lambda value: f"{value:.2f} vision/min",
        lambda affected: f"Vision faible dans {len(affected)} partie(s), selon le rôle.",
        'Avant chaque objectif ou déplacement vers une rivière, place une ward sur l’entrée ou la zone de passage.',
        'Score de vision par minute',
        'Placer une information utile avant les rotations et objectifs.',
        lambda affected: 1 - mean(g['vision_per_min'] for g in affected),
    )

    def damage_condition(g):
        return g['role'] in {'TOP', 'MIDDLE', 'BOTTOM', 'JUNGLE'} and g['damage_share'] < 18 and g['damage_per_min'] < 500

    add_signal(
        'damage', 'Améliorer la contribution en combat', damage_condition,
        lambda sample: mean(g['damage_share'] for g in sample),
        lambda value: f"{value:.1f}% des dégâts d’équipe",
        lambda affected: f"Moins de 18% des dégâts d’équipe dans {len(affected)} partie(s).",
        'En combat, reste à portée utile de la cible prioritaire sans être la première personne exposée.',
        'Part des dégâts d’équipe',
        'Augmenter la contribution sans prendre plus de risques inutiles.',
        lambda affected: 18 - mean(g['damage_share'] for g in affected),
    )

    if not signals:
        return {'priority': 'Continuer la progression', 'why': 'Aucun signal récurrent suffisamment fort dans les données actuelles.', 'evidence': 'Les indicateurs disponibles ne montrent pas de schéma dominant.', 'exercise': ROLE_ADVICE.get(games[0]['role'], ROLE_ADVICE['UNKNOWN']), 'metric': 'À définir après davantage de parties', 'current': '—', 'target': 'Jouer quelques parties supplémentaires pour identifier un schéma.', 'affected_games': 0, 'secondary': []}
    signals.sort(key=lambda s: (-s['count'], -s['severity']))
    primary = signals[0]
    primary['secondary'] = [{'title': s['title'], 'count': s['count'], 'metric': s['metric'], 'current': s['current']} for s in signals[1:3]]
    primary['affected_games'] = primary['count']
    return primary


def analyze_match(match, puuid):
    player = find_player(match, puuid)
    minutes = match['info']['gameDuration'] / 60
    if minutes <= 0:
        raise ValueError('Durée de partie invalide')
    data = participant_metrics(match, player, minutes)
    opponent = find_opponent(match, player)
    opponent_champion = opponent.get('championName') if opponent else None
    data.update({
        'match_id': match['metadata']['matchId'], 'patch': match['info'].get('gameVersion', 'inconnu'),
        'queue': match['info'].get('queueId'), 'mode': match['info'].get('gameMode', 'inconnu'),
        'opponent_champion': opponent_champion, 'objectives': team_objectives(match, player), 'timeline': [],
        'advice': [], 'matchup_advice': [],
    })
    return data


def timeline_gap_averages(games):
    averages = {}
    for target in TIMELINE_MINUTES:
        points = [next((p for p in g.get('timeline', []) if p['minute'] == target), None) for g in games]
        points = [p for p in points if p]
        averages[target] = None if not points else {'games': len(points), 'gold_gap': round(mean(p['gold_gap'] for p in points), 1), 'xp_gap': round(mean(p['xp_gap'] for p in points), 1), 'cs_gap': round(mean(p['cs_gap'] for p in points), 1)}
    return averages


def role_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        groups[game['role']].append(game)
    return {role: {'games': len(s), 'win_rate': round(100 * sum(bool(g['win']) for g in s) / len(s), 1), 'avg_kda': round(mean(g['kda'] for g in s), 2), 'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in s), 2), 'avg_cs_per_min': round(mean(g['cs_per_min'] for g in s), 2), 'avg_damage_per_min': round(mean(g['damage_per_min'] for g in s), 2), 'avg_vision_per_min': round(mean(g['vision_per_min'] for g in s), 2), 'avg_kill_participation': round(mean(g['kill_participation'] for g in s), 1)} for role, s in groups.items()}


def champion_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        groups[game['champion']].append(game)
    result = {}
    for champion, sample in groups.items():
        role = max((g['role'] for g in sample), key=lambda r: sum(g['role'] == r for g in sample))
        result[champion] = {'games': len(sample), 'win_rate': round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1), 'role': role, 'avg_kda': round(mean(g['kda'] for g in sample), 2), 'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in sample), 2), 'avg_damage_per_min': round(mean(g['damage_per_min'] for g in sample), 2), 'avg_vision_per_min': round(mean(g['vision_per_min'] for g in sample), 2), 'advice': personalized_advice(sample[0], next((p for p in sample[0].get('timeline', []) if p['minute'] == 10), None))}
    return dict(sorted(result.items(), key=lambda item: -item[1]['games']))


def matchup_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        if game.get('opponent_champion'):
            groups[(game['champion'], game['opponent_champion'])].append(game)
    result = {}
    for (champion, opponent), sample in groups.items():
        point = next((p for p in sample[0].get('timeline', []) if p['minute'] == 10), None)
        win_rate = round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1)
        result[f'{champion} vs {opponent}'] = {'games': len(sample), 'win_rate': win_rate, 'role': sample[0]['role'], 'champion': champion, 'opponent': opponent, 'performance': 'good' if win_rate >= 50 else 'bad', 'avg_gold_gap_10': point['gold_gap'] if point else None, 'advice': matchup_advice(sample[0], point)}
    return dict(sorted(result.items(), key=lambda item: -item[1]['games']))


def analyze_matches(matches, puuid, timelines=None, timeline_errors=None):
    timelines = timelines or {}
    timeline_errors = timeline_errors or []
    games = [analyze_match(m, puuid) for m in matches]
    if not games:
        raise ValueError('Aucune partie à analyser')
    timeline_insights = []
    for match in matches:
        match_id = match['metadata']['matchId']
        timeline = timelines.get(match_id)
        game = next(g for g in games if g['match_id'] == match_id)
        if not timeline:
            continue
        player = find_player(match, puuid)
        opponent = find_opponent(match, player)
        if opponent:
            game['timeline'] = timeline_points(timeline, player, opponent)
            point10 = next((p for p in game['timeline'] if p['minute'] == 10), None)
            game['advice'] = personalized_advice(game, point10)
            game['matchup_advice'] = matchup_advice(game, point10)
            if point10:
                timeline_insights.append(f"{match_id[-8:]} · {game['champion']} vs {game.get('opponent_champion') or 'adversaire'} à 10 min | Or {point10['gold_gap']:+d} · XP {point10['xp_gap']:+d} · CS {point10['cs_gap']:+d}. {game['advice'][0]}")
        else:
            game['advice'] = personalized_advice(game)
            game['matchup_advice'] = matchup_advice(game)
    groups = defaultdict(list)
    for g in games:
        if g['duration_min'] >= 10:
            groups[g['role']].append(g)
    issues, strengths = [], []
    for role, sample in sorted(groups.items(), key=lambda item: -len(item[1])):
        n = len(sample)
        if n < 3:
            issues.append(f'{role} — {n} partie(s) : échantillon trop petit pour une tendance.')
            continue
        deaths = mean(g['deaths_per_10'] for g in sample)
        damage = mean(g['damage_per_min'] for g in sample)
        vision = mean(g['vision_per_min'] for g in sample)
        kp = mean(g['kill_participation'] for g in sample)
        issues.append(f"{role} — {n} partie(s) | {deaths:.1f} morts/10 min · {damage:.0f} dégâts/min · {vision:.1f} vision/min · {kp:.0f}% KP. Priorité : revoir les moments où tu perds l’initiative.")
        wins = sum(g['win'] for g in sample)
        strengths.append(f"{role} — {n} partie(s) : {wins} victoire(s), {n-wins} défaite(s). Résultat descriptif uniquement.")
    if not timeline_insights:
        timeline_insights = ['Timelines indisponibles : ' + ' ; '.join(timeline_errors)] if timeline_errors else ['Aucun repère timeline exploitable.']
    matchup_filters = {'roles': sorted({g['role'] for g in games}), 'champions': sorted({g['champion'] for g in games})}
    return dict(
        games=games,
        avg_deaths=round(mean(g['deaths'] for g in games), 2), avg_deaths_per_10=round(mean(g['deaths_per_10'] for g in games), 2),
        avg_cs_per_min=round(mean(g['cs_per_min'] for g in games), 2), avg_wards_per_min=round(mean(g['wards_per_min'] for g in games), 2),
        avg_vision_per_min=round(mean(g['vision_per_min'] for g in games), 2), avg_damage_per_min=round(mean(g['damage_per_min'] for g in games), 2),
        avg_damage_taken_per_min=round(mean(g['damage_taken_per_min'] for g in games), 2), avg_gold_per_min=round(mean(g['gold_per_min'] for g in games), 2),
        avg_kda=round(mean(g['kda'] for g in games), 2), avg_kill_participation=round(mean(g['kill_participation'] for g in games), 1),
        avg_cc_per_min=round(mean(g['cc_per_min'] for g in games), 2),
        total_towers=sum(g['objectives']['towers'] for g in games), total_dragons=sum(g['objectives']['dragons'] for g in games),
        total_barons=sum(g['objectives']['barons'] for g in games), total_heralds=sum(g['objectives']['heralds'] for g in games),
        timeline_gaps=timeline_gap_averages(games), role_aggregates=role_aggregates(games),
        champion_aggregates=champion_aggregates(games), matchup_aggregates=matchup_aggregates(games),
        matchup_filters=matchup_filters, progression_plan=progression_plan(games),
        win_rate=round(100 * sum(g['win'] for g in games) / len(games)), issues=issues, strengths=strengths,
        timeline_insights=timeline_insights, timeline_errors=timeline_errors,
    )
