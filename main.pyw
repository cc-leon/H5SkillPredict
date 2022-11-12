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
    from collections import OrderedDict
    a = OrderedDict({"c":1, "a":2, "b":3 })
    b = dict(a)
    from pprint import pprint
    for k, v in a.items():
        print(k, v)

if __name__ == "__main__":
    main()
    #test()
