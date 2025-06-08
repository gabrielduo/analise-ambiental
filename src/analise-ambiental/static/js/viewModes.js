/**
 * ============================================
 * Arquivo: viewModes.js
 * -------------------------------------------
 * Este script gerencia a alternância entre diferentes modos de visualização 
 * na página: "guide-mode", "iqar-mode", e "meteorologia-mode". Cada modo exibe uma visualização 
 * específica na interface, como uma guia de ajuda, a visualização de dados
 * relacionados ao IQAr (Índice de Qualidade do Ar), e a visualização de meteorologia.
 * 
 * Funções principais:
 *  - Alternar entre modos de visualização (Guia, IQAr e Meteorologia)
 *  - Gerenciar a visibilidade de elementos na interface
 *  - Controlar o comportamento dos botões e interações com o mapa
 * ============================================
 */

document.addEventListener("DOMContentLoaded", function() {
    // Obtém os elementos necessários para os três modos
    const guideTrigger    = document.getElementById("guide-trigger");    // Botão que abre o modo guia
    const iqarTrigger     = document.getElementById("iqar-trigger");     // Botão que abre o modo IQAr
    const meteorologiaTrigger = document.getElementById("meteorologia-trigger"); // Botão que abre o modo meteorologia
    
    const guideView       = document.getElementById("inline-guide-view"); // Visão do guia
    const iqarView        = document.getElementById("inline-iqar-view");   // Visão do IQAr
    const meteorologiaView = document.getElementById("inline-meteorologia-view"); // Visão da meteorologia
    
    const btnBackGuide    = document.getElementById("btn-back-from-guide");  // Botão de voltar do guia
    const btnBackIqar     = document.getElementById("btn-back-from-iqar");   // Botão de voltar do IQAr
    const btnBackMeteorologia = document.getElementById("btn-back-from-meteorologia-view");  // Botão de voltar da meteorologia
    
    const mapTrigger = document.getElementById("map-trigger");  // Botão para voltar ao mapa
  
    /**
     * Limpa todos os modos de visualização e esconde as visualizações inline.
     * Remove as classes de modo e esconde todos os divs de visualização inline.
     *
     * @example
     * // Chama a função para limpar todos os modos e esconder as visualizações
     * clearAll();
     */
    function clearAll() {
      document.documentElement.classList.remove(
        "guide-mode",
        "iqar-mode",
        "meteorologia-mode",
        "quality-mode"
      );
      document.querySelectorAll('#page-content > div[id^="inline-"]')
        .forEach(div => div.classList.add("hidden"));
    }
  
    /**
     * Abre a visualização do guia e ativa o modo "guide".
     *
     * @example
     * // Chama a função para abrir o guia
     * openGuide();
     */
    function openGuide() {
      clearAll();  // Limpa os modos anteriores
      document.documentElement.classList.add("guide-mode");  // Ativa o modo de guia
      guideView.classList.remove("hidden");  // Exibe a visualização do guia
    }
  
    /**
     * Fecha a visualização do guia e desativa o modo "guide".
     *
     * @example
     * // Chama a função para fechar o guia
     * closeGuide();
     */
    function closeGuide() {
      document.documentElement.classList.remove("guide-mode");  // Desativa o modo de guia
      guideView.classList.add("hidden");  // Esconde a visualização do guia
    }
  
    /**
     * Abre a visualização do IQAr e ativa o modo "iqar".
     *
     * @example
     * // Chama a função para abrir o IQAr
     * openIqar();
     */
    function openIqar() {
      clearAll();  // Limpa os modos anteriores
      document.documentElement.classList.add("iqar-mode");  // Ativa o modo IQAr
      iqarView.classList.remove("hidden");  // Exibe a visualização do IQAr
    }
  
    /**
     * Fecha a visualização do IQAr e desativa o modo "iqar".
     *
     * @example
     * // Chama a função para fechar o IQAr
     * closeIqar();
     */
    function closeIqar() {
      document.documentElement.classList.remove("iqar-mode");  // Desativa o modo IQAr
      iqarView.classList.add("hidden");  // Esconde a visualização do IQAr
    }
  
    /**
     * Abre a visualização do modo meteorologia e ativa o modo "meteorologia".
     *
     * @example
     * // Chama a função para abrir o modo meteorologia
     * openMeteorologia();
     */
    function openMeteorologia() {
      clearAll();  // Limpa os modos anteriores
      document.documentElement.classList.add("meteorologia-mode");  // Ativa o modo meteorologia
      meteorologiaView.classList.remove("hidden");  // Exibe a visualização do modo meteorologia
    }
  
    /**
     * Fecha a visualização do modo meteorologia e desativa o modo "meteorologia".
     *
     * @example
     * // Chama a função para fechar o modo meteorologia
     * closeMeteorologia();
     */
    function closeMeteorologia() {
      document.documentElement.classList.remove("meteorologia-mode");  // Desativa o modo meteorologia
      meteorologiaView.classList.add("hidden");  // Esconde a visualização do modo meteorologia
    }
  
    // Adiciona eventos de clique para alternar entre os modos de visualização
    guideTrigger?.addEventListener("click", e => {
      e.preventDefault();
      openGuide();
    });
  
    iqarTrigger?.addEventListener("click", e => {
      e.preventDefault();
      openIqar();
    });
  
    meteorologiaTrigger?.addEventListener("click", e => {
      e.preventDefault();
      openMeteorologia();
    });
  
    // Adiciona eventos de clique para fechar os modos de visualização ao clicar no botão de voltar
    btnBackGuide?.addEventListener("click", e => {
      e.preventDefault();
      closeGuide();
    });
  
    btnBackIqar?.addEventListener("click", e => {
      e.preventDefault();
      closeIqar();
    });
  
    btnBackMeteorologia?.addEventListener("click", e => {
      e.preventDefault();
      closeMeteorologia();
    });
  
    // Fecha o guia, o IQAr ou o modo meteorologia se o mapa for acionado enquanto estiver em qualquer um desses modos
    mapTrigger?.addEventListener("click", e => {
      if (document.documentElement.classList.contains("guide-mode")) {
        e.preventDefault();
        closeGuide();
      }
      if (document.documentElement.classList.contains("iqar-mode")) {
        e.preventDefault();
        closeIqar();
      }
      if (document.documentElement.classList.contains("meteorologia-mode")) {
        e.preventDefault();
        closeMeteorologia();
      }
    });
  });
  