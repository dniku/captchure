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

from numpy import vectorize

identity = lambda x: x
def wrap(key):
    return identity if key is None else key

def find(lst, val, key=None):
    key = wrap(key)
    for i in xrange(len(lst)):
        if key(lst[i]) == val:
            return i
    return None
    
def index(lst, key=None):
    key = wrap(key)
    for i in xrange(len(lst)):
        if key(lst[i]):
            return i
    return None
    
def argmin(lst, key=None):
    key = wrap(key)
    mi = 0
    m = key(lst[0])
    for i in xrange(1, len(lst)):
        val = key(lst[i])
        if val < m:
            m = val
            mi = i
    return mi
    
def argmax(lst, key=None):
    key = wrap(key)
    mi = 0
    m = key(lst[0])
    for i in xrange(1, len(lst)):
        val = key(lst[i])
        if val > m:
            m = val
            mi = i
    return mi

def amap(func, array):
    vfunc = vectorize(func)
    return vfunc(array)