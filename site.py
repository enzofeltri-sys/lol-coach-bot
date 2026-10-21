def build_html(riot_id, analysis):
    games_rows = ""
    for game in analysis["games"]:
        result = "Victoire" if game["win"] else "Défaite"
        result_class = "win" if game["win"] else "loss"
        games_rows += f"""
        <tr>
          <td>{game['champion']}</td>
          <td>{game['role']}</td>
          <td class=\"{result_class}\">{result}</td>
          <td>{game['kda']}</td>
          <td>{game['cs_per_min']}</td>
          <td>{game['wards_per_min']}</td>
          <td>{game['deaths']}</td>
        </tr>
        """

    issues = "".join(f"<li>{issue}</li>" for issue in analysis["issues"])
    strengths = "".join(f"<li>{strength}</li>" for strength in analysis["strengths"])

    return f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Rapport LoL — {riot_id}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #0b1120; color: #e2e8f0; }}
    main {{ max-width: 1000px; margin: auto; padding: 24px; }}
    h1 {{ color: #38bdf8; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; }}
    .card strong {{ display: block; font-size: 28px; color: #38bdf8; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; background: #111827; border-radius: 12px; overflow: hidden; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #1f2937; text-align: center; }}
    th {{ background: #1e293b; }}
    .win {{ color: #4ade80; font-weight: 700; }}
    .loss {{ color: #f87171; font-weight: 700; }}
    ul {{ line-height: 1.6; }}
  </style>
</head>
<body>
  <main>
    <h1>Rapport LoL — {riot_id}</h1>
    <p>Analyse des {len(analysis['games'])} dernières games ranked Solo/Duo sur EUW.</p>

    <div class=\"cards\">
      <div class=\"card\"><span>Winrate</span><strong>{analysis['win_rate']}%</strong></div>
      <div class=\"card\"><span>KDA moyen</span><strong>{analysis['avg_kda']}</strong></div>
      <div class=\"card\"><span>CS/min</span><strong>{analysis['avg_cs_per_min']}</strong></div>
      <div class=\"card\"><span>Wards/min</span><strong>{analysis['avg_wards_per_min']}</strong></div>
      <div class=\"card\"><span>Morts moyennes</span><strong>{analysis['avg_deaths']}</strong></div>
    </div>

    <h2>Détail des games</h2>
    <table>
      <thead>
        <tr><th>Champion</th><th>Rôle</th><th>Résultat</th><th>KDA</th><th>CS/min</th><th>Wards/min</th><th>Morts</th></tr>
      </thead>
      <tbody>{games_rows}</tbody>
    </table>

    <h2>Erreurs récurrentes</h2>
    <ul>{issues}</ul>

    <h2>Points forts</h2>
    <ul>{strengths}</ul>

    <h2>Objectifs</h2>
    <ul>
      <li>Vérifie la vision avant chaque rotation.</li>
      <li>Après avoir pushé une vague, recule ou pose un ward.</li>
      <li>Travaille une seule priorité par session de jeu.</li>
    </ul>
  </main>
</body>
</html>"""
