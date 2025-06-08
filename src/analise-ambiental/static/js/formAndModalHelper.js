/**
 * ===========================================
 * Arquivo: formAndModalHelper.js
 * -------------------------------------------
 * Este arquivo gerencia o comportamento de formulários, interações com modais e 
 * eventos relacionados à sobreposição de carregamento (loading overlay).
 * Ele também gerencia o estado de visibilidade dos modais e da interação com o formulário de 
 * classificação da qualidade do ar, bem como eventos relacionados à atualização de dados.
 * 
 * O código é executado quando o DOM está pronto e expõe funções globais para facilitar o uso
 * dessas funcionalidades em outras partes da aplicação.
 * ===========================================
 */

/**
 * @description Gerencia a exibição de uma sobreposição de carregamento (loading overlay) ao 
 * submeter um formulário e armazena o estado da visualização da esfera.
 */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("classification-form"); // Formulário de classificação
    const overlay = document.getElementById("loading-overlay"); // Overlay de carregamento
    const modal = document.getElementById("sphere-modal"); // Modal da esfera
  
    /**
     * @description Exibe a sobreposição de carregamento, se o elemento existir.
     */
    const showOverlay = () => overlay && (overlay.style.display = "flex");
  
    // Ao submeter o formulário manualmente, exibe a sobreposição
    if (form) {
      form.addEventListener("submit", showOverlay);
  
      /**
       * @description Submete o formulário com a sobreposição ativada.
       * Caso a visualização da esfera esteja visível, armazena isso no localStorage
       * para restaurar a interface corretamente após o envio do formulário.
       */
      window.submitWithOverlay = () => {
        if (modal?.style.display === "flex") {
          localStorage.setItem("keepSphereOpen", "true"); // Armazena o estado da esfera no localStorage
        }
        showOverlay(); // Exibe a sobreposição de carregamento
        setTimeout(() => form.submit(), 0); // Submete o formulário com um pequeno atraso para garantir que a sobreposição seja visível
      };
    }
  });
  
  /**
   * @description Função debounce para controlar a frequência de execução de uma função.
   * Usada para evitar que a função seja chamada muitas vezes em um curto intervalo de tempo.
   * 
   * @param {Function} func - A função que será chamada após o debounce.
   * @param {number} wait - O tempo em milissegundos para aguardar antes de chamar a função.
   * @returns {Function} Função debounced.
   */
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait); // Aguarda o tempo especificado antes de chamar a função
    };
  }
  
  /**
   * @description Gerencia os eventos relacionados ao envio de formulários com debounce
   * e interações com os botões de dados meteorológicos e de qualidade do ar.
   */
  document.addEventListener("DOMContentLoaded", function () {
    const inputDate = document.getElementById("input_date"); // Input de data
    const inputHour = document.getElementById("input_hour"); // Input de hora
    const stationSelect = document.getElementById("station"); // Select de estação
    const iqarTrigger = document.getElementById("iqar-trigger"); // Botão de iqar
  
    /**
     * @description Dispara a submissão de dados com base no modo atual (meteorologia ou qualidade do ar).
     */
    function triggerCustomSubmit() {
      // Se estivermos no modo meteorologia, atualiza somente os dados meteorológicos
      if (document.documentElement.classList.contains("meteorologia-dados-mode")) {
        if (typeof updateMeteorologiaFromModal === "function") {
          updateMeteorologiaFromModal(); // Atualiza os dados meteorológicos
        }
      }
      // Se estivermos no modo Qualidade do Ar, executa o comportamento padrão (submit ou similar)
      else if (document.documentElement.classList.contains("quality-mode")) {
        if (typeof window.submitWithOverlay === "function") {
          window.submitWithOverlay(); // Executa o envio do formulário com a sobreposição
        }
      }
      // Se não houver nenhum modo especial, nada é feito (ou um comportamento padrão pode ser definido)
    }
  
    // Aplica debounce de 300ms aos eventos para otimizar as chamadas
    const debouncedSubmit = debounce(triggerCustomSubmit, 300);
  
    // Acompanha as mudanças de data, hora e estação e dispara a função de submit
    if (inputDate) {
      inputDate.addEventListener("change", debouncedSubmit);
    }
    if (inputHour) {
      inputHour.addEventListener("change", debouncedSubmit);
    }
    if (stationSelect) {
      stationSelect.addEventListener("change", debouncedSubmit);
    }
  
    // Mapeia os botões MP2.5 e MP10 para disparar a mesma ação de iqar-trigger
    ["iqar-info-trigger-mp25", "iqar-info-trigger-mp10"].forEach((btnId) => {
      const btn = document.getElementById(btnId);
      if (!btn || !iqarTrigger) return;
  
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        iqarTrigger.click(); // Dispara a ação associada ao botão
      });
    });
  });
  
  /**
   * @description Ao carregar o conteúdo da página, verifica se o modal da esfera 
   * deve ser reaberto, baseado no estado armazenado no localStorage.
   */
  document.addEventListener("DOMContentLoaded", function() {
    if (localStorage.getItem("keepSphereOpen") === "true") {
      localStorage.removeItem("keepSphereOpen"); // Remove a flag após usar
      if (typeof showSphereModal === "function") {
        showSphereModal(); // Reabre o modal da esfera se necessário
      }
    }
  });
  
  /**
   * @description Gerencia o comportamento do modal da esfera, incluindo o fechamento
   * do modal quando um clique fora do conteúdo ou no botão de fechar é detectado.
   */
  document.addEventListener("DOMContentLoaded", function() {
    const sphereModal = document.getElementById("sphere-modal"); // Modal da esfera
    const sphereModalContent = document.getElementById("sphere-modal-content"); // Conteúdo do modal
  
    // Exibe o modal ao clicar fora do conteúdo
    if (sphereModal && sphereModalContent) {
      sphereModal.addEventListener("click", function(e) {
        if (!sphereModalContent.contains(e.target)) {
          sphereModal.style.display = "none"; // Fecha o modal
          document.dispatchEvent(new Event("sphereModalClosed")); // Dispara evento de fechamento
        }
      });
    }
  
    const closeButton = document.getElementById("sphere-modal-close"); // Botão de fechamento
    if (closeButton) {
      closeButton.addEventListener("click", function() {
        sphereModal.style.display = "none"; // Fecha o modal
        document.dispatchEvent(new Event("sphereModalClosed")); // Dispara evento de fechamento
      });
    }
  
    const loadingOverlay = document.getElementById("loading-overlay"); // Overlay de carregamento
    const estatisticasButton = document.getElementById("btn-estatisticas"); // Botão de Estatísticas
    const estatisticasTrigger = document.getElementById("estatisticas-trigger"); // Trigger de Estatísticas
  
    // Controla a exibição do overlay de carregamento antes de mudar para a visualização de Estatísticas
    if (estatisticasButton) {
      estatisticasButton.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation(); // Impede propagação do clique
  
        // Exibe o overlay
        if (loadingOverlay) {
          loadingOverlay.style.display = "flex";
        }
  
        // Simula o clique no trigger de estatísticas após um pequeno delay
        setTimeout(() => {
          if (estatisticasTrigger) {
            estatisticasTrigger.click();
          } else {
            // Caso o trigger não exista, dispara o evento "openEstatisticas"
            document.dispatchEvent(new Event("openEstatisticas"));
          }
  
          // Esconde o overlay após o conteúdo de Estatísticas começar a renderizar
          setTimeout(() => {
            if (loadingOverlay) {
              loadingOverlay.style.display = "none";
            }
          }, 100);
        }, 2000);
      });
    }
  });
  