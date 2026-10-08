#!/usr/bin/env python3
"""
Patch n°3 pour public/createError.js (à lancer APRÈS patch_createError.py et patch_createError_v2.py).

Ajoute, pour Windows 7 (Aero) uniquement, les boutons « Réduire » et « Agrandir »
à gauche du bouton « Fermer », avec la géométrie d'une vraie fenêtre Windows 7
(Réduire 29 px + Agrandir 27 px + Fermer 47 px, collés les uns aux autres).

Nouveau paramètre : captionButtons (true/false), 15e argument de createError().
  - le titre est tronqué plus tôt pour ne pas passer sous les boutons ;
  - la fenêtre ne descend pas sous 190 px de large (comme Windows) ;
  - si la croix est désactivée, les deux boutons sont dessinés estompés.

Usage :  python patch_createError_v3.py public/createError.js
Une sauvegarde public/createError.js.bak3 est créée.
"""
import re
import shutil
import sys

FUNC = r"""
    // Boutons Réduire / Agrandir de Windows 7, collés à gauche du bouton Fermer
    // (le bouton Fermer est dessiné par le sprite de la fenêtre).
    // Géométrie mesurée sur une vraie fenêtre : Réduire 29 px, Agrandir 27 px, Fermer 47 px,
    // suspendus sous la bordure haute (y = 13 à 31). Verre translucide, coins du bas arrondis.
    // caption-buttons v2
    function drawWin7CaptionButtons(ctx, disabled) {
        const w = ctx.canvas.width;
        const xMin = w - 127;      // contour gauche de "Réduire"
        const xMax = w - 98;       // contour gauche de "Agrandir"
        const xClose = w - 71;     // contour gauche de "Fermer" (déjà dessiné)
        const yTop = 13, yBottom = 31;
        const R_OUT = 3;           // rayon du coin extérieur (bas gauche de "Réduire")
        const R_IN = 2;            // rayon des autres coins du bas
        const OUTLINE = "rgba(46,52,68,0.95)";
        // interpolation : couleurs arrondies à l'entier, mais la transparence (4e valeur) reste fractionnaire
        const mix = (a, b, t) => a.map((v, i) => i < 3 ? Math.round(v + (b[i] - v) * t) : v + (b[i] - v) * t);
        const css = (c) => `rgba(${c[0]},${c[1]},${c[2]},${(c[3]).toFixed(3)})`;

        // Verre translucide : [r, g, b, alpha] ; l'arrière-plan reste visible à travers
        function rowColor(y) {
            if (y == yTop) return [252, 252, 252, 0.92];
            if (y <= 21) return mix([255, 255, 255, 0.62], [240, 246, 255, 0.42], (y - 14) / 7);
            if (y <= 29) return mix([110, 150, 210, 0.58], [190, 215, 245, 0.42], (y - 22) / 7);
            return [255, 255, 255, 0.55];
        }

        // Rectangle arrondi uniquement en bas : coins bas-gauche (rl) et bas-droite (rr)
        function roundedBottom(x, y, wd, h, rl, rr) {
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + wd, y);
            ctx.lineTo(x + wd, y + h - rr);
            if (rr) ctx.arcTo(x + wd, y + h, x + wd - rr, y + h, rr);
            ctx.lineTo(x + rl, y + h);
            if (rl) ctx.arcTo(x, y + h, x, y + h - rl, rl);
            ctx.closePath();
        }

        ctx.save();
        ctx.globalAlpha = disabled ? 0.5 : 1;

        // 1) Fond translucide de chaque bouton, découpé selon ses coins arrondis
        const buttons = [
            { x: xMin, wd: xMax - xMin + 1, rl: R_OUT, rr: R_IN },   // Réduire
            { x: xMax, wd: xClose - xMax, rl: R_IN, rr: 0 }          // Agrandir (le bord droit touche Fermer)
        ];
        for (const b of buttons) {
            ctx.save();
            roundedBottom(b.x, yTop, b.wd, yBottom - yTop + 1, b.rl, b.rr);
            ctx.clip();
            for (let y = yTop; y < yBottom; y++) {
                const c = rowColor(y);
                ctx.fillStyle = css(c);
                ctx.fillRect(b.x, y, b.wd, 1);
                // reflets intérieurs au bord gauche/droit
                ctx.fillStyle = css([255, 255, 255, Math.min(0.6, c[3] * 0.7 + 0.15)]);
                ctx.fillRect(b.x + 1, y, 1, 1);
                ctx.fillRect(b.x + b.wd - 2, y, 1, 1);
            }
            ctx.restore();
        }

        // 2) Contours sombres (1 px, tracés au centre des pixels pour rester nets)
        ctx.lineWidth = 1;
        ctx.strokeStyle = OUTLINE;
        ctx.lineJoin = "round";
        // Réduire : côté gauche + coin arrondi + bas, jusqu'au séparateur
        ctx.beginPath();
        ctx.moveTo(xMin + 0.5, yTop);
        ctx.lineTo(xMin + 0.5, yBottom + 0.5 - R_OUT);
        ctx.arcTo(xMin + 0.5, yBottom + 0.5, xMin + 0.5 + R_OUT, yBottom + 0.5, R_OUT);
        ctx.lineTo(xMax + 0.5 - R_IN, yBottom + 0.5);
        ctx.arcTo(xMax + 0.5, yBottom + 0.5, xMax + 0.5, yBottom + 0.5 - R_IN, R_IN);
        ctx.lineTo(xMax + 0.5, yTop);
        ctx.stroke();
        // Agrandir : séparateur déjà tracé, coin bas-gauche arrondi + bas jusqu'à Fermer
        ctx.beginPath();
        ctx.moveTo(xMax + 0.5, yBottom + 0.5 - R_IN);
        ctx.arcTo(xMax + 0.5, yBottom + 0.5, xMax + 0.5 + R_IN, yBottom + 0.5, R_IN);
        ctx.lineTo(xClose, yBottom + 0.5);
        ctx.stroke();

        // 3) Liseré blanc extérieur (gauche + bas), arrondi lui aussi
        ctx.strokeStyle = "rgba(252,252,252,0.72)";
        ctx.beginPath();
        ctx.moveTo(xMin - 0.5, yTop);
        ctx.lineTo(xMin - 0.5, yBottom + 0.5 - R_OUT);
        ctx.arcTo(xMin - 0.5, yBottom + 1.5, xMin - 0.5 + R_OUT + 1, yBottom + 1.5, R_OUT + 1);
        ctx.lineTo(xClose - 1, yBottom + 1.5);
        ctx.stroke();

        // 4) Symboles (11 px de large), opaques comme dans Windows
        function glyph(kind, x, y) {
            const g = document.createElement("canvas");
            g.width = 11;
            g.height = kind == "min" ? 5 : 9;
            const gc = g.getContext("2d");
            const grad = gc.createLinearGradient(0, 0, 0, g.height);
            grad.addColorStop(0, "#ffffff");
            grad.addColorStop(1, "#dfdfdf");
            gc.fillStyle = "rgb(81,85,103)";
            gc.fillRect(0, 0, 11, g.height);
            gc.fillStyle = grad;
            if (kind == "min") {
                gc.fillRect(1, 1, 9, 3);
            } else {
                gc.fillRect(1, 1, 9, 7);
                gc.fillStyle = "rgb(81,85,103)";
                gc.fillRect(2, 3, 7, 4);       // contour intérieur
                gc.clearRect(3, 4, 5, 2);      // creux : laisse voir le bouton
            }
            ctx.drawImage(g, x, y);
        }
        glyph("min", Math.floor((xMin + xMax) / 2 - 5), 23);
        glyph("max", Math.floor((xMax + xClose - 1) / 2 - 5), 18);

        ctx.restore();
    }
"""


def die(msg):
    sys.exit("ERREUR : " + msg)


def main(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    if "CLIENT_RECT" not in src:
        die("lance d'abord patch_createError.py puis patch_createError_v2.py.")
    if "drawWin7CaptionButtons" in src:
        die("déjà patché (drawWin7CaptionButtons trouvé).")

    shutil.copyfile(path, path + ".bak3")

    # 1) signature
    old = "emptyClient = false) {"
    if src.count(old) != 1:
        die("signature introuvable (patch v2 appliqué ?).")
    src = src.replace(old, "emptyClient = false, captionButtons = false) {")

    # 2) fonction de dessin + normalisation, juste avant drawTitleIcon
    anchor = "    function drawTitleIcon(ctx, key) {"
    if src.count(anchor) != 1:
        die("ancre 'function drawTitleIcon' introuvable.")
    block = FUNC.strip("\n") + "\n\n"
    block += '    captionButtons = !!captionButtons && system == "win7";\n\n'
    src = src.replace(anchor, block + anchor)

    # 3) modifications dans la fonction win7()
    m = re.search(r"^[ \t]*async function win7\(\) \{", src, re.M)
    n = re.search(r"^[ \t]*async function win8\(\) \{", src, re.M)
    if not m or not n or n.start() < m.start():
        die("fonction win7() introuvable.")
    seg = src[m.start():n.start()]

    edits = [
        ("chunkWidth + 115 + TS > canvas.width",
         "chunkWidth + 115 + TS + (captionButtons ? 56 : 0) > canvas.width"),
        ('canvas = document.getElementById("canvas");',
         'if (captionButtons && canvasWidth < 190) canvasWidth = 190;\n\n        '
         'canvas = document.getElementById("canvas");'),
        ('drawTitleIcon(ctx, "win7");',
         'drawTitleIcon(ctx, "win7");\n        '
         'if (captionButtons) drawWin7CaptionButtons(ctx, crossDisabled);'),
    ]
    for old, new in edits:
        if seg.count(old) != 1:
            die(f"win7 : '{old[:45]}...' trouvé {seg.count(old)} fois (attendu 1).")
        seg = seg.replace(old, new)
    src = src[:m.start()] + seg + src[n.start():]

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"OK : {path} patché (boutons Réduire/Agrandir pour Windows 7).")
    print(f"Sauvegarde : {path}.bak3")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage : python patch_createError_v3.py public/createError.js")
    main(sys.argv[1])
