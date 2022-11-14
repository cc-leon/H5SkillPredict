import logging
from zipfile import ZipFile

from gui import MainWnd
from persistence import per
from tkinter import font


def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")

    main_window = MainWnd()
    main_window.mainloop()


def test():
    from tkinter import Tk
    root = Tk()
    for i in font.families():
        if "黑" in i.lower():
            print(i)

if __name__ == "__main__":
    main()
    #test()
