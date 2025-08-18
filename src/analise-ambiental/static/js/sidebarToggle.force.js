// Sidebar retrátil – seta branca com sombra, hitbox grande
// Esconde "Nova visualização" e "Relatar um erro" quando a barra está retraída.

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const nav = document.getElementById("vertical-menu");
    const content =
      document.getElementById("page-content") ||
      document.querySelector(".body-wrapper") ||
      document.querySelector("main");

    if (!nav || !content) return;

    // ===== ajustes fáceis =====
    const SHIFT_PIXELS   = 110; // quanto o conteúdo anda para a esquerda
    const COLLAPSED_W    = 64;  // largura do menu colapsado
    const HITBOX_W       = 48;  // largura da área de clique
    const HITBOX_H       = 200; // altura da área de clique
    const HITBOX_OFFSETX = 12;  // distância da seta da borda direita do menu
    const KEY            = "sidebarCollapsed";
    // ==========================

    // posição inicial do conteúdo
    const BASE_ML = (() => {
      const n = parseFloat(getComputedStyle(content).marginLeft || "0");
      return Number.isFinite(n) ? n : 0;
    })();

    // estilos
    const style = document.createElement("style");
    style.textContent = `
      html.is-sidebar-collapsed #vertical-menu{ width:${COLLAPSED_W}px !important; }
      /* Esconde textos (mantém ícones) */
      html.is-sidebar-collapsed #vertical-menu #menu-title,
      html.is-sidebar-collapsed #vertical-menu .menu-section h2,
      html.is-sidebar-collapsed #vertical-menu .menu-section ul li span{ display:none !important; }
      html.is-sidebar-collapsed #vertical-menu .menu-section ul li a{ justify-content:center; }

      /* Esconde itens específicos no estado colapsado */
      html.is-sidebar-collapsed #vertical-menu .hide-in-collapsed { display:none !important; }

      #vertical-menu{ overflow:visible; }

      /* Hitbox invisível + seta branca com sombra */
      #vertical-menu .__sb-btn{
        position:absolute;
        top:50%;
        left:100%;
        transform: translate(${HITBOX_OFFSETX}px, -50%);
        width:${HITBOX_W}px; height:${HITBOX_H}px;
        padding:0; margin:0; border:none; background:transparent;
        cursor:pointer; z-index:9999;
        display:flex; align-items:center; justify-content:flex-start; padding-left:6px;
        color:#fff; /* garante currentColor = branco */
      }
      #vertical-menu .__sb-btn svg{
        width:24px; height:24px;
        display:block;
        filter: drop-shadow(0 2px 8px rgba(0,0,0,.55));
        transition: opacity .15s ease;
        pointer-events:none;
      }
      /* força branco mesmo se outro CSS mexer em color */
      #vertical-menu .__sb-btn svg path{ fill:#fff; }

      #vertical-menu .__sb-btn:hover svg{ opacity:.9; }
      html.is-sidebar-collapsed #vertical-menu .__sb-btn svg{ transform: rotate(180deg); }

      #page-content{ transition: margin-left .22s ease; }
    `;
    document.head.appendChild(style);

    // Marca os itens "Nova visualização" e "Relatar um erro" para sumirem quando colapsado
    ["file-upload-trigger", "error-report-trigger"].forEach(id => {
      const a = document.getElementById(id);
      if (a) (a.closest("li") || a).classList.add("hide-in-collapsed");
    });

    // injeta a seta se não existir
    let btn = nav.querySelector(".__sb-btn");
    if (!btn) {
      btn = document.createElement("button");
      btn.className = "__sb-btn";
      btn.type = "button";
      btn.title = "Recolher menu";
      btn.setAttribute("aria-label","Alternar menu lateral");
      btn.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
        </svg>`;
      nav.appendChild(btn);
    }

    function applyMargin(collapsed){
      const ml = collapsed ? Math.max(0, BASE_ML - SHIFT_PIXELS) : BASE_ML;
      content.style.marginLeft = `${ml}px`;
      if (window.Plotly) {
        requestAnimationFrame(()=> {
          document.querySelectorAll(".js-plotly-plot").forEach(div=>{
            try { window.Plotly.Plots.resize(div); } catch {}
          });
        });
      }
    }

    // estado salvo
    const saved = localStorage.getItem(KEY) === "1";
    if (saved) {
      document.documentElement.classList.add("is-sidebar-collapsed");
      btn.title = "Expandir menu";
    }
    applyMargin(saved);

    // toggle
    btn.addEventListener("click", () => {
      const collapsedNow = document.documentElement.classList.toggle("is-sidebar-collapsed");
      localStorage.setItem(KEY, collapsedNow ? "1" : "0");
      btn.title = collapsedNow ? "Expandir menu" : "Recolher menu";
      applyMargin(collapsedNow);
    });
  });
})();
