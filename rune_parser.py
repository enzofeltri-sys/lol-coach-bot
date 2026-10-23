from build_data import champion_build as legacy_build


def recommended_page(champion_key, role, data):
    champion_id = int(data['champions'][champion_key]['key'])
    entries = data.get('rune_recommendations', [])
    if not isinstance(entries, list):
        raise ValueError('CommunityDragon: expected a champion list')
    entry = next((e for e in entries if isinstance(e, dict) and str(e.get('championId')) == str(champion_id)), {})
    positions = {'MIDDLE': 'mid', 'BOTTOM': 'bottom', 'UTILITY': 'support', 'TOP': 'top', 'JUNGLE': 'jungle'}
    aliases = {'middle': 'mid', 'adc': 'bottom', 'utility': 'support'}
    wanted = positions.get(role, str(role).lower())
    def matches(page):
        position = str(page.get('position', '')).lower()
        return str(page.get('mapId')) == '11' and aliases.get(position, position) == wanted
    pages = [p for p in entry.get('runeRecommendations', []) if isinstance(p, dict) and matches(p)]
    if not pages:
        return None
    styles = {str(s['id']): s for s in data['runes']}
    names = data.get('perk_names', {})
    for page in pages:
        primary = styles.get(str(page.get('primaryPerkStyleId')))
        secondary = styles.get(str(page.get('secondaryPerkStyleId')))
        if not primary or not secondary:
            continue
        ids = {str(i) for i in page.get('perkIds', [])}
        def details(style):
            result = []
            for slot in style['slots']:
                chosen = [r for r in slot['runes'] if str(r['id']) in ids]
                if len(chosen) > 1:
                    return []
                for rune in chosen:
                    result.append({'id': rune['id'], 'name': rune['name'], 'icon': 'https://ddragon.leagueoflegends.com/cdn/img/' + rune['icon']})
            return result
        main = details(primary)
        sub = details(secondary)
        if len(main) != 4 or len(sub) != 2:
            continue
        shard_ids = page['perkIds'][6:]
        shards = ' / '.join(names.get(str(i)) or ('Éclat ' + str(i)) for i in shard_ids)
        return {'primary': primary['name'], 'secondary': secondary['name'], 'primary_icon': 'https://ddragon.leagueoflegends.com/cdn/img/' + primary['icon'], 'secondary_icon': 'https://ddragon.leagueoflegends.com/cdn/img/' + secondary['icon'], 'primary_runes': main, 'secondary_runes': sub, 'shards': shards, 'source': 'CommunityDragon — champion et rôle ; non spécifique à l’adversaire'}
    raise ValueError('CommunityDragon: no valid page with four primary and two secondary runes for ' + champion_key + '/' + role)


def champion_build(champion_key, role, opponent_key, data):
    runes = recommended_page(champion_key, role, data)
    result = legacy_build(champion_key, role, opponent_key, data)
    result['runes'] = runes or {'primary': 'Aucune page disponible pour ce rôle', 'secondary': 'Indisponible', 'primary_runes': [], 'shards': 'Indisponibles', 'source': 'CommunityDragon — aucune page pour ce champion et ce rôle'}
    return result
