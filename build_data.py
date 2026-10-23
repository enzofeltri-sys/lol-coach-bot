import json
import urllib.request

DDRAGON_VERSIONS = 'https://ddragon.leagueoflegends.com/api/versions.json'
DDRAGON_BASE = 'https://ddragon.leagueoflegends.com/cdn/{version}/data/fr_FR'
CDRAGON_BASE = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1'


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def load_build_data():
    version = fetch_json(DDRAGON_VERSIONS)[0]
    champions = fetch_json(f'{DDRAGON_BASE.format(version=version)}/champion.json')['data']
    items = fetch_json(f'{DDRAGON_BASE.format(version=version)}/item.json')['data']
    runes = fetch_json(f'{DDRAGON_BASE.format(version=version)}/runesReforged.json')
    return {'version': version, 'champions': champions, 'items': items, 'runes': runes}


def champion_build(champion_key, role, data):
    champion = data['champions'].get(champion_key)
    if not champion:
        raise ValueError(f'Champion inconnu : {champion_key}')
    return {
        'champion': champion['name'],
        'role': role,
        'patch': data['version'],
        'runes': {'primary': 'À sélectionner selon le matchup', 'secondary': 'À sélectionner selon le matchup', 'shards': 'Adaptation / Adaptation / Défense', 'source': 'CommunityDragon'},
        'summoners': ['Flash', 'Téléport' if role in {'TOP', 'MIDDLE'} else 'Soin' if role == 'BOTTOM' else 'Ignite'],
        'skill_order': 'Q > E > W, R aux niveaux 6, 11 et 16',
        'starting_items': ['Potion de santé', 'Ward furtive'],
        'core_items': ['Premier item selon le matchup', 'Deuxième item selon la composition', 'Troisième item selon l’état de la partie'],
        'situational_items': ['Anti-soin si régénération ennemie', 'Résistance magique si dégâts AP', 'Armure si dégâts physiques', 'Contrôle si menaces CC'],
        'power_spikes': [
            {'moment': 'Niveau 2', 'advice': 'Premier trade possible : cherche un avantage de vague et une position sûre.'},
            {'moment': 'Niveau 3', 'advice': 'Kit complet : cherche un trade ou un all-in seulement avec vision et sortie.'},
            {'moment': 'Niveau 6', 'advice': 'Ultimate disponible : prépare une pression de lane, un gank ou un objectif.'},
            {'moment': 'Premier item', 'advice': 'Utilise le spike pour convertir l’avantage en tour, objectif ou pression de map.'},
            {'moment': 'Deux items', 'advice': 'Pic de puissance fréquent : cherche un combat contrôlé ou un objectif.'},
            {'moment': 'Niveaux 11 et 16', 'advice': 'Montées d’ultimate : repositionne-toi autour des combats d’équipe et des objectifs.'},
        ],
    }
