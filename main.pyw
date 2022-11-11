import logging
from zipfile import ZipFile

from gui import MainWnd
from persistence import per

def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")

    main_window = MainWnd()
    main_window.mainloop()


def test():
    from tkinter import Tk, font
    root = Tk()
    print(font.families()[-2])


if __name__ == "__main__":
    main()
    #test()
