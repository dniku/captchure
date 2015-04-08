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

    tooWide = filter(lambda index: components[index].width > rsegWMax, range(len(components)))
    while len(tooWide) > 1:
        index = tooWide[0]
        image = components[index]
        parts = image.width / rsegWMax + 1
        result = splitIntoNParts(image, parts)
        components[index:index+1] = result
        del(tooWide[0])
        tooWide = map(lambda index: index + parts - 1, tooWide)
    if len(tooWide) == 1:
        if len(components) != nSegs:
            widestIndex = tooWide[0]
            image = components[widestIndex]
            parts = nSegs - len(components) + 1
            result = splitIntoNParts(image, parts)
            components[widestIndex:widestIndex+1] = result

def saveImagePlot(image, title, peaks):
    anglesLo = np.arange(-30,  30, 0.5) # 0
    anglesR  = np.arange( 60, 120, 0.5) # 90
    anglesUp = np.arange(150, 210, 0.5) # 180
    anglesL  = np.arange(240, 300, 0.5) # 270
    
    appr = approximator(cv.GetSize(image))
    ratingsUp = appr.rateAll(image, anglesUp)
    ratingsLo = appr.rateAll(image, anglesLo)
    ratingsL  = appr.rateAll(image, anglesL)
    ratingsR  = appr.rateAll(image, anglesR)
    
    plt.plot(anglesLo, ratingsUp, 'b-')
    plt.plot(anglesLo, ratingsLo, 'r-')
    plt.plot(anglesLo, ratingsL,  'g-')
    plt.plot(anglesLo, ratingsR,  'y-')
    
    colors = ('b', 'r', 'g', 'y')
    offsets = (180.0, 0.0, 270.0, 90.0)
    for i in range(4):
        if peaks[i] is not None:
            plt.axvline(peaks[i] - offsets[i], color=colors[i])
    
    plt.title(title)
    plt.xlabel("Line angle")
    plt.ylabel("Line rating")
    plt.savefig(os.path.join(plot_dir, title + ".png"))
    #plt.show()
    plt.clf()

def rotatedProjectionWidth(image, alpha, projectionAngle):
    appr = approximator(cv.GetSize(image), -alpha + projectionAngle)
    appr.setCollisionPoint(image)
    pt1 = appr.pos1
    off1 = appr.collisionPoint
    appr.setAlpha(-alpha + projectionAngle + 180.0)
    appr.setCollisionPoint(image)
    pt2 = appr.pos1
    off2 = appr.collisionPoint
    h = abs(pt2 - pt1) - (off1 + off2)
    return h * cos(rad(alpha))

def saveProjectionPlot(image, original, title):
    plt.figure(num=1, figsize=(9, 9))
    plt.subplot(311)
    angles = np.arange(-30, 30, 0.5)
    distances = map(lambda angle: rotatedProjectionWidth(image, angle, 90.0), angles)
    plt.plot(angles, distances)
    plt.title(title)
    plt.xlabel("Angle")
    plt.ylabel("Projection width")
    plt.subplot(312)
    plotCvImage(original)
    plt.subplot(313)
    plotCvImage(image)
    #plt.savefig(os.path.join(plot_dir, title + ".png"))
    plt.show()
    plt.clf()

def clearDots1C(image, size):
    for x in xrange(image.width):
        for y in xrange(image.height):
            col = image[y, x]
            if col > 0 and col != 254:
                comp = cv.FloodFill(image, (x, y), 254, 0, 0, 4, None)
                if comp[0] <= size:
                    cv.FloodFill(image, (x, y), 0, 0, 0, 4, None)

b, g, r = doSplit(image)
    for ch in (b, g, r):
        cv.Threshold(ch, ch, 200, 255, cv.CV_THRESH_BINARY_INV)
        clearDots(ch, size)
        cv.Threshold(ch, ch, 128, 255, cv.CV_THRESH_BINARY_INV)
    mask = copyHeader1C(image)
    cv.Or(b, g, mask, None)
    cv.Or(r, mask, mask, None)
    cv.Set(image, cv.ScalarAll(255), mask)



def copyHeader1C(image):
    return cv.CreateImage(cv.GetSize(image), image.depth, 1)

def doSplit(image):
    c1, c2, c3 = copyHeader1C(image), copyHeader1C(image), copyHeader1C(image)
    cv.Split(image, c1, c2, c3, None)
    return c1, c2, c3

def getBlackWhite(image):
    gs = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.CvtColor(image, gs, cv.CV_BGR2GRAY)
    bw = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.Threshold(gs, bw, 254, 255, cv.CV_THRESH_BINARY_INV)
    return bw

"""

def createMask(image):
    mask = cv.CreateImage((image.width + 2, image.height + 2), cv.IPL_DEPTH_8U, 1)
    cv.Zero(mask)
    return mask

"""

def segment(image, addr, extras):
    def splitIntoNParts(image, parts):
        splitters = np.linspace(0, image.width - 1, parts + 1)
        projection = prelude.projectDown(image)
        n = 4
        def adjust(splitter):
            if splitter == 0 or splitter == image.width - 1:
                return splitter
            neighborhood = projection[splitter - n : splitter + n + 1]
            return prelude.argmin(neighborhood) + splitter - n
        splitters = prelude.amap(adjust, splitters.astype(int))
        result = prelude.splitAt(image, splitters)
        return result
    components = findConnectedComponents(image)
    while len(components) < nSegs:
        index = prelude.argmax(components, attrgetter("width"))
        image = components[index]
        parts = image.width / rsegW + 1
        result = splitIntoNParts(image, parts)
        components[index:index+1] = result
    components = map(adjustSize, components)
    return components

def plotCvImage(image, interpolation='linear'):
    if image.nChannels == 1:
        image = Image.fromstring("L", cv.GetSize(image), image.tostring())
    elif image.nChannels == 3:
        image = Image.fromstring("RGB", cv.GetSize(image), image.tostring())
    plt.imshow(image.transpose(Image.FLIP_TOP_BOTTOM), cmap=plt.cm.gray, shape=image.size, interpolation=interpolation)

    while index < len(components):
        comp = components[index]
        seg = comp[3]
        rect = comp[2]
        if seg.width > maxW:
            parts = seg.width / maxW + 1
            segments, rects = splitIntoNParts(seg, parts, projRadius)
            rects = map(lambda rect1: shiftRect(rect1, rect[0], rect[1]), rects)
            mapper = lambda segIndex: (0.0, 255.0, \
                                       rects[segIndex], segments[segIndex])
            comp = map(mapper, xrange(parts))
            comp = map(lambda comp: cutNonBlack(comp, thresh), comp)
            comp = filter(lambda comp: comp is not None, comp)
            components[index: index + 1] = comp
            index += parts
        else: index += 1
    return components

"""
# RGB, divided by 51
gray   = ((3,3,3), (3,2,3), (3,2,2), (2,2,2))
blue   = ((1,1,3), (1,1,2), (0,1,2), (0,0,2))
lgreen = ((1,2,2), (1,3,2), (1,2,1), (0,2,1))
dgreen = ((1,1,1), (0,1,0), (0,0,0))
"""

"""

def splitChannels(image):
    ch1 = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    ch2 = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    ch3 = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    ch4 = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    ch5 = cv.CreateImage(cv.GetSize(image), image.depth, 1)
    cv.CmpS(image, mygray, ch1, cv.CV_CMP_EQ)
    cv.CmpS(image, myblue, ch2, cv.CV_CMP_EQ)
    cv.CmpS(image, mylgrn, ch3, cv.CV_CMP_EQ)
    cv.CmpS(image, mydgrn, ch4, cv.CV_CMP_EQ)
    cv.CmpS(image, myunkn, ch5, cv.CV_CMP_EQ)
    return ch1, ch2, ch3, ch4, ch5

"""

"""

def mergeChannels(channels):
    result = cv.CreateImage(cv.GetSize(channels[0]), cv.IPL_DEPTH_8U, 1)
    temp   = cv.CreateImage(cv.GetSize(channels[0]), cv.IPL_DEPTH_8U, 1)
    cv.Set(result, 255)
    for ch, col in zip(channels, mycolors):
        cv.Threshold(ch, temp, 128, 255, cv.CV_THRESH_BINARY_INV)
        cv.Set(result, col, temp)
    return result

"""

    #angles = map(getRotationAngle, components)
    #angles = filter(lambda angle: angle is not None, angles)
    #alpha = 0.0 if len(angles) == 0 else sum(angles) / len(angles)
    #if abs(alpha) > 0.1:
    #    segments = map(lambda seg: rotate(seg, -alpha, 0), segments)
    #    segments = map(lambda seg: getSubImage(seg, findNonBlackRect(seg)), segments)
    #    steps.append(joinImagesH(segments))

def findCol(image, left):
    if left:
        start, stop, step = 0, image.width, 1
    else:
        start, stop, step = image.width - 1, -1, -1
    for x in xrange(start, stop, step):
        col = cv.GetCol(image, x)
        if cv.CountNonZero(col) > 0:
            return x

def findRow(image, top):
    if top:
        start, stop, step = 0, image.height, 1
    else:
        start, stop, step = image.height - 1, -1, -1
    for y in xrange(start, stop, step):
        row = cv.GetRow(image, y)
        if cv.CountNonZero(row) > 0:
            return y

def findFirstLast(array):
    if array.width == 1:
        first = 0
        last = array.height - 1
        for y in xrange(array.height):
            if array[y, 0] == 255:
                first = y
                break
        for y in xrange(array.height - 1, -1, -1):
            if array[y, 0] == 255:
                last = y
                break
        return (first, last)
    elif array.height == 1:
        first = 0
        last = array.width - 1
        for x in xrange(array.width):
            if array[0, x] == 255:
                first = x
                break
        for x in xrange(array.width - 1, -1, -1):
            if array[0, x] == 255:
                last = x
                break
        return (first, last)

def getRotationAngle(comp):
    def mean(x, y):
        return (x + y) / 2
    image = comp[3]
    leftCol =  0
    rightCol = image.width - 1
    topRow = 0
    bottomRow = image.height - 1
    left = mean(*findFirstLast(cv.GetCol(image, leftCol)))
    right = mean(*findFirstLast(cv.GetCol(image, rightCol)))
    top = mean(*findFirstLast(cv.GetRow(image, topRow)))
    bottom = mean(*findFirstLast(cv.GetRow(image, bottomRow)))
    lP = (leftCol, left)
    rP = (rightCol, right)
    tP = (top, topRow)
    bP = (bottom, bottomRow)
    lowerP, upperP = (lP, rP) if lP[1] > rP[1] else (rP, lP)
    lowerPts = (bP, lowerP)
    upperPts = (tP, upperP)
    #cv.Line(image, bP, lowerP, 96)
    #cv.Line(image, tP, upperP, 160)
    bottomSlope = findLineSlope(bP, lowerP)
    topSlope    = findLineSlope(tP, upperP)
    #print bottomSlope, topSlope
    lim = 20.0
    def truncate(x):
        return x if -lim <= x <= lim else None
    topSlope = truncate(topSlope)
    bottomSlope = truncate(bottomSlope)
    if topSlope is None:
        return bottomSlope
    else:
        if bottomSlope is None:
            return topSlope
        else:
            return mean(topSlope, bottomSlope)

def merge(gray, blue, lgrn, dgrn):
    result = cv.CreateImage(cv.GetSize(gray), gray.depth, gray.nChannels)
    cv.Set(result, mygray, gray)
    cv.Set(result, myblue, blue)
    cv.Set(result, mylgrn, lgrn)
    cv.Set(result, mydgrn, dgrn)
    return result


    """ # this piece of code makes sure that the highest possible quality is achieved
    presult = result
    while result is not None:
        presult = result
        tLetter += 1
        result = doThis()
    result = presult
    while result is not None:
        presult = result
        rBright += 1
        result = doThis()
    result = presult
    """

def findConnectedComponents(image, size):
    mask = cv.CreateImage((image.width + 2, image.height + 2), cv.IPL_DEPTH_8U, 1)
    cv.Zero(mask)
    components = []
    data = []
    for x in range(image.width):
        for y in range(image.height):
            if image[y, x] <= 128:
                continue
            comp = cv.FloodFill(image, (x, y), 255, 0, 0, 8 + cv.CV_FLOODFILL_MASK_ONLY + (255 << 8), mask)
            if comp[0] <= size:
                continue
            seg = cv.GetSubRect(mask, shiftRect(comp[2], 1, 1))
            seg = prelude.matToImage(seg, cv.IPL_DEPTH_8U, 1)
            comp = list(comp)
            comp.append(seg)
            components.append(comp)
            cv.Zero(mask)
            cv.FloodFill(image, (x, y), 0, 0, 0, 8, None)
    return components

def removeNoise(image, log):
    noiseMask = getNoiseMask(image, 15, 4)
    whiteMask = findColor(image, white)
    unknMask = findColor(image, myunkn)
    mask1 = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 1)
    cv.Or(noiseMask, unknMask, mask1)
    log.log(mask1)
    cv.Or(mask1, whiteMask, mask1)
    image = doInpaint(image, mask1)
    log.log(image)
    cv.Set(image, 255, whiteMask)
    log.log(image)
    noiseMask = getNoiseMask(image, 15, 4)
    image = doInpaint(image, noiseMask)
    log.log(image)
    return image

"""
kerW, kerH = 19, 19
b = float(kerW * kerH) / 10.0
kerCX, kerCY = kerW // 2, kerH // 2
kerCX2 = kerCX // 2
kerCX14 = kerCX // 4
kerCX34 = kerCX * 3 // 4
kernel = cv.CreateMat(kerW, kerH, cv.CV_32FC1)
for x in xrange(kerW):
    for y in xrange(kerH):
        dist = sqrt((x - kerCX)**2 + (y - kerCY)**2)
        kernel[y, x] = (kerCX2 - abs(kerCX2 - dist)) / b if kerCX14 < dist < kerCX34 else 0.0
cv.Mul(kernel, kernel, kernel)
"""
"""
    result = cv.CreateImage(cv.GetSize(ch), cv.IPL_DEPTH_32F, 1)
    cv.Filter2D(ch, result, kernel)
    #cv.Mul(result, result, result)
    cv.SaveImage("channel.png", ch)
    cv.SaveImage("image.png", result)
    cv.NamedWindow("Filter", 1)
    cv.ShowImage("Filter", result)
    cv.WaitKey(0)
"""