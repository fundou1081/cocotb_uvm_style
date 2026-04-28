"""
06_env: UVM Environment
"""
import sys
sys.path.insert(0, '.')
from 03_comp.uvm_component import UVMComponent
from 05_agent.uvm_agent import UVMAgent


class UVMEnvironment(UVMComponent):
    """UVM Environment"""
    
    def __init__(self, name="env", parent=None):
        super().__init__(name, parent)
        self.agent = None
    
    def build_phase(self):
        self.agent = UVMAgent("agent", self)
        self.agent.build_phase()


class UVMTest(UVMComponent):
    """UVM Test"""
    
    def __init__(self, name="test", parent=None):
        super().__init__(name, parent)
        self.env = None
    
    def build_phase(self):
        self.env = UVMEnvironment("env", self)
        self.env.build_phase()
