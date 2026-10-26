# Feuille de route — LoL Coach

Objectif : transformer le site en vrai coach. Cycle visé : repérer une difficulté dans les parties, proposer un exercice concret, vérifier la progression.

Règle de travail : une fonctionnalité n’est « terminée » que lorsqu’elle a été testée sur des données réelles et vérifiée sur le site déployé (workflow vert ≠ fonctionnalité validée).

Légende : [x] vérifié sur le site déployé ou dans les logs · [ ] à faire ou à vérifier.

## État actuel (26/10/2026)

- Bilan, Matchups, Timeline, Parties : présents, à revalider.
- Plan : refondu (étape 2), en attente de vérification sur le site.
- Build : sélection champion + rôle puis versus facultatif. Dernière génération confirmée dans les logs : 173 champions sur 173 avec une page de runes valide (282 combinaisons champion/rôle). L’affichage des runes sur le site n’est pas encore confirmé visuellement. Objets et compétences indisponibles ; aucune adaptation au versus.
- CommunityDragon : accès parfois en erreur auparavant (403, délai TLS) ; le site continue sans runes en cas d’échec et l’indique dans « État des données ».

## Étape 1 — Fiabiliser le site et le Build

- [ ] Afficher la date de génération et l’état de chaque source : fait et confirmé sur le site pour Data Dragon et CommunityDragon ; la source Riot n’est pas encore affichée.
- [ ] Valider les runes sur plusieurs champions et rôles réels : couverture 173/173 confirmée dans les logs ; reste à voir 4 runes principales + 2 secondaires à l’écran sur plusieurs champions (dont Yone en Mid).
- [ ] Traduire les shards en noms lisibles : implémenté, affichage non confirmé.
- [ ] Intégrer une source fiable pour objets et ordre des compétences, sinon afficher « indisponible » (actuellement : indisponible).
- [ ] Ne présenter une adaptation au versus que si elle est sourcée (actuellement : aucune adaptation affichée).
- [x] Ajouter des tests automatiques sur le parsing des données externes : exécutés avant chaque génération (runes, interface Build, plan de progression).

## Étape 2 — Plan de progression suivi

- [ ] Une priorité, une preuve, un exercice, un indicateur mesurable : implémenté (refonte), à vérifier sur le site.
- [ ] Bilan par priorité : en progrès, stable, données insuffisantes : implémenté, à vérifier sur le site.
- [ ] Afficher le nombre de parties derrière chaque constat : implémenté, à vérifier sur le site.
- [ ] Conserver l’historique des objectifs : non commencé, stockage persistant à décider.

Notes de conception :

- La tendance compare le nombre de parties concernées sur les N parties les plus récentes et les N précédentes (N = la moitié des parties analysées, soit 10 avec 20 parties). Il faut au moins 5 parties par période, sinon « données insuffisantes ». Un écart de 20 points déclenche « en progrès » ou « en régression ». Ces seuils sont indicatifs, pas des tests statistiques.
- Deux défauts de l’ancienne version sont corrigés : la tendance n’était calculée que sur les parties déjà problématiques (une amélioration complète n’était pas détectée), et l’écran annonçait « 20 parties » par période alors que 20 parties seulement sont analysées au total.
- L’ancienne fonction progression_plan() d’analysis.py n’alimente plus l’onglet Plan ; à supprimer après validation.
- Le suivi fonctionne sans stockage : les périodes glissent à chaque génération. Un historique persistant des objectifs nécessite un stockage.

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
