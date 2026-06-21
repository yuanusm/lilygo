"""Experimentos sugeridos para dsp_lab.

Este archivo NO resuelve los ejercicios. Solo organiza puntos de partida para
que el estudiante complete manualmente FIR, IIR y DFT/FFT en los módulos.
"""

from __future__ import annotations

from dsp_lab.analysis import FFTAnalyzer
from dsp_lab.signals import SignalGenerator
from dsp_lab.systems import FIRFilter, IIRFilter
from dsp_lab.visualization import Plotter


def experiment_aliasing() -> None:
    """Explorar aliasing variando frecuencia de señal y frecuencia de muestreo."""
    generator = SignalGenerator(fs=100.0)
    t, x = generator.sine(frequency=40.0, duration=0.2)
    Plotter().plot_time(t, x, "Experimento: aliasing")


def experiment_fir_filtering() -> None:
    """Completar `FIRFilter.process` y observar el efecto de coeficientes FIR."""
    generator = SignalGenerator(fs=200.0)
    _, x = generator.sine(frequency=10.0, duration=0.5)
    fir = FIRFilter(fs=200.0, coefficients=[1 / 3, 1 / 3, 1 / 3])
    y = fir.process(x)
    print("FIR pendiente de implementar:", y[:5])


def experiment_iir_response() -> None:
    """Completar `IIRFilter.process` y analizar una respuesta recursiva simple."""
    impulse = [1.0] + [0.0] * 31
    iir = IIRFilter(fs=200.0, b_coefficients=[1.0], a_coefficients=[1.0, -0.8])
    y = iir.process(impulse)
    print("IIR pendiente de implementar:", y[:5])


def experiment_spectral_analysis() -> None:
    """Completar `FFTAnalyzer.dft` y construir un espectro de magnitud."""
    generator = SignalGenerator(fs=128.0)
    _, x = generator.sine(frequency=16.0, duration=1.0)
    analyzer = FFTAnalyzer(fs=128.0)
    frequencies, magnitudes = analyzer.magnitude_spectrum(x)
    print("DFT pendiente de implementar:", list(zip(frequencies[:5], magnitudes[:5])))


def main() -> None:
    """Ejecuta los experimentos sugeridos como guía de laboratorio."""
    experiment_aliasing()
    experiment_fir_filtering()
    experiment_iir_response()
    experiment_spectral_analysis()


if __name__ == "__main__":
    main()
