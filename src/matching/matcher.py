"""
Moteur de matching mission -> CV.

Deux notes indépendantes, volontairement séparées pour rester lisibles :

  FIT     0-100  adéquation du meilleur CV à la mission
  VALEUR  0-100  intérêt économique de la mission (TJM, remote, durée)

La décision combine les deux sous un plancher TJM dur. Calibré pour
maximiser le TJM : la valeur pèse autant que l'adéquation.
"""
from __future__ import annotations
import json, os
from dataclasses import dataclass, field, asdict

from .text import TfIdf, norm, tokens

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --------------------------------------------------------------------------- #
#  Paramètres — tout ce qui se règle est ici
# --------------------------------------------------------------------------- #

@dataclass
class Params:
    tjm_floor_hard: int = 550      # en dessous : rejet sec
    tjm_floor_soft: int = 650      # plancher "haut de gamme"
    tjm_target: int = 800          # au-delà : valeur maximale
    remote_pref: str = "partial"   # full | partial | none

    w_fit_skills: float = 0.45
    w_fit_title: float = 0.30
    w_fit_text: float = 0.25

    w_val_tjm: float = 0.65
    w_val_remote: float = 0.20
    w_val_duration: float = 0.15

    w_decision_fit: float = 0.50
    w_decision_value: float = 0.50

    # Mode "contact" : la fourchette affichée est l'ancrage de l'intermédiaire,
    # pas le budget du client. On postule sur l'adéquation et on négocie ensuite.
    # La valeur ne sert alors qu'à départager, et le plancher dur tombe.
    mode: str = "tjm"              # "tjm" | "contact"

    min_fit: int = 45              # sous ce fit, on ne postule pas
    min_decision_shortlist: int = 60
    min_decision_apply: int = 72


@dataclass
class Match:
    aid: str | None
    title: str
    company: str | None
    tjm_min: int | None
    tjm_max: int | None
    axis_id: str
    axis_label: str
    lang: str
    cv_path: str
    fit: int
    value: int
    decision_score: int
    verdict: str                      # apply | shortlist | reject
    reasons: list[str] = field(default_factory=list)
    skills_matched: list[str] = field(default_factory=list)
    skills_missing: list[str] = field(default_factory=list)
    runners_up: list[tuple[str, int]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# --------------------------------------------------------------------------- #

def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class Matcher:
    def __init__(self, catalog_path: str | None = None,
                 cv_texts: dict[str, str] | None = None,
                 params: Params | None = None):
        catalog_path = catalog_path or os.path.join(HERE, "profile", "cv_catalog.json")
        self.cat = json.load(open(catalog_path, encoding="utf-8"))
        self.p = params or Params()
        self.axes = self.cat["axes"]
        self.aliases = {norm(k): [norm(x) for x in v]
                        for k, v in self.cat.get("aliases", {}).items()}

        dx = self.cat.get("domain_exclusions", {})
        self.excl = {g: [norm(x) for x in terms]
                     for g, terms in dx.get("groups", {}).items()}
        self.excl_pen = dx.get("penalty_per_group", 18)
        self.excl_max = dx.get("max_penalty", 36)

        # corpus par axe : texte du CV s'il est fourni, sinon les mots-clés du catalogue
        corpus = {}
        for a in self.axes:
            base = " ".join(a["titles"] + a["core"] + a["core"] + a["plus"])
            extra = (cv_texts or {}).get(a["id"], "")
            corpus[a["id"]] = base + " " + extra
        self.tfidf = TfIdf(corpus)

        self._norm_axis = {}
        for a in self.axes:
            self._norm_axis[a["id"]] = {
                "titles": [norm(t) for t in a["titles"]],
                "core": [norm(t) for t in a["core"]],
                "plus": [norm(t) for t in a["plus"]],
                "blob": norm(corpus[a["id"]]),
            }

    # ---------------- composantes du FIT ----------------

    def _skill_score(self, axis_id, mission_skills):
        """Couverture pondérée des compétences exigées."""
        na = self._norm_axis[axis_id]
        matched, missing, got, total = [], [], 0.0, 0.0
        for raw in mission_skills:
            s = norm(raw)
            if not s:
                continue
            variants = [s] + self.aliases.get(s, [])
            weight = 1.0
            hit = False
            for v in variants:
                if any(v in c or c in v for c in na["core"]):
                    hit, weight = True, 1.5
                    break
                if any(v in c or c in v for c in na["plus"]):
                    hit, weight = True, 1.0
                    break
                if v and v in na["blob"]:
                    hit, weight = True, 0.7
                    break
            total += 1.5
            if hit:
                got += weight
                matched.append(raw)
            else:
                missing.append(raw)
        if total == 0:
            return 0.5, [], []
        return _clip(got / total), matched, missing

    def covers(self, term: str) -> bool:
        """Le terme est-il déjà couvert par au moins un axe (catalogue + CV) ?

        Réutilise la même règle de correspondance que le score de FIT, pour
        qu'un terme jugé « couvert » ici le soit aussi au moment du matching.
        """
        return any(self._skill_score(a["id"], [term])[1] for a in self.axes)

    def _title_score(self, axis_id, title, job):
        na = self._norm_axis[axis_id]
        hay = f"{norm(title)} {norm(job)}"
        best = 0.0
        for t in na["titles"]:
            if t in hay:
                best = max(best, 1.0 if len(t.split()) > 1 else 0.75)
        if best:
            return best
        tk = set(tokens(hay))
        for t in na["titles"]:
            tt = set(tokens(t))
            if tt and len(tk & tt) / len(tt) >= 0.5:
                best = max(best, 0.55)
        return best

    def _text_score(self, axis_id, blob):
        return _clip(TfIdf.cos(self.tfidf.vecs[axis_id], self.tfidf.vec(blob)) * 2.2)

    # ---------------- VALEUR ----------------

    def value_score(self, tjm_min, tjm_max, remote, dur_val, dur_per):
        p, reasons = self.p, []

        # La négociation se fait vers le haut : le milieu de fourchette reflète
        # mieux la valeur réelle que le plancher, qui n'est qu'un ancrage.
        if tjm_min and tjm_max:
            base = (tjm_min + tjm_max) // 2
        elif tjm_min:
            base = tjm_min
        elif tjm_max:
            base = int(tjm_max * 0.85)
        else:
            base = None
        if base is None:
            tjm, reasons = 0.45, reasons + ["TJM non communiqué"]
        else:
            span = p.tjm_target - p.tjm_floor_hard
            tjm = _clip((base - p.tjm_floor_hard) / span) if span else 0.0
            if base >= p.tjm_floor_soft:
                reasons.append(f"TJM plancher {base} € ≥ {p.tjm_floor_soft} €")
            else:
                reasons.append(f"TJM plancher {base} € sous le seuil haut de gamme")

        r = norm(remote)
        rem = {"full": 1.0, "partial": 0.7, "none": 0.25}.get(r, 0.5)
        if r == "none":
            reasons.append("aucun télétravail")

        months = (dur_val or 0) * (12 if dur_per == "year" else 1 if dur_per == "month" else 0.25)
        dur = _clip(months / 12.0) if months else 0.5

        score = p.w_val_tjm * tjm + p.w_val_remote * rem + p.w_val_duration * dur
        return _clip(score), reasons

    # ---------------- point d'entrée ----------------

    def match(self, mission: dict, lang: str | None = None) -> Match:
        p = self.p
        title = mission.get("title") or ""
        job = mission.get("job") or ""
        skills = mission.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        blob = " ".join(filter(None, [title, job, " ".join(skills), mission.get("descr") or ""]))

        scored = []
        for a in self.axes:
            sk, matched, missing = self._skill_score(a["id"], skills)
            ti = self._title_score(a["id"], title, job)
            tx = self._text_score(a["id"], blob)
            fit = p.w_fit_skills * sk + p.w_fit_title * ti + p.w_fit_text * tx
            # léger bonus aux axes prioritaires, pour départager à fit égal
            fit += (5 - a.get("priority", 5)) * 0.004
            scored.append((_clip(fit), a, matched, missing, sk, ti, tx))

        scored.sort(key=lambda x: -x[0])
        fit, axis, matched, missing, sk, ti, tx = scored[0]

        val, vreasons = self.value_score(
            mission.get("tjm_min"), mission.get("tjm_max"),
            mission.get("remote"), mission.get("dur_val"), mission.get("dur_per"))

        if p.mode == "contact":
            decision = 0.85 * fit + 0.15 * val
        else:
            decision = p.w_decision_fit * fit + p.w_decision_value * val

        # Bonus stratégique : amorcer un axe rentable sur lequel il n'existe pas
        # encore de référence. Se règle par axe dans profile/cv_catalog.json.
        # Garde-fou de domaine : un intitulé générique ("directeur de projet")
        # peut masquer un métier étranger au profil (EPC, broadcast, comptabilité).
        nb = norm(blob)
        hit_groups = [g for g, terms in self.excl.items()
                      if sum(1 for t in terms if t and t in nb) >= 2]
        if hit_groups:
            pen = min(len(hit_groups) * self.excl_pen, self.excl_max)
            decision = _clip(decision - pen / 100.0)
            vreasons.append("domaine hors profil : " + ", ".join(hit_groups))

        boost = axis.get("strategic_boost", 0) or 0
        if boost:
            decision = _clip(decision + boost / 100.0)
            vreasons.append(f"bonus stratégique +{boost} ({axis['label']} sans référence)")

        tjm_base = mission.get("tjm_min") or 0
        if p.mode == "contact" and tjm_base and tjm_base < 300:
            verdict = "reject"
            vreasons.append("TJM sous le seuil de crédibilité (300 €)")
        elif p.mode == "contact" and fit * 100 < p.min_fit:
            verdict = "reject"
            vreasons.append(f"adéquation insuffisante ({fit*100:.0f} < {p.min_fit})")
        elif p.mode == "contact":
            verdict = "apply" if decision * 100 >= 62 else (
                "shortlist" if decision * 100 >= 52 else "reject")
        elif tjm_base and tjm_base < p.tjm_floor_hard:
            verdict = "reject"
            vreasons.append(f"sous le plancher dur ({p.tjm_floor_hard} €)")
        elif fit * 100 < p.min_fit:
            verdict = "reject"
            vreasons.append(f"adéquation insuffisante ({fit*100:.0f} < {p.min_fit})")
        elif decision * 100 >= p.min_decision_apply:
            verdict = "apply"
        elif decision * 100 >= p.min_decision_shortlist:
            verdict = "shortlist"
        else:
            verdict = "reject"

        reasons = [
            f"compétences couvertes {sk*100:.0f}%",
            f"intitulé {ti*100:.0f}%",
            f"proximité textuelle {tx*100:.0f}%",
        ] + vreasons

        chosen_lang = lang or ("en" if self._looks_english(blob) else "fr")

        return Match(
            aid=mission.get("aid"),
            title=title,
            company=mission.get("company"),
            tjm_min=mission.get("tjm_min"),
            tjm_max=mission.get("tjm_max"),
            axis_id=axis["id"],
            axis_label=axis["label"],
            lang=chosen_lang,
            cv_path=axis["files"][chosen_lang],
            fit=round(fit * 100),
            value=round(val * 100),
            decision_score=round(decision * 100),
            verdict=verdict,
            reasons=reasons,
            skills_matched=matched,
            skills_missing=missing,
            runners_up=[(a["label"], round(f * 100)) for f, a, *_ in scored[1:3]],
        )

    @staticmethod
    def _looks_english(text: str) -> bool:
        t = set(tokens(text))
        en = {"the", "and", "with", "team", "will", "years", "skills", "experience",
              "design", "build", "delivery", "stakeholders"}
        fr = {"les", "des", "pour", "vous", "notre", "equipe", "annees", "competences",
              "conception", "mise", "oeuvre", "besoin"}
        return len(t & en) > len(t & fr)
