import os
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer




class Persistence:
    FILE_NAME = "H5SkillPredict.ini"

    def __init__(self):
        Persistence.loadfont("heiti_ui.otf", True, True)
        if os.path.isfile(Persistence.FILE_NAME):
            with open(Persistence.FILE_NAME) as fp:
                contents = tuple(line.rstrip() for line in fp)
        else:
            contents = ("", "True", "300,10", "1150,10")

        self.last_path = contents[0]
        self.show_log = True if contents[1] == "True" else False
        self.main_x, self.main_y = [int(i) for i in contents[2].split(",")]
        self.log_x, self.log_y = [int(i) for i in contents[3].split(",")]
        self.font = "Adobe 黑体 Std R"

    def save(self):
        contents = (self.last_path, self.show_log, 
                    f"{self.main_x},{self.main_y}",
                    f"{self.log_x},{self.log_y}")

        with open(Persistence.FILE_NAME, 'w') as fp:
            for i in contents:
                fp.write(f"{i}\n")

    @staticmethod
    def loadfont(fontpath, private=True, enumerable=False):
        FR_PRIVATE  = 0x10
        FR_NOT_ENUM = 0x20

        if isinstance(fontpath, str):
            pathbuf = create_unicode_buffer(fontpath)
            AddFontResourceEx = windll.gdi32.AddFontResourceExW
        else:
            raise TypeError('fontpath must be of type str or unicode')

        flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
        numFontsAdded = AddFontResourceEx(byref(pathbuf), flags, 0)
        return bool(numFontsAdded)


per = Persistence()