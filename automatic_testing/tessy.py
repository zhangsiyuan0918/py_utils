import re
import subprocess
from xml.dom import minidom
import xml.etree.ElementTree as ET
import os
import glob
from datetime import datetime

tbs_file = "uploads/batch_test.tbs"
report_path = "D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\report"
# tbs_file = "D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\batch_test.tbs"

def connect_tessy():
    try:
        subprocess.run(['tessycmd', 'connect'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Connected to Tessy')
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")

def get_tessy_project_list():
    try:
        result = subprocess.run(['tessycmd', 'list-projects'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        if output == '':
            print('No projects found')
        else:
            return output.splitlines()
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")

def select_tessy_project(project_name):
    try:
        subprocess.run(['tessycmd', 'select-project', project_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Selected project: ', project_name)
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")

def get_tessy_test_collections():
    try:
        result = subprocess.run(['tessycmd', 'list-test-collections'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        if output == '':
            print('No test collections found')
        else:
            return output.splitlines()
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")


def select_test_collection(collection_name):
    try:
        subprocess.run(['tessycmd', 'select-test-collection', collection_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Selected test collection: ', collection_name)
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")


def get_tessy_test_modules():
    try:
        result = subprocess.run(['tessycmd', 'list-modules', '-test-collection'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        if output == '':
            print('No test modules found')
        else:
            return output.splitlines()
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")


def update_tessy_test_object(test_object_name):
    test_modules = get_tessy_test_modules()
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
                        # UpdateObject To .tbs file
                        save_tbs_file(test_module, test_object)
                        return
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode('utf-8')
            print(f"An error occurred: {error_message}")


def save_tbs_file(test_module, test_object):
    tree = ET.parse(tbs_file)
    root = tree.getroot()
    # Find the testcollection with name 'UnitTest'
    testcollection = root.find('elements/testcollection')
    if testcollection is None:
        raise ValueError("Test collection 'UnitTest' not found")

    # Find the module with the given name or create a new one if it doesn't exist
    module_element = testcollection.find(f"module[@name='{test_module}']")
    if module_element is None:
        module_element = ET.SubElement(testcollection, 'module', {'name': test_module})

    # Remove existing testobject elements
    for testobj in module_element.findall('testobject'):
        module_element.remove(testobj)

    # Add the new testobject with proper indentation and newline
    new_testobject = ET.SubElement(module_element, 'testobject', {'name': test_object})

    # Save the modified tree back to the file
    tree.write(tbs_file, xml_declaration=True, encoding='utf-8', method="xml")
    with open(tbs_file, 'w', encoding='utf-8') as file:
        file.write(prettify_xml(root))

def prettify_xml(element):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    # Remove unnecessary newlines
    pretty_xml = '\n'.join([line for line in pretty_xml.splitlines() if line.strip() != ''])
    return pretty_xml

def execute_tessy_test_object(file):
    try:
        subprocess.run(['tessycmd', 'import', '-set-passing', file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('File imported successfully')
        subprocess.run(['tessycmd', 'exec-test', tbs_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Test object executed successfully')
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"An error occurred: {error_message}")

def check_report_coverge(report_file):
    # 根据report_file，查找报告，查看覆盖率
    # 解析XML文件
    tree = ET.parse(report_file)
    root = tree.getroot()
     # 找到第5行和第6行的c0和c1元素
    c0_element = root.find('.//coverage/c0')
    c1_element = root.find('.//coverage/c1')

    # 获取c0和c1的percentage属性
    c0_percentage = float(c0_element.get('percentage'))
    c1_percentage = float(c1_element.get('percentage'))
    # 检查c0和c1的值
    if c0_percentage < 85 and c1_percentage < 85:
        return False
    return True


def tessy_project_init():
    connect_tessy()
    project_list = get_tessy_project_list()
    print(project_list[0])
    select_tessy_project(project_list[0])
    test_collections = get_tessy_test_collections()
    select_test_collection(test_collections[0])
    print("Tessy project initialized with default settings.")


def get_xml_report(case_name):
    # 定义搜索路径
    search_path = 'D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\report\\*.xml'
    # 使用glob找到所有匹配的.xml文件
    files = glob.glob(search_path)
    
    # 过滤出包含test_case名字的文件，并且排除.notes.xml文件
    filtered_files = [f for f in files if case_name in os.path.basename(f) and not f.endswith('.notes.xml')]
    
    if not filtered_files:
        raise FileNotFoundError(f"No matching XML report found for test case '{case_name}'")
    
    # 按文件的修改时间排序，获取最新的文件
    latest_file = max(filtered_files, key=os.path.getmtime)
    
    return latest_file



def get_txt_report(case_name):
    # 定义搜索路径
    search_path_c0 = 'D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\report\\*.c0.txt'
    search_path_c1 = 'D:\\svn_code\\GWM\\D01\\P08593_SCU\\Appl\\branches\\B16_B26_NoPp\\Appl_C\\Tools\\Tessy\\report\\*.c1.txt'
    # 使用glob找到所有匹配的.xml文件
    files_c0 = glob.glob(search_path_c0)
    files_c1 = glob.glob(search_path_c1)
    
     # 过滤出包含test_case名字的文件
    filtered_files_c0 = [f for f in files_c0 if case_name in os.path.basename(f)]
    filtered_files_c1 = [f for f in files_c1 if case_name in os.path.basename(f)]
    
    if not filtered_files_c0 or not filtered_files_c1:
        raise FileNotFoundError(f"No matching txt reports found for test case '{case_name}'")
    
    # 按文件的修改时间排序，获取最新的文件
    latest_file_c0 = max(filtered_files_c0, key=os.path.getmtime)
    latest_file_c1 = max(filtered_files_c1, key=os.path.getmtime)
    
    return latest_file_c0, latest_file_c1

def extract_testobject(text):
    # 使用正则表达式匹配 $testobject 块
    pattern = r'\$testobject\s*\{(.*?)\}'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return ""


if __name__ == "__main__":
    # test = 'testcase1: $testcase 1'
    # test = re.sub(r'testcase\d+:', '', test)
    # print(test)
    text = ["testcase1: $testcase 1 {\n $name ""\n $uuid ""\n\n $teststep 1.1 {\n $name ""\n $uuid ""\n $stubfunctions {\n unsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\n static int step = 0;\n switch (step) {\n case 0:\n return 1; // Case where E2E_E_OK is returned\n default:\n break;\n }\n step++;\n '''\n }\n $inputs {\n busoff_flag_External = 0\n PduInfoPtr = target_PduInfoPtr\n &target_PduInfoPtr {\n SduDataPtr = target_SduDataPtr\n SduLength = none\n }\n &target_SduDataPtr = none\n }\n $outputs {\n return 0\n &target_SduDataPtr = 0\n }\n $calltrace {\n *** Ignore Call Trace ***\n }",
            "testcase2: $testcase 2 {\n $name ""\n $uuid ""\n\n $teststep 2.1 {\n $name ""\n $uuid ""\n $stubfunctions {\n unsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\n static int step = 0;\n switch (step) {\n case 0:\n return 0; // Case where E2E_E_OK is not returned\n default:\n break;\n }\n step++;\n '''\n }\n $inputs {\n busoff_flag_External = 1\n Tx_successful_AliveCounter = 5\n PduInfoPtr = target_PduInfoPtr\n &target_PduInfoPtr {\n SduDataPtr = target_SduDataPtr\n SduLength = none\n }\n &target_SduDataPtr = none\n }\n $outputs {\n return 1\n Sta_Write_DDCM2.Counter = 5\n Tx_E2E_States_CounterBackUp = 0\n }\n $calltrace {\n *** Ignore Call Trace ***\n }", 
            "testcase3: $testcase 3 {\n $name ""\n $uuid ""\n\n $teststep 3.1 {\n $name ""\n $uuid ""\n $stubfunctions {}\n $inputs {\n busoff_flag_External = 0\n }\n $outputs {\n return 0\n }\n $calltrace {\n *** Ignore Call Trace ***\n }"]
    # text1 = "```c\n$testobject {\n\n    $testcase 1 {\n        $name \"\"\n        $uuid \"04972c0f-70aa-47cf-a62d-3ab94ce495a2\"\n\n        $teststep 1.1 {\n            $name \"\"\n            $uuid \"606747a1-4798-44d0-ac36-6e60b07477c7\"\n            $stubfunctions {\n                unsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\n                    static int step = 0;\n                    switch (step) {\n                    case 0:\n                        return E2E_E_OK; // Return a successful status\n                    default:\n                        break;\n                    }\n                    step++;\n                '''\n            }\n            $inputs {\n                busoff_flag_External = FALSE\n                Tx_successful_AliveCounter = 15\n                PduInfoPtr = target_PduInfoPtr\n                &target_PduInfoPtr {\n                    SduDataPtr = target_SduDataPtr\n                    SduLength = *none*\n                }\n                &target_SduDataPtr = *none*\n            }\n            $outputs {\n                return 1 // ret = TRUE\n            }\n            $calltrace {\n                *** Ignore Call Trace ***\n            }\n        }\n\n        $teststep 1.2 {\n            $name \"\"\n            $uuid \"606747a1-4798-44d0-ac36-6e60b07477c8\"\n            $stubfunctions {\n                unsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\n                    static int step = 0;\n                    switch (step) {\n                    case 0:\n                        return E2E_E_OK; // Return a successful status\n                    default:\n                        break;\n                    }\n                    step++;\n                '''\n            }\n            $inputs {\n                busoff_flag_External = TRUE\n                Tx_successful_AliveCounter = 15\n                PduInfoPtr = target_PduInfoPtr\n                &target_PduInfoPtr {\n                    SduDataPtr = target_SduDataPtr\n                    SduLength = *none*\n                }\n                &target_SduDataPtr = *none*\n            }\n            $outputs {\n                return 1 // ret = TRUE\n            }\n            $calltrace {\n                *** Ignore Call Trace ***\n            }\n        }\n\n    }\n\n    $testcase 2 {\n        $name \"\"\n        $uuid \"04972c0f-70aa-47cf-a62d-3ab94ce495a3\"\n\n        $teststep 2.1 {\n            $name \"\"\n            $uuid \"606747a1-4798-44d0-ac36-6e60b07477c9\"\n            $stubfunctions {\n                unsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\n                    static int step = 0;\n                    switch (step) {\n                    case 0:\n                        return E2E_E_FAIL; // Return a fail status\n                    default:\n                        break;\n                    }\n                    step++;\n                '''\n            }\n            $inputs {\n                busoff_flag_External = FALSE\n                Tx_successful_AliveCounter = 15\n                PduInfoPtr = target_PduInfoPtr\n                &target_PduInfoPtr {\n                    SduDataPtr = target_SduDataPtr\n                    SduLength = *none*\n                }\n                &target_SduDataPtr = *none*\n            }\n            $outputs {\n                return 0 // ret = FALSE\n            }\n            $calltrace {\n                *** Ignore Call Trace ***\n            }\n        }\n\n    }\n\n}\n```"
    # input_text = text1.replace('```plaintext', '').replace('```c', '').replace('```', '')
    # pattern = r'\$testcase\s+\d+[\s\S]*?\$calltrace\s*\{[^}]*\}\s*'
    # matches = re.findall(pattern, input_text)
    # testcases_list = [f"testcase{i + 1}: {match.strip()}" for i, match in enumerate(matches)]
    # print(testcases_list)
    res = ''
    for i in text:
        i = re.sub(r'testcase\d+:', '', i)
        res += i + '\n' + '}' + '\n' + '}' + '\n'
    print(res)
    # text = "``` \n$testobject {\n\n$testcase 1 {\n$name \"\"\n$uuid \"04972c0f-70aa-47cf-a62d-3ab94ce495a2\"\n\n$teststep 1.1 {\n$name \"\"\n$uuid \"606747a1-4798-44d0-ac36-6e60b07477c7\"\n$stubfunctions {\nunsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\nstatic int step = 0;\nswitch (step) {\ncase 0:\nreturn 1;\ndefault:\nbreak;\n}\nstep++;\n'''\n}\n$inputs {\nbusoff_flag_External = 0\nPduInfoPtr = target_PduInfoPtr\n&target_PduInfoPtr {\nSduDataPtr = target_SduDataPtr\nSduLength = *none*\n}\n&target_SduDataPtr = *none*\n}\n$outputs {\nreturn 0\n&target_SduDataPtr = 0\n}\n$calltrace {\n*** Ignore Call Trace ***\n}\n}\n\n$teststep 1.2 {\n$name \"\"\n$uuid \"606747a2-4798-44d0-ac36-6e60b07477c7\"\n$stubfunctions {\nunsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\nstatic int step = 0;\nswitch (step) {\ncase 0:\nreturn 0;\ndefault:\nbreak;\n}\nstep++;\n'''\n}\n$inputs {\nbusoff_flag_External = 1\nPduInfoPtr = target_PduInfoPtr\n&target_PduInfoPtr {\nSduDataPtr = target_SduDataPtr\nSduLength = *none*\n}\n&target_SduDataPtr = *none*\n}\n$outputs {\nreturn 0\n&target_SduDataPtr = 0\n}\n$calltrace {\n*** Ignore Call Trace ***\n}\n}\n\n$teststep 1.3 {\n$name \"\"\n$uuid \"606747a3-4798-44d0-ac36-6e60b07477c7\"\n$stubfunctions {\nunsigned char E2E_P01Protect(E2E_P01ConfigType * ConfigPtr, E2E_P01ProtectStateType * StatePtr, unsigned char * DataPtr) '''\nstatic int step = 0;\nswitch (step) {\ncase 0:\nreturn 1;\ndefault:\nbreak;\n}\nstep++;\n'''\n}\n$inputs {\nbusoff_flag_External = 1\nPduInfoPtr = target_PduInfoPtr\n&target_PduInfoPtr {\nSduDataPtr = target_SduDataPtr\nSduLength = *none*\n}\n&target_SduDataPtr = *none*\n}\n$outputs {\nreturn 1\n&target_SduDataPtr = *none*\n}\n$calltrace {\n*** Ignore Call Trace ***\n}\n}\n\n}\n```"
    # # text = text.replace('```', '')
    # # print(text)
    # # tessy_project_init()
    # report = get_txt_report('ComIPduCallout_DDCM2_oBODY_6c9af9b7_Tx')
    # print(report)
    # check_report_coverge(report)
    '''
    输入为一个file_list
    根据file.name在test_collection中先查找所有test_module,在根据每个module查找每个test_object,查到之后将这个文件导入，并执行
    '''