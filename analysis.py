from statistics import mean
from collections import defaultdict

TIMELINE_MINUTES = (5, 10, 15, 20)

CHAMPION_ADVICE = {
    'Ahri': ['Utilise ton E pour créer une ouverture, puis enchaîne Q et W seulement si la cible est isolée.', 'Garde un flash ou une sortie après ton ultime.'],
    'Yasuo': ['Stack ton passif avant un trade et évite E dans une vague sans sortie.', 'Cherche un mur pour ton ultime, mais n’engage pas sans vision ou suivi.'],
    'Jinx': ['Reste derrière ta ligne et utilise les rockets pour piquer sans t’exposer.', 'Garde ton ultime pour les combats, fuites ou objectifs.'],
    'Ezreal': ['Poke avec Q hors de portée et utilise E pour fuir plutôt que pour agresser.', 'Garde ton ultime pour combats, objectifs ou une vague difficile.'],
    'Thresh': ['Avance avec ton allié avant de chercher un hook.', 'Garde la lanterne pour sauver un allié ou traverser un mur.'],
    'Amumu': ['Cherche un engage sur plusieurs ennemis groupés.', 'Communique tes timings d’ultime autour des objectifs.'],
    'Darius': ['Stack ton passif avant d’utiliser ton ultime.', 'Contrôle l’espace avec E et évite de poursuivre sans vision.'],
    'Malphite': ['Garde R pour engager plusieurs ennemis ou répondre au carry adverse.', 'Adapte tes résistances au type de dégâts adverse.'],
}

ROLE_ADVICE = {
    'TOP': ['Ne push pas sans vision et sans savoir où est le jungler adverse.', 'Utilise Téléport pour un combat d’objectif, pas pour revenir sans valeur.'],
    'MIDDLE': ['Push puis bouge vers un côté plutôt que de rester au milieu.', 'Garde une sortie avant d’engager.'],
    'JUNGLE': ['Planifie ta route autour du prochain objectif.', 'Ne conteste un objectif que si la vision ou la condition de combat est favorable.'],
    'BOTTOM': ['Respecte la portée de ton support et de l’adversaire avant un trade.', 'Vérifie jungler adverse et summons avant un engage.'],
    'UTILITY': ['Ward les entrées et objectifs avant qu’ils apparaissent.', 'Accompagne ton carry, mais pas dans une position sans vision.'],
    'UNKNOWN': ['Choisis une priorité simple : vision, vague ou positionnement.', 'Après chaque mort, identifie la cause principale.'],
}

MATCHUP_ADVICE = {
    ('ahri', 'zed'): ['Garde ton E pour éviter ou répondre au W de Zed, plutôt que de le lancer au hasard.', 'Ne reste pas à portée de son W : échange à distance puis recule.'],
    ('ahri', 'yasuo'): ['Évite de te placer derrière les minions : son E peut te rapprocher rapidement.', 'Garde ton E pour le windwall ou pour créer une distance après son engage.'],
    ('zed', 'ahri'): ['Utilise W pour bait son E, puis engage seulement après qu’il a été utilisé.', 'Ne poursuis pas dans le brouillard : Ahri peut reprendre une distance avec son R.'],
    ('yasuo', 'ahri'): ['Utilise le windwall pour bloquer Q ou E, puis cherche un trade court.', 'Ne dash pas à travers les minions si son E est disponible.'],
    ('jinx', 'ezreal'): ['Respecte sa portée de Q et ne trade pas sans avantage de minions ou de support.', 'Garde ton accès de recul pour son E : s’il l’utilise pour agresser, tu peux punir.'],
    ('ezreal', 'jinx'): ['Poke avec Q hors de sa portée et évite les échanges longs.', 'Utilise E pour esquiver un engage, pas pour avancer sans vision.'],
    ('thresh', 'leona'): ['Garde ta lanterne pour annuler un engage ou sauver ton ADC.', 'Ne hook pas sans que ton ADC puisse suivre : Leona peut encaisser et engager.'],
    ('leona', 'thresh'): ['Engage après que la lanterne ou le hook a été utilisé.', 'Utilise ton R pour couper la retraite plutôt que d’engager un duel isolé.'],
    ('darius', 'garen'): ['Stack ton passif avec les Q extérieurs avant d’utiliser ton ultime.', 'Évite les longs échanges si son passif est actif : recule puis reviens.'],
    ('garen', 'darius'): ['Ne reste pas dans son E prolongé : entre, trade, puis sors.', 'Garde ton Q pour supprimer un ralentissement ou terminer une fuite.'],
    ('malphite', 'darius'): ['Joue avec la distance : laisse-le push puis farme près de ta tour.', 'Garde ton R pour un gank ou pour répondre à son engage.'],
    ('amumu', 'jarvan iv'): ['Ne Q pas sans être sûr de toucher : son E-Q peut te suivre ou te punir.', 'Garde ton R pour un contre-engage quand son équipe est groupée.'],
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


def champion_advice(champion, role):
    key = next((name for name in CHAMPION_ADVICE if name.lower() == str(champion).lower()), None)
    return CHAMPION_ADVICE.get(key, ROLE_ADVICE.get(role, ROLE_ADVICE['UNKNOWN']))


def matchup_advice(champion, opponent, role):
    if not opponent:
        return ['Adversaire indisponible : concentre-toi sur le contrôle de vague, la vision et le positionnement.']
    pair = tuple(sorted([str(champion).lower(), str(opponent).lower()]))
    if pair in MATCHUP_ADVICE:
        return MATCHUP_ADVICE[pair]
    return [
        f'Identifie la compétence clé de {opponent} : attends qu’elle soit utilisée avant un trade.',
        f'Adapte ta position à la portée de {opponent} et garde une sortie près des minions ou d’un mur.',
        ROLE_ADVICE.get(role, ROLE_ADVICE['UNKNOWN'])[0],
    ]


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
        'advice': champion_advice(data['champion'], data['role']),
        'matchup_advice': matchup_advice(data['champion'], opponent_champion, data['role']),
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
    return {role: {'games': len(s), 'wins': sum(bool(g['win']) for g in s), 'win_rate': round(100 * sum(bool(g['win']) for g in s) / len(s), 1), 'avg_kda': round(mean(g['kda'] for g in s), 2), 'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in s), 2), 'avg_cs_per_min': round(mean(g['cs_per_min'] for g in s), 2), 'avg_damage_per_min': round(mean(g['damage_per_min'] for g in s), 2), 'avg_vision_per_min': round(mean(g['vision_per_min'] for g in s), 2), 'avg_kill_participation': round(mean(g['kill_participation'] for g in s), 1)} for role, s in groups.items()}


def champion_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        groups[game['champion']].append(game)
    result = {}
    for champion, sample in groups.items():
        role = max((g['role'] for g in sample), key=lambda r: sum(g['role'] == r for g in sample))
        result[champion] = {'games': len(sample), 'wins': sum(bool(g['win']) for g in sample), 'win_rate': round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1), 'role': role, 'avg_kda': round(mean(g['kda'] for g in sample), 2), 'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in sample), 2), 'avg_damage_per_min': round(mean(g['damage_per_min'] for g in sample), 2), 'avg_vision_per_min': round(mean(g['vision_per_min'] for g in sample), 2), 'advice': champion_advice(champion, role)}
    return dict(sorted(result.items(), key=lambda item: -item[1]['games']))


def matchup_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        if game.get('opponent_champion'):
            groups[(game['champion'], game['opponent_champion'])].append(game)
    result = {}
    for (champion, opponent), sample in groups.items():
        result[f'{champion} vs {opponent}'] = {'games': len(sample), 'wins': sum(bool(g['win']) for g in sample), 'win_rate': round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1), 'role': sample[0]['role'], 'avg_gold_gap_10': None, 'advice': matchup_advice(champion, opponent, sample[0]['role'])}
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
            point = next((p for p in game['timeline'] if p['minute'] == 10), None)
            if point:
                timeline_insights.append(f"{match_id[-8:]} · {game['champion']} vs {game.get('opponent_champion') or 'adversaire'} à 10 min | Or {point['gold_gap']:+d} · XP {point['xp_gap']:+d} · CS {point['cs_gap']:+d}.")
    groups = defaultdict(list)
    for g in games:
        if g['duration_min'] >= 10:
            groups[g['role']].append(g)
    issues, strengths = [], []
    for role, sample in sorted(groups.items(), key=lambda item: -len(item[1])):
        n = len(sample)
        prefix = f'{role} — {n} partie(s)'
        if n < 3:
            issues.append(f'{prefix} : échantillon trop petit pour proposer une tendance.')
            continue
        issues.append(f"{prefix} | {mean(g['deaths_per_10'] for g in sample):.1f} morts/10 min · {mean(g['damage_per_min'] for g in sample):.0f} dégâts/min · {mean(g['vision_per_min'] for g in sample):.1f} vision/min · {mean(g['kill_participation'] for g in sample):.0f}% KP.")
        wins = sum(g['win'] for g in sample)
        strengths.append(f'{prefix} : {wins} victoire(s), {n-wins} défaite(s).')
    if not timeline_insights:
        timeline_insights = ['Timelines indisponibles : ' + ' ; '.join(timeline_errors)] if timeline_errors else ['Aucun repère timeline exploitable.']
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
        win_rate=round(100 * sum(g['win'] for g in games) / len(games)), issues=issues, strengths=strengths,
        timeline_insights=timeline_insights, timeline_errors=timeline_errors,
    )
