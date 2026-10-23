# Feuille de route — LoL Coach

Objectif : transformer le site en vrai coach. Cycle visé : repérer une difficulté dans les parties, proposer un exercice concret, vérifier la progression.

Règle de travail : une fonctionnalité n’est « terminée » que lorsqu’elle a été testée sur des données réelles et vérifiée sur le site déployé (workflow vert ≠ fonctionnalité validée).

## État actuel

- Bilan, Plan, Matchups, Timeline, Parties : présents, à revalider.
- Build : sélection champion + rôle puis versus facultatif ; runes CommunityDragon à vérifier ; objets et compétences indisponibles ; aucune adaptation au versus vérifiée.
- Données CommunityDragon : accès parfois en erreur (403, délai TLS) ; le site continue sans runes en cas d’échec.

## Étape 1 — Fiabiliser le site et le Build

- [ ] Afficher la date de génération et l’état de chaque source (Riot, Data Dragon, CommunityDragon).
- [ ] Valider les runes sur plusieurs champions et rôles réels ; vérifier 4 runes principales + 2 secondaires.
- [ ] Traduire les shards en noms lisibles.
- [ ] Intégrer une source fiable pour objets et ordre des compétences, sinon afficher « indisponible ».
- [ ] Ne présenter une adaptation au versus que si elle est sourcée.
- [ ] Ajouter des tests automatiques sur le parsing des données externes.

## Étape 2 — Plan de progression suivi

- [ ] Une priorité, une preuve, un exercice, un indicateur mesurable.
- [ ] Bilan par priorité : en progrès, stable, données insuffisantes.
- [ ] Afficher le nombre de parties derrière chaque constat.
- [ ] Conserver l’historique des objectifs (stockage persistant à définir).

## Étape 3 — Débrief de partie et passages à revoir

- [ ] Débrief : points forts, point principal à revoir, action pour la partie suivante.
- [ ] 2 à 3 passages à revoir par partie (mort précoce, dégradation d’écart, objectif) avec minute et question à se poser.
- [ ] Séparer faits, données de match et hypothèses ; gérer les timelines indisponibles.

## Étape 4 — Notes, objectifs et séances

- [ ] Notes personnelles par champion adverse.
- [ ] Mini-débrief facultatif après partie (problème, décision regrettée, objectif travaillé).
- [ ] Objectif de session et bilan de séance.
- [ ] Décider du stockage des données personnelles (local, GitHub privé, service dédié).

## Étape 5 — Préparation avant partie et analyse du lobby

- [ ] Fiche de préparation : objectif, champion, rôle, build classique, versus facultatif, rappels personnels.
- [ ] Analyse de la partie en cours via l’API Riot si disponible.
- [ ] Vérifier les limites de l’API et les règles Riot pour les outils tiers avant de commencer.

## Étape 6 — Analyse de vidéos et replays (à étudier)

- [ ] Choisir le format : extraits vidéo importés manuellement ou fichiers .rofl.
- [ ] Prévoir un import manuel avant toute surveillance de dossier.
- [ ] Définir ce qui est traité localement et ce qui est envoyé à un service externe.
- [ ] Croiser la vidéo avec les données du match ; signaler les hypothèses.
- [ ] Prévoir les contraintes des replays : compatibilité avec le patch et conservation limitée.

## Hors périmètre pour l’instant

- Commentaires d’IA sans preuve dans les données.
- Score global unique non explicable.
- Overlay en jeu.
- Utilitaires secondaires (calculateur de CS, minuteurs) avant les étapes ci-dessus.
