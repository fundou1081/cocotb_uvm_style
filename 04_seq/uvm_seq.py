"""
04_seq: Sequence + Sequencer
===========================

## UVM Sequence 机制对照

| UVM (SystemVerilog)         | cocotb Python 实现         |
|---------------------------|----------------------|
| `uvm_sequence#(T)`         | `UVMSequence` class   |
| `uvm_sequence_item#(T)`     | `UVMSequenceItem`     |
| `uvm_sequencer#(T)`        | `UVMSequencer`       |
| `uvm_do(req)`              | `await sequencer.send()` |
| `uvm_send(req)`            | `sequencer.put()`   |
| `get_next_item()`         | `await get_next_item()` |
| `item_done()`              | 自动完成           |
| `start_sequence(seq)`       | `await seq.start()` |

## Sequence Item 对比

```systemverilog
// SV UVM
class alu_seq_item extends uvm_sequence_item;
  rand logic [7:0] a, b;
  rand logic [2:0] op;
  rand logic [7:0] result;
  
  `uvm_object_utils(alu_seq_item)
  
  function new(string name = "alu_seq_item");
    super.new(name);
  endfunction
endclass
```

```python
# cocotb Python
class ALUSeqItem(UVMSequenceItem):
    def __init__(self, a=0, b=0, op=0, result=0):
        super().__init__("alu_seq_item")
        self.a = a
        self.b = b
        self.op = op
        self.result = result
    
    def __str__(self):
        return f"ALU(a={self.a}, b={self.b}, op={self.op})"
```

## Sequencer 通信

```systemverilog
// SV UVM Driver
class my_driver extends uvm_driver#(alu_seq_item);
  task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);
      drive(req);
      seq_item_port.item_done();
    end
  endtask
endclass
```

```python
# cocotb Driver
class Driver(UVMDriver):
    async def run_phase(self):
        while True:
            item = await self.sequencer.get_next_item()  # 阻塞等待
            await self.drive(item)
            # 等同于 item_done()
```

## Sequence 层级

```systemverilog
// SV: base_seq -> item_seq
class base_seq extends uvm_sequence#(alu_seq_item);
  virtual task body();
    `uvm_do(req)  // 自动随机
  endtask
endclass

class item_seq extends base_seq;
  virtual task body();
    // 自定义序列
  endtask
endclass
```

```python
# cocotb
class BaseSequence(UVMSequence):
    async def body(self):
        item = ALUSeqItem()
        item.randomize()  # 或自动生成
        await self.sequencer.send(item)

class ItemSequence(BaseSequence):
    async def body():
        # 自定义
        pass
```

## port 类型对照

| SV UVM port | Python 实现 |
|-----------|---------|
| `uvm_seq_item_pull_port#(T)` | `Sequencer.get_next_item()` |
| `uvm_seq_item_export#(T)` | `Queue` |
| `uvm_analysis_port#(T)` | `List.append()` |
"""
import cocotb
from cocotb.triggers import Timer, RisingEdge
from typing import Optional, List, Any
import random


# ================== Sequence Item ==================
class UVMSequenceItem:
    """
    Sequence Item 基类
    
    对应 SV UVM: `uvm_sequence_item#(T)`
    
    ## 关键方法
    - randomize(): 随机化
    - convert_string(): 字符串转换
    - compare(): 比较
    """
    
    def __init__(self, name: str = "seq_item"):
        """
        构造函数 - 对应 SV `new()`
        """
        self.name = name
    
    def randomize(self):
        """随机化 - 对应 SV `randomize()""""
        pass
    
    def convert_string(self) -> str:
        """字符串转换 - 对应 SV `convert_string()`"""
        return self.name
    
    def __str__(self):
        return self.convert_string()
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"


class SeqItemALU(UVMSequenceItem):
    """
    ALU Sequence Item 示例
    
    对应 SV:
    ```systemverilog
    class alu_seq_item extends uvm_sequence_item;
      rand bit [7:0] a;
      rand bit [7:0] b;
      rand bit [2:0] op;  // 0=add,1=sub,2=and,3=or,4=xor
      rand bit [7:0] result;
      
      `uvm_object_utils(alu_seq_item)
    endclass
    ```
    """
    
    def __init__(self, a: int = 0, b: int = 0, op: int = 0, result: int = 0):
        super().__init__("alu_seq_item")
        self.a = a
        self.b = b
        self.op = op
        self.result = result
    
    def randomize(self):
        """随机化"""
        self.a = random.randint(0, 255)
        self.b = random.randint(0, 255)
        self.op = random.randint(0, 4)
    
    def convert_string(self) -> str:
        return f"ALU(a={self.a}, b={self.b}, op={self.op}, result={self.result})"


# ================== Sequence ==================
class UVMSequence:
    """
    Sequence 基类
    
    对应 SV UVM: `uvm_sequence#(T)`
    
    ## 关键方法
    - body(): 序列主体 - 对应 SV `task body();`
    - start(): 启动序列 - 对应 SV `p_sequencer.start_sequence(this)`
    - pre_body(): 前置 - 对应 SV `pre_body()``
    - post_body(): 后置 - 对应 SV `post_body()``
    """
    
    def __init__(self, name: str = "sequence"):
        self.name = name
        self.sequencer = None
        self.parent_sequence = None
    
    async def body(self):
        """
        序列主体 - 对应 SV `task body()`
        
        子类必须实现
        """
        pass
    
    async def pre_body(self):
        """前置 - 对应 SV `pre_body()`"""
        pass
    
    async def post_body(self):
        """后置 - 对应 SV `post_body()`"""
        pass
    
    async def start(self, sequencer, parent_sequence=None):
        """
        启动序列 - 对应 SV `p_sequencer.start_sequence(this)`
        
        Args:
            sequencer: 目标 sequencer
            parent_sequence: 父序列（用于分层）
        """
        self.sequencer = sequencer
        self.parent_sequence = parent_sequence
        await self.pre_body()
        await self.body()
        await self.post_body()


class SeqALURandom(UVMSequence):
    """
    随机 ALU Sequence 示例
    
    对应 SV:
    ```systemverilog
    class alu_random_seq extends uvm_sequence#(alu_seq_item);
      `uvm_object_utils(alu_random_seq)
      
      int num_items = 10;
      
      task body();
        for (int i = 0; i < num_items; i++) begin
          `uvm_send(req)  // 或 `uvm_do(req)
        end
      endtask
    endclass
    ```
    """
    
    def __init__(self, num_items: int = 10):
        super().__init__("alu_random_seq")
        self.num_items = num_items
    
    async def body(self):
        """发送随机 items"""
        for _ in range(self.num_items):
            item = SeqItemALU()
            item.randomize()
            # 发送 - 等同于 `uvm_do(req)
            await self.sequencer.send(item)


class SeqALUDirected(UVMSequence):
    """
     directed Sequence 示例
    
    对应 SV:
    ```systemverilog
    class alu_add_seq extends uvm_sequence#(alu_seq_item);
      task body();
        req = alu_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize() with { a == 5; b == 3; op == 0; })
          `uvm_fatal("RAND", "randomize failed")
        finish_item(req);
      endtask
    endclass
    ```
    """
    
    def __init__(self, a: int = 5, b: int = 3, op: int = 0):
        super().__init__("alu_directed_seq")
        self.a = a
        self.b = b
        self.op = op
    
    async def body(self):
        item = SeqItemALU(a=self.a, b=self.b, op=self.op)
        await self.sequencer.send(item)


# ================== Sequencer ==================
class UVMSequencer:
    """
    Sequencer
    
    对应 SV UVM: `uvm_sequencer#(T)`
    
    ## 关键方法
    - get_next_item(): 获取下一个 item - 对应 SV `seq_item_port.get_next_item(req)`
    - try_next_item(): 非阻塞尝试 - 对应 SV `seq_item_port.try_next_item(req)`
    - put(item): 发送响应 - 对应 SV `seq_item_port.put(rsp)`
    - item_done(): 通知完成 - 对应 SV `seq_item_port.item_done()`
    
    ## port 定义
    ```systemverilog
    // SV UVM
    class my_sequencer extends uvm_sequencer#(alu_seq_item);
      `uvm_component_utils(my_sequencer)
      uvm_seq_item_pull_port#(alu_seq_item) seq_item_port;
    endclass
    ```
    
    ```python
    # cocotb
    class ALUSequencer(UVMSequencer):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.seq_item_port = []  # 实现为列表
    ```
    
    ## Driver 连接
    
    ```systemverilog
    // SV
    driver.seq_item_port.connect(sequencer.seq_item_export);
    ```
    
    ```python
    # cocotb - 自动连接
    driver.sequencer = sequencer
    ```
    """
    
    def __init__(self, name: str = "sequencer", parent=None):
        self.name = name
        self.parent = parent
        self.queue: List[UVMSequenceItem] = []
        self.running_sequence: Optional[UVMSequence] = None
    
    async def send(self, item: UVMSequenceItem):
        """
        发送 item 到 Driver - 对应 SV ` seq_item_port.put(req)`
        
        Driver 调用 get_next_item() 阻塞等待
        """
        self.queue.append(item)
    
    async def get_next_item(self) -> UVMSequenceItem:
        """
        获取下一个 item - 对应 SV `seq_item_port.get_next_item(req)`
        
        如果队列为空，阻塞等待
        """
        while not self.queue:
            await Timer(1, 'ns')
        return self.queue.pop(0)
    
    def try_next_item(self) -> Optional[UVMSequenceItem]:
        """
        非阻塞获取 - 对应 SV `seq_item_port.try_next_item(req)`
        
        Returns:
            None 如果队列为空，否则返回 item
        """
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def item_done(self):
        """
        通知完成 - 对应 SV `seq_item_port.item_done()`
        
        在 cocotb 中由 Driver 自动调用（get_next_item 返回即完成）
        """
        pass
    
    async def start_sequence(self, seq: UVMSequence):
        """启动 Sequence - 对应 SV `start_sequence(this)`"""
        self.running_sequence = seq
        await seq.start(self)
    
    def wait_for_sequence_done(self, sequence_id: int):
        """
        等待 Sequence 完成 - 对应 SV `wait_for_sequence_door(sequence_id)`
        """
        pass


# ================== Sequence Library ==================
class UVMSequenceLibrary:
    """
    Sequence 库 - 相当于 UVM-do nothing
    
    预定义一些常用 sequence
    """
    
    # 预定义 sequence 类型
    SEQ_RANDOM = "random"
    SEQ_DIRECTED = "directed"
    SEQ_INCREMENTAL = "incremental"
    
    @staticmethod
    def get_sequence(seq_type: str) -> UVMSequence:
        """根据类型获取 sequence"""
        seq_map = {
            SeqALURandom.name: SeqALURandom,
            SeqALUDirected.name: SeqALUDirected,
        }
        return seq_map.get(seq_type, SeqALURandom)()
