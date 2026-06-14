# LilyGO T-Display ESP32 ECG BLE Monitor

Proyecto completo para Arduino IDE y PC que adquiere una señal ECG ya acondicionada por hardware, la muestrea con ADC continuo + DMA en una LilyGO T-Display ESP32 original, la filtra, la muestra en la TFT ST7789 y la transmite por BLE a una aplicación Python/Tkinter.

## Hardware objetivo

- Placa: LilyGO T-Display ESP32 original, ESP32-D0WDQ6.
- Pantalla: ST7789, 135x240.
- Entrada ECG: GPIO34 / ADC1_CH6.
- `ADC_POWER`: GPIO14, configurado como salida en `HIGH` durante `setup()` para alimentar la sección analógica.

La cadena analógica esperada es:

```text
Electrodos -> INA121 -> HPF -> BSF -> LPF -> GPIO34
```

La señal debe estar centrada alrededor de VCC/2 y dentro del rango aproximado de 0.5 V a 2.8 V. No se agrega ninguna etapa analógica en este proyecto.

## Estructura

```text
firmware/ECG_TDisplay_ESP32/   Firmware Arduino IDE
python_app/ecg_ble_viewer.py   GUI Tkinter + Bleak
python_app/requirements.txt    Dependencias Python
README.md                      Documentación
```

## Dependencias Arduino IDE

Instale desde Library Manager:

- `LovyanGFX`
- `NimBLE-Arduino`

Instale el core `esp32` de Espressif para Arduino IDE 2.x. El firmware usa la API moderna `esp_adc/adc_continuous.h`, disponible en Arduino-ESP32 3.x. En cores 2.x la API de ADC continuo difiere; use 3.x o adapte `adc_task.cpp` a la cabecera legacy equivalente.

Seleccione una placa ESP32 genérica o LilyGO T-Display ESP32, partición por defecto y compile `firmware/ECG_TDisplay_ESP32/ECG_TDisplay_ESP32.ino`.

## Dependencias Python

```bash
cd python_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ecg_ble_viewer.py
```

Tkinter viene incluido en la mayoría de distribuciones Python de escritorio. En Linux puede requerir `python3-tk` desde el gestor de paquetes del sistema.

## Arquitectura del firmware

El firmware separa responsabilidades con FreeRTOS:

- `TaskADC`: prioridad 6, core 0. Configura ADC continuo + DMA a 8000 SPS y hace sobremuestreo/decimación.
- `TaskDSP`: prioridad 4, core 1. Filtra notch 50/100/150 Hz, actualiza buffers circulares y reparte muestras.
- `TaskBLE`: prioridad 2, core 0. Servidor NimBLE, comandos y notificaciones. Nunca bloquea adquisición.
- `TaskDisplay`: prioridad 1, core 1. Dibuja ECG filtrado y estado BLE. Puede perder cuadros sin afectar muestras.

```text
                   +-------------------+
GPIO34 / ADC1_CH6 -> ADC Continuous DMA | 8000 SPS
                   +---------+---------+
                             |
                             v
                      +------+------+
                      |  TaskADC    | OSR=16, decima
                      +------+------+
                             |
                         Queue DSP
                             |
                             v
                      +------+------+
                      |  TaskDSP    | notch 50/100/150
                      +--+-------+--+
                         |       |
                 raw/filtered   muestras procesadas
                    buffers      |
                         |       +----------+------------+
                         v                  v            v
                  GET_BUFFER BLE        TaskBLE      TaskDisplay
                                      streaming       TFT local
```

## Adquisición ADC, sobremuestreo y decimación

No se usa `analogRead()`. El ADC se configura en modo continuo con DMA a:

```text
Fs_ADC = 8000 muestras/s
OSR = 16
Fs_salida = Fs_ADC / OSR = 8000 / 16 = 500 muestras/s
```

Para cada muestra de salida se promedian 16 conversiones consecutivas:

```text
y[n] = (1/16) * Σ x[16n + k], k=0..15
```

Esto es un filtro promedio móvil seguido por decimación por 16. Si el ruido de cuantización es blanco y no correlacionado, la mejora teórica de resolución por sobremuestreo es:

```text
bits_extra = 0.5 * log2(OSR)
bits_extra = 0.5 * log2(16) = 0.5 * 4 = 2 bits
```

Por tanto, un ADC ideal de 12 bits puede alcanzar una resolución efectiva teórica cercana a 14 bits. Esta mejora exige ruido suficiente para decorrelacionar la cuantización; en la práctica el ENOB depende del ruido analógico, alimentación, impedancia de fuente, linealidad del ADC ESP32 y layout.

## DSP: filtros notch IIR biquad en cascada

La salida final es de 500 SPS. El flujo filtrado aplica tres biquads notch en cascada para rechazar red eléctrica y armónicos:

- 50 Hz
- 100 Hz
- 150 Hz

Se eligió `Q = 35`: suficientemente estrecho para reducir distorsión del ECG, con bajo costo computacional y menor retardo de grupo que filtros FIR estrechos equivalentes. Los coeficientes se calculan una sola vez fuera del firmware y quedan fijos en `dsp_task.cpp`.

Para cada notch digital:

```text
ω0 = 2π f0 / Fs
α = sin(ω0) / (2Q)
H(z) = (b0 + b1 z^-1 + b2 z^-2) / (1 + a1 z^-1 + a2 z^-2)

b0 = 1
b1 = -2 cos(ω0)
b2 = 1
a0 = 1 + α
a1 = -2 cos(ω0)
a2 = 1 - α

Coeficientes normalizados:
B0 = b0/a0, B1 = b1/a0, B2 = b2/a0, A1 = a1/a0, A2 = a2/a0
```

Con `Fs = 500 Hz` y `Q = 35`:

| Notch | B0 | B1 | B2 | A1 | A2 |
|---|---:|---:|---:|---:|---:|
| 50 Hz | 0.991114 | -1.604644 | 0.991114 | -1.604644 | 0.982228 |
| 100 Hz | 0.982385 | -0.607183 | 0.982385 | -0.607183 | 0.964770 |
| 150 Hz | 0.973809 | 0.601883 | 0.973809 | 0.601883 | 0.947619 |

La implementación usa forma transpuesta directa II:

```text
y[n] = b0*x[n] + z1
z1 = b1*x[n] - a1*y[n] + z2
z2 = b2*x[n] - a2*y[n]
```

El flujo crudo decimado se guarda sin filtrado. El flujo filtrado resta primero el centro ADC aproximado de 2048 cuentas para trabajar alrededor de cero.

## Buffers circulares

Se mantienen dos buffers thread-safe de `int16_t`:

```text
500 SPS * 5 s = 2500 muestras
```

- Buffer crudo decimado.
- Buffer filtrado.

Los snapshots se copian en orden cronológico para responder comandos `GET_BUFFER_*`.

## TFT local

La TFT usa LovyanGFX, no TFT_eSPI. Se muestra una traza horizontal desplazada del ECG filtrado y el estado BLE. Solo se ven aproximadamente 1-2 segundos; no se dibujan los 5 segundos completos. La cola de display usa overwrite, por lo que la pantalla puede descartar frames sin bloquear ADC ni DSP.

## Protocolo BLE

Servidor BLE NimBLE:

```text
Device name: LilyGO-ECG
Service UUID:        0000ec00-0000-1000-8000-00805f9b34fb
Characteristic_Command: 0000ec01-0000-1000-8000-00805f9b34fb  Write / Write No Response
Characteristic_Data:    0000ec02-0000-1000-8000-00805f9b34fb  Notify / Read
```

Comandos ASCII desde PC hacia ESP32:

- `START_STREAM_RAW`
- `START_STREAM_FILTERED`
- `STOP_STREAM`
- `GET_BUFFER_RAW`
- `GET_BUFFER_FILTERED`
- `PING`

Las muestras se envían como `int16_t` little-endian por notificaciones BLE. El firmware solicita MTU 247 y empaqueta tantas muestras como permita el payload disponible. En desconexión se detiene el streaming, se marca BLE como desconectado y se reinicia advertising para reconexión.

## Aplicación Python

La GUI Tkinter + Bleak ofrece:

- Scan BLE
- Connect
- Disconnect
- Start Raw
- Start Filtered
- Get Buffer Raw
- Get Buffer Filtered
- Stop
- Export CSV
- Estado BLE
- Tasa de muestras
- Paquetes recibidos

La gráfica se actualiza a 20 FPS (`root.after(50, ...)`) y mantiene un buffer gráfico independiente de 10 segundos. La adquisición sigue siendo 500 SPS; la visualización no reduce la resolución recibida.

## Exportación CSV

`Export CSV` guarda todas las muestras recibidas con columnas:

```csv
timestamp,sample
```

El timestamp es tiempo Unix aproximado reconstruido al llegar cada paquete BLE. El contenido puede ser crudo o filtrado según el último comando usado.

## Notas de robustez

- ADC tiene la prioridad FreeRTOS más alta.
- BLE y TFT usan colas y no bloquean ADC.
- Las notificaciones BLE se agrupan para reducir overhead.
- El display puede perder frames sin perder muestras.
- Para señales clínicas reales se requieren aislamiento, seguridad eléctrica, validación médica y diseño IEC aplicable; este proyecto es de adquisición experimental, no dispositivo médico certificado.
