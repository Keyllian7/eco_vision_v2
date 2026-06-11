"""
Métricas — PSNR, SNR e percentual de cobertura vegetal.

- PSNR: relação sinal-ruído de pico entre original e processada; valores acima de ~30 dB indicam alta semelhança.
- SNR: relação entre a potência do sinal e a do ruído introduzido.
- Cobertura vegetal: proporção de pixels brancos (vegetação) na máscara
  binária — a resposta final do problema ambiental.
"""

import numpy as np


def calcular_metricas(img_original, img_processada, mascara):
    """Calcula as métricas de qualidade e o resultado ambiental."""
    erro = img_original.astype(np.float64) - img_processada.astype(np.float64)
    mse = np.mean(erro ** 2)
    psnr = float("inf") if mse == 0 else 10 * np.log10((255.0 ** 2) / mse)
    snr = 10 * np.log10(np.mean(img_original.astype(np.float64) ** 2) / mse)

    return {
        "psnr": psnr,
        "snr": snr,
        "cobertura_vegetal_pct": 100 * np.count_nonzero(mascara) / mascara.size,
        "media_pixel": img_original.mean(),
    }
