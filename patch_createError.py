#!/usr/bin/env python3
"""
Patch public/createError.js pour permettre de fixer la taille de la ZONE CLIENT
(l'intérieur de la fenêtre : texte, icône, boutons). Les bordures et la barre
de titre sont ajoutées autour, donc le canvas final est plus grand.

Usage :  python patch_createError.py public/createError.js
Une sauvegarde public/createError.js.bak est créée.

Ce que fait le patch :
  1. ajoute un 12e paramètre `clientSize` ({w, h} ou null) à createError()
  2. ajoute le tableau CLIENT_LAYOUT (épaisseur des bordures par OS)
  3. dans chaque fonction d'OS :
       - la largeur max du texte suit la largeur demandée (retour à la ligne)
       - canvasWidth / canvasHeight sont forcés juste avant la création du canvas
"""
import re
import shutil
import sys

# dw / dh : (taille du canvas) - (taille de la zone client)
# tx      : canvasWidth - largeur max du texte (marge gauche de l'icône + marge droite)
LAYOUT = {
    "win1":     dict(dw=4,  dh=20,  tx=78),
    "win3":     dict(dw=2,  dh=21,  tx=91),   # canvas réel = canvasWidth+10 / canvasHeight+9
    "win31":    dict(dw=2,  dh=21,  tx=91),
    "win9x":    dict(dw=6,  dh=24,  tx=79),
    "win2k":    dict(dw=6,  dh=24,  tx=88),
    "winwh":    dict(dw=8,  dh=27,  tx=79),
    "winxp":    dict(dw=6,  dh=32,  tx=88),
    "winlh":    dict(dw=6,  dh=26,  tx=78),
    "winvista": dict(dw=16, dh=38,  tx=83),
    "win7":     dict(dw=46, dh=68,  tx=108),
    "win8":     dict(dw=16, dh=39,  tx=79),
    "win10":    dict(dw=40, dh=72,  tx=105),
    "win11":    dict(dw=96, dh=151, tx=160),
}


def main(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    if "CLIENT_LAYOUT" in src:
        sys.exit("Déjà patché (CLIENT_LAYOUT trouvé). Rien à faire.")

    shutil.copyfile(path, path + ".bak")

    # 1) signature de createError + normalisation de clientSize
    sig = re.compile(
        r"(async function createError\([^)]*?gradientSecondaryColor)\)\s*\{"
    )
    m = sig.search(src)
    if not m:
        sys.exit("Signature de createError introuvable.")
    src = (
        src[: m.start()]
        + m.group(1)
        + ", clientSize = null) {\n"
        + "    if (clientSize) clientSize = {\n"
        + "        w: Math.max(100, Math.round(Number(clientSize.w) || 0)),\n"
        + "        h: Math.max(60, Math.round(Number(clientSize.h) || 0))\n"
        + "    };\n"
        + src[m.end():]
    )

    # 2) tableau CLIENT_LAYOUT, placé avant la fonction
    table = "// Épaisseur des bordures/barre de titre par OS (utilisé quand clientSize est défini).\n"
    table += "// dw/dh = taille du canvas - taille de la zone client ; tx = marge horizontale du texte.\n"
    table += "const CLIENT_LAYOUT = {\n"
    for k, v in LAYOUT.items():
        table += f"    {k}: {{ dw: {v['dw']}, dh: {v['dh']}, tx: {v['tx']} }},\n"
    table += "};\n\n"
    src = src.replace("async function createError(", table + "async function createError(", 1)

    # 3) patch de chaque fonction d'OS
    header = re.compile(r"^[ \t]*async function (win\w+)\(\) \{", re.M)
    heads = list(header.finditer(src))
    names = [h.group(1) for h in heads]
    missing = [k for k in LAYOUT if k not in names]
    if missing:
        sys.exit(f"Fonctions d'OS introuvables : {missing}")

    out = []
    last = 0
    report = []
    for i, h in enumerate(heads):
        name = h.group(1)
        start = h.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(src)
        out.append(src[last:start])
        seg = src[start:end]
        last = end

        if name not in LAYOUT:
            out.append(seg)
            continue

        ok_max = ok_canvas = False

        def repl_max(mm, name=name):
            return (
                f"const maxWidth = clientSize ? Math.max(24, clientSize.w + "
                f"CLIENT_LAYOUT.{name}.dw - CLIENT_LAYOUT.{name}.tx) : {mm.group(1)};"
            )

        seg, n = re.subn(r"const maxWidth = (\d+);", repl_max, seg, count=1)
        ok_max = n == 1

        anchor = 'canvas = document.getElementById("canvas");'
        inject = (
            f"if (clientSize) {{\n"
            f"            canvasWidth = clientSize.w + CLIENT_LAYOUT.{name}.dw;\n"
            f"            canvasHeight = clientSize.h + CLIENT_LAYOUT.{name}.dh;\n"
            f"        }}\n\n        "
        )
        if anchor in seg:
            seg = seg.replace(anchor, inject + anchor, 1)
            ok_canvas = True

        report.append((name, ok_max, ok_canvas))
        out.append(seg)

    out.append(src[last:])
    result = "".join(out)

    bad = [r for r in report if not (r[1] and r[2])]
    for name, a, b in report:
        print(f"  {name:9s} maxWidth:{'ok' if a else 'ECHEC'}  canvas:{'ok' if b else 'ECHEC'}")
    if bad:
        sys.exit("Patch incomplet, fichier NON modifié (la sauvegarde .bak reste intacte).")

    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nOK : {path} patché ({len(report)} OS). Sauvegarde : {path}.bak")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage : python patch_createError.py public/createError.js")
    main(sys.argv[1])
