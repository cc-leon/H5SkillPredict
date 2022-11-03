import logging
import os
from time import time
import xml.etree.ElementTree as ET
from collections import namedtuple
import pprint
from zipfile import BadZipFile, ZipFile
from io import BytesIO

from PIL import Image


SkillInfo = namedtuple("SkillInfo", ["names", "descs", "icons"])
PerkInfo = namedtuple("PerkInfo", ["name", "desc", "typ", "icon", "grey", "preq"])


class RawData:
    DIRS = ("data", "UserMods", "Maps")

    def __init__(self, h5_path):
        self.h5_path = h5_path
        self.zip_q = None
        self.manifest = None

        prev_timeit = time()

        logging.info(f"开始\"{h5_path}\"的所有压缩文件扫描……")
        self._build_zip_list()
        logging.warning(f"压缩文件信息扫描完毕，发现{len(self.zip_q)}个文件，用时{time() - prev_timeit:.2f}秒。")
        prev_timeit = time()

    def _build_zip_list(self):
        temp = []
        self.manifest = {}

        for folder in RawData.DIRS:
            fullpath = os.path.join(self.h5_path, folder)

            if os.path.isdir(fullpath):
                for f in os.listdir(fullpath):
                    fullname = os.path.join(fullpath, f)
                    if os.path.isfile(fullname):
                        try:
                            zip_file = ZipFile(fullname)
                            temp.append((zip_file, os.path.getmtime(fullname)))
                            logging.info(f"  在{folder}发现{f}")

                            namelist = zip_file.namelist()
                            self.manifest[fullname] = dict(zip([i.lower() for i in namelist], namelist))
                            logging.info(f"    压缩包中有{len(namelist)}个文件；")

                        except BadZipFile:
                            logging.info(f"  {folder}中的{f}并不是有效的压缩文件")

            elif folder == "data":
                raise ValueError(f"\"{self.h5_path}\"中没有找到\"{folder}\"")

        self.zip_q = tuple(i[0] for i in sorted(temp, key=lambda x: x[1], reverse=True))

    def get_file(self, file_name):
        file_name = file_name.lower()
        for i in self.zip_q:
            if file_name in self.manifest[i.filename]:
                return i.read(self.manifest[i.filename][file_name])

        return None


class GameInfo:
    HEROCLASS_XDB = "GameMechanics/RefTables/HeroClass.xdb"
    SKILLS_XDB = "GameMechanics/RefTables/Skills.xdb"

    def __init__(self, data):
        self.skill_prob = None
        self.class_info = None
        self.skill_info = None
        self.perk_info = None

        prev_timeit = time()

        logging.info("\n解析Skills.xdb中的信息……")
        self.skills_xdb = data.get_file(self.SKILLS_XDB)
        if self.skills_xdb is None:
            raise ValueError("没有找到Skills.xdb，游戏数据损失！")
        self._parse_skills_xdb(data)
        logging.warning(f"Skills.xdb解析完毕，加载了{len(self.skill_info)}个主技能，"
                        f"{sum([len(i) for i in self.perk_info.values()])}个子技能，"
                        f"用时{time() - prev_timeit:.2f}秒。")

        logging.info("\n解析HeroClass.xdb中的信息……")
        self.heroclass_xdb = data.get_file(self.HEROCLASS_XDB)
        if self.heroclass_xdb is None:
            raise ValueError("没有找到HeroClass.xdb，游戏数据损失！")
        self._parse_heroclass_xdb(data)
        logging.warning(f"HeroClass.xdb解析完毕，发现{len(self.class_info)}个职业，"
                        f"一共{sum([len(i) for i in self.class_info.values()])}种主技能技能概率，"
                        f"用时{time() - prev_timeit:.2f}秒。")
        prev_timeit = time()

    @staticmethod
    def _proc_xdb_path(href, xdb=None):
        if href.startswith("/"):
            return href[1:]
        else:
            curr_loc = os.path.dirname(xdb)
            return curr_loc + "/" + href

    @staticmethod
    def _parse_dds(href, xdb, data):
        tex_xdb = GameInfo._proc_xdb_path(href, xdb).split("#")[0]
        dds = ET.fromstring(data.get_file(tex_xdb)).find("DestName").get("href")

        if dds == "":
            return None
        dds = GameInfo._proc_xdb_path(dds, tex_xdb)

        return Image.open(BytesIO(data.get_file(dds)))

    @staticmethod
    def _parse_txt(href, xdb, data):
        result = data.get_file(GameInfo._proc_xdb_path(href, xdb)).decode("utf-16")
        return result

    def _parse_heroclass_xdb(self, data):
        root = ET.fromstring(self.heroclass_xdb)
        self.skill_prob = {}
        self.class_info = {}

        for i in root[0]:
            class_id = i.find("ID").text
            if "NONE" not in class_id:
                self.skill_prob[class_id] = {}
                ele = i.find("obj")

                display_name = GameInfo._parse_txt(ele.find("NameFileRef").get("href"), self.HEROCLASS_XDB, data)
                self.class_info[class_id] = display_name
                logging.info(f"  发现职业信息{class_id}({display_name})")

                for j in ele.find("SkillsProbs"):
                    skill_id = j.find("SkillID").text
                    prob = int(j.find("Prob").text)
                    if prob > 0:
                        self.skill_prob[class_id][skill_id] = prob
                        logging.info(f"    目前职业技能{skill_id}的概率是{prob}")

    def _parse_skills_xdb(self, data):
        root = ET.fromstring(self.skills_xdb)
        self.skill_info = {}
        self.perk_info = {}

        for i in root[0]:
            sp_id = i.find("ID").text
            if "NONE" not in sp_id:
                ele = i.find("obj")

                if ele.find("SkillType").text == "SKILLTYPE_SKILL":
                    def _f(x, f): return tuple(f(j.get("href"), self.SKILLS_XDB, data)
                                               for j in ele.find(x) if "href" in j.attrib)

                    icons = _f("Texture", GameInfo._parse_dds)
                    names = _f("NameFileRef", GameInfo._parse_txt)
                    descs = _f("DescriptionFileRef", GameInfo._parse_txt)
                    self.skill_info[sp_id] = SkillInfo(names, descs, icons)
                    logging.info(f"  找到主技能{sp_id}{str(names)}")

                else:
                    perk_skill = ele.find("BasicSkillID").text
                    if perk_skill not in self.perk_info:
                        self.perk_info[perk_skill] = {}

                    def _f(x, f): return f(x.get("href"), self.SKILLS_XDB, data)

                    name = _f(ele.find("NameFileRef")[0], GameInfo._parse_txt)
                    desc = _f(ele.find("DescriptionFileRef")[0], GameInfo._parse_txt)
                    typ = ele.find("SkillType").text
                    icon = _f(ele.find("Texture")[1], GameInfo._parse_dds)
                    if ele.find("Texture")[0].get("href"):
                        grey = _f(ele.find("Texture")[0], GameInfo._parse_dds)
                        if grey is None:
                            grey = icon
                    else:
                        grey = icon

                    preq = tuple(j for j in ele.find("SkillPrerequisites"))
                    if len(preq) > 0:
                        preq = dict(zip([j.find("Class").text
                                         for j in preq if len(j.find("dependenciesIDs")) > 0],
                                        [tuple(k.text for k in j.find("dependenciesIDs")
                                               if k.tag == "Item")
                                         for j in preq if len(j.find("dependenciesIDs")) > 0]))
                    else:
                        preq = None

                    self.perk_info[perk_skill][sp_id] = PerkInfo(name, desc, typ, icon, grey, preq)
                    logging.info(f"  找到子技能{sp_id}({name})")


    def _parse_ui_xdb(self):
        pass

    def _parse_hero_xdb(self):
        pass
