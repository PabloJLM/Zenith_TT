# SPDX-FileCopyrightText: © 2026 Pablo Lopez
# SPDX-License-Identifier: Apache-2.0

# The test plays the role of the RP2040 on the TT demo board: it generates
# the clock one cycle at a time, serves the program and the data RAM, and
# reads the CPU through the pins only (so it also works on the gate-level
# netlist).

import cocotb
from cocotb.triggers import Timer

HALF = 5  # us

# Program: Fibonacci (programs/fibo.hex)
FIBO = [0x0400, 0x0801, 0x1007, 0x3240, 0xC080, 0x2CA0,
        0x2500, 0x2980, 0x120F, 0x9001, 0xE004, 0xE00B]
FIBO_OUT = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

# Program: STORE then LOAD through the external RAM
#   r1=5; r2=3; mem[r2]=r1; r3=mem[r2]; OUT r3; JUMP self
MEM = [0x0405, 0x0803, 0x6500, 0x4D00, 0xC180, 0xE005]

# Program: PWM on-chip, duty 128, prescaler 1, enable
#   r1=1<<7; r2=r1+5 (0x85); mem[r2]=r1; r3=1; r2+=2 (0x87); mem[r2]=r3;
#   r2-=1 (0x86); mem[r2]=r3; JUMP self
PWM = [0x0401, 0x04D7, 0x0885, 0x6500, 0x0C01,
       0x0902, 0x6D00, 0x090F, 0x6D00, 0xE009]

OP_LOAD, OP_STORE, OP_OUT = 2, 3, 6


class Rp2040:
    """Lockstep model of the RP2040: clock, program memory, data RAM."""

    def __init__(self, dut, program):
        self.dut = dut
        self.prog = program
        self.ram = [0] * 128
        self.gpio_log = []
        self.pwm_samples = []
        self.instr = 0
        self.prev_op = None
        self.pending_store = None
        self.cyc = 0

    async def reset(self):
        dut = self.dut
        dut.ena.value = 1
        dut.ui_in.value = 0
        dut.uio_in.value = 0
        dut.clk.value = 0
        dut.rst_n.value = 0
        await Timer(HALF, unit="us")
        for _ in range(4):
            dut.clk.value = 1
            await Timer(HALF, unit="us")
            dut.clk.value = 0
            await Timer(HALF, unit="us")
        dut.rst_n.value = 1
        await Timer(HALF, unit="us")

    async def step(self):
        dut = self.dut
        st = self.cyc % 6
        if st == 0:
            if self.pending_store is not None:
                self.ram[self.pending_store & 0x7F] = int(dut.uio_out.value)
                self.pending_store = None
        elif st == 1:
            pc = int(dut.uio_out.value)
            self.instr = self.prog[pc] if pc < len(self.prog) else 0xE000 | pc
            dut.ui_in.value = self.instr >> 8
        elif st == 2:
            dut.ui_in.value = self.instr & 0xFF
            if self.prev_op == OP_OUT:
                self.gpio_log.append(int(dut.uio_out.value))
        elif st == 5:
            op = self.instr >> 13
            if op == OP_LOAD:
                addr = int(dut.uio_out.value)
                dut.ui_in.value = self.ram[addr] if addr < 0x80 else 0
            elif op == OP_STORE:
                addr = int(dut.uio_out.value)
                if addr < 0x80:
                    self.pending_store = addr
        dut.clk.value = 1
        await Timer(HALF, unit="us")
        dut.clk.value = 0
        await Timer(HALF, unit="us")
        if st == 5:
            self.prev_op = self.instr >> 13
        self.pwm_samples.append(int(dut.uo_out.value) >> 7)
        self.cyc += 1

    async def run(self, cycles):
        for _ in range(cycles):
            await self.step()


@cocotb.test()
async def test_fibonacci(dut):
    rp = Rp2040(dut, FIBO)
    await rp.reset()
    await rp.run(6 * 130)
    dut._log.info(f"GPIO values: {rp.gpio_log[:14]}")
    assert rp.gpio_log[:14] == FIBO_OUT


@cocotb.test()
async def test_store_load(dut):
    rp = Rp2040(dut, MEM)
    await rp.reset()
    await rp.run(6 * 12)
    dut._log.info(f"RAM[3] = {rp.ram[3]}, GPIO values: {rp.gpio_log[:2]}")
    assert rp.ram[3] == 5
    assert rp.gpio_log[0] == 5


@cocotb.test()
async def test_pwm(dut):
    rp = Rp2040(dut, PWM)
    await rp.reset()
    await rp.run(6 * 14)           # configure duty, prescaler, enable
    rp.pwm_samples.clear()
    await rp.run(1024)             # four full PWM periods
    high = sum(rp.pwm_samples) / len(rp.pwm_samples)
    dut._log.info(f"PWM duty measured: {high:.2f}")
    assert 0.40 <= high <= 0.60
