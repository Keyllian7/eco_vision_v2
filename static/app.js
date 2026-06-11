/* ===== Eco Vision V2 — controle do painel etapa a etapa =====
 *
 * Fluxo: upload da imagem → cada clique em "Continuar" chama POST /etapa/<n>
 * no servidor Flask, que executa a técnica correspondente e devolve as
 * imagens geradas + os dados numéricos. O card da etapa seguinte só é
 * criado após a anterior concluir.
 */

// Explicações exibidas em cada etapa (apoio para a apresentação oral)
const ETAPAS = [
  {
    n: 2,
    titulo: "Pré-processamento",
    explicacao:
      "Prepara a imagem para as próximas etapas, deixando todas no mesmo formato. " +
      "Converte para <b>escala de cinza</b> (junta os canais R, G e B numa única intensidade, " +
      "dando mais peso ao verde, que o olho humano enxerga melhor), <b>redimensiona</b> para " +
      "800 px mantendo a proporção e <b>normaliza</b> os valores para uma escala padrão. "
      
  },
  {
    n: 3,
    titulo: "Análise de Histograma",
    explicacao:
      "Mostra como as cores estão distribuídas: conta quantos pixels existem em cada nível de " +
      "brilho, separado por canal <b>R</b>, <b>G</b> e <b>B</b>. Pela forma do gráfico dá pra ver " +
      "se a imagem é escura, clara ou bem contrastada. Se o <b>canal verde</b> tem média alta, é " +
      "sinal de bastante vegetação na cena. "
      
  },
  {
    n: 4,
    titulo: "Filtro Gaussiano",
    explicacao:
      "Filtro que <b>borra suavemente</b> a imagem para remover ruído. Cada pixel vira uma " +
      "<b>média ponderada</b> dos vizinhos — os mais próximos pesam mais. É simples e eficaz, " +
      "mas tem um efeito colateral: como suaviza tudo por igual, também <b>borra as bordas</b> e " +
      "perde nitidez (compare os contornos com a original). "
      
  },
  {
    n: 5,
    titulo: "Filtro de Mediana",
    explicacao:
      "Remove ruído trocando cada pixel pela <b>mediana</b> (o valor do meio) dos vizinhos, em " +
      "vez da média. Como a mediana <b>ignora valores extremos</b>, é ótimo contra o ruído " +
      "<b>\"sal e pimenta\"</b> (pontos pretos e brancos aleatórios) e <b>preserva as bordas</b> " +
      "bem melhor que o Gaussiano. " 
      
  },
  {
    n: 6,
    titulo: "Filtro Bilateral",
    explicacao:
      "O filtro mais \"inteligente\": suaviza as regiões <b>sem borrar as bordas</b>. Ele só " +
      "mistura vizinhos que são <b>próximos E de cor parecida</b> — quando a cor muda muito (ou " +
      "seja, há uma borda), ele para de misturar. Resultado: áreas lisas com contornos nítidos. " 
      
  },
  {
    n: 7,
    titulo: "Detecção de Bordas (Canny)",
    explicacao:
      "Detecta as <b>bordas</b> — os lugares onde a cor muda bruscamente. Funciona em etapas: " +
      "suaviza a imagem, mede a <b>variação de intensidade</b> (gradiente), afina as linhas e, " +
      "por fim, usa <b>dois limiares</b> para decidir o que é borda de verdade (uma borda fraca " +
      "só vale se estiver ligada a uma forte). " 
      
  },
  {
    n: 8,
    titulo: "Índice de Vegetação ExG",
    explicacao:
      "Transforma a imagem num <b>mapa de vegetação</b>. Usa a fórmula <code>ExG = 2G − R − B</code>, " +
      "que realça os pixels onde o <b>verde domina</b> sobre o vermelho e o azul — típico de plantas. " +
      "Quanto mais claro no mapa, mais vegetação. É uma versão do <b>NDVI</b> (índice de vegetação " +
      "usado em satélites) adaptada para câmeras comuns, que não têm sensor infravermelho. " 
      
  },
  {
    n: 9,
    titulo: "Limiarização de Otsu",
    explicacao:
      "Transforma o mapa de vegetação em <b>preto e branco</b> (vegetação × resto), escolhendo o " +
      "ponto de corte <b>automaticamente</b>. Ele testa todos os valores possíveis e fica com " +
      "aquele que melhor <b>separa os dois grupos</b> de pixels. Resultado: branco = vegetação, " +
      "preto = resto. " 
      
  },
  {
    n: 10,
    titulo: "Refino Morfológico (Abertura + Fechamento)",
    explicacao:
      "<b>Limpa a máscara</b> preto e branco com duas operações. A <b>abertura</b> remove os " +
      "pontinhos brancos soltos (ruído) e o <b>fechamento</b> preenche os buracos pretos dentro " +
      "das regiões de vegetação. Resultado: manchas sólidas e bem definidas, prontas para contar. " 
      
  },
  {
    n: 11,
    titulo: "Resultado Final — Cobertura Vegetal",
    explicacao:
      "A resposta do projeto: o <b>percentual da cena coberto por vegetação</b>, calculado pela " +
      "proporção de pixels brancos na máscara final. Os <b>contornos vermelhos</b> marcam as " +
      "regiões identificadas sobre a foto original. As métricas <b>PSNR</b> e <b>SNR</b> (nas tags " +
      "abaixo) medem o quanto a filtragem preservou a qualidade da imagem. " 
      
  },
];

const painel = document.getElementById("painel");
const cardUpload = document.getElementById("card-upload");
const zonaUpload = document.getElementById("zona-upload");
const inputImagem = document.getElementById("input-imagem");

// ---------------------------------------------------------------- upload ----
// A zona de upload é um <label> que envolve o input: clicar nela já abre o
// seletor de arquivos nativamente. Por isso NÃO registramos um listener de
// clique aqui — fazê-lo abriria o seletor uma segunda vez.
zonaUpload.addEventListener("dragover", (e) => {
  e.preventDefault();
  zonaUpload.classList.add("arrastando");
});
zonaUpload.addEventListener("dragleave", () => zonaUpload.classList.remove("arrastando"));
zonaUpload.addEventListener("drop", (e) => {
  e.preventDefault();
  zonaUpload.classList.remove("arrastando");
  if (e.dataTransfer.files.length) enviarImagem(e.dataTransfer.files[0]);
});
inputImagem.addEventListener("change", () => {
  if (inputImagem.files.length) enviarImagem(inputImagem.files[0]);
});

async function enviarImagem(arquivo) {
  const dados = new FormData();
  dados.append("imagem", arquivo);

  zonaUpload.querySelector("#texto-upload").textContent = "⏳ Processando...";
  try {
    const resposta = await fetch("/upload", { method: "POST", body: dados });
    const json = await resposta.json();
    if (!resposta.ok) throw new Error(json.erro);

    // Reinicia o painel caso uma nova imagem seja enviada
    document.querySelectorAll(".card-etapa").forEach((c) => c.remove());

    zonaUpload.hidden = true;
    const conteudo = cardUpload.querySelector(".conteudo-etapa");
    conteudo.hidden = false;
    preencherConteudo(conteudo, json, 0);
  } catch (erro) {
    mostrarErro(cardUpload, erro.message);
    zonaUpload.querySelector("#texto-upload").textContent =
      "📷 Clique ou arraste a imagem aqui";
  }
}

// ---------------------------------------------------- execução das etapas ----
async function executarEtapa(indice, botaoAnterior) {
  const etapa = ETAPAS[indice];
  botaoAnterior.disabled = true;
  botaoAnterior.textContent = "⏳ Executando...";

  try {
    const resposta = await fetch(`/etapa/${etapa.n}`, { method: "POST" });
    const json = await resposta.json();
    if (!resposta.ok) throw new Error(json.erro);

    botaoAnterior.remove();
    criarCardEtapa(etapa, json, indice);
  } catch (erro) {
    botaoAnterior.disabled = false;
    botaoAnterior.textContent = "Continuar →";
    mostrarErro(botaoAnterior.closest(".card"), erro.message);
  }
}

function criarCardEtapa(etapa, json, indice) {
  const card = document.createElement("section");
  card.className = "card card-etapa";
  card.innerHTML = `
    <div class="card-cabecalho">
      <span class="numero">${etapa.n}</span>
      <h2>${etapa.titulo}</h2>
    </div>
    <p class="explicacao">${etapa.explicacao}</p>
    <div class="conteudo-etapa"></div>
  `;
  painel.appendChild(card);
  preencherConteudo(card.querySelector(".conteudo-etapa"), json, indice + 1);
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Insere imagens (no máximo 2, lado a lado), chips de dados e o botão da próxima etapa
function preencherConteudo(container, json, proximoIndice) {
  const grade = document.createElement("div");
  grade.className = "par-imagens" + (json.imagens.length === 1 ? " unica" : "");
  json.imagens.forEach(({ url, legenda }) => {
    const figura = document.createElement("figure");
    figura.className = "figura";
    figura.innerHTML = `<img src="${url}" alt="${legenda}">
                        <figcaption>${legenda}</figcaption>`;
    grade.appendChild(figura);
  });
  container.appendChild(grade);

  const chips = document.createElement("div");
  chips.className = "chips";
  json.info.forEach(({ label, valor }) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `${label}: <b>${valor}</b>`;
    chips.appendChild(chip);
  });
  container.appendChild(chips);

  if (proximoIndice < ETAPAS.length) {
    const botao = document.createElement("button");
    botao.className = "botao";
    botao.textContent = "Continuar →";
    botao.addEventListener("click", () => executarEtapa(proximoIndice, botao));
    container.appendChild(botao);
  } else {
    const reiniciar = document.createElement("button");
    reiniciar.className = "botao secundario";
    reiniciar.textContent = "↺ Processar outra imagem";
    reiniciar.addEventListener("click", () => location.reload());
    container.appendChild(reiniciar);
  }
}

function mostrarErro(card, mensagem) {
  card.querySelectorAll(".erro").forEach((e) => e.remove());
  const div = document.createElement("div");
  div.className = "erro";
  div.textContent = `Erro: ${mensagem}`;
  card.appendChild(div);
}
