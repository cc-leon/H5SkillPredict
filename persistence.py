import os


class Persistence:
    FILE_NAME = "H5SkillPredict.ini"

    def __init__(self):
        if os.path.isfile(Persistence.FILE_NAME):
            with open(Persistence.FILE_NAME) as fp:
                contents = tuple(line.rstrip() for line in fp)
        else:
            contents = ("", "True")

        self.last_path = contents[0]
        self.show_log = True if contents[1] == "True" else False

    def __del__(self):
        contents = (self.last_path, self.show_log)
        with open(Persistence.FILE_NAME, 'w') as fp:
            for i in contents:
                fp.write(f"{i}\n")
