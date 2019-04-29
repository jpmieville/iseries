import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='iseries',
    version='1.0',
    author="Jean-Paul Mieville",
    author_email="jpmieville@gmail.com",
    description="An library to help to make an ODBC connection with an iSeries or i5 IBM server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jpmieville/iseries.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
