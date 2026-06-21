"""Filtro IIR educativo.

En este módulo el estudiante debe aprender:
- La ecuación en diferencias de un sistema recursivo.
- La diferencia entre coeficientes de entrada `b` y realimentación `a`.
- Por qué la estabilidad depende de la realimentación.
"""

from __future__ import annotations

from typing import List

from dsp_lab.core import DiscreteTimeSystem


class IIRFilter(DiscreteTimeSystem):
    """Plantilla de filtro IIR basado en ecuación en diferencias manual."""

    def __init__(self, fs: float, b_coefficients: List[float], a_coefficients: List[float]) -> None:
        super().__init__(fs)
        if not b_coefficients:
            raise ValueError("b_coefficients no puede estar vacío")
        if not a_coefficients or a_coefficients[0] == 0:
            raise ValueError("a_coefficients debe incluir a[0] distinto de cero")
        self.b = b_coefficients
        self.a = a_coefficients

    def process(self, x: List[float]) -> List[float]:
        """Aplica la ecuación IIR.

        Ecuación objetivo normalizada por a[0]:
            y[n] = (sum b[k] * x[n-k] - sum_{k=1}^{N} a[k] * y[n-k]) / a[0]

        TODO: implementar manualmente la ecuación en diferencias, sin usar `scipy.signal`.
        """
        y = [0.0 for _ in x]
        return y
