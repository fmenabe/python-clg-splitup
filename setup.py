# coding: utf-8

from setuptools import setup

setup(
    name='clg-splitup',
    version='0.1.0',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    url = 'https://clg.readthedocs.org/en/latest/',
    download_url = 'http://github.com/fmenabe/python-clg-splitup',
    license='MIT License',
    description='Split up and organize elements of command-line programs based on python-clg.',
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities'
    ],
    py_modules=['clg/splitup'],
    install_requires=['clg', 'pyyaml', 'yamlordereddictloader'])
