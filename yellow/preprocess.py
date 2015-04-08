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

import cv, cap
from lconsts import mycolors, mygray, myblue, mylgrn, mydgrn, myunkn


# BGR
grays = ((153, 153, 153), (153, 102, 153), (102, 102, 153), (102, 102, 102))
blues = ((153, 51, 51), (102, 51, 51), (102, 51, 0), (102, 0, 0))
lgrns = ((102, 102, 51), (102, 153, 51), (51, 102, 51), (51, 102, 0))
dgrns = ((51, 51, 51), (0, 51, 0), (0, 0, 0))
white3 = (255, 255, 255)

white = 255
black = 0


def doCopyMakeBorder(image, border, fillval):
    result = cv.CreateImage((image.width + border * 2, image.height + border * 2), image.depth, image.nChannels)
    cv.CopyMakeBorder(image, result, (border, border), 0, fillval)
    return result

def removeLightColors(image):
    b = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    g = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    r = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.Split(image, b, g, r, None)
    cv.Threshold(b, b, 154, 255, cv.CV_THRESH_BINARY)
    cv.Threshold(g, g, 154, 255, cv.CV_THRESH_BINARY)
    cv.Threshold(r, r, 154, 255, cv.CV_THRESH_BINARY)
    cv.Or(b, g, b)
    cv.Or(b, r, b)
    cv.Set(image, cv.ScalarAll(255), b)
    return image

def remapColors(image):
    result = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    for x in xrange(image.width):
        for y in xrange(image.height):
            col = image[y, x]
            if   col in grays: result[y, x] = mygray
            elif col in blues: result[y, x] = myblue
            elif col in lgrns: result[y, x] = mylgrn
            elif col in dgrns: result[y, x] = mydgrn
            elif col == white3:result[y, x] = white
            else: result[y, x] = myunkn
    return result

def findColor(image, color):
    result = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.CmpS(image, color, result, cv.CV_CMP_EQ)
    return result

def smoothNoise2(image):
    b = 2
    temp = cv.CreateImage((image.width + 4, image.height + 4), image.depth, image.nChannels)
    result = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    # IPL_BORDER_CONSTANT = 0
    # IPL_BORDER_REPLICATE = 1
    cv.CopyMakeBorder(image, temp, (b, b), 0, 255)
    for x in xrange(b, image.width + b):
        for y in xrange(b, image.height + b):
            if   temp[y + 1, x] == temp[y - 1, x] and \
                 temp[y + 2, x] == temp[y - 2, x] and \
                 temp[y + 1, x] == temp[y + 2, x] and \
                 temp[y, x] != temp[y + 1, x]:
                result[y - b, x - b] = temp[y + 1, x]
            elif temp[y, x + 1] == temp[y, x - 1] and \
                 temp[y, x + 2] == temp[y, x - 2] and \
                 temp[y, x + 1] == temp[y, x + 2] and \
                 temp[y, x] != temp[y, x + 1]:
                result[y - b, x - b] = temp[y, x + 1]
            else:
                result[y - b, x - b] = temp[y, x]
    return result

def getNoiseMask(image, size, connectivity=8):
    mask = cv.CloneImage(image)
    for x in xrange(mask.width):
        for y in range(mask.height):
            col = mask[y, x]
            if col == black or col == white or col == 254:
                continue
            comp = cv.FloodFill(mask, (x, y), black, 0, 0, connectivity, None)
            if comp[0] > size:
                cv.FloodFill(mask, (x, y), 254, 0, 0, connectivity, None)
    cv.Threshold(mask, mask, 253, 255, cv.CV_THRESH_BINARY_INV)
    return mask

def doInpaint(image, mask):
    radius = 2
    result = doCopyMakeBorder(image, radius, 255)
    temp = doCopyMakeBorder(mask, radius, 0)
    cv.Inpaint(result, temp, result, radius, cv.CV_INPAINT_NS)
    result = cap.getSubImage(result, (radius, radius, image.width, image.height))
    return result

def makeLUT():
    lut = cv.CreateMat(1, 256, cv.CV_8UC1)
    colors = mycolors + (white, )
    for i in xrange(256):
        lut[0, i] = colors[cap.argmin(map(lambda col: abs(i - col), colors))]
    return lut

lut = makeLUT()

def sharpenColors(image):
    cv.LUT(image, image, lut)
    return image


def preprocess(image, addr, extras):
    log = cap.logger(extras, image)
    image = removeLightColors(image)
    log.log(image)
    image = remapColors(image)
    log.log(image)
    image = smoothNoise2(image)
    log.log(image)
    image = cap.smoothNoise1(image)
    log.log(image)
    mask = getNoiseMask(image, 15, 4)
    cv.Or(mask, findColor(image, myunkn), mask)
    log.log(mask)
    image = doInpaint(image, mask)
    log.log(image)
    image = sharpenColors(image)
    log.log(image)
    image = cap.repaintCCs(image, doRepaint=lambda comp, col: comp[0] <= 5 or comp[2][2] <= 2 or comp[2][3] <= 2)
    log.log(image)
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_PREPROCESS)
    return image