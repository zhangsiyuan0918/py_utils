from typing import Dict, List, Any, Optional, Union
from enum import Enum
import random
import string
from .case_generator import DataType

class ValueGenerator:
    def __init__(self):
        self.context = {}
        self.type_mappings = {
            'uint32': {'normal': '1234567890', 'boundary': ['0', '4294967295'], 'error': ['4294967296']},
            'uint8': {'normal': '128', 'boundary': ['0', '255'], 'error': ['256']},
            'int': {'normal': '100', 'boundary': ['-2147483648', '2147483647'], 'error': ['2147483648']},
            'boolean': {'normal': '1', 'boundary': ['0', '1'], 'error': ['2']},
            'pointer': {'normal': 'target_ptr', 'boundary': ['*none*'], 'error': ['*none*']},
            'char': {'normal': "'A'", 'boundary': ["'\\0'", "'\\xFF'"], 'error': ["'\\x100'"]},
            'float': {'normal': '1.0', 'boundary': ['0.0', '3.4028235e+38'], 'error': ['inf']},
            'double': {'normal': '1.0', 'boundary': ['0.0', '1.7976931348623157e+308'], 'error': ['inf']}
        }
        
        # 常用的测试值模式
        self.common_patterns = {
            'zero': '0',
            'one': '1',
            'max_uint32': '4294967295',
            'max_int32': '2147483647',
            'min_int32': '-2147483648',
            'null_ptr': '*none*'
        }
        
        # 指针相关的命名模式
        self.pointer_patterns = {
            'target_prefix': 'target_',
            'data_suffix': '_DataPtr',
            'info_suffix': '_InfoPtr'
        }
    def set_context(self, context: Dict[str, Any]):
        """设置生成器上下文"""
        self.context = context
    
    def get_context(self) -> Dict[str, Any]:
        """获取生成器上下文"""
        return self.context
    
    def update_context(self, key: str, value: Any):
        """更新上下文中的特定值"""
        self.context[key] = value
    
    def clear_context(self):
        """清空上下文"""
        self.context = {}
    
    def _extract_base_type(self, param_type: Union[str, DataType]) -> str:
        """提取基础数据类型"""
        if isinstance(param_type, DataType):
            type_str = param_type.value.lower()
        else:
            type_str = str(param_type).lower()
        
        # 清理类型字符串
        type_str = type_str.replace('const', '').replace('static', '').strip()
        
        # 映射到标准类型
        type_mapping = {
            'std_returntype': 'int',
            'uint32': 'uint32',
            'uint8': 'uint8',
            'unsigned char': 'uint8',
            'unsigned int': 'uint32',
            'unsigned long': 'uint32',
            'long': 'int',
            'short': 'int',
            'unsigned short': 'uint32'
        }
        
        return type_mapping.get(type_str, type_str)

    def generate_boundary_value(self, param_name: str, data_type: Union[str, DataType], is_pointer: bool = False) -> str:
        """生成边界值"""
        if is_pointer:
            return self._generate_pointer_boundary_value(param_name)
        
        base_type = self._extract_base_type(data_type)
        
        if base_type in self.type_mappings:
            boundaries = self.type_mappings[base_type]['boundary']
            # 随机选择一个边界值
            return random.choice(boundaries)
        
        return "0"
    
    def generate_error_value(self, param_name: str, data_type: Union[str, DataType], is_pointer: bool = False) -> str:
        """生成错误值"""
        if is_pointer:
            return "*none*"
        
        base_type = self._extract_base_type(data_type)
        
        if base_type in self.type_mappings and 'error' in self.type_mappings[base_type]:
            error_values = self.type_mappings[base_type]['error']
            return random.choice(error_values)
        
        # 默认错误值
        if base_type in ['int', 'uint32', 'uint8']:
            return "-1"
        
        return "0"
    
    def _generate_pointer_boundary_value(self, param_name: str) -> str:
        """生成指针的边界值"""
        return "*none*"

    def generate_pointer_value(self, param_name: str, scenario_type: str = 'normal') -> Dict[str, Any]:
        """生成指针相关的值"""
        result = {}
        
        if scenario_type == 'normal':
            # 生成正常的指针结构
            target_name = f"target_{param_name}"
            result[param_name] = target_name
            result[f"&{target_name}"] = {
                'DataPtr': f"target_{param_name}_DataPtr",
                'Length': "*none*"
            }
            result[f"&target_{param_name}_DataPtr"] = "*none*"
        
        elif scenario_type == 'error':
            # 生成错误的指针值
            result[param_name] = "*none*"
        
        else:
            # 边界情况
            target_name = f"target_{param_name}"
            result[param_name] = target_name
            result[f"&{target_name}"] = {
                'DataPtr': "*none*",
                'Length': "0"
            }
        
        return result
    
    def generate_array_value(self, param_name: str, array_size: int, element_type: str, scenario_type: str = 'normal') -> str:
        """生成数组值"""
        if scenario_type == 'normal':
            return f"target_{param_name}_array"
        elif scenario_type == 'error':
            return "*none*"
        else:
            return f"target_{param_name}_boundary"

    def generate_context_aware_value(self, param_name: str, data_type: Union[str, DataType], 
                                   is_pointer: bool = False, scenario: Dict = None) -> Any:
        """基于上下文生成智能值"""
        scenario = scenario or {}
        
        # 检查上下文中是否有特定的常量值
        constants = self.context.get('constants', {})
        if param_name in constants:
            return str(constants[param_name])
        
        # 检查是否有特定的参数约束
        function_info = self.context.get('function')
        if function_info:
            for param in function_info.parameters:
                if param.name == param_name and param.constraints:
                    return self._apply_constraints(param.constraints, data_type)
        
        # 根据场景类型生成值
        scenario_type = scenario.get('type', 'normal')
        
        if is_pointer:
            return self.generate_pointer_value(param_name, scenario_type)
        elif scenario_type == 'boundary':
            return self.generate_boundary_value(param_name, data_type, is_pointer)
        elif scenario_type == 'error':
            return self.generate_error_value(param_name, data_type, is_pointer)
        else:
            return self.generate_normal_value(param_name, data_type, self.context)
    
    def _apply_constraints(self, constraints: Dict, data_type: Union[str, DataType]) -> str:
        """应用参数约束"""
        if 'min' in constraints and 'max' in constraints:
            min_val = constraints['min']
            max_val = constraints['max']
            # 生成范围内的随机值
            if isinstance(min_val, int) and isinstance(max_val, int):
                return str(random.randint(min_val, max_val))
        
        return self.generate_normal_value('', data_type, {})

    def generate_stub_return_value(self, function_name: str, scenario_type: str = 'normal') -> str:
        """生成stub函数的返回值"""
        if scenario_type == 'error':
            return "1"  # E_NOT_OK
        else:
            return "0"  # E_OK
    
    def generate_random_string(self, length: int = 8) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def generate_test_data_set(self, function_info, scenario: Dict) -> Dict[str, Any]:
        """为整个函数生成一套完整的测试数据"""
        test_data = {
            'inputs': {},
            'outputs': {},
            'pointers': {}
        }
        
        scenario_type = scenario.get('type', 'normal')
        
        # 为每个参数生成值
        for param in function_info.parameters:
            if param.is_pointer:
                pointer_data = self.generate_pointer_value(param.name, scenario_type)
                test_data['inputs'].update(pointer_data)
                test_data['pointers'][param.name] = pointer_data
            else:
                test_data['inputs'][param.name] = self.generate_context_aware_value(
                    param.name, param.data_type, param.is_pointer, scenario)
        
        # 生成期望输出
        if hasattr(function_info, 'return_type') and function_info.return_type.value != 'void':
            if scenario_type == 'error':
                test_data['outputs']['return'] = 1
            else:
                test_data['outputs']['return'] = 0
        
        return test_data

    def generate_normal_value(self, param_name: str, param_type: Union[str, DataType], context: Dict = None) -> str:
        """生成正常测试值"""
        if context is None:
            context = self.context
            
        # 首先检查是否有上下文中的常量值
        if param_name in context.get('constants', {}):
            return str(context['constants'][param_name])
        
        # 根据类型生成默认值
        base_type = self._extract_base_type(param_type)
        if base_type in self.type_mappings:
            return self.type_mappings[base_type]['normal']
        
        return "0"

    
