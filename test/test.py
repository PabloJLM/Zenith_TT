# SPDX-FileCopyrightText: © 2026 Pablo Lopez
# SPDX-License-Identifier: Apache-2.0
# Standalone Zenith-Core: the test loads the program over UART (ui[0]) and
# observes the chip only through its pins (also valid on the gate-level netlist).

import cocotb
from cocotb.triggers import Timer

CLK_NS = 100            # 10 MHz
BIT_CYC = 86            # CLK_FREQ // BAUD (10e6 // 115200)

FIBO = [0x0400, 0x0801, 0x1007, 0x3240, 0xC080, 0x2CA0,
        0x2500, 0x2980, 0x120F, 0x9001, 0xE004, 0xE00B]
FIBO_OUT = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
MEM = [0x0405, 0x0803, 0x6500, 0x4D00, 0xC180, 0xE005]
PWM = [0x0401, 0x04D7, 0x0885, 0x6500, 0x0C01,
       0x0902, 0x6D00, 0x090F, 0x6D00, 0xE009]
# r1 = 'A'; r2 = 0x83; mem[r2] = r1 (UART_TX); loop
UART = [0x0401, 0x04D6, 0x0481, 0x0801, 0x0957, 0x0903, 0x6500, 0xE007]


async def cycles(dut, n, log=None):
    for _ in range(n):
        dut.clk.value = 0
        await Timer(CLK_NS // 2, unit="ns")
        dut.clk.value = 1
        await Timer(CLK_NS // 2, unit="ns")
        if log is not None:
            log.append((int(dut.uo_out.value), int(dut.uio_out.value)))


async def reset(dut):
    dut.ena.value = 1
    dut.ui_in.value = 1      # UART idle high
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    dut.clk.value = 0
    await cycles(dut, 5)
    dut.rst_n.value = 1
    await cycles(dut, 5)


async def send_byte(dut, b):
    for bit in [0] + [(b >> i) & 1 for i in range(8)] + [1]:
        dut.ui_in.value = bit
        await cycles(dut, BIT_CYC)


async def load(dut, prog, log=None):
    for b in [0xAA, 0x55, 0x00, len(prog)]:
        await send_byte(dut, b)
    for w in prog:
        await send_byte(dut, w >> 8)
        await send_byte(dut, w & 0xFF)
    await cycles(dut, 400, log)   # settle; CPU is released inside this window
    assert (int(dut.uo_out.value) >> 2) & 1 == 0, "CPU should run after the load"


def dedupe(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x:
            out.append(x)
    return out


@cocotb.test()
async def test_fibonacci(dut):
    await reset(dut)
    log = []
    await load(dut, FIBO, log)
    await cycles(dut, 1500, log)
    vals = [u for _, u in log]
    seq = [v for v in dedupe(vals) if v != 0]
    dut._log.info(f"GPIO (uio): {seq}")
    assert seq == FIBO_OUT, f"expected {FIBO_OUT}, got {seq}"
    assert int(dut.uio_oe.value) == 0xFF


@cocotb.test()
async def test_store_load(dut):
    await reset(dut)
    log = []
    await load(dut, MEM, log)
    await cycles(dut, 200, log)
    dut._log.info(f'MEM tail uo/uio: {[(hex(a),hex(b)) for a,b in dedupe(log)][-8:]}')
    assert log[-1][1] == 5, f"LOAD should return 5, got {log[-1][1]}"


@cocotb.test()
async def test_pwm(dut):
    await reset(dut)
    await load(dut, PWM)
    log = []
    await cycles(dut, 12000, log)
    pw = [(u >> 1) & 1 for u, _ in log[2000:]]
    duty = sum(pw) / len(pw)
    dut._log.info(f"PWM duty {duty:.3f}")
    assert 0.40 < duty < 0.60


@cocotb.test()
async def test_uart_tx(dut):
    await reset(dut)
    log = []
    await load(dut, UART, log)
    await cycles(dut, 2500, log)
    tx = [u & 1 for u, _ in log]
    start = next(i for i in range(1, len(tx)) if tx[i - 1] == 1 and tx[i] == 0)
    byte = 0
    for k in range(8):
        byte |= tx[start + BIT_CYC // 2 + BIT_CYC * (k + 1)] << k
    dut._log.info(f"UART TX byte: {byte:#x}")
    assert byte == 0x41
