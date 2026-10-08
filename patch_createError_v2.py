#!/usr/bin/env python3
"""
Patch n°2 pour public/createError.js (à lancer APRÈS patch_createError.py).

Ajoute :
  - un paramètre `titleIcon`  : { type: "builtin", id } | { type: "custom", src } | null
    -> une icône 16x16 dans la barre de titre, le titre est décalé pour lui faire place
  - un paramètre `emptyClient` : true => l'intérieur de la fenêtre est entièrement
    vidé ET transparent (canal alpha = 0). Seuls restent les bordures et la barre de titre.
  - les fonctions d'OS sont maintenant attendues (await) : l'image est entièrement
    dessinée avant que createError() ne rende la main (nécessaire pour vider l'intérieur,
    et les erreurs de rendu remontent enfin jusqu'au try/catch de ui.js).

Usage :  python patch_createError_v2.py public/createError.js
Une sauvegarde public/createError.js.bak2 est créée.
"""
import re
import shutil
import sys

# --- Rectangle intérieur par OS, mesuré sur le canvas final : marges gauche/haut/droite/bas ---
CLIENT_RECT = {
    "win1":     (2, 18, 2, 2),
    "win3":     (6, 24, 6, 6),
    "win31":    (1, 20, 1, 1),
    "win9x":    (3, 21, 3, 3),
    "win2k":    (3, 21, 3, 3),
    "winwh":    (4, 23, 4, 4),
    "winxp":    (3, 29, 3, 3),
    "winlh":    (3, 23, 3, 3),
    "winvista": (8, 30, 8, 8),
    "win7":     (21, 42, 25, 26),
    "win8":     (8, 31, 8, 8),
    "win10":    (18, 48, 22, 24),
    "win11":    (47, 64, 49, 87),
}

# --- Icône de barre de titre : position (x, y) de l'icône 16x16 et décalage du titre ---
# win1 / win3 / win31 n'ont pas d'icône dans la barre de titre : non gérés.
TITLE_ICON = {
    "win9x":    (4, 4, 16),
    "win2k":    (4, 4, 17),
    "winwh":    (5, 4, 12),
    "winxp":    (6, 6, 19),
    "winlh":    (6, 4, 18),
    "winvista": (8, 8, 19),
    "win7":     (21, 18, 20),
    "win8":     (8, 8, 0),
    "win10":    (26, 23, 26),
    "win11":    (55, 40, 24),
}

OS_KEY = {
    "win1": "win1", "win3": "win3", "win31": "win31", "win95": "win9x", "win98": "win9x",
    "win2k": "win2k", "winwh": "winwh", "winxp": "winxp", "winlh-4093": "winlh",
    "winvista": "winvista", "win7": "win7", "win8": "win8", "win10": "win10", "win11": "win11",
}

# --- Modifications du dessin du titre, par fonction d'OS : (ancien, nouveau, occurrences attendues) ---
def tw(old_chunk):  # tronque le titre en tenant compte du décalage
    return (old_chunk, old_chunk.replace(" > canvas.width", " + TS > canvas.width"), 1)

TITLE_PATCHES = {
    "win9x": [
        tw("chunkWidth + 40 > canvas.width"),
        ("await drawBitmaps(ctx, title, 6, 5, true)",
         'await drawBitmaps(ctx, title, 6 + TS, 5, true);\n        drawTitleIcon(ctx, "win9x")', 1),
    ],
    "win2k": [
        tw("chunkWidth + 45 > canvas.width"),
        ("await drawBitmaps(ctx, title, 5, 5, true);",
         'await drawBitmaps(ctx, title, 5 + TS, 5, true);\n        drawTitleIcon(ctx, "win2k");', 1),
    ],
    "winwh": [
        tw("chunkWidth + 50 > canvas.width"),
        ("await drawBitmaps(ctx, title, 13, 5, true);",
         'await drawBitmaps(ctx, title, 13 + TS, 5, true);\n        drawTitleIcon(ctx, "winwh");', 1),
    ],
    "winxp": [
        tw("chunkWidth + 50 > canvas.width"),
        ("await drawTitle(ctx, title, 7, 7);",
         'await drawTitle(ctx, title, 7 + TS, 7);\n        drawTitleIcon(ctx, "winxp");', 1),
    ],
    "winlh": [
        tw("chunkWidth + 40 > canvas.width"),
        ("await drawBitmaps(testCtx, title, 6, 6, true)",
         "await drawBitmaps(testCtx, title, 6 + TS, 6, true)", 3),
        ("testBitmaps(title, true) + 18;", "testBitmaps(title, true) + 18 + TS;", 1),
        ("testCanvas.width = ", 'drawTitleIcon(ctx, "winlh");\n\n        testCanvas.width = ', 1),
    ],
    "winvista": [
        tw("chunkWidth + 115 > canvas.width"),
        ("await drawBitmaps(ctx, title, 9, 10, 1, false);",
         'await drawBitmaps(ctx, title, 9 + TS, 10, 1, false);\n        drawTitleIcon(ctx, "winvista");', 1),
    ],
    "win7": [
        tw("chunkWidth + 115 > canvas.width"),
        ("titleGlowLeft.h, 4, 13,", "titleGlowLeft.h, 4 + TS, 13,", 1),
        ("titleGlowMiddle.h, 31, 13, testBitmaps(title) - 17,",
         "titleGlowMiddle.h, 31 + TS, 13, testBitmaps(title) - 17,", 1),
        ("titleGlowRight.h, 14 + testBitmaps(title), 13,",
         "titleGlowRight.h, 14 + TS + testBitmaps(title), 13,", 1),
        ("await drawBitmaps(ctx, title, 21, 20, 1, false);",
         'await drawBitmaps(ctx, title, 21 + TS, 20, 1, false);\n        drawTitleIcon(ctx, "win7");', 1),
    ],
    "win8": [
        ("await drawTitle(ctx, title, titleX, 3);",
         'await drawTitle(ctx, title, titleX, 3);\n        drawTitleIcon(ctx, "win8");', 1),
    ],
    "win10": [
        tw("chunkWidth + 95 > canvas.width"),
        ("await drawBitmaps(ctx, title, 24, 24);",
         'await drawBitmaps(ctx, title, 24 + TS, 24);\n        drawTitleIcon(ctx, "win10");', 1),
    ],
    "win11": [
        tw("chunkWidth + 142 > canvas.width"),
        ("await drawBitmaps(ctx, title, 53, 40);",
         'await drawBitmaps(ctx, title, 53 + TS, 40);\n        drawTitleIcon(ctx, "win11");', 1),
    ],
}

HELPERS = r'''
    // === Ajouts v2 : intérieur vide / icône dans la barre de titre ===
    if (emptyClient) {
        if (!clientSize) clientSize = { w: 500, h: 300 };
        content = "";
        button1 = { name: "", disabled: false, rec: false };
        button2 = null;
        button3 = null;
    }

    const osKey = OS_KEY[system];
    let TS = 0;                 // décalage horizontal du titre quand une icône est affichée
    let titleIconData = null;   // { img, sx, sy, sw, sh }

    function loadImg(src) {
        return new Promise(resolve => {
            const im = new Image();
            im.onload = () => resolve(im);
            im.onerror = () => resolve(null);
            im.src = src;
        });
    }

    async function loadTitleIcon(spec) {
        if (spec.type === "custom" && spec.src) {
            const im = await loadImg(spec.src);
            return im ? { img: im, sx: 0, sy: 0, sw: im.naturalWidth, sh: im.naturalHeight } : null;
        }
        if (spec.type === "builtin") {
            const sheet = system == "win98" ? assetsArray.win98
                : (sysName == "winvista" ? assetsArray.win7 : assetsArray[sysName]);
            if (!sheet) return null;
            const max = Object.keys(sheet.assets).filter(k => k.startsWith("i-")).length;
            const id = Math.min(Math.max(1, Math.trunc(Number(spec.id)) || 1), max);
            const info = sheet.assets[`i-${id}`];
            if (!info) return null;
            const im = await loadImg(`data:image/png;base64,${sheet.src}`);
            return im ? { img: im, sx: info.x, sy: info.y, sw: info.w, sh: info.h } : null;
        }
        return null;
    }

    function drawTitleIcon(ctx, key) {
        if (!titleIconData) return;
        const p = TITLE_ICON[key];
        const d = titleIconData;
        const scale = Math.min(16 / d.sw, 16 / d.sh);
        const w = Math.max(1, Math.round(d.sw * scale));
        const h = Math.max(1, Math.round(d.sh * scale));
        ctx.save();
        ctx.globalAlpha = 1;
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(d.img, d.sx, d.sy, d.sw, d.sh,
            p.x + Math.floor((16 - w) / 2), p.y + Math.floor((16 - h) / 2), w, h);
        ctx.restore();
    }
'''

BEFORE_SWITCH = '''    if (titleIcon && osKey && TITLE_ICON[osKey]) {
        titleIconData = await loadTitleIcon(titleIcon);
        if (titleIconData) TS = TITLE_ICON[osKey].shift;
    }

'''

AFTER_SWITCH = '''
    // Intérieur vide et transparent : on efface le rectangle client (alpha = 0)
    if (emptyClient && osKey && CLIENT_RECT[osKey]) {
        const r = CLIENT_RECT[osKey];
        canvas.getContext("2d").clearRect(r.l, r.t, canvas.width - r.l - r.r, canvas.height - r.t - r.b);
    }
'''


def js_tables():
    t = "// Rectangle intérieur par OS (marges gauche/haut/droite/bas), utilisé pour vider la fenêtre.\n"
    t += "const CLIENT_RECT = {\n"
    for k, (l, tp, r, b) in CLIENT_RECT.items():
        t += f"    {k}: {{ l: {l}, t: {tp}, r: {r}, b: {b} }},\n"
    t += "};\n\n"
    t += "// Icône 16x16 dans la barre de titre : position et décalage du texte du titre.\n"
    t += "const TITLE_ICON = {\n"
    for k, (x, y, s) in TITLE_ICON.items():
        t += f"    {k}: {{ x: {x}, y: {y}, shift: {s} }},\n"
    t += "};\n\n"
    t += "const OS_KEY = {\n"
    for k, v in OS_KEY.items():
        t += f'    "{k}": "{v}",\n'
    t += "};\n\n"
    return t


def die(msg):
    sys.exit("ERREUR : " + msg)


def main(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    if "CLIENT_LAYOUT" not in src:
        die("lance d'abord patch_createError.py (CLIENT_LAYOUT introuvable).")
    if "CLIENT_RECT" in src:
        die("déjà patché (CLIENT_RECT trouvé).")

    shutil.copyfile(path, path + ".bak2")

    # 1) signature
    old = "clientSize = null) {"
    if src.count(old) != 1:
        die("signature de createError (clientSize = null) introuvable.")
    src = src.replace(old, "clientSize = null, titleIcon = null, emptyClient = false) {")

    # 2) tables avant la fonction
    marker = "async function createError("
    if src.count(marker) != 1:
        die("déclaration de createError introuvable.")
    src = src.replace(marker, js_tables() + marker)

    # 3) helpers après `let canvas;`
    anchor = "    let canvas;\n"
    if src.count(anchor) != 1:
        die("ancre 'let canvas;' introuvable ou ambiguë.")
    src = src.replace(anchor, anchor + HELPERS)

    # 4) chargement de l'icône avant le switch + await des fonctions d'OS + effacement après
    sw = "    switch (system) {"
    if src.count(sw) != 1:
        die("ancre 'switch (system) {' introuvable.")
    head, tail = src.split(sw)
    tail, n = re.subn(r"\n(\s+)(win\w+)\(\);", r"\n\1await \2();", tail)
    if n != 13:
        die(f"{n} appels d'OS trouvés dans le switch au lieu de 13.")
    tail = tail.rstrip()
    if not tail.endswith("}\n}"):
        die("la fin du fichier n'a pas la forme attendue ('}' du switch puis '}' de la fonction).")
    tail = tail[:-1].rstrip("\n") + "\n" + AFTER_SWITCH + "}\n"
    src = head + BEFORE_SWITCH + sw + tail

    # 5) dessin du titre dans chaque fonction d'OS
    header = re.compile(r"^[ \t]*async function (win\w+)\(\) \{", re.M)
    heads = list(header.finditer(src))
    out, last = [], 0
    done = set()
    for i, h in enumerate(heads):
        name = h.group(1)
        start = h.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(src)
        out.append(src[last:start])
        seg = src[start:end]
        last = end
        if name in TITLE_PATCHES:
            for old, new, expected in TITLE_PATCHES[name]:
                c = seg.count(old)
                if c != expected:
                    die(f"{name} : '{old[:50]}...' trouvé {c} fois (attendu {expected}).")
                seg = seg.replace(old, new)
            done.add(name)
        out.append(seg)
    out.append(src[last:])
    src = "".join(out)

    missing = set(TITLE_PATCHES) - done
    if missing:
        die(f"fonctions d'OS introuvables : {sorted(missing)}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"OK : {path} patché (icône de titre sur {len(done)} OS, intérieur vide sur 13).")
    print(f"Sauvegarde : {path}.bak2")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage : python patch_createError_v2.py public/createError.js")
    main(sys.argv[1])
