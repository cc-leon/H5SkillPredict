import logging
import os
from time import time
import xml.etree.ElementTree as ET
from collections import namedtuple
import pprint
from zipfile import BadZipFile, ZipFile
from io import BytesIO
from threading import Lock
1
from PIL import Image, ImageChops


SkillInfo = namedtuple("SkillInfo", ["names", "descs", "icons"])
PerkInfo = namedtuple("PerkInfo", ["name", "desc", "typ", "icon", "grey", "preq"])


class RawData:
    DIRS = ("data", "UserMods", "Maps")

    def __init__(self, h5_path):
        self.h5_path = h5_path
        self.zip_q = None
        self.manifest = None
        self.curr_stage = "估计中"
        self.curr_prog = 0.0
        self.total_prog = 1.0
        self.lock = Lock()

    def run(self):
        prev_timeit = time()
        logging.info(f"开始\"{self.h5_path}\"的所有压缩文件扫描……")
        self._gen_stats()
        self._build_zip_list()
        logging.warning(f"压缩文件信息扫描完毕，发现{len(self.zip_q)}个文件，用时{time() - prev_timeit:.2f}秒。")
        prev_timeit = time()

    def _gen_stats(self):
        with self.lock:
            self.total_prog = 0

            for folder in RawData.DIRS:
                fullpath = os.path.join(self.h5_path, folder)
                if os.path.isdir(fullpath):
                    self.total_prog += len(tuple(f for f in os.listdir(fullpath)
                                                if f.lower().endswith(".pak") or f.lower().endswith(".h5m") or \
                                                    f.lower().endswith(".h5u")))

                elif folder == "data":
                    raise ValueError(f"\"{self.h5_path}\"中没有找到\"{folder}\"")

    def _build_zip_list(self):
        temp = []
        self.manifest = {}
        self.curr_prog = 0

        for folder in RawData.DIRS:
            fullpath = os.path.join(self.h5_path, folder)
            if not os.path.isdir(fullpath): continue
            with self.lock:
                self.curr_stage = f"正在扫描{folder}文件夹"

            for f in os.listdir(fullpath):
                fullname = os.path.join(fullpath, f)
                if os.path.isfile(fullname):
                    try:
                        zip_file = ZipFile(fullname)
                        temp.append((zip_file, os.path.getmtime(fullname)))
                        with self.lock:
                            self.curr_prog += 1
                        logging.info(f"  在{folder}发现{f}")

                        namelist = zip_file.namelist()
                        self.manifest[fullname] = dict(zip([i.lower() for i in namelist], namelist))
                        logging.info(f"    压缩包中有{len(namelist)}个文件；")

                    except BadZipFile:
                        logging.info(f"  {folder}中的{f}并不是有效的压缩文件")


        self.zip_q = tuple(i[0] for i in sorted(temp, key=lambda x: x[1], reverse=True))

    def get_file(self, file_name):
        file_name = file_name.lower()
        for i in self.zip_q:
            if file_name in self.manifest[i.filename]:
                return i.read(self.manifest[i.filename][file_name])

        return None

    def get_progress(self):
        with self.lock:
          return self.curr_prog / self.total_prog

    def get_stage(self):
        with self.lock:
            return self.curr_stage

    @staticmethod
    def get_time_weightage():
        return 3.0


class GameInfo:
    HEROCLASS_XDB = "GameMechanics/RefTables/HeroClass.xdb"
    SKILLS_XDB = "GameMechanics/RefTables/Skills.xdb"
    HEROSCREEN3_XDB = "UI/HeroScreen3.(WindowScreen).xdb"
    ANY_XDB = "MapObjects/_(AdvMapSharedGroup)/Heroes/Any.xdb"

    def __init__(self):
        self.skill_prob = None
        self.class_info = None
        self.skill_info = None
        self.perk_info = None
        self.curr_stage = None
        self.ui = None
        self.curr_prog = 0
        self.total_prog = 322
        self.lock = Lock()
        self.xdbs = {"skills": None, "heroclass": None, "heroscreen3": None, "any": None}

    def run(self, data):
        RunInfo = namedtuple("RunInfo", ("xdb_path", "dict_key",  "sub_func", "done_msg", "done_args"))
        run_info = (
            RunInfo(GameInfo.SKILLS_XDB, "skills", self._parse_skills_xdb, 
                    "解析完毕，加载了{}个主技能，{}个子技能",
                    (lambda : len(self.skill_info), lambda : sum([len(i) for i in self.perk_info.values()]))),
            RunInfo(GameInfo.HEROCLASS_XDB, "heroclass", self._parse_heroclass_xdb,
                    "解析完毕，发现{}个职业，一共{}种主技能技能概率",
                    (lambda : len(self.class_info), lambda: sum([len(i) for i in self.skill_prob.values()]))),
            RunInfo(GameInfo.HEROSCREEN3_XDB, "heroscreen3", self._parse_ui_xdb,
                    "解析完毕，加载了{}个UI部件",
                    (lambda : 0, )),
            RunInfo(GameInfo.ANY_XDB, "any", self._parse_hero_xdb,
                    "解析完毕，加载了{}个英雄",
                    (lambda : 0, ))
        )

        for info in run_info:
            prev_timeit = time()
            file_name = os.path.basename(info.xdb_path)
            logging.info(f"\n解析{file_name}中的信息……")
            with self.lock:
                self.curr_stage = f"解析{file_name}中的信息"
            self.xdbs[info.dict_key] = data.get_file(info.xdb_path)
            if self.xdbs[info.dict_key] is None:
                raise ValueError(f"没有找到{file_name}，游戏数据损失！")
            info.sub_func(data)
            done_msg = info.done_msg.format(*(i() for i in info.done_args))
            logging.warning(file_name + done_msg + f"，用时{time() - prev_timeit:.2f}秒。")

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

    @staticmethod
    def _parse_xdb(href, xdb, data):
        return data.get_file(GameInfo._proc_xdb_path(href, xdb).split("#")[0])

    def _parse_heroclass_xdb(self, data):
        root = ET.fromstring(self.xdbs["heroclass"])
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
                        with self.lock:
                            self.curr_prog += 1

    def _parse_skills_xdb(self, data):
        root = ET.fromstring(self.xdbs["skills"])
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
                    with self.lock:
                        self.curr_prog += 1

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
                    with self.lock:
                        self.curr_prog += 1

    def _parse_ui_xdb(self, data):
        self.ui = {}

        ele = ET.fromstring(self.xdbs["heroscreen3"]).find("Shared")
        xdb_path = GameInfo._proc_xdb_path(ele.get("href").split("#")[0], self.HEROSCREEN3_XDB)
        xdb_file = GameInfo._parse_xdb(ele.get("href"), self.HEROSCREEN3_XDB, data)
        ele = ET.fromstring(xdb_file).find("Children")

        # Get Background dds
        # Load HeroMeetFull.(WindowSimple).xdb into memory
        heromeet_xdb_path = GameInfo._proc_xdb_path(ele[5].get("href").split("#")[0], xdb_path)
        logging.info(f"  解析UI文件{heromeet_xdb_path}")
        heromeet_xdb_file = GameInfo._parse_xdb(ele[5].get("href"), xdb_path, data)
        # Load HeroMeetFull.(WindowSimpleShared).xdb into memory
        heromeet_ele = ET.fromstring(heromeet_xdb_file).find("Shared")
        heromeet_xdb_file = GameInfo._parse_xdb(heromeet_ele.get("href"), heromeet_xdb_path, data)
        heromeet_xdb_path = GameInfo._proc_xdb_path(heromeet_ele.get("href").split("#")[0], heromeet_xdb_path)
        logging.info(f"  解析UI文件{heromeet_xdb_path}")
        # Load HeroMeet.(WindowSimple).xdb into memory
        heromeet_ele = ET.fromstring(heromeet_xdb_file).find("Children")[0]
        heromeet_xdb_file = GameInfo._parse_xdb(heromeet_ele.get("href"), heromeet_xdb_path, data)
        heromeet_xdb_path = GameInfo._proc_xdb_path(heromeet_ele.get("href").split("#")[0], heromeet_xdb_path)
        logging.info(f"  解析UI文件{heromeet_xdb_path}")
        # Load HeroMeet.(WindowSimpleShared).xdb into memory
        heromeet_ele = ET.fromstring(heromeet_xdb_file).find("Shared")
        heromeet_xdb_file = GameInfo._parse_xdb(heromeet_ele.get("href"), heromeet_xdb_path, data)
        heromeet_xdb_path = GameInfo._proc_xdb_path(heromeet_ele.get("href").split("#")[0], heromeet_xdb_path)
        logging.info(f"  解析UI文件{heromeet_xdb_path}")

        # Load skills and abilities xdb for dds
        heromeet_ele = ET.fromstring(heromeet_xdb_file).find("Children")
        heromeet_skills = heromeet_ele[2].get("href")
        heromeet_abilities = heromeet_ele[3].get("href")

        def _get_skill_or_ability(href):
            # Load Skills/Abilities.(WindowSimple).xdb into memory
            heromeet_this_xdb_file = GameInfo._parse_xdb(href, heromeet_xdb_path, data)
            heromeet_this_xdb_path = GameInfo._proc_xdb_path(href.split("#")[0], heromeet_xdb_path)
            logging.info(f"  解析UI文件{heromeet_this_xdb_path}")
            # Load Skills/Abilities.(WindowSimpleShared).xdb into memory
            heromeet_ele = ET.fromstring(heromeet_this_xdb_file).find("Shared")
            heromeet_this_xdb_file = GameInfo._parse_xdb(heromeet_ele.get("href"), heromeet_this_xdb_path, data)
            heromeet_this_xdb_path = GameInfo._proc_xdb_path(heromeet_ele.get("href").split("#")[0],
                                                            heromeet_this_xdb_path)
            logging.info(f"  解析UI文件{heromeet_this_xdb_path}")
            # Load Skills/Abilities.(BackgroundSimpleTexture).xdb into memory
            heromeet_ele = ET.fromstring(heromeet_this_xdb_file).find("Background")
            heromeet_this_xdb_file = GameInfo._parse_xdb(heromeet_ele.get("href"), heromeet_this_xdb_path, data)
            heromeet_this_xdb_path = GameInfo._proc_xdb_path(heromeet_ele.get("href").split("#")[0],
                                                            heromeet_this_xdb_path)
            logging.info(f"  解析UI文件{heromeet_this_xdb_path}")
            # Load Skills/Abilities.xdb into memory
            dds_href = ET.fromstring(heromeet_this_xdb_file).find("Texture").get("href")
            result = GameInfo._parse_dds(dds_href, heromeet_this_xdb_path, data)
            logging.info(f"  解析UI文件{heromeet_this_xdb_path}")

            bg = Image.new(result.mode, result.size, result.getpixel((0, 0)))
            diff = ImageChops.difference(result, bg)
            diff = ImageChops.add(diff, diff, 2.0, -100)
            rect = diff.getbbox()
            return result.crop(rect), rect

        img, rect = _get_skill_or_ability(heromeet_skills)
        rect = (rect[0], int((rect[3] - rect[1]) * .681), rect[2], rect[3])
        self.ui["skills"] = (img.crop(rect), rect)
        img, rect = _get_skill_or_ability(heromeet_abilities)
        rect = (rect[0], rect[1], rect[2], int((rect[3] - rect[1]) * .94))
        self.ui["abilities"] = (img.crop(rect), rect)

        # Load ICO bg and positions
        meethero_xdb = ele[3].get("href")


    def _parse_hero_xdb(self, data):
        import time

    @staticmethod
    def get_time_weightage():
        return 2.6

    def get_progress(self):
        with self.lock:
            return self.curr_prog / self.total_prog

    def get_stage(self):
        with self.lock:
            return self.curr_stage