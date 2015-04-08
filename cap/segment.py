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

import cv, cvext, general
from operator import itemgetter, attrgetter
from numpy import linspace
from types import TupleType, ListType

def unwrap(components):
    t1 = type(components[0]) 
    if (t1 == TupleType or t1 == ListType):
        t2 = type(components[0][3])
        if t2 == cv.iplimage or t2 == cv.cvmat:
            return map(itemgetter(3), components)
    elif t1 == cv.iplimage or t1 == cv.cvmat:
        return components

def shiftRect(rect, x, y):
    return (rect[0] + x, rect[1] + y, rect[2], rect[3])

def findCCs(image, erasecol=0, doContinue=None, doSkip=None, bRange=0, connectivity=8):
    """
    Finds all connected components in the image.
    doContinue is a function applied to the color of every new pixel in the image.
    If it is true, this pixel is ignored. Default: <= 128
    doSkip is a function applied to every new connected component found by the
    function. If it is true, this component will not be included in the result.
    Default: do not skip anything.
    """
    if doContinue is None:
        doContinue = lambda col: col <= 128
    if doSkip is None:
        doSkip = lambda comp: False
    mask = cv.CreateImage((image.width + 2, image.height + 2), cv.IPL_DEPTH_8U, 1)
    cv.Zero(mask)
    components = []
    for x in range(image.width):
        for y in range(image.height):
            if doContinue(image[y, x]):
                continue
            comp = cv.FloodFill(image, (x, y), 0, bRange, bRange, connectivity + cv.CV_FLOODFILL_MASK_ONLY + (255 << 8), mask) # here 3rd argument is ignored
            region = shiftRect(comp[2], 1, 1)
            if not doSkip(comp):
                seg = cvext.getSubImage(mask, region)
                components.append((comp[0], comp[1], comp[2], seg))
            cv.SetImageROI(image, comp[2])
            cv.SetImageROI(mask, region)
            cv.Set(image, erasecol, mask)
            cv.Zero(mask)
            cv.ResetImageROI(image)
            cv.ResetImageROI(mask)
    return components

def rectsIntersectH(rect1, rect2):
    minW3 = min(rect1[2], rect2[2]) / 3
    l1 = rect1[0]
    l2 = rect2[0]
    r1 = rect1[0] + rect1[2]
    r2 = rect2[0] + rect2[2]
    return (l2 < r1 - minW3 and r2 > l1 + minW3) or \
           (l1 < r2 - minW3 and r1 > l2 + minW3)

def distV(rect1, rect2):
    t1, b1 = rect1[1], rect1[1] + rect1[3]
    t2, b2 = rect2[1], rect2[1] + rect2[3]
    if b1 < t2: return t2 - b1
    if b2 < t1: return t1 - b2
    return 0

def distH(rect1, rect2):
    l1, r1 = rect1[0], rect1[0] + rect1[2]
    l2, r2 = rect2[0], rect2[0] + rect2[2]
    if r1 < l2: return l2 - r1
    if r2 < l1: return l1 - r2
    return 0

def joinComponents(components):
    rects = [comp[2] for comp in components]
    rect = (min([rect[0] for rect in rects]), min([rect[1] for rect in rects]), \
            max([rect[0] + rect[2] for rect in rects]), max([rect[1] + rect[3] for rect in rects]))
    resW = rect[2] - rect[0]
    resH = rect[3] - rect[1]
    result = cv.CreateImage((resW, resH), cv.IPL_DEPTH_8U, 1)
    cv.Zero(result)
    for comp in components:
        region = cv.GetSubRect(result, shiftRect(comp[2], -rect[0], -rect[1]))
        cv.Or(comp[3], region, region, None)
    return [sum([comp[0] for comp in components]), 255.0, \
            (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]), result]

def joinCCs(components, rectsIntersect):
    i = 0
    while i < len(components) - 1:
        brothers = filter(lambda j: rectsIntersect(components[i][2], components[j][2]), xrange(i+1, len(components)))
        if brothers == []:
            i += 1
            continue
        brothers.append(i)
        family = joinComponents(map(lambda bro: components[bro], brothers))
        components = [components[j] for j in xrange(len(components)) if j not in brothers]
        components[i:i] = [family]
    return components

def splitAt(image, splitters):
    if splitters == []:
        return [image]
    segments = []
    regions = []
    for i in xrange(len(splitters) - 1):
        region = (splitters[i], 0, splitters[i+1] - splitters[i], image.height)
        regions.append(region)
        seg = cvext.getSubImage(image, region)
        segments.append(seg)
    return segments, regions

def projectDown(image):
    proj = []
    for x in range(image.width):
        col = cv.GetCol(image, x)
        sum = cv.Sum(col)
        proj.append(sum)
    return proj

def splitIntoNParts(image, parts, projRadius):
    splitters = linspace(0, image.width - 1, parts + 1)
    projection = projectDown(image)
    def adjust(splitter):
        if splitter == 0 or splitter == image.width - 1:
            return splitter
        neighborhood = projection[splitter - projRadius : splitter + projRadius + 1]
        return general.argmin(neighborhood) + splitter - projRadius
    splitters = general.amap(adjust, splitters.astype(int))
    segments, regions = splitAt(image, splitters)
    return segments, regions

CAP_BOUND_LEFT   = 0
CAP_BOUND_RIGHT  = 1
CAP_BOUND_TOP    = 2
CAP_BOUND_BOTTOM = 3

def getBound(image, bound, thresh=1, colthresh=0, start=None, stop=None):
    if bound == CAP_BOUND_LEFT or bound == CAP_BOUND_RIGHT:
        if bound == CAP_BOUND_LEFT:
            if start is None: start = 0
            if stop is None:  stop  = image.width
            step = 1
        else:
            if start is None: start = image.width - 1
            if stop is None:  stop  = -1
            step = -1
        for x in xrange(start, stop, step):
            n = 0
            for y in xrange(image.height):
                if image[y, x] > colthresh:
                    n += 1
                if n >= thresh:
                    return x
        return start
    elif bound == CAP_BOUND_TOP or bound == CAP_BOUND_BOTTOM:
        if bound == CAP_BOUND_TOP:
            if start is None: start = 0
            if stop is None:  stop  = image.height
            step = 1
        else:
            if start is None: start = image.height - 1
            if stop is None:  stop  = -1
            step = -1
        for y in xrange(start, stop, step):
            n = 0
            for x in xrange(image.width):
                if image[y, x] > colthresh:
                    n += 1
                if n >= thresh:
                    return y
        return start
    else: raise ValueError("Cannot interpret 'bound' argument (%d)" % (bound))

def findNonBlackRect(image, thresh, colthresh=0):
    newTop    = getBound(image, CAP_BOUND_TOP,    thresh, colthresh)
    newBottom = getBound(image, CAP_BOUND_BOTTOM, thresh, colthresh)
    newLeft   = getBound(image, CAP_BOUND_LEFT,   thresh, colthresh)
    newRight  = getBound(image, CAP_BOUND_RIGHT,  thresh, colthresh)
    return (newLeft, newTop, newRight - newLeft, newBottom - newTop)

def cutNonBlackImage(image, thresh=1, colthresh=0):
    newRect = findNonBlackRect(image, thresh, colthresh)
    if newRect[2] == 0 or newRect[3] == 0:
        return None
    region = cvext.getSubImage(image, newRect)
    return region

def cutNonBlack(comp, thresh, colthresh=0):
    image = comp[3]
    rect = comp[2]
    newRect = findNonBlackRect(image, thresh, colthresh)
    if newRect[2] == 0 or newRect[3] == 0:
        return None
    region = cvext.getSubImage(image, newRect)
    newRect = shiftRect(newRect, rect[0], rect[1])
    return (cv.CountNonZero(region), 255.0, newRect, region)

def partsFromSegW(components, segW):
    return map(lambda comp: comp[3].width / segW + 1, components)

# Doesn't work, needs thinking on
#expansions = {}
#
#def getExpansion(n):
#    if n in expansions:
#        return expansions[n]
#    cur = [(1, )]
#    for i in xrange(1, n):
#        a = deque(cur)
#        b = deque(cur)
#        a.append((1, ) * i)
#        b.appendleft((i, ))
#        cur = map(lambda x, y: ((x[0] + 1) + x[1:]), a, b)
#    expansions[n] = cur
#    return cur

five = \
    ((5, ), \
    (1, 4), (2, 3), (3, 2), (4, 1), \
    (1, 1, 3), (1, 3, 1), (3, 1, 1), (2, 2, 1), (2, 1, 2), (1, 2, 2), \
    (1, 1, 1, 2), (1, 1, 2, 1), (1, 2, 1, 1), (2, 1, 1, 1), \
    (1, 1, 1, 1, 1))

five3 = filter(lambda exp: len(exp) == 3, five)

def distance(pt1, pt2):
    if len(pt1) != len(pt2):
        raise ValueError("Points must be of the same dimensionality.")
    return sum([(x1 - x2)**2 for (x1, x2) in zip(pt1, pt2)])
    

def partsFromnSegs5(components):
    segments = unwrap(components)
    if len(segments) == 5:
        return (1, 1, 1, 1, 1)
    elif len(segments) == 4:
        widths = map(attrgetter("width"), segments)
        widest = general.argmax(widths)
        result = [1] * 4
        result[widest] = 2
        return result
    elif len(segments) == 3:
        widths = map(attrgetter("width"), segments)
        narrowest = float(min(widths))
        reduced = map(lambda width: width / narrowest, widths)
        distances = map(lambda exp: distance(exp, reduced), five3)
        #print widths, narrowest, reduced, zip(distances, five3)
        return five3[general.argmin(distances)]
    elif len(segments) == 2:
        w0, w1 = segments[0].width, segments[1].width
        frac = float(w0) / float(w1)
        if frac < 1.0: frac = 1.0 / frac
        if frac > 2.75: return (4, 1) if w0 > w1 else (1, 4)
        else: return (3, 2) if w0 > w1 else (2, 3)
    elif len(segments) == 1:
        return (5, )
    else: return (1, ) * len(segments) # raise ValueError("Incorrect number of components: %d" % (len(segments)))

def spltCCs(components, allParts, projRadius, thresh=2):
    index = 0
    for parts in allParts:
        assert(parts >= 1)
        comp = components[index]
        seg = comp[3]
        rect = comp[2]
        if parts > 1:
            segments, rects = splitIntoNParts(seg, parts, projRadius)
            rects = map(lambda rect1: shiftRect(rect1, rect[0], rect[1]), rects)
            mapper = lambda segIndex: (0.0, 255.0, \
                                       rects[segIndex], segments[segIndex])
            comp = map(mapper, xrange(parts))
            comp = map(lambda comp: cutNonBlack(comp, thresh), comp)
            comp = filter(lambda comp: comp is not None, comp)
            components[index: index + 1] = comp
        index += parts
    return components