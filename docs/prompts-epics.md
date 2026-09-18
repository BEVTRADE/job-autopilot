# Prompts de lancement, epic par epic

Chaque prompt se colle dans Claude Code après :

    cd ~/Projects/job-autopilot && claude

Tous supposent que Spec Kit est installé et que l'epic concerné est déjà
spécifié (voir `docs/prompt-speckit.md`).

## Ce qui peut tourner en parallèle

Trois lots ne se touchent pas et peuvent avancer en même temps :

| Lot | Fichiers modifiés |
|---|---|
| EPIC-1 | `src/apply/freework.py`, `scripts/apply.py` |
| EPIC-2 | `src/store.py`, `src/sources/base.py` |
| EPIC-4 | `scripts/calibrate.py`, nouveau `scripts/catalogue.py` |

Trois autres doivent attendre :

| Lot | Attend | Raison |
|---|---|---|
| EPIC-3 | EPIC-2 | Les deux touchent `scripts/collect.py` ; et multiplier les sources sans regroupement multiplie les doublons |
| EPIC-5 | EPIC-1 | Les deux touchent `scripts/apply.py` ; et adapter un CV qui ne part jamais n'a pas d'intérêt |
| EPIC-6 | EPIC-1 | La file d'attente se remplit avec de vraies candidatures bloquées, pas avec des cas fictifs |

Nuance importante sur EPIC-1 : **il n'est pas parallélisable au sens d'un
agent**. Il demande votre présence — session Free-Work, lecture des captures,
décision d'envoyer. Ce sont EPIC-2 et EPIC-4 qui peuvent tourner pendant que
vous le menez.

**Utilisez un worktree git par lot parallèle**, sinon deux agents écrivent
dans les mêmes fichiers :

    git worktree add ../ja-epic2 -b epic2-empreinte
    git worktree add ../ja-epic4 -b epic4-catalogue

Puis lancez `claude` depuis chaque worktree. La fusion se fait à la main,
lot par lot, une fois les tests passés.

---

## EPIC-1 — Première candidature vérifiée

```
Tu traites EPIC-1, décrit dans docs/epics.md. Lis-le d'abord, ainsi que docs/autonomie.md et src/apply/freework.py.

Objectif : faire passer une candidature réelle de bout en bout sur Free-Work, et prouver qu'elle est arrivée.

Commence par lancer make simu et montre-moi la sortie brute, sans l'interpréter. Ouvre ensuite les captures dans data/output/<jour>/candidatures/ et dis-moi ce que tu vois vraiment : le CV sélectionné, les réponses aux questions, l'état du formulaire.

Le code de src/apply/freework.py date du 4 septembre. Ses sélecteurs CSS ont pu devenir faux. Si c'est le cas, corrige-les en te fondant sur le DOM réel que tu observes, pas sur ce que tu supposes. Chaque correction doit être justifiée par ce que tu as lu dans la page.

Ne lance jamais make candidater-pour-de-vrai. Quand tu estimes que la simulation est propre, dis-le-moi et attends. C'est moi qui déclenche l'envoi.

Après l'envoi, vérifie la présence de la candidature dans « Mes candidatures » et la ligne de statut envoyee dans data/journal.jsonl. Vérifie aussi que le CV de repos a bien été restauré.

Si tu es bloqué deux fois sur la même erreur, arrête-toi et explique ce que tu as essayé.
```

---

## EPIC-2 — Regroupement par empreinte de contenu

```
Tu traites EPIC-2, décrit dans docs/epics.md. Lis-le d'abord, ainsi que src/store.py, src/sources/base.py et docs/sources.md.

Le problème : l'identité d'une mission est aujourd'hui son URL, donc la même mission publiée par trois intermédiaires compte trois fois.

Trois cas réels sont documentés dans les rapports de veille de data/output/ : le 8 septembre, un poste d'IA agentique à Meudon publié par Craftman, Signe + et Nicholson entre 286 et 500 € ; le 9, le programme VOLT/AMIA en deux grades ; le 15, une mission de réassurance à 750 € chez KEONI et 500-720 € chez CAT-AMANIA. Commence par relire ces trois cas : ce sont tes données de test.

Implémente une empreinte calculée sur le titre normalisé et le corps de l'annonce. Regroupe sans jamais supprimer : chaque annonce du groupe reste visible avec sa société et son TJM, et le groupe expose l'intermédiaire le mieux-disant et l'écart de prix.

Écris les tests avant le code, sur données figées, sans réseau. Ils doivent couvrir les trois cas réels et le cas inverse : deux missions réellement distinctes aux titres proches ne doivent pas être regroupées.

Ne touche pas à src/matching/. Le regroupement est une question d'identité, pas de notation.

Termine par bash scripts/verifier.sh et montre-moi la sortie.
```

---

## EPIC-4 — Passe sur le catalogue

```
Tu traites EPIC-4, décrit dans docs/epics.md. Lis-le d'abord, ainsi que profile/cv_catalog.json, scripts/calibrate.py et src/matching/text.py.

Le problème : trois points aveugles du catalogue ont été trouvés par hasard début septembre — gouvernance IA, fraude et LCB-FT, acculturation. L'un faisait passer une mission de 51 à 90 de score après correction. Il en reste probablement.

Écris une commande make catalogue qui confronte le vocabulaire des huit CV à celui des missions déjà collectées, et produit la liste des termes fréquents dans les missions et absents du catalogue.

Chaque terme du rapport doit porter sa fréquence, le TJM médian des missions qui le contiennent, et un exemple d'annonce réelle. Classe par TJM médian décroissant : un terme absent qui apparaît dans des missions à 800 € coûte plus cher qu'un terme absent à 400 €.

Ne modifie jamais profile/cv_catalog.json automatiquement. Le rapport propose, je décide. Distingue explicitement ce qui pourrait être une compétence réelle non déclarée de ce qui est clairement hors profil.

Ajoute la cible au Makefile et à docs/chantiers.md. Termine par bash scripts/verifier.sh.
```

---

## EPIC-3 — Sources supplémentaires

```
Tu traites EPIC-3, décrit dans docs/epics.md. À ne lancer qu'une fois EPIC-2 fusionné.

Lis d'abord docs/sources.md, src/sources/base.py et src/sources/freework.py, qui est le modèle à suivre.

Implémente les sources listées comme « à intégrer » : Freelance-Informatique, Freelance-Day, FreelanceRepublik, TED. Une classe par source, même interface que FreeWork.

Attention au TJM : Free-Work rend les fourchettes avec une barre de fraction unicode, d'autres sites auront leurs propres bizarreries. Chaque extraction doit être couverte par un test sur page enregistrée, sans réseau.

Une source en panne ne doit jamais interrompre la collecte des autres. Vérifie ce comportement par un test.

Déclare les nouvelles sources dans scripts/collect.py, puis lance make veille et montre-moi combien d'annonces chaque source remonte réellement.
```

---

## EPIC-6 — File d'attente et validation

```
Tu traites EPIC-6, décrit dans docs/epics.md. À ne lancer qu'une fois EPIC-1 terminé, pour disposer de vraies candidatures bloquées.

Lis d'abord src/report/digest.py, src/apply/answers.py et profile/reponses_types.json.

Construis une vue des candidatures en attente : pour chacune, le motif du blocage, la capture d'écran, le lien vers l'annonce et le CV prévu. Une page HTML statique générée par le rapport suffit, ne construis pas de serveur.

Le point central : quand le blocage vient d'une question hors banque, je dois pouvoir écrire la réponse et l'ajouter à profile/reponses_types.json sans éditer le JSON à la main, puis relancer cette seule candidature.

Rien ne doit pouvoir être envoyé depuis cette vue sans une action explicite de ma part.

Termine par bash scripts/verifier.sh, en ajoutant des tests sur la génération de la vue et sur l'enrichissement de la banque.
```

---

## EPIC-5 — Personnalisation du CV par mission

```
Tu traites EPIC-5, décrit dans docs/epics.md. À ne lancer qu'une fois EPIC-1 terminé.

Lis d'abord src/cv/render.py, profile/master_profile.json, et deux CV adaptés à la main pour voir la cible : clients/enedis-yele/03_cv/cv_enedis.md et clients/agentique-bti/03_cv/cv_bti.md.

Objectif : appeler claude -p depuis le script pour produire les substitutions à appliquer au CV d'axe — titre, accroche, ordre des sections de compétences. Le rendu reste assuré par render.py, par remplacement XML, pour préserver la mise en forme.

La règle absolue : aucune compétence absente de profile/master_profile.json ne doit apparaître dans le CV généré. Implémente une vérification qui compare le texte produit au profil maître et refuse la substitution en cas d'ajout non justifié. Cette vérification doit être testée.

Prévois le repli : si claude -p échoue ou n'est pas disponible, le CV d'axe part tel quel et le rapport le signale.

Ajoute un mode de comparaison qui produit les deux versions côte à côte, pour que je puisse juger avant de généraliser.

Termine par bash scripts/verifier.sh.
```
