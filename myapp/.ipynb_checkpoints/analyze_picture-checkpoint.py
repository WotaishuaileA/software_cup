import os
import torch
from PIL import Image
import numpy as np
import shutil

import cn_clip.clip as clip
from cn_clip.clip import load_from_name, available_models


def analyze_picture(apk_name):
    num = 0
    path_list = {"赌博": [], "色情": [], "诈骗": []}
    apk_name = os.path.splitext(apk_name)[0]
    print("Available models:", available_models())
    # Available models: ['ViT-B-16', 'ViT-L-14', 'ViT-L-14-336', 'ViT-H-14', 'RN50']
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = load_from_name("ViT-B-16", device=device, download_root='./clip')
    model.eval()
    token_list = ["赌博", "色情", "诈骗","小图标"]
    text = clip.tokenize(token_list).to(device)
    os.makedirs("picture_analyze", exist_ok=True)
    degree = 1.0
    '''for root, dirs, files in os.walk("picture_analyze"):
        for file in files:
            os.remove(os.path.join(root, file))'''
    print("开始分析")
    skip_dirs = set()
    for root, dirs, files in os.walk(os.path.join("decoded_apks", apk_name)):
        if root in skip_dirs:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            filename, extension = os.path.splitext(file_path)
            if root in skip_dirs:
                continue
            if extension == '.jpg' or extension == '.png':
                num = num + 1
            else:
                continue
            try:
                image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
            except Exception:
                continue
            with torch.no_grad():
                logits_per_image, logits_per_text = model.get_similarity(image, text)
                probs = logits_per_image.softmax(dim=-1).cpu().numpy()
                max1 = probs.max()
                if max1 > 0.9:
                    degree = degree/2.0 + max1/2.0
                    token_name = token_list[np.argmax(probs)]
                    '''if token_name == "小图标":
                        skip_dirs.add(root)
                        continue'''
                    if token_name != '正常' and token_name != "小图标":
                        to_path = os.path.join("picture_analyze", token_list[np.argmax(probs)])
                        if not os.path.exists(to_path):
                            os.makedirs(to_path)
                        shutil.copy2(file_path, to_path)
                        path_list[token_name].append(os.path.join(to_path, file))
                        print(f"存在 {token_name} 相关图片!")
                        print(f"{file_path}")
    print(num)
    return path_list, num, degree
