import os.path
from setuptools import setup, find_packages
import sys

install_requires = ["httplib2"]

if sys.version_info < (2, 6):
    install_requires.append("simplejson")

base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "nap",
    version = "0.4.5",
    description = "A fork of slumber, a library that makes consuming a REST API easier and more convenient",
    long_description="\n\n".join([
        open(os.path.join(base_dir, "README.rst"), "r").read(),
    ]),
    url = "http://github.com/ecooper/nap",
    author = "E. Cooper",
    author_email = "ecooper@getfoodgenius.com",
    packages = find_packages(),
    zip_safe = False,
    install_requires = install_requires,
)
