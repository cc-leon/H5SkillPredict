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
    a = [1, 3, 4, 5, 6]
    print([i > 1 for i in a])
    print(any(i > 1 for i in a))


if __name__ == "__main__":
    main()
    #test()
