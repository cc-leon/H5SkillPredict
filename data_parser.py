from fileinput import filename
from multiprocessing.sharedctypes import Value
import os
import pprint

from zipfile import BadZipFile, ZipFile


class DataParser:
    DIRS = ("data", "UserMods", "Maps")

    def __init__(self, h5_path):
        self.h5_path = h5_path
        self.zip_q = None
        self.manifest = None

        self._build_zip_list()

        self.heroclass_xdb = self.get_file("GameMechanics/RefTables/HeroClass.xdb")
        if self.heroclass_xdb is None:
            raise ValueError("没有找到HeroClass.xdb，游戏文件有损失！")
        self._parse_heroclass_xdb()

        self.skills_xdb = self.get_file("GameMechanics/RefTables/Skills.xdb")
        if self.skills_xdb is None:
            raise ValueError("没有找到Skills.xdb，游戏文件有损失！")
        self._parse_skills_xdb()


    def _build_zip_list(self):
        temp = []
        self.manifest_map = {}

        for folder in DataParser.DIRS:
            fullpath = os.path.join(self.h5_path, folder)

            if os.path.isdir(fullpath):
                for f in os.listdir(fullpath):
                    fullname = os.path.join(fullpath, f)
                    if os.path.isfile(fullname):
                        try:
                            zip_file = ZipFile(fullname)
                            self.manifest
                            temp.append((zip_file, os.path.getmtime(fullname)))
                        except BadZipFile:
                            pass

            elif folder == "data":
                raise ValueError(f"\"{self.h5_path}\"中没有找到\"{folder}\"")

        self.zip_q = tuple(i[0] for i in sorted(temp, key=lambda x: x[1], reverse=True))

    def _parse_heroclass_xdb(self):
        self.heroclass_xdb

    def _parse_skills_xdb(self):
        self.skills_xdb

    def get_file(self, file_name):
        for i in self.zip_q:
            import pdb; pdb.set_trace()
            try:
                return i.read(file_name)
            except KeyError:
                pass

        return None