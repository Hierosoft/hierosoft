#!/usr/bin/env python
import setuptools
import sys
import os

# versionedModule = {}
# versionedModule['urllib'] = 'urllib'
# if sys.version_info.major < 3:
#     versionedModule['urllib'] = 'urllib2'

install_requires = []

if os.path.isfile("requirements.txt"):
    with open("requirements.txt", "r") as ins:
        for rawL in ins:
            line = rawL.strip()
            if len(line) < 1:
                continue
            install_requires.append(line)

description = (
    "This is the splash screen which ensures Python and any other"
    " requirements are installed then updates and runs the launcher."
    " From a user perspective, \"Hierosoft\" (hierosoftupdate)"
    " is the shortcut for the launcher. From a developer perspective,"
    " hierosoft is the module that updates and installs"
    " the launcher and then the launcher uses it to install and"
    " update any other programs."
)
long_description = description
if os.path.isfile("readme.md"):
    with open("readme.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='hierosoft-update',
    version='0.5.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        ('License :: OSI Approved :: MIT License'), # See also: license=
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows'
        'Operating System :: MacOS :: MacOS X'
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Logging',
        'Topic :: System :: Software Distribution',
        'Topic :: Text Processing :: General',
    ],
    keywords=('python system management IT tools linux installation'
              ' package selection preloading preinstall'),
    url="https://github.com/Hierosoft/hierosoft",
    author="Jake Gustafson",
    author_email='7557867+poikilos@users.noreply.github.com',
    license='MIT License',  # See also: license classifier above.
    # packages=setuptools.find_packages(),
    packages=['hierosoft'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'],
    # ^ Don't use scripts anymore (according to
    #   <https://packaging.python.org/en/latest/guides
    #   /distributing-packages-using-setuptools
    #   /?highlight=scripts#scripts>).
    # See <https://stackoverflow.com/questions/27784271/
    # how-can-i-use-setuptools-to-generate-a-console-scripts-entry-
    # point-which-calls>
    entry_points={
        'console_scripts': [
            'hierosoft=hierosoft.gui_tk:main',
            'ggrep=hierosoft.ggrep:main',
            'checkpath=hierosoft.checkpath:main',
            'checkversion=hierosoft.checkversion:main',
        ],
    },
    install_requires=install_requires,
    #     versionedModule['urllib'],
    # ^ "ERROR: Could not find a version that satisfies the requirement
    #   urllib (from nopackage) (from versions: none)
    #   ERROR: No matching distribution found for urllib"
    test_suite='nose.collector',
    tests_require=['nose', 'nose-cover3'],
    zip_safe=False,  # It can't run zipped due to needing data files.
)
