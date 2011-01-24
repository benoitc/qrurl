# -*- coding: utf-8 -
#
# This file is part of friendpaste released under Apache License, Version 2.0. 
# See the NOTICE for more information.

import string


BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE62_VALUES = ''.join([chr(i) for i in range(62)])

E_BASE62_PRIMITIVES = dict([(BASE62_CHARS[i], i) for i in range(62)])
D_BASE62_PRIMITIVES = string.maketrans(BASE62_VALUES, BASE62_CHARS)

def b62encode(value):
    """ encode int/long to base62 stsring.
    
    >>> b62encode(1123458)
    '4iGI'
    """
    number = value
    result = ''
    while number != 0:
        result = D_BASE62_PRIMITIVES[number % 62] + result
        number /= 62
    return result

def b62decode(value):
    """ decode string to int/long
    
    >>> b62decode('4iGI')
    1123458
    """
    value = str(value)
    i = 0
    i_out = 0
    for c in value[::-1]:
        place = 62 ** i
        i_out += int(E_BASE62_PRIMITIVES[c]) * place
        i += 1
    return i_out


if __name__ == '__main__':
    import doctest
    doctest.testmod()
