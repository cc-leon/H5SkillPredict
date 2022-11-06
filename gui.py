import logging
import time
import sys
from threading import Thread, Lock
from tkinter import W, E, N, S, END
from tkinter import messagebox, filedialog, Tk, Menu, scrolledtext, Toplevel, Text
from tkinter.ttk import Frame, Label, Button, Progressbar

from PIL import ImageTk

from data_parser import RawData, GameInfo
from persistence import Persistence


TITLE = "英雄无敌5技能概率计算器"


class InteractiveFrame(Frame):
    def __init__(self, parent):
        super(InteractiveFrame, self).__init__(parent)
        self.abilities = Label(self)
        self.abilities.grid(column=0, row=0)
        self.skills = Label(self)
        self.skills.grid(column=0, row=1)

    def load_bg(self, abilities_img, skills_img):
        self.abilities_img = ImageTk.PhotoImage(abilities_img)
        self.abilities.config(image=self.abilities_img)
        self.skills_img = ImageTk.PhotoImage(skills_img)
        self.skills.config(image=self.skills_img)


class LogWnd(Toplevel):
    class _TextHandler(logging.Handler):
        def __init__(self, text):
            super(LogWnd._TextHandler, self).__init__()
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
        super(LogWnd, self).__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.title("日志记录")

        self.log_box = scrolledtext.ScrolledText(self, state='disabled', height=40, width=100)
        self.log_box.configure(font='TkFixedFont')
        self.log_box.grid(column=0, row=0, sticky="NEWS")
        text_handler = LogWnd._TextHandler(self.log_box)
        logger = logging.getLogger()
        logger.addHandler(text_handler)


class MainWnd(Tk):
    def __init__(self, *args):
        super(MainWnd, self).__init__(*args)
        self.per = Persistence()
        self.game_info = None
        self.lock = Lock()

        self.log_wnd = LogWnd(self)
        self.withdraw()
        self.title(TITLE)
        self.resizable(False, False)

        self.interactive_frame = InteractiveFrame(self)
        self.interactive_frame.grid(column=0, row=0, sticky="w")

        self.status_text = Label(self, text="已启动", border=1, relief="sunken", padding=2, font=("TkFixedFont", 10))
        self.status_text.grid(column=0, row=2, sticky=W+E)
        self.status_prog = Progressbar(self)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_top_menu()
        #self.geometry(f"{}x{}+{}+{}")
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
            #self.log_box.grid_forget()
        else:
            new_text = "隐藏日志"
            #self.log_box.grid(column=0, row=1, sticky=W + E, columnspan=2)

        self.per.show_log = not self.per.show_log
        self.top_menu.entryconfig(1, label=new_text)

    def _build_skill_gui(self):
        self.status_prog.grid_forget()
        self.status_text.grid(column=0, row=2, sticky=W+E, columnspan=2)
        self.status_text.config(text="游戏数据加载完毕")

        self.interactive_frame.load_bg(self.game_info.ui["abilities"][0], self.game_info.ui["skills"][0])

    def _asking_game_data(self):
        self.withdraw()
        #h5_path = filedialog.askdirectory(title="请选择英雄无敌5安装文件夹", initialdir=self.per.last_path)

        h5_path = "D:\\games\\TOE31\\"
        if h5_path == "":
            messagebox.showerror(TITLE, "本程序依赖已安装的英雄无敌5游戏数据！\n无游戏数据，退出。")
            return self.on_close()

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
        time.sleep(0.1)

        try:
            raw_data.run()
        except ValueError as e:
            with self.lock:
                self.game_info = e
            return

        try:
            game_info.run(raw_data)
        except ValueError as e:
            with self.lock:
                self.game_info = e
            return

        with self.lock:
            self.game_info = game_info

    def _ask_game_data_after(self, raw_data, game_info):
        with self.lock:
            if type(self.game_info) is ValueError:
                self.withdraw()
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

                prog_value = 100.00 if prog_value > 100.00 else prog_value
                status_text = f"{status_text}, 总进度{prog_value:.2f}%"
                status_text += (65 - len(status_text)) * " "
                self.status_text.config(text=status_text)
                self.status_prog.config(value=prog_value)
                self.after(10, self._ask_game_data_after, raw_data, game_info)
