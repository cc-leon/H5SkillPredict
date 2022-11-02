import logging
import os
from time import time
import pprint

from zipfile import BadZipFile, ZipFile


class DataParser:
    DIRS = ("data", "UserMods", "Maps")

    def __init__(self, h5_path):
        self.h5_path = h5_path
        self.zip_q = None
        self.manifest = None
        self.data = None

        prev_timeit = time()

        logging.info(f"开始\"{h5_path}\"的所有压缩文件扫描……")
        self._build_zip_list()
        logging.info(f"压缩文件信息扫描完毕，发现{len(self.zip_q)}个文件，用时{time() - prev_timeit: .2f}秒。\n")
        prev_timeit = time()

        logging.info("解析HeroClass.xdb中的信息……")
        self.heroclass_xdb = self.get_file("GameMechanics/RefTables/HeroClass.xdb")
        if self.heroclass_xdb is None:
            raise ValueError("没有找到HeroClass.xdb，游戏数据损失！")
        self._parse_heroclass_xdb()
        logging.info(f"HeroClass.xdb解析完毕，发现{0}个职业，{0}种技能，"
                     f"用时{time() - prev_timeit: .2f}秒。\n")
        prev_timeit = time()

        logging.info("解析Skills.xdb中的信息……")
        self.skills_xdb = self.get_file("GameMechanics/RefTables/Skills.xdb")
        if self.skills_xdb is None:
            raise ValueError("没有找到Skills.xdb，游戏数据损失！")
        self._parse_skills_xdb()
        logging.info(f"Skills.xdb解析完毕，加载了{0}个技能名，{0}个技能图标，{0}技能描述，"
                     f"用时{time() - prev_timeit: .2f}秒。\n")
        prev_timeit = time()


    def _build_zip_list(self):
        temp = []
        self.manifest = {}

        for folder in DataParser.DIRS:
            fullpath = os.path.join(self.h5_path, folder)

            if os.path.isdir(fullpath):
                for f in os.listdir(fullpath):
                    fullname = os.path.join(fullpath, f)
                    if os.path.isfile(fullname):
                        try:
                            zip_file = ZipFile(fullname)
                            #self.manifest(fullname)
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
            try:
                return i.read(file_name)
            except KeyError:
                pass

        return None