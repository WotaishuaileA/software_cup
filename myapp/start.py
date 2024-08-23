# coding:utf-8

import model

# 测试文件位置
testfile = 'data/train/poc_test.txt'
#model.main()
# SVM模型预测
result = model.predict(['https://www.baidu.com/'])
print(result)
