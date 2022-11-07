import logging
from zipfile import ZipFile

from gui import MainWnd


def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")

    main_window = MainWnd()
    main_window.mainloop()

from dataclasses import dataclass

def test():
    pass


if __name__ == "__main__":
    main()
    #test()
