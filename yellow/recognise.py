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

import os, cv, cap
from operator import itemgetter
from numpy import linspace
from lconsts import ann_dir, ann_file, charset, segSize
from cap import resizeFit as adjustSize

ann = cap.loadAnn(ann_file)

def recogniseOne(seg):
    resized = adjustSize(seg, segSize)
    array = cap.flattenImage(resized)
    guesses = ann.run(array)
    ichar = cap.argmax(guesses)
    guess = guesses[ichar]
    return (guess, ichar)

def findRect(image, left, right):
    cols = cv.GetCols(image, left, right)
    top    = cap.getBound(cols, cap.CAP_BOUND_TOP, colthresh=128)
    bottom = cap.getBound(cols, cap.CAP_BOUND_BOTTOM, colthresh=128)
    return (left, top, right - left, bottom - top)

def splitRecogniseOne(image, parts, shiftRadius):
    result = ""
    splitters = linspace(0, image.width - 1, parts + 1).astype(int)
    for index in xrange(parts - 1, 0, -1):
        splitter = splitters[index]
        results = []
        for x in xrange(splitter - shiftRadius, splitter + shiftRadius + 1):
            rect = findRect(image, x, splitters[index + 1])
            seg = cap.getSubImage(image, rect)
            guess, ichar = recogniseOne(seg)
            results.append((guess, ichar, x, rect))
        best = max(results, key=itemgetter(0))
        #print best[0]
        splitters[index] = best[2]
        result += charset[best[1]]
    firstSeg = cap.getSubImage(image, findRect(image, 0, splitters[1]))
    guess, ichar = recogniseOne(firstSeg)
    #print guess
    result += charset[ichar]
    for s in splitters[1:-1]:
        cv.Line(image, (s, 0), (s, image.height - 1), 128, 1)
    return result[::-1]

def splitRecogniseAll(segments, allParts, shiftRadius):
    result = ""
    for index, parts in enumerate(allParts):
        assert(parts >= 1)
        seg = segments[index]
        if parts > 1: result += splitRecogniseOne(seg, parts, shiftRadius)
        else:
            guess, ichar = recogniseOne(seg)
            #print guess
            result += charset[ichar]
    return result

def recognise(segments, addr, extras):
    allParts = cap.partsFromnSegs5(segments)
    result = splitRecogniseAll(segments, allParts, shiftRadius=4)
    cap.processExtras([cap.joinImagesH(segments)], addr, extras, cap.CAP_STAGE_RECOGNISE)
    return result