"""
    Copyright 2011 Dmitry Nikulin

    This file is part of Captchure.

    Captchure is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Captchure is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Captchure.  If not, see <http://www.gnu.org/licenses/>.
"""

import cv
from pyfann import libfann
from cvext import copyTo
from general import argmax

def loadAnn(ann_file):
    ann = libfann.neural_net()
    ann.create_from_file(ann_file)
    return ann

def flattenImage(image):
    lst = []
    for y in range(image.height):
        for x in range(image.width):
            n = image[y, x] / 127.5 - 1.0
            lst.append(n)
    return lst

def resizeNaive(image, size):
    result = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    cv.Resize(image, result, cv.CV_INTER_CUBIC)
    return result

def resizeProp(image, (segW, segH)):
    result = cv.CreateImage((segW, segH), image.depth, image.nChannels)
    cv.Zero(result)
    if image.width <= segW and image.height <= segH:
        offW = (segW - image.width) / 2
        offH = (segH - image.height) / 2
        copyTo(image, result, (offW, offH), None)
    else:
        scaleW = float(segW) / float(image.width)
        newH = image.height * scaleW
        if newH <= segH:
            offH = (segH - newH) / 2.0
            rect = (0, int(offH), segW, int(newH))
        else:
            scaleH = float(segH) / float(image.height)
            newW = image.width * scaleH
            offW = (segW - newW) / 2.0
            rect = (int(offW), 0, int(newW), segH)
        cv.SetImageROI(result, rect)
        cv.Resize(image, result, cv.CV_INTER_CUBIC)
        cv.ResetImageROI(result)
    return result

def resizeFit(image, (segW, segH)):
    result = cv.CreateImage((segW, segH), image.depth, image.nChannels)
    cv.Zero(result)
    if image.width > segW:
        if image.height > segH:
            cv.Resize(image, result, cv.CV_INTER_CUBIC)
        else:
            temp = cv.CreateImage((segW, image.height), image.depth, image.nChannels)
            cv.Resize(image, temp, cv.CV_INTER_CUBIC)
            offH = (segH - image.height) / 2
            copyTo(temp, result, (0, offH), None)
    else:
        if image.height > segH:
            temp = cv.CreateImage((image.width, segH), image.depth, image.nChannels)
            cv.Resize(image, temp, cv.CV_INTER_CUBIC)
            offW = (segW - image.width) / 2
            copyTo(temp, result, (offW, 0), None)
        else:
            offW = (segW - image.width) / 2
            offH = (segH - image.height) / 2
            copyTo(image, result, (offW, offH), None)
    return result

def recogniseChar(image, ann, charset):
    result = ann.run(flattenImage(image))
    return charset[argmax(result)]

def defaultRecognise(segments, addr, extras, ann, size, charset, resizer):
    segments = map(lambda seg: resizer(seg, size), segments)
    return "".join(map(lambda seg: recogniseChar(seg, ann, charset), segments))