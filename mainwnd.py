import sys
from tkinter import messagebox, filedialog, Tk, Menu
from tkinter.ttk import Frame, Label, Button

from data_parser import RawData, GameInfo
from persistence import Persistence


TITLE = "英雄无敌5技能概率计算器"


class InteractiveFrame(Frame):
    def __init__(self, container):
        super(InteractiveFrame, self).__init__(container)

        options = {"padx": 5, "pady": 5}

        self.label = Label(self, text="Hello, cats!")
        self.label.pack(**options)

        self.button = Button(self, text="Meow")
        self.button["command"] = self.button_clicked
        self.button.pack(**options)

        self.pack(**options)

    def button_clicked(self):
        messagebox.showinfo("Cats says:", "Meow meow meow!")


class LogFrame(Frame):
    def __init__(self, container):
        super(LogFrame, self).__init__(container)
        options = {"padx": 5, "pady": 5}
        #self.pack(**options)
        self.button = Button(self, text="Logging")
        self.button["command"] = self.button_clicked
        self.button.pack(**options)

    def button_clicked(self):
        messagebox.showinfo("Cats says:", "Meow meow meow!")


class ProgressFrame(Frame):
    def __init__(self, container):
        super(ProgressFrame, self).__init__(container)
        options = {"padx": 5, "pady": 5}
        #self.pack(**options)
        self.button = Button(self, text="Progress")
        self.button["command"] = self.button_clicked
        self.button.pack(**options)

    def button_clicked(self):
        messagebox.showinfo("Cats says:", "Meow meow meow!")


class MainWnd(Tk):
    def __init__(self, *args):
        super(MainWnd, self).__init__(*args)
        self.title(TITLE)

        self.interactive_frame = InteractiveFrame(self)
        self.interactive_frame.grid(column=0, row=0)

        self.log_frame = LogFrame(self)
        self.log_frame.grid(column=0, row=1)

        self._build_top_menu()
        #self._asking_game_data()

    def _build_top_menu(self):
        self.top_menu = Menu(self)
        self.config(menu=self.top_menu)
        self.top_menu.add_command(label="喵喵喵！", command=self._menu1)

    def _menu1(self, **kwargs):
        self.top_menu.entryconfig(1, label="旺旺旺！")

    def _asking_game_data(self):
        per = Persistence()

        while True:
            #h5_path = filedialog.askdirectory(title="请选择英雄无敌5安装文件夹", initialdir=per.last_path)

            h5_path = "D:\\games\\TOE31\\"
            if h5_path == "":
                messagebox.showerror(TITLE, "本程序依赖已安装的英雄无敌5游戏数据！\n无游戏数据，退出。")
                sys.exit(0)

            per.last_path = h5_path

            try:
                self.game_info = GameInfo(RawData(h5_path))
                break
            except ValueError as e:
                messagebox.showerror(TITLE, str(e) + "，\n请检查是否是正确的英雄无敌5安装文件夹")