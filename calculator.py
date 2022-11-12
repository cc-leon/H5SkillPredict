from pprint import pprint
from copy import deepcopy
from collections import OrderedDict

import data_parser as gg


class Hero():
    def __init__(self, hero_info, level=1):
        self._skills = OrderedDict()
        self._perks_set = set()
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
        skills = tuple((i, self._skills[i][0]) for i in self._skills)
        perks = tuple(tuple(self._skills[i][1]) for i in self._skills)
        return skills, perks

    def reload_skills(self, skills, perks):
        self._skills = {}
        self._perks_set = set()
        for skill in skills:
            self._skills[skill[0]] = (skill[1], [])

        for perk in perks:
            self._perks_set.add(perk)
            self._skills[gg.info.perk2skill[perk]][1].append(perk)

    def reload_skill(self, old_skill, skill, perks):
        print(old_skill, skill, perks)
        points_added = 0
        points_removed = 0
        """
        if skill is not None:
            points_added = skill[1] + len(perks)
            if skill in self._skills:
                pass
        elif old_skill is None else self._skills[old_skill][0] + len(self._skills[old_skill][1])
        """

    def get_select_skills(self, id):
        result = []
        if id is not None:
            if id != next(iter(self._skills.keys())):
                result.append((None, None))
            for i in range(1, 4):
                if i != self._skills[id][0]:
                    result.append((id, i))

        if id == next(iter(self._skills.keys())):
            return result

        for s in gg.info.class2skill[self._race]:
            if s not in self._skills:
                result.append((s, 1))

        return result

    def get_levelup_skills(self):
        pass

    def get_select_perks(self, id):
        standard = []
        special = []
        return standard, special

    def get_levelup_perks(self):
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