from genericpath import isdir
import os
from zipfile import BadZipFile, ZipFile

class DataParser:

    DIRS = ("data", "UserMods", "Maps")

    def __init__(self, h5_path):
        self.h5_path = h5_path
        self.zip_list = []

        self._build_zip_list()

    def _build_zip_list(self):
        for folder in DataParser.DIRS:
            fullpath = os.path.join(self.h5_path, folder)

            if os.path.isdir(fullpath):
                for f in os.listdir(fullpath):
                    fullname = os.path.join(fullpath, f)
                    if os.path.isfile(fullname):
                        try:
                            self.zip_list.append((ZipFile(fullname), ))
                        except BadZipFile:
                            pass

            elif folder == "data":
                raise ValueError(f"\"{self.h5_path}\"中没有找到\"{folder}\"")

    def get_file(self, file_name):
        pass