rmdir build /Q/S
rmdir dist /Q/S
rmdir include /Q/S
rmdir Lib /Q/S
rmdir tcl /Q/S
rmdir pandasgui.egg-info /Q/S
python setup.py bdist_wheel sdist
python3 -m twine upload dist/*
PAUSE