#!/usr/bin/env python


from setuptools import setup, find_packages
from pathlib import Path

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
    packages=find_packages("src"),
    package_dir={"": "src"},
    zip_safe=False,
    install_requires=[
        "setuptools",
        "pydantic>=1.4",
        "pymatgen>=2020.1.10",
        "typing-extensions>=3.7.4.1",
        "requests>=2.23.0"
    ],
    extras_require={
        "server": [
            "fastapi>=0.46.0",
            "maggma==0.17.3",
            "uvicorn>=0.11.2",
            "gunicorn[gevent]>=20.0.1",
            "aws-xray-sdk>=2.4.2",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    tests_require=["pytest"],
    python_requires=">=3.7",
)
