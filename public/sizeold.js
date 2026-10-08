// size.js — options supplémentaires pour winerr :
//   1. taille de fenêtre personnalisée (zone intérieure, bordures ajoutées autour)
//   2. intérieur vide et totalement transparent
//   3. icône 16x16 dans la barre de titre (icône intégrée ou image personnalisée)
//
// À charger APRÈS ui.js dans generator.html :
//   <script src="./createError.js"></script>
//   <script src="./ui.js"></script>
//   <script src="./size.js"></script>
(function () {
    const STORE_KEY = "winerr-extra-options";
    const MIN_W = 100, MIN_H = 60, MAX = 3840;
    const NO_TITLE_ICON = ["win1", "win3", "win31"]; // pas d'icône dans la barre de titre à l'époque

    const osSelect = document.querySelector("#os");
    const osCard = osSelect && osSelect.closest(".card-winerr");
    if (!osCard) return;

    // ---------- Interface ----------
    const sizeCard = document.createElement("div");
    sizeCard.className = "card-winerr selectors-long";
    sizeCard.innerHTML = `
        <div class="selector">
            <div>
                <input type="checkbox" id="client-size-on">
                <label for="client-size-on">Fixer la taille de la fenêtre</label>
            </div>
        </div>
        <div class="selector">
            <label for="client-w">Largeur (px) :</label>
            <input type="number" id="client-w" min="${MIN_W}" max="${MAX}" step="1" value="500" disabled>
        </div>
        <div class="selector">
            <label for="client-h">Hauteur (px) :</label>
            <input type="number" id="client-h" min="${MIN_H}" max="${MAX}" step="1" value="500" disabled>
            <small style="opacity:.6">Zone intérieure, sans bordures ni barre de titre.</small>
        </div>
        <div class="selector">
            <div>
                <input type="checkbox" id="client-empty">
                <label for="client-empty">Intérieur vide et transparent</label>
            </div>
            <small style="opacity:.6">Aucun texte, icône ni bouton : seuls la barre de titre et les bordures restent.</small>
        </div>`;

    const iconCard = document.createElement("div");
    iconCard.className = "card-winerr selectors-long";
    iconCard.innerHTML = `
        <div class="selector">
            <label for="title-icon-mode">Icône dans la barre de titre :</label>
            <select id="title-icon-mode">
                <option value="none">Aucune</option>
                <option value="builtin">Icône intégrée</option>
                <option value="custom">Image personnalisée</option>
            </select>
        </div>
        <div class="selector" id="title-icon-builtin-row" style="display:none">
            <label for="title-icon-id">N° d'icône :</label>
            <input type="number" id="title-icon-id" min="1" max="8" step="1" value="1">
        </div>
        <div class="selector" id="title-icon-custom-row" style="display:none">
            <label for="title-icon-file">Image :</label>
            <input type="file" id="title-icon-file" accept="image/*">
        </div>
        <div class="selector"><small id="title-icon-note" style="opacity:.6"></small></div>`;

    osCard.after(sizeCard);
    sizeCard.after(iconCard);

    const $ = (sel) => document.querySelector(sel);
    const onElem = $("#client-size-on"), wElem = $("#client-w"), hElem = $("#client-h");
    const emptyElem = $("#client-empty");
    const modeElem = $("#title-icon-mode"), idElem = $("#title-icon-id"), fileElem = $("#title-icon-file");
    const builtinRow = $("#title-icon-builtin-row"), customRow = $("#title-icon-custom-row");
    const noteElem = $("#title-icon-note");
    let customSrc = null; // data URL de l'image choisie (gardée en mémoire seulement)

    function clamp(v, min, max) {
        v = Math.round(Number(v));
        if (!isFinite(v)) v = min;
        return Math.min(max, Math.max(min, v));
    }

    // ---------- Etat de l'interface ----------
    function refresh() {
        // "Intérieur vide" impose une taille de fenêtre
        if (emptyElem.checked) onElem.checked = true;
        onElem.disabled = emptyElem.checked;
        wElem.disabled = hElem.disabled = !onElem.checked;

        const unsupported = NO_TITLE_ICON.includes(osSelect.value);
        modeElem.disabled = unsupported;
        if (unsupported) modeElem.value = "none";
        builtinRow.style.display = modeElem.value == "builtin" ? "" : "none";
        customRow.style.display = modeElem.value == "custom" ? "" : "none";
        noteElem.textContent = unsupported
            ? "Indisponible pour Windows 1.0, 3.0 et 3.1 (pas d'icône dans la barre de titre)."
            : "L'icône est réduite à 16×16 px.";

        const iconInput = $("#icon");
        if (iconInput && iconInput.max) idElem.max = iconInput.max;
    }

    // ---------- Valeurs lues par createError ----------
    window.getClientSize = function () {
        if (!onElem.checked) return null;
        return { w: clamp(wElem.value, MIN_W, MAX), h: clamp(hElem.value, MIN_H, MAX) };
    };

    window.getTitleIcon = function () {
        if (NO_TITLE_ICON.includes(osSelect.value)) return null;
        if (modeElem.value == "builtin") {
            return { type: "builtin", id: clamp(idElem.value, 1, Number(idElem.max) || 8) };
        }
        if (modeElem.value == "custom" && customSrc) return { type: "custom", src: customSrc };
        return null;
    };

    // ---------- Sauvegarde / restauration ----------
    function save() {
        try {
            localStorage.setItem(STORE_KEY, JSON.stringify({
                on: onElem.checked, w: wElem.value, h: hElem.value,
                empty: emptyElem.checked, mode: modeElem.value, id: idElem.value
            }));
        } catch (e) { /* stockage indisponible */ }
    }

    try {
        const bak = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
        if (bak) {
            onElem.checked = !!bak.on;
            wElem.value = bak.w;
            hElem.value = bak.h;
            emptyElem.checked = !!bak.empty;
            modeElem.value = bak.mode == "custom" ? "none" : (bak.mode || "none"); // l'image perso n'est pas sauvegardée
            idElem.value = bak.id || 1;
        }
    } catch (e) { /* sauvegarde corrompue */ }
    refresh();

    for (const el of [onElem, emptyElem, modeElem]) {
        el.addEventListener("change", () => { refresh(); save(); });
    }
    for (const el of [wElem, hElem]) {
        el.addEventListener("change", () => {
            el.value = clamp(el.value, el === wElem ? MIN_W : MIN_H, MAX);
            save();
        });
    }
    idElem.addEventListener("change", () => { idElem.value = clamp(idElem.value, 1, Number(idElem.max) || 8); save(); });
    osSelect.addEventListener("change", () => setTimeout(refresh, 0)); // après la mise à jour de icon.max par ui.js

    fileElem.addEventListener("change", () => {
        const file = fileElem.files && fileElem.files[0];
        if (!file) { customSrc = null; return; }
        const reader = new FileReader();
        reader.onload = () => { customSrc = reader.result; };
        reader.readAsDataURL(file);
    });

    // ---------- Branchement sur createError ----------
    // ui.js appelle createError(...) avec 11 arguments ; on ajoute :
    //   [11] clientSize  [12] titleIcon  [13] emptyClient
    const originalCreateError = window.createError;
    window.createError = function (...args) {
        args[11] = window.getClientSize();
        args[12] = window.getTitleIcon();
        args[13] = emptyElem.checked;
        return originalCreateError.apply(this, args);
    };
})();
