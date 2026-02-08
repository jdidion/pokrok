"""Build pokrok.
"""
import sys

from setuptools import setup, find_packages
import versioneer


if sys.version_info < (3, 4):
    sys.stdout.write("At least Python 3.4 is required.\n")
    sys.exit(1)


setup(
    name='pokrok',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='John Didion',
    author_email='johndidion@gmail.com',
    url='https://github.com/jdidion/pokrok',
    description='Simple API for progress bars using any of several supported libraries',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'importlib-metadata; python_version<"3.8"',
        'importlib-resources; python_version<"3.7"',
    ],
    tests_require=['pytest'],  # , 'jinja2', 'pysam'],
    entry_points={
        'pokrok': [
            'tqdm=pokrok.plugins.tqdm:TqdmProgressMeterFactory',
            'progressbar2=pokrok.plugins.progressbar2:Progressbar2ProgressMeterFactory',
            'halo=pokrok.plugins.halo:HaloProgressMeterFactory',
            'logging=pokrok.plugins.logging:LoggingProgressMeterFactory',
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ]
)
