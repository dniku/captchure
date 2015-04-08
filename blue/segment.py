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
from operator import itemgetter
from lconsts import nSegs

from math import sqrt
def doRotate(image, alpha, fillval=0, resize=True, interpolation=cv.CV_INTER_CUBIC):
    matrix = cv.CreateMat(2, 3, cv.CV_32FC1)
    w, h = cv.GetSize(image)
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    cv.GetRotationMatrix2D(center, alpha, 1.0, matrix)
    if resize:
        d = sqrt(w*w + h*h)
        d2 = d / 2.0
        matrix[0, 2] += d2 - center[0]
        matrix[1, 2] += d2 - center[1]
        d = int(d)
        size = (d, d)
    else:
        size = cv.GetSize(image)
    result = cv.CreateImage(size, image.depth, image.nChannels)
    cv.WarpAffine(image, result, matrix, interpolation + cv.CV_WARP_FILL_OUTLIERS, fillval)
    return result

def findLineSlope(pt1, pt2):
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]
    result = cv.FastArctan(dy, dx)
    if result >= 180.0:
        result -= 180.0
    result = 180.0 - result
    if result >= 90.0:
        result -= 180.0
    return result

def deRotate(seg):
    box_vtx = cap.minAreaRectImage(seg)
    pts = sorted(box_vtx, key=lambda vtx: vtx[1], reverse=True)[:2]
    slope = findLineSlope(*pts)
    if slope < 20.0:
        seg = doRotate(seg, -slope, fillval=0, resize=True)
        seg = cap.getSubImage(seg, cap.findNonBlackRect(seg, thresh=1))
    return seg

def segment(image, addr, extras):
    clone = cv.CloneImage(image)
    log = cap.logger(extras, image)
    components = cap.findCCs(image, erasecol=255, doContinue=lambda col: col == 255, doSkip=lambda comp: comp[0] <= 20)
    #components = cap.spltCCs(components, cap.partsFromSegW(components, 20), projRadius=5, thresh=1)
    log.log(cap.drawComponents(clone, components))
    while len(components) > nSegs:
        smallest = cap.argmin(components, itemgetter(0))
        del(components[smallest])
    assert(len(components) == nSegs)
    log.log(cap.drawComponents(clone, components))
    segments = map(lambda comp: comp[3], components)
    log.log(cap.joinImagesH(segments))
    segments = map(deRotate, segments)
    log.log(cap.joinImagesH(segments))
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_SEGMENT)
    return segments