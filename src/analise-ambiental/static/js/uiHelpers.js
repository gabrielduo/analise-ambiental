/**
 * ===========================================
 * Arquivo: uiHelpers.js
 * -------------------------------------------
 * Este arquivo agrupa funções auxiliares que são utilizadas em diversas
 * funcionalidades da interface, incluindo:
 *  - A classificação da qualidade do ar.
 *  - A interação com o seletor de datas e exibição da data selecionada.
 * ===========================================
 */

/**
 * Função que inicializa as configurações relacionadas à classificação
 * da qualidade do ar. O script permite associar uma classificação 
 * ("BOA", "MODERADA", "RUIM", etc.) a:
 *  - Número de partículas (influencia a visualização da esfera 3D)
 *  - Cor associada à classificação
 *  - Posição vertical percentual da seta indicadora.
 * Essas funções são disponibilizadas globalmente no objeto `window`.
 */
document.addEventListener("DOMContentLoaded", () => {
    // Objeto de configuração com dados para cada classificação
    // p: número de partículas
    // c: cor associada
    // t: posição vertical da seta, em %
    const classificationConfig = {
      BOA:          { p: 10,  c: "#006b3d", t: 0 },
      MODERADA:     { p: 20,  c: "#069c56", t: 20 },
      RUIM:         { p: 40,  c: "#ff980e", t: 40 },
      "MUITO RUIM": { p: 100, c: "#ff681e", t: 60 },
      PÉSSIMA:      { p: 150, c: "#d3212c", t: 80 }
    };
  
    /**
     * Retorna a configuração completa com base na classificação fornecida.
     * Se a classificação não for reconhecida, retorna valores padrão.
     * @param {string} classification - Texto da classificação (ex: "BOA")
     * @returns {object} Objeto com p, c, t
     */
    const getConfig = (classification) => {
      return classificationConfig[classification?.toUpperCase()] || {
        p: 10, c: "#808080", t: 0
      };
    };
  
    /**
     * Retorna o número de partículas conforme a classificação.
     * @param {string} classification
     * @returns {number}
     */
    window.getNumParticles = (classification) => getConfig(classification).p;
  
    /**
     * Retorna a cor associada à classificação.
     * @param {string} classification
     * @returns {string} Código de cor hexadecimal
     */
    window.getColorForClassification = (classification) => getConfig(classification).c;
  
    /**
     * Posiciona a seta de classificação na barra vertical conforme a classificação.
     * @param {string} classification
     */
    window.positionClassificationArrow = (classification) => {
      const arrowElement = document.getElementById("classification-arrow");
      if (arrowElement) {
        const positionPercent = getConfig(classification).t;
        arrowElement.style.top = (positionPercent + 10) + "%"; // +10% para centralizar visualmente
        arrowElement.setAttribute("data-classification", classification); // salva como atributo
      }
    };
  
    /**
     * Controla a visibilidade da barra de classificação.
     * @param {boolean} show - Se true, exibe a barra; se false, oculta.
     */
    window.showClassificationBar = (show) => {
      const barElement = document.getElementById("classification-bar");
      if (barElement) {
        barElement.style.display = show ? "flex" : "none";
      }
    };
  });
  
  /**
   * Função que gerencia a interação com o campo de data.
   * Exibe um input para seleção de data e atualiza o texto exibido
   * com a data selecionada, formatada como "dd/mm/aaaa".
   * Também retorna ao texto padrão "Data: Mais recente" quando necessário.
   */
  document.addEventListener("DOMContentLoaded", () => {
    // Elementos HTML: exibição da data e campo de seleção
    const dateDisplayElement = document.getElementById("date-display");
    const datePickerElement = document.getElementById("date-picker");
  
    // Se algum dos elementos estiver ausente, não executa nada
    if (!dateDisplayElement || !datePickerElement) return;
  
    /**
     * Alterna a visibilidade entre o texto da data e o input de data.
     * @param {boolean} showInput - Se true, exibe o input de data; senão, exibe o texto.
     */
    const toggleDateInputVisibility = (showInput) => {
      dateDisplayElement.style.display = showInput ? "none" : "inline-block";
      datePickerElement.style.display = showInput ? "inline-block" : "none";
    };
  
    /**
     * Atualiza o texto de exibição da data com base no valor selecionado no input.
     * Se não houver valor, exibe "Data: Mais recente".
     */
    const updateDateDisplay = () => {
      const selectedDate = datePickerElement.value; // Formato: yyyy-mm-dd
      dateDisplayElement.textContent = selectedDate
        ? `Data: ${selectedDate.split("-").reverse().join("/")}`
        : "Data: Mais recente";
  
      toggleDateInputVisibility(false); // Oculta o input e exibe o texto novamente
    };
  
    // Evento: ao clicar no texto, mostra o campo de data e foca nele
    dateDisplayElement.onclick = () => {
      toggleDateInputVisibility(true);
      datePickerElement.focus();
    };
  
    // Evento: ao mudar a data ou perder o foco, atualiza o texto exibido
    datePickerElement.onchange = datePickerElement.onblur = updateDateDisplay;
  });
  