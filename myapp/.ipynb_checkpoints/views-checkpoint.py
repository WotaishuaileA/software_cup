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
from .do_analyze import do_analyze
from .analyze2 import crawl
from .run_opcode_seq_creation import run_opcode_seq_creation
from .models import Apk, BlackPicture, Website, Permission, Cirtification
import sys
import re
import shutil
from openai import OpenAI
import pypandoc
import subprocess
import xml.dom.minidom
from xml.dom.minidom import parse
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import threading
from .analyze2 import crawl
from .QRanalyze import read_barcode
from django.db.models import Q
from django.core.files.storage import FileSystemStorage  
import json
from openai import OpenAI

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="sk-NIu5GsfVbHxF3XH9dAQ9ZfxFnXpXw0XK2Pr4TPeJIyJI8BLo",
    base_url="https://api.chatanywhere.tech/v1"
)

@csrf_exempt
def task_doing(request):
    value_list = list(Apk.objects.filter(~Q(state='完成')).values('apk_name', 'time', 'state'))
    for item in value_list:
        item['date'] = item['time']
        item['apk_name'] = item['apk_name'] + '.apk'
        if item['state'] == '特征分析':
            item['upload_percentage'] = 20
            item['analyze_percentage'] = 0
        elif item['state'] == '签名分析':
            item['upload_percentage'] = 40
            item['analyze_percentage'] = 0
        elif item['state'] == 'URL分析':
            item['upload_percentage'] = 60
            item['analyze_percentage'] = 0
        elif item['state'] == '权限分析':
            item['upload_percentage'] = 80
            item['analyze_percentage'] = 0
        elif item['state'] == 'apk解包':
            item['upload_percentage'] = 100
            item['analyze_percentage'] = 0
        elif item['state'] == '源码分析':
            item['upload_percentage'] = 100
            item['analyze_percentage'] = 33
        elif item['state'] == '图像分析':
            item['upload_percentage'] = 100
            item['analyze_percentage'] = 67
        elif item['state'] == '报告生成':
            item['upload_percentage'] = 100
            item['analyze_percentage'] = 100
        else:
            item['upload_percentage'] = 100
            item['analyze_percentage'] = 100
    return JsonResponse(value_list, safe=False)


def picture_to_apk(file_path):
    crawl(read_barcode(file_path))


def link_to_apk(link):
    crawl(link)


@csrf_exempt
def task_apk(request):
    if request.FILES['file']:
        file_type = request.POST.get('fileType', '')
        files = request.FILES.getlist('file')
        for file in files:
            fs = FileSystemStorage(location='/apks_to_be_analyze')
            fs.save(file.name, file)
            file_path = os.path.join('/apks_to_be_analyze', file.name)
            if file_type == 'apk':
                #do_analyze([file_path])
                t = threading.Thread(target=do_analyze, args=([file_path],))
                t.start()
            elif file_type == 'pic':
                #picture_to_apk(file_path)
                t = threading.Thread(target=picture_to_apk, args=(file_path,))
                t.start()
        # 如果不是POST请求，则返回适当的响应（这里为了简单起见，直接返回空JSON）
    return JsonResponse({})


@csrf_exempt
def task_link(request):
    data = json.loads(request.body)
    link = data.get('link', None)
    if link:
        link_to_apk(link)
        t = threading.Thread(target=link_to_apk, args=(link,))
        t.start()
        # 如果不是POST请求，则返回适当的响应（这里为了简单起见，直接返回空JSON）
    return JsonResponse({})


@csrf_exempt
def task_done(request):
    value_list = list(Apk.objects.filter(state='完成').values('id', 'icon', 'apk_name', 'androidversion_name', 'time', 'md5_code', 'category','conclusion','package'))
    for item in value_list:
        item['date'] = item['time']
        item['iconUrl'] = f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{item['icon']}"
        item['type'] = item['category']
        item['version'] = item['androidversion_name']
        item['package_name'] = item['package']
        item['md'] = item['md5_code']
        item['result'] = item['conclusion']
    return JsonResponse(value_list, safe=False)

@csrf_exempt
def static_report(request):
    apk_id = request.GET.get('id', 0)
    print(apk_id)
    apk = Apk.objects.get(id=apk_id)
    file_path = apk.report.path
    print(file_path)
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/octet-stream")
        response['Content-Disposition'] = 'attachment; filename="%s"' % apk.report.name
    return response

@csrf_exempt
def static_apk(request):
    apk_id = request.GET.get('id', 0)
    print(apk_id)
    apk = Apk.objects.get(id=apk_id)
    file_path = apk.apk_file.path
    print(file_path)
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.android.package-archive")
        response['Content-Disposition'] = 'attachment; filename="%s"' % apk.apk_file.name
    return response

@csrf_exempt
def static_basicinfo(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    certification = Cirtification.objects.get(apk=apk)
    data = {
        "id": apk.id,
        "iconUrl": f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{apk.icon}",
        "app_name": apk.app_name,
        "apk_name": apk.apk_name,
        "size": apk.apk_size,
        "version": apk.androidversion_name,
        "pack": apk.package,
        "md": apk.md5_code,
        "date": apk.time,
        "serial": certification.serial_number,
        "serial": certification.serial_number,
        "certificate": certification.version,
        "SHA1": certification.sha1_code,
        "SHA256": certification.sha256_code,
        "agl_sign": certification.signature_algorithm,
        "agl_key": certification.public_key_algorithm,
        "exp_begin_date": certification.start_time,
        "exp_end_date": certification.end_time,
        "type": apk.category,
        "result": apk.conclusion,
        "report_url":f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{apk.report}"
    }
    return JsonResponse(data, safe=False)

@csrf_exempt
def static_permissioninfo(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    value_list = list(Permission.objects.filter(apk=apk).values('name', 'chinese_name', 'discription', 'level'))
    for item in value_list:
        item['title'] = item['chinese_name']
    return JsonResponse(value_list, safe=False)

@csrf_exempt
def static_urlinfo(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    value_list = list(Website.objects.filter(apk=apk).values('url', 'ip', 'domain_name', 'city','region', 'country', 'is_black'))
    return JsonResponse(value_list, safe=False)

@csrf_exempt
def static_picinfo(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    value_list = list(BlackPicture.objects.filter(apk=apk).values('category', 'picture'))
    for item in value_list:
        item['url'] = f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{item['picture']}"
    return JsonResponse(value_list, safe=False)

@csrf_exempt
def static_pics(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    filter1 = BlackPicture.objects.filter(apk=apk)
    black = filter1.filter(category='黑色产业').count()
    scam = filter1.filter(category='诈骗').count()
    sex = filter1.filter(category='色情').count()
    gamble = filter1.filter(category='赌博').count()
    return JsonResponse([sex,scam,gamble,black], safe=False)

@csrf_exempt
def static_urls(request):
    apk_id = request.GET.get('id', None)
    apk = Apk.objects.get(id=apk_id)
    filter1 = Website.objects.filter(apk=apk)
    black = filter1.filter(is_black=True).count()
    white = filter1.filter(is_black=False).count()
    return JsonResponse([black,white], safe=False)

@csrf_exempt
def list_black(request):
    value_list = list(
        Apk.objects.filter(state='完成',is_black=True).values('id'))
    data_list = []
    for item in value_list:
        apk_id = item['id']
        apk = Apk.objects.get(id=apk_id)
        certification = Cirtification.objects.get(apk=apk)
        data = {
            "id": apk.id,
            "iconUrl": f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{apk.icon}",
            "app_name": apk.app_name,
            "apk_name": apk.apk_name,
            "size": apk.apk_size,
            "version": apk.androidversion_name,
            "pack": apk.package,
            "md": apk.md5_code,
            "date": apk.time,
            "serial": certification.serial_number,
            "certificate": certification.version,
            "SHA1": certification.sha1_code,
            "SHA256": certification.sha256_code,
            "agl_sign": certification.signature_algorithm,
            "agl_key": certification.public_key_algorithm,
            "exp_begin_date": certification.start_time,
            "exp_end_date": certification.end_time,
            "type": apk.category,
            "result": apk.conclusion
        }
        data_list.append(data)
    return JsonResponse(data_list, safe=False)

@csrf_exempt
def list_white(request):
    value_list = list(
        Apk.objects.filter(state='完成',is_black=False).values('id'))
    data_list = []
    for item in value_list:
        apk_id = item['id']
        apk = Apk.objects.get(id=apk_id)
        certification = Cirtification.objects.get(apk=apk)
        data = {
            "id": apk.id,
            "iconUrl": f"https://u144966-8ab3-48d0320a.westb.seetacloud.com:8443/media/{apk.icon}",
            "app_name": apk.app_name,
            "apk_name": apk.apk_name,
            "size": apk.apk_size,
            "version": apk.androidversion_name,
            "pack": apk.package,
            "md": apk.md5_code,
            "date": apk.time,
            "serial": certification.serial_number,
            "certificate": certification.version,
            "SHA1": certification.sha1_code,
            "SHA256": certification.sha256_code,
            "agl_sign": certification.signature_algorithm,
            "agl_key": certification.public_key_algorithm,
            "exp_begin_date": certification.start_time,
            "exp_end_date": certification.end_time,
            "type": apk.category,
            "result": apk.conclusion
        }
        data_list.append(data)
    return JsonResponse(data_list, safe=False)

@csrf_exempt
def task_del(request):
    id_list = json.loads(request.body)
    for apk_id in id_list:
        apk = Apk.objects.get(id=apk_id)
        apk.delete()
    return JsonResponse({})

@csrf_exempt
def chat_chat(request):
    data = json.loads(request.body)
    messages = data.get('messages', None)
    apk_id = data.get('id', None)
    if not apk_id:
        messages.insert(0,{'role': 'assistant','content':'你现在是千问人工智能助手，你将作为apk反诈平台小助手，回答用户关于apk静态分析，动态分析的相关问题。'})
        completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return JsonResponse({'content':completion.choices[0].message.content})
    new_apk = Apk.objects.get(id=apk_id)
    with open(f'{new_apk.apk_name}.txt', 'w') as f:
        f.write(f"# 涉诈APK分析报告-{new_apk.apk_name}\n\n")
        f.write("---\n\n")
        f.write("## 目录\n\n")
        f.write("1. [APK信息](#APK信息)\n")
        f.write("2. [证书信息](#证书信息)\n")
        f.write("3. [网址检测](#网址检测)\n")
        f.write("4. [权限信息](#权限信息)\n")
        f.write("5. [涉诈图片](#涉诈图片)\n")
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
    with open(f'{new_apk.apk_name}.txt', 'a+') as file:
        file.seek(0)
        content = file.read()
    messages.insert(0,{'role': 'assistant','content':f'这是一篇关于{new_apk.apk_name}的静态分析报告，请根据报告内容回答相关问题。' + content})
    messages.insert(0,{'role': 'assistant','content':'你现在是千问人工智能助手，你将作为apk反诈平台小助手，回答用户关于apk静态分析，动态分析的相关问题。'})
    completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
    return JsonResponse({'content':completion.choices[0].message.content})


