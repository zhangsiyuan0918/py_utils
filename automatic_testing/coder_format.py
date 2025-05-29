#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码格式化工具
支持多种编程语言的代码格式化，包括C/C++、Python、JavaScript、Java等
"""

import os
import sys
import json
import argparse
import re
from typing import Dict, List, Optional
from pathlib import Path


class CodeFormatter:
    """代码格式化器主类"""
    
    def __init__(self):
        self.indent_size = 4
        self.use_tabs = False
        self.max_line_length = 120
        
    def detect_language(self, file_path: str) -> str:
        """根据文件扩展名检测编程语言"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.php': 'php',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(ext, 'unknown')
    
    def get_indent_string(self) -> str:
        """获取缩进字符串"""
        return '\t' if self.use_tabs else ' ' * self.indent_size
    
    def format_c_code(self, code: str) -> str:
        """格式化C/C++代码"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                formatted_lines.append('')
                continue
            
            # 处理多行注释
            if '/*' in stripped and '*/' not in stripped:
                in_multiline_comment = True
            elif '*/' in stripped:
                in_multiline_comment = False
            
            # 如果在多行注释中，保持原有格式
            if in_multiline_comment or stripped.startswith('*'):
                formatted_lines.append(self.get_indent_string() * indent_level + stripped)
                continue
            
            # 处理预处理指令
            if stripped.startswith('#'):
                formatted_lines.append(stripped)
                continue
            
            # 减少缩进的情况
            if any(stripped.startswith(keyword) for keyword in ['}', 'case ', 'default:']):
                if stripped.startswith('}'):
                    indent_level = max(0, indent_level - 1)
            
            # 添加格式化的行
            formatted_line = self.get_indent_string() * indent_level + stripped
            formatted_lines.append(formatted_line)
            
            # 增加缩进的情况
            if stripped.endswith('{') or stripped.endswith(':') and not stripped.startswith('case'):
                indent_level += 1
            
            # 特殊处理switch语句
            if stripped.startswith('case ') or stripped.startswith('default:'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def format_python_code(self, code: str) -> str:
        """格式化Python代码"""
        try:
            import autopep8
            return autopep8.fix_code(code, options={'max_line_length': self.max_line_length})
        except ImportError:
            # 如果没有autopep8，使用简单的格式化
            return self._simple_python_format(code)
    
    def _simple_python_format(self, code: str) -> str:
        """简单的Python代码格式化"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                formatted_lines.append('')
                continue
            
            # 减少缩进
            if any(stripped.startswith(keyword) for keyword in ['except', 'elif', 'else', 'finally']):
                current_indent = max(0, indent_level - 1)
            else:
                current_indent = indent_level
            
            # 添加格式化的行
            formatted_line = self.get_indent_string() * current_indent + stripped
            formatted_lines.append(formatted_line)
            
            # 增加缩进
            if stripped.endswith(':') and not stripped.startswith('#'):
                indent_level += 1
            
            # 减少缩进（用于下一行）
            if any(stripped.startswith(keyword) for keyword in ['return', 'break', 'continue', 'pass', 'raise']):
                if not stripped.endswith(':'):
                    # 这些语句后面通常会减少缩进
                    pass
        
        return '\n'.join(formatted_lines)
    
    def format_javascript_code(self, code: str) -> str:
        """格式化JavaScript代码"""
        # 简单的JavaScript格式化
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                formatted_lines.append('')
                continue
            
            # 减少缩进
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)
            
            # 添加格式化的行
            formatted_line = self.get_indent_string() * indent_level + stripped
            formatted_lines.append(formatted_line)
            
            # 增加缩进
            if stripped.endswith('{'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def format_code(self, code: str, language: str) -> str:
        """根据语言类型格式化代码"""
        if language in ['c', 'cpp']:
            return self.format_c_code(code)
        elif language == 'python':
            return self.format_python_code(code)
        elif language in ['javascript', 'typescript']:
            return self.format_javascript_code(code)
        else:
            # 对于其他语言，使用通用的大括号格式化
            return self.format_c_code(code)
    
    def format_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """格式化文件"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            language = self.detect_language(input_path)
            formatted_content = self.format_code(content, language)
            
            output_file = output_path or input_path
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"✓ 已格式化: {input_path} -> {output_file}")
            return True
            
        except Exception as e:
            print(f"✗ 格式化失败 {input_path}: {str(e)}")
            return False
    
    def format_to_json(self, code: str, language: str) -> str:
        """将代码格式化并转换为JSON格式"""
        formatted_code = self.format_code(code, language)
        # 转义特殊字符用于JSON
        escaped_code = formatted_code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        json_data = {
            "function_body": escaped_code,
            "language": language,
            "formatted_at": self._get_timestamp()
        }
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代码格式化工具')
    parser.add_argument('input', help='输入文件路径或代码字符串')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-l', '--language', help='指定编程语言')
    parser.add_argument('-i', '--indent', type=int, default=4, help='缩进大小（默认4）')
    parser.add_argument('-t', '--tabs', action='store_true', help='使用制表符缩进')
    parser.add_argument('-j', '--json', action='store_true', help='输出为JSON格式')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理目录')
    parser.add_argument('--max-line-length', type=int, default=120, help='最大行长度')
    
    args = parser.parse_args()
    
    # 创建格式化器
    formatter = CodeFormatter()
    formatter.indent_size = args.indent
    formatter.use_tabs = args.tabs
    formatter.max_line_length = args.max_line_length
    
    # 处理输入
    if os.path.isfile(args.input):
        # 单个文件
        language = args.language or formatter.detect_language(args.input)
        
        if args.json:
            # 输出为JSON格式
            with open(args.input, 'r', encoding='utf-8') as f:
                code = f.read()
            
            json_output = formatter.format_to_json(code, language)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"✓ JSON输出已保存到: {args.output}")
            else:
                print(json_output)
        else:
            # 普通格式化
            formatter.format_file(args.input, args.output)
            
    elif os.path.isdir(args.input) and args.recursive:
        # 递归处理目录
        supported_extensions = ['.c', '.h', '.cpp', '.hpp', '.py', '.js', '.ts', '.java']
        
        for root, dirs, files in os.walk(args.input):
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, file)
                    formatter.format_file(file_path)
    
    else:
        # 直接处理代码字符串
        language = args.language or 'c'
        
        if args.json:
            json_output = formatter.format_to_json(args.input, language)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"✓ JSON输出已保存到: {args.output}")
            else:
                print(json_output)
        else:
            formatted_code = formatter.format_code(args.input, language)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(formatted_code)
                print(f"✓ 格式化代码已保存到: {args.output}")
            else:
                print(formatted_code)


if __name__ == '__main__':
    main()
