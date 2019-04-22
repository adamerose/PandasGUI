from setuptools import setup

from distutils.core import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name='pandasgui',
      version='0.0.4',
      description='GUI for Pandas DataFrames',
      author='Adam Rose',
      author_email='adamerose@hotmail.com',
      url='https://github.com/adamerose/pandasgui',
      packages=['pandasgui'],
      long_description=long_description,
      long_description_content_type='text/markdown',
      install_requires=[
          'pandas',
          'PyQt5',
          'multiprocess']
      )
