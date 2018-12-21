""" Compatibility functions for Python 3 """
import codecs
from sys import version_info

IS_PYTHON_3 = version_info.major == 3

def num_range(start, end):
    """ Generate numeric range """

    if IS_PYTHON_3:
        return range(start, end)
    else:
        return xrange(start, end)

def file_readlines(file_obj):
    """ Return iterator over file lines """

    if IS_PYTHON_3:
        return file_obj.readlines()
    else:
        return file_obj.xreadlines()

def gen_next(gen_obj):
    """ Return next value of generator """

    if IS_PYTHON_3:
        return next(gen_obj)
    else:
        return gen_obj.next()

def open_utf8(filename):
    """ Open file for reading """

    return codecs.open(filename, 'r', 'utf-8')