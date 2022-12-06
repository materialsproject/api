#!/usr/bin/env python


from pathlib import Path

from setuptools import find_namespace_packages, setup

module_dir = Path(__file__).resolve().parent

with open(module_dir / "README.md") as f:
    long_desc = f.read()
setup(
    name="mp-api",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="API Server for the Materials Project",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/materialsproject/api",
    author="The Materials Project",
    author_email="feedback@materialsproject.org",
    license="modified BSD",
    packages=find_namespace_packages(include=["mp_api.*"]),
    zip_safe=False,
    install_requires=[
        "setuptools",
        "msgpack",
        "pymatgen>=2022.3.7",
        "typing-extensions>=3.7.4.1",
        "requests>=2.23.0",
        "monty>=2021.3.12",
        "emmet-core>=0.36.4",
    ],
    extras_require={
        "all": [
            "emmet-core[all]>=0.36.4",
            "custodian",
            "mpcontribs-client",
            "boto3"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    tests_require=["pytest"],
    python_requires=">=3.8",
)
