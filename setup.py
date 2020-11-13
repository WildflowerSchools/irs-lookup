import os
from setuptools import setup, find_packages

BASEDIR = os.path.dirname(os.path.abspath(__file__))
VERSION = open(os.path.join(BASEDIR, 'VERSION')).read().strip()

# Dependencies (format is 'PYPI_PACKAGE_NAME[>=]=VERSION_NUMBER')
BASE_DEPENDENCIES = [
    'beautifulsoup4',
    'cachetools>=4.1.1',
    'click>=7.1.1',
    'click-log>=0.3.2',
    'dateparser',
    'boto3>=1.6.13',
    'google-cloud-vision',
    'pandas>=0.25.3',
    'pdf2image',
    'Pillow',
    'python-dotenv>=0.14.0',
    #'pytesseract',
    'requests'
]
# TEST_DEPENDENCIES = [
# ]
#
DEVELOPMENT_DEPENDENCIES = [
    'autopep8>=1.5.2'
]

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(BASEDIR))

setup(
    name='irs-lookup',
    packages=find_packages(),
    version=VERSION,
    include_package_data=True,
    description='Tool to fetch irs 990 data',
    long_description=open('README.md').read(),
    url='https://github.com/WildflowerSchools/irs-lookup',
    author='Benjamin Jaffe-Talberg',
    author_email='ben.talberg@wildflowerschools.org',
    install_requires=BASE_DEPENDENCIES,
    # tests_require=TEST_DEPENDENCIES,
    extras_require={
        'development': DEVELOPMENT_DEPENDENCIES
    },
    entry_points={
        "console_scripts": [
            "irs_lookup = irs_lookup.cli:cli"
        ]
    },
    # keywords=['KEYWORD'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
