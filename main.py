import logging
import sys
from tkinter import messagebox, filedialog

from data_parser import RawData, GameInfo
from persistence import Persistence
from mainwnd import MainWnd, TITLE


def main():
    logging.basicConfig(level=logging.INFO, filename="H5SkillPredict.log", filemode="w",
                        encoding="utf_16", format="%(message)s")
    per = Persistence()

    while True:
        h5_path = filedialog.askdirectory(title="请选择英雄无敌5安装文件夹", initialdir=per.last_path)

        #h5_path = "D:\\games\\TOE31\\"
        if h5_path == "":
            messagebox.showerror(TITLE, "本程序依赖已安装的英雄无敌5游戏数据！\n无游戏数据，退出。")
            return

        per.last_path = h5_path

        try:
            game_info = GameInfo(RawData(h5_path))
            break
        except ValueError as e:
            messagebox.showerror(TITLE, str(e) + "，\n请检查是否是正确的英雄无敌5安装文件夹")


def test():
    from zipfile import ZipFile, Path
    aa = ZipFile("D:\\games\\TOE31\\data\\data.pak")
    import datetime
    now = datetime.datetime.now()
    print(now)
    bb = aa.namelist()
    bbb = [i for i in bb]
    bbbb = dict(zip(bbb, bb))


if __name__ == "__main__":
    main()
    #test()
