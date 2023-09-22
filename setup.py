#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [ 
	'manim',
]

test_requirements = [ ]

setup(
    author="Stas Fomin",
    author_email='fomin@ispras.ru',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Visualize Algorithms",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    name='pyalgovisualizer',
    packages=find_packages(include=['pyalgovisualizer', 'pyalgovisualizer.*']),
    version_config=True,
    setup_requires=['setuptools-git-versioning'],
    test_suite='tests',
    tests_require=test_requirements,
    zip_safe=False,
)
