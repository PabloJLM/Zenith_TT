/*
 * Copyright (c) 2026 Pablo Lopez
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Zenith-Core on Tiny Tapeout.
//
// The chip holds only the CPU (cpu_core), an 8-bit PWM and the GPIO register.
// Program memory and data RAM live outside, in the RP2040 of the TT demo
// board, which also generates the clock and steps the CPU one cycle at a time.
//
// The CPU runs a fixed 6-state loop. Pins carry different information
// depending on the state (decoded from cpu_core.debug_state):
//
//   state     RP2040 -> chip (ui_in)        chip -> RP2040 (uio_out, "view")
//   FETCH  0  -                              mem_wdata (data of the last STORE)
//   WAIT   1  instruction high byte          pc[7:0]
//   DECODE 2  instruction low byte           gpio_out (value of the last OUT)
//   EXEC   3  -                              pc[7:0]
//   MEM    4  -                              pc[7:0]
//   WB     5  data read (LOAD only)          mem_addr (LOAD/STORE address)

module tt_um_pablojlm_zenith (
    input  wire [7:0] ui_in,    // Dedicated inputs: instruction byte / load data
    output wire [7:0] uo_out,   // Dedicated outputs: GPIO[6:0] and PWM
    input  wire [7:0] uio_in,   // IOs: Input path (unused)
    output wire [7:0] uio_out,  // IOs: Output path (view bus)
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock (from the RP2040)
    input  wire       rst_n     // reset_n - low to reset
);

  localparam [2:0] S_FETCH  = 3'd0;
  localparam [2:0] S_WAIT   = 3'd1;
  localparam [2:0] S_DECODE = 3'd2;
  localparam [2:0] S_WB     = 3'd5;

  wire [8:0]  pc;
  wire [7:0]  mem_addr;
  wire [7:0]  mem_wdata;
  wire        mem_we;
  wire        mem_re;
  wire [7:0]  gpio_out;
  wire [7:0]  dbg_pc;
  wire [7:0]  dbg_state;
  wire [15:0] dbg_instr;

  wire [2:0] st = dbg_state[2:0];

  // The instruction arrives in two bytes over ui_in: high byte in WAIT
  // (stored here), low byte in DECODE (used directly).
  reg [7:0] instr_hi;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)              instr_hi <= 8'd0;
    else if (st == S_WAIT)   instr_hi <= ui_in;
  end

  cpu_core cpu (
      .clk           (clk),
      .rst_n         (rst_n),
      .pc_out        (pc),
      .instruction_in({instr_hi, ui_in}),
      .mem_addr      (mem_addr),
      .mem_wdata     (mem_wdata),
      .mem_rdata     (ui_in),
      .mem_we        (mem_we),
      .mem_re        (mem_re),
      .gpio_out      (gpio_out),
      .debug_pc      (dbg_pc),
      .debug_state   (dbg_state),
      .debug_instr   (dbg_instr)
  );

  // On-chip PWM at MMIO 0x85 (duty), 0x86 (ctrl), 0x87 (prescaler).
  // Other addresses are seen by the RP2040 through the view bus.
  wire       pwm_pin;
  wire [7:0] pwm_rd;

  pwm_8bit pwm (
      .clk          (clk),
      .rst_n        (rst_n),
      .mmio_addr    (mem_addr),
      .mmio_data_in (mem_wdata),
      .mmio_data_out(pwm_rd),
      .mmio_we      (mem_we),
      .mmio_re      (mem_re),
      .pwm_out      (pwm_pin)
  );

  // View bus: what the RP2040 reads, selected by CPU state.
  reg [7:0] view;
  always @(*) begin
    case (st)
      S_FETCH:  view = mem_wdata;
      S_DECODE: view = gpio_out;
      S_WB:     view = mem_addr;
      default:  view = pc[7:0];
    endcase
  end

  assign uo_out  = {pwm_pin, gpio_out[6:0]};
  assign uio_out = view;
  assign uio_oe  = 8'hFF;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in, dbg_pc, dbg_instr, dbg_state[7:3], pwm_rd, pc[8], 1'b0};

endmodule
