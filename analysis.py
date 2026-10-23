from statistics import mean
from collections import defaultdict

TIMELINE_MINUTES = (5, 10, 15, 20)


def find_player(match, puuid):
    return next(p for p in match['info']['participants'] if p['puuid'] == puuid)


def find_opponent(match, player):
    candidates = [p for p in match['info']['participants'] if p['teamId'] != player['teamId'] and p.get('teamPosition') == player.get('teamPosition')]
    return candidates[0] if len(candidates) == 1 else None


def team_objectives(match, player):
    team = next((t for t in match['info']['teams'] if t['teamId'] == player['teamId']), {})
    objectives = team.get('objectives', {})
    return {
        'towers': objectives.get('tower', {}).get('kills', 0),
        'dragons': objectives.get('dragon', {}).get('kills', 0),
        'barons': objectives.get('baron', {}).get('kills', 0),
        'heralds': objectives.get('riftHerald', {}).get('kills', 0),
        'inhibitors': objectives.get('inhibitor', {}).get('kills', 0),
    }


def participant_metrics(match, player, minutes):
    team_damage = sum(p.get('totalDamageDealtToChampions', 0) for p in match['info']['participants'] if p['teamId'] == player['teamId'])
    team_kills = sum(p.get('kills', 0) for p in match['info']['participants'] if p['teamId'] == player['teamId'])
    cs = player.get('totalMinionsKilled', 0) + player.get('neutralMinionsKilled', 0)
    damage = player.get('totalDamageDealtToChampions', 0)
    damage_taken = player.get('totalDamageTaken', 0)
    gold = player.get('goldEarned', 0)
    vision = player.get('visionScore', 0)
    kills, deaths, assists = player.get('kills', 0), player.get('deaths', 0), player.get('assists', 0)
    return {
        'champion': player.get('championName', 'Inconnu'),
        'role': player.get('teamPosition') or 'UNKNOWN',
        'win': player.get('win', False),
        'kills': kills, 'deaths': deaths, 'assists': assists,
        'kda': round((kills + assists) / max(deaths, 1), 2),
        'cs': cs, 'cs_per_min': round(cs / minutes, 2),
        'gold': gold, 'gold_per_min': round(gold / minutes, 2),
        'damage': damage, 'damage_per_min': round(damage / minutes, 2),
        'damage_share': round(100 * damage / team_damage, 1) if team_damage else 0,
        'damage_taken': damage_taken, 'damage_taken_per_min': round(damage_taken / minutes, 2),
        'wards': player.get('wardsPlaced', 0),
        'wards_per_min': round(player.get('wardsPlaced', 0) / minutes, 2),
        'vision_score': vision, 'vision_per_min': round(vision / minutes, 2),
        'cc_score': player.get('timeCCingOthers', 0),
        'kill_participation': round(100 * (kills + assists) / team_kills, 1) if team_kills else 0,
        'first_blood': bool(player.get('firstBloodKill') or player.get('firstBloodAssist')),
        'duration_min': round(minutes, 2),
        'deaths_per_10': round(deaths * 10 / minutes, 2),
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
        points.append({
            'minute': round(frame['timestamp'] / 60000, 1),
            'gold': mine.get('totalGold', 0), 'opp_gold': theirs.get('totalGold', 0),
            'xp': mine.get('xp', 0), 'opp_xp': theirs.get('xp', 0),
            'cs': mine.get('minionsKilled', 0) + mine.get('jungleMinionsKilled', 0),
            'opp_cs': theirs.get('minionsKilled', 0) + theirs.get('jungleMinionsKilled', 0),
        })
    return points


def analyze_match(match, puuid):
    player = find_player(match, puuid)
    minutes = match['info']['gameDuration'] / 60
    if minutes <= 0:
        raise ValueError('Durée de partie invalide')
    data = participant_metrics(match, player, minutes)
    data.update({
        'match_id': match['metadata']['matchId'],
        'patch': match['info'].get('gameVersion', 'inconnu'),
        'queue': match['info'].get('queueId'),
        'mode': match['info'].get('gameMode', 'inconnu'),
        'objectives': team_objectives(match, player),
        'timeline': [],
    })
    return data


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
                role = game['role']
                gold_gap = point['gold'] - point['opp_gold']
                xp_gap = point['xp'] - point['opp_xp']
                cs_gap = point['cs'] - point['opp_cs']
                timeline_insights.append(f"{match_id[-8:]} · {game['champion']} ({role}) à 10 min | Or {point['gold']} vs {point['opp_gold']} ({gold_gap:+d}) · XP {point['xp']} vs {point['opp_xp']} ({xp_gap:+d}) · CS {point['cs']} vs {point['opp_cs']} ({cs_gap:+d}). Limite : ces écarts ne prouvent pas une faute. Action : revoir les rotations, morts et objectifs autour de 10 minutes.")
    groups = defaultdict(list)
    for g in games:
        if g['duration_min'] >= 10:
            groups[g['role']].append(g)
    issues, strengths = [], []
    for role, sample in sorted(groups.items(), key=lambda item: -len(item[1])):
        n = len(sample)
        prefix = f'{role} — {n} partie(s)'
        if n < 3:
            issues.append(f'{prefix} : échantillon trop petit pour proposer une tendance. Action : accumuler au moins 3 parties sur ce rôle.')
            continue
        deaths = mean(g['deaths_per_10'] for g in sample)
        damage = mean(g['damage_per_min'] for g in sample)
        vision = mean(g['vision_per_min'] for g in sample)
        kp = mean(g['kill_participation'] for g in sample)
        issues.append(f'{prefix} | {deaths:.1f} morts/10 min · {damage:.0f} dégâts/min · {vision:.1f} vision/min · {kp:.0f}% participation aux kills. Limite : contexte et rôle non pris en compte. Action : choisir une seule priorité de relecture.')
        if role in {'TOP', 'MIDDLE', 'BOTTOM', 'JUNGLE'}:
            farm = mean(g['cs_per_min'] for g in sample)
            issues.append(f'{prefix} | {farm:.1f} CS/min en moyenne. Limite : champion, durée et scénario influencent ce total. Action : identifier une vague ou un camp perdu sans négliger un objectif plus important.')
        elif role == 'UTILITY':
            issues.append(f'{prefix} | La vision et la participation aux kills sont prioritaires sur le farm. Action : revoir les déplacements sans vision et les combats sans utilité.')
        wins = sum(g['win'] for g in sample)
        strengths.append(f'{prefix} : {wins} victoire(s), {n-wins} défaite(s). Résultat descriptif uniquement.')
    if not timeline_insights:
        if timeline_errors:
            timeline_insights = ['Timelines indisponibles : ' + ' ; '.join(timeline_errors)]
        else:
            timeline_insights = ['Aucun repère timeline exploitable : données indisponibles, adversaire non identifié ou partie trop courte.']
    result = dict(
        games=games,
        avg_deaths=round(mean(g['deaths'] for g in games), 2),
        avg_cs_per_min=round(mean(g['cs_per_min'] for g in games), 2),
        avg_wards_per_min=round(mean(g['wards_per_min'] for g in games), 2),
        avg_vision_per_min=round(mean(g['vision_per_min'] for g in games), 2),
        avg_damage_per_min=round(mean(g['damage_per_min'] for g in games), 2),
        avg_gold_per_min=round(mean(g['gold_per_min'] for g in games), 2),
        avg_kda=round(mean(g['kda'] for g in games), 2),
        avg_kill_participation=round(mean(g['kill_participation'] for g in games), 1),
        win_rate=round(100 * sum(g['win'] for g in games) / len(games)),
        issues=issues, strengths=strengths,
        timeline_insights=timeline_insights, timeline_errors=timeline_errors,
    )
    return result
