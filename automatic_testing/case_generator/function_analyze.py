from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json
from abc import ABC, abstractmethod

@dataclass
class FunctionInfo:
    """函数信息数据结构"""
    name: str
    return_type: str
    parameters: List[Dict[str, str]]
    body: str
    line_start: int
    line_end: int
    is_static: bool = False
    complexity: int = 0

class FunctionParser:
    """函数解析器"""
    
    def __init__(self):
        self.function_pattern = re.compile(
            r'(static\s+)?(\w+\s+\*?\s*)(\w+)\s*\(([^)]*)\)\s*\{',
            re.MULTILINE
        )
        self.parameter_pattern = re.compile(
            r'(\w+(?:\s*\*)?)\s+(\w+)(?:\s*,\s*)?'
        )
    
    def parse_file(self, file_path: str) -> List[FunctionInfo]:
        """解析C文件中的所有函数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        functions = []
        lines = content.split('\n')
        
        for match in self.function_pattern.finditer(content):
            func_info = self._extract_function_info(match, content, lines)
            if func_info:
                functions.append(func_info)
        
        return functions
    
    def _extract_function_info(self, match, content: str, lines: List[str]) -> Optional[FunctionInfo]:
        """提取单个函数的详细信息"""
        is_static = match.group(1) is not None
        return_type = match.group(2).strip()
        func_name = match.group(3)
        params_str = match.group(4).strip()
        
        # 计算函数在文件中的行号
        start_pos = match.start()
        line_start = content[:start_pos].count('\n') + 1
        
        # 提取函数体
        body_start = match.end()
        body, body_end = self._extract_function_body(content, body_start)
        line_end = content[:body_end].count('\n') + 1
        
        # 解析参数
        parameters = self._parse_parameters(params_str)
        
        return FunctionInfo(
            name=func_name,
            return_type=return_type,
            parameters=parameters,
            body=body,
            line_start=line_start,
            line_end=line_end,
            is_static=is_static
        )
    
    def _extract_function_body(self, content: str, start_pos: int) -> Tuple[str, int]:
        """提取函数体内容"""
        brace_count = 1
        pos = start_pos
        
        while pos < len(content) and brace_count > 0:
            char = content[pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            pos += 1
        
        return content[start_pos:pos-1], pos
    
    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """解析函数参数"""
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
    
    def _parse_single_parameter(self, param_str: str) -> Optional[Dict[str, str]]:
        """解析单个参数"""
        parts = param_str.strip().split()
        if len(parts) < 2:
            return None
        
        param_name = parts[-1].replace('*', '').strip()
        param_type = ' '.join(parts[:-1]).strip()
        
        return {
            'name': param_name,
            'type': param_type,
            'is_pointer': '*' in param_str,
            'is_const': 'const' in param_str
        }

class FunctionAnalyzer:
    """函数分析器"""
    
    def __init__(self):
        self.branch_patterns = [
            r'if\s*\(',
            r'for\s*\(',
            r'while\s*\(',
            r'switch\s*\(',
            r'case\s+\w+:',
        ]
        self.complexity_patterns = {
            'if': re.compile(r'if\s*\([^)]+\)', re.MULTILINE),
            'for': re.compile(r'for\s*\([^)]*;[^)]*;[^)]*\)', re.MULTILINE),
            'while': re.compile(r'while\s*\([^)]+\)', re.MULTILINE),
            'case': re.compile(r'case\s+[^:]+:', re.MULTILINE),
            'return': re.compile(r'return\s+[^;]+;', re.MULTILINE)
        }
    
    def analyze_function(self, func_info: FunctionInfo) -> Dict[str, Any]:
        """分析函数的控制流和测试点"""
        analysis = {
            'branches': self._find_branches(func_info.body),
            'variables': self._extract_variables(func_info.body),
            'constants': self._extract_constants(func_info.body),
            'return_points': self._find_return_points(func_info.body),
            'complexity': self._calculate_complexity(func_info.body),
            'test_scenarios': []
        }
        
        # 生成测试场景
        analysis['test_scenarios'] = self._generate_test_scenarios(analysis, func_info)
        return analysis
    
    def _find_branches(self, function_body: str) -> List[Dict]:
        """识别函数中的分支结构"""
        branches = []
        for pattern in self.branch_patterns:
            matches = re.finditer(pattern, function_body)
            for match in matches:
                branches.append({
                    'type': pattern.replace(r'\s*\(', '').replace(r'\(', ''),
                    'position': match.start(),
                    'condition': self._extract_condition(match, function_body)
                })
        return branches
    
    def _extract_condition(self, match, function_body: str) -> str:
        """提取条件表达式"""
        start = match.end()
        paren_count = 1
        pos = start
        
        while pos < len(function_body) and paren_count > 0:
            char = function_body[pos]
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            pos += 1
        
        return function_body[start:pos-1]
    
    def _extract_variables(self, function_body: str) -> List[Dict]:
        """提取函数中的变量"""
        var_pattern = re.compile(r'(\w+)\s+(\w+)\s*[=;]', re.MULTILINE)
        variables = []
        
        for match in var_pattern.finditer(function_body):
            variables.append({
                'type': match.group(1),
                'name': match.group(2),
                'position': match.start()
            })
        
        return variables
    
    def _extract_constants(self, function_body: str) -> Dict[str, Any]:
        """提取函数中使用的常量"""
        const_pattern = re.compile(r'\b([A-Z_][A-Z0-9_]*)\b', re.MULTILINE)
        constants = {}
        
        for match in const_pattern.finditer(function_body):
            const_name = match.group(1)
            if len(const_name) > 2:  # 过滤掉太短的匹配
                constants[const_name] = None  # 值需要从其他地方获取
        
        return constants
    
    def _find_return_points(self, function_body: str) -> List[Dict]:
        """找到所有返回点"""
        return_pattern = re.compile(r'return\s+([^;]+);', re.MULTILINE)
        return_points = []
        
        for match in return_pattern.finditer(function_body):
            return_points.append({
                'value': match.group(1).strip(),
                'position': match.start()
            })
        
        return return_points
    
    def _calculate_complexity(self, function_body: str) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for pattern_name, pattern in self.complexity_patterns.items():
            matches = pattern.findall(function_body)
            if pattern_name in ['if', 'for', 'while', 'case']:
                complexity += len(matches)
        
        return complexity

    def _generate_test_scenarios(self, analysis: Dict, func_info: FunctionInfo) -> List[Dict]:
        """基于分析结果生成测试场景"""
        scenarios = []
        
        # 正常路径测试
        scenarios.append({
            'type': 'normal_path',
            'description': 'Normal execution path',
            'expected_result': 'E_OK',
            'priority': 1
        })
        
        # 为每个分支生成失败场景
        for i, branch in enumerate(analysis['branches']):
            if 'if' in branch['type']:
                scenarios.append({
                    'type': 'branch_failure',
                    'description': f'Branch failure at condition: {branch["condition"]}',
                    'expected_result': 'E_NOT_OK',
                    'target_branch': i,
                    'priority': 2
                })
        
        # 基于返回点生成场景
        return_points = analysis['return_points']
        if len(return_points) > 1:
            for i, ret_point in enumerate(return_points):
                if 'E_NOT_OK' in ret_point['value'] or '1' in ret_point['value']:
                    scenarios.append({
                        'type': 'error_return',
                        'description': f'Error return path: {ret_point["value"]}',
                        'expected_result': 'E_NOT_OK',
                        'target_return': i,
                        'priority': 3
                    })
        
        # 边界条件测试
        for param in func_info.parameters:
            if param['type'] in ['uint32', 'int', 'uint8']:
                scenarios.append({
                    'type': 'boundary_test',
                    'description': f'Boundary test for parameter {param["name"]}',
                    'expected_result': 'E_NOT_OK',
                    'target_parameter': param['name'],
                    'priority': 2
                })
        
        return scenarios



class TestCaseGenerator:
    def __init__(self, spec_file: str):
        self.spec = self._load_specification(spec_file)
        self.case_counter = 1
        self.step_counter = 1
    
    def generate_test_cases(self, func_info: FunctionInfo, analysis: Dict) -> str:
        """生成完整的测试用例"""
        test_cases = []
        
        for scenario in analysis['test_scenarios']:
            test_case = self._generate_single_test_case(func_info, scenario, analysis)
            test_cases.append(test_case)
            self.case_counter += 1
        
        return self._wrap_in_test_object(test_cases)
    
    def _generate_single_test_case(self, func_info: FunctionInfo, scenario: Dict, analysis: Dict) -> str:
        """生成单个测试用例"""
        inputs = self._generate_inputs(func_info, scenario, analysis)
        outputs = self._generate_outputs(scenario)
        
        test_case = f"""
    $testcase {self.case_counter} {{
        $name ""
        $uuid ""

        $teststep {self.case_counter}.1 {{
            $name ""
            $uuid ""
            $inputs {{
{inputs}
            }}
            $outputs {{
{outputs}
            }}
            $calltrace {{
                *** Ignore Call Trace ***
            }}
        }}
    }}"""
        
        return test_case
    
    def _generate_inputs(self, func_info: FunctionInfo, scenario: Dict, analysis: Dict) -> str:
        """生成输入参数"""
        inputs = []
        
        for param in func_info.parameters:
            param_name = param['name']
            param_type = param['type']
            
            if scenario['type'] == 'normal_path':
                value = self._get_normal_value(param_name, param_type, analysis)
            else:
                value = self._get_failure_value(param_name, param_type, scenario, analysis)
            
            inputs.append(f"                {param_name} = {value}")
        
        return '\n'.join(inputs)
    
    def _generate_outputs(self, scenario: Dict) -> str:
        """生成期望输出"""
        if scenario['expected_result'] == 'E_OK':
            return "                return 0"
        else:
            return "                return 1"
    
    def _wrap_in_test_object(self, test_cases: List[str]) -> str:
        """包装成完整的测试对象"""
        cases_str = '\n'.join(test_cases)
        return f"""$testobject {{
{cases_str}
}}"""
