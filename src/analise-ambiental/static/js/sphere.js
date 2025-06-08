/**
 * ============================================
 * Arquivo: sphere.js
 * -------------------------------------------
 * Este script gerencia a criação e animação de uma esfera 3D interativa, utilizando a biblioteca Three.js.
 * A cena inclui partículas que representam dados específicos, como MP10, MP2,5 e PTS, e exibe indicadores de forma dinâmica.
 * 
 * O código inclui:
 * - Inicialização da cena 3D com uma esfera e partículas.
 * - Criação de partículas em diferentes formas e cores.
 * - Adição de indicadores de texto (MP10, MP2,5, PTS).
 * - Animação da esfera e movimento das partículas com Perlin noise.
 * - Interação com o usuário para rotação da esfera.
 * - Exibição de um modal com a visualização da esfera.
 * 
 * Funções principais:
 * - `initSphereScene`: Inicializa a cena 3D e configura a esfera e partículas.
 * - `updateParticles`: Atualiza a quantidade e as propriedades das partículas exibidas.
 * - `createTextSprite`: Cria um sprite de texto 3D que é usado como indicador.
 * - `criarParticula`: Cria uma nova partícula com propriedades configuráveis.
 * ============================================
 */

/**
 * Esta função é executada após o carregamento completo do DOM.
 * Inicializa variáveis e configurações para a criação da esfera 3D e suas partículas.
 * @function
 */
document.addEventListener("DOMContentLoaded", function() {
  let sphereInitialized = false;  // Flag para verificar se a esfera foi inicializada
  let particleGroup = null;  // Grupo de partículas a ser adicionado à cena
  let globeGroup = null;  // Grupo que contém a esfera 3D (globo)

  // Tamanhos e propriedades da esfera e partículas
  const PARTICLE_SIZE = 0.12;  // Tamanho das partículas
  const SMALL_PARTICLE_SIZE = 0.08;  // Tamanho das partículas menores
  const sphereRadius = 3.2;  // Raio da esfera
  const sphereSegments = 16;  // Número de segmentos da esfera
  const globeInnerRadius = sphereRadius * 0.9;  // Raio interno da esfera (globo)

  const indicatorOffsetMultiplier = 4.0;  // Fator de deslocamento dos indicadores

  // Variáveis para as partículas de cada indicador
  let mp10TargetParticle = null;  // Partícula alvo para MP10
  let mp10IndicatorLine = null;  // Linha indicadora para MP10
  let mp10IndicatorSprite = null;  // Sprite indicador para MP10

  let mp25TargetParticle = null;  // Partícula alvo para MP2,5
  let mp25IndicatorLine = null;  // Linha indicadora para MP2,5
  let mp25IndicatorSprite = null;  // Sprite indicador para MP2,5

  let ptsTargetParticle = null;  // Partícula alvo para PTS
  let ptsIndicatorLine = null;  // Linha indicadora para PTS
  let ptsIndicatorSprite = null;  // Sprite indicador para PTS

  /**
   * Cria um sprite de texto 3D que será utilizado como indicador.
   * @param {string} message - A mensagem a ser exibida no sprite (ex: "MP10").
   * @param {Object} parameters - Parâmetros de personalização do sprite.
   * @param {string} parameters.fontface - Fonte a ser utilizada (padrão: "Arial").
   * @param {number} parameters.fontsize - Tamanho da fonte (padrão: 16).
   * @returns {THREE.Sprite} O sprite gerado com o texto.
   */
  function createTextSprite(message, parameters) {
    parameters = parameters || {};  // Parâmetros padrões para personalização do texto
    const fontface = parameters.fontface || "Arial";  
    const fontsize = parameters.fontsize || 16;  
    if(message === "MP10") message = "MP₁₀";  
    else if(message === "MP2,5") message = "MP₂,₅";  

    const canvas = document.createElement('canvas');  // Criação do elemento canvas para desenhar o texto
    const context = canvas.getContext('2d');  // Contexto 2D do canvas
    const scaleFactor = 2;  // Fator de escala para melhorar a resolução
    const ratio = window.devicePixelRatio || 1;  // Razão de pixels do dispositivo (para suportar telas de alta densidade)
    context.font = fontsize + "px " + fontface;  // Definir fonte e tamanho do texto
    const metrics = context.measureText(message);  // Medir o comprimento do texto
    const textWidth = metrics.width;  // Largura do texto

    //Fiz isso para ajustar largura e altura do canvas, a versão antiga não funcionava então ficou assim
    canvas.width = textWidth * ratio * scaleFactor;  
    canvas.height = fontsize * ratio * scaleFactor;  

    context.scale(ratio * scaleFactor, ratio * scaleFactor);  // Aplicar escala ao contexto 2D
    context.font = fontsize + "px " + fontface;  // Redefinir fonte após escalonamento

    //Alinhamento do texto
    context.textAlign = "center";  
    context.textBaseline = "middle";  

    context.clearRect(0, 0, canvas.width, canvas.height);  // Limpar o canvas antes de desenhar
    context.fillStyle = "rgba(255,255,255,1.0)";  // Definir cor de preenchimento do texto
    context.fillText(message, canvas.width/(2 * ratio * scaleFactor), canvas.height/(2 * ratio * scaleFactor));  // Desenhar o texto no canvas

    const texture = new THREE.Texture(canvas);  // Criar textura a partir do canvas
    texture.needsUpdate = true;  // Atualizar textura
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true });  // Material para o sprite
    const sprite = new THREE.Sprite(spriteMaterial);  // Criar o sprite
    sprite.scale.set(0.9, 0.5, 2);  // Ajustar o tamanho do sprite
    return sprite;  // Retornar o sprite
  }

  /**
   * Cria uma nova partícula 3D em formato esférico.
   * @param {string} corHex - A cor da partícula em formato hexadecimal (ex: "#ff0000").
   * @param {number} tamanho - O tamanho da partícula.
   * @param {number} [velocidade=0.001] - A velocidade da partícula, que define seu movimento (padrão: 0.001).
   * @returns {THREE.Mesh} A partícula gerada.
   */
  function criarParticula(corHex, tamanho, velocidade = 0.001) {
    const geometry = new THREE.SphereGeometry(tamanho, 8, 8);  // Geometria esférica para a partícula
    const material = new THREE.MeshStandardMaterial({
      color: corHex,  // Cor da partícula
      roughness: 3.2,  // Rugosidade do material
      metalness: 0.0,  // Metalicidade do material
      transparent: true,  // Torna a partícula transparente
      opacity: 0.75  // Define a opacidade
    });
    /*
     * Cálculos de ângulos e posições. Nesse caso, não há necessidade de fazer mudanças, o código utilizado como base
     * foi um tutorial de como utilizar o Three.js, encontrado em:
     * https://www.pentacreation.com/blog/2020/09/200930.html
    */
    const particle = new THREE.Mesh(geometry, material);  
    const theta = Math.acos(2 * Math.random() - 1);  
    const phi = 2 * Math.PI * Math.random();  
    const r = Math.cbrt(Math.random()) * globeInnerRadius;  // Determina a distância radial da partícula
    const x = r * Math.sin(theta) * Math.cos(phi);  
    const y = r * Math.sin(theta) * Math.sin(phi);  
    const z = r * Math.cos(theta);  
    particle.position.set(x, y, z);  // Define a posição da partícula
    particle.userData.velocity = new THREE.Vector3(
      (Math.random() - 0.5) * velocidade,  // Velocidade aleatória no eixo X
      (Math.random() - 0.5) * velocidade,  // Velocidade aleatória no eixo Y
      (Math.random() - 0.5) * velocidade   // Velocidade aleatória no eixo Z
    );
    return particle;  // Retorna a partícula criada
  }
/**
 * Atualiza a quantidade de partículas geradas na cena.
 * Esta função remove as partículas anteriores, recria as partículas com base nas novas configurações e as adiciona ao grupo.
 * Além disso, ela ajusta a criação de partículas e os indicadores conforme o tipo de forma selecionado.
 * @param {number} newCount - O número de partículas a serem criadas.
 */
function updateParticles(newCount) {
  // Verifica se o grupo de partículas e o grupo da esfera existem
  if (!particleGroup || !globeGroup) return;

  // Remove as partículas existentes antes de criar novas
  while (particleGroup.children.length > 0) {
    particleGroup.remove(particleGroup.children[0]);
  }

  // Define o tipo de forma das partículas (padrão é "sphere")
  const shape = window.particleShape || "sphere";
  const particlesCreated = [];

  // Remove os indicadores anteriores da cena
  if (mp10IndicatorLine) globeGroup.remove(mp10IndicatorLine);
  if (mp10IndicatorSprite) globeGroup.remove(mp10IndicatorSprite);
  mp10IndicatorLine = mp10IndicatorSprite = mp10TargetParticle = null;
  if (mp25IndicatorLine) globeGroup.remove(mp25IndicatorLine);
  if (mp25IndicatorSprite) globeGroup.remove(mp25IndicatorSprite);
  mp25IndicatorLine = mp25IndicatorSprite = mp25TargetParticle = null;
  if (ptsIndicatorLine) globeGroup.remove(ptsIndicatorLine);
  if (ptsIndicatorSprite) globeGroup.remove(ptsIndicatorSprite);
  ptsIndicatorLine = ptsIndicatorSprite = ptsTargetParticle = null;

  // Criação de partículas dependendo da forma selecionada
  if (shape !== "pts" && shape !== "ptsInsufficient") {
    let colorHex = 0x808080;  // Cor padrão das partículas
    // Ajusta a cor das partículas conforme o tipo de forma selecionado
    if (shape === "square" || shape === "squareInsufficient")
      colorHex = window.mp10Color ? parseInt(window.mp10Color.slice(1), 16) : 0x69be28;
    else if (shape === "sphere" || shape === "sphereInsufficient")
      colorHex = window.mp25Color ? parseInt(window.mp25Color.slice(1), 16) : 0x3db7e4;

    // Define o tamanho das partículas dependendo da forma selecionada
    const particleSize = (shape === "sphere" || shape === "sphereInsufficient") ? PARTICLE_SIZE * (2/3) : PARTICLE_SIZE;

    // Cria as partículas e as adiciona ao grupo
    for (let i = 0; i < newCount; i++) {
      const particle = criarParticula(colorHex, particleSize);  // Criação de cada partícula
      particleGroup.add(particle);  // Adiciona a partícula ao grupo
      particlesCreated.push(particle);  // Adiciona à lista de partículas criadas
    }

    // Criação do indicador de texto para MP10 ou MP2,5 dependendo da forma
    if ((shape === "square" || shape === "squareInsufficient") && particlesCreated.length > 0) {
      mp10TargetParticle = particlesCreated[0];
      const direction = mp10TargetParticle.position.clone().normalize();
      const labelOffset = direction.multiplyScalar(sphereRadius * 1.1);
      mp10IndicatorSprite = createTextSprite("MP10", { fontsize: 12, fontface: "Arial" });
      mp10IndicatorSprite.position.copy(labelOffset);  // Posiciona o sprite do indicador
      globeGroup.add(mp10IndicatorSprite);  // Adiciona o indicador ao grupo
    } else if ((shape === "sphere" || shape === "sphereInsufficient") && particlesCreated.length > 0) {
      mp25TargetParticle = particlesCreated[0];
      const direction = mp25TargetParticle.position.clone().normalize();
      const labelOffset = direction.multiplyScalar(sphereRadius * 1.1);
      mp25IndicatorSprite = createTextSprite("MP2,5", { fontsize: 12, fontface: "Arial" });
      mp25IndicatorSprite.position.copy(labelOffset);  // Posiciona o sprite do indicador
      globeGroup.add(mp25IndicatorSprite);  // Adiciona o indicador ao grupo
    }

  } else {  // Caso a forma seja "pts" ou "ptsInsufficient"
    if (shape === "ptsInsufficient") {
      // Criação de 4 partículas "insuficientes" no caso de "ptsInsufficient"
      for (let i = 0; i < 4; i++) {
        const particle = criarParticula(0x808080, PARTICLE_SIZE);
        particleGroup.add(particle);  // Adiciona as partículas ao grupo
      }
    } else {
      // Define o número de partículas para MP25 e MP10
      let countMP25 = window.numParticles_MP25 || 10;
      let countMP10 = window.numParticles_MP10 || 10;
      // Verifica se a cor das partículas é "insuficiente" e ajusta o número de partículas
      if (window.mp25Color === "#808080") countMP25 = 0;
      if (window.mp10Color === "#808080") countMP10 = 0;
      const extraCount = 10;  // Partículas extras

      // Criação das partículas para MP2,5
      const colorMP25 = window.mp25Color ? parseInt(window.mp25Color.slice(1), 16) : 0x3db7e4;
      for (let i = 0; i < countMP25; i++) {
        const particle = criarParticula(colorMP25, PARTICLE_SIZE * (2/3));
        particleGroup.add(particle);  // Adiciona as partículas ao grupo
      }

      // Criação das partículas para MP10
      const colorMP10 = window.mp10Color ? parseInt(window.mp10Color.slice(1), 16) : 0x69be28;
      for (let i = 0; i < countMP10; i++) {
        const particle = criarParticula(colorMP10, PARTICLE_SIZE);
        particleGroup.add(particle);  // Adiciona as partículas ao grupo
      }

      // Criação das partículas extras
      for (let i = 0; i < extraCount; i++) {
        const particle = criarParticula(0x8a7c72, PARTICLE_SIZE * 1.2);
        particleGroup.add(particle);  // Adiciona as partículas extras ao grupo
        if (!ptsTargetParticle) ptsTargetParticle = particle;  // Define a partícula de PTS
      }
    }
  }
}

// Função para atualizar as partículas exibidas na cena
/**
 * Atualiza as partículas na cena, removendo as existentes e criando novas com base no tipo de forma e contagem especificados.
 * Também atualiza os indicadores de partículas (MP10, MP2,5, PTS) dependendo da forma selecionada.
 * @param {number} newCount - O número de partículas a serem criadas.
 */
window.updateParticles = updateParticles;

/**
 * Inicializa a cena 3D da esfera, criando os elementos necessários para exibição (esfera, partículas, luzes, etc.).
 * Esta função configura a câmera, a iluminação e o ambiente, além de definir a animação para a visualização.
 * @function
 */
function initSphereScene() {
  // Recupera o contêiner da esfera e o oculta inicialmente
  const sphereContainer = document.getElementById('sphere-container');
  sphereContainer.style.visibility = "hidden";
  sphereContainer.style.opacity = "0";

  // Define as dimensões da exibição
  const displayWidth = 240;  // Largura 
  const displayHeight = 240;  // Altura 
  const highResFactor = 2;  // Fator de alta resolução para melhorar a qualidade visual
  const renderWidth = displayWidth * highResFactor;  // Largura do renderizado
  const renderHeight = displayHeight * highResFactor;  // Altura do renderizado

  // Cria uma nova cena
  const scene = new THREE.Scene();
  const aspect = renderWidth / renderHeight;  // Aspecto da câmera
  const d = 4.5;  // Distância da câmera
  const camera = new THREE.OrthographicCamera(-d * aspect, d * aspect, d, -d, 1, 1000);  // Câmera ortográfica
  camera.position.set(5, 2, 5);  // Define a posição da câmera
  camera.lookAt(0, 0, 0);  // Faz a câmera "olhar para o centro" da cena

  // Cria o renderizador WebGL
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);  // Cor de fundo da cena
  renderer.setPixelRatio(window.devicePixelRatio);  // Define a razão de pixels do dispositivo
  renderer.setSize(renderWidth, renderHeight);  // Define o tamanho da tela de renderização
  sphereContainer.appendChild(renderer.domElement);  // Adiciona o elemento de renderização ao contêiner

  // Adiciona luz ambiente à cena
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);  // Luz ambiente suave
  scene.add(ambientLight);

  // Adiciona luz direcional à cena
  const dirLight = new THREE.DirectionalLight(0xffffff, 1);  // Luz direcional
  dirLight.position.set(10, 8, -1);  // Define a posição da luz
  dirLight.castShadow = false;  // Desativa sombras para a luz direcional
  scene.add(dirLight);

  // Cria um grupo externo para a cena (caixa de limites)
  const outerGroup = new THREE.Group();
  const boxGeometry = new THREE.BoxGeometry(6, 6, 3);  // Geometria da caixa
  const edgesGeometry = new THREE.EdgesGeometry(boxGeometry);  // Geometria das bordas da caixa
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0xDFDFDF,  // Cor das bordas
    linewidth: 0,  // Largura da linha (não visível)
    opacity: 0.00,  // Opacidade da linha
    transparent: true  // Transparente
  });
  const wireframe = new THREE.LineSegments(edgesGeometry, lineMaterial);  // Criação das bordas
  outerGroup.add(wireframe);  // Adiciona o wireframe ao grupo
  outerGroup.rotation.set(-0.11, 0.35, 0.1);  // Define a rotação do grupo (opcional)
  //scene.add(outerGroup);  // Adiciona ao cenário (comentado)

  // Material da esfera com transparência e wireframe
  const globeMaterial = new THREE.MeshStandardMaterial({
    color: 0xffffff,  // Cor da esfera
    transparent: true,  // Transparência ativada
    wireframe: true,  // Ativa o wireframe para mostrar as bordas
    opacity: 0.1  // Opacidade da esfera
  });

  // Geometria da esfera (Icosaedro)
  const globeGeometry = new THREE.IcosahedronGeometry(sphereRadius, 5);
  const globeMesh = new THREE.Mesh(globeGeometry, globeMaterial);  // Criação da esfera
  globeMesh.originalPositions = globeMesh.geometry.attributes.position.array.slice();  // Armazena as posições originais dos vértices

  // Cria um grupo para a esfera e adiciona à cena
  globeGroup = new THREE.Group();
  globeGroup.add(globeMesh);
  scene.add(globeGroup);

  // Grupo de partículas a ser adicionado à esfera
  particleGroup = new THREE.Group();
  globeGroup.add(particleGroup);

  // Variáveis de controle de arraste da esfera
  let isDragging = false;
  let previousMouseX = 0;
  // Adiciona evento para controle de arraste da esfera
  renderer.domElement.addEventListener('mousedown', (e) => {
    isDragging = true;
    previousMouseX = e.clientX;
  });
  renderer.domElement.addEventListener('mousemove', (e) => {
    if (isDragging) {
      const deltaX = e.clientX - previousMouseX;
      globeGroup.rotation.y += deltaX * 0.002;  // Rotaciona a esfera no eixo Y
      previousMouseX = e.clientX;
    }
  });
  renderer.domElement.addEventListener('mouseup', () => { isDragging = false; });  // Desativa o arraste
  renderer.domElement.addEventListener('mouseleave', () => { isDragging = false; });  // Desativa o arraste se o mouse sair da área

  /**
   * Função de animação para atualizar a cena, incluindo movimento de partículas e animação da esfera.
   * @function
   */
  function animate() {
    requestAnimationFrame(animate);  // Requisição para a próxima animação

    // Animação dos vértices da esfera usando Perlin noise para criar um efeito de "movimento"
    /*
     * Aqui eu utilizo uma referência disponibilizada no github disponibilizada pela seguinte página:
     * https://raw.githubusercontent.com/josephg/noisejs/master/perlin.js
     * O código foi reaproveitado e a única coisa que eu modifico são as constantes r, k e amplitude.
    */
    const time = performance.now() * 0.0001;  // Tempo de animação
    const positions = globeMesh.geometry.attributes.position.array;
    const original = globeMesh.originalPositions;
    const r = sphereRadius;  // Raio da esfera
    const k = 1.1;  // Fator de escala do ruído
    const amplitude = 0.45;  // Amplitude do movimento

    // Atualiza a posição dos vértices com Perlin noise
    for (let i = 0; i < positions.length / 3; i++) {
      const ix = i * 3;
      const iy = i * 3 + 1;
      const iz = i * 3 + 2;

      const p = new THREE.Vector3(original[ix], original[iy], original[iz]);

      p.normalize().multiplyScalar(r + amplitude * noise.perlin3(p.x * k + time, p.y * k, p.z * k));

      positions[ix] = p.x;  // Atualiza a posição X
      positions[iy] = p.y;  // Atualiza a posição Y
      positions[iz] = p.z;  // Atualiza a posição Z
    }

    globeMesh.geometry.attributes.position.needsUpdate = true;  // Marca a geometria para atualização
    globeMesh.geometry.computeVertexNormals();  // Recalcula as normais dos vértices para iluminação

    // Atualiza as partículas
    particleGroup.children.forEach(p => {
      p.position.add(p.userData.velocity);  // Atualiza a posição da partícula com base na sua velocidade
      if (p.position.length() > sphereRadius * 0.9) {  // Inverte a direção se a partícula ultrapassar o limite da esfera
        p.userData.velocity.negate();
      }
    });

    // Rotação automática suave da esfera (anti-horário)
    globeGroup.rotation.y -= 0.001;

    // Renderiza a cena com a câmera
    renderer.render(scene, camera);
  }

  animate();  // Inicia a animação

  // Torna o contêiner da esfera visível após a inicialização
  sphereContainer.style.visibility = "visible";
  sphereContainer.style.opacity = "1";

  sphereInitialized = true;  // Marca a esfera como inicializada
  const initialCount = window.numParticles || 10;  // Número inicial de partículas
  updateParticles(initialCount);  // Atualiza as partículas com a contagem inicial
}

/**
 * Função para exibir o modal da esfera com visualização interativa.
 * @function
 */
window.showSphereModal = function() {
  const sphereModal = document.getElementById('sphere-modal');
  sphereModal.style.display = 'flex';  // Exibe o modal
  document.dispatchEvent(new Event("sphereModalOpened"));  // Dispara evento de abertura do modal
  if (!sphereInitialized) {
    initSphereScene();  // Inicializa a cena se ainda não estiver inicializada
  } else {
    if (typeof window.numParticles === "number") {
      updateParticles(window.numParticles);  // Atualiza as partículas com o número configurado
    } else {
      updateParticles(10);  // Atualiza as partículas com a quantidade padrão
    }
  }
};

  /**
   * Função para fechar o modal da esfera.
   * @function
   */
  document.getElementById('sphere-modal-close').addEventListener('click', function() {
    const sphereModal = document.getElementById('sphere-modal');
    sphereModal.style.display = 'none';  // Fecha o modal
    document.dispatchEvent(new Event("sphereModalClosed"));  // Dispara evento de fechamento do modal
  });
});
