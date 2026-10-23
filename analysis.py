from statistics import mean
from collections import defaultdict

TIMELINE_MINUTES = (5, 10, 15, 20)

CHAMPION_ADVICE = {
    'Ahri': ['Utilise ton E pour créer une ouverture, puis enchaîne Q et W seulement si la cible est isolée.', 'Garde un flash ou une sortie après ton ultime : ne le consomme pas uniquement pour farming.'],
    'Yasuo': ['Stack ton passif avant un trade et évite d’utiliser E dans une vague sans issue de sortie.', 'Cherche les murs pour ton ultime, mais n’engage pas sans ton équipe ou sans vision.'],
    'Yone': ['Garde E pour rentrer puis ressortir du combat ; ne l’utilise pas pour push une vague dangereuse.', 'Attends un contrôle adverse ou un mur avant d’utiliser ton ultime.'],
    'Zed': ['Utilise W pour créer une sortie avant d’engager sur le carry adverse.', 'Ne reste pas au corps-à-corps après ton combo : recule et attends la prochaine fenêtre.'],
    'Jinx': ['Positionne-toi derrière ta ligne et utilise tes rockets pour piquer sans t’exposer.', 'Garde ton ultime pour les combats longs, les fuites ou les objectifs plutôt que pour un poke aléatoire.'],
    'Ashe': ['Utilise ton E pour sécuriser les entrées de jungle et préparer les objectifs.', 'Reste à distance maximale et utilise ton R pour initier seulement quand ton équipe peut suivre.'],
    'Ezreal': ['Poke avec Q en restant hors de portée, puis utilise E pour fuir plutôt que pour agresser sans besoin.', 'Garde ton ultime pour les combats, les objectifs ou une vague difficile à clear.'],
    'Lux': ['Pose tes wards avant de chercher un E ou un R à longue distance.', 'Utilise E pour contrôler une zone, puis Q seulement sur une cible importante ou pour te protéger.'],
    'Thresh': ['Avance avec ton allié avant de chercher un hook : un hook isolé donne rarement un kill sûr.', 'Garde la lanterne pour sauver un allié ou traverser un mur, pas seulement pour du engage.'],
    'Leona': ['Engage seulement quand ton ADC peut suivre et quand la vision adverse est limitée.', 'Utilise ton R pour couper une fuite ou initier un combat déjà favorable.'],
    'Amumu': ['Cherche un engage sur plusieurs ennemis groupés plutôt qu’un Q isolé sur le frontline.', 'Communique tes timings d’ultime autour des dragons, hérauts et barons.'],
    'Jarvan IV': ['Utilise E-Q pour engager une cible isolée, puis garde R pour enfermer le carry adverse.', 'Ne saute pas dans un combat sans savoir si ton équipe peut te suivre.'],
    'Master Yi': ['Attends que les contrôles adverses soient utilisés avant d’entrer dans le combat.', 'Farme les camps et les vagues entre les combats pour garder une avance d’or et d’objets.'],
    'Warwick': ['Cherche les cibles blessées avec ton ultime ou ton Q, plutôt que d’engager un ennemi en pleine santé.', 'Utilise ta régénération pour rester sur la map, mais évite les combats prolongés sans vision.'],
    'Darius': ['Cherche à stack ton passif avant d’utiliser ton ultime.', 'Contrôle l’espace avec ton E et évite de poursuivre trop loin sans vision.'],
    'Garen': ['Utilise ton Q pour supprimer un ralentissement et t’approcher, puis garde ton R pour exécuter une cible blessée.', 'Push puis recule : ton absence de mobilité te rend vulnérable aux ganks.'],
    'Malphite': ['Garde ton R pour engager plusieurs ennemis ou répondre à un carry bien positionné.', 'Construis la résistance adaptée : armure contre les dégâts physiques, résistance magique contre les dégâts magiques.'],
    'Gnar': ['Garde Mega Gnar pour un engage ou un contre-engage, pas pour push une vague sans vision.', 'Utilise Mini Gnar pour poke et contrôler la distance avant un combat.'],
}

ROLE_ADVICE = {
    'TOP': ['Priorise la gestion de vague : ne push pas sans vision et sans savoir où est le jungler adverse.', 'Utilise Téléport pour rejoindre un combat d’objectif plutôt que pour revenir en lane sans valeur.'],
    'MIDDLE': ['Push la vague puis bouge vers un côté de la map au lieu de rester statique au milieu.', 'Garde une sortie avant d’engager : un contrôle de plus dans la rivière peut décider du combat.'],
    'JUNGLE': ['Planifie ta route autour du prochain objectif et ne clear pas sans savoir où aider.', 'Ne conteste un objectif que si tu as une vision ou une condition de combat favorable.'],
    'BOTTOM': ['Respecte la portée de ton support et de l’adversaire : ne trade pas si tu es plus court sans condition gagnante.', 'Avant un engage, vérifie la position du jungler adverse et la disponibilité des summons.'],
    'UTILITY': ['Ward les entrées et les objectifs avant qu’ils apparaissent, pas après le combat.', 'Accompagne ton carry dans les rotations, mais ne le suis pas dans une position sans vision.'],
    'UNKNOWN': ['Choisis une priorité simple : vision, gestion de vague ou positionnement pendant les combats.', 'Après chaque mort, note la cause principale : position, vision, objectif ou engagement.'],
}


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
        'cc_per_min': round(player.get('timeCCingOthers', 0) / minutes, 2),
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
        cs = mine.get('minionsKilled', 0) + mine.get('jungleMinionsKilled', 0)
        opp_cs = theirs.get('minionsKilled', 0) + theirs.get('jungleMinionsKilled', 0)
        points.append({
            'minute': round(frame['timestamp'] / 60000, 1),
            'gold': mine.get('totalGold', 0), 'opp_gold': theirs.get('totalGold', 0),
            'gold_gap': mine.get('totalGold', 0) - theirs.get('totalGold', 0),
            'xp': mine.get('xp', 0), 'opp_xp': theirs.get('xp', 0),
            'xp_gap': mine.get('xp', 0) - theirs.get('xp', 0),
            'cs': cs, 'opp_cs': opp_cs, 'cs_gap': cs - opp_cs,
        })
    return points


def champion_advice(champion, role):
    key = next((name for name in CHAMPION_ADVICE if name.lower() == str(champion).lower()), None)
    if key:
        return CHAMPION_ADVICE[key]
    return ROLE_ADVICE.get(role, ROLE_ADVICE['UNKNOWN'])


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
        'advice': champion_advice(data['champion'], data['role']),
    })
    return data


def timeline_gap_averages(games):
    averages = {}
    for target in TIMELINE_MINUTES:
        points = [next((p for p in g.get('timeline', []) if p['minute'] == target), None) for g in games]
        points = [p for p in points if p]
        if not points:
            averages[target] = None
            continue
        averages[target] = {
            'games': len(points),
            'gold_gap': round(mean(p['gold_gap'] for p in points), 1),
            'xp_gap': round(mean(p['xp_gap'] for p in points), 1),
            'cs_gap': round(mean(p['cs_gap'] for p in points), 1),
        }
    return averages


def role_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        groups[game['role']].append(game)
    result = {}
    for role, sample in groups.items():
        result[role] = {
            'games': len(sample),
            'wins': sum(bool(g['win']) for g in sample),
            'win_rate': round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1),
            'avg_kda': round(mean(g['kda'] for g in sample), 2),
            'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in sample), 2),
            'avg_cs_per_min': round(mean(g['cs_per_min'] for g in sample), 2),
            'avg_damage_per_min': round(mean(g['damage_per_min'] for g in sample), 2),
            'avg_damage_taken_per_min': round(mean(g['damage_taken_per_min'] for g in sample), 2),
            'avg_gold_per_min': round(mean(g['gold_per_min'] for g in sample), 2),
            'avg_vision_per_min': round(mean(g['vision_per_min'] for g in sample), 2),
            'avg_cc_per_min': round(mean(g['cc_per_min'] for g in sample), 2),
            'avg_kill_participation': round(mean(g['kill_participation'] for g in sample), 1),
        }
    return dict(sorted(result.items(), key=lambda item: -item[1]['games']))


def champion_aggregates(games):
    groups = defaultdict(list)
    for game in games:
        groups[game['champion']].append(game)
    result = {}
    for champion, sample in groups.items():
        role = max((g['role'] for g in sample), key=lambda r: sum(g['role'] == r for g in sample))
        result[champion] = {
            'games': len(sample),
            'wins': sum(bool(g['win']) for g in sample),
            'win_rate': round(100 * sum(bool(g['win']) for g in sample) / len(sample), 1),
            'role': role,
            'avg_kda': round(mean(g['kda'] for g in sample), 2),
            'avg_deaths_per_10': round(mean(g['deaths_per_10'] for g in sample), 2),
            'avg_damage_per_min': round(mean(g['damage_per_min'] for g in sample), 2),
            'avg_vision_per_min': round(mean(g['vision_per_min'] for g in sample), 2),
            'advice': champion_advice(champion, role),
        }
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
                timeline_insights.append(
                    f"{match_id[-8:]} · {game['champion']} ({game['role']}) à 10 min | Or {point['gold']} vs {point['opp_gold']} ({point['gold_gap']:+d}) · "
                    f"XP {point['xp']} vs {point['opp_xp']} ({point['xp_gap']:+d}) · CS {point['cs']} vs {point['opp_cs']} ({point['cs_gap']:+d})."
                )
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
        deaths = mean(g['deaths_per_10'] for g in sample)
        damage = mean(g['damage_per_min'] for g in sample)
        vision = mean(g['vision_per_min'] for g in sample)
        kp = mean(g['kill_participation'] for g in sample)
        cc = mean(g['cc_per_min'] for g in sample)
        issues.append(f'{prefix} | {deaths:.1f} morts/10 min · {damage:.0f} dégâts/min · {vision:.1f} vision/min · {kp:.0f}% KP · {cc:.1f} CC/min.')
        wins = sum(g['win'] for g in sample)
        strengths.append(f'{prefix} : {wins} victoire(s), {n-wins} défaite(s).')
    if not timeline_insights:
        timeline_insights = ['Timelines indisponibles : ' + ' ; '.join(timeline_errors)] if timeline_errors else ['Aucun repère timeline exploitable.']
    result = dict(
        games=games,
        avg_deaths=round(mean(g['deaths'] for g in games), 2),
        avg_deaths_per_10=round(mean(g['deaths_per_10'] for g in games), 2),
        avg_cs_per_min=round(mean(g['cs_per_min'] for g in games), 2),
        avg_wards_per_min=round(mean(g['wards_per_min'] for g in games), 2),
        avg_vision_per_min=round(mean(g['vision_per_min'] for g in games), 2),
        avg_damage_per_min=round(mean(g['damage_per_min'] for g in games), 2),
        avg_damage_taken_per_min=round(mean(g['damage_taken_per_min'] for g in games), 2),
        avg_gold_per_min=round(mean(g['gold_per_min'] for g in games), 2),
        avg_kda=round(mean(g['kda'] for g in games), 2),
        avg_kill_participation=round(mean(g['kill_participation'] for g in games), 1),
        avg_cc_per_min=round(mean(g['cc_per_min'] for g in games), 2),
        total_towers=sum(g['objectives']['towers'] for g in games),
        total_dragons=sum(g['objectives']['dragons'] for g in games),
        total_barons=sum(g['objectives']['barons'] for g in games),
        total_heralds=sum(g['objectives']['heralds'] for g in games),
        timeline_gaps=timeline_gap_averages(games),
        role_aggregates=role_aggregates(games),
        champion_aggregates=champion_aggregates(games),
        win_rate=round(100 * sum(g['win'] for g in games) / len(games)),
        issues=issues, strengths=strengths,
        timeline_insights=timeline_insights, timeline_errors=timeline_errors,
    )
    return result
