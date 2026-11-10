<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Zenith-Core is a small 8-bit CPU inspired by RISC-V: 16-bit instructions, 8 registers (r0 is always 0), an 8-bit ALU, 4-bit signed immediates and a 6-state FSM (FETCH, WAIT, DECODE, EXEC, MEM, WB), so every instruction takes 6 clock cycles. The ISA, an assembler and an IDE are in the main project repository (PabloJLM/Zenith-Core).

To fit in one tile, the chip contains only the CPU, an 8-bit PWM and the GPIO output register. Program memory and data RAM are **outside the chip**: the RP2040 of the Tiny Tapeout demo board generates the clock, steps the CPU one cycle at a time and answers every memory access. Because the RP2040 holds the clock, it can answer in the same cycle, and loading a new program is just writing a new array in the RP2040.

The CPU FSM is a fixed 6-cycle loop that starts at FETCH on the first clock after reset. The pins carry different data depending on the state:

| State | Cycle | RP2040 drives `ui[7:0]` | Chip drives `uio[7:0]` (view bus) |
|-------|-------|-------------------------|-----------------------------------|
| FETCH  | 0 | -                          | `mem_wdata`: data of the last STORE |
| WAIT   | 1 | instruction high byte      | `pc[7:0]`: address of the instruction |
| DECODE | 2 | instruction low byte       | `gpio_out`: value of the last OUT |
| EXEC   | 3 | -                          | `pc[7:0]` |
| MEM    | 4 | -                          | `pc[7:0]` |
| WB     | 5 | read data (only for LOAD)  | `mem_addr`: address of LOAD / STORE |

The RP2040 knows whether the instruction is a LOAD or a STORE from the opcode it served (bits 15:13: 010 = LOAD, 011 = STORE, 110 = OUT), so no extra read/write pins are needed. A STORE is completed one cycle later, in the next FETCH, when `mem_wdata` appears on the view bus.

Program counter: only `pc[7:0]` is exported, so programs are limited to 256 words.

Data memory map (the RP2040 serves everything except the PWM):

| Address | Where | Function |
|---------|-------|----------|
| 0x00-0x7F | RP2040 | RAM |
| 0x83 | RP2040 | UART TX, virtual: the RP2040 forwards the byte to its USB serial port |
| 0x85 | chip | PWM duty (write) |
| 0x86 | chip | PWM control: bit 0 enable, bit 1 invert (write) |
| 0x87 | chip | PWM prescaler (write; 0 means 255) |

The `OUT` instruction writes the GPIO register. `uo[6:0]` show bits 6:0 of that register. Bit 7 is visible through the view bus (DECODE state of the next instruction), because `uo[7]` is used by the PWM.

## How to test

The RP2040 must run the protocol of the table above in lockstep: for each clock cycle, set the clock low, read the view bus, drive `ui[7:0]` if needed, then pulse the clock. A reference model of the RP2040 is in `test/test.py`; it runs a Fibonacci program (prints 0, 1, 1, 2, 3, 5, 8, ..., 233 on the GPIO register), a STORE/LOAD round trip and the PWM at 50% duty. It talks to the chip only through the pins, so it can also be used on the gate-level netlist.

Programs are assembled with `tools/assembler.py` from the Zenith-Core repository; the `.hex` file has one 16-bit word per line.

## External hardware

The RP2040 on the Tiny Tapeout demo board (clock, program memory, data RAM and virtual UART). Optional: LEDs on `uo[7:0]` to watch the GPIO and the PWM.
