"""
Aquisição — leitura/decodificação da imagem e conversão de espaço de cores.

O OpenCV trabalha internamente com o formato BGR; a conversão para RGB é
necessária para que as cores sejam exibidas corretamente no navegador e
no Matplotlib.
"""

import cv2
import numpy as np


def decodificar_upload(dados_bytes):
    """Decodifica os bytes enviados pelo navegador em uma imagem BGR.

    Retorna None se os bytes não corresponderem a uma imagem válida.
    """
    dados = np.frombuffer(dados_bytes, np.uint8)
    return cv2.imdecode(dados, cv2.IMREAD_COLOR)


def carregar_imagem(caminho):
    """Lê a imagem do disco com cv2.imread() e converte BGR → RGB."""
    img_bgr = cv2.imread(caminho)
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
