import setuptools
from pathlib import Path

# Read README file
readme_path = Path(__file__).parent / "README.md"
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='iseries',
    version='1.2.0',
    author="Jean-Paul Mieville",
    author_email="jpmieville@gmail.com",
    description="A modern Python library for ODBC connections to iSeries (AS/400) IBM servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jpmieville/iseries",
    project_urls={
        "Bug Reports": "https://github.com/jpmieville/iseries/issues",
        "Source": "https://github.com/jpmieville/iseries",
    },
    packages=setuptools.find_packages(),
    install_requires=[
        "pyodbc>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
            "mypy",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="iseries as400 ibm odbc database",
)
