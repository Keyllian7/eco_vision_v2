"""
Visualização — geração dos grids comparativos do relatório (Matplotlib).

As figuras são salvas na pasta de resultados; o backend "Agg" permite
gerar os arquivos sem abrir janelas (essencial rodando como servidor).
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PASTA_RESULTADOS = "resultados"


def plotar_grid(imagens, titulos, nome_arquivo, titulo_geral="", cinza=False):
    """Monta um grid comparativo com as imagens e salva em resultados/."""
    n = len(imagens)
    fig, eixos = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        eixos = [eixos]
    if titulo_geral:
        fig.suptitle(titulo_geral, fontsize=14)

    for eixo, img, titulo in zip(eixos, imagens, titulos):
        mapa = "gray" if (cinza and img.ndim == 2) else None
        eixo.imshow(img, cmap=mapa)
        eixo.set_title(titulo)
        eixo.axis("off")

    plt.tight_layout()
    salvar_figura(fig, nome_arquivo)


def salvar_figura(fig, nome_arquivo):
    """Salva a figura na pasta de resultados e libera a memória."""
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    caminho = os.path.join(PASTA_RESULTADOS, nome_arquivo)
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
