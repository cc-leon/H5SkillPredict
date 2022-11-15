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
        self._history = []

    def __str__(self):
        return "L{}--{}\n  {}".format(
            self._level, gg.info.hero_info[self._id].name,
            "\n  ".join(Hero._output_line(i, lambda x: gg.info.skill_info[x].name,
                                          lambda x: gg.info.perk_info[x].name)
                        for i in self._skills.items()))

    def __repr__(self):
        return "L{}--{}\n{}".format(
            self._level, self._id,
            "\n".join(Hero._output_line(i, lambda x: x.split("HERO_SKILL_")[1]) for i in self._skills.items()))

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

    def _get_keys(self):
        return frozenset(self._perks_set), \
            frozenset(zip(self._skills.keys(), tuple(self._skills[i][0] for i in self._skills)))

    def __hash__(self):
        return hash(self._get_keys())

    def __eq__(self, other):
        return self._get_keys() == other._get_keys()

    def __ge__(self, other):
        return self._perks_set >= other._perks_set and set(self._skills.keys()) >= set(other._skills.keys()) and \
            all(self._skills[i][0] >= other._skills[i][0] for i in self._skills if i in other._skills)

    def __le__(self, other):
        return self._perks_set <= other._perks_set and set(self._skills.keys()) <= set(other._skills.keys()) and \
            all(self._skills[i][0] <= other._skills[i][0] for i in self._skills if i in other._skills)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.__ge__(other) and self.__ne__(other)

    def __lt__(self, other):
        return self.__le__(other) and self.__ne__(other)

    @staticmethod
    def _calc_prob(items, target, tries=1, prob_mat=None):
        result = 0
        print(items)
        if prob_mat is None:
            result = 1/len(items)
            return result + (0 if tries == 1 else (1-result) * 1/(len(items) - 1))
        else:
            result = prob_mat[items.index(target)] / sum(prob_mat)
            print(result)
            return result + \
                (sum(Hero._calc_prob(items, i, prob_mat=prob_mat) *
                     Hero._calc_prob(
                        [j for j in items if j != i], target,
                        prob_mat=[prob_mat[j] for j in range(len(prob_mat)) if j != items.index(i)])
                 for i in items if i != target) if tries != 1 else 0)

    @staticmethod
    def _output_line(line, sfunc, pfunc):
        sid, (mastery, perks) = line
        return "{}-{}: [{}]".format(sfunc(sid), mastery, ", ".join(pfunc(i) for i in perks))

    @staticmethod
    def _list_num_perks(perk_list):
        return len([i for i in perk_list if gg.info.perk_info[i].typ != "SKILLTYPE_UINQUE_PERK"])

    def _self_num_perks(self, skill_id):
        if skill_id not in self._skills:
            return None
        else:
            result = len([i for i in self._skills[skill_id][1] if gg.info.perk_info[i].typ != "SKILLTYPE_UINQUE_PERK"])
            return result

    def _build_remove_order(self, skill):
        result = []
        remaining = [i for i in self._skills[skill][1] if gg.info.perk_info[i].typ != "SKILLTYPE_UINQUE_PERK"]
        i = -1
        while len(remaining) > 0:
            if len(set(self._get_perk_full_list(remaining[i], False)).intersection(remaining)) == 0:
                result.append(remaining[i])
                del remaining[i]
                i = -1
            else:
                i -= 1
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
            if is_preq is True:
                result = temp + result
            else:
                result += temp
        return result

    def _get_skill_need(self, perk):
        preqs = self._get_perk_full_list(perk, True)
        skill_need = {}
        for preq in preqs:
            if preq not in self._perks_set:
                skill_id = gg.info.perk2skill[preq]
                if skill_id not in skill_need:
                    skill_need[skill_id] = []
                skill_need[skill_id].append(preq)
        if gg.info.perk2skill[perk] not in skill_need:
            skill_need[gg.info.perk2skill[perk]] = []
        skill_need[gg.info.perk2skill[perk]].append(perk)
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
                    result.append("需要学习子技能{}，主技能{}空槽不够".format(
                        "、".join(gg.info.perk_info[p].name for p in skill_need[skill]),
                        gg.info.skill_info[skill].name))
        if empty_skills < len(new_skills_need):
            result.append(f"该英雄只有{empty_skills}主技能空槽，但是需要学习" +
                          "{}".format("、".join(new_skills_need)) +
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
            if perks is None:
                perks = []
            levels_added = skill[1] + len(perks)
            self._skills[skill[0]] = [skill[1], perks]
        elif skill is None:
            levels_removed = self._skills[old_skill][0]
            to_remove = self._build_remove_order(old_skill)
            for i in to_remove:
                self.replace_perk(i, None)
            del self._skills[old_skill]
        elif old_skill is not None and skill is not None:
            if perks is not None:
                self._skills[old_skill][1] = perks
                levels_added += len(perks)
                levels_removed += len(self._skills[old_skill][1])

            if old_skill == skill[0]:
                if self._skills[old_skill][0] < skill[1]:
                    levels_added += skill[1] - self._skills[old_skill][0]
                elif self._skills[old_skill][0] > skill[1]:
                    levels_removed += self._skills[old_skill][0] - skill[1]
                    if perks is None:
                        num_perks_to_remove = self._self_num_perks(old_skill) - skill[1]
                        if num_perks_to_remove > 0:
                            to_remove = self._build_remove_order(old_skill)
                            for i in to_remove[:num_perks_to_remove]:
                                self.replace_perk(i, None)
                self._skills[old_skill][0] = skill[1]
            else:
                levels_added = skill[1]
                levels_removed = self._skills[old_skill][0]
                for i in self._build_remove_order(old_skill):
                    self.replace_perk(i, None)
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
            result = set(result).intersection(self._perks_set)
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

                self._skills[s][1].extend(list(ps))
                if self._skills[s][0] < len(self._skills[s][1]):
                    self._skills[s][0] = min(len(self._skills[s][1]), 3)
                levels_added += self._skills[s][0] - temp

        self._level += levels_added - levels_removed

    def compromise(self, other, is_src):
        if is_src is True:
            other._level = self._level
            o_skills, o_perks = other.slots22dtuple()
            skills, perks = self.slots22dtuple()
            other.reload_skills(skills, [item for sublist in perks for item in sublist])

            for sid, slvl in o_skills:
                if len(other._skills) >= 6:
                    break
                skill = (sid, max(other._skills[sid][0], slvl) if sid in other._skills else slvl)
                other.replace_skill(sid if sid in other._skills else None, skill, None)

            for perks in o_perks:
                for pid in perks:
                    if pid not in other._perks_set:
                        skill_need = other._get_skill_need(pid)
                        if len(other._can_accept_skills(skill_need, None)) == 0:
                            other.replace_perk(None, pid)
        else:
            to_remove = {}
            for i in other._perks_set - self._perks_set:
                if gg.info.perk2skill[i] not in to_remove:
                    to_remove[gg.info.perk2skill[i]] = []
                to_remove[gg.info.perk2skill[i]].append(i)
            for s, ps in to_remove.items():
                temp = other._build_remove_order(s)
                temp = [i for i in temp if i in ps]
                for p in temp:
                    other.replace_perk(p, None)
            for sid, (mastery, perks) in tuple(other._skills.items()):
                self_sid = None
                if sid in self._skills:
                    self_sid = [sid, min(self._skills[sid][0], mastery)]
                other.replace_skill(sid, self_sid, None)

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

    def get_select_perks(self, sid, pid=None):
        remove = []
        standard = list(set(gg.info.class2skill[self._race][sid][0]) - set(self._skills[sid][1]) - {pid, })
        special = set(gg.info.class2skill[self._race][sid][1]) - set(self._skills[sid][1]) - {pid, }
        if pid is not None:
            remove.append(True)
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

        return remove, standard, special, unlearnable, reasons

    def get_levelup_skills(self):
        if len(self._skills) == 6:
            new = []
            new_probs = []
        else:
            new = [i for i in gg.info.class2skill[self._race] if i not in self._skills]
            new_probs = [gg.info.skill_prob[self._race][i]
                         for i in gg.info.class2skill[self._race] if i not in self._skills]

        old = [i for i in self._skills if self._skills[i][0] < 3]
        return new, new_probs, old

    def get_levelup_perks(self):
        special = []
        standard = []
        for sid, (mastery, perks) in self._skills.items():
            if mastery > len(perks):
                standard.extend([i for i in gg.info.class2skill[self._race][sid][0] if i not in self._perks_set])
                special.extend([i for i in gg.info.class2skill[self._race][sid][1]
                                if i not in self._perks_set and
                                gg.info.perk_info[i].preq[self._race].issubset(self._perks_set)])
            elif mastery == len(perks) and sid == next(iter(self._skills.keys())):
                special.extend([i for i in gg.info.class2skill[self._race][sid][1]
                                if i not in self._perks_set and
                                gg.info.perk_info[i].preq[self._race].issubset(self._perks_set) and
                                gg.info.perk_info[i].typ == "SKILLTYPE_UINQUE_PERK"])
        return standard, special

    def levelup(self, id):
        result = deepcopy(self)
        if id in gg.info.skill_info:
            if id not in result._skills:
                result._skills[id] = [1, []]
            else:
                result._skills[id][0] += 1
        else:
            result._perks_set.add(id)
            result._skills[gg.info.perk2skill[id]][1].append(id)

        result._level += 1
        result._history.append(id)
        return result

    def leveldown(self):
        if len(result._history) == 0:
            return None
        result = deepcopy(self)
        id = result._history.pop()
        result._level -= 1
        if id in gg.info.skill_info:
            if result._skills[id][0] == 1:
                del result._skills[id]
            else:
                result._skills[id][0] -= 1
        else:
            result._perks_set.remove(id)
            result._skills[gg.info.perk2skill[id]][1].remove(id)
        return result

    def calculate(self, dst, buffer_level=0, new_skills=True):
        print(Hero._calc_prob(list(range(10)), 1, tries=2))
        items = ["cat", "dog", "pig"]
        prob = [2, 1, 1]
        print(Hero._calc_prob(items, "cat", 2, prob))

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
