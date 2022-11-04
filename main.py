import logging

from mainwnd import MainWnd


def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")

    main_window = MainWnd()
    main_window.mainloop()


def test():
    from zipfile import ZipFile, Path
    aa = ZipFile("D:\\games\\TOE31\\data\\data.pak")


if __name__ == "__main__":
    main()
    #test()
