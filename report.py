def build_report(riot_id, analysis):
    lines = [
        f"# Rapport LoL — {riot_id}", "",
        f"**Games analysées :** {len(analysis['games'])}", f"**Winrate :** {analysis['win_rate']}%", f"**KDA moyen :** {analysis['avg_kda']}",
        f"**CS/min moyen :** {analysis['avg_cs_per_min']}", f"**Dégâts/min moyens :** {analysis['avg_damage_per_min']}",
        f"**Dégâts subis/min moyens :** {analysis['avg_damage_taken_per_min']}", f"**Or/min moyens :** {analysis['avg_gold_per_min']}",
        f"**Vision/min moyenne :** {analysis['avg_vision_per_min']}", f"**CC/min moyen :** {analysis['avg_cc_per_min']}",
        f"**Participation aux kills :** {analysis['avg_kill_participation']}%", "",
        "## Conseils par matchup", "",
    ]
    for matchup, data in analysis.get('matchup_aggregates', {}).items():
        lines.append(f"### {matchup} — {data['role']} · {data['games']} partie(s) · {data['win_rate']}% victoires")
        lines.append("")
        lines += [f"- {advice}" for advice in data['advice']]
        lines.append("")
    lines += ["## Conseils personnalisés par champion", ""]
    for champion, data in analysis.get('champion_aggregates', {}).items():
        lines.append(f"### {champion} — {data['role']} · {data['games']} partie(s) · {data['win_rate']}% victoires")
        lines.append("")
        lines += [f"- {advice}" for advice in data['advice']]
        lines.append("")
    lines += ["## Détail des games", "", "| Champion | Adversaire | Rôle | Patch | Résultat | KDA | CS/min | Dégâts/min | Dégâts subis/min | Or/min | Vision/min | CC/min | KP |", "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for game in analysis["games"]:
        result = "Victoire" if game["win"] else "Défaite"
        lines.append(f"| {game['champion']} | {game.get('opponent_champion') or '—'} | {game['role']} | {game['patch']} | {result} | {game['kda']} | {game['cs_per_min']} | {game['damage_per_min']} | {game['damage_taken_per_min']} | {game['gold_per_min']} | {game['vision_per_min']} | {game['cc_per_min']} | {game['kill_participation']}% |")
    lines += ["", "## Écarts moyens timeline", "", "| Minute | Parties | Écart or | Écart XP | Écart CS |", "|---:|---:|---:|---:|---:|"]
    for minute in (5, 10, 15, 20):
        gap = analysis.get('timeline_gaps', {}).get(minute)
        lines.append(f"| {minute} | {gap['games'] if gap else 0} | {gap['gold_gap']:+} | {gap['xp_gap']:+} | {gap['cs_gap']:+} |" if gap else f"| {minute} | 0 | — | — | — |")
    lines += ["", "## Repères timeline", ""]
    lines += [f"- {item}" for item in analysis.get("timeline_insights", [])]
    lines += ["", "## Pistes à vérifier", ""]
    lines += [f"- {issue}" for issue in analysis["issues"]]
    lines += ["", "## Points forts", ""]
    lines += [f"- {strength}" for strength in analysis["strengths"]]
    return "\n".join(lines)
