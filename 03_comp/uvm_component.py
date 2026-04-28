"""
03_comp: UVM Component 基类
=========================

## UVM vs cocotb 对照表

| UVM (SystemVerilog)              | cocotb Python 实现              |
|------------------------------|-----------------------------|
| `uvm_component`                | `UVMComponent` class          |
| `uvm_driver`                  | `UVMDriver` class           |
| `uvm_monitor`                | `UVMMonitor` class        |
| `uvm_scoreboard`              | `UVMScoreboard` class      |
| `uvm_sequencer`              | `UVMSequencer` class     |
| `uvm_agent`                  | `UVMAgent` class        |
| `uvm_env`                    | `UVMEnvironment` class   |
| `uvm_test`                   | `UVMTest` class         |
| `build_phase()`                | `__init__()` + `build()` |
| `connect_phase()`              | `connect_phase()`         |
| `run_phase()`                | `run_phase()` async    |
| `uvm_info/warning/error()`   | `logger.info/warn/error()` |
| `uvm_config_db#(...)::set` | `cocotb.config.set`    |
| `uvm_config_db#(...)::get` | `cocotb.config.get`    |

## Phase 机制对比

UVM Phase:
```
build_phase     -> connect_phase -> run_phase -> report_phase -> final_phase
   |                |             |            |              |
 构造子         连接组件        运行       报告结果       清理
```

cocotb:
```
__init__()  ->  connect_phase()  ->  run_phase()  ->  cleanup
   构造子          连接            运行(async)      清理
```

## 日志级别对比

| UVM 日志级别     | cocotb 日志        | 数值 |
|---------------|-----------------|-----|
| UVM_FATAL    | FATAL/CRITICAL   | 50  |
| UVM_ERROR   | ERROR          | 40  |
| UVM_WARNING | WARNING        | 30  |
| UVM_INFO   | INFO          | 20  |
| UVM_DEBUG  | DEBUG         | 10  |

"""
import cocotb
from cocotb.triggers import Timer
from typing import Optional, Any
import logging

# ================== UVM Reporter ==================
class UVMReporter:
    """
    UVM 风格日志 reporter
    
    等 SV UVM 中的 `uvm_info()`, `uvm_warning()`, `uvm_error()`, `uvm_fatal()`
    
    ## 用法
    ```python
    # 等同于 uvm_info("COMP", "message", UVM_INFO)
    logger.info("message")
    
    # 等同于 uvm_warning("COMP", "message", UVM_WARNING)  
    logger.warning("message")
    
    # 等同于 uvm_error("COMP", "message", UVM_ERROR)
    logger.error("message")
    
    # 等同于 uvm_fatal("COMP", "message", UVM_FATAL)
    logger.fatal("message")
    ```
    """
    # UVM 日志级别常量
    UVM_NONE   = logging.NOTSET      # 0
    UVM_DEBUG  = logging.DEBUG     # 10
    UVM_INFO   = logging.INFO      # 20
    UVM_INFO2  = 15              # UVM_MEDIUM
    UVM_WARNING = logging.WARNING    # 30
    UVM_ERROR  = logging.ERROR     # 40
    UVM_FATAL = logging.CRITICAL # 50
    
    @staticmethod
    def log(level: int, msg: str):
        """输出日志 - 对应 uvm_info/warning/error/fatal"""
        logging.log(level, msg)


# ================== UVM Component ==================
class UVMComponent:
    """
    UVM Component 基类
    
    对应 SV UVM: `uvm_component`
    
    ## 基本结构
    ```systemverilog
    // SV UVM
    class my_agent extends uvm_agent;
      `uvm_component_utils(my_agent)
      
      function new(string name, uvm_component parent);
        super.new(name, parent);
      endfunction
      
      function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        // 创建子组件
      endfunction
      
      task run_phase(uvm_phase phase);
        // 运行
      endtask
    endclass
    ```
    
    ```python
    # cocotb Python
    class MyAgent(UVMComponent):
        def __init__(self, name, parent=None):
            super().__init__(name, parent)
        
        def build_phase(self):
            # 创建子组件
            pass
        
        async def run_phase(self):
            # 运行
            pass
    ```
    """
    
    def __init__(self, name: str, parent: Optional['UVMComponent'] = None):
        """
        构造函数 - 对应 UVM `new()`
        
        Args:
            name: 组件名称 (对应 SV `super.new(name, parent)`)
            parent: 父组件 (对应 SV `uvm_component parent`)
        """
        self.name = name
        self.parent = parent
        self.children = []
        self.vlog = logging.getLogger(name)
        self.vlog.setLevel(logging.DEBUG)
        
        if parent:
            parent.children.append(self)
    
    def build_phase(self):
        """
        build 阶段 - 对应 SV `build_phase(uvm_phase phase)`
        
        在此阶段创建子组件、配置等
        相当于 Python 的 `__init__` + 构造逻辑
        """
        self.vlog.info(f"{self.name}.build_phase()")
    
    def connect_phase(self):
        """
        connect 阶段 - 对应 SV `connect_phase(uvm_phase phase)`
        
        在此阶段连接组件间的端口、注册回调等
        build 之后、run 之前调用
        """
        self.vlog.info(f"{self.name}.connect_phase()")
    
    async def run_phase(self):
        """
        run 阶段 - 对应 SV `task run_phase(uvm_phase phase)`
        
        这是异步任务，对应 SV 的 task
        """
        self.vlog.info(f"{self.name}.run_phase()")
        await Timer(1, 'ns')  # 避免死循环
    
    async def get_parent(self):
        """获取父组件 - 对应 SV `get_parent()""""
        return self.parent


# ================== UVM Driver ==================
class UVMDriver(UVMComponent):
    """
    UVM Driver
    
    对应 SV UVM: `uvm_driver#(...)`
    
    ## 结构对比
    ```systemverilog
    // SV UVM
    class alu_driver extends uvm_driver #(alu_seq_item);
      `uvm_component_utils(alu_driver)
      
      virtual task drive(alu_seq_item req);
        // 驱动接口
      endtask
      
      virtual task run_phase(uvm_phase phase);
        while (1) begin
          seq_item_port.get_next_item(req);
          drive(req);
          seq_item_port.item_done();
        end
      endtask
    endclass
    ```
    
    ```python
    # cocotb
    class ALUDriver(UVMDriver):
        async def drive(self, item):
            # 驱动到 DUT
            self.dut.a <= item.a
            self.dut.b <= item.b
            self.dut.op <= item.op
            self.dut.valid <= 1
            await Timer(10, 'ns')
            self.dut.valid <= 0
        
        async def run_phase(self):
            while True:
                item = await self.seq_item_port.get_next_item()
                await self.drive(item)
    ```
    
    ## Driver 通信机制
    - SV: `seq_item_port.get_next_item(req)` / `item_done()`
    - Python: `await sequencer.get_next_item()`
    """
    
    def __init__(self, name: str, parent: Optional['UVMComponent'] = None):
        super().__init__(name, parent)
        self.seq_item_port = None  # Sequencer 连接端
    
    async def drive(self, item):
        """驱动 sequence item - 对应 SV `drive(req)`"""
        pass
    
    async def run_phase(self):
        """主循环 - 对应 SV `run_phase`"""
        self.vlog.info(f"{self.name} waiting for sequence items")


# ================== UVM Monitor ==================
class UVMMonitor(UVMComponent):
    """
    UVM Monitor
    
    对应 SV UVM: `uvm_monitor`
    
    ## 结构对比
    ```systemverilog
    // SV UVM
    class alu_monitor extends uvm_monitor;
      `uvm_component_utils(alu_monitor)
      
      uvm_analysis_port #(alu_seq_item) ap;
      
      virtual task run_phase(uvm_phase phase);
        forever begin
          @(posedge vif.clk);
          if (vif.valid) begin
            alu_seq_item req = alu_seq_item::type_id::create("req");
            req.a = vif.a;
            req.result = vif.result;
            ap.write(req);
          end
        end
      endtask
    endclass
    ```
    
    ```python
    # cocotb  
    class ALUMonitor(UVMMonitor):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.ap = []  # analysis port
        
        async def run_phase(self):
            while True:
                await RisingEdge(self.dut.clk)
                if self.dut.valid.value:
                    item = ALUSeqItem()
                    item.a = self.dut.a.value
                    item.result = self.dut.result.value
                    self.ap_write(item)
        
        def ap_write(self, item):
            for port in self.ap:
                port.write(item)
    ```
    
    ## Monitor 端口
    - SV: `uvm_analysis_port #(T) ap;`
    - Python: `self.ap = []` (analysis port 列表)
    """
    
    def __init__(self, name: str, parent: Optional['UVMComponent'] = None):
        super().__init__(name, parent)
        self.ap = []  # Analysis port 列表
    
    async def run_phase(self):
        """监控 DUT - 对应 SV `run_phase`"""
        pass
    
    def ap_write(self, item):
        """写Analysis Port - 对应 SV `ap.write(req)`"""
        for port in self.ap:
            port.write(item)


# ================== UVM Scoreboard ==================
class UVMScoreboard(UVMComponent):
    """
    UVM Scoreboard
    
    对应 SV UVM: `uvm_scoreboard`
    
    ## 结构对比
    ```systemverilog
    // SV UVM
    class alu_scoreboard extends uvm_scoreboard;
      `uvm_component_utils(alu_scoreboard)
      
      uvm_analysis_imp #(alu_seq_item, alu_scoreboard) expected_imp;
      uvm_analysis_imp #(alu_seq_item, alu_scoreboard) actual_imp;
      
      function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        expected_imp = new("expected_imp", this);
        actual_imp = new("actual_imp", this);
      endfunction
      
      function void write_expected(alu_seq_item req);
        // 存储期望值
      endfunction
      
      function void write_actual(alu_seq_item req);
        // 比较
      endfunction
    endclass
    ```
    
    ```python
    # cocotb
    class ALUScoreboard(UVMScoreboard):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.expected_queue = []
            self.actual_queue = []
        
        def write_expected(self, item):
            self.expected_queue.append(compare(item))
        
        def write_actual(self, item):
            self.actual_queue.append(item)
            self.compare()
    ```
    """
    
    def __init__(self, name: str, parent: Optional['UVMComponent'] = None):
        super().__init__(name, parent)
        self.expected_queue = []
        self.actual_queue = []
    
    def write_expected(self, item):
        """接收期望值 - 对应 SV `write_expected()`"""
        self.vlog.debug(f"expected: {item}")
    
    def write_actual(self, item):
        """接收实际值 - 对应 SV `write_actual()`"""
        self.vlog.debug(f"actual: {item}")
        self.compare()
    
    def compare(self):
        """比较期望与实际 - 对应 SV `compare()`"""
        pass


# ================== UVM Config DB ==================
class UVMConfigDB:
    """
    配置数据库 - 对应 SV UVM `uvm_config_db#(...)::set/get`
    
    ## 用法对比
    ```systemverilog
    // SV UVM
    uvm_config_db#(virtual alu_if)::set("*", " vif", this.vif);
    uvm_config_db#(virtual alu_if)::get(this, "", "vif", vif);
    ```
    
    ```python
    # cocotb
    cocotb.set_global("alu_if", vif)
    vif = cocotb.get_global("alu_if")
    
    # 或使用类
    UVMConfigDB.set(self, "vif", vif)
    vif = UVMConfigDB.get(self, "vif")
    ```
    """
    _config = {}
    
    @classmethod
    def set(cls, comp: UVMComponent, field: str, value: Any):
        """
        设置配置 - 对应 SV `uvm_config_db#(...)::set()`
        
        Example:
            UVMConfigDB.set(agent, "vif", dut_if)
        """
        key = f"{comp.name}.{field}"
        cls._config[key] = value
        logging.debug(f"Config set: {key} = {value}")
    
    @classmethod
    def get(cls, comp: UVMComponent, field: str, default=None) -> Any:
        """
        获取配置 - 对应 SV `uvm_config_db#(...)::get()`
        
        Example:
            vif = UVMConfigDB.get(agent, "vif", None)
        """
        key = f"{comp.name}.{field}"
        value = cls._config.get(key)
        if value is None:
            value = cls._config.get(field, default)  # 尝试全局
        return value


# ================== UVM Phases ==================
class UVMPhase:
    """
    UVM Phase 枚举 - 对应 SV 的 phase
    """
    UVM_BUILD        = "build"
    UVM_CONNECT     = "connect" 
    UVM_RUN         = "run"
    UVM_POST_BUILD  = "post_build"
    UVM_POST_RUN    = "post_run"
    UVM_EXTRACT     = "extract"
    UVM_REPORT      = "report"
    UVM_FINAL      = "final"
