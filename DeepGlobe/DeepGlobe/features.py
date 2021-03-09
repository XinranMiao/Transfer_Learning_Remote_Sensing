import urllib.request
import tarfile
from pathlib import Path
from data import create_dir, download_data
import os
import cv2 
import glob
import matplotlib.image as mpimg 
import matplotlib.pyplot as plt 

from torch.utils.data import Dataset, DataLoader
from torchvision import  transforms
import torch
import torch.nn as nn
import torch.nn.functional as F

import numpy as np
import os
import random
import shutil
import tarfile
import torch
import torchvision.transforms.functional as TF
import urllib.request


import numpy as np
from tqdm import tqdm
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from torch.autograd import Variable
from PIL import Image


'''
x: 4-dim torch.tensor (2,3,2448,2448)
'''
def extract_features(x,model,flatten = False, batch_size = 1):
    data_x = []

    inputs = x.numpy().copy()
    #input_data = torch.tensor(inputs,dtype = torch.float)
    #input_data = Variable(input_data)
    
    #features = model.features(input_data)
    #avg_features = model.avgpool(features)

    for i in tqdm(range(int(x.shape[0]/batch_size))): 
        input_data = torch.tensor(inputs[i*batch_size:(i+1)*batch_size],dtype = torch.float)

        input_data  = Variable(input_data)
        
        input_data = model.features(input_data)

        input_data= model.avgpool(input_data)

        data_x.extend(input_data.data.cpu().numpy())
    
    data_x  = torch.from_numpy(np.array(data_x))
    if flatten:
        data_x = data_x.view(data_x.size(0), -1)
    
    del inputs,input_data
    
    return data_x