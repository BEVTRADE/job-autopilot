"""
Rendu des CV : variante -> docx personnalisé -> pdf.

Le remplacement se fait dans le XML du document, ce qui préserve
intégralement la mise en forme : aucune régénération, aucun risque
de dérive typographique entre la version relue et celle envoyée.
"""
from __future__ import annotations
import os, re, shutil, subprocess, tempfile, zipfile

SOFFICE = shutil.which("soffice") or shutil.which("libreoffice")


def substitute(src_docx: str, dst_docx: str, rules: dict[str, str]) -> list[str]:
    """Applique des remplacements littéraux dans les parties word/*.xml."""
    touched = []
    zin = zipfile.ZipFile(src_docx)
    os.makedirs(os.path.dirname(dst_docx) or ".", exist_ok=True)
    with zipfile.ZipFile(dst_docx, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                try:
                    t = data.decode("utf-8")
                    before = t
                    for old, new in rules.items():
                        t = t.replace(_esc(old), _esc(new))
                    if t != before:
                        touched.append(item.filename)
                        data = t.encode("utf-8")
                except UnicodeDecodeError:
                    pass
            zout.writestr(item, data)
    zin.close()
    return touched


def to_pdf(docx_path: str, out_dir: str, timeout: int = 120) -> str:
    """Convertit en PDF. Renvoie le chemin produit."""
    if not SOFFICE:
        raise RuntimeError("LibreOffice introuvable : impossible de produire le PDF")
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    # Conversion dans un répertoire neuf : LibreOffice échoue s'il doit écraser
    # un PDF existant sur un montage sans droit de suppression.
    with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as profile:
        r = subprocess.run(
            [SOFFICE, "--headless", f"-env:UserInstallation=file://{profile}",
             "--convert-to", "pdf", "--outdir", work, docx_path],
            capture_output=True, timeout=timeout)
        produced = os.path.join(work, name)
        if r.returncode != 0 or not os.path.exists(produced):
            raise RuntimeError(
                f"conversion PDF échouée ({r.returncode}) : "
                f"{(r.stderr or b'').decode('utf-8', 'replace')[:300]}")
        pdf = os.path.join(out_dir, name)
        with open(produced, "rb") as src, open(pdf, "wb") as dst:
            shutil.copyfileobj(src, dst)          # truncate, pas de suppression
    if os.path.getsize(pdf) < 4096:
        raise RuntimeError(f"PDF suspect (trop petit) : {pdf}")
    return pdf


def build(variant_docx: str, out_dir: str, name: str,
          rules: dict[str, str] | None = None) -> dict:
    """Produit le couple docx + pdf nommé pour une candidature donnée."""
    os.makedirs(out_dir, exist_ok=True)
    docx = os.path.join(out_dir, f"{name}.docx")
    if rules:
        substitute(variant_docx, docx, rules)
    else:
        shutil.copy(variant_docx, docx)
    pdf = to_pdf(docx, out_dir)
    return {"docx": docx, "pdf": pdf, "octets": os.path.getsize(pdf)}


def slug(*parts: str) -> str:
    s = "_".join(p for p in parts if p)
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return re.sub(r"_+", "_", s).strip("_")[:80]


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
