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
from segment import shiftRect

# IPL_BORDER_CONSTANT = 0
# IPL_BORDER_REPLICATE = 1

def repaintCCs(image, doRepaint=None, returnMask=False, resizeMask=True, doFillBackground=True, bgPoint=(0, 0), newcol=255, connectivity=4):
    if doRepaint is None:
        doRepaint = lambda comp, col: False
    resultMask = cv.CreateImage((image.width + 2, image.height + 2), image.depth, image.nChannels)
    tempMask = cv.CreateImage((image.width + 2, image.height + 2), image.depth, image.nChannels)
    visitMask = cv.CreateImage((image.width + 2, image.height + 2), image.depth, image.nChannels)
    cv.Zero(resultMask)
    cv.Zero(tempMask)
    cv.Zero(visitMask)
    if doFillBackground:
        cv.FloodFill(image, bgPoint, 0, 0, 0, connectivity + cv.CV_FLOODFILL_MASK_ONLY + (255 << 8), visitMask)
    for x in xrange(image.width):
        for y in xrange(image.height):
            if visitMask[y + 1, x + 1] == 255:
                continue
            comp = cv.FloodFill(image, (x, y), 0, 0, 0, connectivity + cv.CV_FLOODFILL_MASK_ONLY + (255 << 8), tempMask)
            region = shiftRect(comp[2], 1, 1)
            cv.SetImageROI(tempMask, region)
            cv.SetImageROI(visitMask, region)
            cv.Or(tempMask, visitMask, visitMask)
            if doRepaint(comp, image[y, x]):
                cv.SetImageROI(resultMask, region)
                cv.Or(tempMask, resultMask, resultMask)
                cv.ResetImageROI(resultMask)
            cv.Zero(tempMask)
            cv.ResetImageROI(tempMask)
            cv.ResetImageROI(visitMask)
    if returnMask:
        if resizeMask: return cap.getSubImage(resultMask, (1, 1, image.width, image.height))
        else: return resultMask
    else:    
        cv.SetImageROI(resultMask, (1, 1, image.width, image.height))
        cv.Set(image, newcol, resultMask)
        return image

def smoothNoise1(image, bgcolor=255):
    temp = cv.CreateImage((image.width + 2, image.height + 2), image.depth, image.nChannels)
    result = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    cv.CopyMakeBorder(image, temp, (1, 1), 0, bgcolor)
    for x in xrange(1, image.width + 1):
        for y in xrange(1, image.height + 1):
            if   temp[y + 1, x] == temp[y - 1, x] and temp[y, x] != temp[y + 1, x]:
                result[y - 1, x - 1] = temp[y + 1, x]
            elif temp[y, x + 1] == temp[y, x - 1] and temp[y, x] != temp[y, x + 1]:
                result[y - 1, x - 1] = temp[y, x + 1]
            else:
                result[y - 1, x - 1] = temp[y, x]
    return result