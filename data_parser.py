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
        return 2.8


class GameInfo:
    HEROCLASS_XDB = "GameMechanics/RefTables/HeroClass.xdb"
    SKILLS_XDB = "GameMechanics/RefTables/Skills.xdb"
    HEROSCREEN3_XDB = "UI/HeroScreen3.(WindowScreen).xdb"
    ANY_XDB = "MapObjects/_(AdvMapSharedGroup)/Heroes/Any.xdb"
    UIInfo = namedtuple("UIInfo", ("bg", "ico"))

    def __init__(self):
        self.skill_prob = None
        self.class_info = None
        self.skill_info = None
        self.perk_info = None
        self.curr_stage = None
        self.ui = None
        self.offsets = None
        self.curr_prog = 0
        self.total_prog = 322
        self.lock = Lock()

    def run(self, data):
        RunInfo = namedtuple("RunInfo", ("xdb_path", "sub_func", "done_msg", "done_args"))
        run_info = (
            RunInfo(GameInfo.SKILLS_XDB, self._parse_skills_xdb, 
                    "解析完毕，加载了{}个主技能，{}个子技能",
                    (lambda : len(self.skill_info), lambda : sum([len(i) for i in self.perk_info.values()]))),
            RunInfo(GameInfo.HEROCLASS_XDB, self._parse_heroclass_xdb,
                    "解析完毕，发现{}个职业，一共{}种主技能技能概率",
                    (lambda : len(self.class_info), lambda: sum([len(i) for i in self.skill_prob.values()]))),
            RunInfo(GameInfo.HEROSCREEN3_XDB, self._parse_ui_xdb,
                    "解析完毕，加载了{}个UI部件",
                    (lambda : 0, )),
            RunInfo(GameInfo.ANY_XDB, self._parse_hero_xdb,
                    "解析完毕，加载了{}个英雄",
                    (lambda : 0, ))
        )

        for info in run_info:
            prev_timeit = time()
            file_name = os.path.basename(info.xdb_path)
            logging.info(f"\n解析{file_name}中的信息……")
            with self.lock:
                self.curr_stage = f"解析{file_name}中的信息"
            if data.get_file(info.xdb_path) is None:
                raise ValueError(f"没有找到{file_name}，游戏数据损失！")
            info.sub_func(data)
            done_msg = info.done_msg.format(*(i() for i in info.done_args))
            logging.warning(file_name + done_msg + f"，用时{time() - prev_timeit:.2f}秒。")

    @staticmethod
    def _proc_xdb_path(href, xdb=None):
        # Given href string from an XDB, and where the XDB is located
        # Returns a file path corresponds to the href string

        if href.startswith("/"):
            return href[1:]
        else:
            curr_loc = os.path.dirname(xdb)
            return curr_loc + "/" + href

    @staticmethod
    def _parse_dds(href, xdb, data):
        # Given a href that poins to a for-dds XDB file, from which XDB file that href is located
        # Returns the Image representation of the dds

        tex_xdb = GameInfo._proc_xdb_path(href, xdb).split("#")[0]
        dds = ET.fromstring(data.get_file(tex_xdb)).find("DestName").get("href")

        if dds == "":
            return None
        dds = GameInfo._proc_xdb_path(dds, tex_xdb)

        return Image.open(BytesIO(data.get_file(dds)))

    @staticmethod
    def _parse_txt(href, xdb, data):
        # Given a href that points to a txt file, and from which XDB file that href is located
        # Return that the string in UTF-16 containted in the txt file

        result = data.get_file(GameInfo._proc_xdb_path(href, xdb)).decode("utf-16")
        return result

    @staticmethod
    def _parse_xdb(href, xdb, data):
        # Given a href that points to a xdb file, and from which XDB file that href is located
        # Return the binary contents of that xdb file
        return data.get_file(GameInfo._proc_xdb_path(href, xdb).split("#")[0])

    @staticmethod
    def _parse_shared_from_simple(simple_href, xdb, data):
        # Given the href that points to a WindowSimple XDB, and from which XDB file that href is located
        # Return the ETree for both WindowSimple and its WindowSimpleShared, and WindowSimpleShared Path

        simple_file = GameInfo._parse_xdb(simple_href, xdb, data)
        simple_path = GameInfo._proc_xdb_path(simple_href.split("#")[0], xdb)
        logging.info(f"  解析UI文件{simple_path}")
        simple_ele = ET.fromstring(simple_file)
        shared_file = GameInfo._parse_xdb(simple_ele.find("Shared").get("href"), simple_path, data)
        shared_path = GameInfo._proc_xdb_path(simple_ele.find("Shared").get("href").split("#")[0], simple_path)
        logging.info(f"  解析UI文件{shared_path}")
        shared_ele = ET.fromstring(shared_file)
        return simple_ele, shared_ele, shared_path

    def _parse_heroclass_xdb(self, data):
        root = ET.fromstring(data.get_file(self.HEROCLASS_XDB))
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
        root = ET.fromstring(data.get_file(self.SKILLS_XDB))
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
        self.offsets = {}

        _, ele, xdb_path = GameInfo._parse_shared_from_simple("/" + GameInfo.HEROSCREEN3_XDB, None, data)
        ele = ele.find("Children")

        # Get Background dds
        # Load HeroMeetFull related into memory
        _, heromeet_ele, heromeet_xdb_path = GameInfo._parse_shared_from_simple(ele[5].get("href"), xdb_path, data)
        heromeet_ele = heromeet_ele.find("Children")[0]
        # Load HeroMeet related into memory
        _, heromeet_ele, heromeet_xdb_path = GameInfo._parse_shared_from_simple(heromeet_ele.get("href"),
                                                                                heromeet_xdb_path, data)
        heromeet_ele = heromeet_ele.find("Children")

        # Load skills and abilities xdb for dds
        heromeet_skills = heromeet_ele[2].get("href")
        heromeet_abilities = heromeet_ele[3].get("href")

        def _get_heromeet_skill_or_ability(href):
            # Load Skills/Abilities related into memory
            _, this_ele, this_xdb_path = GameInfo._parse_shared_from_simple(href, heromeet_xdb_path, data)
            # Load Skills/Abilities.(BackgroundSimpleTexture).xdb into memory
            this_ele = this_ele.find("Background")
            this_xdb_file = GameInfo._parse_xdb(this_ele.get("href"), this_xdb_path, data)
            this_xdb_path = GameInfo._proc_xdb_path(this_ele.get("href").split("#")[0], this_xdb_path)
            logging.info(f"  解析UI文件{this_xdb_path}")
            # Load Skills/Abilities.xdb into memory
            dds_href = ET.fromstring(this_xdb_file).find("Texture").get("href")
            result = GameInfo._parse_dds(dds_href, this_xdb_path, data)
            logging.info(f"  解析UI文件{this_xdb_path}")

            bg = Image.new(result.mode, result.size, result.getpixel((0, 0)))
            diff = ImageChops.difference(result, bg)
            diff = ImageChops.add(diff, diff, 2.0, -100)
            rect = diff.getbbox()
            return result.crop(rect), rect

        logging.info("  合兵Skills和Abilities的DDS文件")
        img1, rect1 = _get_heromeet_skill_or_ability(heromeet_skills)
        rect1 = (rect1[0], int((rect1[3] - rect1[1]) * .681), rect1[2], rect1[3])
        img1 = img1.crop(rect1)
        img2, rect2 = _get_heromeet_skill_or_ability(heromeet_abilities)
        rect2 = (rect2[0], rect2[1], rect2[2], int((rect2[3] - rect2[1]) * .94))
        img2 = img2.crop(rect2)

        cated = Image.new('RGBA', (img1.width, img1.height + img2.height))
        cated.paste(img2, (0, 0))
        cated.paste(img1, (0, img2.height))
        self.ui["bg"] = cated
        self.offsets["abilities"] = (rect2[0], rect2[1])
        self.offsets["skills"] = (rect1[0], rect1[1])

        def _load_meet_or_self_hero(href):
            this_ele, hero_ele, this_xdb_path = GameInfo._parse_shared_from_simple(href, xdb_path, data)
            this_ele = this_ele.find("Placement").find("Position").find("First")
            offset = (int(this_ele.find("x").text), int(this_ele.find("y").text))
            return offset, hero_ele, this_xdb_path

        # Load SelfHero
        self.offsets["self"], hero_ele, hero_xdb_path = _load_meet_or_self_hero(ele[2].get("href"))
        # Load MeetHero
        self.offsets["meet"], _, _ = _load_meet_or_self_hero(ele[3].get("href"))

        hero_ele = hero_ele.find("Children")

        def _load_sub_hero_file(this_sub_ele):
            # Load HeroX.(WindowSimple).xdb into memory
            this_sub_xdb_file = GameInfo._parse_xdb(this_sub_ele.get("href"), hero_xdb_path, data)
            this_sub_xdb_path = GameInfo._proc_xdb_path(this_sub_ele.get("href").split("#")[0],
                                                        hero_xdb_path)
            logging.info(f"  解析UI文件{this_sub_xdb_path}")
            # Load HeroX.(WindowSimpleShared).xdb into memory
            this_sub_ele = ET.fromstring(this_sub_xdb_file).find("Shared")
            this_sub_xdb_file = GameInfo._parse_xdb(this_sub_ele.get("href"), this_sub_xdb_path, data)
            this_sub_xdb_path = GameInfo._proc_xdb_path(this_sub_ele.get("href").split("#")[0],
                                                    this_sub_xdb_path)
            this_sub_ele = ET.fromstring(this_sub_xdb_file)
            return this_sub_xdb_file, this_sub_xdb_path

        # Load HeroInfo.(WindowSimpleShared).xdb into memory
        this_sub_xdb_file, this_sub_xdb_path = _load_sub_hero_file(hero_ele[0])
        # Load HeroSkills.(WindowSimpleShared).xdb into memory
        this_sub_xdb_file, this_sub_xdb_path = _load_sub_hero_file(hero_ele[3])
        # Load HeroAbilities2.(WindowSimpleShared).xdb into memory
        this_sub_xdb_file, this_sub_xdb_path = _load_sub_hero_file(hero_ele[4])

    def _parse_hero_xdb(self, data):
        pass

    @staticmethod
    def get_time_weightage():
        return 0.7

    def get_progress(self):
        with self.lock:
            return self.curr_prog / self.total_prog

    def get_stage(self):
        with self.lock:
            return self.curr_stage