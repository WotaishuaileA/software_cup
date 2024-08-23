import os
import time
import urllib
import pickle
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from scipy.sparse import coo_matrix
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
import torch.nn.functional as F
from torch.cuda import is_available, device_count, current_device

# 定义样本文件位置
good_dir = 'data/good'
bad_dir = 'data/bad'

# kmeans聚合的维度
k = 80
# ngram系数
n = 2

# 是否使用kmeans
use_k = False

# 新定义输出方法，便于调试
def printT(word):
    a = time.strftime('%Y-%m-%d %H:%M:%S: ', time.localtime(time.time()))
    print(a + str(word))

# 读取数据
def getdata(filepath):
    with open(filepath, 'r') as f:
        data = [i.strip('\n') for i in f.readlines()]
    return data

# 遍历文件夹中文件以读取数据
def load_files(dir):
    data = []
    g = os.walk(dir)
    for path, dirs, files in g:
        for filename in files:
            fullpath = os.path.join(path, filename)
            printT("load file: " + fullpath)
            t = getdata(fullpath)
            data.extend(t)
    return data

# 数据预处理裁剪字符格式
def get_ngrams(query):
    tempQuery = str(query)
    ngrams = []
    for i in range(0, len(tempQuery)-n):
        ngrams.append(tempQuery[i:i+n])
    return ngrams

# 定义数据集类
class TextDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# 定义模型
class TextClassifier(nn.Module):
    def __init__(self, input_dim):
        super(TextClassifier, self).__init__()
        self.fc = nn.Linear(input_dim, 1)

    def forward(self, x):
        x = self.fc(x)
        return torch.sigmoid(x).squeeze()

# 训练模型
def train_model(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs.float())
        loss = criterion(outputs, labels.float())
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
    epoch_loss = running_loss / len(dataloader.dataset)
    return epoch_loss

# 验证模型
def validate_model(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    running_corrects = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            # 模型前向传播
            outputs = model(inputs)

            # 打印输出张量的形状以进行调试
            print("Outputs shape:", outputs.shape)

            # 计算损失
            loss = criterion(outputs, labels)

            # 获取预测标签
            _, preds = torch.max(outputs, 1)  # 确保维度正确

            # 统计损失和准确率
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = running_corrects.double() / len(dataloader.dataset)

# 主函数
def main():
    # 读取数据
    printT("Loading Good Data:")
    good_query_list = load_files(good_dir)

    printT("Loading Bad Data:")
    bad_query_list = load_files(bad_dir)

    # 整合数据
    data = [good_query_list, bad_query_list]
    printT("Done, Good Numbers:" + str(len(data[0])) + " Bad Numbers:" + str(len(data[1])))

    # 打标记
    good_y = [0 for _ in range(len(data[0]))]
    bad_y = [1 for _ in range(len(data[1]))]

    y = good_y + bad_y

    # 数据向量化预处理
    vectorizer = TfidfVectorizer(tokenizer=get_ngrams)
    print(len(y))
    X = vectorizer.fit_transform(data[0] + data[1])
    print(X.shape[0])
    # 通过kmeans降维
    if use_k:
        X = transform_kmeans(X, n_clusters=k)
    print(X.shape[0])
    printT("Devide Training Data")
    # 使用train_test_split分割X，y列表（testsize表示测试占的比例）（random为种子）
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 将数据转换为 PyTorch Tensor
    X_train_tensor = torch.tensor(X_train.todense(), dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test.todense(), dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.int64)
    y_test_tensor = torch.tensor(y_test, dtype=torch.int64)
    print('tensor')
    # 创建数据加载器
    train_dataset = TextDataset(X_train_tensor, y_train_tensor)
    test_dataset = TextDataset(X_test_tensor, y_test_tensor)
    print('dataset')
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 检查 CUDA 是否可用
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 创建模型
    model = TextClassifier(X_train_tensor.shape[1]).to(device)

    # 定义损失函数和优化器
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 训练模型
    num_epochs = 10
    for epoch in range(num_epochs):
        train_loss = train_model(model, train_loader, criterion, optimizer, device)
        #val_loss, val_acc = validate_model(model, test_loader, criterion, device)
        #printT(f'Epoch {epoch+1}/{num_epochs}')
        #printT(f'Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}')

    # 保存模型
    torch.save(model.state_dict(), 'model/pytorch_model.pth')
    with open('model/tfidf_vectorizer.pkl', 'wb') as file:
        pickle.dump(vectorizer, file)
    # 测试模型
    # 使用测试值对模型的准确度进行计算
    test_loss, test_acc = validate_model(model, test_loader, criterion, device)
    printT('Test Loss: {:.4f} | Test Acc: {:.4f}'.format(test_loss, test_acc))

# 转换成聚类后结果输入转置后的矩阵返回转置好的矩阵
def transform_kmeans(weight, n_clusters=100):
    # 将稀疏矩阵转换为 lil_matrix 以提高效率
    weight = weight.tolil().transpose()

    # 尝试从文件中加载聚类标签
    try:
        with open('model/k' + str(n_clusters) + '.label', 'r') as input:
            printT('Loading K-means labels...')
            a = input.read().split(' ')
            label = [int(i) for i in a[:-1]]

            # 使用聚类标签构建新的特征矩阵
            transformed_weight = np.zeros((weight.shape[0], n_clusters))
            for i, cluster_label in enumerate(label):
                transformed_weight[i, cluster_label] = 1

            # 转换回稀疏矩阵
            transformed_weight = csr_matrix(transformed_weight)

            return transformed_weight

    except FileNotFoundError:
        printT('Starting K-means...')

        # 实现 K-means 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(weight)

        # 保存聚类的结果
        label = kmeans.labels_
        with open('model/k' + str(n_clusters) + '.label', 'w') as output:
            for i in label:
                output.write(str(i) + ' ')

        # 使用聚类标签构建新的特征矩阵
        transformed_weight = np.zeros((weight.shape[0], n_clusters))
        for i, cluster_label in enumerate(label):
            transformed_weight[i, cluster_label] = 1

        # 转换回稀疏矩阵
        transformed_weight = csr_matrix(transformed_weight)

        printT('K-means completed, total: ' + str(n_clusters) + ' clusters')
        return transformed_weight

# 对新的请求列表进行预测
def predict(new_queries):
    # 解码
    new_queries = [urllib.parse.unquote(url) for url in new_queries]
    with open('model/tfidf_vectorizer.pkl', 'rb') as file:
        vectorizer = pickle.load(file)
    X_predict = vectorizer.transform(new_queries)

    X_predict_tensor = torch.tensor(X_predict.todense(), dtype=torch.float32)
    device = "cpu"
    # 加载模型
    model = TextClassifier(X_predict_tensor.shape[1]).to(device)
    model.load_state_dict(torch.load('model/pytorch_model.pth'))
    model.eval()

    with torch.no_grad():
        outputs = model(X_predict_tensor.float())
        predictions = (outputs > 0.5).float()
    if predictions.dim() == 0:
        predictions = predictions.unsqueeze(0)
    # 处理预测结果
    result = {}
    result[0] = []  # 好的查询
    result[1] = []  # 不好的查询
    print(new_queries)
    print(predictions)
    for query, prediction in zip(new_queries, predictions):
        if prediction.item() == 0:
            result[0].append(query)
        else:
            result[1].append(query)

    printT('Predict Succeed, Total：' + str(len(predictions)))
    printT('good query: ' + str(len(result[0])))
    printT('bad query: ' + str(len(result[1])))

    return result