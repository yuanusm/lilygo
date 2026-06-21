"""Abstracciones comunes para sistemas discretos.

En este módulo el estudiante debe aprender:
- Cómo representar la frecuencia de muestreo de un sistema.
- Cómo calcular `Ts` a partir de `fs`.
- Cómo definir una interfaz común para procesar secuencias discretas.
"""

from __future__ import annotations

from typing import List


class DiscreteTimeSystem:
    """Clase base para sistemas que procesan señales en tiempo discreto."""

    def __init__(self, fs: float) -> None:
        if fs <= 0:
            raise ValueError("fs debe ser mayor que cero")
        self.fs = fs
        self.Ts = 1.0 / fs

    def process(self, x: List[float]) -> List[float]:
        """Procesa una secuencia de entrada.

        Las subclases deben implementar la ecuación correspondiente.
        """
        raise NotImplementedError("Implementar en la subclase")
