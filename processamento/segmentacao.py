"""
Segmentação da vegetação — índice ExG + Otsu + morfologia + contornos.

É a etapa que responde o problema ambiental do projeto: identificar quais
pixels da cena são vegetação, para então quantificar a cobertura vegetal.
"""

import cv2
import numpy as np

ELEMENTO_MORFOLOGIA = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
COR_CONTORNO = (255, 0, 0)  # vermelho (RGB) — destaca sobre a vegetação
ESPESSURA_CONTORNO = 2


def indice_vegetacao(img_rgb):
    """Calcula o índice ExG (Excess Green): ExG = 2G − R − B.

    O NDVI clássico exige banda infravermelha, indisponível em câmeras
    comuns. O ExG é sua adaptação para imagens RGB: realça pixels em que
    o canal verde domina sobre vermelho e azul — característica da
    vegetação. O resultado é normalizado para [0, 255] para permitir a
    limiarização de Otsu na sequência.
    """
    img = img_rgb.astype(np.float32)
    exg = 2 * img[:, :, 1] - img[:, :, 0] - img[:, :, 2]
    exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX)
    return exg_norm.astype(np.uint8)


def segmentar(img_rgb):
    """Executa a cadeia completa de segmentação da vegetação.

    - ExG: converte a imagem RGB em um mapa de "intensidade de vegetação".
    - Otsu: encontra automaticamente o limiar que maximiza a variância
      entre as duas classes (vegetação × não-vegetação) no mapa ExG.
    - Morfologia: abertura (erosão → dilatação) remove ruídos pequenos e
      fechamento (dilatação → erosão) preenche buracos na máscara.
    - Contornos: as fronteiras das regiões de vegetação são desenhadas
      sobre a imagem original em cor de destaque.

    Retorna um dicionário com todos os intermediários, permitindo que o
    painel exiba cada passo separadamente.
    """
    exg = indice_vegetacao(img_rgb)
    limiar, mascara_otsu = cv2.threshold(
        exg, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    mascara = cv2.morphologyEx(mascara_otsu, cv2.MORPH_OPEN,
                               ELEMENTO_MORFOLOGIA)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE,
                               ELEMENTO_MORFOLOGIA)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    img_contornos = img_rgb.copy()
    cv2.drawContours(img_contornos, contornos, -1,
                     COR_CONTORNO, ESPESSURA_CONTORNO)

    return {
        "exg": exg,
        "mascara_otsu": mascara_otsu,
        "mascara": mascara,
        "img_contornos": img_contornos,
        "limiar": limiar,
        "n_regioes": len(contornos),
    }
