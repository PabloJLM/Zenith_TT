<!---
This file is used to generate your project datasheet.
-->

## How it works

Zenith-Core is a small 8-bit, RISC-V-inspired microcontroller. This version is standalone: the CPU (16-bit
instructions, 8 registers, 8-bit ALU, 6-state FSM), the program memory (64 x 16 bit), the data RAM (16 bytes),
a UART loader, a UART transmitter, an 8-bit PWM and an 8-bit GPIO port are all inside the chip.

The program is loaded over UART at 115200 baud with a 10 MHz clock. While the loader is receiving, the CPU is held in reset.

Loader protocol (bytes): `0xAA 0x55`, count high byte, count low byte (count <= 64), then count instructions
as 2 bytes each, big-endian. When the last instruction arrives the CPU starts from address 0.

Data memory map (LOAD/STORE):

| Address | Register |
|---|---|
| 0x00-0x0F | RAM (16 B) |
| 0x80 | GPIO_OUT |
| 0x81 | GPIO_IN (reads the uio pins) |
| 0x82 | GPIO_DIR (1 = output, reset value 0xFF) |
| 0x83 | UART_TX (write a byte) |
| 0x84 | UART_STAT (bit 0 = busy) |
| 0x85 | PWM_DUTY |
| 0x86 | PWM_CTRL (bit 0 = enable) |
| 0x87 | PWM_PRESCALER |

The `OUT` instruction writes the GPIO output register directly, so a program can show an 8-bit value on `uio`
without touching GPIO_DIR.

Pins: `ui[0]` UART RX, `uo[0]` UART TX, `uo[1]` PWM, `uo[2]` high while the loader is receiving, `uo[7:3]` the
low 5 bits of the program counter, `uio[7:0]` GPIO.

## How to test

1. Apply the 10 MHz clock and release reset.
2. Send a program with the loader protocol on `ui[0]` (for example the Fibonacci program in `programs/fibo.hex`).
3. Watch `uio[7:0]`: the Fibonacci program shows 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233.

The cocotb tests in `test/` do exactly this (Fibonacci, STORE/LOAD, PWM, UART TX).

## External hardware

A USB-UART adapter (or the RP2040 of the demo board) to send the program. LEDs on `uio` and `uo` are optional.
