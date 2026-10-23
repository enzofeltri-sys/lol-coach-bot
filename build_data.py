import json
import urllib.request

DDRAGON_VERSIONS = 'https://ddragon.leagueoflegends.com/api/versions.json'
DDRAGON_BASE = 'https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR'
DDRAGON_IMAGES = 'https://ddragon.leagueoflegends.com/cdn/img'
CDRAGON_BASE = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1'
RUNE_RECOMMENDATIONS = f'{CDRAGON_BASE}/champion-rune-recommendations.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; LoLCoachBot/1.0)'}


def fetch_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def load_build_data():
    version = fetch_json(DDRAGON_VERSIONS)[0]
    champions = fetch_json(f'{DDRAGON_BASE.format(version=version)}/champion.json')['data']
    items = fetch_json(f'{DDRAGON_BASE.format(version=version)}/item.json')['data']
    runes = fetch_json(f'{DDRAGON_BASE.format(version=version)}/runesReforged.json')
    rune_recommendations = fetch_json(RUNE_RECOMMENDATIONS)
    return {'version': version, 'champions': champions, 'items': items, 'runes': runes, 'rune_recommendations': rune_recommendations}


def rune_icon(style_name, data):
    for style in data.get('runes', []):
        if style.get('name') == style_name:
            return f"https://ddragon.leagueoflegends.com/cdn/img/{style.get('icon', '')}"
    return ''


def rune_details(style_name, rune_ids, data):
    for style in data.get('runes', []):
        if style.get('name') != style_name:
            continue
        details = []
        for slot in style.get('slots', []):
            for rune in slot.get('runes', []):
                if rune.get('id') in rune_ids:
                    details.append({'name': rune.get('name', ''), 'icon': f"https://ddragon.leagueoflegends.com/cdn/img/{rune.get('icon', '')}"})
        return details
    return []


def find_rune_entry(recommendations, champion_keys):
    keys = {str(key).lower() for key in champion_keys if key}
    if isinstance(recommendations, dict):
        for key in keys:
            if key in recommendations:
                return recommendations[key]
        return None
    if isinstance(recommendations, list):
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            values = {str(item.get(field, '')).lower() for field in ('championKey', 'champion', 'championId', 'key', 'name', 'id')}
            if keys & values:
                return item
    return None


def recommended_runes(champion_key, numeric_key, data):
    recommendations = data.get('rune_recommendations', [])
    entry = find_rune_entry(recommendations, [champion_key, numeric_key])
    if not entry:
        return {'primary': 'Recommandation indisponible', 'secondary': 'Recommandation indisponible', 'shards': 'Adaptation / Adaptation / Défense', 'primary_icon': '', 'secondary_icon': '', 'primary_runes': [], 'source': 'CommunityDragon'}
    if isinstance(entry, list):
        pages = entry
    elif isinstance(entry, dict):
        pages = entry.get('recommendations') or entry.get('runes') or []
    else:
        pages = []
    first = pages[0] if pages else {}
    primary = first.get('primaryStyleName') or first.get('primaryStyle') or 'Recommandation indisponible'
    secondary = first.get('subStyleName') or first.get('subStyle') or 'Recommandation indisponible'
    shards = ' / '.join(str(shard) for shard in first.get('statShards', [])) or 'Adaptation / Adaptation / Défense'
    rune_ids = first.get('primaryRuneIds') or first.get('selectedPerkIds') or []
    return {'primary': primary, 'secondary': secondary, 'shards': shards, 'primary_icon': rune_icon(primary, data), 'secondary_icon': rune_icon(secondary, data), 'primary_runes': rune_details(primary, rune_ids, data), 'source': 'CommunityDragon'}


def champion_build(champion_key, role, opponent_key, data):
    champion = data['champions'].get(champion_key)
    opponent = data['champions'].get(opponent_key)
    if not champion:
        raise ValueError(f'Champion inconnu : {champion_key}')
    if not opponent:
        raise ValueError(f'Adversaire inconnu : {opponent_key}')
    opponent_tags = opponent.get('tags', [])
    is_magic = 'Mage' in opponent_tags
    is_physical = 'Fighter' in opponent_tags or 'Marksman' in opponent_tags or 'Assassin' in opponent_tags
    numeric_key = champion.get('key')
    runes = recommended_runes(champion_key, numeric_key, data)
    return {
        'champion': champion['name'],
        'opponent': opponent['name'],
        'role': role,
        'patch': data['version'],
        'runes': runes,
        'summoners': ['Flash', 'Téléport' if role in {'TOP', 'MIDDLE'} else 'Soin' if role == 'BOTTOM' else 'Ignite'],
        'skill_order': 'Q > E > W, R aux niveaux 6, 11 et 16',
        'starting_items': ['Potion de santé', 'Ward furtive'],
        'core_items': ['Premier item selon le matchup', 'Deuxième item selon la composition', 'Troisième item selon l’état de la partie'],
        'situational_items': (['Résistance magique contre les dégâts AP'] if is_magic else []) + (['Armure contre les dégâts physiques'] if is_physical else []) + ['Anti-soin si régénération ennemie', 'Contrôle si menaces CC'],
        'power_spikes': [
            {'moment': 'Niveau 2', 'advice': f"Contre {opponent['name']}, identifie sa deuxième compétence et évite son premier trade tant que tu n’as pas d’avantage de vague ou de vision."},
            {'moment': 'Niveau 3', 'advice': f"Contre {opponent['name']}, cherche un trade seulement si sa compétence clé est indisponible ou si tu as une sortie."},
            {'moment': 'Niveau 6', 'advice': f"Contre {opponent['name']}, respecte son ultimate : ne engage pas sans savoir s’il est disponible."},
            {'moment': 'Premier item', 'advice': 'Utilise le spike pour convertir l’avantage en tour, objectif ou pression de map.'},
            {'moment': 'Deux items', 'advice': 'Pic de puissance fréquent : cherche un combat contrôlé ou un objectif.'},
            {'moment': 'Niveaux 11 et 16', 'advice': 'Montées d’ultimate : repositionne-toi autour des combats d’équipe et des objectifs.'},
        ],
        'matchup_plan': [
            f"Identifie la compétence clé de {opponent['name']} et garde une sortie pour y répondre.",
            'Ne engage pas sans vision, sans avantage de vague ou sans savoir où sont deux ennemis.',
            'Après un trade perdu ou une mort, sécurise d’abord une vague, un camp ou une ward défensive.',
            'Convertis un avantage par une tour, un objectif ou une pression de map plutôt qu’en cherchant un nouveau duel.',
        ],
    }
