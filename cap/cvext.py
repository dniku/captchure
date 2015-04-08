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
from math import ceil, sin, cos, radians as rad

def getSubImage(image, rect):
    region = cv.GetSubRect(image, rect)
    image = cv.CreateImage(cv.GetSize(region), image.depth, image.nChannels)
    cv.Copy(region, image, None)
    return image
    
def copyTo(src, dst, point, mask=None):
    if not (point[0] + src.width <= dst.width and point[1] + src.height <= dst.height):
        msg = "Source image is too large: %dx%d, maximum is %dx%d" % (src.width, src.height, \
                                                                      dst.width - point[0], dst.height - point[1])
        raise cv.error(msg)
    try:
        region = cv.GetSubRect(dst, (point[0], point[1], src.width, src.height))
    except:
        print "cv.GetSubRect failure, arguments: " + str((point[0], point[1], src.width, src.height))
        raise
    cv.Copy(src, region, mask)

def doResize(image, factor, method=cv.CV_INTER_CUBIC):
    result = cv.CreateImage((int(image.width * factor), int(image.height * factor)), image.depth, image.nChannels)
    cv.Resize(image, result, method)
    return result

def doRotate(image, alpha, fillval=0, resize=True, interpolation=cv.CV_INTER_CUBIC):
    matrix = cv.CreateMat(2, 3, cv.CV_32FC1)
    w, h = cv.GetSize(image)
    center = ((w - 1) / 2.0, (h - 1) / 2.0)
    cv.GetRotationMatrix2D(center, alpha, 1.0, matrix)
    if resize:
        angle = rad(abs(alpha))
        nw = w * cos(angle) + h * sin(angle)
        nh = w * sin(angle) + h * cos(angle)
        ncenter = (nw / 2.0, nh / 2.0)
        matrix[0, 2] += ncenter[0] - center[0]
        matrix[1, 2] += ncenter[1] - center[1]
        size = (int(ceil(nw)), int(ceil(nh)))
    else:
        size = cv.GetSize(image)
    result = cv.CreateImage(size, image.depth, image.nChannels)
    cv.WarpAffine(image, result, matrix, interpolation + cv.CV_WARP_FILL_OUTLIERS, fillval)
    return result

def roundXY(pt):
    return (cv.Round(pt[0]), cv.Round(pt[1]))

def minAreaRectImage(image, returnPoints=True):
    points = []
    for x in xrange(image.width):
        for y in xrange(image.height):
            if image[y, x] > 128: points.append((x, y))
    box = cv.MinAreaRect2(points)
    if not returnPoints:
        return box
    box_vtx = map(roundXY, cv.BoxPoints(box))
    return box_vtx
    