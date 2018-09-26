from os import path
from setuptools import setup, find_packages
import sys
import versioneer


# NOTE: This file must remain Python 2 compatible for the foreseeable future,
# to ensure that we error out properly for people with outdated setuptools
# and/or pip.
if sys.version_info < (3, 6):
    error = """
fs2dicom does not support Python {0}.{1}.
Python 3.6 and above is required. Check your Python version like so:

python3 --version

This may be due to an out-of-date pip. Make sure you have pip >= 9.0.1.
Upgrade pip like so:

pip install --upgrade pip
""".format(sys.version_info.major, sys.version_info.minor)
    sys.exit(error)

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open(path.join(here, 'requirements.txt')) as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [line for line in requirements_file.read().splitlines()
                    if not line.startswith('#')]


setup(
    name='fs2dicom',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Create DICOM Segmentation Image and Structured Report objects from FreeSurfer segmentations",
    long_description=readme,
    author="CorticoMetrics",
    author_email='ltirrell@corticometrics.com',
    url='https://github.com/corticometrics/fs2dicom',
    packages=find_packages(exclude=['docs', 'tests']),
    entry_points='''
        [console_scripts]
        fs2dicom=fs2dicom.fs2dicom:cli
    ''',
    include_package_data=True,
    package_dir={'fs2dicom': 'fs2dicom'},
    package_data={
        'fs2dicom': [
            'templates/*.json'
            # When adding files here, remember to update MANIFEST.in as well,
            # or else they will not be included in the distribution on PyPI!
            # 'path/to/data_file',
            ]
        },
    install_requires=requirements,
    license="BSD (3-clause)",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
