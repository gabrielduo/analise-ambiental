// Arquivo: togglePanels.js

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
      text: "Toda a população pode apresentar agravamento dos sintomas como tosse seca, cansaço, ardor nos olhos, nariz e garganta e ainda falta de ar e respiração ofegante. Efeitos ainda mais graves à saúde de grupos sensíveis.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    },
    PÉSSIMA: {
      text: "	Toda a população pode apresentar sérios riscos de manifestações de doenças respiratórias e cardiovasculares. Aumento de mortes prematuras em pessoas de grupos sensíveis.",
      source: "Resolução CONAMA/OMS N° 506/2024"
    }
  };

  /**
   * Extrai IQAr e classificação de um painel info-panel.
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
   * Ajusta a opacidade dos segmentos da barra de classificação.
   * Só o segmento que casa com a classificação fica opacity=1; os outros 0.3.
   */
  function updateClassificationBarOpacity(classification) {
    const cls = classification
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-');
    document.querySelectorAll('#classification-bar .classification-segment')
      .forEach(seg => {
        seg.style.opacity = seg.classList.contains(cls) ? '1' : '0.3';
      });
  }

  /**
   * Exibe as informações relacionadas às partículas MP2.5.
   */
  function showMp25() {
    // Visibilidade de seções
    basicInfoMp25.classList.replace("hidden", "visible");
    basicInfoMp10.classList.replace("visible", "hidden");
    basicInfoPts.classList.replace("visible", "hidden");

    // Atualiza botões
    btnMp25.classList.add("selected");
    btnMp10.classList.remove("selected");
    btnPts.classList.remove("selected");

    const { iqarText, classificationText } = getIqArAndClassification(basicInfoMp25);

    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      window.showClassificationBar(false);
      window.numParticles_MP25 = 4;
      window.mp25Color = "#808080";
      window.particleShape = "sphereInsufficient";
    } else {
      window.showClassificationBar(true);
      window.positionClassificationArrow(classificationText);
      updateClassificationBarOpacity(classificationText);
      window.numParticles_MP25 = window.getNumParticles(classificationText);
      window.mp25Color = window.getColorForClassification(classificationText);
      window.particleShape = "sphere";
    }

    if (typeof window.updateParticles === "function") {
      window.updateParticles(window.numParticles_MP25);
    }

    // Texto de significado
    const meaningContainer = document.getElementById("classification-meaning");
    if (!classificationText) {
      meaningContainer.innerHTML = "";
    } else {
      const info = meaningMap[classificationText];
      meaningContainer.innerHTML = `
        <p>${info.text}</p>
        <span class="meaning-source">Fonte: ${info.source}</span>
      `;
    }
  }

  /**
   * Exibe as informações relacionadas às partículas MP10.
   */
  function showMp10() {
    basicInfoMp25.classList.replace("visible", "hidden");
    basicInfoMp10.classList.replace("hidden", "visible");
    basicInfoPts.classList.replace("visible", "hidden");

    btnMp25.classList.remove("selected");
    btnMp10.classList.add("selected");
    btnPts.classList.remove("selected");

    const { iqarText, classificationText } = getIqArAndClassification(basicInfoMp10);

    if (!iqarText || iqarText.toLowerCase().includes("não há registros suficientes") || !classificationText) {
      window.showClassificationBar(false);
      window.numParticles_MP10 = 4;
      window.mp10Color = "#808080";
      window.particleShape = "squareInsufficient";
    } else {
      window.showClassificationBar(true);
      window.positionClassificationArrow(classificationText);
      updateClassificationBarOpacity(classificationText);
      window.numParticles_MP10 = window.getNumParticles(classificationText);
      window.mp10Color = window.getColorForClassification(classificationText);
      window.particleShape = "square";
    }

    if (typeof window.updateParticles === "function") {
      window.updateParticles(window.numParticles_MP10);
    }

    const meaningContainer = document.getElementById("classification-meaning");
    if (!classificationText) {
      meaningContainer.innerHTML = "";
    } else {
      const info = meaningMap[classificationText];
      meaningContainer.innerHTML = `
        <p>${info.text}</p>
        <span class="meaning-source">Fonte: ${info.source}</span>
      `;
    }
  }

  /**
   * Exibe as informações relacionadas às partículas PTS.
   */
  function showPts() {
    basicInfoMp25.classList.replace("visible", "hidden");
    basicInfoMp10.classList.replace("visible", "hidden");
    basicInfoPts.classList.replace("hidden", "visible");

    btnMp25.classList.remove("selected");
    btnMp10.classList.remove("selected");
    btnPts.classList.add("selected");

    // PTS não usa barra de classificação
    window.showClassificationBar(false);

    // Lógica de PTS
    let mediaHoraria = "";
    basicInfoPts.querySelectorAll("p").forEach(p => {
      if (p.textContent.trim().startsWith("Média das últimas 24h:")) {
        mediaHoraria = p.textContent.split(":")[1].trim();
      }
    });
    if (!mediaHoraria || mediaHoraria.toLowerCase().includes("não há registros suficientes")) {
      window.numParticles = 4;
      window.particleShape = "ptsInsufficient";
    } else {
      const count25 = window.mp25Color !== "#808080" ? window.numParticles_MP25 : 0;
      const count10 = window.mp10Color !== "#808080" ? window.numParticles_MP10 : 0;
      window.numParticles = count25 + count10 + 10;
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

  // Inicializa exibindo MP2.5, depois MP10, depois PTS
  showMp25();
  showMp10();
  showPts();
});
