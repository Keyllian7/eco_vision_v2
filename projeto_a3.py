"""
================================================================================
ECO VISION V2 — Estimativa de Cobertura Vegetal
================================================================================
Disciplina : Computação Gráfica — Avaliação A3
Curso      : Ciência da Computação
Aluno      : Keyllian Azevedo

PROBLEMA AMBIENTAL: estimar o percentual de COBERTURA VEGETAL de uma área
a partir de uma imagem (foto ou satélite), apoiando o monitoramento de
desmatamento e arborização urbana. A resposta final do sistema é:
"quantos % desta cena são vegetação?"

Este servidor Flask executa o pipeline etapa por etapa, permitindo
acompanhar e explicar cada técnica durante a apresentação. Cada etapa
exibe NO MÁXIMO duas imagens lado a lado (em resolução cheia, salvas em
resultados/painel/), para que a diferença entre elas seja nítida. Os
grids comparativos do relatório são gerados em resultados/.

A lógica de processamento vive no pacote `processamento/` — um módulo por
responsabilidade. Este arquivo só orquestra as etapas e serve o painel.

Execução:
    python app.py
    → abra http://localhost:5000 no navegador
================================================================================
"""

import os
import time

import cv2
from flask import (Flask, jsonify, render_template, request,
                   send_file, send_from_directory)

from processamento import (aquisicao, bordas, filtros, histograma,
                           metricas, pre_processamento, segmentacao,
                           visualizacao)

app = Flask(__name__)

# Intermediários do pipeline da sessão atual (imagem carregada, máscaras etc.).
# Como o painel é de uso local e individual, um dicionário simples é suficiente.
ESTADO = {}

ARQUIVO_ORIGINAL = "imagem_original.png"
PASTA_PAINEL = os.path.join(visualizacao.PASTA_RESULTADOS, "painel")


def salvar_imagem_painel(nome, img, legenda):
    """Salva uma imagem individual em resolução cheia para exibição no painel
    e devolve o item {url, legenda} consumido pelo frontend."""
    os.makedirs(PASTA_PAINEL, exist_ok=True)
    caminho = os.path.join(PASTA_PAINEL, nome)
    if img.ndim == 2:
        cv2.imwrite(caminho, img)                                   # cinza/máscara
    else:
        cv2.imwrite(caminho, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))  # RGB → BGR
    return {"url": url_resultado(f"painel/{nome}"), "legenda": legenda}


def url_resultado(nome_arquivo):
    """Monta a URL da imagem gerada com cache-busting (timestamp),
    para o navegador sempre exibir a versão mais recente."""
    return f"/resultados/{nome_arquivo}?t={int(time.time() * 1000)}"


# --------------------------------------------------------------------------- #
# Rotas de páginas e arquivos
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resultados/<path:nome>")
def servir_resultado(nome):
    return send_from_directory(visualizacao.PASTA_RESULTADOS, nome)


@app.route("/imagem-original")
def servir_original():
    return send_file(ARQUIVO_ORIGINAL)


# --------------------------------------------------------------------------- #
# Etapa 1 — Upload e aquisição
# --------------------------------------------------------------------------- #
@app.post("/upload")
def upload():
    arquivo = request.files.get("imagem")
    if not arquivo:
        return jsonify(erro="Nenhuma imagem enviada."), 400

    # Decodifica o upload em memória e salva sempre como PNG,
    # garantindo o entregável imagem_original.png
    img_bgr = aquisicao.decodificar_upload(arquivo.read())
    if img_bgr is None:
        return jsonify(erro="Arquivo não é uma imagem válida."), 400
    cv2.imwrite(ARQUIVO_ORIGINAL, img_bgr)

    ESTADO.clear()
    ESTADO["img_rgb"] = aquisicao.carregar_imagem(ARQUIVO_ORIGINAL)

    altura, largura, canais = ESTADO["img_rgb"].shape
    tamanho_kb = os.path.getsize(ARQUIVO_ORIGINAL) / 1024
    return jsonify(
        imagens=[{"url": f"/imagem-original?t={int(time.time() * 1000)}",
                  "legenda": "Imagem original capturada"}],
        info=[
            {"label": "Resolução", "valor": f"{largura} × {altura} px"},
            {"label": "Canais", "valor": f"{canais} (RGB)"},
            {"label": "Profundidade", "valor": "8 bits/canal [0–255]"},
            {"label": "Leitura", "valor": "BGR → RGB"},
            {"label": "Tamanho", "valor": f"{tamanho_kb:.1f} KB"},
        ],
    )


# --------------------------------------------------------------------------- #
# Etapas 2 a 11 — uma função por etapa do pipeline
# --------------------------------------------------------------------------- #
def etapa_pre_processamento():
    img_red, img_cinza, img_norm = pre_processamento.pre_processar(
        ESTADO["img_rgb"])
    ESTADO.update(img_red=img_red, img_cinza=img_cinza)

    # Grid do relatório (entregável)
    visualizacao.plotar_grid(
        [img_red, img_cinza],
        ["Original (RGB)", "Escala de Cinza"],
        "00_original_vs_cinza.png",
        titulo_geral="Original × Escala de Cinza",
        cinza=True,
    )
    return {
        "imagens": [
            salvar_imagem_painel("02_original.png", img_red,
                                 "Original redimensionada (RGB)"),
            salvar_imagem_painel("02_cinza.png", img_cinza,
                                 "Escala de cinza (0,299R + 0,587G + 0,114B)"),
        ],
        "info": [
            {"label": "Nova resolução",
             "valor": f"{img_red.shape[1]} × {img_red.shape[0]} px"},
            {"label": "Cinza (luminância)", "valor": "0,299R + 0,587G + 0,114B"},
            {"label": "Interpolação", "valor": "por área (média dos pixels)"},
            {"label": "Normalização",
             "valor": f"[{img_norm.min():.2f}, {img_norm.max():.2f}]"},
        ],
    }


def etapa_histograma():
    analise = histograma.analisar_histograma(ESTADO["img_red"])
    m = analise["medias"]
    return {
        "imagens": [{"url": url_resultado("01_histograma_rgb.png"),
                     "legenda": "Distribuição de intensidades por canal"}],
        "info": [
            {"label": "Bins por canal", "valor": "256 (0–255)"},
            {"label": "Média R", "valor": f"{m[0]:.1f}"},
            {"label": "Média G", "valor": f"{m[1]:.1f}"},
            {"label": "Média B", "valor": f"{m[2]:.1f}"},
            {"label": "Canal dominante", "valor": analise["canal_dominante"]},
        ],
    }


def etapa_filtro_gaussiano():
    # Os três filtros são calculados de uma vez; os resultados ficam no
    # ESTADO para as duas etapas seguintes
    ESTADO["filtros"] = filtros.aplicar_filtros(ESTADO["img_red"])
    f = ESTADO["filtros"]

    # Grid comparativo do relatório (entregável)
    visualizacao.plotar_grid(
        [ESTADO["img_red"], f["gaussiano"], f["mediana"], f["bilateral"]],
        ["Original", f"Gaussiano (σ={filtros.SIGMA_GAUSSIANO})",
         f"Mediana ({filtros.KERNEL_MEDIANA}×{filtros.KERNEL_MEDIANA})",
         "Bilateral"],
        "02_filtros_comparativo.png",
        titulo_geral="Comparativo de Filtros de Suavização",
    )
    return {
        "imagens": [
            salvar_imagem_painel("04_original.png", ESTADO["img_red"],
                                 "Original"),
            salvar_imagem_painel("04_gaussiano.png", f["gaussiano"],
                                 f"Filtro Gaussiano (σ = {filtros.SIGMA_GAUSSIANO})"),
        ],
        "info": [
            {"label": "Tipo", "valor": "passa-baixa linear"},
            {"label": "Kernel", "valor": "gaussiano, gerado a partir de σ"},
            {"label": "Sigma (σ)", "valor": f"{filtros.SIGMA_GAUSSIANO}"},
            {"label": "Efeito nas bordas", "valor": "borra (suaviza tudo)"},
        ],
    }


def etapa_filtro_mediana():
    k = filtros.KERNEL_MEDIANA
    return {
        "imagens": [
            salvar_imagem_painel("05_original.png", ESTADO["img_red"],
                                 "Original"),
            salvar_imagem_painel("05_mediana.png", ESTADO["filtros"]["mediana"],
                                 f"Filtro de Mediana (kernel {k}×{k})"),
        ],
        "info": [
            {"label": "Tipo", "valor": "não-linear (de ordem)"},
            {"label": "Kernel", "valor": f"{k} × {k} ({k * k} valores)"},
            {"label": "Operação", "valor": "mediana da vizinhança"},
            {"label": "Robusto a", "valor": "ruído sal e pimenta"},
        ],
    }


def etapa_filtro_bilateral():
    s = filtros.BILATERAL_SIGMA
    return {
        "imagens": [
            salvar_imagem_painel("06_original.png", ESTADO["img_red"],
                                 "Original"),
            salvar_imagem_painel("06_bilateral.png",
                                 ESTADO["filtros"]["bilateral"],
                                 f"Filtro Bilateral (d={filtros.BILATERAL_D}, "
                                 f"σcor={s}, σespaço={s})"),
        ],
        "info": [
            {"label": "Tipo", "valor": "não-linear, preserva borda"},
            {"label": "Diâmetro (d)", "valor": f"{filtros.BILATERAL_D} px"},
            {"label": "σ de cor / espaço", "valor": f"{s} / {s}"},
            {"label": "Pesos", "valor": "espaço × semelhança de cor"},
        ],
    }


def etapa_bordas():
    img_bordas = bordas.detectar_bordas(ESTADO["img_cinza"])
    perc = 100 * (img_bordas > 0).sum() / img_bordas.size

    # Grid do relatório (entregável)
    visualizacao.plotar_grid(
        [ESTADO["img_cinza"], img_bordas],
        ["Escala de Cinza",
         f"Bordas — Canny ({bordas.CANNY_LIMIAR_MIN}, {bordas.CANNY_LIMIAR_MAX})"],
        "03_bordas_canny.png",
        titulo_geral="Detecção de Bordas (Operador Canny)",
        cinza=True,
    )
    return {
        "imagens": [
            salvar_imagem_painel("07_cinza.png", ESTADO["img_cinza"],
                                 "Escala de cinza (entrada do Canny)"),
            salvar_imagem_painel("07_bordas.png", img_bordas,
                                 "Bordas detectadas (Canny)"),
        ],
        "info": [
            {"label": "Operador de gradiente", "valor": "Sobel"},
            {"label": "Etapas", "valor": "gradiente → afinamento → histerese"},
            {"label": "Limiares (histerese)",
             "valor": f"{bordas.CANNY_LIMIAR_MIN} / {bordas.CANNY_LIMIAR_MAX}"},
            {"label": "Pixels de borda", "valor": f"{perc:.2f}% da imagem"},
        ],
    }


def etapa_indice_exg():
    # segmentar() executa toda a cadeia (ExG → Otsu → morfologia → contornos);
    # os intermediários alimentam as etapas 9 a 11
    seg = segmentacao.segmentar(ESTADO["img_red"])
    ESTADO["seg"] = seg

    # Grid do relatório (entregável)
    visualizacao.plotar_grid(
        [seg["exg"], seg["mascara_otsu"], seg["mascara"], seg["img_contornos"]],
        ["Índice ExG (2G−R−B)",
         f"Máscara Otsu (limiar={seg['limiar']:.0f})",
         "Após Morfologia (abertura + fechamento)",
         "Contornos sobre a Original"],
        "04_segmentacao_otsu.png",
        titulo_geral="Segmentação da Vegetação — ExG + Otsu + Morfologia",
        cinza=True,
    )
    return {
        "imagens": [
            salvar_imagem_painel("08_original.png", ESTADO["img_red"],
                                 "Original"),
            salvar_imagem_painel("08_exg.png", seg["exg"],
                                 "Índice ExG — quanto mais claro, mais vegetação"),
        ],
        "info": [
            {"label": "ExG — Excess Green (excesso de verde)",
             "valor": "2G − R − B"},
            {"label": "Base", "valor": "NDVI (índice de vegetação de satélite)"},
            {"label": "Realça", "valor": "predomínio do verde"},
            {"label": "Saída", "valor": "mapa normalizado [0, 255]"},
        ],
    }


def etapa_otsu():
    seg = ESTADO["seg"]
    return {
        "imagens": [
            salvar_imagem_painel("09_exg.png", seg["exg"],
                                 "Índice ExG (entrada do Otsu)"),
            salvar_imagem_painel("09_otsu.png", seg["mascara_otsu"],
                                 "Máscara binária (branco = vegetação)"),
        ],
        "info": [
            {"label": "Tipo", "valor": "limiar global automático"},
            {"label": "Busca", "valor": "256 limiares testados"},
            {"label": "Limiar encontrado", "valor": f"{seg['limiar']:.0f}"},
            {"label": "Critério", "valor": "máxima variância entre classes"},
        ],
    }


def etapa_morfologia():
    seg = ESTADO["seg"]
    return {
        "imagens": [
            salvar_imagem_painel("10_antes.png", seg["mascara_otsu"],
                                 "Máscara antes da morfologia"),
            salvar_imagem_painel("10_depois.png", seg["mascara"],
                                 "Após abertura + fechamento"),
        ],
        "info": [
            {"label": "Elemento estruturante", "valor": "elipse 5 × 5"},
            {"label": "Abertura (erosão→dilatação)", "valor": "remove ruído"},
            {"label": "Fechamento (dilatação→erosão)", "valor": "preenche buracos"},
            {"label": "Regiões de vegetação",
             "valor": f"{seg['n_regioes']} contornos"},
        ],
    }


def etapa_final():
    seg = ESTADO["seg"]
    resultado = metricas.calcular_metricas(
        ESTADO["img_red"], ESTADO["filtros"]["gaussiano"], seg["mascara"])

    # Grid resumo do relatório (entregável)
    visualizacao.plotar_grid(
        [ESTADO["img_red"], seg["exg"], seg["mascara"], seg["img_contornos"]],
        ["1. Original", "2. Índice ExG (vegetação)",
         "3. Máscara de Vegetação", "4. Contornos Detectados"],
        "05_resumo_pipeline.png",
        titulo_geral="Resumo do Pipeline — Estimativa de Cobertura Vegetal",
        cinza=True,
    )
    return {
        "imagens": [
            salvar_imagem_painel("11_original.png", ESTADO["img_red"],
                                 "Original"),
            salvar_imagem_painel("11_contornos.png", seg["img_contornos"],
                                 "Vegetação identificada (contornos em vermelho)"),
        ],
        "info": [
            {"label": "🌿 COBERTURA VEGETAL ESTIMADA",
             "valor": f"{resultado['cobertura_vegetal_pct']:.2f}%"},
            {"label": "Cálculo", "valor": "pixels brancos ÷ total × 100"},
            {"label": "PSNR — Relação Sinal-Ruído de Pico (qualidade da filtragem)",
             "valor": f"{resultado['psnr']:.2f} dB"},
            {"label": "SNR — Relação Sinal-Ruído",
             "valor": f"{resultado['snr']:.2f} dB"},
            {"label": "MSE — Erro Quadrático Médio (base do PSNR e SNR)",
             "valor": "diferença média entre as imagens"},
            {"label": "Valor médio de pixel",
             "valor": f"{resultado['media_pixel']:.1f}"},
        ],
    }


ETAPAS = {
    2: etapa_pre_processamento,
    3: etapa_histograma,
    4: etapa_filtro_gaussiano,
    5: etapa_filtro_mediana,
    6: etapa_filtro_bilateral,
    7: etapa_bordas,
    8: etapa_indice_exg,
    9: etapa_otsu,
    10: etapa_morfologia,
    11: etapa_final,
}


@app.post("/etapa/<int:numero>")
def executar_etapa(numero):
    if "img_rgb" not in ESTADO:
        return jsonify(erro="Envie uma imagem antes de executar as etapas."), 400
    if numero not in ETAPAS:
        return jsonify(erro=f"Etapa {numero} não existe."), 404
    return jsonify(ETAPAS[numero]())


if __name__ == "__main__":
    print("Eco Vision V2 — painel disponível em http://localhost:5000")
    app.run(debug=False, port=5000)
