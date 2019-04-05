call "Scripts/activate.bat"
python setup.py bdist_wheel sdist
twine upload dist/*
PAUSE