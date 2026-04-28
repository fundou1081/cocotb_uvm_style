"""
05_agent: UVM Agent
=====================

## UVM Agent 机制对照

| UVM (SystemVerilog)         | cocotb Python 实现      |
|-------------------------|---------------------|
| `uvm_agent`               | `UVMAgent` class     |
| `is_active`              | `is_active`        |
| `driver`                 | `self.driver`      |
| `monitor`                | `self.monitor`    |
| `sequencer`              | `self.sequencer`   |
| `get_is_active()`         | `is_active` getter |
| `get_driver()`           | `driver` getter   |
| `get_monitor()`         | `monitor` getter  |

## Agent 结构

```systemverilog
// SV UVM
class alu_agent extends uvm_agent;
  `uvm_component_utils(alu_agent)
  
  alu_driver     driver;
  alu_monitor   monitor;
  alu_sequencer sequencer;
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    // 创建子组件
    driver     = alu_driver::type_id::create("driver", this);
    monitor    = alu_monitor::type_id::create("monitor", this);
    sequencer  = alu_sequencer::type_id::create("sequencer", this);
  endfunction
  
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // 连接 driver 到 sequencer
    driver.seq_item_port.connect(sequencer.seq_item_export);
  endfunction
endclass
```

```python
# cocotb
class ALUAgent(UVMAgent):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
    
    def build_phase(self):
        # 创建子组件
        self.driver = ALUDriver("driver", self)
        self.monitor = ALUMonitor("monitor", self)
        self.sequencer = ALUSequencer("sequencer", self)
    
    def connect_phase(self):
        # 连接 driver 到 sequencer
        self.driver.sequencer = self.sequencer
```

## Agent 配置

```systemverilog
// SV: 配置 is_active
uvm_config_int::set(this, "*.driver", "is_active", UVM_ACTIVE);
```

```python
# cocotb
self.is_active = True  # 或 UVM_ACTIVE
```

## is_active 模式

| 模式 | 说明 | Driver/Monitor |
|-----|-----|---------------|
| UVM_ACTIVE | 主动模式 | Driver + Monitor |
| UVM_PASSIVE | 被动模式 | 仅 Monitor |
"""
from cocotb.triggers import Timer, RisingEdge
from typing import Optional, List
import sys
sys.path.insert(0, '.')
from 03_comp.uvm_component import UVMComponent, UVMMonitor
from 04_seq.uvm_seq import UVMSequencer, UVMSequenceItem


# ================== Agent 配置常量 ==================
class UVMActive:
    """Agent 活跃状态常量"""
    UVM_ACTIVE = True
    UVM_PASSIVE = False


# ================== Agent ==================
class UVMAgent(UVMComponent):
    """
    UVM Agent
    
    对应 SV UVM: `uvm_agent`
    
    ## 职责
    1. 组装 Driver + Sequencer + Monitor
    2. 管理 is_active 状态
    3. 连接组件间通信
    
    ## 结构
    ```systemverilog
    // SV
    agent
     +-- driver (通过 sequencer 连接)
     +-- sequencer
     +-- monitor (通过 analysis_port 连接 scoreboard)
    ```
    
    ```python
    # cocotb
    agent
     +-- driver (连接到 sequencer)
     +-- sequencer
     +-- monitor (输出到 scoreboard)
    ```
    """
    
    def __init__(self, name: str, parent: Optional[UVMComponent] = None,
                 is_active: bool = True):
        """
        构造函数
        
        Args:
            name: Agent 名称
            parent: 父组件
            is_active: 是否主动模式
                - True (UVM_ACTIVE): 包含 Driver + Sequencer
                - False (UVM_PASSIVE): 仅 Monitor
        """
        super().__init__(name, parent)
        self.is_active = is_active
        self.driver = None
        self.monitor = None
        self.sequencer = None
    
    def build_phase(self):
        """
        构建 Agent - 对应 SV `build_phase()`
        
        创建子组件
        """
        if self.is_active:
            # 主动模式：创建 Driver + Sequencer
            self.vlog.info(f"{self.name} [ACTIVE]")
            # 子类实现具体创建
        else:
            # 被动模式：仅 Monitor
            self.vlog.info(f"{self.name} [PASSIVE]")
    
    def connect_phase(self):
        """
        连接阶段 - 对应 SV `connect_phase()`
        
        连接 Driver <-> Sequencer
        """
        if self.is_active and self.driver and self.sequencer:
            self.driver.sequencer = self.sequencer
            self.vlog.info(f"{self.name}: driver -> sequencer connected")


# ================== 具体 Agent 示例 ==================
class ALUDriver(UVMComponent):
    """
    ALU Driver 示例
    
    对应 SV: `class alu_driver extends uvm_driver#(alu_seq_item);`
    """
    
    def __init__(self, name: str, parent: Optional[UVMComponent] = None,
                 dut=None):
        super().__init__(name, parent)
        self.sequencer = None
        self.dut = dut
    
    async def drive_item(self, item):
        """驱动 item 到 DUT"""
        if self.dut:
            self.dut.a <= item.a
            self.dut.b <= item.b
            self.dut.op <= item.op
            self.dut.valid <= 1
            await RisingEdge(self.dut.clk)
            await Timer(10, 'ns')
            self.dut.valid <= 0
    
    async def run_phase(self):
        """主循环"""
        while True:
            if self.sequencer:
                item = await self.sequencer.get_next_item()
                await self.drive_item(item)
                self.sequencer.item_done()


class ALUMonitor(UVMMonitor):
    """
    ALU Monitor 示例
    """
    
    def __init__(self, name: str, parent: Optional[UVMComponent] = None,
                 dut=None):
        super().__init__(name, parent)
        self.dut = dut
    
    async def run_phase(self):
        """监控 DUT"""
        while True:
            if self.dut:
                await RisingEdge(self.dut.clk)
                if self.dut.valid.value:
                    # 采样
                    item = UVMSequenceItem()
                    item.a = self.dut.a.value
                    item.result = self.dut.result.value
                    # 发送到 analysis port
                    self.ap_write(item)


class ALUSequencer(UVMSequencer):
    """ALU Sequencer"""
    pass
