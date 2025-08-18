// Carregamento sob demanda dos "Mais detalhes" (MP10 / MP2.5)
// Usa DELEGAÇÃO + CAPTURA para funcionar mesmo que o DOM seja trocado depois.
(function () {
  function toPt(x) {
    if (x === null || x === undefined || Number.isNaN(Number(x))) return "—";
    try { return Number(x).toFixed(2).replace(".", ","); } catch { return String(x); }
  }

  function renderDetails(targetEl, data) {
    if (!targetEl) return;
    if (data.status === "insufficient") {
      targetEl.innerHTML = `<p>Dados insuficientes para calcular os detalhes.</p>`;
      targetEl.classList.remove("hidden");
      return;
    }
    if (data.status !== "ok") {
      targetEl.innerHTML = `<p>Não foi possível carregar os detalhes.</p>`;
      targetEl.classList.remove("hidden");
      return;
    }
    const html = `
      <h4>Detalhes ${data.pollutant.replace("MP", "MP<sub>")}</sub></h4>
      <p>Índice Inicial: ${toPt(data.indice_inicial)} µg/m³</p>
      <p>Índice Final: ${toPt(data.indice_final)} µg/m³</p>
      <p>Concentração Inicial: ${toPt(data.concentracao_inicial)} µg/m³</p>
      <p>Concentração Final: ${toPt(data.concentracao_final)} µg/m³</p>
    `;
    targetEl.innerHTML = html;
    targetEl.classList.remove("hidden");
  }

  function setLoading(targetEl) {
    if (!targetEl) return;
    targetEl.classList.remove("hidden");
    targetEl.innerHTML = `<p>Carregando…</p>`;
  }

  async function fetchDetails(pol, targetSel) {
    const targetEl = document.querySelector(targetSel);
    if (!targetEl) return;

    const inputDate = document.getElementById("input_date")?.value;
    const inputHour = document.getElementById("input_hour")?.value;
    const station   = document.getElementById("station")?.value;

    if (!inputDate || !inputHour || !station) {
      targetEl.innerHTML = `<p>Preencha data, hora e estação.</p>`;
      targetEl.classList.remove("hidden");
      return;
    }

    setLoading(targetEl);

    const fd = new FormData();
    fd.append("input_date", inputDate);
    fd.append("input_hour", inputHour);
    fd.append("station", station);
    fd.append("pollutant", pol);

    try {
      const res = await fetch("/api/detalhes", { method: "POST", body: fd });
      const data = await res.json();
      renderDetails(targetEl, data);
    } catch (e) {
      console.error(e);
      targetEl.innerHTML = `<p>Erro ao carregar detalhes.</p>`;
      targetEl.classList.remove("hidden");
    }
  }

  // Delegação com captura para pegar cliques mesmo que outro script pare a propagação
  document.addEventListener("click", function (ev) {
    const a = ev.target.closest("a.details-load");
    if (!a) return;
    ev.preventDefault();            // não navegar para '#'
    ev.stopPropagation();           // evita que outro handler mexa
    const pol    = a.getAttribute("data-pol");
    const target = a.getAttribute("data-target");
    if (pol && target) fetchDetails(pol, target);
  }, true); // <— CAPTURA
})();
