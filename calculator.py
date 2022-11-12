from pprint import pprint
from copy import deepcopy

import data_parser as gg


class Hero():
    def __init__(self, hero_info, level=1):
        self._skills = {}
        self._perks_set = set()
        self._skill_list = []
        self._race = hero_info.race
        self._id = hero_info.id
        self.reload_skills(hero_info.skills, hero_info.perks)
        self._level = level
        self._history = {}

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def slots22dtuple(self):
        skills = tuple((i, self._skills[i][0]) for i in self._skill_list)
        perks = tuple(tuple(self._skills[i][1]) for i in self._skill_list)
        return skills, perks

    def reload_skills(self, skills, perks):
        self._skills = {}
        self._skill_list = []
        self._perks_set = set()
        for skill in skills:
            self._skills[skill[0]] = (skill[1], [])
            self._skill_list.append(skill[0])

        for perk in perks:
            self._perks_set.add(perk)
            self._skills[gg.info.perk2skill[perk]][1].append(perk)

    def reload_skill(self, skill, perks, old_skill=None):
        pass

    def show_skill_options(self, skill=None):
        for skill in Hero.gg.info.class2skill[self._race]:
            pass

    def show_perk_options(self, perk=None):
        pass

    def _compress_slots(self):
        pass

    @property
    def race(self):
        return self._race

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def level(self):
        return self._level