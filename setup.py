import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="root_dash_lib",
    version="0.1",
    author="Zach Hafen-Saavedra",
    author_email="zachary.h.hafen@gmail.com",
    description="template dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhafen/root-dash",
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
