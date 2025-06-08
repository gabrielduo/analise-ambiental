/**
 * ============================================
 * Arquivo: togglePanels.js
 * -------------------------------------------
 * Este script gerencia a exibição e atualização de informações relacionadas à qualidade do ar, com foco nas partículas MP2.5, MP10 e PTS.
 * O código permite a alternância entre as informações de cada tipo de partícula e exibe dados dinâmicos baseados nas classificações de qualidade do ar.
 * 
 * Funções principais:
 * - `getIqArAndClassification`: Obtém os textos relacionados ao IQAr e classificação de qualidade do ar de um elemento.
 * - `showMp25`: Exibe informações relacionadas às partículas MP2.5.
 * - `showMp10`: Exibe informações relacionadas às partículas MP10.
 * - `showPts`: Exibe informações sobre as partículas PTS.
 * 
 * O código inclui:
 * - Alternância entre a visibilidade de diferentes seções de informações.
 * - Cálculo da quantidade de partículas e atualização da cor e forma com base na classificação de qualidade do ar.
 * - Exibição dinâmica de informações de significado com base na classificação.
 * ============================================
 */

document.addEventListener("DOMContentLoaded", function() {
  // Inicializa contadores de partículas
  window.numParticles_MP25 = 0;  // Contador de partículas MP2.5
  window.numParticles_MP10 = 0;  // Contador de partículas MP10

  // Botões para alternar entre os tipos de partículas
  const btnMp25 = document.getElementById("btn-mp2_5");
  const btnMp10 = document.getElementById("btn-mp10");
  const btnPts  = document.getElementById("btn-pts");

  // Containers de informações básicas para cada tipo de partícula
  const basicInfoMp25 = document.getElementById("basic-info-mp2_5");
  const basicInfoMp10 = document.getElementById("basic-info-mp10");
  const basicInfoPts  = document.getElementById("basic-info-pts");

  // Mapeamento de significados de classificação
  const meaningMap = {
    BOA: {
      text: "Sem sintomas. Atende às especificações da OMS e padrões finais do Conama.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    },
    MODERADA: {
      text: "Pessoas de grupos sensíveis podem apresentar sintomas como tosse seca e cansaço. A população, em geral, não é afetada.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    },
    RUIM: {
      text: "Toda a população pode apresentar sintomas como tosse seca, cansaço, ardor nos olhos, nariz e garganta. Pessoas de grupos sensíveis podem apresentar efeitos mais sérios na saúde.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    },
    "MUITO RUIM": {
      text: "Aumento significativo de sintomas respiratórios, podendo agravar condições cardíacas e pulmonares crônicas.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    },
    PÉSSIMA: {
      text: "Risco muito alto à saúde de toda a população. Evitar atividades ao ar livre e permanecer em ambientes protegidos.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    }
  };

  /**
   * @param {HTMLElement} element - Elemento HTML que contém as informações de IQAr e classificação.
   * @returns {Object} - Objeto contendo:
   *   - `iqarText` (String): Texto extraído referente ao IQAr.
   *   - `classificationText` (String): Texto extraído referente à classificação de qualidade do ar.
   * 
   * Função que extrai as informações de IQAr e classificação a partir dos parágrafos do elemento.
   */
  function getIqArAndClassification(element) {
    const paragraphs = element.querySelectorAll("p");
    let iqarText = "";
    let classificationText = "";
    paragraphs.forEach((p) => {
      const text = p.textContent.trim();
      if (text.startsWith("IQAr:")) {
        iqarText = text.replace("IQAr:", "").trim();
      } else if (text.startsWith("Classificação:")) {
        classificationText = text.replace("Classificação:", "").trim();
      }
    });
    return { iqarText, classificationText };
  }

  /**
   * Exibe as informações relacionadas às partículas MP2.5.
   * Ajusta a visibilidade das seções e atualiza os dados de partículas com base na classificação.
   * Atualiza os botões e exibe o texto de significado com base na classificação da qualidade do ar.
   * 
   * @returns {void}
   */
  function showMp25() {
    // Ajusta visibilidade das seções
    basicInfoMp25.classList.remove("hidden"); basicInfoMp25.classList.add("visible");
    basicInfoMp10.classList.remove("visible"); basicInfoMp10.classList.add("hidden");
    basicInfoPts.classList.remove("visible");  basicInfoPts.classList.add("hidden");

    // Atualiza botões
    btnMp25.classList.add("selected");
    btnMp10.classList.remove("selected");
    btnPts.classList.remove("selected");

    // Lógica de partículas para MP2.5
    const { iqarText, classificationText } = getIqArAndClassification(basicInfoMp25);
    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      window.showClassificationBar(false);
      window.numParticles_MP25 = 4;
      window.mp25Color = "#808080";
      window.particleShape = "sphereInsufficient";
    } else {
      window.showClassificationBar(true);
      window.positionClassificationArrow(classificationText);
      window.numParticles_MP25 = window.getNumParticles(classificationText);
      window.mp25Color = window.getColorForClassification(classificationText);
      window.particleShape = "sphere";
    }
    if (typeof window.updateParticles === "function") {
      window.updateParticles(window.numParticles_MP25);
    }

    // Atualiza o texto de significado
    const meaningContainer = document.getElementById("classification-meaning");
    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      meaningContainer.innerHTML = "";
    } else {
      const info25 = meaningMap[classificationText];
      meaningContainer.innerHTML = `
        <p>${info25.text}</p>
        <span class="meaning-source">Fonte: ${info25.source}</span>
      `;
    }
  }

  /**
   * Exibe as informações relacionadas às partículas MP10.
   * Ajusta a visibilidade das seções e atualiza os dados de partículas com base na classificação.
   * Atualiza os botões e exibe o texto de significado com base na classificação da qualidade do ar.
   * 
   * @returns {void}
   */
  function showMp10() {
    // Ajusta visibilidade das seções
    basicInfoMp25.classList.remove("visible"); basicInfoMp25.classList.add("hidden");
    basicInfoMp10.classList.remove("hidden");  basicInfoMp10.classList.add("visible");
    basicInfoPts.classList.remove("visible");  basicInfoPts.classList.add("hidden");

    // Atualiza botões
    btnMp25.classList.remove("selected");
    btnMp10.classList.add("selected");
    btnPts.classList.remove("selected");

    // Lógica de partículas para MP10
    const { iqarText, classificationText } = getIqArAndClassification(basicInfoMp10);
    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      window.showClassificationBar(false);
      window.numParticles_MP10 = 4;
      window.mp10Color = "#808080";
      window.particleShape = "squareInsufficient";
    } else {
      window.showClassificationBar(true);
      window.positionClassificationArrow(classificationText);
      window.numParticles_MP10 = window.getNumParticles(classificationText);
      window.mp10Color = window.getColorForClassification(classificationText);
      window.particleShape = "square";
    }
    if (typeof window.updateParticles === "function") {
      window.updateParticles(window.numParticles_MP10);
    }

    // Atualiza o texto de significado
    const meaningContainer = document.getElementById("classification-meaning");
    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      meaningContainer.innerHTML = "";
    } else {
      const info10 = meaningMap[classificationText];
      meaningContainer.innerHTML = `
        <p>${info10.text}</p>
        <span class="meaning-source">Fonte: ${info10.source}</span>
      `;
    }
  }

  /**
   * Exibe as informações relacionadas às partículas PTS.
   * Ajusta a visibilidade das seções e atualiza os dados de partículas com base na média das últimas 24h.
   * Atualiza os botões e limpa o texto de significado.
   * 
   * @returns {void}
   */
  function showPts() {
    // Ajusta visibilidade das seções
    basicInfoMp25.classList.remove("visible"); basicInfoMp25.classList.add("hidden");
    basicInfoMp10.classList.remove("visible"); basicInfoMp10.classList.add("hidden");
    basicInfoPts.classList.remove("hidden");  basicInfoPts.classList.add("visible");

    // Atualiza botões
    btnMp25.classList.remove("selected");
    btnMp10.classList.remove("selected");
    btnPts.classList.add("selected");

    // Lógica de partículas para PTS
    window.showClassificationBar(false);
    const paragraphs = basicInfoPts.querySelectorAll("p");
    let mediaHoraria = "";
    paragraphs.forEach((p) => {
      const text = p.textContent.trim();
      if (text.startsWith("Média das últimas 24h:")) {
        mediaHoraria = text.replace("Média das últimas 24h:", "").trim();
      }
    });
    if (!mediaHoraria || mediaHoraria.toLowerCase().includes("não há registros suficientes") || mediaHoraria === "--") {
      window.numParticles = 4;
      window.particleShape = "ptsInsufficient";
    } else {
      const countMP25 = (window.mp25Color && window.mp25Color !== "#808080") ? window.numParticles_MP25 : 0;
      const countMP10 = (window.mp10Color && window.mp10Color !== "#808080") ? window.numParticles_MP10 : 0;
      window.numParticles = countMP25 + countMP10 + 10;
      window.particleShape = "pts";
    }
    if (typeof window.updateParticles === "function") {
      window.updateParticles(window.numParticles);
    }

    // Limpa o texto de significado
    document.getElementById("classification-meaning").innerHTML = "";
  }

  // Conecta os eventos aos botões
  if (btnMp25) btnMp25.addEventListener("click", showMp25);
  if (btnMp10) btnMp10.addEventListener("click", showMp10);
  if (btnPts)  btnPts.addEventListener("click", showPts);

  // Inicializa as cores e exibe PTS por padrão
  (function initClassificationColors() {
    showMp25();
    showMp10();
    showPts();
  })();

  showPts();  // Exibe PTS inicialmente
});
