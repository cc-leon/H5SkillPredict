from pprint import pprint
from copy import deepcopy
from collections import OrderedDict

import data_parser as gg


class Hero():
    def __init__(self, hero_info, level=1):
        self._level = 0
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

    def _get_perk_full_list(self, pid, is_preq=True):
        if is_preq is True:
            target = gg.info.perk_info[pid].preq
        else:
            target = gg.info.perk_info[pid].req

        if self._race in target:
            perks = target[self._race]
        else:
            return []
        result = [i for i in perks]
        for i in perks:
            temp = self._get_perk_full_list(i, is_preq)
            result = temp + result
        return result

    def _get_skill_need(self, perk):
        preqs = self._get_perk_full_list(perk, True)
        skill_need = {}
        skill_need[gg.info.perk2skill[perk]] = {perk, }
        for preq in preqs:
            if preq not in self._perks_set:
                skill_id = gg.info.perk2skill[preq] 
                if skill_id not in skill_need:
                    skill_need[skill_id] = set()
                skill_need[skill_id].add(preq)
        return skill_need

    def _can_accept_skills(self, skill_need, old_perk):
        if old_perk is not None:
            to_remove = set(self._get_perk_full_list(old_perk, False)).intersection(self._perks_set)
        else:
            to_remove = set()

        result = []
        empty_skills = 6 - len(self._skills)
        new_skills_need = []
        freed_up = {}
        for perk in to_remove:
            skill = gg.info.perk2skill[perk]
            if skill not in freed_up:
                freed_up[skill] = 0
            freed_up[skill] += 1

        for skill in skill_need:
            if skill not in self._skills:
                new_skills_need.append(gg.info.skill_info[skill].name)
            else:
                slots_need = len(skill_need[skill]) + len(self._skills[skill][1]) - \
                    (freed_up[skill] if skill in freed_up else 0)
                max_slots = 4 if next(iter(self._skills.keys())) == skill else 3
                if slots_need > max_slots:
                    result.append(f"主技能{gg.info.skill_info[skill].name}空槽不够，即使专家级后"
                                  f"仍需要{len(skill_need[skill])}个额空槽来学习"
                                  "{}".format("、".join(gg.info.perk_info[p].name for p in skill_need[skill])))
        if empty_skills < len(new_skills_need):
            result.append(f"该英雄只有{empty_skills}主技能空槽，但是需要学习" + \
                          "{}".format("、".join(new_skills_need)) + \
                          f"这{len(new_skills_need)}个主技能")
        return result

    def slots22dtuple(self):
        skills = tuple((i, self._skills[i][0]) for i in self._skills)
        perks = tuple(tuple(self._skills[i][1]) for i in self._skills)
        return skills, perks

    def reload_skills(self, skills, perks):
        self._skills = {}
        self._perks_set = set()
        for skill in skills:
            self._skills[skill[0]] = [skill[1], []]

        for perk in perks:
            self._perks_set.add(perk)
            self._skills[gg.info.perk2skill[perk]][1].append(perk)

    def replace_skill(self, old_skill, skill, perks=None):
        # If old_skill is None, you are adding a new skill
        # If skill is None, you are removing a old skill
        # If perks is None, the number of perks may shrink.

        levels_added = 0
        levels_removed = 0

        if old_skill is None:
            if perks is None: perks = []
            levels_added = skill[1] + len(perks)
            self._skills[skill[0]] = [skill[1], perks]
        elif skill is None:
            levels_removed = self._skills[old_skill][0] + len(self._skills[old_skill][1])
            self._perks_set -= set(self._skills[old_skill][1])
            del self._skills[old_skill]
        elif old_skill is not None and skill is not None:
            if old_skill == skill[0]:
                if perks is not None:
                    self._skills[old_skill][1] = perks
                    levels_added += len(perks)
                    levels_removed += len(self._skills[old_skill][1])

                if self._skills[old_skill][0] < skill[1]:
                    levels_added += skill[1] - self._skills[old_skill][0]
                elif self._skills[old_skill][0] > skill[1]:
                    levels_removed += self._skills[old_skill][0] - skill[1]
                    to_remove = deepcopy(self._skills[old_skill][1])
                    for i in self._skills[old_skill][1]:
                        self._get_perk_full_list(i, True)

                self._skills[old_skill][0] = skill[1]
            else:
                levels_added = skill[1]
                levels_removed = self._skills[old_skill][0] + len(self._skills[old_skill][1])
                temp = list(self._skills.items())
                i = [i for i in range(len(temp)) if temp[i][0] == old_skill][0]
                temp[i] = [skill[0], [skill[1], []]]
                self._skills = OrderedDict(temp)

        self._level += levels_added - levels_removed

    def replace_perk(self, old_perk, perk):
        # If old_perk is None, you are adding a new perk
        # If perk is None, you are removing a old perk

        levels_added = 0
        levels_removed = 0

        if old_perk is not None:
            result = self._get_perk_full_list(old_perk, False)
            result = set(result).intersection(self._skills[gg.info.perk2skill[old_perk]][1])
            result.add(old_perk)
            levels_removed += len(result)
            for i in result:
                self._perks_set.remove(i)
                self._skills[gg.info.perk2skill[i]][1].remove(i)

        if perk is not None:
            result = self._get_skill_need(perk)
            for s, ps in result.items():
                levels_added += len(ps)
                self._perks_set.update(ps)
                if s not in self._skills:
                    temp = 0
                    self._skills[s] = [max(len(ps), 1), []]
                else:
                    temp = self._skills[s][0]

                self._skills[s][1] += list(ps)
                self._skills[s][0] = min(len(self._skills[s][1]), 3)
                levels_added += self._skills[s][0] - temp

        self._level += levels_added - levels_removed

    def compromise(self, master):
        pass

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

    def get_select_perks(self, sid, pid=None):
        standard = list(set(gg.info.class2skill[self._race][sid][0]) - set(self._skills[sid][1]) - {pid, })
        special = set(gg.info.class2skill[self._race][sid][1]) - set(self._skills[sid][1]) - {pid, }
        if pid is not None:
            standard.insert(0, None)
        unlearnable = []
        reasons = []

        for id in special:
            skill_need = self._get_skill_need(id)
            reason = self._can_accept_skills(skill_need, pid)
            if len(reason) > 0:
                unlearnable.append(id)
                reasons.append(reason)
        special -= set(unlearnable)
        special = list(special)
        return standard, special, unlearnable, reasons

    def get_levelup_perks(self):
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