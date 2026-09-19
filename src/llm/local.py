"""
Client du modèle de langage local (Ollama), sans dépendance externe.

Principe : les données du candidat ne quittent pas la machine. Le client
refuse donc toute adresse qui n'est pas locale, et n'a ni clé ni jeton.

On parle à l'API native d'Ollama (/api/chat) plutôt qu'à sa couche de
compatibilité, pour deux raisons : le paramètre `format` y accepte un schéma
JSON, qui contraint la sortie du modèle au décodage (sorties structurées), et
`num_ctx` y fixe la fenêtre de contexte, trop courte par défaut.
"""
from __future__ import annotations
import json, urllib.request, urllib.error
from urllib.parse import urlparse

HOTES_LOCAUX = {"localhost", "127.0.0.1", "::1"}


class LLMIndisponible(RuntimeError):
    """Serveur absent, modèle absent, ou réponse inexploitable."""


def _verifier_local(base_url: str) -> str:
    h = urlparse(base_url).hostname or ""
    if h not in HOTES_LOCAUX:
        raise ValueError(f"adresse non locale refusée : {base_url} — le modèle doit tourner sur ce poste")
    return base_url.rstrip("/")


class LLMLocal:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5-coder:14b",
                 num_ctx: int = 16384, timeout: int = 300, temperature: float = 0.0):
        self.base_url = _verifier_local(base_url)
        self.model, self.num_ctx, self.timeout, self.temperature = model, num_ctx, timeout, temperature
        self.mesure: dict = {}          # chronométrage de la dernière requête, tel que rendu par Ollama

    @classmethod
    def depuis_config(cls, cfg: dict) -> "LLMLocal":
        l = (cfg or {}).get("llm", {})
        if l.get("provider") != "ollama":
            raise ValueError("llm.provider doit valoir « ollama » pour le modèle local")
        return cls(l.get("base_url", "http://127.0.0.1:11434"), l.get("model", "qwen2.5-coder:14b"),
                   int(l.get("num_ctx", 16384)), int(l.get("timeout_s", 300)))

    def _post(self, chemin: str, corps: dict | None = None) -> dict:
        data = json.dumps(corps).encode() if corps is not None else None
        req = urllib.request.Request(self.base_url + chemin, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise LLMIndisponible(f"{chemin} : HTTP {e.code} {e.read()[:200]!r}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise LLMIndisponible(f"serveur local injoignable ({self.base_url}) : {e}") from e

    def modeles(self) -> list[str]:
        return [m["name"] for m in self._post("/api/tags").get("models", [])]

    def disponible(self) -> tuple[bool, str]:
        try:
            noms = self.modeles()
        except LLMIndisponible as e:
            return False, str(e)
        if not any(n == self.model or n.split(":")[0] == self.model for n in noms):
            return False, f"modèle {self.model} absent (présents : {', '.join(noms) or 'aucun'}) — ollama pull {self.model}"
        return True, "ok"

    def json(self, systeme: str, utilisateur: str, schema: dict) -> dict:
        """Une requête, une réponse JSON conforme au schéma, ou une exception."""
        rep = self._post("/api/chat", {
            "model": self.model, "stream": False, "format": schema,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
            "messages": [{"role": "system", "content": systeme},
                         {"role": "user", "content": utilisateur}]})
        s = 1e9                          # Ollama compte en nanosecondes
        self.mesure = {"charge_s": round(rep.get("load_duration", 0) / s, 1),
                       "jetons_prompt": rep.get("prompt_eval_count"),
                       "prompt_s": round(rep.get("prompt_eval_duration", 0) / s, 1),
                       "jetons_sortie": rep.get("eval_count"),
                       "sortie_s": round(rep.get("eval_duration", 0) / s, 1),
                       "total_s": round(rep.get("total_duration", 0) / s, 1)}
        texte = (rep.get("message") or {}).get("content", "")
        try:
            return json.loads(texte)
        except json.JSONDecodeError as e:
            raise LLMIndisponible(f"réponse non JSON : {texte[:200]!r}") from e
