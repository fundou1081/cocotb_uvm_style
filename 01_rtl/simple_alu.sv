// 01_rtl: Simple ALU for testing
module simple_alu (
    input         clk,
    input         rst_n,
    input  [7:0] a,
    input  [7:0] b,
    input  [2:0]  op,    // 000=add, 001=sub, 010=and, 011=or, 100=xor
    input         valid,
    output [7:0] result,
    output        ready
);
    reg ready_r;
    assign ready = ready_r;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 8'h0;
            ready_r <= 1'b1;
        end else if (valid && ready_r) begin
            ready_r <= 1'b0;
            case (op)
                3'b000: result <= a + b;
                3'b001: result <= a - b;
                3'b010: result <= a & b;
                3'b011: result <= a | b;
                3'b100: result <= a ^ b;
                default: result <= 8'h0;
            endcase
            ready_r <= 1'b1;
        end
    end
endmodule
