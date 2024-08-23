from androguard.session import Session
from androguard.misc import AnalyzeAPK
from urllib.parse import urlparse
from django.core.files.base import File
import hashlib
import re
import os
import subprocess
import sys
from .models import Apk,Website,Permission, Cirtification
import model as model
from tldextract import extract
import requests
import socket
import json

def get_domain(url):
    # 解析URL
    parsed_url = urlparse(url)
    # 使用tldextract获取更准确的域名
    domain_info = extract(parsed_url.netloc)
    return f"{domain_info.domain}.{domain_info.suffix}"

def get_ip_address(url):
    # 解析URL
    parsed_url = urlparse(url)
    # 假设我们需要获取的是服务器的IP地址，这里使用简单的DNS查询
    try:
        ip_address = socket.gethostbyname(parsed_url.hostname)
    except socket.gaierror:
        ip_address = None
    return ip_address

def get_ip_location(ip_address):
    if not ip_address:
        return None
    # 使用IP-API.com API获取位置信息
    response = requests.get(f"http://ip-api.com/json/{ip_address}")
    data = response.json()
    if data['status'] == 'success':
        return {
            'city': data['city'],
            'region': data['regionName'],
            'country': data['country']
        }
    return None
url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/(?:[\w/._-]*?\??(?:[\w/._-]*=\w+(?:&[\w/._-]*=\w+)*)?)?)?'
black_urls = set()


def analyze_permissions(a, new_apk):
    if Permission.objects.filter(apk=new_apk).exists():
        return
    permissions = a.get_permissions()
    with open('permissions.json', 'r') as file:  
        all_permissions = json.load(file)["PermissList"]
    if permissions:
        for perm in permissions:
            item = next((p for p in all_permissions if p["Key"] == perm), None)
            if item:
                chinese_name = item["Title"]
                discription = item["Memo"]
                level = item["Level"]
                new_permission = Permission.objects.create(name=perm, discription=discription, chinese_name=chinese_name,level=level, apk=new_apk)
                new_permission.save()

def url_analyze(urls):
    #sys.path.append('myapp')
    try:
        result = model.predict(urls)
    except Exception:
        result = [[],[]]
    #sys.path.remove('myapp')
    return result[1]


def analyze_urls(dx, black_urls):
    white_urls = set()
    urls = set()
    urls_to_test = []
    for cls in dx.get_classes():
        for method in cls.get_methods():
            if method.is_external():
                continue
            method = method.get_method()
            for i in method.get_instructions():
                if i.get_name() == "const-string":
                    # 假设字符串可能是URL（这里需要更复杂的逻辑来准确识别URL）
                    s = i.get_string()
                    urls1 = re.findall(url_pattern, s)
                    urls_to_test.extend(urls1)
                    for url in urls1:
                        parsed_url = urlparse(url)
                        input_domain = parsed_url.netloc
                        for item in black_urls:
                            try:
                                parsed_item = urlparse(item)
                                item_domain = parsed_item.netloc
                                if item_domain == input_domain:
                                    urls.add(url)
                                    break
                            except Exception:
                                pass
    urls.update(url_analyze(urls_to_test))
    for item in urls_to_test:  
    # 如果当前元素不在集合中，则添加到新列表中  
        if item not in urls:  
            white_urls.add(item)
    return urls, white_urls



def calculate_md5(file_path):
    """  
    计算并返回给定文件的MD5哈希值。  
      
    :param file_path: 要计算MD5的文件路径  
    :return: 文件的MD5哈希值（十六进制字符串）  
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def analyze_exported_components(a, file):
    # 获取AndroidManifest.xml中的组件  
    manifest_xml = a.get_android_manifest_xml()

    exposed_components = []

    # 假设有一个函数parse_manifest用于解析manifest并返回暴露的组件列表  
    # exposed_components = parse_manifest(manifest)  
    if isinstance(manifest_xml, str):
        root = ET.fromstring(manifest_xml)
    else:
        root = manifest_xml

        # 遍历所有 activity, service, receiver, provider
    for tag in ['activity', 'service', 'receiver', 'provider']:
        for elem in root.findall(f'./{tag}'):
            exported = elem.get('android:exported', 'false').lower()
            has_intent_filter = len(elem.findall('./intent-filter')) > 0

            # 如果 exported 为 true，或者未设置但包含 intent-filter，则认为组件是暴露的  
            if exported == 'true' or (exported == 'false' and has_intent_filter):
                # 添加组件的全限定名到列表中  
                component_name = elem.get('android:name')
                if component_name:
                    exposed_components.append(component_name)

                    # 输出结果
    if exposed_components:
        print("## 被暴露的组件:\n")
        for component in exposed_components:
            print(component)

            # 在这里，你可以进一步评估每个暴露组件的风险，并生成报告


def analyze_signature(apk_path, new_apk):
    # apksigner的路径，这里假设它已经在环境变量中，否则你需要提供完整路径  
    apksigner_path = 'apksigner.jar'

    # 构建命令  
    command = ['java', '-jar', apksigner_path, 'verify', '--verbose', apk_path]
    # 运行命令并捕获输出  
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        new_apk.is_signed = True
    except subprocess.CalledProcessError as e:
        # 如果命令执行失败（即返回非零退出码），则捕获错误信息  
        new_apk.is_signed = False
        
def analyze_certification(a, new_apk):
    cert_info = a.get_all_certificates_x509()
    
    # 输出证书信息
    if cert_info:
        for cert in cert_info:
            new_cirtification = Cirtification.objects.create(
                serial_number=cert.get_serial_number(), sha1_code=cert.get_fingerprint('sha1'), sha256_code=cert.get_fingerprint('sha256'),
                information=cert.get_subject().to_issuer(),apk=new_apk)
            new_cirtification.save()


'''def analyze_api_calls(apk_path):  
    session = Session()  
    a, d, dx = AnalyzeAPK(apk_path, session=session)  
  
    # 假设 APK 只有一个 DEX 文件  
    for method in dx.get_methods():
        if method.is_external():
            continue
        m = method.get_method()
        print(m.source())'''
def get_apk_size(apk_path):  
    """  
    获取APK文件的大小（以字节为单位）  
      
    :param apk_path: APK文件的路径  
    :return: APK文件的大小（字节）  
    """  
    apk_size = os.path.getsize(apk_path)
    if apk_size < 1024:
        return f"{apk_size}B"
    elif apk_size >= 1024 * 1024:
        return f"{(apk_size / 1024 / 1024):.2f}MB"
    else:
        return f"{(apk_size / 1024):.2f}KB"
    
def add_website(black_urls, white_urls,new_apk):
    if Website.objects.filter(apk=new_apk).exists():
        return
    for url in black_urls:
        try:
            ip_address = get_ip_address(url)
            location = get_ip_location(ip_address)
            if location:
                new_website = Website.objects.create(
                    url=url, ip=ip_address, domain_name=get_domain(url),
                    city=location['city'],region=location['region'],country=location['country'], is_black=True, apk=new_apk)
            else:
                new_website = Website.objects.create(
                    url=url, ip=ip_address, domain_name=get_domain(url),
                    is_black=True, apk=new_apk)
            new_website.save()
        except Exception:
            pass
    for url in white_urls:
        try:
            ip_address = get_ip_address(url)
            location = get_ip_location(ip_address)
            if location:
                new_website = Website.objects.create(
                    url=url, ip=ip_address, domain_name=get_domain(url),
                    city=location['city'],region=location['region'],country=location['country'], is_black=False, apk=new_apk)
            else:
                new_website = Website.objects.create(
                    url=url, ip=ip_address, domain_name=get_domain(url),
                    is_black=False, apk=new_apk)
                new_website.save()
        except Exception:
            pass
def static_analyze_apk(apk_path):
    apk_name = os.path.basename(apk_path)
    with open('black_urls.txt', 'r', encoding='utf-8') as file1:
        black_urls = {line.strip() for line in file1}  # 使用集合推导式
    file1.close()
    md5_code = calculate_md5(apk_path)
    apk_name = os.path.splitext(apk_name)[0]
    try:
        new_apk = Apk.objects.get(md5_code=md5_code)
        new_apk.state = '特征分析'
    except Exception:
        new_apk = Apk.objects.create(
            apk_name=apk_name,apk_size=get_apk_size(apk_path),md5_code=md5_code, state='特征分析')
    a, d, dx = AnalyzeAPK(apk_path)
    new_apk.app_name=a.get_app_name()
    new_apk.package=a.get_package()
    new_apk.androidversion_name=a.get_androidversion_name()
    new_apk.effective_target_sdk_version=a.get_effective_target_sdk_version()
    new_apk.state = '签名分析'
    new_apk.save()
    analyze_signature(apk_path, new_apk)
    new_apk.state = 'URL分析'
    new_apk.save()
    analyze_permissions(a, new_apk)
    black_urls, white_urls = analyze_urls(dx, black_urls)
    add_website(black_urls, white_urls,new_apk)
    new_apk.state = '权限分析'
    new_apk.save()
    #analyze_certification(a, new_apk)
    return new_apk
