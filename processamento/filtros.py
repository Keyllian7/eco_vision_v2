"""
Filtros de suavização — Gaussiano, Mediana e Bilateral.
"""

import cv2

SIGMA_GAUSSIANO = 1.5   # desvio padrão do filtro Gaussiano
KERNEL_MEDIANA = 5      # tamanho do kernel do filtro de Mediana
BILATERAL_D = 9         # diâmetro da vizinhança do filtro Bilateral
BILATERAL_SIGMA = 75    # sigma de cor e de espaço do Bilateral


def aplicar_gaussiano(img_rgb):
    """Convolução com kernel gaussiano: cada pixel vira a média ponderada
    da vizinhança (vizinhos próximos pesam mais). Reduz ruído de alta
    frequência, mas borra as bordas."""
    return cv2.GaussianBlur(img_rgb, (0, 0), SIGMA_GAUSSIANO)


def aplicar_mediana(img_rgb):
    """Substitui cada pixel pela MEDIANA da vizinhança. Elimina ruído
    impulsivo ("sal e pimenta") sem criar valores novos, preservando
    bordas melhor que o Gaussiano."""
    return cv2.medianBlur(img_rgb, KERNEL_MEDIANA)


def aplicar_bilateral(img_rgb):
    """Pondera os vizinhos por proximidade espacial E semelhança de cor:
    a suavização não atravessa bordas, mantendo-as nítidas."""
    return cv2.bilateralFilter(img_rgb, d=BILATERAL_D,
                               sigmaColor=BILATERAL_SIGMA,
                               sigmaSpace=BILATERAL_SIGMA)


def aplicar_filtros(img_rgb):
    """Aplica os três filtros e retorna um dicionário com os resultados."""
    return {
        "gaussiano": aplicar_gaussiano(img_rgb),
        "mediana": aplicar_mediana(img_rgb),
        "bilateral": aplicar_bilateral(img_rgb),
    }
