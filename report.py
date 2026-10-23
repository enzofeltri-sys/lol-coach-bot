def build_report(riot_id, analysis):
    lines = [
        f"# Rapport LoL — {riot_id}",
        "",
        f"**Games analysées :** {len(analysis['games'])}",
        f"**Winrate :** {analysis['win_rate']}%",
        f"**KDA moyen :** {analysis['avg_kda']}",
        f"**CS/min moyen :** {analysis['avg_cs_per_min']}",
        f"**Dégâts/min moyens :** {analysis['avg_damage_per_min']}",
        f"**Dégâts subis/min moyens :** {analysis['avg_damage_taken_per_min']}",
        f"**Or/min moyens :** {analysis['avg_gold_per_min']}",
        f"**Vision/min moyenne :** {analysis['avg_vision_per_min']}",
        f"**CC/min moyen :** {analysis['avg_cc_per_min']}",
        f"**Participation aux kills :** {analysis['avg_kill_participation']}%",
        f"**Morts moyennes :** {analysis['avg_deaths']} ({analysis['avg_deaths_per_10']} / 10 min)",
        f"**Objectifs cumulés :** {analysis['total_towers']} tours · {analysis['total_dragons']} dragons · {analysis['total_barons']} barons · {analysis['total_heralds']} hérauts",
        "",
        "## Détail des games",
        "",
        "| Champion | Rôle | Patch | Mode | Résultat | KDA | CS/min | Dégâts/min | Dégâts subis/min | Or/min | Vision/min | CC/min | KP |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for game in analysis["games"]:
        result = "Victoire" if game["win"] else "Défaite"
        lines.append(
            f"| {game['champion']} | {game['role']} | {game['patch']} | {game['mode']} | {result} | {game['kda']} | "
            f"{game['cs_per_min']} | {game['damage_per_min']} | {game['damage_taken_per_min']} | {game['gold_per_min']} | "
            f"{game['vision_per_min']} | {game['cc_per_min']} | {game['kill_participation']}% |"
        )
    lines += ["", "## Écarts moyens timeline", "", "Écart moyen avec l’adversaire du même rôle ; un nombre positif te favorise.", "", "| Minute | Parties | Écart or | Écart XP | Écart CS |", "|---:|---:|---:|---:|---:|"]
    for minute in (5, 10, 15, 20):
        gap = analysis.get('timeline_gaps', {}).get(minute)
        if gap:
            lines.append(f"| {minute} | {gap['games']} | {gap['gold_gap']:+} | {gap['xp_gap']:+} | {gap['cs_gap']:+} |")
        else:
            lines.append(f"| {minute} | 0 | — | — | — |")
    lines += ["", "## Moyennes par rôle", "", "| Rôle | Parties | Winrate | KDA | Morts/10 | CS/min | Dégâts/min | Vision/min | KP |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for role, data in analysis.get('role_aggregates', {}).items():
        lines.append(
            f"| {role} | {data['games']} | {data['win_rate']}% | {data['avg_kda']} | {data['avg_deaths_per_10']} | "
            f"{data['avg_cs_per_min']} | {data['avg_damage_per_min']} | {data['avg_vision_per_min']} | {data['avg_kill_participation']}% |"
        )
    lines += ["", "## Repères timeline", ""]
    lines += [f"- {item}" for item in analysis.get("timeline_insights", [])]
    lines += ["", "## Pistes à vérifier", ""]
    lines += [f"- {issue}" for issue in analysis["issues"]]
    lines += ["", "## Points forts", ""]
    lines += [f"- {strength}" for strength in analysis["strengths"]]
    lines += ["", "## Objectifs pour les prochaines games", "", "- Avant chaque rotation, vérifie la vision autour de toi.", "- Après avoir pushé une vague, recule ou pose un ward plutôt que de rester exposé.", "- Vise une amélioration progressive : une seule priorité par session de jeu."]
    return "\n".join(lines)
