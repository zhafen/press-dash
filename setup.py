import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="press_dash_lib",
    version="0.1",
    author="CIERA (Zach Hafen-Saavedra)",
    author_email="ciera@northwestern.edu",
    description="Dashboard for exploring and presenting press data related to CIERA.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CIERA-Northwestern/press-dash",
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
        'sympy',
        'nbconvert',
        'nbformat',
        'PyYAML',
        'streamlit',
        'pytest',
        'ipython',
        'jupyter',
        'jupyterlab',
        'jupyter_contrib_nbextensions',
    ],
)
