def build_report(riot_id, analysis):
    lines = [
        f"# Rapport LoL — {riot_id}",
        "",
        f"**Games analysées :** {len(analysis['games'])}",
        f"**Winrate :** {analysis['win_rate']}%",
        f"**KDA moyen :** {analysis['avg_kda']}",
        f"**CS/min moyen :** {analysis['avg_cs_per_min']}",
        f"**Wards/min moyen :** {analysis['avg_wards_per_min']}",
        f"**Morts moyennes :** {analysis['avg_deaths']}",
        "",
        "## Détail des games",
        "",
        "| Champion | Rôle | Résultat | KDA | CS/min | Wards/min | Morts |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for game in analysis["games"]:
        result = "Victoire" if game["win"] else "Défaite"
        lines.append(
            f"| {game['champion']} | {game['role']} | {result} | "
            f"{game['kda']} | {game['cs_per_min']} | {game['wards_per_min']} | {game['deaths']} |"
        )

    lines += ["", "## Erreurs récurrentes", ""]
    lines += [f"- {issue}" for issue in analysis["issues"]]

    lines += ["", "## Points forts", ""]
    lines += [f"- {strength}" for strength in analysis["strengths"]]

    lines += [
        "",
        "## Objectifs pour les prochaines games",
        "",
        "- Avant chaque rotation, vérifie la vision autour de toi.",
        "- Après avoir pushé une vague, recule ou pose un ward plutôt que de rester exposé.",
        "- Vise une amélioration progressive : une seule priorité par session de jeu.",
    ]

    return "\n".join(lines)
