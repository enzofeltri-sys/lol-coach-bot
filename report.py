def build_report(riot_id, analysis):
    lines = [
        f"# Rapport LoL — {riot_id}",
        "",
        f"**Games analysées :** {len(analysis['games'])}",
        f"**Winrate :** {analysis['win_rate']}%",
        f"**KDA moyen :** {analysis['avg_kda']}",
        f"**CS/min moyen :** {analysis['avg_cs_per_min']}",
        f"**Dégâts/min moyens :** {analysis['avg_damage_per_min']}",
        f"**Or/min moyens :** {analysis['avg_gold_per_min']}",
        f"**Vision/min moyenne :** {analysis['avg_vision_per_min']}",
        f"**Participation aux kills :** {analysis['avg_kill_participation']}%",
        f"**Morts moyennes :** {analysis['avg_deaths']}",
        "",
        "## Détail des games",
        "",
        "| Champion | Rôle | Résultat | KDA | CS/min | Dégâts/min | Or/min | Vision/min | KP |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for game in analysis["games"]:
        result = "Victoire" if game["win"] else "Défaite"
        lines.append(f"| {game['champion']} | {game['role']} | {result} | {game['kda']} | {game['cs_per_min']} | {game['damage_per_min']} | {game['gold_per_min']} | {game['vision_per_min']} | {game['kill_participation']}% |")
    lines += ["", "## Repères timeline", ""]
    lines += [f"- {item}" for item in analysis.get("timeline_insights", [])]
    lines += ["", "## Pistes à vérifier", ""]
    lines += [f"- {issue}" for issue in analysis["issues"]]
    lines += ["", "## Points forts", ""]
    lines += [f"- {strength}" for strength in analysis["strengths"]]
    lines += ["", "## Objectifs pour les prochaines games", "", "- Avant chaque rotation, vérifie la vision autour de toi.", "- Après avoir pushé une vague, recule ou pose un ward plutôt que de rester exposé.", "- Vise une amélioration progressive : une seule priorité par session de jeu."]
    return "\n".join(lines)
