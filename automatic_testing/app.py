import os
import re
import time
from flask import Flask, jsonify, request
import subprocess
import psutil
import urllib.parse
from tessy_utils import TessyManager

app = Flask(__name__)
# global variables
tessy_process = None
test_case = None
case_content = []
tessy_manager = TessyManager()


@app.route('/')
def home():
    return "Welcome to the Code Generate Demo API!"

@app.route('/start_tessy', methods=['POST'])
def start_tessy():
    if is_tessy_running():
        return jsonify({"output": "Tessy.exe is already running"}), 200
    global tessy_process
    tessy_command = 'Tessy.exe'  
    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({"error": "File path is required"}), 400
    try:
        tessy_process = subprocess.Popen([tessy_command, '--file', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(30)  # Wait for Tessy to start
        if is_tessy_running():
            tessy_message = "Tessy.exe opened successfully\n"
        else:
            tessy_message = "Tessy.exe failed to open\n"
        return jsonify({"output": tessy_message})
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        return jsonify({"error": error_message}), 500

@app.route('/set_env', methods=['POST'])
def set_env():
    global test_case
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    save_directory = 'data'
    save_path = os.path.join(save_directory, file.filename)
    file.save(save_path)
    time.sleep(10)

    if not tessy_manager.tessy_project_init():
            return jsonify({"error": "Failed to initialize Tessy project"}), 500
    # tessy.tessy_project_init()
    filename_without_extension = os.path.splitext(file.filename)[0]
    test_case = filename_without_extension

    if not tessy_manager.update_tessy_test_object(filename_without_extension):
        return jsonify({"error": "Failed to update test object"}), 500
    # tessy.update_tessy_test_object(filename_without_extension)
    return jsonify({"output": "环境配置完成..."})

@app.route('/run_case', methods=['GET'])
def run_case():
    file_path = os.path.join('data', test_case + '.script')
    print('file_path:', file_path)
    if not tessy_manager.execute_tessy_test_object(file_path):
        return jsonify({"error": "Failed to execute test case"}), 500
    
    case_content.clear()
    return jsonify({"output": "Case is running..."})

@app.route('/report_status', methods=['GET'])
def report_status():
    time.sleep(10)
    try:
        report = tessy_manager.get_xml_report(test_case)
        is_success = tessy_manager.check_report_coverage(report)
        if is_success:
            return jsonify({'message': 'Success', 'report': report}), 200
        else:
            return jsonify({'message': 'Failed', 'info': 'Test case failed'}), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/get_report', methods=['GET'])
def get_report():
    try:
        report_c0, report_c1 = tessy_manager.get_txt_report(test_case)
        
        content_c0 = tessy_manager.read_file_content(report_c0)
        content_c1 = tessy_manager.read_file_content(report_c1)
        
        report_data = {
            'c0_content': content_c0,
            'c1_content': content_c1
        }
        
        return jsonify(report_data), 200
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/generate_case', methods=['POST'])
def generate_case():
    try:
        script_content = request.args.get('script_content')
        print('script_content:', script_content)
        if script_content is None:
            return jsonify({'error': 'Missing script_content parameter'}), 400
        
        script_content = tessy_manager.modify_text_style(script_content)
        case_content.append(script_content)
        
        file_name = f'{test_case}.script'
        file_path = os.path.join('data', file_name)
        os.makedirs('data', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(script_content.splitlines(keepends=True))
        return jsonify({'message': 'Script generated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/split_case', methods=['POST'])
def split_case():
    try:
        script_content = request.args.get('script_content')
        if script_content is None:
            return jsonify({'error': 'Missing script_content parameter'}), 400
        
        decoded_content = urllib.parse.unquote(script_content)
        
        cleaned_content = re.sub(r'\btestcase\d+:\b', '', decoded_content)
        processed_content = tessy_manager.clear_all_uuids(cleaned_content)
        case_content.append(processed_content)
        
        return jsonify({
            'message': 'Script generated successfully',
            'processed_content': processed_content
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_case', methods=['GET'])
def save_case():
    try:
        if not case_content:
            return jsonify({'error': 'No case content to save'}), 400
        
        res = '$testobject{\n'
        for i in case_content:
            i = re.sub(r'testcase\d+:', '', i)
            i = tessy_manager.modify_text_style(i)
            res += i + '\n'
        res += '}'
        
        file_name = f'{test_case}.script'
        file_path = os.path.join('data', file_name)
        os.makedirs('data', exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(res.splitlines(keepends=True))
        return jsonify({'message': 'Script generated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def is_tessy_running():
    """检查Tessy是否正在运行"""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'TESSY.exe':
            return True
    return False


# @app.route('/report_status', methods=['GET'])
# def report_status():
#     # 等待case执行完成
#     time.sleep(10)
#     report = tessy.get_xml_report(test_case)
#     is_success = tessy.check_report_coverge(report)
#     if is_success:
#         return jsonify({'message': 'Success', 'report': report}), 200
#     else:
#         return jsonify({'message': 'Failed', 'info': 'Test case failed'}), 200
    
# @app.route('/get_report', methods=['GET'])
# def get_report():
#     try:
#         report_c0, report_c1 = tessy.get_txt_report(test_case)
        
#         # 读取文件内容
#         content_c0 = read_file_content(report_c0)
#         content_c1 = read_file_content(report_c1)
        
#         # 将内容存储到字典中
#         report_data = {
#             'c0_content': content_c0,
#             'c1_content': content_c1
#         }
#         print('report_data: ', report_data)
        
#         # 返回JSON响应
#         return jsonify(report_data), 200
#     except FileNotFoundError as e:
#         return jsonify({'error': str(e)}), 404

# @app.route('/generate_case', methods=['POST'])
# def generate_case():
#     try:
#         # 获取前端发送的数据
#         script_content = request.args.get('script_content')
#         print('script_content:', script_content)
#         if script_content is None:
#             return jsonify({'error': 'Missing script_content parameter'}), 400
        
#         script_content = modify_text_style(script_content)
#         case_content.append(script_content)
#         print('case_content:', case_content)
#         # 定义文件名和路径
#         # file_name = 'test.script'
#         file_name = f'{test_case}.script'
#         file_path = os.path.join('data', file_name)
#         # 确保上传目录存在
#         os.makedirs('data', exist_ok=True)
#         # 将内容写入文件
#         with open(file_path, 'w', encoding='utf-8') as file:
#             file.writelines(script_content.splitlines(keepends=True))
#         return jsonify({'message': 'Script generated successfully'}), 200
#     except Exception as e:
#         # 捕获所有异常并返回错误信息
#         return jsonify({'error': str(e)}), 500



# @app.route('/split_case', methods=['POST'])
# def split_case():
#     try:
#         # 获取前端发送的数据
#         script_content = request.args.get('script_content')
#         if script_content is None:
#             return jsonify({'error': 'Missing script_content parameter'}), 400
#         # script_content = re.sub(r'\btestcase\d+:\b', '', script_content)
#         print(f"原始URL编码内容: {script_content}")
        
#         # URL解码
#         decoded_content = urllib.parse.unquote(script_content)
#         print(f"解码后内容: {decoded_content}")
#         # 原有的清理逻辑：移除testcase标签
#         cleaned_content = re.sub(r'\btestcase\d+:\b', '', decoded_content)
#         # 新增：UUID检查和处理
#         processed_content = clear_all_uuids(cleaned_content)
#         case_content.append(processed_content)
#         return jsonify({
#             'message': 'Script generated successfully',
#             'processed_content': processed_content
#         }), 200
#     except Exception as e:
#         # 捕获所有异常并返回错误信息
#         return jsonify({'error': str(e)}), 500

# @app.route('/save_case', methods=['GET'])
# def save_case():
#     try:
#         if case_content is None:
#             return jsonify({'error': 'Missing case_content parameter'}), 400
#         res = '$testobject{\n'
#         for i in case_content:
#             i = re.sub(r'testcase\d+:', '', i)
#             i = modify_text_style(i)
#             res += i + '\n'
#         res += '}'
#         # 定义文件名和路径
#         # file_name = 'test.script'
#         file_name = f'{test_case}.script'
#         file_path = os.path.join('data', file_name)
#         # 确保上传目录存在
#         os.makedirs('data', exist_ok=True)
#         # 将内容写入文件
#         with open(file_path, 'w', encoding='utf-8') as file:
#             file.writelines(res.splitlines(keepends=True))
#         return jsonify({'message': 'Script generated successfully'}), 200
#     except Exception as e:
#         # 捕获所有异常并返回错误信息
#         return jsonify({'error': str(e)}), 500


# def is_tessy_running():
#     for proc in psutil.process_iter(['pid', 'name']):
#         if proc.info['name'] == 'TESSY.exe':
#             return True
#     return False
    

# def modify_text_style(script_content):
#     script_content = script_content.replace('```plaintext', '').replace('```c', '').replace('```', '')
#     balance = 0
#     for char in script_content:
#         if char == '{':
#             balance += 1
#         elif char == '}':
#             balance -= 1
#     if balance > 0:
#         script_content += '\n}\n' * balance
#         # script_content += '}' * balance

#     return script_content


# def read_file_content(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         return file.read()

# def clear_all_uuids(content):
#     uuid_patterns = [
#         # 匹配 $uuid "任何内容" 格式，替换为 $uuid ""
#         (r'\$uuid\s+"[^"]*"', r'$uuid ""'),
        
#         # 匹配 $uuid 后跟非引号内容的格式，替换为 $uuid ""
#         (r'\$uuid\s+[^\s\n]+', r'$uuid ""'),
#     ]
#     processed_content = content
#     for pattern, replacement in uuid_patterns:
#         processed_content = re.sub(pattern, replacement, processed_content)
    
#     return processed_content


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=5001)
    # print(is_tessy_running())
    # test_with_your_data()
