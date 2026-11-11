`default_nettype none
// Data memory + MMIO bridge (Tiny Tapeout version, 16 B RAM).
//   0x00-0x0F : RAM (addr[3:0]); 0x80-0xFF : MMIO
//
// Difference with Micro/rtl/data_memory.v: the CPU samples mem_rdata at the
// same clock edge where the old version registered data_out, so LOAD returned
// stale data (0 after reset). Here the read path is combinational and the
// MMIO bus is a pass-through of the CPU bus, valid during the WB state.

module data_memory (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  addr,
    input  wire [7:0]  data_in,
    input  wire        we,
    input  wire        re,
    output wire [7:0]  data_out,

    output wire [7:0]  mmio_addr,
    output wire [7:0]  mmio_data_wr,
    input  wire [7:0]  mmio_data_rd,
    output wire        mmio_we,
    output wire        mmio_re
);

    reg [7:0] ram [0:15];

    wire is_mmio = addr[7];

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1)
                ram[i] <= 8'h00;
        end else if (we && !is_mmio) begin
            ram[addr[3:0]] <= data_in;
        end
    end

    assign mmio_addr    = addr;
    assign mmio_data_wr = data_in;
    assign mmio_we      = we & is_mmio;
    assign mmio_re      = re & is_mmio;

    assign data_out = is_mmio ? mmio_data_rd : ram[addr[3:0]];

    wire _unused = &{re, 1'b0};

endmodule

`default_nettype wire
