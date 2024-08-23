
import base64
import json
import os
import time
import re
import xml.dom.minidom
from xml.dom.minidom import parse
import subprocess  
import shutil

def find_icon(base_path):
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
    print(base_path)
    print(path_name)
    print(icon_name)
    ls = os.listdir(os.path.join(base_path,'res'))
    print(ls)
    for p in ls:
        if p.startswith(path_name):
            path = os.path.join(base_path, p, icon_name+".png")
            print(path)
            
def do_code_analyze(file_name):
    os.system(f"th testWithPreTrainedNetwork.lua -dataPath {file_name}.opseq")
    with open(f"temp/{file_name}.opseq.result.txt", 'r', encoding='utf-8') as file:  
        content = file.read()
        print(content)
        lines = re.split(r'\r?\n', content)
        print(lines)
    confidence = '1'
    result = '正常'
    try:
        if 'Malware' in lines[0]:
            result = '涉诈'
        else:
            result = '正常'
        confidence = lines[1]
    except Exception:
        pass
    print(result, confidence)
    return result, confidence
    
do_code_analyze('189邮箱')