/**
 * ============================================
 * Arquivo: vertical.js
 * -------------------------------------------
 * Este script gerencia a interação com o menu vertical da interface,
 * incluindo a alternância entre diferentes modos de visualização como
 * mapa, IQAr, meteorologia, guia e submenus.
 * 
 * Funções principais:
 *  - Alternar entre modos de visualização (Guia, IQAr, Meteorologia, etc.)
 *  - Gerenciar a visibilidade de elementos na interface
 *  - Controlar o comportamento dos botões e interações com o mapa
 *  - Gerenciar o envio de relatórios de erro
 * ============================================
 */

/**
 * @description Seleciona todos os links/menu-items que terminam em "-trigger" e
 * adiciona um listener de clique para gerenciar a alternância de visualizações.
 * 
 * @event DOMContentLoaded
 * @param {Event} evt - O evento disparado quando o DOM foi completamente carregado.
 */
document.addEventListener('DOMContentLoaded', () => {
  // Seleciona TODOS os triggers que terminem em "-trigger"
  const triggers = document.querySelectorAll(
    '#vertical-menu .menu-section li a[id$="-trigger"]'
  );

  // Para cada link/menu-item, adiciona listener de clique
  triggers.forEach(link => {
    link.addEventListener('click', evt => {
      evt.preventDefault(); // previne o “#” padrão

      // Garante que apenas UM link do menu tenha classe “active” de cada vez 
      triggers.forEach(l => l.classList.remove('active'));
      link.classList.add('active');

      // Chama a view correta ou alterna o submenu 
      if (link.id === 'map-trigger') {
        showMapView();
      } else if (link.id === 'iqar-trigger') {
        showIqarView();
      } else if (link.id === 'meteorologia-trigger') {
        showMeteorologiaView();
      } else if (link.id === 'guide-trigger') {
        showGuideView();
      } else if (link.id === 'file-upload-trigger') {
        // alterna o submenu de "Nova Visualização"
        toggleSubmenu('file-upload-trigger');
      } else if (link.id === 'error-report-trigger') {
        // alterna o submenu de "Relatar um erro"
        toggleSubmenu('error-report-trigger');
      }
    });
  });

  // (3) Se clicar em qualquer botão de "voltar" (guide/ meteorologia/ iqar),
  //      volta o estado do menu para “Mapa”
  const backButtons = [
    'btn-back-from-guide',
    'btn-back-from-meteorologia-view',
    'btn-back-from-iqar'
  ];
  backButtons.forEach(buttonId => {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.addEventListener('click', () => {
      triggers.forEach(l => l.classList.remove('active'));
      const mapLink = document.getElementById('map-trigger');
      if (mapLink) mapLink.classList.add('active');
    });
  });


  // ============================================================
  // Função genérica que recebe um triggerId (ex: 'error-report-trigger')
  // e alterna a classe ".open" no <li class="has-submenu"> pai dele.
  // ============================================================
  /**
   * @description Alterna a visibilidade de um submenu ao clicar no trigger correspondente.
   * 
   * @param {string} triggerId - O ID do trigger que foi clicado (ex: 'error-report-trigger').
   * 
   * @returns {void}
   */
  function toggleSubmenu(triggerId) {
    const link = document.getElementById(triggerId);
    if (!link) return;
    const parentLi = link.closest('li.has-submenu');
    if (!parentLi) return;
    parentLi.classList.toggle('open');
  }

  /**
   * @description Fecha qualquer submenu aberto quando o usuário clicar fora dele.
   * 
   * @event click
   * @param {Event} event - O evento disparado quando o usuário clica fora de um submenu.
   */
  document.addEventListener('click', (event) => {
    // percorre todos os <li class="has-submenu"> para fechar se estiver aberto
    document.querySelectorAll('#vertical-menu .has-submenu').forEach(li => {
      if (li.classList.contains('open') && !li.contains(event.target)) {
        li.classList.remove('open');
      }
    });
  });

  const errorText = document.getElementById('error-text');
  const charCounter = document.getElementById('error-char-counter');
  const errorUploadButton = document.getElementById('error-upload-button');
  const errorUploadInput = document.getElementById('error-upload-input');
  const errorSubmitButton = document.getElementById('error-submit-button');
  const MAX_CHARS = 300;

  /**
   * @description Atualiza o contador de caracteres no formulário de erro e
   * desabilita o botão de envio se o limite de caracteres for excedido.
   * 
   * @returns {void}
   */
  function updateCharCounter() {
    const remaining = MAX_CHARS - (errorText?.value.length || 0);
    if (charCounter) {
      charCounter.textContent = remaining;
      if (remaining < 0) {
        charCounter.classList.add('exceeded');
        errorSubmitButton.disabled = true;
      } else {
        charCounter.classList.remove('exceeded');
        errorSubmitButton.disabled = false;
      }
    }
  }

  // Se houver o textarea, já liga o listener para atualizações
  if (errorText) {
    errorText.addEventListener('input', updateCharCounter);
    updateCharCounter(); // inicializa no carregamento
  }

  // Quando clica em “Selecionar Imagem”
  if (errorUploadButton && errorUploadInput) {
    errorUploadButton.addEventListener('click', (e) => {
      e.preventDefault();
      errorUploadInput.click();
    });

    errorUploadInput.addEventListener('change', () => {
      if (errorUploadInput.files.length > 0) {
        console.log('Imagem selecionada para erro:', errorUploadInput.files[0].name);
      }
    });
  }

  // Quando clica em “Enviar Relatório”
  /**
   * @description Envia o relatório de erro para o servidor, verificando se os limites de caracteres
   * são atendidos e fazendo upload de um arquivo de erro, se necessário.
   * 
   * @event click
   * @param {Event} e - O evento de clique no botão de envio do relatório de erro.
   */
  if (errorSubmitButton && errorText) {
    errorSubmitButton.addEventListener('click', (e) => {
      e.preventDefault();

      // Não deixa enviar se excedeu o número de caracteres
      if (errorText.value.length > MAX_CHARS) {
        alert('O texto excede o limite de 300 caracteres. Reduza o texto.');
        return;
      }

      // Monta FormData e envia via fetch()
      const formData = new FormData();
      formData.append('error_text', errorText.value);
      if (errorUploadInput.files.length > 0) {
        formData.append('error_file', errorUploadInput.files[0]);
      }

      fetch('/report_error', {
        method: 'POST',
        body: formData
      })
      .then(async response => {
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || `Erro ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Erro reportado:', data);
        alert(data.message || 'Erro enviado com sucesso!');

        // Limpa campos e fecha submenu
        errorText.value = '';
        errorUploadInput.value = '';
        updateCharCounter();
        // Fecha o submenu de erro
        const parentLi = document.getElementById('error-report-trigger').closest('li.has-submenu');
        if (parentLi) parentLi.classList.remove('open');
      })
      .catch(err => {
        console.error('Falha ao enviar relatório de erro:', err);
        alert('Falha ao enviar relatório: ' + err.message);
      });
    });
  }
});
