from pprint import pprint


class Hero():
    def __init__(self, race, id, skills, perks, info, level=1):
        self._skills = {}
        self._perks_set = set()
        self._skill_list = []
        self._race = race
        self._id = id
        self._info = info
        self.load_skills(skills, perks)
        self._level = level
        self._history = {}

    def slots22dtuple(self):
        skills = tuple((i, self._skills[i][0]) for i in self._skill_list)
        perks = tuple(tuple(self._skills[i][1]) for i in self._skill_list)
        return skills, perks

    def load_skills(self, skills, perks):
        self._skills = {}
        self._skill_list = []
        self._perks_set = set()
        for skill in skills:
            self._skills[skill[0]] = (skill[1], [])
            self._skill_list.append(skill[0])

        for perk in perks:
            self._perks_set.add(perk)
            self._skills[self._info.perk2skill[perk]][1].append(perk)

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