import os


class Persistence:
    FILE_NAME = "H5SkillPredict.txt"

    def __init__(self):
        if os.path.isfile(Persistence.FILE_NAME):
            with open(Persistence.FILE_NAME) as fp:
                contents = tuple(line.rstrip() for line in fp)
        else:
            contents = ("", )

        self.last_path = contents[0]

    def __del__(self):
        contents = (self.last_path, )
        with open(Persistence.FILE_NAME, 'w') as fp:
            for i in contents:
                fp.write(f"{i}\n")
