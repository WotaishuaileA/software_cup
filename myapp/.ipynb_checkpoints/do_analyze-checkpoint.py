from .decode_apk import decode_apk
from .static_analyze import static_analyze_apk
from .analyze_picture import analyze_picture
from django.core.files.base import File
import threading
import os
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import markdown
import random
from .run_opcode_seq_creation import run_opcode_seq_creation
from .models import Apk,BlackPicture,Website, Permission, Cirtification
import sys
import re
import shutil
from openai import OpenAI
import pypandoc
import subprocess
import xml.dom.minidom
from xml.dom.minidom import parse
import random

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="sk-NIu5GsfVbHxF3XH9dAQ9ZfxFnXpXw0XK2Pr4TPeJIyJI8BLo",
    base_url="https://api.chatanywhere.tech/v1"
)

def md_to_html(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content)
    file_name, extension = os.path.splitext(md_file)
    with open(f"{file_name}.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_content

def gpt_35_api(messages: list):
    """为提供的对话消息创建新的回答

    Args:
        messages (list): 完整的对话消息
    """
    completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    return(completion.choices[0].message.content)


def do_analyze(apk_list):
    os.makedirs("decoded_apks", exist_ok=True)
    os.makedirs("opseq", exist_ok=True)
    os.makedirs("picture_analyze", exist_ok=True)
    os.makedirs("analyze_report", exist_ok=True)
    os.makedirs("clip", exist_ok=True)
    threads = []
    for apk_path in apk_list:
        thread = threading.Thread(target=analyze_apk, args=(apk_path,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return True

def find_icon(base_path,new_apk):
    manifest_path = os.path.join(base_path,'AndroidManifest.xml')
    if not os.path.exists(manifest_path):
        return
    dom = parse(manifest_path)
    collection = dom.documentElement
    tag = collection.getElementsByTagName("application")[0]
    # Something like: @mipmap/ic_launcher
    icon_str = tag.getAttribute("android:icon")
    if icon_str is None or icon_str == "":
        return
    matches = re.match(r'@(.*)\/(.*)', icon_str)
    path_name = matches.group(1)
    icon_name = matches.group(2)
    base_path = os.path.join(base_path,'res')
    ls = os.listdir(base_path)
    for p in ls:
        if p.startswith(path_name):
            path = os.path.join(base_path, p, icon_name+".png")
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    new_apk.icon.save(f'{new_apk.apk_name}.png', File(f), save=True)
                return
def get_certification(apk_path,new_apk):
    result = subprocess.run(['keytool', '--printcert', '--jarfile', apk_path], capture_output=True, text=True)
    info = result.stdout
    cert_info = {}  
      
    # 分割证书信息以获取不同的块（如所有者、发行者等）  
    # 注意：这里我们假设每个块的开始都有一个明确的标识符（如"Owner:", "Issuer:"等）  
    # 并且每个块的结束都是下一个块的开始或字符串的末尾  
    parts = info.split('\n')  
      
    # 遍历每个部分  
    current_key = None  
    for part in parts:  
        part = part.strip()  # 去除前后空格  
        if ':' in part:  
            key, value = part.split(':', 1)  # 假设每个键后面紧跟一个冒号和值  
            key = key.strip()   
            if key in ['Serial number', 'Valid from', 'until', 'Signature algorithm name', 'SHA1','SHA256','Subject Public Key Algorithm', 'Version']:
                if key == 'Valid from':
                    parts = value.split('until:')
                    before_until = parts[0].strip()
                    after_until = parts[1].strip()
                    cert_info['Valid from'] = before_until
                    cert_info['until'] = after_until
                else:
                    
                # 对于其他简单的键值对，我们直接存储它们  
                    cert_info[key.strip()] = value.strip()
        for key in ['Serial number', 'Valid from', 'until', 'Signature algorithm name', 'SHA1','SHA256','Subject Public Key Algorithm', 'Version']:
            if key not in cert_info:
                cert_info[key] = ''
    try:
        Cirtification.objects.get(apk=new_apk)
    except Exception:
        cir = Cirtification.objects.create(serial_number=cert_info['Serial number'],start_time=cert_info['Valid from'], end_time=cert_info['until'],signature_algorithm=cert_info['Signature algorithm name'],sha1_code=cert_info['SHA1'],sha256_code=cert_info['SHA256'],version=cert_info['Version'],public_key_algorithm=cert_info['Subject Public Key Algorithm'],apk=new_apk)
        cir.save()
        
        
        
def do_code_analyze(file_name):
    run_opcode_seq_creation(file_name)
    shutil.copy(f"opseq/{file_name}.opseq", f"{file_name}.opseq")
    os.system(f"th testWithPreTrainedNetwork.lua -dataPath {file_name}.opseq")
    with open(f"temp/{file_name}.opseq.result.txt", 'r', encoding='utf-8') as file:  
        content = file.read()
        print(content)
        lines = re.split(r'\r?\n', content)
    confidence = ''
    result = '正常'
    try:
        if 'Malware' in lines[0]:
            result = '涉诈'
        else:
            result = '正常'
        confidence = lines[1]
    except Exception:
        pass
    os.remove(f"{file_name}.opseq")
    return result, confidence


def analyze_apk(apk_path):
    apk_name = os.path.basename(apk_path)
    file_name, extension = os.path.splitext(apk_name)
    new_apk = static_analyze_apk(apk_path)
    get_certification(apk_path,new_apk)
    new_apk.state = 'apk解包'
    new_apk.save()
    decode_apk(apk_path)
    try:
        find_icon(f'decoded_apks/{file_name}',new_apk)
    except Exception:
        pass
    new_apk.state = '源码分析'
    new_apk.save()
    result1, confidence = do_code_analyze(file_name)  # 获取第一个任务的结果
    '''result1 = '正常'
    confidence = str(random.uniform(0.95, 1))'''
    new_apk.code_result = result1
    new_apk.confidence_level = confidence
    new_apk.state = '图像分析'
    new_apk.is_black = new_apk.is_black or result1 != '正常'
    new_apk.save()
    result2, num, degree = analyze_picture(apk_name)
    all_len = 0
    max_len = 0
    max_item = '正常'
    sizes = []
    labels = []
    num1 = num
    if not BlackPicture.objects.filter(apk=new_apk).exists():
        for item in result2:
            len1 = len(result2[item])
            if len1 > max_len:
                max_len = len1
                max_item = item
            for picture_path in result2[item]:
                new_picture = BlackPicture.objects.create(
                    category=item, file_path=picture_path, apk=new_apk)
                with open(picture_path, 'rb') as f:
                    new_picture.picture.save(picture_path.replace("\\", "_").replace("/", "_"), File(f), save=True)
    new_apk.is_black = new_apk.is_black or max_item != '正常'
    if new_apk.is_black and max_item == '正常':
        new_apk.category = '黑色产业'
    else:
        new_apk.category = max_item
    new_apk.state = '报告生成'
    new_apk.save()
    
    generate_report(new_apk)
    new_apk.state = '完成'
    new_apk.save()
    try:  
        shutil.rmtree(f'decoded_apks/{file_name}')
    except Exception: 
        pass
    with open(apk_path, 'rb') as f:
        new_apk.apk_file.save(f'{apk_name}.apk', File(f), save=True)
    os.remove(apk_path)
    
def generate_report(new_apk):
    with open(f'{new_apk.apk_name}.md', 'w') as f:
        f.write(f"# 涉诈APK分析报告-{new_apk.apk_name}\n\n")
        f.write("---\n\n")
        f.write("## 目录\n\n")
        f.write("1. [APK信息](#APK信息)\n")
        f.write("2. [证书信息](#证书信息)\n")
        f.write("3. [网址检测](#网址检测)\n")
        f.write("4. [权限信息](#权限信息)\n")
        f.write("5. [涉诈图片](#涉诈图片)\n")
        f.write("6. [结论](#结论)\n")
        f.write("---\n\n")

    # 写入 APK 信息
        f.write("## APK信息\n\n")
        f.write("| 属性     | 值                            |\n")
        f.write("|----------|--------------------------------|\n")
        f.write(f"| 图标   | <img src=\"myapp/media/{new_apk.icon}\"  width=\"150\"/> |\n")
        f.write(f"| 文件名   | `{new_apk.apk_name}.apk`            |\n")
        f.write(f"| 文件大小 | `{new_apk.apk_size}` |\n")
        f.write(f"| 应用名称 | `{new_apk.app_name}`            |\n")
        f.write(f"| 包名     | `{new_apk.package}`             |\n")
        f.write(f"| 版本号   | `{new_apk.androidversion_name}` |\n")
        f.write(f"| MD5码    | `{new_apk.md5_code}`            |\n")
        f.write(f"| 签名可验证 | `{new_apk.is_signed}`           |\n")
        if new_apk.code_result == '涉诈':
            f.write(f"| 代码分析结果 | <span style=\"color:red;\">{new_apk.code_result}</span>|\n")
        else:
            f.write(f"| 代码分析结果 | <span style=\"color:green;\">{new_apk.code_result}</span>|\n")
        f.write(f"| 置信度 | `{new_apk.confidence_level}` |\n")
        if new_apk.is_black:
            f.write(f"| **是否涉诈** | <span style=\"color:red;\">{new_apk.is_black}</span>|\n")
        else:
            f.write(f"| **是否涉诈** | <span style=\"color:green;\">{new_apk.is_black}</span>|\n")
        f.write(f"| **涉诈类型** | **{new_apk.category}**             |\n")
        f.write(f"| 分析完成时间 | `{new_apk.time}`                |\n")
        f.write("---\n\n")
        try:
            cirtification = Cirtification.objects.get(apk=new_apk)
            f.write("## 证书信息\n\n")
            f.write("| 属性     | 值                            |\n")
            f.write("|----------|--------------------------------|\n")
            f.write(f"| 序列号   | `{cirtification.serial_number}` |\n")
            f.write(f"| 版本   | `{cirtification.version}`            |\n")
            f.write(f"| 起始时间 | `{cirtification.start_time}` |\n")
            f.write(f"| 终止时间 | `{cirtification.end_time}`   |\n")
            f.write(f"| SHA1 | `{cirtification.sha1_code}`   |\n")
            f.write(f"| SHA256 | `{cirtification.sha256_code}`   |\n")
            f.write(f"| 签名算法 | `{cirtification.signature_algorithm}`   |\n")
            f.write(f"| 公钥算法 | `{cirtification.public_key_algorithm}`   |\n")
            f.write("---\n\n")
        except Exception:
            pass
        # 写入网址检测
        f.write("## 网址检测\n\n")
        f.write("| URL   | IP地址  | 域名 | 国家 | 城市 | 区域 | 是否涉诈 |\n")
        f.write("|-------|---------|------|------|------|------|----------|\n")
        url_list = list(Website.objects.filter(apk=new_apk).order_by('-is_black').values('url', 'ip', 'domain_name', 'country', 'city', 'region', 'is_black'))
        for item in url_list:
            if item['is_black']:
                f.write(f"| {item['url']}   | {item['ip']}  | {item['domain_name']} | {item['country']} | {item['city']} | {item['region']} | <span style=\"color:red;\">{item['is_black']}</span> |\n")
            else:
                f.write(f"| {item['url']}   | {item['ip']}  | {item['domain_name']} | {item['country']} | {item['city']} | {item['region']} | <span style=\"color:green;\">{item['is_black']}</span> |\n")
        f.write("\n---\n\n")

    # 写入权限检测
        f.write("## 权限信息\n\n")
        f.write("| 权限   | 中文名 | 说明  | 危险等级 |\n")
        f.write("|-------|-------|-----|-----|\n")
        permission_list = list(Permission.objects.filter(apk=new_apk).order_by('-level').values('name', 'chinese_name','discription', 'level'))
        for item in permission_list:
            if item['level'] == 0:
                f.write(f"| {item['name']}   | {item['chinese_name']} | {item['discription']}  | <span style=\"color:green;\">正常</span> |\n")
            elif item['level'] == 1:
                f.write(f"| {item['name']}   | {item['chinese_name']} | {item['discription']}  | <span style=\"color:orange;\">中危</span> |\n")
            else:
                f.write(f"| {item['name']}   | {item['chinese_name']} | {item['discription']}  | <span style=\"color:red;\">高危</span> |\n")
        f.write("\n---\n\n")

    # 写入图片检测
        f.write("## 涉诈图片\n\n")
        f.write("| 文件路径   | 涉诈类别  | 涉诈图片 |\n")
        f.write("|------------|----------|----------|\n")
        picture_list = list(BlackPicture.objects.filter(apk=new_apk).order_by('category').values('file_path', 'category', 'picture'))
        for item in picture_list:
            f.write(f"| {item['file_path']}   | {item['category']}  | ![alt text](myapp/media/{item['picture']}) |\n")
        f.write("\n---\n\n")

    # 写入结论
        f.write("## 结论\n\n")
    f.close()
    with open(f'{new_apk.apk_name}.md', 'a+') as file:
    # 移动文件指针到开头
        file.seek(0)
    # 读取现有内容
        content = file.read()
        conclusion = gpt_35_api([{'role': 'user','content':'以下是一篇markdown格式的apk分析报告，请为这个报告写一个结论，仅写出结论内容即可，不要包含标题和客套话。\n' + content}])
        file.write(conclusion)
        new_apk.conclusion = conclusion
        new_apk.save()
    command = ['mdout', f'{new_apk.apk_name}.md', '-f', 'tabloid']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()
    stdout, stderr = process.communicate()  
  
# 检查命令是否成功执行  
    if process.returncode == 0:  
        print("命令执行成功，标准输出:")  
        print(stdout.decode('utf-8'))  # 将字节串解码为字符串  
    else:  
        print("命令执行失败，错误信息:")  
        print(stderr.decode('utf-8'))  # 将字节串解码为字符串
    result = os.system(f'mdout {new_apk.apk_name}.md -f tabloid')
    with open(f'{new_apk.apk_name}.pdf', 'rb') as f:
        new_apk.report.save(f'{new_apk.apk_name}.pdf', File(f), save=True)
    os.remove(f'{new_apk.apk_name}.pdf')
    os.remove(f'{new_apk.apk_name}.md')