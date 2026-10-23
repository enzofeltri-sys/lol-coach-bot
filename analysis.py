from statistics import mean
from collections import defaultdict


def find_player(match, puuid):
    return next(p for p in match['info']['participants'] if p['puuid'] == puuid)


def find_opponent(match, player):
    candidates = [p for p in match['info']['participants'] if p['teamId'] != player['teamId'] and p.get('teamPosition') == player.get('teamPosition')]
    return candidates[0] if len(candidates) == 1 else None


def timeline_snapshot(timeline, participant_id, target_minute=10):
    frames = timeline.get('info', {}).get('frames', [])
    usable = [f for f in frames if f.get('timestamp', 0) <= target_minute * 60000 and str(participant_id) in f.get('participantFrames', {})]
    if not usable:
        return None
    frame = usable[-1]
    data = frame['participantFrames'][str(participant_id)]
    return {
        'minute': round(frame['timestamp'] / 60000, 1),
        'gold': data.get('totalGold', 0),
        'xp': data.get('xp', 0),
        'cs': data.get('minionsKilled', 0) + data.get('jungleMinionsKilled', 0),
    }


def build_timeline_insight(match, timeline, puuid):
    player = find_player(match, puuid)
    opponent = find_opponent(match, player)
    if opponent is None:
        return []
    mine = timeline_snapshot(timeline, player['participantId'])
    theirs = timeline_snapshot(timeline, opponent['participantId'])
    if not mine or not theirs:
        return []
    role = player.get('teamPosition') or 'UNKNOWN'
    prefix = f"{match['info']['gameId']} · {player['championName']} ({role}) à {mine['minute']} min"
    insights = []
    gold_gap = mine['gold'] - theirs['gold']
    xp_gap = mine['xp'] - theirs['xp']
    cs_gap = mine['cs'] - theirs['cs']
    insights.append(f"{prefix} | Or : {mine['gold']} contre {theirs['gold']} ({gold_gap:+d}). Limite : l’écart ne dit pas comment il s’est créé. Action : revoir la période autour de 10 minutes et identifier une vague, un camp ou un objectif perdu.")
    insights.append(f"{prefix} | XP : {mine['xp']} contre {theirs['xp']} ({xp_gap:+d}). Limite : les rotations et les morts influencent fortement l’expérience. Action : repérer les moments où tu étais absent d’une voie ou d’un camp exploitable.")
    if role != 'UTILITY':
        insights.append(f"{prefix} | CS : {mine['cs']} contre {theirs['cs']} ({cs_gap:+d}). Limite : le style de voie, les ganks et les objectifs modifient ce total. Action : choisir une vague précise perdue et noter si une meilleure position ou un recall plus tôt était possible.")
    else:
        insights.append(f"{prefix} | CS : {mine['cs']} contre {theirs['cs']} ({cs_gap:+d}). Limite : le farm n’est pas la priorité principale d’un support. Action : revoir plutôt les occasions de vision et d’accompagnement autour de 10 minutes.")
    return insights


def analyze_match(match, puuid):
    p = find_player(match, puuid)
    minutes = match['info']['gameDuration'] / 60
    if minutes <= 0:
        raise ValueError('Durée de partie invalide')
    cs = p['totalMinionsKilled'] + p['neutralMinionsKilled']
    return dict(champion=p['championName'], role=p.get('teamPosition') or 'UNKNOWN',
                win=p['win'], kills=p['kills'], deaths=p['deaths'], assists=p['assists'],
                kda=round((p['kills'] + p['assists']) / max(p['deaths'], 1), 2),
                cs=cs, cs_per_min=cs / minutes, wards=p['wardsPlaced'],
                wards_per_min=p['wardsPlaced'] / minutes,
                damage=p['totalDamageDealtToChampions'], dragons=p.get('dragonKills', 0),
                barons=p.get('baronKills', 0), duration_min=minutes,
                deaths_per_10=p['deaths'] * 10 / minutes)


def analyze_matches(matches, puuid, timelines=None):
    timelines = timelines or {}
    games = [analyze_match(m, puuid) for m in matches]
    if not games:
        raise ValueError('Aucune partie à analyser')
    timeline_insights = []
    for match in matches:
        timeline = timelines.get(match['info']['gameId'])
        if timeline:
            timeline_insights.extend(build_timeline_insight(match, timeline, puuid))
    groups = defaultdict(list)
    for g in games:
        if g['duration_min'] >= 10:
            groups[g['role']].append(g)
    issues, strengths = [], []
    for role, sample in sorted(groups.items(), key=lambda item: -len(item[1])):
        n = len(sample)
        prefix = f'{role} — {n} partie(s)'
        if n < 3:
            issues.append(f'{prefix} : échantillon trop petit pour proposer une tendance. Action : accumuler au moins 3 parties sur ce rôle ; ce minimum reste un repère pratique, pas une garantie statistique.')
            continue
        deaths = mean(g['deaths_per_10'] for g in sample)
        issues.append(f'{prefix} | Observation : {deaths:.1f} mort(s) par 10 minutes en moyenne. Limite : ce nombre ne distingue pas un sacrifice utile d’une mort évitable. Action : revoir la première mort de chaque partie et noter une alternative possible, sans fixer arbitrairement un nombre maximal de morts.')
        if role in {'TOP', 'MIDDLE', 'BOTTOM', 'JUNGLE'}:
            farm = mean(g['cs_per_min'] for g in sample)
            low = min(sample, key=lambda g: g['cs_per_min'])
            issues.append(f'{prefix} | Observation : {farm:.1f} CS/min en moyenne ; minimum observé {low["cs_per_min"]:.1f} sur {low["champion"]}. Limite : champion, durée et scénario influencent cette mesure ; aucune comparaison de niveau n’est disponible. Action : revoir cette partie et rechercher une période où une vague ou un camp était récupérable sans abandonner un objectif plus important.')
        elif role == 'UTILITY':
            zero = sum(g['wards'] == 0 for g in sample)
            if zero:
                issues.append(f'{prefix} | Observation : aucune ward posée dans {zero}/{n} parties. Limite : cela ne décrit pas à lui seul la qualité du contrôle de vision. Action : revoir les occasions de poser une ward en sécurité avant les déplacements de l’équipe.')
        else:
            issues.append(f'{prefix} : rôle non reconnu ; aucun conseil spécifique au rôle n’est appliqué.')
        wins = sum(g['win'] for g in sample)
        strengths.append(f'{prefix} : {wins} victoire(s), {n-wins} défaite(s). Résultat descriptif uniquement ; il ne permet pas d’attribuer les victoires à une action précise.')
    excluded = len(games) - sum(map(len, groups.values()))
    if excluded:
        issues.append(f'{excluded} partie(s) de moins de 10 minutes exclue(s) des conseils pour limiter le poids des parties très courtes ; elles restent dans les statistiques globales.')
    if not issues:
        issues = ['Pas assez de parties exploitables pour proposer des conseils. Aucun diagnostic automatique.']
    if not strengths:
        strengths = ['Pas de point fort déduit automatique : échantillon insuffisant ou contexte manquant.']
    if not timeline_insights:
        timeline_insights = ['Aucun repère timeline exploitable : données indisponibles, adversaire non identifié ou partie trop courte.']
    result = dict(games=games, avg_deaths=round(mean(g['deaths'] for g in games), 2),
                  avg_cs_per_min=round(mean(g['cs_per_min'] for g in games), 2),
                  avg_wards_per_min=round(mean(g['wards_per_min'] for g in games), 2),
                  avg_kda=round(mean(g['kda'] for g in games), 2),
                  win_rate=round(100 * sum(g['win'] for g in games) / len(games)),
                  issues=issues, strengths=strengths, timeline_insights=timeline_insights)
    for g in games:
        for key in ('cs_per_min', 'wards_per_min', 'duration_min', 'deaths_per_10'):
            g[key] = round(g[key], 2)
    return result
