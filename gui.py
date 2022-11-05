import sys
import logging
import time
from threading import Thread, Lock
from tkinter import W, E, END
from tkinter import messagebox, filedialog, Tk, Menu, scrolledtext
from tkinter.ttk import Frame, Label, Button, Progressbar

from data_parser import RawData, GameInfo
from persistence import Persistence


TITLE = "英雄无敌5技能概率计算器"


class InteractiveFrame(Frame):
    def __init__(self, container):
        super(InteractiveFrame, self).__init__(container)

        self.label = Label(self, text="Hello, cats!")
        self.label.grid(column=0, row=0)

        self.button = Button(self, text="Meow")
        self.button["command"] = self.button_clicked
        self.button.grid(column=0, row=1)

    def button_clicked(self):
        logging.info("Cats says:")
        logging.info("Meow meow meow!")


class LogFrame(Frame):
    class _TextHandler(logging.Handler):
        def __init__(self, text):
            super(LogFrame._TextHandler, self).__init__()
            self.text = text

        def emit(self, record):
            msg = self.format(record)
            def append():
                self.text.configure(state="normal")
                self.text.insert(END, msg + "\n")
                self.text.configure(state="disabled")
                self.text.yview(END)
            self.text.after(0, append)

    def __init__(self, parent):
        super(LogFrame, self).__init__(parent)
        self.root = parent
        self.build_gui()

    def build_gui(self):                    
        self.log_box = scrolledtext.ScrolledText(self, state='disabled', height=20, width=80)
        self.log_box.configure(font='TkFixedFont')
        self.log_box.grid(column=0, row=0)

        text_handler = LogFrame._TextHandler(self.log_box)

        logger = logging.getLogger()
        logger.addHandler(text_handler)


class MainWnd(Tk):
    def __init__(self, *args):
        super(MainWnd, self).__init__(*args)
        self.per = Persistence()
        self.game_info = None
        self.lock = Lock()

        self.withdraw()
        self.title(TITLE)
        self.resizable(False, False)

        #self.interactive_frame = InteractiveFrame(self)
        #self.interactive_frame.(column=0, row=0, sticky="w", padx=10, pady=10)

        self.log_frame = LogFrame(self)
        self.log_frame.grid(column=0, row=1, columnspan=2)

        self.status_text = Label(self, text="已启动", border=1, relief="sunken", padding=2, font=("", 10))
        self.status_text.grid(column=0, row=2, sticky=W+E)
        self.status_prog = Progressbar(self)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_top_menu()
        self._asking_game_data()

    def on_close(self):
        del self.per
        self.destroy()

    def _build_top_menu(self):
        self.top_menu = Menu(self)
        self.config(menu=self.top_menu)

        self.top_menu.add_command(label="", command=self._on_menu_showlog)
        self.per.show_log = not self.per.show_log
        self._on_menu_showlog()

    def _on_menu_showlog(self, **kwargs):
        if self.per.show_log:
            new_text = "显示日志"
            self.log_frame.grid_forget()
        else:
            new_text = "隐藏日志"
            self.log_frame.grid(column=0, row=1)

        self.per.show_log = not self.per.show_log
        self.top_menu.entryconfig(1, label=new_text)

    def _build_skill_gui(self):
        self.status_prog.grid_forget()
        self.status_text.grid(column=0, row=2, sticky=W+E, columnspan=2)
        self.status_text.config(text="游戏数据加载完毕")

    def _asking_game_data(self):
        self.withdraw()
        #h5_path = filedialog.askdirectory(title="请选择英雄无敌5安装文件夹", initialdir=self.per.last_path)

        h5_path = "D:\\games\\TOE31\\"
        if h5_path == "":
            messagebox.showerror(TITLE, "本程序依赖已安装的英雄无敌5游戏数据！\n无游戏数据，退出。")
            sys.exit(0)
        self.per.last_path = h5_path

        self.game_info = None
        self.deiconify()
        self.status_text.grid(column=0, row=2, sticky=W+E, columnspan=1)
        self.status_prog.grid(column=1, row=2, sticky=W+E)
        raw_data = RawData(h5_path)
        game_info = GameInfo()
        Thread(target=self._ask_game_data_thread, args=(raw_data, game_info)).start()
        self.after(10, self._ask_game_data_after, raw_data, game_info)

    def _ask_game_data_thread(self, raw_data, game_info):
        raw_data.run()
        try:
            game_info.run(raw_data)
        except ValueError as e:
            with self.lock:
                self.game_info = e

        with self.lock:
            self.game_info = game_info

    def _ask_game_data_after(self, raw_data, game_info):
        with self.lock:
            if type(self.game_info) is ValueError:
                messagebox.showerror(TITLE, str(self.game_info) + "，\n请检查是否是正确的英雄无敌5安装文件夹")
                self._asking_game_data()
            elif type(self.game_info) is GameInfo:
                self._build_skill_gui()
            else:
                status_text = ""
                prog_value = 0.0
                total_weight = RawData.get_time_weightage() + GameInfo.get_time_weightage()

                if game_info.get_stage() is None:
                    status_text = raw_data.get_stage()
                    prog_value = raw_data.get_progress() * 100 * \
                        RawData.get_time_weightage() / total_weight
                else:
                    status_text = game_info.get_stage()
                    prog_value = game_info.get_progress() * 100 * GameInfo.get_time_weightage() / total_weight \
                        + RawData.get_time_weightage() * 100 / total_weight

                self.status_text.config(text=f"{status_text}, 总进度{prog_value:.2f}%")
                self.status_prog.config(value=prog_value)
                self.after(10, self._ask_game_data_after, raw_data, game_info)
