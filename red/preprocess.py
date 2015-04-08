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
from math import cos, pi
from lconsts import factor, rimgW, rimgH

mapX = cv.CreateImage((rimgW, rimgH), cv.IPL_DEPTH_32F, 1)
for y in xrange(mapX.height):
    for x in xrange(mapX.width):
        mapX[y, x] = x

t = 4.0 # top offset
scale1 = 2.3
step1 = 27.0
h = 16.0 # character height
stretch = rimgW * 10.0

ft = t * factor
fscale1 = scale1 * factor
fh = h * factor
fstep1 = pi / (step1 * factor)

mapY = cv.CreateImage((rimgW, rimgH), cv.IPL_DEPTH_32F, 1)
for y in xrange(mapY.height):
    for x in xrange(mapY.width):
        q = fscale1 * (1 + cos(fstep1 * x))
        mapY[y, x] = ((y - ft) * ((fh - q) / fh) + q) * (1 + x / stretch) + ft

#cv.SaveImage("_mapy.png", mapY)
    
def undistort(image):
    result = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
    cv.Remap(image, result, mapX, mapY, cv.CV_INTER_CUBIC + cv.CV_WARP_FILL_OUTLIERS, cv.ScalarAll(0))
    return result

"""
test = cv.CreateImage((rimgW, rimgH), cv.IPL_DEPTH_8U, 1)
cv.Zero(test)
for y in (i for i in xrange(test.height) if i % 4 < 2):
    row = cv.GetRow(test, y)
    cv.Set(row, 255)
cv.SaveImage("_test_original.png", test)
cv.SaveImage("_test_modified.png", undistort(test))
#"""


def preprocess(image, addr, extras):
    log = cap.logger(extras, image)
    image = cap.doResize(image, factor, cv.CV_INTER_CUBIC)
    log.log(image)
    image = undistort(image)
    log.log(image)
    cv.Threshold(image, image, 200, 255, cv.CV_THRESH_BINARY)
    log.log(image)
    image = cap.repaintCCs(image, doRepaint=lambda comp, col: comp[0] <= 10 and col <= 128)
    log.log(image)
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_PREPROCESS)
    return image