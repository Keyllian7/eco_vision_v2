"""
Pré-processamento — escala de cinza, redimensionamento e normalização.
"""

import cv2
import numpy as np

LARGURA_PADRAO = 800  # largura usada no redimensionamento


def pre_processar(img_rgb):
    """Converte para escala de cinza, redimensiona e normaliza para [0, 1].

    - Escala de cinza: média ponderada dos canais (0.299R + 0.587G + 0.114B),
      que reflete a sensibilidade do olho humano a cada cor.
    - Redimensionamento: padroniza a largura mantendo a proporção original.
    - Normalização: converte os valores de [0, 255] para [0, 1] (float),
      formato adequado para operações numéricas.
    """
    proporcao = LARGURA_PADRAO / img_rgb.shape[1]
    nova_altura = int(img_rgb.shape[0] * proporcao)
    img_red = cv2.resize(img_rgb, (LARGURA_PADRAO, nova_altura),
                         interpolation=cv2.INTER_AREA)

    img_cinza = cv2.cvtColor(img_red, cv2.COLOR_RGB2GRAY)
    img_norm = img_red.astype(np.float32) / 255.0

    return img_red, img_cinza, img_norm
