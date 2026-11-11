/*
 * Copyright (c) 2026 Pablo Lopez
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Zenith-Core standalone on Tiny Tapeout (4x2).
// Program memory (64 x 16 bit) and data RAM (16 B) are inside the chip.
// The program is loaded over UART (0xAA 0x55, count, instructions big-endian).
//
//   ui[0]      UART RX (loader)
//   uo[0]      UART TX
//   uo[1]      PWM
//   uo[2]      loader active (CPU held in reset while loading)
//   uo[7:3]    PC[4:0] (debug)
//   uio[7:0]   GPIO (out / in / direction, MMIO 0x80-0x82)

module tt_um_pablojlm_zenith (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  wire [7:0] gpio_out;
  wire [7:0] gpio_dir;
  wire       uart_tx;
  wire       pwm;
  wire       loading;
  wire [7:0] dbg_pc;

  microrv8_system #(
      .CLK_FREQ (10_000_000),
      .BAUD_RATE(115200)
  ) core (
      .clk          (clk),
      .rst_n        (rst_n),
      .gpio_in      (uio_in),
      .gpio_out     (gpio_out),
      .gpio_dir     (gpio_dir),
      .uart_rx_pin  (ui_in[0]),
      .uart_tx_pin  (uart_tx),
      .pwm_pin      (pwm),
      .debug_pc     (dbg_pc),
      .debug_state  (),
      .debug_instr  (),
      .loader_active(loading)
  );

  assign uo_out  = {dbg_pc[4:0], loading, pwm, uart_tx};
  assign uio_out = gpio_out;
  assign uio_oe  = gpio_dir;

  wire _unused = &{ena, ui_in[7:1], 1'b0};

endmodule

`default_nettype wire
