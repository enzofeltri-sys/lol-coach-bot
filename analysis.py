from statistics import mean
from collections import defaultdict


def find_player(match, puuid):
    return next(p for p in match['info']['participants'] if p['puuid'] == puuid)


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


def analyze_matches(matches, puuid):
    games = [analyze_match(m, puuid) for m in matches]
    if not games:
        raise ValueError('Aucune partie à analyser')
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
        strengths = ['Pas de point fort déduit automatiquement : échantillon insuffisant ou contexte manquant.']
    result = dict(games=games, avg_deaths=round(mean(g['deaths'] for g in games), 2),
                  avg_cs_per_min=round(mean(g['cs_per_min'] for g in games), 2),
                  avg_wards_per_min=round(mean(g['wards_per_min'] for g in games), 2),
                  avg_kda=round(mean(g['kda'] for g in games), 2),
                  win_rate=round(100 * sum(g['win'] for g in games) / len(games)),
                  issues=issues, strengths=strengths)
    for g in games:
        for key in ('cs_per_min', 'wards_per_min', 'duration_min', 'deaths_per_10'):
            g[key] = round(g[key], 2)
    return result
