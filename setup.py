from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="pandasgui",
    version="0.2.9",
    description="A GUI for Pandas DataFrames.",
    author="Adam Rose",
    author_email="adam.e.rose@hotmail.com",
    url="https://github.com/adamerose/pandasgui",
    packages=find_packages(),
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    exclude_package_data={'': ['.gitignore']},
    # Using this instead of MANIFEST.in - https://pypi.org/project/setuptools-git/
    setup_requires=['setuptools-git'],
    install_requires=[
        "pandas",
        "PyQt5",
        "PyQt5-sip",
        "PyQtWebEngine",
        "plotly",
        "wordcloud",
        "setuptools",
        "appdirs",
        "dacite",
        "pynput",
        "IPython",
        "pyarrow",
        "astor",
    ],
)
