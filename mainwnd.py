import sys

TITLE = "英雄无敌5技能概率计算器"

class MainWnd():
    def __init__(self, *args, **kwargs):
        super(MainWnd, self).__init__(*args)
        self.info = kwargs["info"]

    def closeEvent(self,event):
        event.ignore()
        sys.exit(0)