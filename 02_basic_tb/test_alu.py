"""
02_basic_tb: 基础 cocotb testbench
"""
import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock

@cocotb.test()
async def basic_test(dut):
    """基础测试"""
    # 启动时钟
    cocotb.start_await(Clock(dut.clk, 10, 'ns').start())
    
    # 重置
    dut.rst_n <= 0
    await Timer(50, 'ns')
    dut.rst_n <= 1
    await Timer(50, 'ns')
    
    # 测试加法
    dut.a <= 5
    dut.b <= 3
    dut.op <= 0  # add
    dut.valid <= 1
    await Timer(10, 'ns')
    dut.valid <= 0
    
    await Timer(30, 'ns')
    print(f"Result: {dut.result.value}")
    assert dut.result.value == 8
