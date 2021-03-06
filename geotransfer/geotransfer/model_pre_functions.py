import rasterio
from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from tqdm import tqdm
import torch
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
from torch.autograd import Variable
from torch.nn import Linear, ReLU, CrossEntropyLoss, Sequential, Conv2d, MaxPool2d, Module, Softmax, BatchNorm2d, Dropout,AdaptiveAvgPool2d
from torch.optim import Adam, SGD
import torch.nn.functional as F
from torchvision import models
from sklearn.metrics import accuracy_score
import torch.optim as optim

def get_dict(y,num_classes=10):
    d1={x: x-y.min() for x in y}
    key_left = set(range(0,num_classes)) - set(d1.keys())
    value_left = set(range(0,num_classes)) - set(d1.values())
    d2 = {list(key_left)[i]:list(value_left)[i] for i in range(len(key_left))}
    d2.update(d1)
    
    return d2

def prepare_data(x,y,d2):
    y = np.array([d2[k] for k in y])
    y = torch.from_numpy(y)
    
    x = x.astype(float)
    x = torch.from_numpy(np.array(x,dtype='f'))
    return x,y

def extract_features(x,y, batch_size):
    data_x = []
    label_x = []

    inputs,labels = x, y

    for i in tqdm(range(int(x.shape[0]/batch_size)+1)): 
        input_data = inputs[i*batch_size:(i+1)*batch_size]
        #print('The shape of input_data is ',input_data.shape)
        label_data = labels[i*batch_size:(i+1)*batch_size]
        input_data , label_data = Variable(input_data),Variable(label_data)
        features = model.features(input_data)
        #print('1. The shape of x is ',x.shape)
        features = model.avgpool(features)
        #print('2.The shape of x is ',x.shape)
        data_x.extend(features.data.cpu().numpy())
        label_x.extend(label_data.data.cpu().numpy())
    
    x_train  = torch.from_numpy(np.array(data_x))
    x_train = x_train.view(x_train.size(0), -1)
    y_train  = torch.from_numpy(np.array(label_x))
    
    del data_x,label_x,inputs,labels
    
    return x_train,y_train

def train_model(x_train,y_train, model, criterion, optimizer,
                model_type='CBR' ,
                n_epochs=2,
                batch_size=8):

    for epoch in tqdm(range(1, n_epochs+1)):

        # keep track of training and validation loss
        train_loss = 0.0
        
        permutation = torch.randperm(x_train.size()[0])

        training_loss = []
        for i in range(0,x_train.size()[0], batch_size):

            indices = permutation[i:i+batch_size]
            batch_x, batch_y = x_train[indices], y_train[indices]

            if torch.cuda.is_available():
                batch_x, batch_y = batch_x.cuda(), batch_y.cuda()
        
            optimizer.zero_grad()
            # in case you wanted a semi-full example
            if model_type=='CBR':
                outputs = model(batch_x)
            else:
                outputs = model.classifier(batch_x)
            loss = criterion(outputs,batch_y)

            training_loss.append(loss.item())
            loss.backward()
            optimizer.step()
        
        training_loss = np.average(training_loss)
        print('epoch: \t', epoch, '\t training loss: \t', training_loss)
    return model

def pred_acc(x_train,y_train,model,model_type = 'CBR',batch_size=8):
    # prediction for training set
    prediction = []
    target = []
    permutation = torch.randperm(x_train.size()[0])
    for i in tqdm(range(0,x_train.size()[0], batch_size)):
        indices = permutation[i:i+batch_size]
        batch_x, batch_y = x_train[indices], y_train[indices]
    
        if torch.cuda.is_available():
            batch_x, batch_y = batch_x.cuda(), batch_y.cuda()
    
        with torch.no_grad():
            if model_type=='CBR':
                output = model(batch_x)
            else:
                output = model.classifier(batch_x)

        softmax = torch.exp(output).cpu()
        prob = list(softmax.numpy())
        predictions = np.argmax(prob, axis=1)
        prediction.append(predictions)
        target.append(batch_y)
    
    # training accuracy
    accuracy = []
    for i in range(len(prediction)):
        accuracy.append(accuracy_score(target[i],prediction[i]))
        
    avg = np.average(accuracy)
    del prediction,target,permutation,accuracy
    return avg

class Net(Module):   
    def __init__(self):
        super(Net, self).__init__()

        self.cnn_layers = Sequential(
            # Defining a 2D convolution layer
            Conv2d(13, 64, kernel_size=(5,5), stride=1, padding=2),
            BatchNorm2d(64),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=(2,2),padding = 1),
            
            Conv2d(64, 128, kernel_size=(5,5), stride=1, padding=2),
            BatchNorm2d(128),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            Conv2d(128, 256, kernel_size=(5,5), stride=1, padding=2),
            BatchNorm2d(256),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            Conv2d(256, 512, kernel_size=(5,5), stride=1, padding=2),
            BatchNorm2d(512),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            AdaptiveAvgPool2d((1, 1))
        )
        self.linear_layers = Sequential(
            Linear(in_features= 512, out_features=10, bias = True)
        )
        


    # Defining the forward pass    
    def forward(self, x):
        x = self.cnn_layers(x)
        x = x.view(x.size(0), -1)
        x = self.linear_layers(x)
        return x

class smallNet(Module):   
    def __init__(self):
        super(smallNet, self).__init__()

        self.cnn_layers = Sequential(
            Conv2d(13, 32, kernel_size=(7,7), stride=1, padding=3),
            BatchNorm2d(32),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=(2,2),padding = 1),
            
            Conv2d(32, 64, kernel_size=(7,7), stride=1, padding=3),
            BatchNorm2d(64),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            Conv2d(64, 128, kernel_size=(7,7), stride=1, padding=3),
            BatchNorm2d(128),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            Conv2d(128, 256, kernel_size=(7,7), stride=1, padding=3),
            BatchNorm2d(256),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(3,3), stride=2, padding = 1),
            
            AdaptiveAvgPool2d((1, 1))
        )
        self.linear_layers = Sequential(
            Linear(in_features= 256, out_features=10, bias = True)
        )
    def forward(self, x):
        x = self.cnn_layers(x)
        x = x.view(x.size(0), -1)
        x = self.linear_layers(x)
        return x
        