from tkinter import messagebox as msgbox

from data_parser import DataParser
from persistence import Persistence


def main():
    per = Persistence()

    while True:
        """
        h5_path = fd.askdirectory(
            title="请选择英雄无敌5安装文件夹",
            initialdir=per.last_path
        )"""
        h5_path = "D:\\games\\TOE31\\"
        if h5_path == "":
            return

        per.last_path = h5_path

        try:
            parser = DataParser(h5_path)
            break
        except ValueError as e:
            msgbox.showerror("错误：", str(e) + "，\n请检查是否是正确的英雄无敌5安装文件夹")

    print()

def test():
    from zipfile import ZipFile, Path
    aa = ZipFile("D:\\games\\TOE31\\data\\data.pak")
    import datetime
    now = datetime.datetime.now()
    print(now)
    bb = aa.namelist()
    bbb = [i for i in bb]
    bbbb = dict(zip(bbb, bb))
    import pprint, sys
    pprint.pprint(sys.getsizeof(bbbb))
    now = datetime.datetime.now()
    print(now)
    #print(bb.exists())
    #print(bb)


if __name__ == "__main__":
    #main()
    test()