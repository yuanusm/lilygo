# dsp_lab

Proyecto educativo para implementar manualmente conceptos fundamentales de procesamiento digital de señales (DSP): generación de señales, sistemas discretos, filtros FIR/IIR y análisis espectral.

> Objetivo: completar los algoritmos paso a paso sin usar `scipy.signal` ni `numpy.fft` para FIR, IIR o FFT/DFT.

## Módulos

- `signals/`: generación de señales de prueba.
- `core/`: abstracciones comunes para sistemas discretos.
- `systems/`: esqueletos de filtros FIR e IIR.
- `analysis/`: análisis espectral con DFT manual educativa.
- `visualization/`: utilidades de graficación con Matplotlib.

## Ejecución sugerida

```bash
python -m dsp_lab.main
```

Los experimentos incluidos son guías para que el estudiante complete implementaciones y compare resultados.
