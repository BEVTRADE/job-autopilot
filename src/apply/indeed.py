"""
Indeed — préparation de candidature, jamais de soumission automatique.

Les conditions d'utilisation d'Indeed interdisent aux chercheurs d'emploi
d'automatiser le processus de candidature (https://www.indeed.com/legal,
vérifié le 19/09/2026). Le risque n'est pas un échec technique mais la
fermeture du compte du candidat.

Ce module prépare donc tout ce qu'une candidature demande — lien, CV
recommandé par le moteur, message — et l'inscrit au journal avec le statut
`a_faire_manuel`. Le rapport du matin le présente dans une section dédiée :
le candidat clique, joint le CV indiqué, envoie.

Capacités déclarées : preparer. Il n'existe pas de chemin de soumission, et
aucun paramètre ne permet d'en ajouter un.
"""
from __future__ import annotations

from .base import Result, journal

CAPACITES = frozenset({"preparer"})


class Indeed:
    name = "indeed"
    capacites = CAPACITES

    def postuler(self, url: str, uid: str, titre: str, cv: str | None = None,
                 message: str | None = None) -> Result:
        detail = f"candidature Indeed à faire à la main : ouvrir {url}"
        if cv:
            detail += f", joindre {cv}"
        if message:
            detail += ", message préparé dans le rapport"
        res = Result(uid, url, titre, "a_faire_manuel", detail, cv=cv)
        journal(res)            # journal() renvoie le chemin du fichier, pas le résultat
        return res
