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
      "Prepara a imagem para o processamento: converte para escala de cinza " +
      "(média ponderada dos canais R, G e B), redimensiona para 800 px de largura " +
      "e normaliza os valores para o intervalo [0, 1].",
  },
  {
    n: 3,
    titulo: "Análise de Histograma",
    explicacao:
      "Mostra como as intensidades dos pixels se distribuem em cada canal de cor. " +
      "Concentração à esquerda = imagem escura; à direita = imagem clara. " +
      "Canal verde dominante indica vegetação na cena.",
  },
  {
    n: 4,
    titulo: "Filtro Gaussiano",
    explicacao:
      "Suaviza a imagem: cada pixel vira a média ponderada dos vizinhos, onde os " +
      "mais próximos pesam mais. Remove o ruído (granulado), mas borra as bordas — " +
      "compare a nitidez dos contornos com a original.",
  },
  {
    n: 5,
    titulo: "Filtro de Mediana",
    explicacao:
      "Troca cada pixel pela MEDIANA da vizinhança 5×5, não pela média. Como a mediana " +
      "ignora valores extremos, elimina pixels aberrantes (ruído \"sal e pimenta\") " +
      "sem borrar as bordas.",
  },
  {
    n: 6,
    titulo: "Filtro Bilateral",
    explicacao:
      "Suaviza apenas vizinhos que são próximos E de cor parecida — a suavização " +
      "não atravessa as bordas. Resultado: regiões lisas com contornos intactos.",
  },
  {
    n: 7,
    titulo: "Detecção de Bordas (Canny)",
    explicacao:
      "Encontra os contornos onde a intensidade muda bruscamente (gradiente). " +
      "Os dois limiares (50/150) filtram o ruído: bordas fracas só são mantidas " +
      "se estiverem conectadas a uma borda forte.",
  },
  {
    n: 8,
    titulo: "Índice de Vegetação ExG (NDVI adaptado)",
    explicacao:
      "Transforma a imagem em um mapa de vegetação: ExG = 2G − R − B mede o quanto " +
      "o verde domina em cada pixel. Quanto mais claro, mais vegetação. " +
      "É a adaptação do NDVI para câmeras comuns, que não têm banda infravermelha.",
  },
  {
    n: 9,
    titulo: "Limiarização de Otsu",
    explicacao:
      "Escolhe automaticamente o limiar que melhor separa vegetação de não-vegetação: " +
      "testa todos os 256 valores possíveis e fica com o que melhor divide as duas " +
      "classes do histograma. Resultado: branco = vegetação, preto = resto.",
  },
  {
    n: 10,
    titulo: "Refino Morfológico (Abertura + Fechamento)",
    explicacao:
      "Limpa a máscara: a ABERTURA remove pontos brancos isolados (ruído) e o " +
      "FECHAMENTO preenche buracos dentro das regiões de vegetação.",
  },
  {
    n: 11,
    titulo: "Resultado Final — Cobertura Vegetal",
    explicacao:
      "A resposta do problema: o percentual da cena coberto por vegetação " +
      "(proporção de pixels brancos na máscara final). Os contornos vermelhos " +
      "delimitam as regiões identificadas sobre a imagem original.",
  },
];

const painel = document.getElementById("painel");
const cardUpload = document.getElementById("card-upload");
const zonaUpload = document.getElementById("zona-upload");
const inputImagem = document.getElementById("input-imagem");

// ---------------------------------------------------------------- upload ----
zonaUpload.addEventListener("click", () => inputImagem.click());
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
