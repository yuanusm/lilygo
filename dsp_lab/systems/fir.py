"""Filtro FIR educativo.

En este módulo el estudiante debe aprender:
- La ecuación de convolución discreta.
- El rol de los coeficientes `b[k]` como respuesta al impulso finita.
- Cómo manejar índices fuera del rango de la señal de entrada.
"""

from __future__ import annotations

from typing import List

from dsp_lab.core import DiscreteTimeSystem


class FIRFilter(DiscreteTimeSystem):
    """Plantilla de filtro FIR basado en convolución manual."""

    def __init__(self, fs: float, coefficients: List[float]) -> None:
        super().__init__(fs)
        if not coefficients:
            raise ValueError("coefficients no puede estar vacío")
        self.b = coefficients

    """def process(self, x: List[float]) -> List[float]:
        Aplica la ecuación FIR.

        Ecuación objetivo:
            y[n] = sum_{k=0}^{M-1} b[k] * x[n-k]

        TODO: implementar manualmente la convolución, sin usar `scipy.signal`.
        
        y = [0.0 for _ in x]
        return y"""
    def process(self, x: List[float]) -> List[float]:
    #"""Aplica la ecuación FIR de forma directa."""

        M = len(self.b)
        N = len(x)

        y = [0.0] * N

        # Recorre cada muestra de salida
        for n in range(N):
            acc = 0.0

            # convolución manual
            for k in range(M):
                if n - k >= 0:
                    acc += self.b[k] * x[n - k]

            y[n] = acc

        return y