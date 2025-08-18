/**
 * formAndModalHelper.js — mínimo
 * - Mantém QUALIDADE DO AR via AJAX sem overlay.
 * - Removeu a lógica específica de Estatísticas (overlay/timeout/click),
 *   que agora fica isolada em statsOverlay.js.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("classification-form");
  const overlay = document.getElementById("loading-overlay");
  const modal = document.getElementById("sphere-modal");

  const showOverlay = () => overlay && (overlay.style.display = "flex");

  if (form) {
    form.addEventListener("submit", function (ev) {
      // Em quality-mode, usamos AJAX e não mostramos overlay
      if (document.documentElement.classList.contains("quality-mode")) {
        ev.preventDefault();
        if (typeof window.ajaxSubmitQuality === "function") {
          window.ajaxSubmitQuality();
          return;
        }
      }
      // Fluxos que ainda dependem de reload (outros)
      showOverlay();
    });

    // Compatibilidade para submits tradicionais
    window.submitWithOverlay = () => {
      if (modal?.style.display === "flex") {
        localStorage.setItem("keepSphereOpen", "true");
      }
      showOverlay();
      setTimeout(() => form.submit(), 0);
    };
  }
});

/* ---------- debounce util ---------- */
function debounce(fn, wait) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), wait); };
}

document.addEventListener("DOMContentLoaded", function () {
  const inputDate = document.getElementById("input_date");
  const inputHour = document.getElementById("input_hour");
  const stationSelect = document.getElementById("station");
  const iqarTrigger = document.getElementById("iqar-trigger");

  function triggerCustomSubmit() {
    if (document.documentElement.classList.contains("meteorologia-dados-mode")) {
      if (typeof updateMeteorologiaFromModal === "function") updateMeteorologiaFromModal();
    } else if (document.documentElement.classList.contains("quality-mode")) {
      if (typeof window.ajaxSubmitQuality === "function") window.ajaxSubmitQuality();
    }
  }

  const debouncedSubmit = debounce(triggerCustomSubmit, 300);
  if (inputDate) inputDate.addEventListener("change", debouncedSubmit);
  if (inputHour) inputHour.addEventListener("change", debouncedSubmit);
  if (stationSelect) stationSelect.addEventListener("change", debouncedSubmit);
  if (iqarTrigger) iqarTrigger.addEventListener("click", e => { e.preventDefault(); debouncedSubmit(); });
});

/* =============================
   (já existente) — AJAX da Qualidade do Ar
   ============================= */
(function () {
  function toBR(n) {
    const v = typeof n === "number" ? n : parseFloat(n || 0);
    return isFinite(v) ? v.toFixed(2).replace(".", ",") : "0,00";
  }

  // Helpers da esfera (iguais aos que já vinham nas versões anteriores)
  function getActiveInfoPanel() {
    return (
      document.querySelector(".info-panel.visible") ||
      document.getElementById("basic-info-mp10") ||
      document.getElementById("basic-info-mp2_5") ||
      document.getElementById("basic-info-pts")
    );
  }
  function retriggerActivePollutantByClick() {
    const panel = getActiveInfoPanel();
    if (!panel) return false;
    const id = panel.id;
    const btn =
      document.querySelector(`[data-target="#${id}"]`) ||
      document.querySelector(`[href="#${id}"]`) ||
      document.getElementById(id === "basic-info-mp10" ? "btn-mp10" : id === "basic-info-mp2_5" ? "btn-mp2_5" : "btn-pts");
    if (btn) { btn.click(); return true; }
    return false;
  }
  function fallbackUpdateSphereFromPanel() {
    const panel = getActiveInfoPanel();
    if (!panel) return;
    const pClass = Array.from(panel.querySelectorAll("p")).find(p =>
      p.textContent.trim().toLowerCase().startsWith("classificação:")
    );
    const classText = pClass ? pClass.textContent.replace(/^\s*Classificação:\s*/i, "").trim() : "";
    if (typeof window.positionClassificationArrow === "function") {
      try { window.positionClassificationArrow(classText); } catch {}
    }
    if (typeof window.getNumParticles === "function" && typeof window.updateParticles === "function") {
      try { window.updateParticles(window.getNumParticles(classText)); } catch {}
    }
    if (typeof window.getColorForClassification === "function") {
      try {
        const color = window.getColorForClassification(classText);
        if (typeof window.setParticlesColor === "function") window.setParticlesColor(color);
      } catch {}
    }
  }

  function setPanel(containerId, polData, polName) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const media = polData["Média Horária"] ?? polData["value"] ?? 0.0;
    const iqar  = polData["IQAr"] ?? polData["iqar"] ?? 0.0;
    const cls   = polData["Classificação"] ?? polData["class"] ?? "Indisponível";
    const iini  = polData["Índice Inicial"] ?? polData["I_ini"] ?? 0.0;
    const ifin  = polData["Índice Final"]   ?? polData["I_fin"] ?? 0.0;
    const cini  = polData["Concentração Inicial"] ?? polData["C_ini"] ?? 0.0;
    const cfin  = polData["Concentração Final"]   ?? polData["C_fin"] ?? 0.0;

    const ps = container.querySelectorAll("p");
    if (ps[0]) ps[0].innerHTML = `Média das últimas 24h: ${toBR(media)} µg/m³`;
    if (ps[1]) {
      const info = ps[1].querySelector(".info-button");
      ps[1].innerHTML = `IQAr: ${toBR(iqar)} `;
      if (info) ps[1].appendChild(info);
    }
    if (ps[2]) ps[2].innerHTML = `Classificação: ${cls}`;

    const detailsId = containerId.replace("basic-info", "details");
    const details = document.getElementById(detailsId);
    if (details) {
      details.innerHTML = `
        <h4>Detalhes ${polName}</h4>
        <p>Índice Inicial: ${toBR(iini)} µg/m³</p>
        <p>Índice Final: ${toBR(ifin)} µg/m³</p>
        <p>Concentração Inicial: ${toBR(cini)} µg/m³</p>
        <p>Concentração Final: ${toBR(cfin)} µg/m³</p>
      `;
    }
  }

  async function ajaxSubmitQuality() {
    const form = document.getElementById("classification-form");
    if (!form) return;

    const formData = new FormData(form);

    try {
      const res = await fetch("/classificar/json", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Falha ao consultar IQAr.");
      const data = await res.json();

      if (data["MP2.5"]) setPanel("basic-info-mp2_5", data["MP2.5"], "MP<sub>2,5</sub>");
      if (data["MP10"])  setPanel("basic-info-mp10",  data["MP10"],  "MP<sub>10</sub>");
      if (data["PTS"])   setPanel("basic-info-pts",   data["PTS"],   "PTS");

      // Re-aciona a esfera
      const ok = retriggerActivePollutantByClick();
      if (!ok) fallbackUpdateSphereFromPanel();

    } catch (err) {
      //console.error(err);
      alert(err.message || "Erro ao atualizar qualidade do ar.");
    }
  }

  window.ajaxSubmitQuality = ajaxSubmitQuality;
})();
