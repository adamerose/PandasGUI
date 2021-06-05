import os
import sys

sys.path.append(os.path.dirname(__file__))
dirname = os.path.dirname(__file__)

DARK = None
LIGHT = None
with open(os.path.join(dirname, "compiled/dark.qss")) as f:
    DARK = f.read()
with open(os.path.join(dirname, "compiled/light.qss")) as f:
    LIGHT = f.read()


def dark(hot_reload=False):
    if hot_reload:
        compile()
    return DARK


def light(hot_reload=False):
    if hot_reload:
        compile()
    return LIGHT


def compile():
    import qtsass
    # Compile SCSS into QSS
    qtsass.compile_filename(os.path.join(dirname, "./styling/dark.scss"),
                            os.path.join(dirname, "./compiled/dark.qss"))
    qtsass.compile_filename(os.path.join(dirname, "./styling/light.scss"),
                            os.path.join(dirname, "./compiled/light.qss"))
    # Compile resources defined by style.qrc into a python module
    os.system("pyrcc5 ./styling/main.qrc -o ./compiled/qstylish_rc.py")
    # This part is for hot reload
    with open(os.path.join(dirname, "compiled/dark.qss")) as f:
        global DARK
        DARK = f.read()
    with open(os.path.join(dirname, "compiled/light.qss")) as f:
        global LIGHT
        LIGHT = f.read()


if __name__ == "__main__":
    compile()
