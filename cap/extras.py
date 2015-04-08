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

import os, types, cv, cvext
from operator import itemgetter
from consts import *

def getFilename(addr):
    return os.path.splitext(os.path.basename(addr))[0]

def addFakeChannels(image):
    if image.nChannels == 3:
        return image
    if image.nChannels != 1:
        raise ValueError("Input image must be 1- or 3-channel.")
    result = cv.CreateImage(cv.GetSize(image), image.depth, 3)
    cv.CvtColor(image, result, cv.CV_GRAY2BGR)
    return result

def joinImagesV(images, bgcolor=128):
    totalHeight = sum([image.height for image in images])
    maxWidth = max([image.width for image in images])
    maxNChannels = max([image.nChannels for image in images])
    if maxNChannels == 3:
        images = map(addFakeChannels, images)
        bgcolor = cv.ScalarAll(bgcolor)
    total = len(images)
    result = cv.CreateImage((maxWidth, totalHeight + total - 1), images[0].depth, images[0].nChannels)
    cv.Set(result, bgcolor)
    curH = 0
    for index in xrange(len(images)):
        image = images[index]
        off = (maxWidth - image.width) / 2
        cvext.copyTo(image, result, (off, curH), None)
        curH += image.height + 1
    return result

def joinImagesH(images, bgcolor=128):
    totalWidth = sum([image.width for image in images])
    maxHeight = max([image.height for image in images])
    maxNChannels = max([image.nChannels for image in images])
    if maxNChannels == 3:
        images = map(addFakeChannels, images)
        bgcolor = cv.ScalarAll(bgcolor)
    total = len(images)
    result = cv.CreateImage((totalWidth + total - 1, maxHeight), images[0].depth, images[0].nChannels)
    cv.Set(result, bgcolor)
    curW = 0
    for index in xrange(len(images)):
        image = images[index]
        off = (maxHeight - image.height) / 2
        cvext.copyTo(image, result, (curW, off), None)
        curW += image.width + 1
    return result

def drawComponents(image, components, startcol=192, stepcol=8):
    result = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 3)
    cv.CvtColor(image, result, cv.CV_GRAY2BGR)
    if len(components) == 0: return result
    if type(components[0][2]) == types.TupleType:
        rects = map(itemgetter(2), components)
    else:
        rects = components
    for index, rect in enumerate(rects):
        pt1 = (rect[0], rect[1])
        pt2 = (rect[0] + rect[2], rect[1] + rect[3])
        cv.Rectangle(result, pt1, pt2, (0, 0, startcol + stepcol * index), 1)
    return result

suffixes = {CAP_STAGE_PRE:"pre", CAP_STAGE_SEG:"seg", CAP_STAGE_REC:"rec"}
titles = {CAP_STAGE_PRE:"Preprocessing", CAP_STAGE_SEG:"Segmentation", CAP_STAGE_REC:"Recognition"}

def getSuffix(stage):
    try: suffix = suffixes[stage]
    except KeyError: raise ValueError("Incorrect stage parameter")
    return suffix

def getTitle(stage):
    try: title = titles[stage]
    except KeyError: raise ValueError("Incorrect stage parameter")
    return title

def processExtras(steps, addr, extras, stage):
    if extras == CAP_EXTRAS_OFF:
        return
    result = joinImagesV(steps)
    if extras == CAP_EXTRAS_SAVE:
        name = getFilename(addr)
        suf = getSuffix(stage)
        #newaddr = os.path.join(extras_dir, name + "_" + suf)
        #for index, image in enumerate(steps):
        #    cv.SaveImage(newaddr + str(index) + defext, image)
        newaddr = os.path.join(extras_dir, name + "_" + suf + defext)
        cv.SaveImage(newaddr, result)
    elif extras == CAP_EXTRAS_SHOW:
        title = getTitle(stage)
        cv.NamedWindow(title + " steps", 0)
        cv.ShowImage(title + " steps", result)

class logger:
    def __init__(self, extras, image=None, clone=True):
        self.steps = []
        if extras == CAP_EXTRAS_OFF:
            self.log = self.dontLog
        else:
            self.log = self.doLog
            if image is not None:
                self.log(image, clone)
    def dontLog(self, image, clone=True):
        pass
    def doLog(self, image, clone=True):
        if clone: self.steps.append(cv.CloneImage(image))
        else: self.steps.append(image)