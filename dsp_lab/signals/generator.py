"""Generación educativa de señales discretas.

En este módulo el estudiante debe aprender:
- La relación entre frecuencia de muestreo (`fs`), periodo de muestreo (`Ts`) y eje temporal.
- Cómo se construyen señales básicas muestra a muestra.
- Qué parámetros controlan amplitud, fase, frecuencia y duración.
"""

from __future__ import annotations

import math
import random
from typing import List, Tuple


class SignalGenerator:
    """Generador simple de señales en tiempo discreto."""

    def __init__(self, fs: float) -> None:
        if fs <= 0:
            raise ValueError("fs debe ser mayor que cero")
        self.fs = fs
        self.Ts = 1.0 / fs

    def time_axis(self, duration: float) -> List[float]:
        """Crea un eje temporal discreto para una duración dada."""
        if duration <= 0:
            raise ValueError("duration debe ser mayor que cero")
        n_samples = int(duration * self.fs)
        return [n * self.Ts for n in range(n_samples)]

    def sine(self, frequency: float, duration: float, amplitude: float = 1.0, phase: float = 0.0) -> Tuple[List[float], List[float]]:
        """Genera una señal senoidal muestra a muestra."""
        t = self.time_axis(duration)
        x = [amplitude * math.sin(2.0 * math.pi * frequency * tn + phase) for tn in t]
        return t, x

    def square(self, frequency: float, duration: float, amplitude: float = 1.0) -> Tuple[List[float], List[float]]:
        """Genera una onda cuadrada básica a partir del signo de una senoide."""
        t = self.time_axis(duration)
        x = [amplitude if math.sin(2.0 * math.pi * frequency * tn) >= 0 else -amplitude for tn in t]
        return t, x

    def noise(self, duration: float, amplitude: float = 1.0) -> Tuple[List[float], List[float]]:
        """Genera ruido uniforme simple para pruebas educativas."""
        t = self.time_axis(duration)
        x = [random.uniform(-amplitude, amplitude) for _ in t]
        return t, x

    def chirp(self, start_frequency: float, end_frequency: float, duration: float, amplitude: float = 1.0) -> Tuple[List[float], List[float]]:
        """Plantilla de chirp lineal.

        TODO: completar la fase instantánea para que la frecuencia cambie de
        `start_frequency` a `end_frequency` durante la duración indicada.
        """
        t = self.time_axis(duration)
        x = [0.0 for _ in t]
        return t, x
