from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="pandasgui",
    version="0.2.13",
    description="A GUI for Pandas DataFrames.",
    author="Adam Rose",
    author_email="adrotog@gmail.com",
    url="https://github.com/adamerose/pandasgui",
    packages=find_packages(),
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    exclude_package_data={'': ['.gitignore']},
    # Using this instead of MANIFEST.in - https://pypi.org/project/setuptools-git/
    python_requires=">=3.7",
    setup_requires=['setuptools-git'],
    install_requires=[
        "pandas",
        "numpy",
        "qtpy",
        "plotly",
        "wordcloud",
        "setuptools",
        "appdirs",
        "pynput",
        "IPython",
        "pyarrow",
        "astor",
        "typing-extensions",
        "qtstylish>=0.1.2",
        "pywin32; platform_system=='Windows'",
    ],
    entry_points={
        "gui_scripts": [
            "pandasgui = pandasgui.run_with_args:main"
        ]
    },
)
