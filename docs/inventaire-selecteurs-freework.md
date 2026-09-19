# Inventaire des sélecteurs Free-Work — EPIC-8, étape 2

Relevé le 19/09/2026 sur les instantanés `tests/pages/freework/`, produits par
`scripts/sonde_freework.py`. Chaque nombre est le nombre d'éléments trouvés
par le sélecteur dans l'instantané de l'étape indiquée.

## SEL avant correction

| Entrée | Sélecteur d'origine | Étape | Trouvé | Verdict |
|---|---|---|---|---|
| `message` | `#job-application-message` | 02 | 1 | Correct (id). |
| `submit` | `button[type=submit]:has-text('Je postule')` | 02 | 1 | Trouvé, mais repose sur un libellé. Le bouton n'a ni id, ni testid, ni name. |
| `editer_cv` | `button:has-text('Éditer')` | 02 | **2** | **Ambigu** : Profil et CV partagé. Le code contournait par une boucle et un `Escape`. |
| `partager_cv` | `button:has-text('Partager le CV')` | 04 à 08 | 1 | Trouvé, libellé seul. |
| `carte_cv` | `figure` | 08 | **8** (2 hors modale) | **Ambigu** hors du préfixe `fw-modal`. |
| `carte_fichier` | `fw-modal [data-testid^='file-item-']` | 04 | 6 | Correct. |
| `nom_fichier` | `figcaption` | 04 | 1 par carte | Correct. |
| `ajouter_cv` | `[data-testid='add-resume-button']` | 04 | 1 | Sélecteur correct, **usage faux** : c'est un accordéon ouvert à l'ouverture, son clic referme le panneau de dépôt. |
| `valider_modale` | `fw-modal form button[type=submit]` | 04, 06 à 08 | **2** | **Ambigu** : « Partager le CV » et « Envoyer mon CV ». À l'étape 03 il vaut « Mettre à jour » de la modale Profil. |

## Écarts hors de SEL

| Emplacement | Sélecteur d'origine | Constat |
|---|---|---|
| `cv_partage()` | `a[href*='/users/documents/']` | Trouve 1 lien, mais par href. L'id `#default-resume-attachment` existe. |
| `deposer_cv()` | `input[type=file]` | **0 élément à toutes les étapes.** Le champ fichier n'est pas dans le DOM, il est créé par « Parcourir… ». Ce repli ne peut jamais réussir. |
| `_valider_selection()` | libellé « Joindre le document » | **Absent de tous les instantanés.** Le bouton de confirmation de la modale des CV est « Partager le CV ». |
| `CANDIDATURES` | `/fr/tech-it/dashboard/applications` | **404.** La bonne URL est `/fr/applications`. `verifier()` échouait donc toujours. |
| `questions()` | `form textarea:not(#job-application-message), form input[type=text]` | 0 champ sur l'offre de simulation, qui n'a pas de question filtrante. **Aucun instantané ne couvre ces champs** (voir « Non couvert »). |

## Sélecteurs corrigés

Les propositions ont toutes été mesurées : exactement 1 élément (6 pour les
cartes) aux étapes concernées, 0 ailleurs.

| Entrée | Sélecteur proposé | Étapes | Attribut stable |
|---|---|---|---|
| `message` | `#job-application-message` | 02 | id |
| `submit` | `form:has(#job-application-message) button[type=submit]` | 02 | structure |
| `editer_cv` | `#default-resume-edit` | 02 | id |
| `cv_partage_lien` | `#default-resume-attachment` | 02, 09 | id |
| `modale_cv` | `[data-testid='file-chooser-modal']` | 04 à 08 | data-testid |
| `carte_fichier` | `[data-testid='file-chooser-modal'] [data-testid='file-list'] > [data-testid^='file-item-']` | 04 | data-testid |
| `nom_fichier` | `figcaption` (relatif à la carte) | 04 | balise |
| `partager_cv` | `[data-testid='file-chooser-modal'] form:has([data-testid='file-list']) button[type=submit]` | 04 à 08 | data-testid |
| `ajouter_cv` | `[data-testid='add-resume-button']` | 04 | data-testid |
| `parcourir` | `[data-testid='file-chooser-modal'] [data-testid='file-upload-input'] button:has-text('Parcourir')` | 04, 06 à 08 | data-testid, puis libellé |
| `envoyer_cv` | `[data-testid='file-chooser-modal'] form:has([data-testid='file-upload-input']) button[type=submit]` | 04, 06 à 08 | data-testid |
| `session` | `[data-testid='user-menu']` | toutes | data-testid |

`submit` et `parcourir` n'ont pas d'attribut stable propre : le premier est
ancré sur le formulaire par `#job-application-message`, le second sur le
conteneur `file-upload-input` puis sur son libellé, seul discriminant entre
« Parcourir… » et « Changer ».

## Comportement de la modale des CV (observé)

- Elle s'ouvre avec la liste des CV **et** la zone de dépôt déjà visibles.
- « Ajouter un CV » bascule l'accordéon : cliquer quand la zone est ouverte la referme.
- « Partager le CV » et « Envoyer mon CV » sont désactivés tant qu'aucune carte ni aucun fichier n'est choisi.
- Après choix du fichier : « Changer » apparaît, « Envoyer mon CV » devient actif.
- Après confirmation : la modale se ferme, `#default-resume-attachment` change de href.

## Non couvert

- **Questions filtrantes.** L'offre de simulation n'en a pas. Il faut un
  instantané d'une offre qui en pose pour tester `questions()`, `_relire()` et
  la frappe. Tant qu'il manque, ces sélecteurs restent non vérifiés.
- **« Mes candidatures » après un envoi réel.** `/fr/applications` charge, mais
  aucun instantané ne montre une candidature envoyée : `verifier()` ne peut
  être validé qu'après le premier envoi réel.
