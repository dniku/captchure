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
from lconsts import mycolors, nSegs, segSize, ann_file, charset
from cap import resizeFit as adjustSize

minW = 15
maxW = 40

ann = cap.loadAnn(ann_file)
colors = map(lambda col: 255 - col, mycolors)

def findBounds(image, right, w):
    left = right - w + 1
    cols = cv.GetCols(image, left, right + 1)
    top    = cap.getBound(cols, cap.CAP_BOUND_TOP)
    bottom = cap.getBound(cols, cap.CAP_BOUND_BOTTOM)
    return (left, top, w, bottom - top)

def extractCol(image, col):
    result = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    cv.CmpS(image, col, result, cv.CV_CMP_EQ)
    return result

def getChannels(image):
    return map(lambda col: extractCol(image, col), colors)

def findColors(image):
    flags  = [False, False, False, False]
    for x in xrange(image.width):
        for y in xrange(image.height):
            col = image[y, x]
            if col == 0: continue
            flags[cap.find(colors, col)] = True
    return flags

def getSegment(channel, image, rect, bgcolor=96):
    seg      = cap.getSubImage(channel, rect)
    original = cv.GetSubRect  (image,   rect)
    for x in xrange(original.width):
        for y in xrange(original.height):
            if original[y, x] != 0 and seg[y, x] != 255:
                seg[y, x] = bgcolor
    return seg


def recognise(image, addr, extras):
    result = ""
    x = image.width - 1
    channels = getChannels(image)
    bestBounds = []
    #cv.NamedWindow("pic", 1)
    #cv.NamedWindow("cols", 0)
    while len(result) < nSegs and x >= minW:
        x = cap.getBound(image, cap.CAP_BOUND_RIGHT, start=x)
        ratings = []
        for w in xrange(minW, min(maxW + 1, x)):
            bounds = findBounds(image, x, w)
            subImage = cap.getSubImage(image, bounds)
            flags = findColors(subImage)
            for index, flag in enumerate(flags):
                if not flag: continue
                seg = getSegment(channels[index], image, bounds)
                seg = cap.flattenImage(adjustSize(seg, segSize))
                guesses = ann.run(seg)
                charIndex = cap.argmax(guesses)
                ratings.append((guesses[charIndex], charIndex, index, bounds, seg))
        best = max(ratings, key=itemgetter(0))
        result += charset[best[1]]
        bestChannel = channels[best[2]]
        cv.SetImageROI(bestChannel, best[3])
        cv.Set(bestChannel, 96, bestChannel)
        cv.ResetImageROI(bestChannel)
        bestBounds.append(best[3])
        bestW = best[3][2]
        x -= bestW
        #print ann.run(best[4])
    cap.processExtras([cap.drawComponents(image, bestBounds)], addr, extras, cap.CAP_STAGE_RECOGNISE)
    return result[::-1]