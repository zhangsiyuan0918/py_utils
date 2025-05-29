import re
import subprocess
from xml.dom import minidom
import xml.etree.ElementTree as ET
import os
import glob
from datetime import datetime

class TessyManager:
    def __init__(self, tbs_file="uploads/batch_test.tbs", report_path="D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\report"):
        self.tbs_file = tbs_file
        self.report_path = report_path
    
    def connect_tessy(self):
        """连接到Tessy"""
        try:
            subprocess.run(['tessycmd', 'connect'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Connected to Tessy')
            return True
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return False

    def get_tessy_project_list(self):
        """获取Tessy项目列表"""
        try:
            result = subprocess.run(['tessycmd', 'list-projects'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8')
            if output == '':
                print('No projects found')
                return []
            else:
                return output.splitlines()
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return []

    def select_tessy_project(self, project_name):
        """选择Tessy项目"""
        try:
            subprocess.run(['tessycmd', 'select-project', project_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Selected project: ', project_name)
            return True
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return False

    def get_tessy_test_collections(self):
        """获取测试集合"""
        try:
            result = subprocess.run(['tessycmd', 'list-test-collections'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8')
            if output == '':
                print('No test collections found')
                return []
            else:
                return output.splitlines()
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return []

    def select_test_collection(self, collection_name):
        """选择测试集合"""
        try:
            subprocess.run(['tessycmd', 'select-test-collection', collection_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Selected test collection: ', collection_name)
            return True
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return False

    def get_tessy_test_modules(self):
        """获取测试模块"""
        try:
            result = subprocess.run(['tessycmd', 'list-modules', '-test-collection'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8')
            if output == '':
                print('No test modules found')
                return []
            else:
                return output.splitlines()
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return []

    def update_tessy_test_object(self, test_object_name):
        """更新测试对象"""
        test_modules = self.get_tessy_test_modules()
        for test_module in test_modules:
            try:
                subprocess.run(['tessycmd', 'select-module', '-test-collection', test_module], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result = subprocess.run(['tessycmd', 'list-test-objects'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result == '':
                    print('No test objects found')
                else:
                    test_objects = result.stdout.decode('utf-8').splitlines()
                    for test_object in test_objects:
                        if test_object == test_object_name:
                            subprocess.run(['tessycmd', 'select-test-object', test_object], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            print('Selected test object in module: ', test_object, test_module)
                            self.save_tbs_file(test_module, test_object)
                            return True
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode('utf-8')
                print(f"An error occurred: {error_message}")
        return False

    def save_tbs_file(self, test_module, test_object):
        """保存TBS文件"""
        tree = ET.parse(self.tbs_file)
        root = tree.getroot()
        testcollection = root.find('elements/testcollection')
        if testcollection is None:
            raise ValueError("Test collection 'UnitTest' not found")

        module_element = testcollection.find(f"module[@name='{test_module}']")
        if module_element is None:
            module_element = ET.SubElement(testcollection, 'module', {'name': test_module})

        for testobj in module_element.findall('testobject'):
            module_element.remove(testobj)

        new_testobject = ET.SubElement(module_element, 'testobject', {'name': test_object})

        tree.write(self.tbs_file, xml_declaration=True, encoding='utf-8', method="xml")
        with open(self.tbs_file, 'w', encoding='utf-8') as file:
            file.write(self.prettify_xml(root))

    def prettify_xml(self, element):
        """格式化XML"""
        rough_string = ET.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        pretty_xml = '\n'.join([line for line in pretty_xml.splitlines() if line.strip() != ''])
        return pretty_xml

    def execute_tessy_test_object(self, file):
        """执行测试对象"""
        try:
            subprocess.run(['tessycmd', 'import', '-set-passing', file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('File imported successfully')
            subprocess.run(['tessycmd', 'exec-test', self.tbs_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Test object executed successfully')
            return True
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")
            return False

    def check_report_coverage(self, report_file):
        """检查报告覆盖率"""
        try:
            tree = ET.parse(report_file)
            root = tree.getroot()
            c0_element = root.find('.//coverage/c0')
            c1_element = root.find('.//coverage/c1')

            c0_percentage = float(c0_element.get('percentage'))
            c1_percentage = float(c1_element.get('percentage'))
            
            return c0_percentage >= 85 and c1_percentage >= 85
        except Exception as e:
            print(f"Error checking coverage: {e}")
            return False

    def tessy_project_init(self):
        """初始化Tessy项目"""
        if not self.connect_tessy():
            return False
        
        project_list = self.get_tessy_project_list()
        if not project_list:
            return False
        
        if not self.select_tessy_project(project_list[0]):
            return False
        
        test_collections = self.get_tessy_test_collections()
        if not test_collections:
            return False
        
        if not self.select_test_collection(test_collections[0]):
            return False
        
        print("Tessy project initialized with default settings.")
        return True

    def get_xml_report(self, case_name):
        """获取XML报告"""
        search_path = os.path.join(self.report_path, '*.xml')
        files = glob.glob(search_path)
        
        filtered_files = [f for f in files if case_name in os.path.basename(f) and not f.endswith('.notes.xml')]
        
        if not filtered_files:
            raise FileNotFoundError(f"No matching XML report found for test case '{case_name}'")
        
        latest_file = max(filtered_files, key=os.path.getmtime)
        return latest_file

    def get_txt_report(self, case_name):
        """获取TXT报告"""
        search_path_c0 = os.path.join(self.report_path, '*.c0.txt')
        search_path_c1 = os.path.join(self.report_path, '*.c1.txt')
        
        files_c0 = glob.glob(search_path_c0)
        files_c1 = glob.glob(search_path_c1)
        
        filtered_files_c0 = [f for f in files_c0 if case_name in os.path.basename(f)]
        filtered_files_c1 = [f for f in files_c1 if case_name in os.path.basename(f)]
        
        if not filtered_files_c0 or not filtered_files_c1:
            raise FileNotFoundError(f"No matching txt reports found for test case '{case_name}'")
        
        latest_file_c0 = max(filtered_files_c0, key=os.path.getmtime)
        latest_file_c1 = max(filtered_files_c1, key=os.path.getmtime)
        
        return latest_file_c0, latest_file_c1

    @staticmethod
    def extract_testobject(text):
        """提取测试对象"""
        pattern = r'\$testobject\s*\{(.*?)\}'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            return ""

    @staticmethod
    def modify_text_style(script_content):
        """修改文本样式"""
        script_content = script_content.replace('```plaintext', '').replace('```c', '').replace('```', '')
        balance = 0
        for char in script_content:
            if char == '{':
                balance += 1
            elif char == '}':
                balance -= 1
        if balance > 0:
            script_content += '\n}\n' * balance
        return script_content

    @staticmethod
    def clear_all_uuids(content):
        """清除所有UUID"""
        uuid_patterns = [
            (r'\$uuid\s+"[^"]*"', r'$uuid ""'),
            (r'\$uuid\s+[^\s\n]+', r'$uuid ""'),
        ]
        processed_content = content
        for pattern, replacement in uuid_patterns:
            processed_content = re.sub(pattern, replacement, processed_content)
        return processed_content

    @staticmethod
    def read_file_content(file_path):
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
