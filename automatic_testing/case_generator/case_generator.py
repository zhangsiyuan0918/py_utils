#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用C函数测试用例生成框架
支持任意C函数的自动化测试用例生成
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json

from case_generator.value_generator import ValueGenerator

# ==================== 数据结构定义 ====================

class DataType(Enum):
    """数据类型枚举"""
    VOID = "void"
    CHAR = "char"
    UCHAR = "unsigned char"
    SHORT = "short"
    USHORT = "unsigned short"
    INT = "int"
    UINT = "unsigned int"
    LONG = "long"
    ULONG = "unsigned long"
    FLOAT = "float"
    DOUBLE = "double"
    POINTER = "pointer"
    ARRAY = "array"
    STRUCT = "struct"
    ENUM = "enum"
    BOOLEAN = "boolean"

class TestCaseType(Enum):
    """测试用例类型"""
    NORMAL = "normal"           # 正常路径
    BOUNDARY = "boundary"       # 边界条件
    ERROR = "error"            # 错误处理
    EXCEPTION = "exception"     # 异常情况
    PERFORMANCE = "performance" # 性能测试

@dataclass
class Parameter:
    """函数参数信息"""
    name: str
    data_type: DataType
    is_pointer: bool = False
    is_const: bool = False
    array_size: Optional[int] = None
    struct_members: Optional[Dict] = None
    constraints: Optional[Dict] = field(default_factory=dict)

@dataclass
class Function:
    """函数信息"""
    name: str
    return_type: DataType
    parameters: List[Parameter]
    is_static: bool = False
    body: str = ""
    dependencies: List[str] = field(default_factory=list)
    complexity: int = 0

@dataclass
class TestCase:
    """测试用例"""
    id: int
    name: str
    description: str
    test_type: TestCaseType
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    stub_functions: Dict[str, str] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)

@dataclass
class TestSuite:
    """测试套件"""
    function_name: str
    test_cases: List[TestCase]
    coverage_target: float = 0.85
    metadata: Dict[str, Any] = field(default_factory=dict)

# ==================== 解析器接口 ====================

class IParser(ABC):
    """解析器接口"""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析C文件"""
        pass
    
    @abstractmethod
    def extract_function(self, function_name: str) -> Function:
        """提取指定函数信息"""
        pass
    
    @abstractmethod
    def extract_constants(self) -> Dict[str, Any]:
        """提取常量定义"""
        pass

class IAnalyzer(ABC):
    """分析器接口"""
    
    @abstractmethod
    def analyze_control_flow(self, function: Function) -> Dict[str, Any]:
        """控制流分析"""
        pass
    
    @abstractmethod
    def analyze_data_flow(self, function: Function) -> Dict[str, Any]:
        """数据流分析"""
        pass
    
    @abstractmethod
    def calculate_complexity(self, function: Function) -> int:
        """计算复杂度"""
        pass

class ITestStrategy(ABC):
    """测试策略接口"""
    
    @abstractmethod
    def generate_test_scenarios(self, function: Function, 
                              analysis_result: Dict) -> List[Dict]:
        """生成测试场景"""
        pass
    
    @abstractmethod
    def determine_test_data(self, scenario: Dict, 
                          function: Function) -> Dict[str, Any]:
        """确定测试数据"""
        pass

class IFormatter(ABC):
    """格式化器接口"""
    
    @abstractmethod
    def format_test_suite(self, test_suite: TestSuite) -> str:
        """格式化测试套件"""
        pass

# ==================== 具体实现类 ====================

class RegexCParser(IParser):
    """基于正则表达式的C代码解析器"""
    
    def __init__(self):
        self.content = ""
        self.functions = {}
        self.constants = {}
        self.includes = []
        
        # 正则表达式模式
        self.function_pattern = re.compile(
            r'(static\s+)?(\w+(?:\s*\*)?)\s+(\w+)\s*\(([^)]*)\)\s*\{',
            re.MULTILINE | re.DOTALL
        )
        self.constant_pattern = re.compile(
            r'#define\s+(\w+)\s+(.+?)(?:\n|$)',
            re.MULTILINE
        )
        self.include_pattern = re.compile(
            r'#include\s*[<"]([^>"]+)[>"]',
            re.MULTILINE
        )
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析C文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                self.content = f.read()
        
        # 提取包含文件
        self.includes = [match.group(1) for match in self.include_pattern.finditer(self.content)]
        
        # 提取常量定义
        self._extract_constants()
        
        # 提取函数
        self._extract_functions()
        
        return {
            'functions': self.functions,
            'constants': self.constants,
            'includes': self.includes,
            'content': self.content
        }
    
    def extract_function(self, function_name: str) -> Function:
        """提取指定函数信息"""
        if function_name not in self.functions:
            raise ValueError(f"函数 {function_name} 未找到")
        
        func_info = self.functions[function_name]
        return Function(
            name=function_name,
            return_type=self._parse_data_type(func_info['return_type']),
            parameters=self._parse_parameters(func_info['parameters']),
            is_static=func_info['is_static'],
            body=func_info['body']
        )
    
    def extract_constants(self) -> Dict[str, Any]:
        """提取常量定义"""
        return self.constants.copy()
    
    def _extract_constants(self):
        """提取常量定义"""
        for match in self.constant_pattern.finditer(self.content):
            name = match.group(1)
            value = match.group(2).strip()
            self.constants[name] = self._parse_constant_value(value)
    
    def _extract_functions(self):
        """提取函数定义"""
        for match in self.function_pattern.finditer(self.content):
            is_static = match.group(1) is not None
            return_type = match.group(2).strip()
            func_name = match.group(3)
            params = match.group(4).strip()
            
            # 提取函数体
            body_start = match.end()
            body = self._extract_function_body(body_start)
            
            self.functions[func_name] = {
                'is_static': is_static,
                'return_type': return_type,
                'parameters': params,
                'body': body
            }
    
    def _extract_function_body(self, start_pos: int) -> str:
        """提取函数体"""
        brace_count = 1
        pos = start_pos
        
        while pos < len(self.content) and brace_count > 0:
            char = self.content[pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            pos += 1
        
        return self.content[start_pos:pos-1]
    
    def _parse_parameters(self, params_str: str) -> List[Parameter]:
        """解析参数列表"""
        if not params_str or params_str.strip() == 'void':
            return []
        
        parameters = []
        param_list = [p.strip() for p in params_str.split(',')]
        
        for param in param_list:
            if param:
                param_info = self._parse_single_parameter(param)
                if param_info:
                    parameters.append(param_info)
        
        return parameters
    
    def _parse_single_parameter(self, param_str: str) -> Optional[Parameter]:
        """解析单个参数"""
        # 简化的参数解析
        parts = param_str.strip().split()
        if len(parts) < 2:
            return None
        
        is_const = 'const' in parts
        is_pointer = '*' in param_str
        
        # 提取类型和名称
        if is_const:
            parts.remove('const')
        
        param_name = parts[-1].replace('*', '').strip()
        type_parts = parts[:-1]
        type_str = ' '.join(type_parts).replace('*', '').strip()
        
        return Parameter(
            name=param_name,
            data_type=self._parse_data_type(type_str),
            is_pointer=is_pointer,
            is_const=is_const
        )
    
    def _parse_data_type(self, type_str: str) -> DataType:
        """解析数据类型"""
        type_str = type_str.strip().lower()
        
        type_mapping = {
            'void': DataType.VOID,
            'char': DataType.CHAR,
            'unsigned char': DataType.UCHAR,
            'short': DataType.SHORT,
            'unsigned short': DataType.USHORT,
            'int': DataType.INT,
            'unsigned int': DataType.UINT,
            'uint32': DataType.UINT,
            'uint8': DataType.UCHAR,
            'long': DataType.LONG,
            'unsigned long': DataType.ULONG,
            'float': DataType.FLOAT,
            'double': DataType.DOUBLE,
            'boolean': DataType.BOOLEAN,
            'std_returntype': DataType.INT
        }
        
        return type_mapping.get(type_str, DataType.INT)
    
    def _parse_constant_value(self, value_str: str) -> Any:
        """解析常量值"""
        value_str = value_str.strip()
        
        # 移除注释
        if '//' in value_str:
            value_str = value_str.split('//')[0].strip()
        
        # 十六进制
        if value_str.startswith('0x') or value_str.startswith('0X'):
            return int(value_str, 16)
        
        # 数字
        if value_str.isdigit():
            return int(value_str)
        
        # 带UL后缀的数字
        if value_str.endswith('UL') or value_str.endswith('ul'):
            return int(value_str[:-2])
        
        return value_str

class ASTCParser(IParser):
    """基于AST的C代码解析器（占位符实现）"""
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析C文件"""
        # TODO: 实现基于clang AST的解析
        raise NotImplementedError("AST解析器尚未实现")
    
    def extract_function(self, function_name: str) -> Function:
        """提取指定函数信息"""
        raise NotImplementedError("AST解析器尚未实现")
    
    def extract_constants(self) -> Dict[str, Any]:
        """提取常量定义"""
        raise NotImplementedError("AST解析器尚未实现")

class BasicCodeAnalyzer(IAnalyzer):
    """基础代码分析器"""
    
    def __init__(self):
        self.control_patterns = {
            'if': re.compile(r'if\s*\([^)]+\)', re.MULTILINE),
            'for': re.compile(r'for\s*\([^)]*;[^)]*;[^)]*\)', re.MULTILINE),
            'while': re.compile(r'while\s*\([^)]+\)', re.MULTILINE),
            'switch': re.compile(r'switch\s*\([^)]+\)', re.MULTILINE),
            'case': re.compile(r'case\s+[^:]+:', re.MULTILINE),
            'return': re.compile(r'return\s+[^;]+;', re.MULTILINE)
        }
    
    def analyze_control_flow(self, function: Function) -> Dict[str, Any]:
        """控制流分析"""
        body = function.body
        control_structures = {}
        
        for structure_type, pattern in self.control_patterns.items():
            matches = pattern.findall(body)
            control_structures[structure_type] = {
                'count': len(matches),
                'instances': matches
            }
        
        # 计算分支数量
        branch_count = (control_structures['if']['count'] + 
                       control_structures['case']['count'] + 
                       control_structures['while']['count'] + 
                       control_structures['for']['count'])
        
        return {
            'structures': control_structures,
            'branch_count': branch_count,
            'return_count': control_structures['return']['count'],
            'has_loops': (control_structures['for']['count'] > 0 or 
                         control_structures['while']['count'] > 0),
            'has_switch': control_structures['switch']['count'] > 0
        }
    
    def analyze_data_flow(self, function: Function) -> Dict[str, Any]:
        """数据流分析"""
        body = function.body
        
        # 查找变量声明
        var_pattern = re.compile(r'(\w+)\s+(\w+)\s*[=;]', re.MULTILINE)
        variables = var_pattern.findall(body)
        
        # 查找赋值操作
        assignment_pattern = re.compile(r'(\w+)\s*=\s*([^;]+);', re.MULTILINE)
        assignments = assignment_pattern.findall(body)
        
        # 查找函数调用
        call_pattern = re.compile(r'(\w+)\s*\([^)]*\)', re.MULTILINE)
        function_calls = call_pattern.findall(body)
        
        return {
            'variables': variables,
            'assignments': assignments,
            'function_calls': function_calls,
            'parameter_usage': self._analyze_parameter_usage(function, body)
        }
    
    def calculate_complexity(self, function: Function) -> int:
        """计算圈复杂度"""
        control_flow = self.analyze_control_flow(function)
        
        # 基础复杂度为1
        complexity = 1
        
        # 每个判断分支增加复杂度
        complexity += control_flow['structures']['if']['count']
        complexity += control_flow['structures']['case']['count']
        complexity += control_flow['structures']['while']['count']
        complexity += control_flow['structures']['for']['count']
        
        return complexity
    
    def _analyze_parameter_usage(self, function: Function, body: str) -> Dict[str, List[str]]:
        """分析参数使用情况"""
        usage = {}
        
        for param in function.parameters:
            param_name = param.name
            # 查找参数在函数体中的使用
            usage_pattern = re.compile(rf'\b{param_name}\b', re.MULTILINE)
            matches = usage_pattern.findall(body)
            usage[param_name] = {
                'usage_count': len(matches),
                'is_modified': self._is_parameter_modified(param_name, body)
            }
        
        return usage
    
    def _is_parameter_modified(self, param_name: str, body: str) -> bool:
        """检查参数是否被修改"""
        # 简单检查赋值操作
        assignment_pattern = re.compile(rf'{param_name}\s*=', re.MULTILINE)
        return bool(assignment_pattern.search(body))

class AdvancedCodeAnalyzer(IAnalyzer):
    """高级代码分析器（占位符实现）"""
    
    def analyze_control_flow(self, function: Function) -> Dict[str, Any]:
        """控制流分析"""
        # TODO: 实现更高级的控制流分析
        basic_analyzer = BasicCodeAnalyzer()
        return basic_analyzer.analyze_control_flow(function)
    
    def analyze_data_flow(self, function: Function) -> Dict[str, Any]:
        """数据流分析"""
        # TODO: 实现更高级的数据流分析
        basic_analyzer = BasicCodeAnalyzer()
        return basic_analyzer.analyze_data_flow(function)
    
    def calculate_complexity(self, function: Function) -> int:
        """计算复杂度"""
        # TODO: 实现更精确的复杂度计算
        basic_analyzer = BasicCodeAnalyzer()
        return basic_analyzer.calculate_complexity(function)


class ComprehensiveTestStrategy(ITestStrategy):
    """综合测试策略"""
    
    def __init__(self):
        self.value_generator = ValueGenerator()
    
    def determine_test_data(self, scenario: Dict, function: Function) -> Dict[str, Any]:
        """确定测试数据"""
        test_data = {
            'inputs': {},
            'outputs': {},
            'stubs': {}
        }
        
        scenario_type = scenario.get('type', 'normal')
        target_param = scenario.get('target_parameter')
        
        # 设置值生成器的上下文
        self.value_generator.set_context({
            'function': function,
            'scenario': scenario,
            'scenario_type': scenario_type
        })
    def generate_test_scenarios(self, function: Function, 
                              analysis_result: Dict) -> List[Dict]:
        """生成测试场景"""
        scenarios = []
        
        # 1. 正常路径测试
        scenarios.append({
            'name': 'Normal Path Test',
            'description': 'Test normal execution path',
            'type': 'normal',
            'priority': 1
        })
        # 2. 边界条件测试
        for param in function.parameters:
            if param.data_type in [DataType.INT, DataType.UINT, DataType.UCHAR]:
                scenarios.append({
                    'name': f'Boundary Test - {param.name}',
                    'description': f'Test boundary values for parameter {param.name}',
                    'type': 'boundary',
                    'priority': 2,
                    'target_parameter': param.name
                })
        
        # 3. 基于控制流的测试场景
        control_flow = analysis_result.get('control_flow', {})
        
        # 为每个分支生成测试场景
        branch_count = control_flow.get('branch_count', 0)
        for i in range(branch_count):
            scenarios.append({
                'name': f'Branch Coverage Test {i+1}',
                'description': f'Test to cover branch {i+1}',
                'type': 'normal',
                'priority': 2,
                'target_branch': i+1
            })
        
        # 4. 错误处理测试
        if control_flow.get('return_count', 0) > 1:
            scenarios.append({
                'name': 'Error Handling Test',
                'description': 'Test error handling paths',
                'type': 'error',
                'priority': 3
            })
        
        # 5. 循环相关测试
        if control_flow.get('has_loops', False):
            scenarios.extend([
                {
                    'name': 'Loop Zero Iterations',
                    'description': 'Test loop with zero iterations',
                    'type': 'boundary',
                    'priority': 2
                },
                {
                    'name': 'Loop Multiple Iterations',
                    'description': 'Test loop with multiple iterations',
                    'type': 'normal',
                    'priority': 2
                }
            ])
        
        return scenarios
    
    def determine_test_data(self, scenario: Dict, function: Function) -> Dict[str, Any]:
        """确定测试数据"""
        test_data = {
            'inputs': {},
            'outputs': {},
            'stubs': {}
        }
        
        scenario_type = scenario.get('type', 'normal')
        target_param = scenario.get('target_parameter')
        
        # 生成输入参数
        for param in function.parameters:
            if target_param == param.name and scenario_type == 'boundary':
                # 为目标参数生成边界值
                test_data['inputs'][param.name] = self.value_generator.generate_boundary_value(
                    param.name, param.data_type, param.is_pointer)
            elif scenario_type == 'error':
                # 生成可能导致错误的值
                test_data['inputs'][param.name] = self.value_generator.generate_error_value(
                    param.name, param.data_type, param.is_pointer)
            else:
                # 生成正常值
                test_data['inputs'][param.name] = self.value_generator.generate_normal_value(
                    param.name, param.data_type, param.is_pointer)
        
        # 生成期望输出
        if function.return_type != DataType.VOID:
            if scenario_type == 'error':
                test_data['outputs']['return'] = 1  # E_NOT_OK
            else:
                test_data['outputs']['return'] = 0  # E_OK
        
        # 生成stub函数（如果需要）
        data_flow = self.value_generator.get_context().get('data_flow', {})
        function_calls = data_flow.get('function_calls', [])
        
        for call in function_calls:
            if call not in ['if', 'for', 'while', 'return']:  # 排除关键字
                test_data['stubs'][call] = self._generate_stub_function(call, scenario_type)
        
        return test_data
    
    def _generate_stub_function(self, function_name: str, scenario_type: str) -> str:
        """生成stub函数"""
        if scenario_type == 'error':
            return f'''
                static int step = 0;
                switch (step) {{
                case 0:
                    return 1;  // Error case
                default:
                    break;
                }}
                step++;
            '''
        else:
            return f'''
                static int step = 0;
                switch (step) {{
                case 0:
                    return 0;  // Success case
                default:
                    break;
                }}
                step++;
            '''

class BasicTestStrategy(ITestStrategy):
    """基础测试策略"""
    
    def __init__(self):
        self.value_generator = ValueGenerator()
    
    def generate_test_scenarios(self, function: Function, 
                              analysis_result: Dict) -> List[Dict]:
        """生成测试场景"""
        scenarios = []
        control_flow = analysis_result.get('control_flow', {})
        
        # 1. 正常路径测试
        scenarios.append({
            'name': 'Normal Execution',
            'description': 'Test normal execution path with valid inputs',
            'type': 'normal',
            'priority': 1,
            'target_branch': None
        })
        
        # 2. 基于分支的测试场景
        if control_flow.get('branch_count', 0) > 0:
            # 为每个if分支生成测试场景
            if_count = control_flow.get('structures', {}).get('if', {}).get('count', 0)
            for i in range(if_count):
                scenarios.append({
                    'name': f'Branch Test {i+1}',
                    'description': f'Test branch condition {i+1}',
                    'type': 'boundary',
                    'priority': 2,
                    'target_branch': f'if_{i+1}'
                })
        
        # 3. 返回值测试
        if control_flow.get('return_count', 0) > 1:
            scenarios.append({
                'name': 'Error Return Test',
                'description': 'Test error return path',
                'type': 'error',
                'priority': 3,
                'expected_return': 'error'
            })
        
        # 4. 循环测试（如果存在循环）
        if control_flow.get('has_loops', False):
            scenarios.append({
                'name': 'Loop Boundary Test',
                'description': 'Test loop boundary conditions',
                'type': 'boundary',
                'priority': 2,
                'target_structure': 'loop'
            })
        
        return scenarios
    
    def determine_test_data(self, scenario: Dict, function: Function) -> Dict[str, Any]:
        """确定测试数据"""
        test_data = {
            'inputs': {},
            'outputs': {},
            'stubs': {}
        }
        
        scenario_type = scenario.get('type', 'normal')
        
        # 生成输入参数
        for param in function.parameters:
            if scenario_type == 'normal':
                test_data['inputs'][param.name] = self.value_generator.generate_normal_value(
                    param.name, param.data_type, param.is_pointer)
            elif scenario_type == 'boundary':
                test_data['inputs'][param.name] = self.value_generator.generate_boundary_value(
                    param.name, param.data_type, param.is_pointer)
            elif scenario_type == 'error':
                test_data['inputs'][param.name] = self.value_generator.generate_error_value(
                    param.name, param.data_type, param.is_pointer)
            else:
                test_data['inputs'][param.name] = self.value_generator.generate_normal_value(
                    param.name, param.data_type, param.is_pointer)
        
        # 生成期望输出
        if function.return_type != DataType.VOID:
            if scenario.get('expected_return') == 'error':
                test_data['outputs']['return'] = self._get_error_return_value(function.return_type)
            else:
                test_data['outputs']['return'] = self._get_normal_return_value(function.return_type)
        
        return test_data
    
    def _get_normal_return_value(self, return_type: DataType) -> Any:
        """获取正常返回值"""
        if return_type == DataType.INT or return_type == DataType.UINT:
            return 0  # E_OK
        elif return_type == DataType.BOOLEAN:
            return 1  # TRUE
        elif return_type == DataType.POINTER:
            return "valid_pointer"
        else:
            return 0
    
    def _get_error_return_value(self, return_type: DataType) -> Any:
        """获取错误返回值"""
        if return_type == DataType.INT or return_type == DataType.UINT:
            return 1  # E_NOT_OK
        elif return_type == DataType.BOOLEAN:
            return 0  # FALSE
        elif return_type == DataType.POINTER:
            return "*none*"
        else:
            return 1

class DomainSpecificTestStrategy(ITestStrategy):
    """领域特定测试策略（占位符实现）"""
    
    def generate_test_scenarios(self, function: Function, 
                              analysis_result: Dict) -> List[Dict]:
        """生成测试场景"""
        # TODO: 实现领域特定的测试策略
        # 可以根据特定领域（如汽车电子、通信协议等）定制测试场景
        basic_strategy = BasicTestStrategy()
        return basic_strategy.generate_test_scenarios(function, analysis_result)
    
    def determine_test_data(self, scenario: Dict, 
                          function: Function) -> Dict[str, Any]:
        """确定测试数据"""
        # TODO: 实现领域特定的测试数据生成
        basic_strategy = BasicTestStrategy()
        return basic_strategy.determine_test_data(scenario, function)

class TessyFormatter(IFormatter):
    """Tessy格式化器"""
    
    def format_test_suite(self, test_suite: TestSuite) -> str:
        """格式化测试套件"""
        output = ["$testobject {", ""]
        
        for i, test_case in enumerate(test_suite.test_cases, 1):
            output.extend(self._format_test_case(test_case, i))
            output.append("")
        
        output.append("}")
        return "\n".join(output)
    
    def _format_test_case(self, test_case: TestCase, case_id: int) -> List[str]:
        """格式化单个测试用例"""
        lines = [
            f"    $testcase {case_id} {{",
            f'        $name ""',
            f'        $uuid ""',
            "",
            f"        $teststep {case_id}.1 {{",
            f'            $name ""',
            f'            $uuid ""'
        ]
        
        # 添加stub函数
        if test_case.stub_functions:
            lines.append("            $stubfunctions {")
            for func_name, func_body in test_case.stub_functions.items():
                lines.append(f"                {func_name} '''{func_body}'''")
            lines.append("            }")
        
        # 添加输入
        if test_case.inputs:
            lines.append("            $inputs {")
            for param_name, value in test_case.inputs.items():
                lines.append(f"                {param_name} = {value}")
            lines.append("            }")
        
        # 添加输出
        if test_case.expected_outputs:
            lines.append("            $outputs {")
            for output_name, value in test_case.expected_outputs.items():
                lines.append(f"                {output_name} {value}")
            lines.append("            }")
        
        # 添加调用跟踪
        lines.extend([
            "            $calltrace {",
            "                *** Ignore Call Trace ***",
            "            }",
            "        }",
            "    }"
        ])
        
        return lines

class JsonFormatter(IFormatter):
    """JSON格式化器"""
    
    def format_test_suite(self, test_suite: TestSuite) -> str:
        """格式化测试套件"""
        import json
        
        data = {
            'function_name': test_suite.function_name,
            'coverage_target': test_suite.coverage_target,
            'metadata': test_suite.metadata,
            'test_cases': []
        }
        
        for test_case in test_suite.test_cases:
            case_data = {
                'id': test_case.id,
                'name': test_case.name,
                'description': test_case.description,
                'type': test_case.test_type.value,
                'inputs': test_case.inputs,
                'expected_outputs': test_case.expected_outputs,
                'stub_functions': test_case.stub_functions
            }
            data['test_cases'].append(case_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)

class XmlFormatter(IFormatter):
    """XML格式化器（占位符实现）"""
    
    def format_test_suite(self, test_suite: TestSuite) -> str:
        """格式化测试套件"""
        # TODO: 实现XML格式输出
        json_formatter = JsonFormatter()
        return json_formatter.format_test_suite(test_suite)



# ==================== 核心框架类 ====================

class TestCaseGenerationFramework:
    """测试用例生成框架主类"""
    
    def __init__(self, 
                 parser: IParser,
                 analyzer: IAnalyzer,
                 strategy: ITestStrategy,
                 formatter: IFormatter,
                 config: Optional[Dict] = None):
        self.parser = parser
        self.analyzer = analyzer
        self.strategy = strategy
        self.formatter = formatter
        self.config = config or {}
        self.constants = {}
        self.global_context = {}
    
    def generate_test_cases(self, 
                          file_path: str, 
                          function_name: str,
                          options: Optional[Dict] = None) -> str:
        """主要的测试用例生成流程"""
        
        # 1. 解析阶段
        print(f"正在解析文件: {file_path}")
        logger.info(f"正在解析文件: {file_path}")
        parse_result = self.parser.parse_file(file_path)
        self.constants = self.parser.extract_constants()
        
        # 2. 提取目标函数
        print(f"正在提取函数: {function_name}")
        target_function = self.parser.extract_function(function_name)
        
        # 3. 分析阶段
        print(f"正在分析函数: {function_name}")
        analysis_result = self._analyze_function(target_function)
        
        # 4. 生成测试场景
        print("正在生成测试场景...")
        test_scenarios = self.strategy.generate_test_scenarios(
            target_function, analysis_result)
        
        # 5. 生成测试用例
        print("正在生成测试用例...")
        test_cases = self._generate_test_cases(
            target_function, test_scenarios, options)
        
        # 6. 创建测试套件
        test_suite = TestSuite(
            function_name=function_name,
            test_cases=test_cases,
            metadata={
                'file_path': file_path,
                'generation_time': self._get_timestamp(),
                'complexity': analysis_result.get('complexity', 0),
                'coverage_paths': len(test_scenarios)
            }
        )
        
        # 7. 格式化输出
        print("正在格式化输出...")
        return self.formatter.format_test_suite(test_suite)
    
    def _analyze_function(self, function: Function) -> Dict[str, Any]:
        """分析函数"""
        control_flow = self.analyzer.analyze_control_flow(function)
        data_flow = self.analyzer.analyze_data_flow(function)
        complexity = self.analyzer.calculate_complexity(function)
        
        return {
            'control_flow': control_flow,
            'data_flow': data_flow,
            'complexity': complexity,
            'function': function
        }
    
    def _generate_test_cases(self, 
                           function: Function,
                           scenarios: List[Dict],
                           options: Optional[Dict]) -> List[TestCase]:
        """生成测试用例"""
        test_cases = []
        
        for i, scenario in enumerate(scenarios, 1):
            # 确定测试数据
            test_data = self.strategy.determine_test_data(scenario, function)
            
            # 创建测试用例
            test_case = TestCase(
                id=i,
                name=scenario.get('name', f'Test case {i}'),
                description=scenario.get('description', ''),
                test_type=TestCaseType(scenario.get('type', 'normal')),
                inputs=test_data.get('inputs', {}),
                expected_outputs=test_data.get('outputs', {}),
                stub_functions=test_data.get('stubs', {}),
                preconditions=scenario.get('preconditions', []),
                postconditions=scenario.get('postconditions', [])
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

# ==================== 配置管理 ====================

class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'coverage_target': 0.85,
        'max_test_cases': 50,
        'include_boundary_tests': True,
        'include_error_tests': True,
        'generate_stubs': True,
        'output_format': 'tessy',
        'naming_convention': 'descriptive'
    }
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict:
        """加载配置"""
        config = cls.DEFAULT_CONFIG.copy()
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                config.update(user_config)
            except FileNotFoundError:
                print(f"配置文件 {config_path} 未找到，使用默认配置")
        
        return config
    
    @classmethod
    def validate_config(cls, config: Dict) -> bool:
        """验证配置的有效性"""
        required_keys = ['coverage_target', 'max_test_cases', 'output_format']
        
        for key in required_keys:
            if key not in config:
                print(f"配置缺少必需的键: {key}")
                return False
        
        # 验证数值范围
        if not 0 <= config['coverage_target'] <= 1:
            print("coverage_target 必须在 0-1 之间")
            return False
        
        if config['max_test_cases'] <= 0:
            print("max_test_cases 必须大于 0")
            return False
        
        return True

class Logger:
    """简单的日志记录器"""
    
    def __init__(self, level: str = 'INFO'):
        self.level = level
        self.levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    
    def _should_log(self, level: str) -> bool:
        return self.levels.get(level, 1) >= self.levels.get(self.level, 1)
    
    def debug(self, message: str):
        if self._should_log('DEBUG'):
            print(f"[DEBUG] {message}")
    
    def info(self, message: str):
        if self._should_log('INFO'):
            print(f"[INFO] {message}")
    
    def warning(self, message: str):
        if self._should_log('WARNING'):
            print(f"[WARNING] {message}")
    
    def error(self, message: str):
        if self._should_log('ERROR'):
            print(f"[ERROR] {message}")

# 全局日志实例
logger = Logger()


# ==================== 工厂类 ====================

class ComponentFactory:
    """组件工厂"""
    
    @staticmethod
    def create_parser(parser_type: str = 'regex') -> IParser:
        """创建解析器"""
        if parser_type == 'regex':
            return RegexCParser()
        elif parser_type == 'ast':
            return ASTCParser()
        else:
            raise ValueError(f"不支持的解析器类型: {parser_type}")
    
    @staticmethod
    def create_analyzer(analyzer_type: str = 'basic') -> IAnalyzer:
        """创建分析器"""
        if analyzer_type == 'basic':
            return BasicCodeAnalyzer()
        elif analyzer_type == 'advanced':
            return AdvancedCodeAnalyzer()
        else:
            raise ValueError(f"不支持的分析器类型: {analyzer_type}")
    
    @staticmethod
    def create_strategy(strategy_type: str = 'comprehensive') -> ITestStrategy:
        """创建测试策略"""
        if strategy_type == 'basic':
            return BasicTestStrategy()
        elif strategy_type == 'comprehensive':
            return ComprehensiveTestStrategy()
        elif strategy_type == 'domain_specific':
            return DomainSpecificTestStrategy()
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
    
    @staticmethod
    def create_formatter(format_type: str = 'tessy') -> IFormatter:
        """创建格式化器"""
        if format_type == 'tessy':
            return TessyFormatter()
        elif format_type == 'json':
            return JsonFormatter()
        elif format_type == 'xml':
            return XmlFormatter()
        else:
            raise ValueError(f"不支持的格式化器类型: {format_type}")

# ==================== 主入口类 ====================

class TestCaseGenerator:
    """测试用例生成器主入口"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigManager.load_config(config_path)
        self.framework = None
        self._initialize_framework()
    
    def _initialize_framework(self):
        """初始化框架"""
        parser = ComponentFactory.create_parser('regex')
        analyzer = ComponentFactory.create_analyzer('basic')
        strategy = ComponentFactory.create_strategy('comprehensive')
        formatter = ComponentFactory.create_formatter('tessy')
        
        self.framework = TestCaseGenerationFramework(
            parser=parser,
            analyzer=analyzer,
            strategy=strategy,
            formatter=formatter,
            config=self.config
        )
    
    def generate(self, 
                file_path: str, 
                function_name: str,
                output_path: Optional[str] = None,
                **options) -> str:
        """生成测试用例"""
        
        # 生成测试用例
        result = self.framework.generate_test_cases(
            file_path, function_name, options)
        
        # 保存到文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"测试用例已保存到: {output_path}")
        
        return result
    
    def batch_generate(self, 
                      file_functions: List[Tuple[str, str]],
                      output_dir: str = './test_cases/') -> Dict[str, str]:
        """批量生成测试用例"""
        import os
        
        results = {}
        os.makedirs(output_dir, exist_ok=True)
        
        for file_path, function_name in file_functions:
            try:
                output_file = os.path.join(
                    output_dir, f"{function_name}_test.txt")
                result = self.generate(file_path, function_name, output_file)
                results[function_name] = result
                print(f"✓ 成功生成 {function_name} 的测试用例")
            except Exception as e:
                print(f"✗ 生成 {function_name} 的测试用例失败: {str(e)}")
                results[function_name] = None
        
        return results
