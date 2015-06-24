# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='clif',
    version='0.2.0',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    url = 'http://github.com/fmenabe/python-clif',
    download_url = 'http://github.com/fmenabe/python-clif',
    license='MIT License',
    description='Framework for generating command-line',
    long_description=open('README.rst').read(),
    keywords=['command-line', 'argparse', 'wrapper', 'clg', 'framework'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
    packages=['clif'],
    install_requires=['clg', 'pyyaml', 'yamlordereddictloader'])
