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
from lconsts import segW, segH, nSegs

def segment(image, addr, extras):
    clone = cv.CloneImage(image)
    log = cap.logger(extras, image)
    components = cap.findCCs(image, erasecol=0, doContinue=None, doSkip=lambda comp: comp[0] <= 25)
    log.log(cap.drawComponents(clone, components))
    if len(components) != nSegs:
        components = cap.joinCCs(components, cap.rectsIntersectH)
        log.log(cap.drawComponents(clone, components))
    cap.processExtras(log.steps, addr, extras, cap.CAP_STAGE_SEGMENT)
    assert(len(components) == nSegs)
    segments = map(lambda comp: comp[3], components)
    return segments