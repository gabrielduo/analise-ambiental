/**
 * statsOverlay.js — navegação limpa para "Estatísticas" (sem reload)
 * - Evita submit quando o clique vem dos triggers de Estatísticas
 * - Reutiliza o gatilho nativo (#estatisticas-trigger) para abrir a view
 * - Fallback: oculta outras views e mostra Estatísticas
 * - Faz um resize do Plotly ao final para evitar "pulos"
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("classification-form");

  // Triggers que levam para Estatísticas (ajuste ids se precisar)
  const triggers = [
    document.getElementById("stats-trigger"),       // menu lateral
    document.getElementById("btn-estatisticas"),    // botão do cartão
    // NÃO inclua aqui o próprio #estatisticas-trigger, ele já está ligado ao handler original
  ].filter(Boolean);

  const internalTrigger = document.getElementById("estatisticas-trigger");

  // Helpers de views (usados só no fallback)
  const getStatsView = () => document.getElementById("inline-estatisticas-view");
  const getIqarView  = () => document.getElementById("inline-iqar-view");
  const getMetView   = () => document.getElementById("inline-meteorologia-view");
  const getGuideView = () => document.getElementById("inline-guide-view");

  function openStatsNaturally() {
    // 1) Preferência: acionar o mesmo handler que já funciona na sua app
    if (internalTrigger) {
      internalTrigger.click();
      return true;
    }
    // 2) Alternativas comuns (se existirem na sua app)
    if (typeof window.switchView === "function") { window.switchView("estatisticas"); return true; }
    if (typeof window.navigateTo === "function") { window.navigateTo("estatisticas"); return true; }

    // 3) Fallback: só troca classes (não recarrega nada)
    const stats = getStatsView();
    if (stats) {
      [getIqarView(), getMetView(), getGuideView()].forEach(v => v && v.classList.add("hidden"));
      stats.classList.remove("hidden");
      document.documentElement.classList.remove("quality-mode");
      try { localStorage.setItem("view", "estatisticas"); } catch {}
      return true;
    }
    return false;
  }

  function resizePlotlySoon() {
    if (!window.Plotly) return;
    requestAnimationFrame(() => {
      setTimeout(() => {
        document.querySelectorAll(".js-plotly-plot").forEach(div => {
          try { window.Plotly.Plots.resize(div); } catch {}
        });
      }, 50);
    });
  }

  // Evita que os triggers virem "submit" quando estiverem dentro de <form>
  triggers.forEach(el => {
    if (el.tagName === "BUTTON" && !el.getAttribute("type")) {
      el.setAttribute("type", "button");
    }
  });

  // Cancela apenas o submit que venha logo após o clique em Estatísticas
  let suppressNextSubmit = false;
  if (form) {
    form.addEventListener("submit", (e) => {
      if (suppressNextSubmit) {
        e.preventDefault();
        e.stopImmediatePropagation();
        suppressNextSubmit = false;
      }
    }, true); // capture para pegar antes de outros handlers
  }

  // Handler principal dos triggers externos (menu lateral / botão do cartão)
  function onStatsClick(e) {
    // Se o trigger estiver dentro do form, evitamos o submit/reload
    if (form && e.currentTarget.closest("form") === form) {
      suppressNextSubmit = true;
      e.preventDefault();
      e.stopImmediatePropagation();
    }
    // Abre Estatísticas pelo caminho nativo; se não houver, usa fallback
    openStatsNaturally();
    resizePlotlySoon();
  }

  // Conecta o handler (sem bloquear o #estatisticas-trigger nativo)
  triggers.forEach(el => el.addEventListener("click", onStatsClick, true));

  // Se a página abrir com view "estatísticas" salva, garante que está visível
  if (localStorage.getItem("view") === "estatisticas") {
    openStatsNaturally();
    resizePlotlySoon();
  }
});
