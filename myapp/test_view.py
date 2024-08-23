from .do_analyze import do_analyze,generate_report

from django.http import HttpResponse
from .models import Apk,Cirtification
import os
from concurrent.futures import ProcessPoolExecutor 

def split_list(big_list, n):  
    # 使用列表推导式和range函数生成分割后的列表  
    return [big_list[i:i + n] for i in range(0, len(big_list), n)]

def generate():
    pathes = []
    '''for root, dirs, files in os.walk('apks_to_be_analyze'):  
        for file in files:  
            # 检查文件后缀名  
            if file.endswith('apk'):
                pathes.append(os.path.join(root, file))'''
    '''with ProcessPoolExecutor(max_workers=2) as executor:  # 最多5个线程  
        futures = [executor.submit(do_analyze, [path]) for path in pathes]  
        for future in futures:  
            future.result()  # 这会阻塞直到所有任务完成'''
    '''spilt = split_list(pathes, 20)
    for item in spilt:
        do_analyze(item)'''
    #Apk.objects.exclude(state='完成').delete()
    new_apk = Apk.objects.get(id=492)
    '''certification = Cirtification.objects.get(apk=apk)
    certification.serial_number = '6745e896'
    certification.version = '3'
    certification.sha1_code = '9574782a770f657cf4d71cdf667427070d74c5ed'
    certification.sha256_code = '31b6add6103d33e14dbb8ba54792af3cdd5a92ea3fcc24682e46459928e1dd76'
    certification.signature_algorithm = 'SHA256withRSA'
    certification.public_key_algorithm = '2048-bit RSA key'
    certification.start_time = 'Wed Aug 06 13:47:13 CST 2024'
    certification.end_time = 'Wed Jul 25 13:47:13 CST 2074'
    certification.save()'''
    generate_report(new_apk)
    #do_analyze(pathes)
def index(request):
    #generate_report(Apk.objects.get(apk_name='caomeiyinghe13'))
    #do_analyze(['caomeiyinghe13.apk'])
    generate()
    #Apk.objects.all().delete()
    return HttpResponse("这是主页")