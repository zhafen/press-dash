import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="press_dashboard_library",
    version="0.1",
    author="Zach Hafen-Saavedra",
    author_email="zachary.h.hafen@gmail.com",
    description="CIERA press dashboard.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/zhafen/trove",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)