import logging

from gui import MainWnd


def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")

    main_window = MainWnd()
    main_window.mainloop()


def test():
    from threading import Lock
    aa = Lock()

    with aa:
        print("aa")

    with aa:
        print("bb")

if __name__ == "__main__":
    main()
    #test()
