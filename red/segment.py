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
from operator import attrgetter
from lconsts import nSegs

    
def segment(image, addr, extras):
    log = cap.logger(extras, image)
    clone = cv.CloneImage(image)
    components = cap.findCCs(image, 0, lambda col: col <= 128, lambda comp: comp[0] < 10)
    log.log(cap.drawComponents(clone, components), False)
    components = cap.joinCCs(components, cap.rectsIntersectH)
    log.log(cap.drawComponents(clone, components), False)
    assert(len(components) <= nSegs)
    parts = cap.partsFromnSegs5(components)
    components = cap.spltCCs(components, parts, projRadius=4, thresh=1)
    log.log(cap.drawComponents(clone, components), False)
    segments = map(lambda comp: comp[3], components)
    log.log(cap.joinImagesH(segments), False)
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_SEGMENT)
    return segments