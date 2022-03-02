# coding: utf-8

from setuptools import setup

setup(
    name='clg-splitup',
    version='1.0.0',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    url = 'http://github.com/fmenabe/python-clg-splitup',
    download_url = 'http://github.com/fmenabe/python-clg-splitup',
    license='MIT License',
    description='Split and organize `clg` CLI programs.',
    long_description=open('README.rst').read(),
    keywords=['command-line', 'argparse', 'wrapper', 'clg', 'framework'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
    py_modules=['clg/splitup'],
    install_requires=['clg', 'pyyaml', 'yamlloader', 'argcomplete'])
