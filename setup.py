#!/usr/bin/env python
# -*- coding: utf-8 -
#
# This file is part of qrurl released under the MIT license. 
# See the NOTICE for more information.

import os

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

from restkit import __version__

ext_modules = [Extension("qrurl.qrencode", ["qrurl/qrencode.pyx"],
    libraries=['qrencode'])]

package_data = {
        'qrurl': [
            'templates/*',
            'static/css/*'
        ]
}

setup(
    name ="qrurl",
    version = __version__,

    description = "QR URL redirect service.",

    long_description = file(
        os.path.join(
            os.path.dirname(__file__),
            'README.rst'
        )
    ).read(),

    author = "Benoit Chesneau",
    author_email = "benoitc@e-engura.org",
    url = "http://github.com/benoitc/qrurl",

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
    ],

    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,

    packages = ['qrurl'],
    package_data = package_data,

    scripts = ['bin/qrurl-consumer'],
)

