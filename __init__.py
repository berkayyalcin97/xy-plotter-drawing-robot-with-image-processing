'''
Raster/DXF Image to G code Converter Package
Author: Andrew Ilersich
Last modified: August 19, 2015
'''

__author__ = 'Andrew Ilersich'
__email__ = 'andrew.ilersich@mail.utoronto.ca'
__version__ = '0.0.0'
__all__ = ['gOut', 'gRead', 'config']

# Import user-intended package functions
from gRead import imToPaths
from gOut import toTextFile, toSerial
from config import IMDIM, SMOOTHERR