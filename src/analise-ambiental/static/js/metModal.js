/**
 * ============================================
 * Arquivo: metModal.js
 * -------------------------------------------
 * Provisório - Futuramente vou implementar todo o html adaptado em arquivos apropriados.
 * 
 * Este script gerencia as interações do modal de dados meteorológicos e as funções 
 * auxiliares relacionadas à coleta e exibição de dados de precipitação, umidade, 
 * vento e temperatura. Além disso, ele lida com a atualização dinâmica das informações 
 * meteorológicas exibidas, com base em uma seleção de data e hora.
 * 
 * O código inclui:
 * - Obtenção das imagens associadas aos valores de precipitação e umidade
 * - Criação de opções de horas em um seletor
 * - Atualização do painel de vento
 * - Requisição AJAX para obter dados meteorológicos
 * - Funções de visualização e interação com a interface
 * ============================================
 */

/**
 * @description Função para obter a imagem correspondente ao valor de precipitação.
 * A imagem muda com base nos valores de precipitação, como "nuvem-0" para baixa precipitação,
 * "nuvem-80" para alta precipitação, etc.
 *
 * @param {string|number} value - Valor de precipitação (em mm) para determinar a imagem.
 * @returns {string} Caminho da imagem correspondente à precipitação.
 */
function getPrecipImage(value) {
  const v = parseFloat(value) || 0;
  if (v >= 0 && v <= 5)    return "/static/images/nuvem-0.webp";
  if (v >= 6 && v <= 15)   return "/static/images/nuvem-20.webp";
  if (v >= 16 && v <= 49)  return "/static/images/nuvem-60.webp";
  if (v >= 50 && v <= 100) return "/static/images/nuvem-80.webp";
  return "/static/images/nuvem-80.webp";
}

/**
 * @description Função para obter a imagem correspondente ao valor de umidade.
 * A imagem muda com base nos valores de umidade, como "planta-boa" para alta umidade,
 * "planta-pessima" para baixa umidade, etc.
 *
 * @param {string|number} value - Valor de umidade relativa do ar (em %) para determinar a imagem.
 * @returns {string} Caminho da imagem correspondente à umidade.
 */
function getUmidadeImage(value) {
  const v = parseFloat(value) || 0;
  if (v >= 50 && v <= 100) return "/static/images/planta-boa.webp";
  if (v >= 36 && v <= 49)  return "/static/images/planta-moderado.webp";
  if (v >= 30 && v <= 35)  return "/static/images/planta-ruim.webp";
  if (v < 30)              return "/static/images/planta-pessima.webp";
  return "/static/images/planta-boa.webp";
}

/**
 * @description Gera as opções de hora para o seletor de horário, com base nas horas do dia (0 a 23).
 * Utiliza o valor da hora padrão para definir a opção selecionada no seletor.
 *
 * @param {string} defaultHour - Hora padrão a ser marcada como selecionada no seletor de horas.
 * @returns {string} As opções de hora em formato HTML para serem inseridas no seletor.
 */
function buildHourOptions(defaultHour) {
  let options = "";
  for (let h = 0; h < 24; h++) {
    const val = String(h).padStart(2, "0");
    let selected = (defaultHour === val) ? "selected" : "";
    options += `<option value="${val}" ${selected}>${val}</option>`;
  }
  return options;
}

/**
 * @description Atualiza o painel de vento exibido na interface, alterando a direção e a velocidade do vento,
 * e também atualizando o valor exibido no termômetro.
 * 
 * @param {number} direcao - Direção do vento em graus (0-360).
 * @param {number} velocidade - Velocidade do vento em metros por segundo (m/s).
 */
function atualizarPainelVento(direcao, velocidade) {
  const ventContainer = document.querySelector('.vento-container');
  ventContainer.innerHTML = `
    <div class="compass" id="wind-compass">
      <svg viewBox="0 0 331 331" xmlns="http://www.w3.org/2000/svg">
        <!-- risquinhos e letras -->
        <g fill="none" fill-rule="evenodd" opacity=".4">
        // O código a seguir gera 120 linhas (representando os pontos cardeais e as subdivisões da rosa dos ventos) e as rotaciona no círculo.
        ${[...Array(120)] // Cria um array de 120 elementos.
          .map((_, i) => { // Mapeia sobre o array, onde "_" é o valor do elemento (não usado) e "i" é o índice (de 0 a 119).
            const ang = i * 3; // Define o ângulo de cada linha, começando de 0 e aumentando 3 graus para cada iteração (total de 360 graus).
            
            // Se o ângulo for múltiplo de 30 (pontos principais da rosa dos ventos: N, NE, L, SE, etc.), faz o traço mais grosso.
            const isMajor = ang % 30 === 0;
            
            // Define o comprimento da linha. Todas têm o mesmo comprimento fixo de 20.
            const len = 20;
            
            // Se for um ponto cardinal (como N, NE, etc.), a linha terá uma espessura maior (2). Caso contrário, será mais fina (1).
            const stroke = isMajor ? 2 : 1;
            
            // Gera o SVG <path> para desenhar cada linha da rosa dos ventos.
            // O <path> desenha uma linha com a coordenada inicial (M165.5,11.5) e a coordenada final (M165.5, 11.5 + len),
            // e a linha é rotacionada conforme o ângulo calculado.
            return `
              <path stroke="#fff" stroke-width="${stroke}"
                    d="M165.5,11.5 L165.5,${11.5 + len}" // Define a linha a ser desenhada no SVG
                    transform="rotate(${ang} 165.5 165.5)"/>`; // A linha é rotacionada em torno do ponto central (165.5, 165.5).
          })
          .join('')} // Junta todos os <path> gerados em uma string para serem inseridos no SVG.
          <g fill="#fff" font-family="Arial-BoldMT, Arial" font-size="28" font-weight="bold">
            <text x="165.5" y="65"  text-anchor="middle">N</text>
            <text x="278"   y="173" text-anchor="middle">E</text>
            <text x="165.5" y="285" text-anchor="middle">S</text>
            <text x="60"    y="173" text-anchor="middle">W</text>
          </g>
        </g>

        <!-- aqui o <g> da seta atualizado -->
        <g id="arrowSVG" class="will-transform" transform="rotate(0 165.5 165.5)">
          <!-- ponta -->
          <polygon points="165.5,15 156,48 175,48" fill="#fff"/>
          <!-- trecho dianteiro: agora até y=120 em vez de 130 -->
          <line x1="165.5" y1="48"  x2="165.5" y2="120" stroke="#fff" stroke-width="4"/>
          <!-- trecho traseiro: mantendo o início em y=220 -->
          <line x1="165.5" y1="220" x2="165.5" y2="291.5" stroke="#fff" stroke-width="4"/>
          <!-- círculo traseiro -->
          <circle cx="165.5" cy="303.5" r="12" fill="none" stroke="#fff" stroke-width="4"/>
        </g>
      </svg>

      <div class="compass-content">
        <span id="wind-speed-value">${velocidade.toFixed(1)}</span>
        <span class="unit">m/s</span>
      </div>
    </div>
  `;
  // rotação e atualização de valor seguem iguais...
  const arrow = document.getElementById("arrowSVG");
  if (arrow) arrow.setAttribute("transform", `rotate(${direcao} 165.5 165.5)`);
  const speedEl = document.getElementById("wind-speed-value");
  if (speedEl) speedEl.textContent = velocidade.toFixed(1);
}

/**
 * @description Atualiza os dados meteorológicos a partir do modal, obtendo 
 * a data e a hora selecionadas pelo usuário e fazendo a requisição para 
 * obter as informações correspondentes.
 * Caso os valores de data e hora não estejam presentes, a função é interrompida.
 */
function updateMeteorologiaFromModal() {
  const meteorologiaContainer = document.getElementById("inline-meteorologia-data-view");
  if (meteorologiaContainer && meteorologiaContainer.classList.contains("hidden")) return;

  var dateVal = document.getElementById("input_date").value;
  var hourVal = document.getElementById("input_hour").value;

  if (!dateVal || !hourVal) return;
  console.log("Atualizando meteorologia com data:", dateVal, "hora:", hourVal);
  fetchMeteorologia(dateVal, hourVal);
}

/**
 * @description Faz uma requisição AJAX para obter os dados meteorológicos do servidor.
 * Utiliza o método POST para enviar os parâmetros de data e hora ao backend, 
 * e exibe os resultados ou mensagens de erro na interface do usuário.
 *
 * @param {string} dateVal - A data selecionada pelo usuário no formato yyyy-mm-dd.
 * @param {string} hourVal - A hora selecionada pelo usuário no formato HH.
 */
function fetchMeteorologia(dateVal, hourVal) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/meteorologia", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

  xhr.onreadystatechange = function () {
    // Verifica se a requisição foi completada
    if (xhr.readyState === 4) {
      // Obtém o elemento da página onde as informações meteorológicas serão exibidas
      var infoDiv = document.getElementById("meteorologia-info");
  
      // Verifica se a requisição foi bem-sucedida (status 200)
      if (xhr.status === 200) {
        try {
          // Converte a resposta da requisição (xhr.responseText) para um objeto JSON
          var response = JSON.parse(xhr.responseText);
          console.log("Resposta da meteorologia:", response);
  
          // Verifica se existe um erro na resposta (caso o servidor tenha retornado um erro)
          if (response.error) {
            // Se houver um erro, muda a cor de fundo do contêiner do mapa e exibe a mensagem de erro
            document.querySelector(".map-container").style.backgroundColor = "#272727";
            infoDiv.innerHTML = `<p class="met-error-message">${response.error}</p>`;
          } 
          // Verifica se a resposta contém "Temperatura" com valor "n" (indicando que não há dados meteorológicos)
          else if (response["Temperatura"] === "n") {
            // Se não houver dados, muda a cor de fundo e exibe uma mensagem de erro
            document.querySelector(".map-container").style.backgroundColor = "#272727";
            infoDiv.innerHTML = `<p class="met-error-message">Não foram encontrados registros meteorológicos para esse período.</p>`;
          } 
          // Caso a resposta contenha dados válidos
          else {
            // Restaura a cor de fundo do contêiner do mapa
            document.querySelector(".map-container").style.backgroundColor = "";
  
            // Converte os valores da resposta para números (caso o valor seja inválido, usa 0)
            let umidadeValor = parseFloat(response["Umidade Relativa"]) || 0;
            let precipValor = parseFloat(response["Precipitação Pluviométrica"]) || 0;
            let precipImageFile = getPrecipImage(precipValor); // Obtém a imagem de precipitação correspondente
            let umidadeImageFile = getUmidadeImage(umidadeValor); // Obtém a imagem de umidade correspondente
            let direcaoValor = parseFloat(response["Direção Escalar do Vento"]) || 0;
            let velocidadeValor = parseFloat(response["Velocidade Escalar do Vento"]) || 0;
            let temperaturaValor = parseFloat(response["Temperatura"]) || 0;
            let pressaoValor = parseFloat(response["Pressão Atmosférica"]) || 0;
  
            // Calcula a porcentagem da temperatura com base em um intervalo de 0 a 45°C
            const tMin = 0, tMax = 45;
            const tPerc = Math.min(Math.max((temperaturaValor - tMin) / (tMax - tMin) * 100, 0), 100);
  
            // Determina a classe de precipitação (se não houver precipitação, é classificado como "norain")
            const chuvaClass = (precipImageFile === "/static/images/nuvem-0.webp") ? "norain" : "rain-medium";

            infoDiv.innerHTML = 
        `<div class="meteorologia-data-grid">

          <!-- CARTÃO 1: Precipitação e Umidade -->
          <div class="met-block">
            <div class="left-column">
              <div class="precip-section">
                <div class="met-label-top">Precipitação Pluviométrica</div>
                <div class="met-value-top">${precipValor} mm</div>
              </div>
              <div class="umidade-section">
                <div class="met-label-bottom umidade-relativa-label">Umidade Relativa</div>
                <div class="met-value-bottom umidade-relativa-valor">${umidadeValor}%</div>
              </div>
            </div>
            <div class="center-section">
              <div class="met-center-box chuva ${chuvaClass}"> 
                <img class="precip-img" src="${precipImageFile}" alt="Nuvem - Precipitação" />
                <img class="umidade-img" src="${umidadeImageFile}" alt="Planta - Umidade" />
                <div class="rain-container">
                  <span class="rain-drop" style="left: 10%; animation-delay: 0s;"></span>
                  <span class="rain-drop" style="left: 30%; animation-delay: 0.3s;"></span>
                  <span class="rain-drop" style="left: 50%; animation-delay: 0.6s;"></span>
                  <span class="rain-drop" style="left: 70%; animation-delay: 0.1s;"></span>
                  <span class="rain-drop" style="left: 90%; animation-delay: 0.4s;"></span>
                </div>
                <div class="met-dual-scale">
                  <div class="horizontal-base"></div>
                  <div class="vertical-divider"></div>
                  <div class="vertical-container humidity-container">
                    <div class="column humidity-column">
                      <div class="column-tip"></div>
                    </div>
                  </div>
                  <div class="vertical-container precipitation-container">
                    <div class="column precipitation-column">
                      <div class="column-tip"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- CARTÃO 2: Vento -->
          <div class="met-block">
            <div class="precip-section">
              <div class="met-label-top">Direção do Vento</div>
              <div class="met-value-top">${direcaoValor}°</div>
            </div>
            <div class="center-section">
              <div class="met-center-box vento-container">
                <div class="vento-arrow"></div>
                <!-- SVG fixo já está no HTML -->
              </div>
            </div>
            <div class="umidade-section">
              <div class="met-label-bottom">Velocidade do Vento</div>
              <div class="met-value-bottom">${velocidadeValor} m/s</div>
            </div>
          </div>

          <!-- CARTÃO 3: Temperatura -->
          <div class="met-block">
            <div class="precip-section">
              <div class="met-label-top temperatura-label">Temperatura</div>
              <div class="met-value-top temperatura-valor">${temperaturaValor}°C</div>
            </div>
            <div class="center-section">
              <div class="met-center-box temperatura">
                <div id="termometer">
                  <div id="graduations"></div>
                  <div id="temperature" data-value="${temperaturaValor}°C" style="height: ${tPerc}%;">
                    <span class="temp-label"></span>             
                  </div>
                  <div class="scale"></div>
                </div>
              </div>
            </div>
          </div>
        </div>`;

        
      atualizarPainelVento(direcaoValor, velocidadeValor);

      infoDiv.insertAdjacentHTML('beforeend', `
        <div id="meaning-precip" class="met-meaning-text">
          <p>
            Precipitação pluviométrica é a quantidade de água que cai na forma de chuva, 
            expressa em milímetros acumulados. Valores baixos (até 5 mm) indicam 
            precipitação leve, enquanto acima de 50 mm podem causar alagamentos e erosão.
          </p>
          <span class="met-meaning-source">
            Fonte: INMET – Glossário Meteorológico
          </span>
        </div>

        <div id="meaning-umid" class="met-meaning-text">
          <p>
            Umidade relativa do ar é a razão entre a quantidade de vapor d’água presente 
            no ar e a máxima que o ar pode conter à mesma temperatura. Valores abaixo 
            de 30 % podem causar ressecamento das mucosas, acima de 80 % favorecem 
            sensação de abafamento.
          </p>
          <span class="met-meaning-source">
            Fonte: INMET – Glossário Meteorológico
          </span>
        </div>

        <div id="meaning-vento" class="met-meaning-text">
          <p>
            Velocidade escalar do vento mede a rapidez do ar em direção horizontal, em 
            metros por segundo. Ventos acima de 10 m/s são considerados fortes e podem 
            derrubar galhos e aumentar a sensação de frio.
          </p>
          <span class="met-meaning-source">
            Fonte: INMET – Glossário Meteorológico
          </span>
        </div>

        <div id="meaning-temp" class="met-meaning-text">
          <p>
            Temperatura do ar expressa o grau de calor ou frio ambiente, em °C. 
            Temperaturas acima de 30 °C podem causar desconforto térmico, insolação e 
            agravar problemas cardiovasculares.
          </p>
          <span class="met-meaning-source">
            Fonte: INMET – Glossário Meteorológico
          </span>
        </div>
      `); 

      }
        } catch (e) {
          // Se ocorrer um erro ao processar a resposta, exibe uma mensagem de erro
          document.querySelector(".map-container").style.backgroundColor = "#272727";
          document.getElementById("inline-meteorologia-view").style.height = "880px";
          infoDiv.innerHTML = `<p class="met-error-message">Erro ao processar a resposta.</p>`;
          console.error("Erro de parsing:", e); // Log do erro para depuração
        }
        } else {
        // Se o status da requisição não for 200 (indica erro na requisição), exibe uma mensagem de erro
        document.querySelector(".map-container").style.backgroundColor = "#272727";
        document.getElementById("inline-meteorologia-view").style.height = "880px";
        infoDiv.innerHTML = `<p class="met-error-message">Não foram encontrados registros meteorológicos para esse período.</p>`;
      }
    }
  };
  var params = "input_date=" + encodeURIComponent(dateVal) +
               "&input_hour=" + encodeURIComponent(hourVal);
  xhr.send(params);
}

/**
 * @description Adiciona a rosa dos ventos à visualização de vento, com os pontos cardeais 
 * (N, NE, L, SE, S, SO, O, NO) dispostos de acordo com a posição no círculo.
 */
function adicionarRosaDosVentos() {
  const container = document.querySelector('.vento-container');
  if (!container || container.querySelector('.cardinal')) return;

  const centerX = 170;
  const centerY = 170;
  const radius = 160;

  const pontos = [
    { nome: 'N',  ang: 270 },
    { nome: 'NE', ang: 315 },
    { nome: 'L',  ang: 0   },
    { nome: 'SE', ang: 45  },
    { nome: 'S',  ang: 90  },
    { nome: 'SO', ang: 135 },
    { nome: 'O',  ang: 180 },
    { nome: 'NO', ang: 225 }
  ];

  pontos.forEach(p => {
    const angleRad = (p.ang * Math.PI) / 180;
    const x = centerX + radius * Math.cos(angleRad);
    const y = centerY + radius * Math.sin(angleRad);

    const el = document.createElement('span');
    el.className = 'cardinal';
    el.textContent = p.nome;
    el.style.position = 'absolute';
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    el.style.transform = 'translate(-50%, -50%)';
    el.style.fontSize = '16px';
    el.style.color = '#ddd';
    el.style.fontWeight = 'bold';
    el.style.pointerEvents = 'none';
    el.style.zIndex = 2;

    container.appendChild(el);
  });
}

/**
 * @description Expor a função global que abre a visualização de meteorologia no modo inline.
 */
function openMeteorologiaInlineView() {
  var inlineContainer = document.getElementById("inline-meteorologia-data-view");
  var mainDate = document.getElementById("input_date")?.value;
  var mainHour = document.getElementById("input_hour")?.value;
  if (!mainDate || !mainHour) return;
  fetchMeteorologia(mainDate, mainHour);
}
window.openMeteorologiaInlineView = openMeteorologiaInlineView;
