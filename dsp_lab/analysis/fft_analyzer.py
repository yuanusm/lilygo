"""Análisis espectral educativo con DFT manual.

En este módulo el estudiante debe aprender:
- Cómo la DFT proyecta una señal sobre senos y cosenos complejos.
- La diferencia conceptual entre DFT O(N^2) y FFT O(N log N).
- Por qué no se debe usar `numpy.fft` mientras se aprende el algoritmo.
"""

from __future__ import annotations

from typing import List, Tuple


class FFTAnalyzer:
    """Plantilla de analizador espectral.

    El nombre de la clase prepara el proyecto para una futura FFT, pero el
    primer ejercicio recomendado es implementar una DFT manual O(N^2).
    """

    def __init__(self, fs: float) -> None:
        if fs <= 0:
            raise ValueError("fs debe ser mayor que cero")
        self.fs = fs

    def dft(self, x: List[float]) -> List[complex]:
        """Calcula la DFT manualmente.

        Ecuación objetivo:
            X[k] = sum_{n=0}^{N-1} x[n] * exp(-j * 2*pi*k*n/N)

        TODO: implementar con dos bucles anidados O(N^2), sin `numpy.fft`.
        """
        return [0j for _ in x]

    def magnitude_spectrum(self, x: List[float]) -> Tuple[List[float], List[float]]:
        """Devuelve frecuencias y magnitudes usando la DFT educativa.

        TODO: llamar a `dft`, calcular magnitud y construir el eje de frecuencia.
        """
        frequencies = [0.0 for _ in x]
        magnitudes = [0.0 for _ in x]
        return frequencies, magnitudes
