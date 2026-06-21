"""Herramientas de visualización con Matplotlib.

En este módulo el estudiante debe aprender:
- Cómo inspeccionar una señal en el dominio del tiempo.
- Cómo interpretar un espectro de magnitud.
- Cómo comparar visualmente entrada y salida de un sistema discreto.
"""

from __future__ import annotations

from typing import List

import matplotlib.pyplot as plt


class Plotter:
    """Utilidades simples para graficar experimentos DSP."""

    def plot_time(self, t: List[float], x: List[float], title: str = "Señal en el tiempo") -> None:
        """Grafica una señal discreta en el dominio temporal."""
        plt.figure()
        plt.plot(t, x)
        plt.title(title)
        plt.xlabel("Tiempo [s]")
        plt.ylabel("Amplitud")
        plt.grid(True)

    def plot_frequency(self, frequencies: List[float], magnitudes: List[float], title: str = "Espectro") -> None:
        """Grafica un espectro de magnitud."""
        plt.figure()
        plt.plot(frequencies, magnitudes)
        plt.title(title)
        plt.xlabel("Frecuencia [Hz]")
        plt.ylabel("Magnitud")
        plt.grid(True)

    def show(self) -> None:
        """Muestra todas las figuras pendientes."""
        plt.show()
