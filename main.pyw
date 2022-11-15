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


class A:
    def __init__(self, name):
        self.name = name

    def __hash__(self): return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__ne__(other)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

def test():
    a = A("cat")
    aa = {}
    aa[a] = 123
    a.name = "dog"
    print(aa)

    print(aa)

if __name__ == "__main__":
    main()
    #test()
