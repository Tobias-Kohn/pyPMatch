#
# (c) 2018, Tobias Kohn
#
# Created: 28.08.2018
# Updated: 28.08.2018
#
# License: Apache 2.0
#
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'PyMa',
    version = '0.1.0',
    author = 'Tobias Kohn',
    author_email = 'kohnt@tobiaskohn.ch',
    description = 'Pattern Matching in Python',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/Tobias-Kohn/PyMa',
    packages = setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    )
)
