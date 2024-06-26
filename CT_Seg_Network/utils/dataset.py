import numpy as np
from PIL import Image
import random
import torch
from torch.utils.data import Dataset
#import torchvision.transforms as transforms
from torchvision.transforms import v2 as transforms
import cv2
import os


class CenterCrop(object):
    def __init__(self,arg):
        self.transform = transforms.CenterCrop(arg)
    def __call__(self, sample):
        img, label = sample
        return self.transform(img),self.transform(label)

class Resize(object):
    def __init__(self,arg):
        self.transform_img = transforms.Resize(arg,Image.BILINEAR)
        self.transform_label = transforms.Resize(arg,Image.NEAREST)

    def __call__(self, sample):
        img, label = sample
        return self.transform_img(img),self.transform_label(label)

class Normalize(object):
    def __init__(self,mean,std):
        self.transform = transforms.Normalize(mean, std)
    def __call__(self, sample):
        img, label = sample
        return self.transform(img),label

class ToTensor(object):
    def __init__(self):
        pass
    def __call__(self, sample):
        img, label = sample
        label = np.array(label)/255
        img = np.array(img)/255

        return torch.from_numpy(img.transpose((2, 0, 1))).float(),torch.from_numpy(label.copy()).long()

class RandomRescale(object):
    def __init__(self,min_ratio=0.5,max_ratio=1.0):
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
    def __call__(self, sample):
        img, label = sample
        width, height = img.size
        ratio = random.uniform(self.min_ratio,self.max_ratio)
        new_width, new_height = int(ratio*width), int(ratio*height)
        return img.resize((new_width,new_height)), label.resize((new_width,new_height))

class RandomFlip(object):
    def __init__(self,p=0.5):
        self.p = p

    def __call__(self, sample):
        img, label = sample
        if random.uniform(0,1)>self.p:
            return transforms.functional.hflip(img),transforms.functional.hflip(label)
        else:
            return img, label

class RandomColor(object):
    def __init__(self,brightness=0.2,contrast=0.2,saturation=0.2,hue=0.2):
        self.transform = transforms.ColorJitter(brightness,contrast,saturation,hue)
    def __call__(self, sample):
        img, label = sample
        return self.transform(img),label

class RandomRotation(object):
    def __init__(self, degree=[-10,10]):
        self.degree = degree

    def __call__(self, sample):
        img, label = sample

        angle = transforms.RandomRotation.get_params(self.degree)

        img = transforms.functional.rotate(img, angle,resample = Image.BILINEAR)
        label = transforms.functional.rotate(label, angle)
        return img, label

class RandomCrop(object):
    def __init__(self,output_size,fill=0, padding_mode='constant'):
        self.output_size = output_size
        self.fill = fill
        self.padding_mode = padding_mode
        self.pad_if_needed = True
    def __call__(self, sample):
        img, label = sample

        # pad the width if needed
        if self.pad_if_needed and img.size[0] < self.output_size[1]:
            img = transforms.functional.pad(img, (self.output_size[1] - img.size[0], 0), self.fill, self.padding_mode)
            label = transforms.functional.pad(label, (self.output_size[1] - label.size[0], 0), self.fill, self.padding_mode)
        # pad the height if needed
        if self.pad_if_needed and img.size[1] < self.output_size[0]:
            img = transforms.functional.pad(img, (0, self.output_size[0] - img.size[1]), self.fill, self.padding_mode)
            label = transforms.functional.pad(label, (0, self.output_size[0] - label.size[1]), self.fill, self.padding_mode)

        i, j, h, w = transforms.RandomCrop.get_params(
            img, output_size=self.output_size)

        img = transforms.functional.crop(img, i, j, h, w)
        label = transforms.functional.crop(label, i, j, h, w)

        return img, label


class SegCTDataset(Dataset):
    """Covid XRay dataset."""

    def __init__(self, txt, transforms):
        self.IMAGE_LIB = '../Segmen/data/2d_images/'
        self.MASK_LIB = '../Segmen/data/2d_masks/'

        self.images = np.loadtxt(txt, dtype=str)

        self.transform = transforms

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        image_name = self.images[idx]
        img = cv2.imread(self.IMAGE_LIB + image_name, cv2.IMREAD_UNCHANGED).astype("int16").astype('float32')
        img = (img - np.min(img)) / (np.max(img) - np.min(img))
        img = Image.fromarray(np.uint8(img * 255)).convert('RGB')
        label = Image.open(self.MASK_LIB + image_name)
        if self.transform:
            img, label = self.transform((img, label))
        sample = {'img': img,
                  'label': label}
        return sample

class SegCOVICTDataset(Dataset):
    """Covid XRay dataset."""

    def __init__(self, covid_txt, non_covid_txt, image_dir, mask_dir, transforms=None):
        self.IMAGE_LIB = image_dir
        self.MASK_LIB = mask_dir

        self.images = ['CT_COVID/{}'.format(name) for name in np.loadtxt(covid_txt, dtype=str)]+ \
                      ['CT_NonCOVID/{}'.format(name) for name in np.loadtxt(non_covid_txt, dtype=str)]

        self.transform = transforms

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        image_name = self.images[idx]
        img = Image.open(os.path.join(self.IMAGE_LIB, image_name)).convert('RGB')
        label = Image.open(os.path.join(self.MASK_LIB, image_name)).convert('L')
        if self.transform:
            img, label = self.transform((img, label))
        sample = {'img': img,
                  'label': label}
        return sample
    

class CallistoCTDataset(Dataset):
    def __init__(self, covid_txt, non_covid_txt, image_dir, mask_dir, transforms=None):
        self.IMAGE_LIB = image_dir
        self.MASK_LIB = mask_dir

        self.images = ['CT_COVID/{}'.format(name) for name in np.loadtxt(covid_txt, dtype=str)]+ \
                      ['CT_NonCOVID/{}'.format(name) for name in np.loadtxt(non_covid_txt, dtype=str)]

        self.transform = transforms

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        image_name = self.images[idx]
        img = Image.open(os.path.join(self.IMAGE_LIB, image_name)).convert('RGB')
        label = Image.open(os.path.join(self.MASK_LIB, image_name)).convert('L')
        if self.transform:
            img, label = self.transform((img, label))
        sample = {'img': img,
                  'label': label}
        return sample