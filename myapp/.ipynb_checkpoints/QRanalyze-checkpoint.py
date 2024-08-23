import cv2
from pyzbar.pyzbar import decode
import zxing
import os

def read_with_pyzbar(img):
    decoded_objects = decode(img)
    if not decoded_objects:
        return None

    results = []
    for obj in decoded_objects:
        results.append((obj.type, obj.data.decode('utf-8')))
    return results

def read_with_zxing(file):
    reader = zxing.BarCodeReader()
    barcode = reader.decode(file)
    if barcode is not None:
        return [(barcode.format, barcode.parsed)]
    return None


def read_barcode(file_path):
    if not os.path.isfile(file_path):
        print(f"文件不存在或不是一个有效的文件: {file_path}")
        return None

    img = cv2.imread(file_path)
    if img is None:
        print(f"无法读取图像文件: {file_path}")
        return None

    results = read_with_pyzbar(img)

    if results:
        for result in results:
            print(f"Type: {result[0]}, Data: {result[1]}")
        return result[1]

    results = read_with_zxing(file_path)
    if results:
        for result in results:
            print(f"Type: {result[0]}, Data: {result[1]}")
        return result[1]

    print(f"未能检测到二维码或条码")
