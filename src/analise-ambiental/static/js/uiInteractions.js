/**
 * ===========================================
 * Arquivo: uiInteractions.js
 * -------------------------------------------
 * Este arquivo gerencia as interações de UI para os botões de estatísticas,
 * qualidade do ar, meteorologia, e navegação do mapa. Também controla a exibição
 * de conteúdo dinâmico, como gráficos e informações meteorológicas.
 * 
 * Ele inclui as funcionalidades para:
 * - Alternar entre os modos de exibição (qualidade do ar, meteorologia, estatísticas)
 * - Exibir ou esconder elementos do mapa conforme as interações do usuário
 * - Controlar os sub-botões de exibição do gráfico e gradiente nas estatísticas.
 * 
 * O código é executado após o DOM estar pronto e responde a interações de navegação.
 * ===========================================
 */

/**
 * @description Gerencia as interações com os botões de estatísticas e gráficos,
 * alternando entre modos de exibição de gráfico, gradiente e exibição de valores mínimos,
 * máximos e médias nas estatísticas.
 */
document.addEventListener("DOMContentLoaded", () => {
    const btnG = document.getElementById("btn-estatisticas-graph"); // Botão de gráfico
    const btnD = document.getElementById("btn-estatisticas-gradient"); // Botão de gradiente
    const plot = document.getElementById("estatisticas-plot"); // Elemento de gráfico
    const grad = document.getElementById("estatisticas-gradient"); // Elemento de gradiente
    const btns = document.querySelector(".estatisticas-buttons"); // Contêiner dos botões
    const statsForm = document.getElementById("stats-form"); // Formulário de estatísticas
    const container = document.querySelector(".estatisticas-content"); // Conteúdo de estatísticas
  
    /**
     * @description Cria dinamicamente o contêiner para os sub-botões do gráfico de gradiente.
     * @param {boolean} show - Define se o botão do gráfico ou do gradiente deve ser mostrado.
     */
    const subBtnContainer = document.createElement("div");
    subBtnContainer.id = "gradient-sub-buttons";
    subBtnContainer.style.display = "none";
    subBtnContainer.style.gap = "8px";
    subBtnContainer.style.zIndex = "10";
    grad.prepend(subBtnContainer);
  
    subBtnContainer.innerHTML = `
      <button id="btn-gradient-media" class="toggle-btn">Média</button>
      <button id="btn-gradient-max" class="toggle-btn">Máximo</button>
      <button id="btn-gradient-min" class="toggle-btn">Mínimo</button>
    `;
  
    // Imagens correspondentes para cada tipo de visualização do gráfico
    const imgMedia = document.querySelector(".estatisticas-gradient-img.media");
    const imgMax = document.querySelector(".estatisticas-gradient-img.max");
    const imgMin = document.querySelector(".estatisticas-gradient-img.min");
  
    // Botões de interação para as visualizações
    const btnMedia = document.getElementById("btn-gradient-media");
    const btnMax = document.getElementById("btn-gradient-max");
    const btnMin = document.getElementById("btn-gradient-min");
  
    if (container) container.style.minHeight = "";
  
    // Inicializa o estado de exibição do gráfico
    btns.classList.remove("gradient-mode");
    if (statsForm) statsForm.classList.remove("hidden");
    subBtnContainer.style.display = "none";
  
    /**
     * @description Alterna para o modo de exibição de gráfico, escondendo o gradiente.
     * @param {Event} e - Evento de clique no botão de gráfico.
     */
    btnG.addEventListener("click", e => {
      e.preventDefault();
      if (container) container.style.minHeight = "";
      btnG.classList.add("active");
      btnD.classList.remove("active");
      plot.classList.remove("hidden");
      grad.classList.add("hidden");
      btns.classList.remove("gradient-mode");
      if (statsForm) statsForm.classList.remove("hidden");
      subBtnContainer.style.display = "none";
    });
  
    /**
     * @description Alterna para o modo de exibição de gradiente, escondendo o gráfico.
     * @param {Event} e - Evento de clique no botão de gradiente.
     */
    btnD.addEventListener("click", e => {
      e.preventDefault();
      if (container && plot) {
        container.style.minHeight = plot.offsetHeight + "px";
      }
      btnD.classList.add("active");
      btnG.classList.remove("active");
      plot.classList.add("hidden");
      grad.classList.remove("hidden");
      btns.classList.add("gradient-mode");
      if (statsForm) statsForm.classList.add("hidden");
      subBtnContainer.style.display = "flex";
      // Ativa a visualização "Média" por padrão
      btnMedia.click();
    });
  
    /**
     * @description Alterna a visualização para "Média".
     * @param {Event} e - Evento de clique no botão de média.
     */
    btnMedia.addEventListener("click", e => {
      e.preventDefault();
      btnMedia.classList.add("active");
      btnMax.classList.remove("active");
      btnMin.classList.remove("active");
      imgMedia.style.display = "block";
      imgMax.style.display = "none";
      imgMin.style.display = "none";
    });
  
    /**
     * @description Alterna a visualização para "Máximo".
     * @param {Event} e - Evento de clique no botão de máximo.
     */
    btnMax.addEventListener("click", e => {
      e.preventDefault();
      btnMax.classList.add("active");
      btnMedia.classList.remove("active");
      btnMin.classList.remove("active");
      imgMax.style.display = "block";
      imgMedia.style.display = "none";
      imgMin.style.display = "none";
    });
  
    /**
     * @description Alterna a visualização para "Mínimo".
     * @param {Event} e - Evento de clique no botão de mínimo.
     */
    btnMin.addEventListener("click", e => {
      e.preventDefault();
      btnMin.classList.add("active");
      btnMedia.classList.remove("active");
      btnMax.classList.remove("active");
      imgMin.style.display = "block";
      imgMedia.style.display = "none";
      imgMax.style.display = "none";
    });
  });
  
  /**
   * @description Gerencia a navegação entre as visualizações de qualidade do ar, meteorologia 
   * e estatísticas, controlando a visibilidade dos elementos do mapa e alterando a exibição 
   * das informações conforme as interações do usuário.
   */
  document.addEventListener("DOMContentLoaded", () => {
    const $ = id => document.getElementById(id); // Função auxiliar para pegar elementos pelo ID
    const mapTrigger = $("map-trigger"); // Botão de volta para o mapa
    const btnQualidade = $("btn-qualidade-ar"); // Botão para a visualização de qualidade do ar
    const btnMet = $("btn-meteorologia"); // Botão para a visualização de meteorologia
    const btnEstatisticas = $("btn-estatisticas"); // Botão para a visualização de estatísticas
    const locIcon = $("location-icon-img"); // Ícone do local
    const mapContainer = document.querySelector(".map-container"); // Contêiner do mapa
    const sphereView = $("inline-sphere-view"); // Visualização da esfera
    const meteoView = $("inline-meteorologia-data-view"); // Visualização de dados meteorológicos
    const statsView = $("inline-estatisticas-view"); // Visualização de estatísticas
  
    /**
     * @description Alterna a visibilidade dos elementos no mapa.
     * @param {boolean} show - Se true, mostra os elementos do mapa; caso contrário, oculta.
     */
    function toggleMapElements(show) {
      mapContainer
        .querySelectorAll(".map-image, .hotspot")
        .forEach(el => el.classList.toggle("hidden", !show));
    }
  
    /**
     * @description Define o ícone de localização conforme a chave fornecida.
     * @param {string} srcKey - Chave para o ícone do local.
     */
    function setLocationIcon(srcKey) {
      if (locIcon) locIcon.src = locIcon.dataset[srcKey];
    }
  
    /**
     * @description Abre a visualização de qualidade do ar.
     */
    function openQualityView() {
      localStorage.setItem("view", "quality");
      document.documentElement
        .classList.add("quality-mode");
      document.documentElement
        .classList.remove("meteorologia-dados-mode");
      setLocationIcon("qualitySrc");
      toggleMapElements(false);
  
      if (meteoView) meteoView.classList.add("hidden");
      if (statsView) statsView.classList.add("hidden");
      if (sphereView) sphereView.classList.remove("hidden");
  
      if (typeof window.showSphereModal === "function") {
        window.showSphereModal();
        const modal = $("sphere-modal");
        if (modal) modal.style.display = "none";
      }
    }
  
    /**
     * @description Abre a visualização de meteorologia.
     */
    function openMeteorologiaView() {
      localStorage.setItem("view", "meteorologia-dados");
      document.documentElement
        .classList.add("meteorologia-dados-mode");
      document.documentElement
        .classList.remove("quality-mode");
      setLocationIcon("meteorologiaSrc");
      toggleMapElements(false);
  
      if (sphereView) sphereView.classList.add("hidden");
      if (statsView) statsView.classList.add("hidden");
      if (meteoView) meteoView.classList.remove("hidden");
  
      if (typeof window.openMeteorologiaInlineView === "function") {
        window.openMeteorologiaInlineView();
      }
    }
  
    /**
     * @description Abre a visualização de estatísticas.
     */
    function openEstatisticasView() {
      localStorage.setItem("view", "estatisticas");
      document.documentElement
        .classList.add("estatisticas-mode");
      document.documentElement
        .classList.remove("quality-mode", "meteorologia-dados-mode");
      setLocationIcon("estatisticasSrc");
      toggleMapElements(false);
  
      if (sphereView) sphereView.classList.add("hidden");
      if (meteoView) meteoView.classList.add("hidden");
      if (statsView) statsView.classList.remove("hidden");
    }
  
    /**
     * @description Retorna para o mapa e esconde todas as outras visualizações.
     */
    function backToMap() {
      localStorage.removeItem("view");
      document.documentElement
        .classList.remove("quality-mode", "meteorologia-dados-mode", "estatisticas-mode");
      setLocationIcon("mapSrc");
      toggleMapElements(true);
  
      if (sphereView) sphereView.classList.add("hidden");
      if (meteoView) meteoView.classList.add("hidden");
      if (statsView) statsView.classList.add("hidden");
    }
  
    // Liga os botões para abrir as diferentes visualizações
    mapTrigger && (mapTrigger.onclick = e => { e.preventDefault(); backToMap(); });
    btnQualidade && (btnQualidade.onclick = e => { e.preventDefault(); openQualityView(); });
    btnMet && (btnMet.onclick = e => { e.preventDefault(); openMeteorologiaView(); });
  
    // Mudança de visualização para as estatísticas
    btnEstatisticas && (btnEstatisticas.onclick = e => {
      e.preventDefault();
      openEstatisticasView();
  
      // Força o selector para MP10 e dispara o change -> submit
      const metricSelect = document.getElementById("metric");
      if (metricSelect) {
        metricSelect.value = "mp10";
        metricSelect.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  
    // "Voltar ao Mapa" interno
    document.querySelectorAll(".back-to-map")
      .forEach(btn => btn.addEventListener("click", e => {
        e.preventDefault();
        backToMap();
      }));
  
    // Restaura a visualização após o reload
    const saved = localStorage.getItem("view");
    if (saved === "quality") openQualityView();
    else if (saved === "meteorologia-dados") openMeteorologiaView();
    else if (saved === "estatisticas") openEstatisticasView();
  });
  
/**
 * Manipula o evento DOMContentLoaded para configurar a interação com o mapa e os hotspots.
 * Este evento adiciona os eventos de hover, click e mouseout nos hotspots, e também 
 * controla o comportamento do mapa, como mudar a imagem e exibir as visualizações de dados.
 * 
 * @event DOMContentLoaded
 * @param {Event} event - O evento que é disparado quando o DOM foi completamente carregado.
 */
document.addEventListener("DOMContentLoaded", function() {
  const mainMap = document.getElementById("main-map");  // Mapa principal
  if (!mainMap) return;

  // Guarda o caminho original (mapa3.jpg) para restaurar no mouseout
  const defaultSrc = mainMap.src;
  
  // Seleciona todas as divs com classe "hotspot"
  const hotspots = document.querySelectorAll(".hotspot");

  // Botões globais das visualizações
  const btnMet       = document.getElementById("btn-meteorologia");
  const btnQualidade = document.getElementById("btn-qualidade-ar");
  const stationSelect = document.getElementById("station");

  /**
   * @description Adiciona o comportamento de hover nos hotspots, alterando a imagem do mapa.
   *              Ao passar o mouse, a imagem do mapa é alterada para a imagem associada ao hotspot.
   * 
   * @param {Event} e - O evento de mouseover disparado quando o mouse entra no hotspot.
   */
  hotspots.forEach((spot) => {
    // Quando o mouse entrar, troca a imagem
    spot.addEventListener("mouseover", function() {
      const newImage = spot.getAttribute("data-image");
      mainMap.src = newImage;
    });
    
    // Quando o mouse sair, volta para a imagem original
    spot.addEventListener("mouseout", function() {
      mainMap.src = defaultSrc;
    });

    /**
     * @description Ao clicar no hotspot, dispara as ações relacionadas a qualidade do ar ou meteorologia.
     *              Dependendo do tipo de dado do hotspot, a ação de clique é direcionada.
     *
     * @param {Event} e - O evento de clique disparado ao clicar no hotspot.
     */
    spot.addEventListener("click", function(e) {
      e.preventDefault();
      const action = spot.dataset.action;

      // Ação para mostrar dados de meteorologia
      if (action === "meteorologia") {
        btnMet?.click();
      }
      // Ação para mostrar dados de qualidade do ar
      else if (action === "qualidade") {
        const est = spot.dataset.station;
        if (stationSelect && est) {
          stationSelect.value = est;
          // Dispara evento de 'change' para atualizar resultados
          stationSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
        btnQualidade?.click();
      }
    });
  });
});