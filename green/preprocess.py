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
from math import tan, pi, radians as rad
from numpy import linspace

class approximator:
    def __init__(self, (w, h), alpha = None):
        self.w = w
        self.h = h
        if alpha is not None:
            self.setAlpha(alpha)
    def endPointsH(self, off):
        pt1 = (0,          self.pos1 + self.step * off)
        pt2 = (self.w - 1, self.pos2 + self.step * off)
        return (pt1, pt2)
    def endPointsV(self, off):
        pt1 = (self.pos1 + self.step * off, 0)
        pt2 = (self.pos2 + self.step * off, self.h - 1)
        return (pt1, pt2)
    def coords(self, off):
        (pt1x, pt1y), (pt2x, pt2y) = self.endPoints(off)
        try:
            return cv.ClipLine((self.w, self.h), (int(pt1x), int(pt1y)), (int(pt2x), int(pt2y)))
        except:
            print off, self.alpha
            raise
    def setAlpha(self, alpha):
        alpha = alpha % 360
        self.alpha = alpha
        if alpha < 45.0: # 1
            self.pos1 = self.h - 1 + self.w * tan(rad(alpha))
            self.pos2 = self.h - 1
            self.step = -1
            self.endPoints = self.endPointsH
            self.span = self.h
            return
        if 45.0 <= alpha < 90.0: # 2
            self.pos1 = self.w - 1 + self.h / tan(rad(alpha))
            self.pos2 = self.w - 1
            self.step = -1
            self.endPoints = self.endPointsV
            self.span = self.w
            return
        if 90.0 <= alpha < 135.0: # 3
            self.pos1 = self.w - 1
            self.pos2 = self.w - 1 - self.h / tan(rad(alpha))
            self.step = -1
            self.endPoints = self.endPointsV
            self.span = self.w
            return
        if 135.0 <= alpha < 180.0: # 4
            self.pos1 = self.w * tan(rad(alpha)) # this is correct since tan(pi - x) = -tan x
            self.pos2 = 0
            self.step = 1
            self.endPoints = self.endPointsH
            self.span = self.h
            return
        if 180.0 <= alpha < 225.0: # 5
            self.pos1 = 0
            self.pos2 = -self.w * tan(rad(alpha))
            self.step = 1
            self.endPoints = self.endPointsH
            self.span = self.h
            return
        if 225.0 <= alpha < 270.0: # 6
            self.pos1 = 0
            self.pos2 = -self.h / tan(rad(alpha))
            self.step = 1
            self.endPoints = self.endPointsV
            self.span = self.w
            return
        if 270.0 <= alpha < 315.0: # 7
            self.pos1 = self.h / tan(rad(alpha)) # this is correct since tan(x - 3/2 * pi) = -cot x
            self.pos2 = 0
            self.step = 1
            self.endPoints = self.endPointsV
            self.span = self.w
            return
        if 315.0 <= alpha: # 8
            self.pos1 = self.h - 1
            self.pos2 = self.h - 1 - self.w * tan(rad(alpha))
            self.step = -1
            self.endPoints = self.endPointsH
            self.span = self.h
            return
        raise ValueError("Weird Python behavior at angle: " + str(alpha))
    def testAt(self, image, off):
        crd = self.coords(off)
        if crd is None:
            return 0
        iter = cv.InitLineIterator(image, *crd)
        return sum(iter)
    def setCollisionPoint(self, image):
        for off in xrange(self.span):
            tst = self.testAt(image, off)
            if tst != 0:
                self.collisionPoint = off
                return tst
        return 0
    def rate(self, image):
        n = 8
        tests = [self.setCollisionPoint(image)]
        for y in xrange(self.collisionPoint + 1, self.collisionPoint + n):
            tests.append(self.testAt(image, y))
        self.rating = sum(tests)
        return self.rating
    def rateAt(self, image, alpha):
        self.setAlpha(alpha)
        return self.rate(image)
    def approximate(self, image, alpha, range):
        angles = linspace(alpha - range, alpha + range, range + 1 + range)
        ratings = cap.amap(lambda alpha: self.rateAt(image, alpha), angles)
        return angles[ratings.argmax()]
    def draw(self, image):
        a, b = self.coords(self.collisionPoint)
        cv.Line(image, a, b, (0, 0, 192), 3, cv.CV_AA)

def rotAngle(image):
    dark = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    cv.Erode(image, dark, None, 2)
    cv.Threshold(dark, dark, 224, 255, cv.CV_THRESH_BINARY_INV)
    appr = approximator(cv.GetSize(dark))
    alpha = appr.approximate(dark, 180.0, 10.0)
    appr.setAlpha(alpha)
    appr.setCollisionPoint(dark)
    forLog = cv.CreateImage(cv.GetSize(dark), cv.IPL_DEPTH_8U, 3)
    cv.CvtColor(dark, forLog, cv.CV_GRAY2BGR)
    appr.draw(forLog)
    return alpha + 180.0, forLog

def clearNoise(image, tLetter=64, rBright=30):
    if tLetter <= 0:
        raise ValueError("tLetter = " + str(tLetter))
    if rBright <= 0:
        raise ValueError("rBright = " + str(rBright))
    def doThis():
        result = cv.CloneImage(image)
        for x in xrange(result.width):
            for y in xrange(result.height):
                if result[y, x] == 0:
                    continue
                if result[y, x] < tLetter:
                    cv.FloodFill(result, (x, y), 0, rBright, rBright, 8, None)
                    if result[0, 0] != image[0, 0] or \
                       result[result.height - 1, 0] != image[image.height - 1, 0] or \
                       result[0, result.width - 1] != image[0, image.width - 1] or \
                       result[result.height - 1, result.width - 1] != image[image.height - 1, image.width - 1]:
                        return None
        return result
    result = doThis()
    while result is None:
        rBright -= 1
        result = doThis()
    cv.Threshold(result, result, 1, 255, cv.CV_THRESH_BINARY_INV)
    return result


def preprocess(image, addr, extras):
    log = cap.logger(extras, image)
    alpha, dark = rotAngle(image)
    log.log(dark, False)
    clear = clearNoise(image)
    log.log(clear, False)
    straight = cap.doRotate(clear, -alpha, fillval=0, resize=False, interpolation=cv.CV_INTER_NN)
    #cv.Threshold(straight, straight, 128, 255, cv.CV_THRESH_BINARY)
    log.log(straight)
    cv.Dilate(straight, straight)
    cv.Erode(straight, straight)
    log.log(straight)
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_PREPROCESS)
    return straight