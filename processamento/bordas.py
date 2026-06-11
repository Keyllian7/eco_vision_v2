"""
Detecção de bordas — Canny.
"""

import cv2

CANNY_LIMIAR_MIN = 50    # limiar inferior da histerese
CANNY_LIMIAR_MAX = 150   # limiar superior da histerese
SIGMA_SUAVIZACAO = 1.5   # suavização prévia para reduzir falsas bordas


def detectar_bordas(img_cinza):
    """Suaviza a imagem em cinza e aplica o operador Canny."""
    img_suave = cv2.GaussianBlur(img_cinza, (5, 5), SIGMA_SUAVIZACAO)
    return cv2.Canny(img_suave, CANNY_LIMIAR_MIN, CANNY_LIMIAR_MAX)
