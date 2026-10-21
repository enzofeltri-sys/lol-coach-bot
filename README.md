# LoL Coach Bot

Analyse tes 10 dernières games ranked Solo/Duo sur EUW et génère un rapport d'amélioration.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Ajoute ta clé API Riot dans `.env` :

```env
RIOT_API_KEY=ta_cle_riot
```

## Lancement

```bash
python main.py
```

Le rapport est créé dans `rapport.md`.

## Ce que le bot analyse

- KDA, CS/min, wards/min et morts
- Participation aux dragons, hérauts et Barons
- Erreurs récurrentes : manque de vision, mauvais farm, décès fréquents
- Points forts et objectifs concrets pour les prochaines games

## Clé API

Crée une clé sur https://developer.riotgames.com/ puis colle-la dans `.env`.
