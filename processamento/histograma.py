"""
Histograma — análise da distribuição de intensidades dos canais R, G e B.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt

from . import visualizacao

CORES = ("red", "green", "blue")
NOMES = ("Vermelho (R)", "Verde (G)", "Azul (B)")


def analisar_histograma(img_rgb):
    """Plota o histograma de cada canal e retorna as médias e o dominante."""
    fig, eixos = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Histograma dos Canais de Cor — Imagem Original", fontsize=14)

    for i, (cor, nome) in enumerate(zip(CORES, NOMES)):
        hist = cv2.calcHist([img_rgb], [i], None, [256], [0, 256])
        eixos[i].plot(hist, color=cor)
        eixos[i].fill_between(range(256), hist.ravel(), color=cor, alpha=0.3)
        eixos[i].set_title(nome)
        eixos[i].set_xlabel("Intensidade (0–255)")
        eixos[i].set_ylabel("Quantidade de pixels")
        eixos[i].set_xlim([0, 255])

    plt.tight_layout()
    visualizacao.salvar_figura(fig, "01_histograma_rgb.png")

    medias = [img_rgb[:, :, i].mean() for i in range(3)]
    return {
        "medias": medias,
        "canal_dominante": NOMES[int(np.argmax(medias))],
    }
