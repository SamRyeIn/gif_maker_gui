"""
py2app setup script for FFGIF Maker

To build:
    source venv/bin/activate
    python setup.py py2app

The app will be created in the 'dist' folder.
"""

from setuptools import setup

APP = ['gif_maker.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'FFGIF Maker.icns',
    'plist': {
        'CFBundleName': 'FFGIF Maker',
        'CFBundleDisplayName': 'FFGIF Maker',
        'CFBundleIdentifier': 'com.ffgifmaker.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
    },
    'packages': [],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
