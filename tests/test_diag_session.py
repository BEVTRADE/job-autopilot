"""EPIC-12 : le journal de durée ne contient jamais une valeur de cookie."""
import datetime as dt, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import diag_session as d

# Valeurs reconnaissables : si l'une d'elles apparaît dans le fichier, le test échoue.
SECRETS = {"jwt_s": "SECRET-JWT-S-eyJhbGciOi", "jwt_hp": "SECRET-JWT-HP-abc.def.ghi",
           "refresh_token": "SECRET-REFRESH-0123456789", "_pk_id": "SECRET-AUDIENCE-777",
           "cc_cookie": "SECRET-CONSENT-999"}
EXPIRE = dt.datetime(2026, 9, 20, 8, 15, 30).timestamp()


def _cookies(sans=()):
    return [{"name": n, "value": v, "domain": ".free-work.com", "path": "/",
             "expires": EXPIRE, "httpOnly": True, "secure": True}
            for n, v in SECRETS.items() if n not in sans]


def _ecrire(cookies, chemin="/fr/applications"):
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "sous", "diag.jsonl")
        d.ajouter_journal(d.ligne_journal(True, cookies, chemin), f)
        d.ajouter_journal(d.ligne_journal(True, cookies, chemin), f)
        return open(f, encoding="utf-8").read()


def test_aucune_valeur_de_cookie_dans_le_fichier():
    brut = _ecrire(_cookies())
    for valeur in SECRETS.values():
        assert valeur not in brut
    assert "SECRET" not in brut


def test_seules_des_cles_connues_sont_ecrites():
    ligne = json.loads(_ecrire(_cookies()).splitlines()[0])
    assert set(ligne) == {"date", "connecte", "page", "jwt_s", "jwt_hp", "refresh_token"}
    for nom in d.COOKIES_AUTH:
        assert set(ligne[nom]) == {"present", "longueur", "expire"}
        assert isinstance(ligne[nom]["longueur"], int)


def test_longueur_et_expiration_relevees():
    ligne = json.loads(_ecrire(_cookies()).splitlines()[0])
    assert ligne["jwt_s"]["present"] and ligne["jwt_s"]["longueur"] == len(SECRETS["jwt_s"])
    assert ligne["jwt_s"]["expire"] == "2026-09-20T08:15:30"


def test_cookie_absent_ou_de_session():
    ligne = d.ligne_journal(False, _cookies(sans=("jwt_s",)), "/fr/login")
    assert ligne["jwt_s"] == {"present": False, "longueur": 0, "expire": None}
    assert not ligne["connecte"]
    session = [dict(c, expires=-1) for c in _cookies()]
    assert d.ligne_journal(True, session, "/")["refresh_token"]["expire"] is None


def test_cookie_d_un_autre_domaine_ignore():
    autre = [dict(c, domain=".exemple.org") for c in _cookies()]
    assert not d.ligne_journal(True, autre, "/")["jwt_s"]["present"]


def test_page_sans_parametres():
    ligne = d.ligne_journal(False, [], "/fr/login")
    assert ligne["page"] == "/fr/login"


def test_le_journal_ajoute_sans_ecraser_et_reste_prive():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "diag.jsonl")
        for _ in range(3):
            d.ajouter_journal(d.ligne_journal(True, _cookies(), "/fr/applications"), f)
        assert len(open(f, encoding="utf-8").read().splitlines()) == 3
        assert oct(os.stat(f).st_mode & 0o777) == "0o600"


def test_verrou_partage_avec_le_matin():
    with tempfile.TemporaryDirectory() as tmp:
        v = os.path.join(tmp, "verrou")
        assert d.prendre_verrou(v)
        assert not d.prendre_verrou(v)        # déjà pris : la visite s'abstient
        os.rmdir(v)
        assert d.prendre_verrou(v)
    assert d.VERROU == os.path.expanduser("~/.job-autopilot/verrou")


class _Loc:
    def __init__(self, present): self.present = present
    @property
    def first(self): return self
    def wait_for(self, timeout=0):
        if not self.present:
            raise TimeoutError("marqueur absent")


class _Page:
    def __init__(self, connecte, url):
        self.connecte, self.url = connecte, url
    def goto(self, url, wait_until=None): pass
    def wait_for_load_state(self, etat, timeout=0): pass
    def locator(self, sel):
        assert sel == "[data-testid='user-menu']"      # le marqueur convenu
        return _Loc(self.connecte)


class _Ctx:
    def cookies(self): return _cookies()


def test_visiter_connecte_ne_transporte_aucune_valeur():
    ligne = d.visiter(_Page(True, "https://www.free-work.com/fr/applications"), _Ctx())
    assert ligne["connecte"] and ligne["page"] == "/fr/applications"
    assert "SECRET" not in json.dumps(ligne)


def test_visiter_redirige_vers_la_connexion():
    url = "https://www.free-work.com/fr/login?redirect=/fr/applications&t=SECRET-JETON"
    ligne = d.visiter(_Page(False, url), _Ctx())
    assert not ligne["connecte"] and ligne["page"] == "/fr/login"
    assert "SECRET" not in json.dumps(ligne)


def test_agent_launchd_toutes_les_6_heures():
    import plistlib
    brut = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "scripts", "launchd", "diag-session.plist"), encoding="utf-8").read()
    p = plistlib.loads(brut.replace("@RACINE@", "/r").replace("@PYTHON@", "/p").encode())
    assert p["StartInterval"] == 6 * 3600
    assert p["ProgramArguments"][-1] == "--visiter"
    assert p["Label"] != "fr.kiras.jobautopilot"          # ne remplace pas l'agent du matin
