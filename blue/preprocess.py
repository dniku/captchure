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

def doSplit(image):
    b = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    g = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    r = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.Split(image, b, g, r, None)
    return b, g, r

def createMask(image, thresh):
    b, g, r = doSplit(image)
    cv.Threshold(b, b, thresh, 255, cv.CV_THRESH_BINARY)
    cv.Threshold(g, g, thresh, 255, cv.CV_THRESH_BINARY)
    cv.Threshold(r, r, thresh, 255, cv.CV_THRESH_BINARY)
    cv.And(b, g, b, None)
    cv.And(b, r, b, None)
    return b

def cutLetters(image, thresh, log):
    mask = createMask(image, thresh)
    log.log(mask)
    h = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.CvtColor(image, image, cv.CV_BGR2HSV)
    cv.Split(image, h, None, None, None)
    log.log(h)
    cv.Set(h, cv.ScalarAll(255), mask)
    return h
    

def preprocess(image, addr, extras):
    log = cap.logger(extras, image)
    image = cutLetters(image, 116, log)
    log.log(image)
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_PREPROCESS)
    return image