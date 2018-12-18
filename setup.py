#!/usr/bin/env python
import os
import sys

from fluttercomic import __version__

try:
    from setuptools import setup, find_packages
    from setuptools.command.test import test as TestCommand

    class PyTest(TestCommand):
        def finalize_options(self):
            TestCommand.finalize_options(self)
            self.test_args = []
            self.test_suite = True

        def run_tests(self):
            # import here, because outside the eggs aren't loaded
            import pytest
            errno = pytest.main(self.test_args)
            sys.exit(errno)

except ImportError:

    from distutils.core import setup

    def PyTest(x):
        pass

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
long_description = f.read()
f.close()

setup(
    install_requires=('goperation>=1.0',
                      'goperation<1.1',
                      'simpleutil>=1.0',
                      'simpleutil<1.1',
                      'simpleservice>=1.0',
                      'simpleservice<1.0',
                      'lxml>=3.2.5',
                      'xmltodict>=0.10.1',
                      'ndg_httpsclient>=0.4.0'
                      ),
    name='fluttercomic',
    version=__version__,
    description='A flutter comic app web server',
    long_description=long_description,
    url='http://github.com/lolizeppelin/fluttercomic',
    author='Lolizeppelin',
    author_email='lolizeppelin@gmail.com',
    maintainer='Lolizeppelin',
    maintainer_email='lolizeppelin@gmail.com',
    keywords=['fluttercomic'],
    license='MIT',
    packages=find_packages(include=['fluttercomic*']),
    tests_require=['pytest>=1.9.0'],
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
)
