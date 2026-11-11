# Zenith-Core v1 — 1x1 tile (TTSKY26d)

Resultados del flujo oficial de Tiny Tapeout (GitHub Actions), commit en `main`.

| Métrica | Valor |
|---|---|
| Tamaño | 1x1 (167 x 108 µm) |
| Utilización | 82.047 % |
| Celdas (sin fill/tap) | 1221 |
| Flip-flops | 185 |
| Longitud de cable | 69,533 µm |
| Precheck | 15/15 OK |
| gl_test (gate-level, cocotb) | 3/3 OK |

## Arquitectura
CPU Zenith (16 bits de instrucción, 8 regs, ALU 8 bits) + PWM. La memoria de programa y datos
vive fuera del chip (RP2040), en modo lockstep: el RP2040 genera el reloj, avanza un ciclo y lee
el bus de observación `uio` (VIEW), manejando `ui_in` con instrucción/dato.

## Resultados gate-level (netlist post-síntesis)
- `gl_fibonacci_gpio.png`: GPIO = 1,2,3,5,8,13,21,34,55,89. Los dos últimos valores (144, 233) aparecen
  como 16 y 105 porque el GPIO del chip es de 7 bits (144 mod 128 = 16, 233 mod 128 = 105).
- `gl_pwm.png`: periodo 2.56 ms, alto 1.28 ms → duty 0.50.
- `gl_viewbus.png`: bus `uio` multiplexado por estado de la FSM.
- `gds_render.png`: layout.
- `results.xml`: reporte de cocotb (3 tests, 0 fallos).

Nota: los tiempos están en el reloj del modelo de prueba (el chip no tiene frecuencia fija; clock_hz = 0).
