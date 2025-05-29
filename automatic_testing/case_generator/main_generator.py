from ast import Dict
from case_generator.code_analyze import CCodeParser
from case_generator.function_analyze import FunctionAnalyzer, TestCaseGenerator
from case_generator.value_generator import ValueGenerator


class TestCaseGeneratorMain:
    def __init__(self, spec_file: str):
        self.parser = CCodeParser()
        self.analyzer = FunctionAnalyzer()
        self.generator = TestCaseGenerator(spec_file)
        self.value_gen = ValueGenerator()
    
    def generate_for_function(self, source_file: str, function_name: str) -> str:
        """为指定函数生成测试用例"""
        # 解析源文件
        functions = self.parser.parse_file(source_file)
        
        # 找到目标函数
        target_func = None
        for func in functions:
            if func.name == function_name:
                target_func = func
                break
        
        if not target_func:
            raise ValueError(f"Function {function_name} not found in {source_file}")
        
        # 分析函数
        analysis = self.analyzer.analyze_function(target_func)
        
        # 生成测试用例
        test_cases = self.generator.generate_test_cases(target_func, analysis)
        
        return test_cases
    
    def generate_for_all_functions(self, source_file: str) -> Dict[str, str]:
        """为文件中所有函数生成测试用例"""
        functions = self.parser.parse_file(source_file)
        results = {}
        
        for func in functions:
            if not func.name.startswith('_'):  # 跳过私有函数
                analysis = self.analyzer.analyze_function(func)
                test_cases = self.generator.generate_test_cases(func, analysis)
                results[func.name] = test_cases
        
        return results
