# cocotb UVM-Style Environment

## 项目目标
用 cocotb 构建 UVM 风格的验证环境，具备：
- **Component 层级**：Driver/Monitor/Scoreboard/Agent
- **Sequence 机制**：分层 sequence + sequencer
- **Configuration**：uvm_config_db 风格配置管理
- **Phase 机制**：build/connect/run/cleanup
- **Reporter**：UVM 风格日志层级

## 核心功能对标 UVM (详细对照)

### 1. Component 层级

| SV UVM | cocotb 实现 | 说明 |
|-------|-----------|-----|
| `uvm_component` | `UVMComponent` | 基类 |
| `uvm_driver#(T)` | `UVMDriver` | 驱动 |
| `uvm_monitor` | `UVMMonitor` | 监控 |
| `uvm_scoreboard` | `UVMScoreboard` | 计分板 |
| `uvm_sequencer#(T)` | `UVMSequencer` | 序列控制 |
| `uvm_agent` | `UVMAgent` | 代理 |
| `uvm_env` | `UVMEnvironment` | 环境 |
| `uvm_test` | `UVMTest` | 测试 |

### 2. Phase 机制

| SV UVM Phase | cocotb | 说明 |
|------------|-------|-----|
| `build_phase` | `build_phase()` | 构建组件 |
| `connect_phase` | `connect_phase()` | 连接组件 |
| `run_phase` | `async run_phase()` | 运行(异步) |
| `extract_phase` | `extract_phase()` | 提取数据 |
| `report_phase` | `report_phase()` | 报告 |
| `final_phase` | `final_phase()` | 清理 |

### 3. Sequence 机制

| SV UVM | cocotb | 说明 |
|-------|--------|-----|
| `uvm_sequence#(T)` | `UVMSequence` | 序列 |
| `uvm_sequence_item` | `UVMSequenceItem` | 序列项 |
| `uvm_do(req)` | `await sequencer.send(item)` | 发送 |
| `get_next_item()` | `await get_next_item()` | 获取 |
| `item_done()` | 自动 | 完成通知 |

### 4. Port/Export 机制

| SV UVM | cocotb | 说明 |
|-------|--------|-----|
| `uvm_seq_item_pull_port#(T)` | `Sequencer.get_next_item()` | 获取端口 |
| `uvm_analysis_port#(T)` | `List.append()` | 分析端口 |
| `uvm_analysis_imp#(T)` | `write()` | 分析实现 |

### 5. 配置管理

| SV UVM | cocotb |
|--------|--------|
| `uvm_config_db#(...)::set()` | `UVMConfigDB.set()` |
| `uvm_config_db#(...)::get()` | `UVMConfigDB.get()` |

### 6. 日志级别

| UVM | cocotb logging |
|-----|--------------|
| `uvm_fatal` | FATAL/CRITICAL |
| `uvm_error` | ERROR |
| `uvm_warning` | WARNING |
| `uvm_info` | INFO |
| `uvm_debug` | DEBUG |

## 目录结构
```
cocotb_uvm_style/
├── 01_rtl/              # 待测RTL: simple_alu.sv
├── 02_basic_tb/        # 基础 cocotb TB
├── 03_comp/             # Component 基类 + 详细注释
├── 04_seq/              # Sequence + Sequencer + 详细注释
├── 05_agent/            # UVM Agent + 详细注释
├── 06_env/              # Environment
└── REPOS.md
```

## 核心代码示例

### RandomClass 封装
```python
import random

class RandPacket:
    def __init__(self):
        self.length = 0
        self.addr = 0
        self.data = [0] * 4
    
    def pre_randomize(self):
        """randomize 前处理"""
        pass
    
    def randomize(self):
        """Python 风格 randomize"""
        self.length = random.randint(1, 64)
        self.addr = random.randint(0, 0xFFFF_FFFC) & ~3
        self.data = [random.randint(0, 255) for _ in range(4)]
    
    def post_randomize(self):
        """randomize 后处理"""
        pass
```

### Sequencer
```python
class Sequencer:
    def __init__(self):
        self.queue = []
    
    def start_sequence(self, seq):
        """启动 sequence"""
        self.queue.append(seq)
    
    async def get_next_item(self):
        while not self.queue:
            await Timer(1, 'ns')
        return self.queue.pop(0)
```

### Driver
```python
class Driver:
    async def drive(self, dut, seq_item):
        dut.drv_valid <= 1
        dut.drv_data <= seq_item.data
        await dut.drv_ready.event
        dut.drv_valid <= 0
```

### Monitor + Scoreboard
```python
class Monitor:
    async def monitor(self, dut):
        while True:
            await dut.out_valid.event
            yield dut.out_data.value
            await self.scoreboard.put(dut.out_data)

class Scoreboard:
    def __init__(self):
        self.exp_queue = []
    
    def put(self, item):
        self.exp_queue.append(item)
```

## 参考
- cocotb: https://docs.cocotb.org
- UVM 1.2: https://www.accellera.org/downloads/standards/uvm
