import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="press_dash_lib",
    version="0.1",
    author="Zach Hafen-Saavedra",
    author_email="zachary.h.hafen@gmail.com",
    description="CIERA press dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CIERA-Northwestern/press-dashboard",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires = [
        'numpy',
        'pandas',
        'openpyxl',
        'matplotlib',
        'seaborn',
        'jupyterlab',
        'sympy',
        'nbconvert',
        'nbformat',
        'PyYAML',
        'streamlit',
        'pytest',
        'jupyter_contrib_nbextensions',
    ],
)
