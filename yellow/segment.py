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

from __future__ import division
import cv, cap
from math import radians as rad, sqrt, sin, cos, tan, asin, fsum
from itertools import chain
from lconsts import nSegs, mygray, myblue, mylgrn, mydgrn

def dist2D((x1, y1), (x2, y2)):
    return sqrt((x1 - x2)**2 + (y1 - y2)**2)

def dist3D((x1, y1, z1), (x2, y2, z2)):
    return sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)

def distND(v1, v2):
    return sum([(c1 - c2)**2 for c1, c2 in zip(v1, v2)])

class piston:
    def __init__(self, (w, h)):
        # For now, include only support for rho=w//2, theta=0
        self.w = w
        self.h = h
        self.rho = w // 2
        self.theta = 0
        self.pos = float(-(h - 1))
        self.step = 0.05
        self.span = h - 1
        self.steps = int(self.span / self.step)
        self.setAlpha(0.0)
    def setAlpha(self, alpha):
        self.alpha = alpha
        self.ralpha = rad(alpha)
    def endPoints(self):
        off = self.rho * tan(self.ralpha)
        pt1 = (0,          -self.pos + off)
        pt2 = (self.w - 1, -self.pos - off)
        return (pt1, pt2)
    def coords(self, image):
        original = self.endPoints()
        (x1, y1), (x2, y2) = original
        try:
            clipped = cv.ClipLine((self.w, self.h), (int(x1), int(y1)), (int(x2), int(y2)))
        except:
            print self.alpha, self.pos
            raise
        if clipped is None:
            return None
        (x1c, y1c), (x2c, y2c) = clipped
        iter = cv.InitLineIterator(image, *clipped)
        clip = tuple(iter)
        cliplenpts = len(clip)
        cliplen = dist2D(*clipped)
        origlen = dist2D(*original)
        clipoff = dist2D((x1, y1), (x1c, y1c))
        origpist = origlen / 2.0
        clippist = origpist - clipoff
        clippistpt = (cliplenpts * clippist) / cliplen
        return (int(clippistpt), clip)
    def atan(self, dy, dx):
        result = cv.FastArctan(dy, dx)
        if result >= 180.0:
            result -= 180.0
        if result >= 90.0:
            result -= 180.0
        return result
    def push(self, image):
        crd = self.coords(image)
        if crd is None:
            self.pos += step
            return True
        pistpt, line = crd
        if line[pistpt] > 0: return False
        left, right = 0, 0
        for x in xrange(pistpt - 1, -1, -1):
            if line[x] > 0:
                left = pistpt - x
                break
        for x in xrange(pistpt + 1, len(line), 1):
            if line[x] > 0:
                right = x - pistpt
                break
        if left == 0 and right == 0:
            self.pos += self.step
            return True
        if left != 0 and right != 0:
            return False
        if self.alpha > 0.0:
            alpha = self.ralpha
            if left != 0:
                dx = left * cos(alpha)
                dy = left * sin(alpha) + self.step
                newAlpha = self.atan(dy, dx)
            else: # right != 0
                dx = right * cos(alpha)
                dy = right * sin(alpha) - self.step
                newAlpha = self.atan(dy, dx)
        elif self.alpha < 0.0:
            alpha = -self.ralpha
            if left != 0:
                dx = left * cos(alpha)
                dy = left * sin(alpha) - self.step
                newAlpha = -self.atan(dy, dx)
            else: # right != 0
                dx = right * cos(alpha)
                dy = right * sin(alpha) + self.step
                newAlpha = -self.atan(dy, dx)
        else: # self.alpha == 0.0
            if left != 0:
                newAlpha = asin(self.step / left)
            else: # right != 0
                newAlpha = -asin(self.step / right)
        self.setAlpha(newAlpha)
        self.pos += self.step
        return True
    def approximate(self, image):
        resized = cap.doResize(image, 2, cv.CV_INTER_NN)
        self.__init__(cv.GetSize(resized))
        for x in xrange(self.steps):
            if not self.push(resized): break
        forLog = cv.CreateImage(cv.GetSize(resized), cv.IPL_DEPTH_8U, 3)
        cv.CvtColor(resized, forLog, cv.CV_GRAY2BGR)
        self.draw(forLog)
        return self.alpha, forLog
    def draw(self, image):
        (x1, y1), (x2, y2) = self.endPoints()
        try: clipped = cv.ClipLine((self.w, self.h), (int(x1), int(y1)), (int(x2), int(y2)))
        except:
            print self.alpha, self.pos
            raise
        if clipped is None:
            return
        pt1, pt2 = clipped
        cv.Line(image, pt1, pt2, (0, 0, 192), 2, cv.CV_AA)

def split(image):
    ch1 = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    ch2 = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    ch3 = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    ch4 = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    cv.CmpS(image, mygray, ch1, cv.CV_CMP_EQ)
    cv.CmpS(image, myblue, ch2, cv.CV_CMP_EQ)
    cv.CmpS(image, mylgrn, ch3, cv.CV_CMP_EQ)
    cv.CmpS(image, mydgrn, ch4, cv.CV_CMP_EQ)
    return (ch1, ch2, ch3, ch4)

def filtCCs(components, (minW, minH), minRectArea, minDensity):
    sizefilter = lambda comp: comp[2][2] >= minW and comp[2][3] >= minH
    def areafilter(comp):
        w, h = cap.minAreaRectImage(comp[3], returnPoints=False)[1]
        return w * h >= minRectArea
    densityfilter = lambda comp: comp[0] / (comp[2][2] * comp[2][3]) >= minDensity
    myfilter = lambda comp: sizefilter(comp) and areafilter(comp) and densityfilter(comp)
    components = filter(myfilter, components)
    return components

def segmentChannel(ch, log=None):
    clone = cv.CloneImage(ch)
    components = cap.findCCs(ch, erasecol=0)
    joiner = lambda rect1, rect2: (cap.rectsIntersectH(rect1, rect2) and cap.distV(rect1, rect2) <= 6) or \
                                  (rect1[2] <= 10 and rect2[2] <= 10 and cap.distH(rect1, rect2) <= 6) or \
                                  ((rect1[2] <= 6 or rect2[2] <= 6)  and cap.distH(rect1, rect2) <= 6)
    components = cap.joinCCs(components, joiner)
    components = filtCCs(components, (15, 15), 200, 0.2)
    if log is not None:
        log.log(cap.drawComponents(clone, components))
    return components

def reorder(components):
    return sorted(chain(*components), key=lambda comp: comp[2][0])

def addBackground(comp, image, bgcolor=96):
    seg = comp[3]
    rect = comp[2]
    original = cap.getSubImage(image, rect)
    for x in xrange(original.width):
        for y in xrange(original.height):
            if original[y, x] != 255 and seg[y, x] != 255:
                seg[y, x] = bgcolor
    return comp

def findComponents(image, log=None):
    channels = split(image)
    components = map(lambda ch: segmentChannel(ch, log), channels)
    components = reorder(components)
    return components

def findAngle(comp, log):
    seg = comp[3]
    pist = piston(cv.GetSize(seg))
    angle, forLog = pist.approximate(seg)
    #log.log(forLog)
    return angle

def removeBadBackground(seg):
    threshUp   = cv.CreateImage(cv.GetSize(seg), cv.IPL_DEPTH_8U, 1)
    comparison = cv.CreateImage(cv.GetSize(seg), cv.IPL_DEPTH_8U, 1)
    visitMask  = cv.CreateImage(cv.GetSize(seg), cv.IPL_DEPTH_8U, 1)
    ffMask     = cv.CreateImage((seg.width + 2, seg.height + 2), cv.IPL_DEPTH_8U, 1)
    cv.Threshold(seg, threshUp, 1, 255, cv.CV_THRESH_BINARY)
    cv.Zero(visitMask)
    cv.Zero(ffMask)
    for x in xrange(seg.width):
        for y in xrange(seg.height):
            if seg[y, x] != 96 or visitMask[y, x] == 255: continue
            comp = cv.FloodFill(threshUp, (x, y), 0, 0, 0, 4 + cv.CV_FLOODFILL_MASK_ONLY + (255 << 8), ffMask)
            rect = comp[2]
            cv.SetImageROI(ffMask, cap.shiftRect(rect, 1, 1))
            cv.OrS(ffMask, 1, ffMask)
            cv.SetImageROI(seg, rect)
            cv.SetImageROI(comparison, rect)
            cv.Cmp(seg, ffMask, comparison, cv.CV_CMP_EQ) # 'comparison' does not need to be zeroed later
            intersect = cv.CountNonZero(comparison)
            cv.SetImageROI(visitMask, rect)
            cv.Or(visitMask, ffMask, visitMask)
            cv.ResetImageROI(visitMask)
            if intersect == 0:
                cv.Set(seg, 0, ffMask)
            cv.Zero(ffMask)
            cv.ResetImageROI(seg)
            cv.ResetImageROI(ffMask)
    return seg


def segment(image, addr, extras):
    log = cap.logger(extras, image)
    components = findComponents(image, log)
    log.log(cap.drawComponents(image, components))
    angles = map(lambda comp: findAngle(comp, log), components)
    angles = filter(lambda angle: angle != 0.0 and abs(angle) <= 27.0, angles)
    if len(angles) != 0:
        angle = fsum(angles) / len(angles)
        image = cap.doRotate(image, -angle, fillval=255, interpolation=cv.CV_INTER_NN)
        log.log(image)
        components = findComponents(image)
    assert(len(components) <= nSegs)
    log.log(cap.drawComponents(image, components))
    #components = cap.spltCCs(components, cap.partsFromnSegs5(components), projRadius=5, thresh=2)
    #components = filtCCs(components, (15, 15), 200, 0.2)
    components = map(lambda comp: addBackground(comp, image, bgcolor=96), components)
    segments = map(lambda comp: comp[3], components)
    segments = map(removeBadBackground, segments)
    log.log(cap.joinImagesH(segments))
    segments = map(lambda seg: cap.smoothNoise1(seg, bgcolor=0), segments)
    log.log(cap.joinImagesH(segments))
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_SEGMENT)
    return segments