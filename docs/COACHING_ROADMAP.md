# Préparation coaching et vidéo

Statut : cadrage seulement. Aucune analyse vidéo ni collecte supplémentaire activée.

## Constat de revue du 23 octobre 2026
- Permissions Actions séparées, actions verrouillées, credentials checkout non persistés.
- Ancienne exposition dans .env.example ; rotation déclarée par le propriétaire. Suppression de l'historique non effectuée.
- Revue du code et historique ciblé seulement : aucun audit exhaustif des branches, logs, artefacts, dépendances ou réglages du compte.
- Pas de validation du rendu Safari ni de test réseau Riot dans cette revue.
- Une erreur Riot empêche une nouvelle publication ; dernière page publiée susceptible de rester ancienne.
- Les conseils sont descriptifs et groupés par rôle, sans preuve causale.

## Priorité 1 : tests et fiabilité
- Tests synthétiques : support sans conseil farm, rôle inconnu, zéro mort, durée nulle, parties courtes, échantillon réduit, HTML échappé.
- Tests HTTP simulés : 401/403, 429, 5xx et timeout ; erreurs sans secret ni URL contenant une clé.
- Audit historique complet avec détecteur de secrets standard et règle Riot ; résultats masqués, sans clé active ni permission d'écriture.
- Examiner séparément les anciens logs et artefacts.
- Scanner les dépendances et prévoir leur mise à jour.
- Afficher âge des données et dernier succès sans effacer les données utiles lors d'un échec.

## Priorité 2 : coaching fondé sur les événements
- Conserver match_id, patch, date et participant_id dans un schéma versionné.
- Ajouter une timeline mise en cache côté traitement, avec limites de requêtes.
- Comparer or, expérience et CS aux instants disponibles face au joueur adverse du même rôle.
- Produire observation, preuve horodatée, limites, action et confiance explicite.
- Ne pas déduire une mort sans vision de la seule absence de ward personnelle.

## Priorité 3 : prototype vidéo privé
- Commencer par un clip court choisi par l'utilisateur, pas un replay binaire interprété comme vidéo.
- Choisir et valider un hébergement privé, une authentification, des limites de taille et une durée de conservation avant tout upload.
- Ne jamais envoyer vidéos, cookies ou clés vers Pages ou un dépôt public.
- Synchroniser le temps vidéo avec le temps de jeu via un décalage vérifié.
- Fournir horodatages et preuves visuelles ; signaler les ambiguïtés et demander une validation humaine.
- Chiffrer le coût d'analyse avant tout appel payant ; aucun fournisseur choisi pour l'instant.
