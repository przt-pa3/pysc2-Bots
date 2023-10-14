__author__ = 'Gwoo, Hong'

import math

import time

import numpy as np

import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from sc2.data import Alert


class Bot(sc2.BotAI):
    """
    빌드 오더 대신, 유닛 비율을 맞추도록 유닛을 생산함
    개별 전투 유닛이 적사령부에 바로 공격하는 대신, 15이 모일 때까지 대기
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        # self.plan: "BuildOrder" = None
        # self.knowledge = Knowledge()
        self.last_game_loop = -1

    def on_start(self):
        """
        새로운 게임마다 초기화
        """
        print("ver_0131_2325_mana")
        self.game_time = 0
        self.game_start_time = self.time
        self.accum_min = 0
        self.accum_gas = 0

        self.unit_cost_data = dict()

        self.unit_cost_data[UnitTypeId.MARINE] = [50,0]
        self.unit_cost_data[UnitTypeId.MARAUDER] = [100, 25]
        self.unit_cost_data[UnitTypeId.REAPER] = [50, 50]
        self.unit_cost_data[UnitTypeId.GHOST] = [150, 125]
        self.unit_cost_data[UnitTypeId.HELLION] = [100, 0]
        self.unit_cost_data[UnitTypeId.SIEGETANK] = [150, 125]
        self.unit_cost_data[UnitTypeId.SIEGETANKSIEGED] = [150, 125]
        self.unit_cost_data[UnitTypeId.THOR] = [300, 200]
        self.unit_cost_data[UnitTypeId.THORAP] = [300, 200]
        self.unit_cost_data[UnitTypeId.MEDIVAC] = [100, 100]
        self.unit_cost_data[UnitTypeId.VIKINGFIGHTER] = [150, 75]
        self.unit_cost_data[UnitTypeId.VIKINGASSAULT] = [150, 75]
        self.unit_cost_data[UnitTypeId.BANSHEE] = [150, 100]
        self.unit_cost_data[UnitTypeId.RAVEN] = [100, 200]
        self.unit_cost_data[UnitTypeId.BATTLECRUISER] = [400, 300]
        self.unit_cost_data[UnitTypeId.AUTOTURRET] = [0, 0]
        self.unit_cost_data[UnitTypeId.MULE] = [0, 0]
        self.unit_cost_data[UnitTypeId.NUKE] = [100, 100]

        self.side = 0
        # 1 : Left(our)
        # -1 : Right(our)

        # (32.5, 31.5) or (95.5, 31.5)
        if self.start_location.distance_to(Point2((32.5, 31.5))) < 5.0:
            self.enemy_cc = Point2(Point2((95.5, 31.5)))  # 적 시작 위치
            self.defense_line = 63
            #self.defense_line = 68
            # Defense_Line - 7 : 탱크 최대사정거리
            # Defense_Line - 20 : 탱크 위치
            # Defense_Line - 3 : 공중 최대사정거리
            # Defense_Line - 12 : 공중 위치
            self.side = 1
        else:
            self.enemy_cc = Point2(Point2((32.5, 31.5)))  # 적 시작 위치
            self.defense_line = 66
            self.side = -1

        self.enemy_close_counter = 0

        self.defense_radius = 20

        self.combat_controller = dict()
        self.move_controller = dict()

        self.is_combat = 0

        self.evoked = dict()
        self.battlecruiser_position = dict()

        self.marine_position = dict()
        self.marine_pos_num = dict()

        self.tank_position = dict()
        self.tank_pos_num = dict()

        self.thor_pos_num = dict()
        self.thor_position = dict()

        self.raven_pos_num = dict()
        self.raven_tactic = 1
        self.raven_target = dict()
        self.raven_ability_time = dict()
        self.raven_move_time = dict()

        self.banshee_pos_num = dict()

        self.hellion_pos_num = dict()
        self.hellion_position = dict()

        self.viking_pos_num = dict()
        self.viking_position = dict()

        self.unit_dict = dict()
        self.enemy_unit_dict = dict()
        self.enemy_counter = dict()

        self.enemy_death_min = 0
        self.enemy_death_gas = 0

        self.my_death_min = 0
        self.my_death_gas = 0

        self.enemy_counter[UnitTypeId.MARINE] = 0
        self.enemy_counter[UnitTypeId.SIEGETANK] = 0
        self.enemy_counter[UnitTypeId.SIEGETANKSIEGED] = 0
        self.enemy_counter[UnitTypeId.RAVEN] = 0
        self.enemy_counter[UnitTypeId.BATTLECRUISER] = 0
        self.enemy_counter[UnitTypeId.VIKINGFIGHTER] = 0
        self.enemy_counter[UnitTypeId.VIKINGASSAULT] = 0
        self.enemy_counter[UnitTypeId.MEDIVAC] = 0
        self.enemy_counter[UnitTypeId.HELLION] = 0
        self.enemy_counter[UnitTypeId.BANSHEE] = 0
        self.enemy_counter[UnitTypeId.GHOST] = 0
        self.enemy_counter[UnitTypeId.THOR] = 0
        self.enemy_counter[UnitTypeId.THORAP] = 0
        self.enemy_counter[UnitTypeId.MARAUDER] = 0
        self.enemy_counter[UnitTypeId.REAPER] = 0
        self.enemy_counter[UnitTypeId.MULE] = 0
        self.enemy_counter[UnitTypeId.AUTOTURRET] = 0
        self.enemy_counter[UnitTypeId.NUKE] = 0

        self.test_tick = 0

        self.enemy_has_raven = 0
        self.cloaked_enemy = 0
        self.cloaked_enemy_position = list()

        self.combat_start_time = 0
        self.move_start_time = 0

        self.game_start_time = self.time

        self.gas_price_dict = dict()
        self.gas_price_dict[UnitTypeId.SIEGETANK] = 85
        self.gas_price_dict[UnitTypeId.RAVEN] = 175
        self.gas_price_dict[UnitTypeId.BATTLECRUISER] = 200
        self.gas_price_dict[UnitTypeId.VIKINGFIGHTER] = 35
        self.gas_price_dict[UnitTypeId.BANSHEE] = 60
        self.gas_price_dict[UnitTypeId.GHOST] = 85
        self.gas_price_dict[UnitTypeId.NUKE] = 75
        self.gas_price_dict[UnitTypeId.MEDIVAC] = 75
        self.gas_price_dict[UnitTypeId.MARINE] = 0
        self.gas_price_dict[UnitTypeId.HELLION] = 0
        self.gas_price_dict[UnitTypeId.THOR] = 125

        self.gas_unit_build = list()

        self.gas_unit_build.append(UnitTypeId.BANSHEE)
        self.gas_unit_build.append(UnitTypeId.RAVEN)
        self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
        self.gas_unit_build.append(UnitTypeId.SIEGETANK)


        self.min_unit_build = list()

        self.min_unit_build.append(UnitTypeId.HELLION)
        self.min_unit_build.append(UnitTypeId.HELLION)
        self.min_unit_build.append(UnitTypeId.HELLION)
        self.min_unit_build.append(UnitTypeId.HELLION)
        self.min_unit_build.append(UnitTypeId.HELLION)

        self.move_adjust = dict()
        self.move_adjust[UnitTypeId.BANSHEE] = 5
        self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 5
        self.move_adjust[UnitTypeId.MARINE] = 4
        self.move_adjust[UnitTypeId.HELLION] = 6
        self.move_adjust[UnitTypeId.RAVEN] = 5


        self.unit_build_phase = 0

        self.defense_line_modi_time = 0

        self.bv_harass_bond = [0,0]
        self.banshee_harass_switch = 0

        self.enemy_strategy = 1

        self.end_game_time = 0
        self.enemy_tp = 0
        self.enemy_tp_time = 0
        self.tacnuke = 0

        self.emp_target_dict = dict()
        self.enemy_nuke_alert = 0
        self.enemy_nuke_alert_time = 0
        self.enemy_nuke_position = Point2((30, 30))
        self.enemy_nuke_tactic = 0

        self.ghost_build_time = 0
        self.raven_build_time = 0
        self.banshee_build_time = 0
        self.enemy_nuke_boom_time = 0

        self.need_kill_ghost = 0
        self.rav_ghost_mat = 0

        self.my_nuke_build_time = 0
        self.my_nuke_launch_time = 0
        self.enemy_close_tank_counter = 0
        self.moving_line = [0,0]

        self.enemy_line_tick = [0,0,0,0,0]
        self.is_enemy_rush = 0
        self.line_break_time = 0

        self.raven_matrix_target = list()
        self.raven_matrix_time = dict()
        self.nuke_ghost_maginot = 8
        self.find_nuke_maginot = 14
        self.nuke_kill = 0
        self.nuke_kill_gas1 = 0
        self.nuke_kill_gas0 = 0
        self.nuke_kill_min1 = 0
        self.nuke_kill_min0 = 0
        self.before_nuke_position = Point2((0,0))
        self.allin_tp_time = 250
        self.enemy_can_tp = 0
        self.enemy_tp_position = Point2((0,0))
        self.enemy_is_MARAUDER = 0
    async def on_step(self, iteration: int):
        """

        """


        self.game_time = self.time - self.game_start_time
        self.accum_gas = round(self.game_time) * 7
        self.accum_min = round(self.game_time) * 28

        #print((self.tacnuke, self.defense_line, self.enemy_tank_line(), self.enemy_ground_line(), self.enemy_strategy, self.unit_build_phase))
        #print((self.tacnuke))

        ally_cc = self.start_location
        # print(self.enemy_counter[UnitTypeId.MARINE])
        # print(self.state.score.total_damage_dealt_life)
        actions = list()  # 이번 step에 실행할 액션 목록
        enemy_cc = self.enemy_cc
        ccs = self.units(UnitTypeId.COMMANDCENTER).idle
        combat_units = self.units.exclude_type([UnitTypeId.COMMANDCENTER, UnitTypeId.MEDIVAC, UnitTypeId.MULE])

        wounded_mech_units = self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED, UnitTypeId.RAVEN, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BANSHEE]).filter(
            lambda u: u.health_percentage < 1.0
        )
        wounded_bio_units = self.units.filter(
            lambda u: u.is_biological and u.health_percentage < 1.0
        )  # 체력이 100% 이하인 유닛 검색
        if self.accum_gas - self.enemy_death_gas > 1500:
            self.enemy_can_tp = 1
        else:
            self.enemy_can_tp = 0

        # 상대 빌드 평가 ( 공중 중심 0 <-> 지상 중심 1)
        if (self.accum_gas - self.enemy_death_gas) > 0:
            enemy_air_gas = (self.enemy_counter[UnitTypeId.BATTLECRUISER] * self.unit_cost_data[UnitTypeId.BATTLECRUISER][1] +
                self.enemy_counter[UnitTypeId.BANSHEE] * self.unit_cost_data[UnitTypeId.BANSHEE][1] + self.enemy_counter[
                    UnitTypeId.VIKINGFIGHTER] * self.unit_cost_data[UnitTypeId.VIKINGFIGHTER][1] + self.enemy_counter[
                    UnitTypeId.VIKINGASSAULT] * self.unit_cost_data[UnitTypeId.VIKINGFIGHTER][1]) / (
                    self.accum_gas - self.enemy_death_gas)
            enemy_ground_gas = (self.enemy_counter[UnitTypeId.SIEGETANK] * self.unit_cost_data[UnitTypeId.SIEGETANK][1] +
                self.enemy_counter[UnitTypeId.SIEGETANKSIEGED] * self.unit_cost_data[UnitTypeId.SIEGETANK][1] + self.enemy_counter[
                    UnitTypeId.MARAUDER] * self.unit_cost_data[UnitTypeId.MARAUDER][1] + self.enemy_counter[
                    UnitTypeId.THOR] * self.unit_cost_data[UnitTypeId.THOR][1] + self.enemy_counter[UnitTypeId.REAPER] * self.unit_cost_data[UnitTypeId.REAPER][1] + self.enemy_counter[UnitTypeId.MEDIVAC] * self.unit_cost_data[UnitTypeId.MEDIVAC][1]) / (
                    self.accum_gas - self.enemy_death_gas)
            if enemy_air_gas < enemy_ground_gas:
                self.enemy_strategy = 0
            else:
                self.enemy_strategy = 1
        else:
            pass

        if self.enemy_counter[UnitTypeId.MARAUDER] > 7:
            self.enemy_is_MARAUDER = 1
        else:
            pass

        # 빌드 페이즈 : 상대 공중 중심 <-> 상대 지상 중심 변환 매끄럽지 않음
        if self.unit_build_phase == 0:
            if (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount >= 2) and (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount >= 4):
                self.unit_build_phase = 1
            else:
                pass
        elif self.unit_build_phase == 1:
            if (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 2) or (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 4):
                self.unit_build_phase = 0
            elif (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount >= 4) and (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount >= 8):
                self.unit_build_phase = 2
            elif (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount >= 7) and (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount >= 5):
                self.unit_build_phase = 20
        elif self.unit_build_phase == 2:
            if (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 4) or (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 10):
                self.unit_build_phase = 1
            elif (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount >= 5) and (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount >= 12) and (
                    self.units.of_type([UnitTypeId.THOR]).amount >= 1):
                self.unit_build_phase = 3
            else:
                pass
        elif self.unit_build_phase == 3:
            if (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 5) or (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 12) or (
                    self.units.of_type([UnitTypeId.THOR]).amount < 1):
                self.unit_build_phase = 2
        elif self.unit_build_phase == 20:
            if (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 7) or (
                    self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 5):
                self.unit_build_phase = 1

        cc = self.units(UnitTypeId.COMMANDCENTER).closest_to(ally_cc)
        # 가스 유닛 빌드
        if len(self.gas_unit_build) < 1 and self.time - self.evoked[(cc.tag, 'train')] > 1:
            if self.unit_build_phase == 0:
                if self.enemy_strategy == 0:
                    if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 2:
                        self.gas_unit_build.append(UnitTypeId.SIEGETANK)
                    else:
                        self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                else:
                    if self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 4:
                        if self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 1:
                            self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                        else:
                            if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 1:
                                self.gas_unit_build.append(UnitTypeId.SIEGETANK)
                            else:
                                self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                    else:
                        if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount >= 2:
                            self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                        else:
                            self.gas_unit_build.append(UnitTypeId.SIEGETANK)
            elif self.unit_build_phase == 1:
                if self.enemy_strategy == 0:
                    if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 7:
                        self.gas_unit_build.append(UnitTypeId.SIEGETANK)
                    else:
                        self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                else:
                    if self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 8:
                        if self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 4:
                            self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                        else:
                            if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 3:
                                self.gas_unit_build.append(UnitTypeId.SIEGETANK)
                            else:
                                self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                    else:
                        self.gas_unit_build.append(UnitTypeId.SIEGETANK)
            elif self.unit_build_phase == 2:
                if self.units.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.VIKINGASSAULT]).amount < 12:
                    self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
                else:
                    if self.units.of_type([UnitTypeId.THOR, UnitTypeId.THORAP]).amount < 1:
                        self.gas_unit_build.append(UnitTypeId.THOR)
                    else:
                        if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount < 5:
                            self.gas_unit_build.append(UnitTypeId.SIEGETANK)
                        else:
                            self.gas_unit_build.append(UnitTypeId.VIKINGFIGHTER)
            else:
                pass
        else:
            pass

        # 고스트
        if (self.unit_build_phase > 0) and (self.game_time > 100) and (self.units.of_type(
                [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount > 2) and (self.units.of_type(
                [UnitTypeId.VIKINGASSAULT, UnitTypeId.VIKINGFIGHTER]).amount > 3):
            if self.units(UnitTypeId.GHOST).amount == 0:
                if len(self.gas_unit_build) > 0:
                    ghost_in_queue = 0
                    for list_i in range(len(self.gas_unit_build)):
                        if self.gas_unit_build[list_i] == UnitTypeId.GHOST:
                            ghost_in_queue = 1
                        else:
                            pass
                    if ghost_in_queue == 0:
                        if self.time - self.ghost_build_time > 25:
                            print("GHOST ADDED")
                            self.gas_unit_build.insert(0, UnitTypeId.GHOST)
                            self.ghost_build_time = self.time
                        else:
                            pass
                    else:
                        pass
                else:
                    if self.time - self.ghost_build_time > 25:
                        self.gas_unit_build.insert(0, UnitTypeId.GHOST)
                        self.ghost_build_time = self.time
                    else:
                        pass
            else:
                pass
        else:
            pass

        # 밴시
        if (self.unit_build_phase > 0) and (self.game_time > 280) and (self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount > 2):
            if self.units(UnitTypeId.BANSHEE).amount == 0:
                if len(self.gas_unit_build) > 0:
                    banshee_in_queue = 0
                    for list_i in range(len(self.gas_unit_build)):
                        if self.gas_unit_build[list_i] == UnitTypeId.BANSHEE:
                            banshee_in_queue = 1
                        else:
                            pass
                    if banshee_in_queue == 0:
                        if self.time - self.banshee_build_time > 40:
                            print("BANSHEE ADDED")
                            self.gas_unit_build.insert(0, UnitTypeId.BANSHEE)
                            self.banshee_build_time = self.time
                        else:
                            pass
                    else:
                        pass
                else:
                    if self.time - self.banshee_build_time > 40:
                        self.gas_unit_build.insert(0, UnitTypeId.BANSHEE)
                        self.banshee_build_time = self.time
                    else:
                        pass
            else:
                pass
                # 핵 생산
        else:
            pass

        if self.time - self.my_nuke_launch_time <0.5:
            self.nuke_kill_min0 = self.enemy_death_min
            self.nuke_kill_gas0 = self.enemy_death_gas

        if 13 < self.time - self.my_nuke_launch_time < 16:
            self.nuke_kill_min1 = self.enemy_death_min
            self.nuke_kill_gas1 = self.enemy_death_gas

        self.nuke_kill_min = self.nuke_kill_min1 - self.nuke_kill_min0
        self.nuke_kill_gas = self.nuke_kill_gas1 - self.nuke_kill_gas0

        # 밤까 보충
        if 200 > self.game_time and self.game_time > 70:
            if self.units(UnitTypeId.RAVEN).amount == 0:
                if len(self.gas_unit_build) > 0:
                    raven_in_queue = 0
                    for list_i in range(len(self.gas_unit_build)):
                        if self.gas_unit_build[list_i] == UnitTypeId.RAVEN:
                            raven_in_queue = 1
                        else:
                            pass

                    if raven_in_queue == 0:
                        if self.time - self.raven_build_time > 40:
                            self.gas_unit_build.insert(0, UnitTypeId.RAVEN)
                            self.raven_build_time = self.time
                        else:
                            pass
                    else:
                        pass
                else:
                    if self.time - self.raven_build_time > 40:
                        self.gas_unit_build.insert(0, UnitTypeId.RAVEN)
                        self.raven_build_time = self.time
                    else:
                        pass
            else:
                pass
        else:
            if self.game_time > 200:
                if self.units(UnitTypeId.RAVEN).amount < 2:
                    if len(self.gas_unit_build) > 0:
                        raven_in_queue = 0
                        for list_i in range(len(self.gas_unit_build)):
                            if self.gas_unit_build[list_i] == UnitTypeId.RAVEN:
                                raven_in_queue = 1
                            else:
                                pass

                        if raven_in_queue == 0:
                            if self.time - self.raven_build_time > 70:
                                self.gas_unit_build.insert(0, UnitTypeId.RAVEN)
                                self.raven_build_time = self.time
                            else:
                                pass
                        else:
                            pass
                    else:
                        if self.time - self.raven_build_time > 70:
                            self.gas_unit_build.insert(0, UnitTypeId.RAVEN)
                            self.raven_build_time = self.time
                        else:
                            pass
                else:
                    pass
            else:
                pass

        #print(self.raven_matrix_target)
        # 밤까 스킬 도우미
        del_list = list()
        for list_i in range(len(self.raven_matrix_target)):
            if self.time - self.raven_matrix_target[list_i][1] > 7.8:
                self.raven_matrix_target[list_i][0] = 0
            else:
                pass


        # 전술핵 공격 조정
        if self.tacnuke == 2 and self.units(UnitTypeId.NUKE).amount > 0:
            self.tacnuke = 0
        elif self.tacnuke == 1 and self.alert(Alert.NukeComplete) and self.is_combat != 2:
            self.tacnuke = 2
        elif self.tacnuke == 0 and self.time - self.my_nuke_launch_time > 30 and self.enemy_nuke_alert != 1 and self.is_combat != 2:
            if self.units(UnitTypeId.GHOST).amount > 0:
                if self.side == 1:
                    if self.defense_line > 92.8:
                        absol_nuke = 1
                    else:
                        absol_nuke = 0
                else:
                    if self.defense_line < 34.2:
                        absol_nuke = 1
                    else:
                        absol_nuke = 0
                nuke_target_count = 0

                if absol_nuke == 0:
                    if self.enemy_tank_line() != 999:
                        if self.side == 1:
                            nuke_point = Point2((self.defense_line - 8, 31.5))
                        else:
                            nuke_point = Point2((self.defense_line + 8, 31.5))
                    else:
                        if self.side == 1:
                            nuke_point = Point2((self.defense_line - 5, 31.5))
                        else:
                            nuke_point = Point2((self.defense_line + 5, 31.5))

                    if len(list(self.enemy_unit_dict.keys())) > 0:  # 전체 유닛으로
                        for enemy_ind_tag in list(self.enemy_unit_dict.keys()):
                            if Point2((self.enemy_unit_dict[enemy_ind_tag][1], self.enemy_unit_dict[enemy_ind_tag][2])).distance_to(nuke_point) < 7.8:
                                nuke_target_count += 1
                            else:
                                pass
                    else:
                        pass
                if absol_nuke == 1 or nuke_target_count > 5:
                    self.tacnuke = 1
                else:
                    pass
            else:
                pass # No GHOST

        # 미네랄 유닛 (마린/화염차) 빌드 : Base 마린 -> Hellion 이 리스트에 있을 때 Hellion => 수정필요
        # 1 적 공중, 0 적 지상
        if len(self.min_unit_build) < 1 and self.time - self.evoked[(cc.tag, 'train')] > 1:
            if self.units(UnitTypeId.SIEGETANKSIEGED).amount < 2:
                if self.enemy_strategy == 0:
                    if self.enemy_counter[UnitTypeId.MARAUDER] < 1:
                        self.min_unit_build.append(UnitTypeId.HELLION)
                    else:
                        pass
                else:
                    if self.units(UnitTypeId.MARINE).amount < 5 and self.units(UnitTypeId.HELLION).amount < 3:
                        self.min_unit_build.append(UnitTypeId.HELLION)
                    else:
                        pass
            else:
                if self.enemy_strategy == 0:
                    if self.units(UnitTypeId.MARINE).amount > 50:
                        self.min_unit_build.append(UnitTypeId.HELLION)
                    else:
                        pass
                else:
                    if self.units(UnitTypeId.MARINE).amount > 74:
                        self.min_unit_build.append(UnitTypeId.HELLION)
                    else:
                        pass
        else:
            pass

        # 커맨드 명령 생성 ( MULE 소환, 병력 생산 )
        if ccs.exists:
            cc = ccs.first
            
            # MULE 소환 - 수정할 것 초반에 너무 많이 떨어짐
            if self.enemy_tp == 1:
                if cc.energy > 100:
                    if self.side == 1:
                        if self.time - self.enemy_tp_time > 9:
                            actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((29.5, 29.5))))
                    else:
                        if self.time - self.enemy_tp_time > 9:
                            actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((98.5, 29.5))))
                else:
                    pass
            else:
                if cc.energy > 100 and cc.health_percentage < 0.8 and self.units(UnitTypeId.MULE).amount < 1:
                    if self.side == 1:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((29.5, 29.5))))
                    else:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((98.5, 29.5))))
                elif cc.energy > 50 and cc.health_percentage < 0.35:
                    if self.side == 1:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((29.5, 29.5))))
                    else:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2((98.5, 29.5))))
                else:
                    if self.units(UnitTypeId.BANSHEE).exists:
                        bs = self.units(UnitTypeId.BANSHEE).closest_to(ally_cc)
                        if bs.health_percentage < 1.0 and bs.distance_to(Point2((self.defense_line - self.side*20,31.5))) > 10:
                            bs_no_repair = 1
                        else:
                            bs_no_repair = 0
                    else:
                        bs_no_repair = 0

                    if cc.energy > 100 and wounded_mech_units.exists and bs_no_repair == 0:
                        if self.game_time < 130:
                            repair_cool = 40
                        else:
                            repair_cool = 40
                        if self.time - self.evoked.get((cc.tag, 'repair'), 0) > repair_cool and self.units(UnitTypeId.MULE).amount < 2:
                            actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target=Point2(((self.defense_line - self.side * 22), 30))))
                            self.evoked[(cc.tag, 'repair')] = self.time
                        else:
                            pass
                    else:
                        pass

            if len(self.gas_unit_build) > 0:
                next_unit = self.gas_unit_build[0]
            else:
                if len(self.min_unit_build) > 0:
                    next_unit = self.min_unit_build[0]
                else:
                    next_unit = UnitTypeId.MARINE

            if len(self.min_unit_build) > 0:
                next_min_unit = self.min_unit_build[0]
            else:
                next_min_unit = UnitTypeId.MARINE

            # 유닛 생산
            if self.tacnuke != 1 or self.vespene < 75:
                if self.vespene >= self.gas_price_dict[next_unit]:
                    if self.can_afford(next_unit) and self.time - self.evoked.get((cc.tag,'train'), 0) > 1.0:
                        actions.append(cc.train(next_unit))
                        if len(self.gas_unit_build) > 0:
                            if self.gas_unit_build[0] == next_unit:
                                self.gas_unit_build.pop(0)
                            else:
                                pass
                        elif len(self.min_unit_build) > 0:
                            if self.min_unit_build[0] == next_unit:
                                pass
                        else:
                            pass
                        self.evoked[(cc.tag, 'train')] = self.time
                    else:
                        pass
                else:
                    if self.can_afford(next_min_unit) and self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 and self.supply_left > 20:
                        # 인구수 조건 넣기
                        actions.append(cc.train(next_min_unit))
                        if len(self.min_unit_build) > 0:
                            self.min_unit_build.pop(0)
                        else:
                            pass
                        self.evoked[(cc.tag, 'train')] = self.time
                    else:
                        pass
            else:
                if self.vespene >= 100 and self.minerals >= 100:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc(AbilityId.BUILD_NUKE))
                        self.evoked[(cc.tag, 'train')] = self.time
                        self.my_nuke_build_time = self.time
                    else:
                        pass
                else:
                    pass

        self.enemy_close_counter = 0
        self.enemy_close_tank_counter = 0
        self.cloaked_enemy = 0
        self.need_kill_ghost = 0

        enemy_tp_counter = 0
        # 적 유닛 총 카운트, 클록 유닛 감지, 차원도약 대응
        if self.known_enemy_units.not_structure.exists:
            for enemy_ind in self.known_enemy_units.not_structure:
                if self.side == 1:
                    if enemy_ind.type_id == UnitTypeId.GHOST:
                        if enemy_ind.position.y > 58 or enemy_ind.position.y < 5:
                            ghost_dead_line = 0
                        else:
                            if self.game_time < 120:
                                ghost_dead_line = 4
                            else:
                                ghost_dead_line = 8

                        if enemy_ind.position.x < self.defense_line - ghost_dead_line:
                            self.need_kill_ghost = 1
                        else:
                            pass
                    else:
                        if enemy_ind.position.x < self.defense_line - 12 and enemy_ind.position.x >= self.defense_line - 21:
                            self.enemy_close_counter += 1
                        elif (enemy_ind.type_id == UnitTypeId.SIEGETANK or enemy_ind.type_id == UnitTypeId.SIEGETANKSIEGED) and enemy_ind.position.x < self.defense_line - 7:
                            self.enemy_close_tank_counter += 1
                        elif enemy_ind.position.x < self.defense_line - 21:
                            if enemy_ind.type_id == UnitTypeId.BATTLECRUISER:
                                enemy_tp_counter += 1
                                self.enemy_tp_position = enemy_ind.position
                            else:
                                self.enemy_close_counter += 1
                        else:
                            pass
                else:
                    if enemy_ind.type_id == UnitTypeId.GHOST:
                        if enemy_ind.position.y > 58 or enemy_ind.position.y < 5:
                            ghost_dead_line = 0
                        else:
                            if self.game_time < 120:
                                ghost_dead_line = 4
                            else:
                                ghost_dead_line = 8

                        if enemy_ind.position.x > self.defense_line + ghost_dead_line:
                            self.need_kill_ghost = 1
                        else:
                            pass
                    else:
                        if enemy_ind.position.x > self.defense_line + 12 and enemy_ind.position.x <= self.defense_line + 21:
                            self.enemy_close_counter += 1
                        elif (enemy_ind.type_id == UnitTypeId.SIEGETANK or enemy_ind.type_id == UnitTypeId.SIEGETANKSIEGED) and enemy_ind.position.x > self.defense_line + 7:
                            self.enemy_close_tank_counter += 1
                        elif enemy_ind.position.x > self.defense_line + 21:
                            if enemy_ind.type_id == UnitTypeId.BATTLECRUISER:
                                enemy_tp_counter += 1
                                self.enemy_tp_position = enemy_ind.position
                            else:
                                self.enemy_close_counter += 1
                        else:
                            pass

                if enemy_ind.tag in list(self.enemy_unit_dict.keys()):
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x,
                                                           enemy_ind.position.y]
                else:
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x,
                                                           enemy_ind.position.y]
                    self.enemy_counter[self.enemy_unit_dict[enemy_ind.tag][0]] += 1

                if enemy_ind.is_cloaked == True:
                    if self.game_time < 120:
                        if enemy_ind.type_id == UnitTypeId.GHOST:
                            cloak_maginot = 4
                        else:
                            cloak_maginot = 8
                    else:
                        cloak_maginot = 8
                    if self.side == 1:
                        if enemy_ind.position.x < self.defense_line - cloak_maginot:
                            self.cloaked_enemy = 1
                            already_in_list = 0
                            for list_i in range(len(self.cloaked_enemy_position)):
                                if enemy_ind.tag == self.cloaked_enemy_position[list_i][1]:
                                    already_in_list = 1
                                    self.cloaked_enemy_position[list_i] = [
                                        Point2((enemy_ind.position.x, enemy_ind.position.y)), enemy_ind.tag]
                                else:
                                    pass
                            if already_in_list == 0:
                                self.cloaked_enemy_position.append([
                                        Point2((enemy_ind.position.x, enemy_ind.position.y)), enemy_ind.tag])
                            else:
                                pass
                        else:
                            pass
                    else:
                        if enemy_ind.position.x > self.defense_line + cloak_maginot:
                            self.cloaked_enemy = 1
                            already_in_list = 0
                            for list_i in range(len(self.cloaked_enemy_position)):
                                if enemy_ind.tag == self.cloaked_enemy_position[list_i][1]:
                                    already_in_list = 1
                                    self.cloaked_enemy_position[list_i] = [
                                        Point2((enemy_ind.position.x, enemy_ind.position.y)), enemy_ind.tag]
                                else:
                                    pass
                            if already_in_list == 0:
                                self.cloaked_enemy_position.append([
                                        Point2((enemy_ind.position.x, enemy_ind.position.y)), enemy_ind.tag])
                            else:
                                pass
                        else:
                            pass
                else:
                    pass

                if enemy_ind.type_id == UnitTypeId.RAVEN:
                    self.enemy_has_raven = 1
                else:
                    pass

            if self.cloaked_enemy == 0:
                self.cloaked_enemy_position.clear()
            else:
                pass
        else:
            if self.is_combat != 2:
                self.is_combat = 0
            else:
                pass

        if self.enemy_tp == 0:
            if enemy_tp_counter > 0:
                self.enemy_tp = 1
                self.enemy_tp_time = self.time
            else:
                pass
        else:
            if enemy_tp_counter == 0:
                self.enemy_tp = 0
            else:
                pass

        #적이 접근중인지 판단 0->1->2->3 시간 순서
        self.is_enemy_rush = 0
        self.enemy_line_tick[0] = self.enemy_line_tick[1]
        self.enemy_line_tick[1] = self.enemy_line_tick[2]
        self.enemy_line_tick[2] = self.enemy_line_tick[3]
        self.enemy_line_tick[3] = self.enemy_line_tick[4]
        self.enemy_line_tick[4] = self.enemy_ground_line()
        if self.side == 1:
            if self.enemy_line_tick[0] > self.enemy_line_tick[1] and self.enemy_line_tick[1] > self.enemy_line_tick[2] and self.enemy_line_tick[2] > self.enemy_line_tick[3] and self.enemy_line_tick[3] > self.enemy_line_tick[4]:
                self.is_enemy_rush = 1
            else:
                pass
        else:
            if self.enemy_line_tick[0] < self.enemy_line_tick[1] and self.enemy_line_tick[1] < self.enemy_line_tick[2] and self.enemy_line_tick[2] < self.enemy_line_tick[3] and self.enemy_line_tick[3] < self.enemy_line_tick[4]:
                self.is_enemy_rush = 1
            else:
                pass

        #근접유닛 카운트 -> 전면전 여부 판단
        if self.enemy_close_counter > 0: # 근접 유닛 1개 이상
            if self.is_combat == 0:
                if self.units.of_type([UnitTypeId.SIEGETANKSIEGED, UnitTypeId.SIEGETANK]).exists:
                    if self.units.of_type([UnitTypeId.SIEGETANKSIEGED, UnitTypeId.SIEGETANK]).amount == 1:
                        self.combat_start_time = self.time
                        print("COMBAT START")
                        self.is_combat = 1
                    else:
                        if self.units(UnitTypeId.SIEGETANKSIEGED).amount >= self.units(UnitTypeId.SIEGETANK).amount:
                            self.combat_start_time = self.time
                            print("COMBAT START")
                            self.is_combat = 1
                        else:
                            pass
                else:
                    self.combat_start_time = self.time
                    print("COMBAT START")
                    self.is_combat = 1
            elif self.is_combat == 1:
                pass
            else:
                pass
        else: # 근접 유닛 0개
            if self.is_combat == 0:
                pass
            elif self.is_combat == 1:
                if self.enemy_close_tank_counter > 0:
                    pass
                else:
                    if self.time - self.combat_start_time > 3:  # or defense +- 7 밖으로..
                        self.is_combat = 0
                    else:
                        if self.known_enemy_units.not_structure.exists:
                            if self.side == 1:
                                if self.known_enemy_units.not_structure.closest_to(
                                        ally_cc).position.x > self.defense_line - 7:
                                    self.is_combat = 0
                                else:
                                    pass
                            else:
                                if self.known_enemy_units.not_structure.closest_to(
                                        ally_cc).position.x < self.defense_line + 7:
                                    self.is_combat = 0
                                else:
                                    pass
                        else:
                            self.is_combat = 0

            else:
                pass

        # Defense Line 조정
        if self.is_combat == 0 and self.game_time > 60 and self.enemy_can_tp == 0 and self.enemy_nuke_alert == 0: # 60으로
            if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount > 2:
                if self.enemy_death_gas * 10000 + self.enemy_death_min > self.my_death_gas * 10000 + self.my_death_min and self.time - self.line_break_time > 30:
                    if self.enemy_tank_line() == 999: # No tank or Not detected yet
                        if self.enemy_ground_line() != 999:
                            if self.side == 1:
                                if self.defense_line > self.enemy_ground_line() + 4: # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                    if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type([UnitTypeId.SIEGETANKSIEGED]).amount:
                                        temp_defense_line = self.enemy_ground_line() + 4
                                        if self.is_enemy_rush == 1: # 여기 수정해볼 생각
                                            if self.time - self.moving_line[1] < 0.5:
                                                if self.moving_line[0] - self.side * 1.5 >= 63:
                                                    self.defense_line = self.moving_line[0] - self.side * 1.5
                                                else:
                                                    self.defense_line = 63
                                                self.defense_line_modi_time = self.time
                                                self.line_break_time = self.time
                                        else:
                                            if temp_defense_line > 93 and self.defense_line != 93:
                                                self.defense_line = 93
                                                self.defense_line_modi_time = self.time
                                            elif temp_defense_line < 63 and self.defense_line != 63:
                                                self.defense_line = 63
                                                self.defense_line_modi_time = self.time
                                            elif temp_defense_line > 93 and self.defense_line == 93:
                                                pass
                                            elif temp_defense_line < 63 and self.defense_line == 63:
                                                pass # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                    else:
                                        pass
                                else: # 디펜스라인 전진
                                    if self.time - self.defense_line_modi_time > 60:
                                        temp_defense_line = self.enemy_ground_line() + 4
                                        if temp_defense_line > 93 and self.defense_line != 93:
                                            self.defense_line = 93
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                        elif temp_defense_line < 63 and self.defense_line != 63:
                                            self.defense_line = 63
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                        elif temp_defense_line > 93 and self.defense_line == 93:
                                            pass
                                        elif temp_defense_line < 63 and self.defense_line == 63:
                                            pass  # 마지노선
                                        else:
                                            self.defense_line = temp_defense_line
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                    else:
                                        pass
                            else: # 오른쪽사이드
                                if self.defense_line < self.enemy_ground_line() - 4: # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                    if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type([UnitTypeId.SIEGETANKSIEGED]).amount:
                                        temp_defense_line = self.enemy_ground_line() - 4
                                        if self.is_enemy_rush == 1:
                                            if self.time - self.moving_line[1] < 0.5:
                                                if self.moving_line[0] - self.side * 1.5 <= 66:
                                                    self.defense_line = self.moving_line[0] - self.side * 1.5
                                                else:
                                                    self.defense_line = 66
                                                self.defense_line_modi_time = self.time
                                                self.line_break_time = self.time
                                        else:
                                            if temp_defense_line < 34 and self.defense_line != 34:
                                                self.defense_line = 34
                                                self.defense_line_modi_time = self.time
                                            elif temp_defense_line > 66 and self.defense_line != 66:
                                                self.defense_line = 66
                                                self.defense_line_modi_time = self.time
                                            elif temp_defense_line < 34 and self.defense_line == 34:
                                                pass
                                            elif temp_defense_line > 66 and self.defense_line == 66:
                                                pass # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                    else:
                                        pass
                                else: # 디펜스라인 전진
                                    if self.time - self.defense_line_modi_time > 60:
                                        temp_defense_line = self.enemy_ground_line() - 4
                                        if temp_defense_line < 34 and self.defense_line != 34:
                                            self.defense_line = 34
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                        elif temp_defense_line > 66 and self.defense_line != 66:
                                            self.defense_line = 66
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                        elif temp_defense_line < 34 and self.defense_line == 34:
                                            pass
                                        elif temp_defense_line > 66 and self.defense_line == 66:
                                            pass  # 마지노선
                                        else:
                                            self.defense_line = temp_defense_line
                                            self.defense_line_modi_time = self.time
                                            self.move_start_time = self.time
                                    else:
                                        pass
                        else: # No enemy unit detected yet
                            pass
                    else: # enemy has tank_line
                        if self.enemy_ground_line != 999:
                            if self.side == 1:
                                if (self.enemy_ground_line() + 4) < (self.enemy_tank_line() + 2):
                                    if self.defense_line > self.enemy_ground_line() + 4:  # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                        if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type(
                                                [UnitTypeId.SIEGETANKSIEGED]).amount:
                                            temp_defense_line = self.enemy_ground_line() + 4
                                            if self.is_enemy_rush == 1: # 수정해보자
                                                if self.time - self.moving_line[1] < 0.5:
                                                    if self.moving_line[0] - self.side * 1.5 >= 63:
                                                        self.defense_line = self.moving_line[0] - self.side * 1.5
                                                    else:
                                                        self.defense_line = 63
                                                    self.defense_line_modi_time = self.time
                                                    self.line_break_time = self.time
                                            else:
                                                if temp_defense_line > 93 and self.defense_line != 93:
                                                    self.defense_line = 93
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line < 63 and self.defense_line != 63:
                                                    self.defense_line = 63
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line > 93 and self.defense_line == 93:
                                                    pass
                                                elif temp_defense_line < 63 and self.defense_line == 63:
                                                    pass  # 마지노선
                                                else:
                                                    self.defense_line = temp_defense_line
                                                    self.defense_line_modi_time = self.time
                                        else:
                                            pass
                                    else:  # 디펜스라인 전진
                                        if self.time - self.defense_line_modi_time > 60:
                                            temp_defense_line = self.enemy_ground_line() + 4
                                            if temp_defense_line > 93 and self.defense_line != 93:
                                                self.defense_line = 93
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line < 63 and self.defense_line != 63:
                                                self.defense_line = 63
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line > 93 and self.defense_line == 93:
                                                pass
                                            elif temp_defense_line < 63 and self.defense_line == 63:
                                                pass  # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                        else:
                                            pass
                                else:
                                    if self.defense_line > self.enemy_tank_line() + 2:  # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                        if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type(
                                                [UnitTypeId.SIEGETANKSIEGED]).amount:
                                            temp_defense_line = self.enemy_tank_line() + 2
                                            if self.is_enemy_rush == 1:
                                                if self.time - self.moving_line[1] < 0.5:
                                                    if self.moving_line[0] - self.side * 1.5 >= 63:
                                                        self.defense_line = self.moving_line[0] - self.side * 1.5
                                                    else:
                                                        self.defense_line = 63
                                                    self.defense_line_modi_time = self.time
                                                    self.line_break_time = self.time
                                            else:
                                                if temp_defense_line > 93 and self.defense_line != 93:
                                                    self.defense_line = 93
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line < 63 and self.defense_line != 63:
                                                    self.defense_line = 63
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line > 93 and self.defense_line == 93:
                                                    pass
                                                elif temp_defense_line < 63 and self.defense_line == 63:
                                                    pass  # 마지노선
                                                else:
                                                    self.defense_line = temp_defense_line
                                                    self.defense_line_modi_time = self.time
                                        else:
                                            pass
                                    else:  # 디펜스라인 전진
                                        if self.time - self.defense_line_modi_time > 60:
                                            temp_defense_line = self.enemy_tank_line() + 2
                                            if temp_defense_line > 93 and self.defense_line != 93:
                                                self.defense_line = 93
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line < 63 and self.defense_line != 63:
                                                self.defense_line = 63
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line > 93 and self.defense_line == 93:
                                                pass
                                            elif temp_defense_line < 63 and self.defense_line == 63:
                                                pass  # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                        else:
                                            pass

                            else: # 오른쪽 사이드
                                if (self.enemy_ground_line() - 4) > (self.enemy_tank_line() - 2):
                                    if self.defense_line < self.enemy_ground_line() - 4:  # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                        if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type(
                                                [UnitTypeId.SIEGETANKSIEGED]).amount:
                                            temp_defense_line = self.enemy_ground_line() - 4
                                            if self.is_enemy_rush == 1:
                                                if self.time - self.moving_line[1] < 0.5:
                                                    if self.time - self.moving_line[1] < 0.5:
                                                        if self.moving_line[0] - self.side * 1.5 <= 66:
                                                            self.defense_line = self.moving_line[0] - self.side * 1.5
                                                        else:
                                                            self.defense_line = 66
                                                    self.defense_line_modi_time = self.time
                                                    self.line_break_time = self.time
                                            else:
                                                if temp_defense_line < 34 and self.defense_line != 34:
                                                    self.defense_line = 34
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line > 66 and self.defense_line != 66:
                                                    self.defense_line = 66
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line < 34 and self.defense_line == 34:
                                                    pass
                                                elif temp_defense_line > 66 and self.defense_line == 66:
                                                    pass  # 마지노선
                                                else:
                                                    self.defense_line = temp_defense_line
                                                    self.defense_line_modi_time = self.time
                                        else:
                                            pass
                                    else:  # 디펜스라인 전진
                                        if self.time - self.defense_line_modi_time > 60:
                                            temp_defense_line = self.enemy_ground_line() - 4
                                            if temp_defense_line < 34 and self.defense_line != 34:
                                                self.defense_line = 34
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line > 66 and self.defense_line != 66:
                                                self.defense_line = 66
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line < 34 and self.defense_line == 34:
                                                pass
                                            elif temp_defense_line > 66 and self.defense_line == 66:
                                                pass  # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                        else:
                                            pass
                                else: #탱크라인 기준
                                    if self.defense_line < self.enemy_tank_line() - 2:  # 디펜스라인 후퇴하는 상황 ( 이동 중 적 보고 조정)
                                        if self.units.of_type([UnitTypeId.SIEGETANK]).amount > self.units.of_type(
                                                [UnitTypeId.SIEGETANKSIEGED]).amount:
                                            temp_defense_line = self.enemy_tank_line() - 2
                                            if self.is_enemy_rush == 1:
                                                if self.time - self.moving_line[1] < 0.5:
                                                    if self.time - self.moving_line[1] < 0.5:
                                                        if self.moving_line[0] - self.side * 1.5 <= 66:
                                                            self.defense_line = self.moving_line[0] - self.side * 1.5
                                                        else:
                                                            self.defense_line = 66
                                                    self.defense_line_modi_time = self.time
                                                    self.line_break_time = self.time
                                            else:
                                                if temp_defense_line < 34 and self.defense_line != 34:
                                                    self.defense_line = 34
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line > 66 and self.defense_line != 66:
                                                    self.defense_line = 66
                                                    self.defense_line_modi_time = self.time
                                                elif temp_defense_line < 34 and self.defense_line == 34:
                                                    pass
                                                elif temp_defense_line > 66 and self.defense_line == 66:
                                                    pass  # 마지노선
                                                else:
                                                    self.defense_line = temp_defense_line
                                                    self.defense_line_modi_time = self.time
                                        else:
                                            pass
                                    else:  # 디펜스라인 전진
                                        if self.time - self.defense_line_modi_time > 60:
                                            temp_defense_line = self.enemy_tank_line() - 2
                                            if temp_defense_line < 34 and self.defense_line != 34:
                                                self.defense_line = 34
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line > 66 and self.defense_line != 66:
                                                self.defense_line = 66
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                            elif temp_defense_line < 34 and self.defense_line == 34:
                                                pass
                                            elif temp_defense_line > 66 and self.defense_line == 66:
                                                pass  # 마지노선
                                            else:
                                                self.defense_line = temp_defense_line
                                                self.defense_line_modi_time = self.time
                                                self.move_start_time = self.time
                                        else:
                                            pass
                        else: # impossible
                            pass
                else: # 자원적으로 크게 여유있지 않음 : Hold
                    pass
            else:
                pass
        else:
            if self.game_time > self.allin_tp_time and self.is_combat == 0 and self.enemy_can_tp == 1 and self.enemy_nuke_alert == 0:
                if self.side == 1:
                    self.defense_line = 63
                else:
                    self.defense_line = 66

        # 어택땅 트리거
        if self.is_combat == 0 and self.game_time > 120 and self.time - self.my_nuke_launch_time > 15:
            if ((self.enemy_death_gas > self.my_death_gas + self.accum_gas * 0.4 + 48) and (self.enemy_death_min > self.my_death_min + self.accum_min * 0.3)) or (self.enemy_death_min > self.my_death_min + self.accum_min * 0.6):
                if 1:
                    if self.units.amount > 30:
                        if self.side == 1:
                            if 95.5 - self.defense_line <= 10:
                                self.move_adjust[UnitTypeId.BANSHEE] = 0
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 0
                                self.move_adjust[UnitTypeId.MARINE] = 0
                                self.move_adjust[UnitTypeId.HELLION] = 0
                                self.move_adjust[UnitTypeId.RAVEN] = 0
                            elif 10 < 95.5 - self.defense_line < 30:
                                self.move_adjust[UnitTypeId.BANSHEE] = 1
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 2
                                self.move_adjust[UnitTypeId.MARINE] = 1
                                self.move_adjust[UnitTypeId.HELLION] = 1
                                self.move_adjust[UnitTypeId.RAVEN] = 3
                            else:
                                self.move_adjust[UnitTypeId.BANSHEE] = 2
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 3
                                self.move_adjust[UnitTypeId.MARINE] = 2
                                self.move_adjust[UnitTypeId.HELLION] = 2
                                self.move_adjust[UnitTypeId.RAVEN] = 3
                            self.defense_line = 102.5

                        else:
                            if self.defense_line - 32.5 <= 10:
                                self.move_adjust[UnitTypeId.BANSHEE] = 0
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 0
                                self.move_adjust[UnitTypeId.MARINE] = 0
                                self.move_adjust[UnitTypeId.HELLION] = 0
                                self.move_adjust[UnitTypeId.RAVEN] = 0
                            elif 10 < self.defense_line - 32.5 < 30:
                                self.move_adjust[UnitTypeId.BANSHEE] = 1
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 2
                                self.move_adjust[UnitTypeId.MARINE] = 1
                                self.move_adjust[UnitTypeId.HELLION] = 1
                                self.move_adjust[UnitTypeId.RAVEN] = 3
                            else:
                                self.move_adjust[UnitTypeId.BANSHEE] = 2
                                self.move_adjust[UnitTypeId.VIKINGFIGHTER] = 3
                                self.move_adjust[UnitTypeId.MARINE] = 2
                                self.move_adjust[UnitTypeId.HELLION] = 2
                                self.move_adjust[UnitTypeId.RAVEN] = 3
                            self.defense_line = 25.5

                        self.end_game_time = self.time
                        self.is_combat = 2 # 어택땅
                    else:
                        pass
                else:
                    pass
            else:
                pass

        # 적 핵 감지
        enemy_nuke = 0
        self.enemy_nuke_position_list = list()
        for effect in self.state.effects:
            if effect.id == EffectId.NUKEPERSISTENT:
                print("NUKE DETECTED")
                self.enemy_nuke_position_list.append(list(effect.positions)[0])
                enemy_nuke = 1
            else:
                pass
        closest_nuke_dist = 100
        if enemy_nuke == 1:
            for enemy_nuke_position in self.enemy_nuke_position_list:
                if closest_nuke_dist > enemy_nuke_position.distance_to(ally_cc):
                    closest_enemy_nuke = enemy_nuke_position
                    closest_nuke_dist = enemy_nuke_position.distance_to(ally_cc)
            self.enemy_nuke_position = closest_enemy_nuke
        else:
            pass

        if enemy_nuke == 1:
            if self.time - self.enemy_nuke_alert_time > 14.8 or self.alert(Alert.NuclearLaunchDetected):
                self.enemy_nuke_alert_time = self.time
                self.enemy_nuke_alert = 1
                self.enemy_death_min += 100
                self.enemy_death_gas += 100
        else:
            if self.time - self.enemy_nuke_alert_time > 16:# or self.time - self.enemy_nuke_boom_time > 5:
                self.enemy_nuke_alert = 0

        #self.time - self.enemy_nuke_boom_time
        # 유닛 명령 생성
        for unit in self.units.not_structure:
            if unit.type_id is UnitTypeId.MULE:
                no_repair = 0
                cc = self.units(UnitTypeId.COMMANDCENTER).closest_to(unit)
                if cc.health_percentage < 1.0:
                    actions.append(unit.repair(cc))
                else:
                    if wounded_mech_units.exists:
                        if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).filter(
                        lambda u: u.health_percentage < 1.0).exists:
                            closest_repair = self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).filter(
                        lambda u: u.health_percentage < 1.0).closest_to(unit)
                        else:
                            if self.units.of_type([UnitTypeId.RAVEN]).filter(
                            lambda u: u.health_percentage < 1.0).exists:
                                closest_repair = self.units.of_type([UnitTypeId.RAVEN]).filter(
                            lambda u: u.health_percentage < 1.0).closest_to(unit)
                            else:
                                if self.units.of_type([UnitTypeId.BANSHEE]).filter(
                                lambda u: u.health_percentage < 1.0).exists:
                                    closest_repair = self.units.of_type([UnitTypeId.BANSHEE]).filter(
                                        lambda u: u.health_percentage < 1.0).closest_to(unit)
                                    if unit.distance_to(closest_repair) < 20:
                                        no_repair = 0
                                    else:
                                        no_repair = 1
                                else:
                                    if self.units.of_type([UnitTypeId.VIKINGFIGHTER]).filter(
                                            lambda u: u.health_percentage < 1.0).exists:
                                        closest_repair = self.units.of_type([UnitTypeId.VIKINGFIGHTER]).filter(
                                            lambda u: u.health_percentage < 1.0).closest_to(unit)
                                        if unit.distance_to(closest_repair) < 20:
                                            no_repair = 0
                                        else:
                                            no_repair = 1
                                    else:
                                        no_repair = 1

                        if no_repair == 0:
                            actions.append(unit.repair(closest_repair))
                        else:
                            if self.enemy_tp == 0:
                                actions.append(unit.move(Point2((self.defense_line - self.side * 23.5, 31.5))))
                            else:
                                if self.side == 1:
                                    actions.append(unit.move(Point2((32.5, 31.5))))
                                else:
                                    actions.append(unit.move(Point2((92.5, 31.5))))
                    else:
                        if self.enemy_tp == 0:
                            actions.append(unit.move(Point2((self.defense_line - self.side * 23.5, 31.5))))
                        else:
                            if self.side == 1:
                                actions.append(unit.move(Point2((32.5, 31.5))))
                            else:
                                actions.append(unit.move(Point2((92.5, 31.5))))

            if self.known_enemy_units.not_structure.exists:
                closest_enemy_unit = self.known_enemy_units.not_structure.closest_to(unit)
            else:
                closest_enemy_unit = enemy_cc

            if unit.type_id is UnitTypeId.HELLION:
                hel_list = list(self.hellion_pos_num.values())
                hel_list.sort()
                hel_num = 0
                for i in range(len(hel_list)):
                    if i != hel_list[i] - 1:
                        hel_num = i
                        break
                    elif i == hel_list[i] - 1 and i == len(hel_list) - 1:
                        hel_num = i + 1
                    else:
                        continue
                hel_num = hel_num + 1
                if self.hellion_pos_num.get(unit.tag, -2) == -2:
                    self.hellion_pos_num[unit.tag] = hel_num
                    hellion_target_pos_x, hellion_target_pos_y = self.defense_position(hel_num, UnitTypeId.HELLION)
                    self.hellion_position[(unit.tag, 'x')] = hellion_target_pos_x
                    self.hellion_position[(unit.tag, 'y')] = hellion_target_pos_y
                    hellion_target_position = Point2(Point2((hellion_target_pos_x, hellion_target_pos_y)))
                    self.hellion_position[(unit.tag, 't')] = self.time
                else:
                    hel_num = self.hellion_pos_num[unit.tag]
                    hellion_target_pos_x, hellion_target_pos_y = self.defense_position(hel_num, UnitTypeId.HELLION)
                    if self.hellion_position[(unit.tag, 'x')] == hellion_target_pos_x and self.hellion_position[
                        (unit.tag, 'y')] == hellion_target_pos_y:
                        hellion_target_position = Point2(Point2(
                            (self.hellion_position.get((unit.tag, 'x'), 0),
                             self.hellion_position.get((unit.tag, 'y'), 0))))
                    else:
                        self.hellion_position[(unit.tag, 'x')] = hellion_target_pos_x
                        self.hellion_position[(unit.tag, 'y')] = hellion_target_pos_y
                        hellion_target_position = Point2(Point2(
                            (self.hellion_position.get((unit.tag, 'x'), 0),
                             self.hellion_position.get((unit.tag, 'y'), 0))))
                if self.is_combat == 1:
                    if self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.exists:
                        t_ghost = self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)
                        if unit.distance_to(t_ghost) < 5:
                            kill_kill_ghost = 1
                        else:
                            kill_kill_ghost = 0
                    else:
                        kill_kill_ghost = 0
                    if self.known_enemy_units.not_structure.visible.not_flying.exists:
                        enemy_unit = self.known_enemy_units.not_structure.not_flying.closest_to(unit)
                        if self.side == 1:
                            if enemy_unit.position.x < self.defense_line - 3:
                                hel_attack = 1
                            else:
                                hel_attack = 0
                        else:
                            if enemy_unit.position.x > self.defense_line + 3:
                                hel_attack = 1
                            else:
                                hel_attack = 0

                        if hel_attack == 1:
                            if unit.weapon_cooldown < 8:
                                if kill_kill_ghost == 1:
                                    actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)))
                                else:
                                    actions.append(unit.attack(enemy_unit.position.towards(unit, 2)))
                            else:
                                x = enemy_unit.position.towards(unit, 2).x + 5 * self.side
                                y = enemy_unit.position.towards(unit, 2).y
                                if kill_kill_ghost == 1:
                                    actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)))
                                else:
                                    if self.game_time < 170:
                                        actions.append(unit.move(enemy_unit.position.towards(unit, 9)))
                                    else:
                                        actions.append(unit.move(Point2((x, y))))
                        else: # 최대한 안맞도록..
                            if self.enemy_nuke_alert == 1:
                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                    actions.append(unit.move(
                                        self.enemy_nuke_position.towards(unit, 11)))
                                else:
                                    if self.need_kill_ghost == 1:
                                        if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                            enemy_ghost = self.known_enemy_units(
                                                UnitTypeId.GHOST).closest_to(unit)
                                            actions.append(
                                                unit.attack(enemy_ghost.position.towards(unit, 1)))
                                        else:
                                            actions.append(unit.move(hellion_target_position))
                                    else:
                                        actions.append(unit.move(hellion_target_position))
                            else:
                                if self.game_time < 130:
                                    if self.units(UnitTypeId.AUTOTURRET).exists:
                                        turret_move_point = self.units(UnitTypeId.AUTOTURRET).closest_to(
                                            unit).position.towards(
                                            unit, 1)
                                        actions.append(unit.move(turret_move_point))
                                    else:
                                        actions.append(unit.move(ally_cc)) # 여기 이상해
                                else:
                                    actions.append(unit.move(hellion_target_position))

                                # 여기 수정하기
                    else: # 최대한 안맞도록..
                        if self.enemy_nuke_alert == 1:
                            if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                actions.append(unit.move(
                                    self.enemy_nuke_position.towards(unit, 11)))
                            else:
                                if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                    enemy_ghost = self.known_enemy_units(
                                        UnitTypeId.GHOST).closest_to(unit)
                                    actions.append(unit.attack(
                                        enemy_ghost.position.towards(unit, 0.5)))
                                else:
                                    actions.append(unit.move(hellion_target_position))
                        else:
                            if self.game_time < 130:
                                if self.units(UnitTypeId.AUTOTURRET).exists:
                                    turret_move_point = self.units(UnitTypeId.AUTOTURRET).closest_to(
                                        unit).position.towards(
                                        unit, 1)
                                    actions.append(unit.move(turret_move_point))
                                else:
                                    actions.append(unit.move(ally_cc))
                            else:
                                pass
                            # 여기 수정하기
                elif self.is_combat == 0:
                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.BANSHEE]).exists:
                        closest_hazard = self.known_enemy_units.of_type(
                            [UnitTypeId.BATTLECRUISER, UnitTypeId.BANSHEE]).closest_to(unit)
                        if unit.distance_to(closest_hazard) < 9.5:
                            m_x = unit.position.x - 3 * self.side
                            m_y = unit.position.y
                            actions.append(unit.move(Point2((m_x, m_y))))
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).exists:
                                closest_hazard = self.known_enemy_units.of_type(
                                    [UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).closest_to(unit)
                                if closest_hazard.type_id == UnitTypeId.HELLION or closest_hazard.type_id == UnitTypeId.MARAUDER:
                                    safe_dist = 10
                                else:
                                    safe_dist = 9
                                if unit.distance_to(closest_hazard) < safe_dist:
                                    m_x = unit.position.x - 8 * self.side
                                    m_y = unit.position.y
                                    actions.append(unit.move(Point2((m_x, m_y))))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                            actions.append(unit.move(
                                                self.enemy_nuke_position.towards(unit, 11)))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).closest_to(unit)
                                                    actions.append(
                                                        unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(hellion_target_position))
                                                    else:
                                                        actions.append(unit.attack(unit.position))

                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(hellion_target_position))
                                                else:
                                                    actions.append(unit.attack(unit.position))

                                    else:
                                        if self.need_kill_ghost == 1:
                                            if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                                enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(unit)
                                                actions.append(unit.attack(enemy_ghost.position.towards(unit,1)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(hellion_target_position))
                                                else:
                                                    actions.append(unit.attack(unit.position))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))

                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                        actions.append(unit.move(
                                            self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        if self.need_kill_ghost == 1:
                                            if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                                enemy_ghost = self.known_enemy_units(
                                                    UnitTypeId.GHOST).closest_to(unit)
                                                actions.append(
                                                    unit.attack(enemy_ghost.position.towards(unit, 1)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(hellion_target_position))
                                                else:
                                                    actions.append(unit.attack(unit.position))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))

                                else:
                                    if self.need_kill_ghost == 1:
                                        if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                            enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(
                                                unit)
                                            actions.append(unit.attack(enemy_ghost.position.towards(unit, 1)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))
                                    else:
                                        if self.time - self.move_start_time > 3:
                                            actions.append(unit.move(hellion_target_position))
                                        else:
                                            actions.append(unit.attack(unit.position))
                    else:
                        if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).exists:
                            closest_hazard = self.known_enemy_units.of_type(
                                [UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).closest_to(unit)
                            if closest_hazard.type_id == UnitTypeId.HELLION or closest_hazard.type_id == UnitTypeId.MARAUDER:
                                safe_dist = 10
                            else:
                                safe_dist = 9
                            if unit.distance_to(closest_hazard) < safe_dist:
                                m_x = unit.position.x - 8 * self.side
                                m_y = unit.position.y
                                actions.append(unit.move(Point2((m_x, m_y))))
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                        actions.append(unit.move(
                                            self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        if self.need_kill_ghost == 1:
                                            if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                                enemy_ghost = self.known_enemy_units(
                                                    UnitTypeId.GHOST).closest_to(unit)
                                                actions.append(
                                                    unit.attack(enemy_ghost.position.towards(unit, 1)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(hellion_target_position))
                                                else:
                                                    actions.append(unit.attack(unit.position))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))

                                else:
                                    if self.need_kill_ghost == 1:
                                        if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                            enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(
                                                unit)
                                            actions.append(unit.attack(enemy_ghost.position.towards(unit, 1)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))
                                    else:
                                        if self.time - self.move_start_time > 3:
                                            actions.append(unit.move(hellion_target_position))
                                        else:
                                            actions.append(unit.attack(unit.position))
                        else:
                            if self.enemy_nuke_alert == 1:
                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                    actions.append(unit.move(
                                        self.enemy_nuke_position.towards(unit, 11)))
                                else:
                                    if self.need_kill_ghost == 1:
                                        if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                            enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(
                                                unit)
                                            actions.append(unit.attack(enemy_ghost.position.towards(unit, 1)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(hellion_target_position))
                                            else:
                                                actions.append(unit.attack(unit.position))
                                    else:
                                        if self.time - self.move_start_time > 3:
                                            actions.append(unit.move(hellion_target_position))
                                        else:
                                            actions.append(unit.attack(unit.position))

                            else:
                                if self.need_kill_ghost == 1:
                                    if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                        enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(unit)
                                        actions.append(unit.attack(enemy_ghost.position.towards(unit, 1)))
                                    else:
                                        if self.time - self.move_start_time > 3:
                                            actions.append(unit.move(hellion_target_position))
                                        else:
                                            actions.append(unit.attack(unit.position))
                                else:
                                    if self.time - self.move_start_time > 3:
                                        actions.append(unit.move(hellion_target_position))
                                    else:
                                        actions.append(unit.attack(unit.position))
                else: # 어택땅!
                    if self.time - self.end_game_time > self.move_adjust[UnitTypeId.HELLION]:
                        actions.append(unit.attack(enemy_cc))
                    else:
                        if self.units(UnitTypeId.SIEGETANK).exists:
                            actions.append(unit.attack(Point2((self.units(UnitTypeId.SIEGETANK).closest_to(unit).position.x, unit.position.y))))
                        else:
                            actions.append(unit.attack(Point2((unit.position.x, unit.position.y))))

            elif unit.type_id is UnitTypeId.BANSHEE:
                self.bv_harass_bond = [unit.position.x, unit.position.y]
                if unit.is_cloaked == False:
                    if unit.energy > 55 and unit.health_percentage > 0.9:
                        self.banshee_pos_num[unit.tag] = 1
                        self.banshee_harass_switch = 1
                    else:
                        if unit.has_buff(BuffId.RAVENSCRAMBLERMISSILE):
                            self.banshee_pos_num[unit.tag] = 3  # 백
                            self.banshee_harass_switch = 0
                        else:
                            if self.banshee_harass_switch == 1:
                                pass
                            else:
                                self.banshee_pos_num[unit.tag] = 3  # 백
                                self.banshee_harass_switch = 0
                else:
                    if unit.energy < 5 or unit.health_percentage < 0.3:
                        self.banshee_pos_num[unit.tag] = 3
                        self.banshee_harass_switch = 0

                if self.enemy_nuke_alert == 1:
                    if unit.distance_to(self.enemy_nuke_position) < 10:
                        avoid_nuke = 1
                    else:
                        avoid_nuke = 0
                else:
                    avoid_nuke = 0

                if self.is_combat == 0 or self.is_combat == 1:
                    if self.banshee_pos_num[unit.tag] == 1:  # Harass

                        if avoid_nuke == 1:
                            actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                        else:
                            if unit.is_cloaked == True:
                                if unit.health_percentage < 1.0:
                                    self.enemy_has_raven = 1
                                else:
                                    pass

                                if self.enemy_has_raven == 0:
                                    if self.known_enemy_units.not_structure.not_flying.exists:
                                        closest_hit = self.known_enemy_units.not_structure.not_flying.closest_to(unit)
                                        actions.append(unit.attack(closest_hit))
                                    else:
                                        actions.append(unit.attack(enemy_cc))
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR, UnitTypeId.THORAP]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR, UnitTypeId.THORAP]).closest_to(unit)
                                        if unit.distance_to(closest_hazard) < 13:
                                            actions.append(unit.move(
                                                closest_hazard.position.towards(unit, 15)))
                                        else:
                                            if self.known_enemy_units.of_type([UnitTypeId.AUTOTURRET]).exists:
                                                closest_turret = self.known_enemy_units.of_type(
                                                    [UnitTypeId.AUTOTURRET]).closest_to(unit)
                                                if unit.distance_to(closest_turret) < 9:
                                                    actions.append(unit.move(closest_turret.position.towards((unit.position + ally_cc)/2, 11)))
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(
                                                            unit)

                                                        if unit.weapon_cooldown > 0:
                                                            self.combat_controller[unit.tag] = self.time
                                                        else:
                                                            pass

                                                        if unit.distance_to(closest_hazard) < 7.05:
                                                            actions.append(
                                                                unit.move(closest_hazard.position.towards(unit, 15)))
                                                        else:
                                                            if self.time - self.combat_controller.get(unit.tag, 0) > 1:
                                                                actions.append(
                                                                    unit.attack(
                                                                        closest_hazard.position.towards(unit, 7.04)))
                                                            else:
                                                                actions.append(unit.move(
                                                                    closest_hazard.position.towards(unit, 15)))
                                                    else:
                                                        if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                            attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                                unit)
                                                            actions.append(unit.attack(attack_target))
                                                        else:
                                                            actions.append(unit.attack(enemy_cc))
                                            else: # No Turret
                                                if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.MARINE]).closest_to(
                                                        unit)

                                                    if unit.weapon_cooldown > 0:
                                                        self.combat_controller[unit.tag] = self.time
                                                    else:
                                                        pass

                                                    if unit.distance_to(closest_hazard) < 7.05:
                                                        actions.append(
                                                            unit.move(closest_hazard.position.towards(unit, 15)))
                                                    else:
                                                        if self.time - self.combat_controller.get(unit.tag, 0) > 1:
                                                            actions.append(
                                                                unit.attack(
                                                                    closest_hazard.position.towards(unit, 7.04)))
                                                        else:
                                                            actions.append(unit.move(
                                                                closest_hazard.position.towards(unit, 15)))
                                                else:
                                                    if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                        attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                            unit)
                                                        actions.append(unit.attack(attack_target))
                                                    else:
                                                        actions.append(unit.attack(enemy_cc))
                                    else:
                                        if self.known_enemy_units.of_type([UnitTypeId.AUTOTURRET]).exists:
                                            closest_turret = self.known_enemy_units.of_type(
                                                [UnitTypeId.AUTOTURRET]).closest_to(unit)
                                            if unit.distance_to(closest_turret) < 9:
                                                actions.append(unit.move(closest_turret.position.towards((unit.position + ally_cc)/2, 11)))
                                            else:
                                                if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.MARINE]).closest_to(
                                                        unit)

                                                    if unit.weapon_cooldown > 0:
                                                        self.combat_controller[unit.tag] = self.time
                                                    else:
                                                        pass

                                                    if unit.distance_to(closest_hazard) < 7.05:
                                                        actions.append(
                                                            unit.move(closest_hazard.position.towards(unit, 15)))
                                                    else:
                                                        if self.time - self.combat_controller.get(unit.tag, 0) > 1:
                                                            actions.append(
                                                                unit.attack(
                                                                    closest_hazard.position.towards(unit, 7.04)))
                                                        else:
                                                            actions.append(unit.move(
                                                                closest_hazard.position.towards(unit, 15)))
                                                else:
                                                    if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                        attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                            unit)
                                                        actions.append(unit.attack(attack_target))
                                                    else:
                                                        actions.append(unit.attack(enemy_cc))
                                        else:  # No Turret
                                            if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                closest_hazard = self.known_enemy_units.of_type(
                                                    [UnitTypeId.MARINE]).closest_to(
                                                    unit)

                                                if unit.weapon_cooldown > 0:
                                                    self.combat_controller[unit.tag] = self.time
                                                else:
                                                    pass

                                                if unit.distance_to(closest_hazard) < 7.05:
                                                    actions.append(
                                                        unit.move(closest_hazard.position.towards(unit, 15)))
                                                else:
                                                    if self.time - self.combat_controller.get(unit.tag, 0) > 1:
                                                        actions.append(
                                                            unit.attack(
                                                                closest_hazard.position.towards(unit, 7.04)))
                                                    else:
                                                        actions.append(unit.move(
                                                            closest_hazard.position.towards(unit, 15)))
                                            else:
                                                if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                    attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                        unit)
                                                    actions.append(unit.attack(attack_target))
                                                else:
                                                    actions.append(unit.attack(enemy_cc))
                            else: # Banshee is not cloacked
                                if self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER,
                                         UnitTypeId.THOR, UnitTypeId.THORAP, UnitTypeId.GHOST]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER,
                                         UnitTypeId.THOR, UnitTypeId.THORAP, UnitTypeId.GHOST]).closest_to(unit)
                                    if unit.distance_to(closest_hazard) < 11:
                                        actions.append(unit(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
                                    else:
                                        if self.known_enemy_units.of_type([UnitTypeId.AUTOTURRET]).exists:
                                            closest_turret = self.known_enemy_units.of_type(
                                                [UnitTypeId.AUTOTURRET]).closest_to(unit)
                                            if unit.distance_to(closest_turret) < 9:
                                                actions.append(unit.move(closest_turret.position.towards((unit.position + ally_cc)/2, 11)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                                    else:
                                                        if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                            attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                                unit)
                                                            actions.append(unit.attack(attack_target))
                                                        else:
                                                            actions.append(unit.attack(enemy_cc))
                                                else:
                                                    if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                        attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                            unit)
                                                        actions.append(unit.attack(attack_target))
                                                    else:
                                                        actions.append(unit.attack(enemy_cc))

                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                                else:
                                                    if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                        attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                            unit)
                                                        actions.append(unit.attack(attack_target))
                                                    else:
                                                        actions.append(unit.attack(enemy_cc))
                                            else:
                                                if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                    attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                        unit)
                                                    actions.append(unit.attack(attack_target))
                                                else:
                                                    actions.append(unit.attack(enemy_cc))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.AUTOTURRET]).exists:
                                        closest_turret = self.known_enemy_units.of_type([UnitTypeId.AUTOTURRET]).closest_to(
                                            unit)
                                        if unit.distance_to(closest_turret) < 9:
                                            actions.append(unit.move(closest_turret.position.towards((unit.position + ally_cc)/2, 11)))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                                else:
                                                    if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                        attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                            unit)
                                                        actions.append(unit.attack(attack_target))
                                                    else:
                                                        actions.append(unit.attack(enemy_cc))
                                            else:
                                                if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                    attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                        unit)
                                                    actions.append(unit.attack(attack_target))
                                                else:
                                                    actions.append(unit.attack(enemy_cc))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 8:
                                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                            else:
                                                if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                    attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                        unit)
                                                    actions.append(unit.attack(attack_target))
                                                else:
                                                    actions.append(unit.attack(enemy_cc))
                                        else:
                                            if self.known_enemy_units.not_structure.not_flying.visible.exists:
                                                attack_target = self.known_enemy_units.not_structure.not_flying.visible.closest_to(
                                                    unit)
                                                actions.append(unit.attack(attack_target))
                                            else:
                                                actions.append(unit.attack(enemy_cc))

                    elif self.banshee_pos_num[unit.tag] == 3 or self.banshee_pos_num[unit.tag] == 2:  # hold and Taunt 여기 수정하자 상대 터렛 : 일단 복귀하기로
                        if self.side == 1:
                            if unit.position.x > (self.defense_line - 5) :
                                bs_retreat = 1
                            else:
                                bs_retreat = 0
                        else:
                            if unit.position.x < (self.defense_line + 5) :
                                bs_retreat = 1
                            else:
                                bs_retreat = 0
                        if bs_retreat == 0:
                            if self.known_enemy_units.of_type(
                                    [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR, UnitTypeId.THORAP]).exists:
                                closest_hazard = self.known_enemy_units.of_type(
                                    [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR, UnitTypeId.THORAP]).closest_to(unit)
                                if unit.distance_to(closest_hazard) < 13:
                                    actions.append(unit.move(closest_hazard.position.towards(unit, 15)))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).exists:
                                        closest_hazard = self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).closest_to(
                                            unit)

                                        if unit.distance_to(closest_hazard) < 9:
                                            actions.append(unit.move(closest_hazard.position.towards(unit, 14)))
                                        else:
                                            if unit.weapon_cooldown > 0:
                                                actions.append(unit.attack(closest_hazard.position.towards(unit, 7.04)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                        actions.append(
                                                            unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                                    else:
                                                        if self.need_kill_ghost == 1:
                                                            if self.known_enemy_units(
                                                                    UnitTypeId.GHOST).visible.exists:
                                                                enemy_ghost = self.known_enemy_units(
                                                                    UnitTypeId.GHOST).visible.closest_to(unit)
                                                                if unit.distance_to(enemy_ghost) < 25:
                                                                    actions.append(unit.attack(
                                                                        enemy_ghost.position.towards(unit, 1)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3.5:
                                                                        actions.append(unit.move(Point2((
                                                                                                        self.defense_line - self.side * 20,
                                                                                                        31.5))))
                                                            else:
                                                                if self.time - self.move_start_time > 3.5:
                                                                    actions.append(unit.move(Point2(
                                                                        (self.defense_line - self.side * 20, 31.5))))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3.5:
                                                                    actions.append(unit.move(Point2((
                                                                        self.defense_line - self.side * 20,
                                                                        31.5))))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2(
                                                                    (self.defense_line - self.side * 20, 31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 20, 31.5))))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                actions.append(
                                                    unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(unit.attack(
                                                                enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2((
                                                                    self.defense_line - self.side * 20,
                                                                    31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2(
                                                                (self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 20, 31.5))))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(unit.attack(
                                                            enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2((
                                                                self.defense_line - self.side * 20,
                                                                31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2(
                                                            (self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * 20, 31.5))))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).closest_to(
                                        unit)

                                    if unit.distance_to(closest_hazard) < 9:
                                        actions.append(unit.move(closest_hazard.position.towards(unit, 14)))
                                    else:
                                        if unit.weapon_cooldown > 0:
                                            actions.append(unit.attack(closest_hazard.position.towards(unit, 7.04)))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3.5:
                                                                    actions.append(unit.move(Point2((
                                                                        self.defense_line - self.side * 20,
                                                                        31.5))))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2(
                                                                    (self.defense_line - self.side * 20, 31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(unit.attack(
                                                                enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2((
                                                                    self.defense_line - self.side * 20,
                                                                    31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2(
                                                                (self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 20, 31.5))))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                            actions.append(
                                                unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(unit.attack(
                                                            enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2((
                                                                self.defense_line - self.side * 20,
                                                                31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2(
                                                            (self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * 20, 31.5))))
                                    else:
                                        if self.need_kill_ghost == 1:
                                            if self.known_enemy_units(
                                                    UnitTypeId.GHOST).visible.exists:
                                                enemy_ghost = self.known_enemy_units(
                                                    UnitTypeId.GHOST).visible.closest_to(unit)
                                                if unit.distance_to(enemy_ghost) < 25:
                                                    actions.append(unit.attack(
                                                        enemy_ghost.position.towards(unit, 1)))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2((
                                                            self.defense_line - self.side * 20,
                                                            31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(Point2(
                                                        (self.defense_line - self.side * 20, 31.5))))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * 20, 31.5))))
                        else: # bs_retreat == 1
                            if self.known_enemy_units.of_type(
                                    [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR,
                                     UnitTypeId.THORAP]).exists:
                                closest_hazard = self.known_enemy_units.of_type(
                                    [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.THOR,
                                     UnitTypeId.THORAP]).closest_to(unit)
                                if unit.distance_to(closest_hazard) < 13:
                                    actions.append(unit.move(closest_hazard.position.towards(unit, 15)))
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).closest_to(
                                            unit)

                                        if unit.distance_to(closest_hazard) < 7.05:
                                            actions.append(unit.move(closest_hazard.position.towards(unit, 14)))
                                        else:
                                            if self.enemy_nuke_alert == 1 and self.time - self.enemy_nuke_alert_time > 8:
                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).visible.closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3.5:
                                                                    actions.append(unit.move(Point2((
                                                                        self.defense_line - self.side * 20,
                                                                        31.5))))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2(
                                                                    (self.defense_line - self.side * 20, 31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(unit.attack(
                                                                enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2((
                                                                    self.defense_line - self.side * 20,
                                                                    31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2(
                                                                (self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 20, 31.5))))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                actions.append(
                                                    unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(unit.attack(
                                                                enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2((
                                                                    self.defense_line - self.side * 20,
                                                                    31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2(
                                                                (self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 20, 31.5))))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(unit.attack(
                                                            enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2((
                                                                self.defense_line - self.side * 20,
                                                                31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2(
                                                            (self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * 20, 31.5))))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.AUTOTURRET]).closest_to(
                                        unit)

                                    if unit.distance_to(closest_hazard) < 7.05:
                                        actions.append(unit.move(closest_hazard.position.towards(unit, 14)))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                actions.append(
                                                    unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).visible.closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(unit.attack(
                                                                enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3.5:
                                                                actions.append(unit.move(Point2((
                                                                    self.defense_line - self.side * 20,
                                                                    31.5))))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2(
                                                                (self.defense_line - self.side * 20, 31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 20, 31.5))))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(unit.attack(
                                                            enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2((
                                                                self.defense_line - self.side * 20,
                                                                31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2(
                                                            (self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * 20, 31.5))))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                            actions.append(
                                                unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).visible.closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(unit.attack(
                                                            enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(Point2((
                                                                self.defense_line - self.side * 20,
                                                                31.5))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2(
                                                            (self.defense_line - self.side * 20, 31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * 20, 31.5))))
                                    else:
                                        if self.need_kill_ghost == 1:
                                            if self.known_enemy_units(
                                                    UnitTypeId.GHOST).visible.exists:
                                                enemy_ghost = self.known_enemy_units(
                                                    UnitTypeId.GHOST).visible.closest_to(unit)
                                                if unit.distance_to(enemy_ghost) < 25:
                                                    actions.append(unit.attack(
                                                        enemy_ghost.position.towards(unit, 1)))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2((
                                                            self.defense_line - self.side * 20,
                                                            31.5))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(Point2(
                                                        (self.defense_line - self.side * 20, 31.5))))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * 20, 31.5))))

                elif self.is_combat == 2: #임시 (no use)
                    if self.time - self.end_game_time > self.move_adjust[UnitTypeId.BANSHEE]:
                        actions.append(unit.attack(enemy_cc))
                    else:
                        if self.units(UnitTypeId.SIEGETANK).exists:
                            actions.append(unit.attack(Point2(
                                (self.units(UnitTypeId.SIEGETANK).closest_to(unit).position.x, unit.position.y))))
                        else:
                            actions.append(unit.attack(Point2((unit.position.x, unit.position.y))))

            elif unit.type_id is UnitTypeId.RAVEN:
                rav_list = list(self.raven_pos_num.values())
                rav_list.sort()
                rav_num = 0
                for i in range(len(rav_list)):
                    if i != rav_list[i] - 1:
                        rav_num = i
                        break
                    elif i == rav_list[i] - 1 and i == len(rav_list) - 1:
                        rav_num = i + 1
                    else:
                        continue
                rav_num = rav_num + 1

                if self.raven_pos_num.get(unit.tag, -2) == -2:
                    self.raven_pos_num[unit.tag] = rav_num
                else:
                    rav_num = self.raven_pos_num[unit.tag]
                if self.units(UnitTypeId.VIKINGFIGHTER).amount < self.enemy_counter[UnitTypeId.VIKINGFIGHTER]:
                    safe_pos_dist = 21
                else:
                    safe_pos_dist = 19
                if self.enemy_tp == 0:
                    if self.is_combat == 0:
                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,UnitTypeId.VIKINGFIGHTER]).exists:
                            closest_hazard = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                            hazard_dist = 13
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                closest_hazard = self.known_enemy_units.of_type([UnitTypeId.MARINE]).closest_to(unit).position
                                hazard_dist = 10
                            else:
                                closest_hazard = ally_cc
                                hazard_dist = 0.1

                        if unit.distance_to(closest_hazard) < hazard_dist:
                            actions.append(
                                unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                        else:
                            if self.enemy_nuke_alert == 1:
                                if self.time - self.enemy_nuke_alert_time > 9:
                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                        if unit.distance_to(self.enemy_nuke_position) == 0:
                                            actions.append(unit.move(self.enemy_nuke_position.towards(ally_cc, 13)))
                                        else:
                                            actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                    else:
                                        if self.cloaked_enemy == 1:
                                            actions.append(
                                                unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                            else:
                                                pass
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                        target_ghost = self.known_enemy_units.of_type([UnitTypeId.GHOST]).closest_to(ally_cc)
                                        if self.side == 1:
                                            if target_ghost.position.x < (self.defense_line - self.nuke_ghost_maginot):
                                                go_ghost = 1
                                            else:
                                                go_ghost = 0
                                        else:
                                            if target_ghost.position.x > (self.defense_line + self.nuke_ghost_maginot):
                                                go_ghost = 1
                                            else:
                                                go_ghost = 0
                                        if go_ghost == 1:
                                            actions.append(unit.move(target_ghost.position))
                                        else:
                                            if self.cloaked_enemy == 1:
                                                actions.append(
                                                    unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                else:
                                                    pass
                                    else:
                                        if self.side == 1:
                                            if self.enemy_nuke_position.x < (self.defense_line - self.find_nuke_maginot):
                                                find_ghost = 1
                                            else:
                                                find_ghost = 0
                                        else:
                                            if self.enemy_nuke_position.x > (self.defense_line + self.find_nuke_maginot):
                                                find_ghost = 1
                                            else:
                                                find_ghost = 0

                                        print(("파인드고스트", find_ghost))
                                        if find_ghost == 1:
                                            actions.append(unit.move(self.enemy_nuke_position.towards(ally_cc, -1)))
                                        else:
                                            if self.cloaked_enemy == 1:
                                                actions.append(
                                                    unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                else:
                                                    pass
                            else:
                                if self.cloaked_enemy == 1:
                                    actions.append(
                                        unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                else:
                                    if self.time - self.move_start_time > 3:
                                        actions.append(unit.move(
                                            Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                    else:
                                        pass
                    elif self.is_combat == 1:
                        if self.game_time > 120:
                            if unit.energy > 50:  # need to change -> 50 later (version) 밤까마나수정
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                    target_found = 0
                                    for mat_target in self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]):
                                        if (not mat_target.has_buff(BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(
                                                mat_target) < 25:
                                            already_target = 0
                                            for list_i in range(len(self.raven_matrix_target)):
                                                if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                    already_target = 1
                                                else:
                                                    pass
                                            if already_target == 0:
                                                target_found = 1
                                                break
                                            else:
                                                pass
                                        else:
                                            pass
                                    if target_found == 1:
                                        if self.time - self.raven_matrix_time.get(unit.tag, 0) > 0.5 and unit.distance_to(mat_target) < 9:
                                            actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                            self.raven_matrix_target.append([mat_target.tag, self.time])
                                            self.raven_matrix_time[unit.tag] = self.time
                                        else:
                                            actions.append(unit.move(mat_target.position.towards(unit,9)))
                                    else: # target not found
                                        if self.known_enemy_units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).exists:
                                            target_found = 0
                                            for mat_target in self.known_enemy_units.of_type(
                                                    [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]):
                                                if (not mat_target.has_buff(
                                                        BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(
                                                        mat_target) < 25:
                                                    already_target = 0
                                                    for list_i in range(len(self.raven_matrix_target)):
                                                        if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                            already_target = 1
                                                        else:
                                                            pass
                                                    if already_target == 0:
                                                        target_found = 1
                                                        break
                                                    else:
                                                        pass
                                                else:
                                                    pass
                                            if target_found == 1:
                                                if self.time - self.raven_matrix_time.get(unit.tag,0) > 0.5 and unit.distance_to(mat_target) < 9:
                                                    actions.append(
                                                        unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                                    self.raven_matrix_target.append([mat_target.tag, self.time])
                                                    self.raven_matrix_time[unit.tag] = self.time
                                                else:
                                                    actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                            else: #target not found
                                                if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1: # 방깎
                                                    if self.enemy_close_counter > 1 and unit.energy > 75:
                                                        if self.side == 1:
                                                            if self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                            u: u.position.x > self.defense_line - 8).exists:
                                                                anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                        u: u.position.x > self.defense_line - 8).closest_to(
                                                                    unit)
                                                                antiarmor = 1
                                                            else:
                                                                antiarmor = 0
                                                        else:
                                                            if self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                            u: u.position.x > self.defense_line + 8).exists:
                                                                anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                        u: u.position.x > self.defense_line + 8).closest_to(
                                                                    unit)
                                                                antiarmor = 1
                                                            else:
                                                                antiarmor = 0
                                                        if antiarmor == 1:
                                                            actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                                target=anti_armor_target))
                                                        else:
                                                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                               UnitTypeId.VIKINGFIGHTER]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.BATTLECRUISER,
                                                                     UnitTypeId.VIKINGFIGHTER]).closest_to(
                                                                    unit).position
                                                                hazard_dist = 13
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.MARINE]).exists:
                                                                    closest_hazard = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.MARINE]).closest_to(unit).position
                                                                    hazard_dist = 10
                                                                else:
                                                                    closest_hazard = ally_cc
                                                                    hazard_dist = 0.1

                                                            if unit.distance_to(closest_hazard) < hazard_dist:
                                                                actions.append(
                                                                    unit.move(
                                                                        closest_hazard.towards(unit, hazard_dist + 2)))
                                                            else:
                                                                if self.enemy_nuke_alert == 1:
                                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                                        if unit.distance_to(
                                                                                self.enemy_nuke_position) < 11:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(unit,
                                                                                                                 13)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                            self.defense_line - self.side * safe_pos_dist,
                                                                                            31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.known_enemy_units.of_type(
                                                                                [UnitTypeId.GHOST]).exists:
                                                                            target_ghost = self.known_enemy_units.of_type(
                                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                            if self.side == 1:
                                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                    go_ghost = 1
                                                                                else:
                                                                                    go_ghost = 0
                                                                            else:
                                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                    go_ghost = 1
                                                                                else:
                                                                                    go_ghost = 0
                                                                            if go_ghost == 1:
                                                                                actions.append(
                                                                                    unit.move(target_ghost.position))
                                                                            else:
                                                                                if self.cloaked_enemy == 1:
                                                                                    actions.append(
                                                                                        unit.move(
                                                                                            self.cloaked_enemy_position[
                                                                                                0][
                                                                                                0].towards(unit, 6)))
                                                                                else:
                                                                                    if self.time - self.move_start_time > 3:
                                                                                        actions.append(unit.move(
                                                                                            Point2((
                                                                                                self.defense_line - self.side * safe_pos_dist,
                                                                                                31.5))))
                                                                                    else:
                                                                                        pass
                                                                        else:
                                                                            if self.side == 1:
                                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                    find_ghost = 1
                                                                                else:
                                                                                    find_ghost = 0
                                                                            else:
                                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                    find_ghost = 1
                                                                                else:
                                                                                    find_ghost = 0
                                                                            if find_ghost == 1:
                                                                                actions.append(unit.move(
                                                                                    self.enemy_nuke_position.towards(
                                                                                        ally_cc,
                                                                                        -1)))
                                                                            else:
                                                                                if self.cloaked_enemy == 1:
                                                                                    actions.append(
                                                                                        unit.move(
                                                                                            self.cloaked_enemy_position[
                                                                                                0][
                                                                                                0].towards(unit, 6)))
                                                                                else:
                                                                                    if self.time - self.move_start_time > 3:
                                                                                        actions.append(unit.move(
                                                                                            Point2((
                                                                                                self.defense_line - self.side * safe_pos_dist,
                                                                                                31.5))))
                                                                                    else:
                                                                                        pass
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(
                                                                                self.cloaked_enemy_position[0][
                                                                                    0].towards(unit,
                                                                                               6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2(
                                                                                    (self.defense_line - self.side * safe_pos_dist,
                                                                                     31.5))))
                                                                        else:
                                                                            pass
                                                    else: #나띵
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type([UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                        self.defense_line - self.side * safe_pos_dist,
                                                                                        31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                            self.defense_line - self.side * safe_pos_dist,
                                                                                            31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc,
                                                                                    -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                            self.defense_line - self.side * safe_pos_dist,
                                                                                            31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit,
                                                                                6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else: #나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                        else: #매트릭스타겟 없음
                                            if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                                if self.enemy_close_counter > 1 and unit.energy > 75:
                                                    if self.side == 1:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line - 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line - 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    else:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line + 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line + 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    if antiarmor == 1:
                                                        actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                            target=anti_armor_target))
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                           UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.BATTLECRUISER,
                                                                 UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(
                                                                unit.move(
                                                                    closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc, -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:  # 나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).exists:
                                        target_found = 0
                                        for mat_target in self.known_enemy_units.of_type(
                                                [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]):
                                            if (not mat_target.has_buff(
                                                    BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(
                                                mat_target) < 25:
                                                already_target = 0
                                                for list_i in range(len(self.raven_matrix_target)):
                                                    if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                        already_target = 1
                                                    else:
                                                        pass
                                                if already_target == 0:
                                                    target_found = 1
                                                    break
                                                else:
                                                    pass
                                            else:
                                                pass
                                        if target_found == 1:
                                            if self.time - self.raven_matrix_time.get(unit.tag,0) > 0.5 and unit.distance_to(mat_target) < 9:
                                                actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                                self.raven_matrix_target.append([mat_target.tag, self.time])
                                                self.raven_matrix_time[unit.tag] = self.time
                                            else:
                                                actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                        else:  # target not found
                                            if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                                if self.enemy_close_counter > 1 and unit.energy > 75:
                                                    if self.side == 1:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line - 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line - 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    else:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line + 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line + 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    if antiarmor == 1:
                                                        actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                            target=anti_armor_target))
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                           UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.BATTLECRUISER,
                                                                 UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(
                                                                unit.move(
                                                                    closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc, -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:  # 나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * 19, 31.5))))
                                                            else:
                                                                pass
                                    else:  # 매트릭스타겟 없음
                                        if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                            if self.enemy_close_counter > 1 and unit.energy > 75:
                                                if self.side == 1:
                                                    if self.known_enemy_units.not_structure.visible.filter(
                                                        lambda u: u.position.x > self.defense_line - 8).exists:
                                                        anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line - 8).closest_to(
                                                            unit)
                                                        antiarmor = 1
                                                    else:
                                                        antiarmor = 0
                                                else:
                                                    if self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line + 8).exists:
                                                        anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line + 8).closest_to(
                                                            unit)
                                                        antiarmor = 1
                                                    else:
                                                        antiarmor = 0
                                                if antiarmor == 1:
                                                    actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,target=anti_armor_target))
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                        else:  # 나띵
                                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                               UnitTypeId.VIKINGFIGHTER]).exists:
                                                closest_hazard = self.known_enemy_units.of_type(
                                                    [UnitTypeId.BATTLECRUISER,
                                                     UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                hazard_dist = 13
                                            else:
                                                if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.MARINE]).closest_to(unit).position
                                                    hazard_dist = 10
                                                else:
                                                    closest_hazard = ally_cc
                                                    hazard_dist = 0.1

                                            if unit.distance_to(closest_hazard) < hazard_dist:
                                                actions.append(
                                                    unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                        if unit.distance_to(self.enemy_nuke_position) < 11:
                                                            actions.append(unit.move(
                                                                self.enemy_nuke_position.towards(unit, 13)))
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                            target_ghost = self.known_enemy_units.of_type(
                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                            if self.side == 1:
                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            else:
                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            if go_ghost == 1:
                                                                actions.append(unit.move(target_ghost.position))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.side == 1:
                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            else:
                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            if find_ghost == 1:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(ally_cc, -1)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                            else:  # 후퇴
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.BATTLECRUISER,
                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                    hazard_dist = 13
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                        hazard_dist = 10
                                    else:
                                        closest_hazard = ally_cc
                                        hazard_dist = 0.1

                                if unit.distance_to(closest_hazard) < hazard_dist:
                                    actions.append(unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if self.time - self.enemy_nuke_alert_time > 9:
                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                actions.append(unit.move(
                                                    self.enemy_nuke_position.towards(unit, 13)))
                                            else:
                                                if self.cloaked_enemy == 1:
                                                    actions.append(
                                                        unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                    else:
                                                        pass
                                        else:
                                            if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                target_ghost = self.known_enemy_units.of_type(
                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                if self.side == 1:
                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                else:
                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                if go_ghost == 1:
                                                    actions.append(unit.move(target_ghost.position))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                            else:
                                                if self.side == 1:
                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                else:
                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                if find_ghost == 1:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(ally_cc, -1)))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                    else:
                                        if self.cloaked_enemy == 1:
                                            actions.append(
                                                unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                            else:
                                                pass
                        else: # 2분 10초 전
                            if unit.energy > 50:
                                if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                    hazard_distance = 13
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                        hazard_distance = 10
                                    else:
                                        closest_hazard = ally_cc
                                        hazard_distance = 0.2

                                if self.known_enemy_units.of_type([UnitTypeId.BANSHEE, UnitTypeId.VIKINGFIGHTER]).exists:
                                    turret_target = self.known_enemy_units.closest_to(unit).position.towards(ally_cc,1)
                                    if self.side == 1:
                                        if turret_target.x < self.defense_line - 4:
                                            if self.units(UnitTypeId.MARINE).amount < 5:
                                                actions.append(unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, target=turret_target))
                                            else:
                                                if unit.distance_to(closest_hazard) < hazard_distance:
                                                    actions.append(unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                        else:
                                            if unit.distance_to(closest_hazard) < hazard_distance:
                                                actions.append(
                                                    unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                        if unit.distance_to(self.enemy_nuke_position) < 11:
                                                            actions.append(unit.move(
                                                                self.enemy_nuke_position.towards(unit, 13)))
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                            target_ghost = self.known_enemy_units.of_type(
                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                            if self.side == 1:
                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            else:
                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            if go_ghost == 1:
                                                                actions.append(unit.move(target_ghost.position))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.side == 1:
                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            else:
                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            if find_ghost == 1:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(ally_cc, -1)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                    else:
                                        if turret_target.x > self.defense_line + 4:
                                            if self.units(UnitTypeId.MARINE).amount < 5:
                                                actions.append(unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, target=turret_target))
                                            else:
                                                if unit.distance_to(closest_hazard) < hazard_distance:
                                                    actions.append(unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                        else:
                                            if unit.distance_to(closest_hazard) < hazard_distance:
                                                actions.append(
                                                    unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                        if unit.distance_to(self.enemy_nuke_position) < 11:
                                                            actions.append(unit.move(
                                                                self.enemy_nuke_position.towards(unit, 13)))
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                            target_ghost = self.known_enemy_units.of_type(
                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                            if self.side == 1:
                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            else:
                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            if go_ghost == 1:
                                                                actions.append(unit.move(target_ghost.position))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.side == 1:
                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            else:
                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            if find_ghost == 1:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(ally_cc, -1)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                else:
                                    if unit.distance_to(closest_hazard) < hazard_distance:
                                        actions.append(unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                    actions.append(unit.move(
                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                            else:
                                                if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                    target_ghost = self.known_enemy_units.of_type(
                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                    if self.side == 1:
                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                            go_ghost = 1
                                                        else:
                                                            go_ghost = 0
                                                    else:
                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                            go_ghost = 1
                                                        else:
                                                            go_ghost = 0
                                                    if go_ghost == 1:
                                                        actions.append(unit.move(target_ghost.position))
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                                else:
                                                    if self.side == 1:
                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                            find_ghost = 1
                                                        else:
                                                            find_ghost = 0
                                                    else:
                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                            find_ghost = 1
                                                        else:
                                                            find_ghost = 0
                                                    if find_ghost == 1:
                                                        actions.append(
                                                            unit.move(self.enemy_nuke_position.towards(ally_cc, -1)))
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                            else:
                                                                pass
                                        else:
                                            if self.cloaked_enemy == 1:
                                                actions.append(
                                                    unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(
                                                        Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                else:
                                                    pass
                            else:  # 후퇴
                                if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                    hazard_distance = 13
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                        hazard_distance = 10
                                    else:
                                        closest_hazard = ally_cc
                                        hazard_distance = 0.2
                                if unit.distance_to(closest_hazard) < hazard_distance:
                                    actions.append(unit.move(closest_hazard.towards(unit, hazard_distance + 2)))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if self.time - self.enemy_nuke_alert_time > 9:
                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                actions.append(unit.move(
                                                    self.enemy_nuke_position.towards(unit, 13)))
                                            else:
                                                if self.cloaked_enemy == 1:
                                                    actions.append(
                                                        unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                    else:
                                                        pass
                                        else:
                                            if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                target_ghost = self.known_enemy_units.of_type(
                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                if self.side == 1:
                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                else:
                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                if go_ghost == 1:
                                                    actions.append(unit.move(target_ghost.position))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                            else:
                                                if self.side == 1:
                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                else:
                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                if find_ghost == 1:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(ally_cc, -1)))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                                        else:
                                                            pass
                                    else:
                                        if self.cloaked_enemy == 1:
                                            actions.append(
                                                unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * safe_pos_dist, 31.5))))
                                            else:
                                                pass
                    else: # 어택땅
                        if self.time - self.end_game_time > self.move_adjust[UnitTypeId.RAVEN]:
                            if unit.energy > 50:  # need to change -> 50 later (version) 밤까마나수정
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                    target_found = 0
                                    for mat_target in self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]):
                                        if (not mat_target.has_buff(BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(
                                                mat_target) < 25:
                                            already_target = 0
                                            for list_i in range(len(self.raven_matrix_target)):
                                                if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                    already_target = 1
                                                else:
                                                    pass
                                            if already_target == 0:
                                                target_found = 1
                                                break
                                            else:
                                                pass
                                        else:
                                            pass
                                    if target_found == 1:
                                        if self.time - self.raven_matrix_time.get(unit.tag,0) > 0.5 and unit.distance_to(mat_target) < 9:
                                            actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                            self.raven_matrix_target.append([mat_target.tag, self.time])
                                            self.raven_matrix_time[unit.tag] = self.time
                                        else:
                                            actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                    else:  # target not found
                                        if self.known_enemy_units.of_type(
                                                [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).exists:
                                            target_found = 0
                                            for mat_target in self.known_enemy_units.of_type(
                                                    [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]):
                                                if (not mat_target.has_buff(
                                                        BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(
                                                    mat_target) < 25:
                                                    already_target = 0
                                                    for list_i in range(len(self.raven_matrix_target)):
                                                        if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                            already_target = 1
                                                        else:
                                                            pass
                                                    if already_target == 0:
                                                        target_found = 1
                                                        break
                                                    else:
                                                        pass
                                                else:
                                                    pass
                                            if target_found == 1:
                                                if self.time - self.raven_matrix_time.get(unit.tag,0) > 0.5 and unit.distance_to(mat_target) < 9:
                                                    actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                                    self.raven_matrix_target.append([mat_target.tag, self.time])
                                                    self.raven_matrix_time[unit.tag] = self.time
                                                else:
                                                    actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                            else:  # target not found
                                                if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                                    if self.enemy_close_counter > 1 and unit.energy > 75:
                                                        if self.side == 1:
                                                            if self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                            u: u.position.x > self.defense_line - 8).exists:
                                                                anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                        u: u.position.x > self.defense_line - 8).closest_to(
                                                                    unit)
                                                                antiarmor = 1
                                                            else:
                                                                antiarmor = 0
                                                        else:
                                                            if self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                            u: u.position.x > self.defense_line + 8).exists:
                                                                anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                    lambda
                                                                        u: u.position.x > self.defense_line + 8).closest_to(
                                                                    unit)
                                                                antiarmor = 1
                                                            else:
                                                                antiarmor = 0
                                                        if antiarmor == 1:
                                                            actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                                target=anti_armor_target))
                                                        else:
                                                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                               UnitTypeId.VIKINGFIGHTER]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.BATTLECRUISER,
                                                                     UnitTypeId.VIKINGFIGHTER]).closest_to(
                                                                    unit).position
                                                                hazard_dist = 13
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.MARINE]).exists:
                                                                    closest_hazard = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.MARINE]).closest_to(unit).position
                                                                    hazard_dist = 10
                                                                else:
                                                                    closest_hazard = ally_cc
                                                                    hazard_dist = 0.1

                                                            if unit.distance_to(closest_hazard) < hazard_dist:
                                                                actions.append(
                                                                    unit.move(
                                                                        closest_hazard.towards(unit, hazard_dist + 2)))
                                                            else:
                                                                if self.enemy_nuke_alert == 1:
                                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                                        if unit.distance_to(
                                                                                self.enemy_nuke_position) < 11:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(unit,
                                                                                                                 13)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.known_enemy_units.of_type(
                                                                                [UnitTypeId.GHOST]).exists:
                                                                            target_ghost = self.known_enemy_units.of_type(
                                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                            if self.side == 1:
                                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                    go_ghost = 1
                                                                                else:
                                                                                    go_ghost = 0
                                                                            else:
                                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                    go_ghost = 1
                                                                                else:
                                                                                    go_ghost = 0
                                                                            if go_ghost == 1:
                                                                                actions.append(
                                                                                    unit.move(target_ghost.position))
                                                                            else:
                                                                                if self.cloaked_enemy == 1:
                                                                                    actions.append(
                                                                                        unit.move(
                                                                                            self.cloaked_enemy_position[
                                                                                                0][0].towards(unit, 6)))
                                                                                else:
                                                                                    if self.time - self.move_start_time > 3:
                                                                                        actions.append(unit.move(
                                                                                            Point2((
                                                                                                   self.defense_line - self.side * safe_pos_dist,
                                                                                                   31.5))))
                                                                                    else:
                                                                                        pass
                                                                        else:
                                                                            if self.side == 1:
                                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                    find_ghost = 1
                                                                                else:
                                                                                    find_ghost = 0
                                                                            else:
                                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                    find_ghost = 1
                                                                                else:
                                                                                    find_ghost = 0
                                                                            if find_ghost == 1:
                                                                                actions.append(unit.move(
                                                                                    self.enemy_nuke_position.towards(
                                                                                        ally_cc, -1)))
                                                                            else:
                                                                                if self.cloaked_enemy == 1:
                                                                                    actions.append(
                                                                                        unit.move(
                                                                                            self.cloaked_enemy_position[
                                                                                                0][0].towards(unit, 6)))
                                                                                else:
                                                                                    if self.time - self.move_start_time > 3:
                                                                                        actions.append(unit.move(
                                                                                            Point2((
                                                                                                   self.defense_line - self.side * safe_pos_dist,
                                                                                                   31.5))))
                                                                                    else:
                                                                                        pass
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * safe_pos_dist,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:  # 나띵
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                           UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.BATTLECRUISER,
                                                                 UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(unit.move(
                                                                closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * safe_pos_dist,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc, -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * safe_pos_dist,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * safe_pos_dist,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:  # 나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * 19,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                        else:  # 매트릭스타겟 없음
                                            if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                                if self.enemy_close_counter > 1 and unit.energy > 75:
                                                    if self.side == 1:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line - 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line - 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    else:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line + 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line + 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    if antiarmor == 1:
                                                        actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                            target=anti_armor_target))
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                           UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.BATTLECRUISER,
                                                                 UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(
                                                                unit.move(
                                                                    closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * 19,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc, -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * 19,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:  # 나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * 19,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * 19, 31.5))))
                                                            else:
                                                                pass
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).exists:
                                        target_found = 0
                                        for mat_target in self.known_enemy_units.of_type(
                                                [UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]):
                                            if (not mat_target.has_buff(
                                                    BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(mat_target) < 25:
                                                already_target = 0
                                                for list_i in range(len(self.raven_matrix_target)):
                                                    if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                        already_target = 1
                                                    else:
                                                        pass
                                                if already_target == 0:
                                                    target_found = 1
                                                    break
                                                else:
                                                    pass
                                            else:
                                                pass
                                        if target_found == 1:
                                            if self.time - self.raven_matrix_time.get(unit.tag,0) > 0.5 and unit.distance_to(mat_target) < 9:
                                                actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                                self.raven_matrix_target.append([mat_target.tag, self.time])
                                                self.raven_matrix_time[unit.tag] = self.time
                                            else:
                                                actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                        else:  # target not found
                                            if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                                if self.enemy_close_counter > 1 and unit.energy > 75:
                                                    if self.side == 1:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line - 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line - 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    else:
                                                        if self.known_enemy_units.not_structure.visible.filter(
                                                                lambda u: u.position.x > self.defense_line + 8).exists:
                                                            anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                                lambda
                                                                    u: u.position.x > self.defense_line + 8).closest_to(
                                                                unit)
                                                            antiarmor = 1
                                                        else:
                                                            antiarmor = 0
                                                    if antiarmor == 1:
                                                        actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                            target=anti_armor_target))
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                           UnitTypeId.VIKINGFIGHTER]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.BATTLECRUISER,
                                                                 UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                            hazard_dist = 13
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).exists:
                                                                closest_hazard = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.MARINE]).closest_to(unit).position
                                                                hazard_dist = 10
                                                            else:
                                                                closest_hazard = ally_cc
                                                                hazard_dist = 0.1

                                                        if unit.distance_to(closest_hazard) < hazard_dist:
                                                            actions.append(
                                                                unit.move(
                                                                    closest_hazard.towards(unit, hazard_dist + 2)))
                                                        else:
                                                            if self.enemy_nuke_alert == 1:
                                                                if self.time - self.enemy_nuke_alert_time > 9:
                                                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(unit, 13)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).exists:
                                                                        target_ghost = self.known_enemy_units.of_type(
                                                                            [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                        if self.side == 1:
                                                                            if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        else:
                                                                            if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                                go_ghost = 1
                                                                            else:
                                                                                go_ghost = 0
                                                                        if go_ghost == 1:
                                                                            actions.append(
                                                                                unit.move(target_ghost.position))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * 19,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                                    else:
                                                                        if self.side == 1:
                                                                            if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        else:
                                                                            if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                                find_ghost = 1
                                                                            else:
                                                                                find_ghost = 0
                                                                        if find_ghost == 1:
                                                                            actions.append(unit.move(
                                                                                self.enemy_nuke_position.towards(
                                                                                    ally_cc, -1)))
                                                                        else:
                                                                            if self.cloaked_enemy == 1:
                                                                                actions.append(
                                                                                    unit.move(
                                                                                        self.cloaked_enemy_position[0][
                                                                                            0].towards(unit, 6)))
                                                                            else:
                                                                                if self.time - self.move_start_time > 3:
                                                                                    actions.append(unit.move(
                                                                                        Point2((
                                                                                               self.defense_line - self.side * 19,
                                                                                               31.5))))
                                                                                else:
                                                                                    pass
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:  # 나띵
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * 19,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * 19, 31.5))))
                                                            else:
                                                                pass
                                    else:  # 매트릭스타겟 없음
                                        if self.time - self.combat_start_time > 3.5 or self.enemy_is_MARAUDER == 1:  # 방깎
                                            if self.enemy_close_counter > 1 and unit.energy > 75:
                                                if self.side == 1:
                                                    if self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line - 8).exists:
                                                        anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line - 8).closest_to(
                                                            unit)
                                                        antiarmor = 1
                                                    else:
                                                        antiarmor = 0
                                                else:
                                                    if self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line + 8).exists:
                                                        anti_armor_target = self.known_enemy_units.not_structure.visible.filter(
                                                            lambda u: u.position.x > self.defense_line + 8).closest_to(
                                                            unit)
                                                        antiarmor = 1
                                                    else:
                                                        antiarmor = 0
                                                if antiarmor == 1:
                                                    actions.append(unit(AbilityId.EFFECT_ANTIARMORMISSILE,
                                                                        target=anti_armor_target))
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                       UnitTypeId.VIKINGFIGHTER]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.BATTLECRUISER,
                                                             UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                        hazard_dist = 13
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                            closest_hazard = self.known_enemy_units.of_type(
                                                                [UnitTypeId.MARINE]).closest_to(unit).position
                                                            hazard_dist = 10
                                                        else:
                                                            closest_hazard = ally_cc
                                                            hazard_dist = 0.1

                                                    if unit.distance_to(closest_hazard) < hazard_dist:
                                                        actions.append(
                                                            unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                    else:
                                                        if self.enemy_nuke_alert == 1:
                                                            if self.time - self.enemy_nuke_alert_time > 9:
                                                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(unit, 13)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).exists:
                                                                    target_ghost = self.known_enemy_units.of_type(
                                                                        [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                    if self.side == 1:
                                                                        if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    else:
                                                                        if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                            go_ghost = 1
                                                                        else:
                                                                            go_ghost = 0
                                                                    if go_ghost == 1:
                                                                        actions.append(unit.move(target_ghost.position))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                                else:
                                                                    if self.side == 1:
                                                                        if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    else:
                                                                        if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                            find_ghost = 1
                                                                        else:
                                                                            find_ghost = 0
                                                                    if find_ghost == 1:
                                                                        actions.append(unit.move(
                                                                            self.enemy_nuke_position.towards(ally_cc,
                                                                                                             -1)))
                                                                    else:
                                                                        if self.cloaked_enemy == 1:
                                                                            actions.append(
                                                                                unit.move(
                                                                                    self.cloaked_enemy_position[0][
                                                                                        0].towards(unit, 6)))
                                                                        else:
                                                                            if self.time - self.move_start_time > 3:
                                                                                actions.append(unit.move(
                                                                                    Point2((
                                                                                           self.defense_line - self.side * 19,
                                                                                           31.5))))
                                                                            else:
                                                                                pass
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * 19,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                            else:  # 나띵
                                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.BATTLECRUISER,
                                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                    hazard_dist = 13
                                                else:
                                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                        closest_hazard = self.known_enemy_units.of_type(
                                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                                        hazard_dist = 10
                                                    else:
                                                        closest_hazard = ally_cc
                                                        hazard_dist = 0.1

                                                if unit.distance_to(closest_hazard) < hazard_dist:
                                                    actions.append(
                                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if self.time - self.enemy_nuke_alert_time > 9:
                                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(unit, 13)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).exists:
                                                                target_ghost = self.known_enemy_units.of_type(
                                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                                if self.side == 1:
                                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                else:
                                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                        go_ghost = 1
                                                                    else:
                                                                        go_ghost = 0
                                                                if go_ghost == 1:
                                                                    actions.append(unit.move(target_ghost.position))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                            else:
                                                                if self.side == 1:
                                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                else:
                                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                        find_ghost = 1
                                                                    else:
                                                                        find_ghost = 0
                                                                if find_ghost == 1:
                                                                    actions.append(unit.move(
                                                                        self.enemy_nuke_position.towards(ally_cc, -1)))
                                                                else:
                                                                    if self.cloaked_enemy == 1:
                                                                        actions.append(
                                                                            unit.move(self.cloaked_enemy_position[0][
                                                                                          0].towards(unit, 6)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(
                                                                                Point2((
                                                                                       self.defense_line - self.side * 19,
                                                                                       31.5))))
                                                                        else:
                                                                            pass
                                                    else:
                                                        if self.cloaked_enemy == 1:
                                                            actions.append(
                                                                unit.move(
                                                                    self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(
                                                                    Point2((self.defense_line - self.side * 19, 31.5))))
                                                            else:
                                                                pass
                                        else:  # 나띵
                                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                               UnitTypeId.VIKINGFIGHTER]).exists:
                                                closest_hazard = self.known_enemy_units.of_type(
                                                    [UnitTypeId.BATTLECRUISER,
                                                     UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                                hazard_dist = 13
                                            else:
                                                if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                                    closest_hazard = self.known_enemy_units.of_type(
                                                        [UnitTypeId.MARINE]).closest_to(unit).position
                                                    hazard_dist = 10
                                                else:
                                                    closest_hazard = ally_cc
                                                    hazard_dist = 0.1

                                            if unit.distance_to(closest_hazard) < hazard_dist:
                                                actions.append(
                                                    unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if self.time - self.enemy_nuke_alert_time > 9:
                                                        if unit.distance_to(self.enemy_nuke_position) < 11:
                                                            actions.append(unit.move(
                                                                self.enemy_nuke_position.towards(unit, 13)))
                                                        else:
                                                            if self.cloaked_enemy == 1:
                                                                actions.append(
                                                                    unit.move(
                                                                        self.cloaked_enemy_position[0][0].towards(unit,
                                                                                                                  6)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(
                                                                        Point2((self.defense_line - self.side * 19,
                                                                                31.5))))
                                                                else:
                                                                    pass
                                                    else:
                                                        if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                            target_ghost = self.known_enemy_units.of_type(
                                                                [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                            if self.side == 1:
                                                                if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            else:
                                                                if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                                    go_ghost = 1
                                                                else:
                                                                    go_ghost = 0
                                                            if go_ghost == 1:
                                                                actions.append(unit.move(target_ghost.position))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                        else:
                                                            if self.side == 1:
                                                                if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            else:
                                                                if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                                    find_ghost = 1
                                                                else:
                                                                    find_ghost = 0
                                                            if find_ghost == 1:
                                                                actions.append(unit.move(
                                                                    self.enemy_nuke_position.towards(ally_cc, -1)))
                                                            else:
                                                                if self.cloaked_enemy == 1:
                                                                    actions.append(
                                                                        unit.move(
                                                                            self.cloaked_enemy_position[0][0].towards(
                                                                                unit, 6)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(
                                                                            Point2((self.defense_line - self.side * 19,
                                                                                    31.5))))
                                                                    else:
                                                                        pass
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 19, 31.5))))
                                                        else:
                                                            pass
                            else:  # 후퇴
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER,
                                                                   UnitTypeId.VIKINGFIGHTER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.BATTLECRUISER,
                                         UnitTypeId.VIKINGFIGHTER]).closest_to(unit).position
                                    hazard_dist = 13
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE]).closest_to(unit).position
                                        hazard_dist = 10
                                    else:
                                        closest_hazard = ally_cc
                                        hazard_dist = 0.1

                                if unit.distance_to(closest_hazard) < hazard_dist:
                                    actions.append(
                                        unit.move(closest_hazard.towards(unit, hazard_dist + 2)))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if self.time - self.enemy_nuke_alert_time > 9:
                                            if unit.distance_to(self.enemy_nuke_position) < 11:
                                                actions.append(unit.move(
                                                    self.enemy_nuke_position.towards(unit, 13)))
                                            else:
                                                if self.cloaked_enemy == 1:
                                                    actions.append(
                                                        unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(
                                                            Point2((self.defense_line - self.side * 19, 31.5))))
                                                    else:
                                                        pass
                                        else:
                                            if self.known_enemy_units.of_type([UnitTypeId.GHOST]).exists:
                                                target_ghost = self.known_enemy_units.of_type(
                                                    [UnitTypeId.GHOST]).closest_to(ally_cc)
                                                if self.side == 1:
                                                    if target_ghost.position.x < self.defense_line - self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                else:
                                                    if target_ghost.position.x > self.defense_line + self.nuke_ghost_maginot:
                                                        go_ghost = 1
                                                    else:
                                                        go_ghost = 0
                                                if go_ghost == 1:
                                                    actions.append(unit.move(target_ghost.position))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 19, 31.5))))
                                                        else:
                                                            pass
                                            else:
                                                if self.side == 1:
                                                    if self.enemy_nuke_position.x < self.defense_line - self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                else:
                                                    if self.enemy_nuke_position.x > self.defense_line + self.find_nuke_maginot:
                                                        find_ghost = 1
                                                    else:
                                                        find_ghost = 0
                                                if find_ghost == 1:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(ally_cc, -1)))
                                                else:
                                                    if self.cloaked_enemy == 1:
                                                        actions.append(
                                                            unit.move(
                                                                self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 19, 31.5))))
                                                        else:
                                                            pass
                                    else:
                                        if self.cloaked_enemy == 1:
                                            actions.append(
                                                unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                        else:
                                            if self.time - self.move_start_time > 3:
                                                actions.append(unit.move(
                                                    Point2((self.defense_line - self.side * 19, 31.5))))
                                            else:
                                                pass
                        else:
                            if self.side == 1:
                                if 40 - unit.position.x > 0:
                                    actions.append(unit.move(Point2((40, 31.5))))
                                else:
                                    pass
                            else:
                                if unit.position.x - (88) > 0:
                                    actions.append(unit.move(Point2((88, 31.5))))
                                else:
                                    pass
                else: # self.enemy_tp == 1
                    if self.enemy_nuke_alert == 1 and self.time - self.enemy_nuke_alert_time > 10:
                        if unit.distance_to(self.enemy_nuke_position) < 10:
                            need_avoid = 1
                        else:
                            need_avoid = 0
                    else:
                        need_avoid = 0

                    if self.time - self.enemy_tp_time > 4.4:
                        if unit.energy > 50:  # need to change -> 50 later (version) 밤까마나수정
                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                target_found = 0
                                for mat_target in self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]):
                                    if (not mat_target.has_buff(BuffId.RAVENSCRAMBLERMISSILE)) and unit.distance_to(mat_target) < 25:
                                        already_target = 0
                                        for list_i in range(len(self.raven_matrix_target)):
                                            if self.raven_matrix_target[list_i][0] == mat_target.tag:
                                                already_target = 1
                                            else:
                                                pass
                                        if already_target == 0:
                                            target_found = 1
                                            break
                                        else:
                                            pass
                                    else:
                                        pass
                                if target_found == 1:
                                    if self.time - self.raven_matrix_time.get(unit.tag, 0) > 0.5 and unit.distance_to(mat_target) < 9:
                                        print("shot")
                                        actions.append(unit(AbilityId.EFFECT_INTERFERENCEMATRIX, target=mat_target))
                                        self.raven_matrix_target.append([mat_target.tag, self.time])
                                        self.raven_matrix_time[unit.tag] = self.time
                                    else:
                                        actions.append(unit.move(mat_target.position.towards(unit, 9)))
                                else:
                                    if need_avoid == 1:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                    else:
                                        if self.cloaked_enemy == 1:
                                            actions.append(
                                                unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                        else:
                                            actions.append(unit.move(self.enemy_tp_position))
                            else:
                                if need_avoid == 1:
                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                else:
                                    if self.cloaked_enemy == 1:
                                        actions.append(unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                    else:
                                        actions.append(unit.move(self.enemy_tp_position))
                        else:
                            if need_avoid == 1:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                            else:
                                if self.cloaked_enemy == 1:
                                    actions.append(unit.move(self.cloaked_enemy_position[0][0].towards(unit, 6)))
                                else:
                                    actions.append(unit.move(self.enemy_tp_position))
                    else:
                        if need_avoid == 1:
                            actions.append(unit.move(self.enemy_nuke_position.towards(unit,13)))
                        else:
                            actions.append(unit.move(self.enemy_tp_position))

            elif unit.type_id is UnitTypeId.MARINE:
                mar_list = list(self.marine_pos_num.values())
                mar_list.sort()
                mar_num = 0
                for i in range(len(mar_list)):
                    if i != mar_list[i] - 1:
                        mar_num = i
                        break
                    elif i == mar_list[i] - 1 and i == len(mar_list) - 1:
                        mar_num = i + 1
                    else:
                        continue
                mar_num = mar_num + 1
                if self.marine_pos_num.get(unit.tag, -2) == -2:
                    self.marine_pos_num[unit.tag] = mar_num
                    marine_target_pos_x, marine_target_pos_y = self.defense_position(mar_num, UnitTypeId.MARINE)
                    self.marine_position[(unit.tag, 'x')] = marine_target_pos_x
                    self.marine_position[(unit.tag, 'y')] = marine_target_pos_y
                    marine_target_position = Point2(Point2((marine_target_pos_x, marine_target_pos_y)))
                    self.marine_position[(unit.tag, 't')] = self.time
                else:
                    mar_num = self.marine_pos_num[unit.tag]
                    marine_target_pos_x, marine_target_pos_y = self.defense_position(mar_num, UnitTypeId.MARINE)
                    if self.marine_position[(unit.tag, 'x')] == marine_target_pos_x and self.marine_position[(unit.tag, 'y')] == marine_target_pos_y:
                        marine_target_position = Point2(Point2(
                            (self.marine_position.get((unit.tag, 'x'), 0),
                             self.marine_position.get((unit.tag, 'y'), 0))))
                    else:
                        self.marine_position[(unit.tag, 'x')] = marine_target_pos_x
                        self.marine_position[(unit.tag, 'y')] = marine_target_pos_y
                        marine_target_position = Point2(Point2(
                            (self.marine_position.get((unit.tag, 'x'), 0),
                             self.marine_position.get((unit.tag, 'y'), 0))))
                if self.game_time > 165 and (mar_num <= 25) and (mar_num >= 19) and (self.enemy_is_MARAUDER == 0):
                    if self.known_enemy_units(UnitTypeId.BATTLECRUISER).exists:
                        target = self.known_enemy_units(UnitTypeId.BATTLECRUISER).closest_to(ally_cc)
                        if target.distance_to(ally_cc) < 20:
                            actions.append(unit.attack(target))
                        else:
                            actions.append(unit.attack(unit.position))
                    else:
                        if self.side == 1:
                            mp_x = 15
                            cp_x = 32.5
                        else:
                            mp_x = 110
                            cp_x = 95.5
                        if mar_num == 20:
                            actions.append(unit.attack(Point2((mp_x,10))))
                        elif mar_num == 19:
                            actions.append(unit.attack(Point2((mp_x,30))))
                        elif mar_num == 21:
                            actions.append(unit.attack(Point2((mp_x,50))))
                        elif mar_num == 22:
                            actions.append(unit.attack(Point2((mp_x + self.side * 5, 20))))
                        elif mar_num == 23:
                            actions.append(unit.attack(Point2((mp_x + self.side * 5, 40))))
                        elif mar_num == 24:
                            actions.append(unit.attack(Point2((cp_x, 10))))
                        else:
                            actions.append(unit.attack(Point2((cp_x, 50))))
                else:
                    if self.is_combat == 1:
                        if unit.distance_to(ally_cc) < 10 and self.enemy_tp == 1:
                            if self.known_enemy_units(UnitTypeId.BATTLECRUISER).exists:
                                target_battle = self.known_enemy_units(UnitTypeId.BATTLECRUISER).closest_to(unit)
                                if unit.distance_to(target_battle) < 13:
                                    kill_kill_battle = 1
                                else:
                                    kill_kill_battle = 0
                            else:
                                kill_kill_battle = 0
                        else:
                            kill_kill_battle = 0

                        if self.enemy_nuke_alert == 1 and self.time - self.enemy_nuke_alert_time > 9:
                            if unit.distance_to(self.enemy_nuke_position) < 10:
                                if self.side == 1:
                                    if unit.position.x < self.defense_line - 20:
                                        a = 1
                                    else:
                                        a = 0
                                else:
                                    if unit.position.x > self.defense_line + 20:
                                        a = 1
                                    else:
                                        a = 0
                                if a == 1:
                                    need_avoid = 1
                                else:
                                    need_avoid = 0
                            else:
                                need_avoid = 0
                        else:
                            need_avoid = 0
                        if self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.exists:
                            t_ghost = self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)
                            if unit.distance_to(t_ghost) < 5:
                                kill_kill_ghost = 1
                            else:
                                kill_kill_ghost = 0
                        else:
                            kill_kill_ghost = 0

                        if self.known_enemy_units.not_structure.visible.exists:
                            enemy_unit = self.known_enemy_units.not_structure.visible.closest_to(unit)
                            if self.side == 1:
                                if enemy_unit.position.x < self.defense_line - 6:
                                    mar_attack = 1
                                else:
                                    mar_attack = 0
                            else:
                                if enemy_unit.position.x > self.defense_line + 6:
                                    mar_attack = 1
                                else:
                                    mar_attack = 0
                            if mar_attack == 1:
                                if not unit.has_buff(BuffId.STIMPACK) and unit.health_percentage > 0.5 and (self.enemy_close_counter > 4):
                                    # 현재 스팀팩 사용중이 아니며, 체력이 50% 이상
                                    if self.time - self.evoked.get((unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                        # 1초 이전에 스팀팩을 사용한 적이 없음
                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                        self.evoked[(unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                if unit.weapon_cooldown < 10:
                                    if need_avoid == 1:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit,11)))
                                    else:
                                        if kill_kill_ghost == 1:
                                            actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)))
                                        else:
                                            if kill_kill_battle == 1:
                                                actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(unit)))
                                            else:
                                                actions.append(unit.attack(enemy_unit.position.towards(unit, 2)))
                                else:
                                    x = enemy_unit.position.towards(unit, 3).x + 5 * self.side
                                    y = enemy_unit.position.towards(unit, 3).y
                                    if need_avoid == 1:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit,11)))
                                    else:
                                        if kill_kill_ghost == 1:
                                            actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit)))
                                        else:
                                            if kill_kill_battle == 1:
                                                actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(unit)))
                                            else:
                                                actions.append(unit.move(Point2((x, y))))
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit,11)))
                                    else:
                                        if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                            enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(unit)
                                            if self.side == 1:
                                                if enemy_ghost.position.x < self.defense_line - 8:
                                                    kill_ghost = 1
                                                else:
                                                    kill_ghost = 0
                                            else:
                                                if enemy_ghost.position.x > self.defense_line + 8:
                                                    kill_ghost = 1
                                                else:
                                                    kill_ghost = 0

                                            if kill_ghost == 1 and self.game_time < 130:
                                                actions.append(unit.attack(
                                                    enemy_ghost.position.towards(unit, 0.5)))
                                            else:
                                                if self.game_time < 60 and self.known_enemy_units(
                                                        UnitTypeId.BANSHEE).exists and self.units(
                                                        UnitTypeId.RAVEN).amount < 1:
                                                    actions.append(unit.move(ally_cc))
                                                else:
                                                    actions.append(unit.move(marine_target_position))
                                        else:
                                            if self.game_time < 60 and self.known_enemy_units(
                                                    UnitTypeId.BANSHEE).exists and self.units(UnitTypeId.RAVEN).amount < 1:
                                                actions.append(unit.move(ally_cc))
                                            else:
                                                actions.append(unit.move(marine_target_position))

                                else:
                                    if self.game_time < 60 and self.known_enemy_units(
                                            UnitTypeId.BANSHEE).exists and self.units(UnitTypeId.RAVEN).amount < 1:
                                        actions.append(unit.move(ally_cc))
                                    else:
                                        actions.append(unit.move(marine_target_position))
                        else:
                            if self.enemy_nuke_alert == 1:
                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                else:
                                    if self.known_enemy_units(UnitTypeId.GHOST).exists:
                                        enemy_ghost = self.known_enemy_units(UnitTypeId.GHOST).closest_to(unit)
                                        if self.side == 1:
                                            if enemy_ghost.position.x < self.defense_line - 8:
                                                kill_ghost = 1
                                            else:
                                                kill_ghost = 0
                                        else:
                                            if enemy_ghost.position.x > self.defense_line + 8:
                                                kill_ghost = 1
                                            else:
                                                kill_ghost = 0

                                        if kill_ghost == 1 and self.game_time < 130:
                                            actions.append(unit.attack(
                                                enemy_ghost.position.towards(unit, 0.5)))
                                        else:
                                            if self.game_time < 60 and self.known_enemy_units(
                                                    UnitTypeId.BANSHEE).exists and self.units(UnitTypeId.RAVEN).amount < 1:
                                                actions.append(unit.move(ally_cc))
                                            else:
                                                actions.append(unit.move(marine_target_position))
                                    else:
                                        if self.game_time < 60 and self.known_enemy_units(
                                                UnitTypeId.BANSHEE).exists and self.units(UnitTypeId.RAVEN).amount < 1:
                                            actions.append(unit.move(ally_cc))
                                        else:
                                            actions.append(unit.move(marine_target_position))

                            else:
                                if self.game_time < 60 and self.known_enemy_units(UnitTypeId.BANSHEE).exists and self.units(UnitTypeId.RAVEN).amount < 1:
                                    actions.append(unit.move(ally_cc))
                                else:
                                    actions.append(unit.move(marine_target_position))
                    elif self.is_combat == 0:
                        my_cc = self.units(UnitTypeId.COMMANDCENTER).closest_to(ally_cc)
                        if self.game_time < 60:
                            tp_bool = 1
                        else:
                            if my_cc.health_percentage < 0.8 or (
                                    self.units(UnitTypeId.VIKINGFIGHTER).amount < self.known_enemy_units.of_type(
                                    [UnitTypeId.BATTLECRUISER]).amount * 3 and self.units(
                                    UnitTypeId.RAVEN).amount * 2 < self.known_enemy_units.of_type(
                                    [UnitTypeId.BATTLECRUISER]).amount) or self.time - self.enemy_tp_time > 10:
                                tp_bool = 1
                            else:
                                tp_bool = 0
                        if self.enemy_tp == 1 and mar_num < 999 and tp_bool == 1: # 적텔포 반응
                            # 여기에욧
                            if self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.exists:
                                ghost_x = self.known_enemy_units.of_type([UnitTypeId.GHOST]).visible.closest_to(unit).position.x
                                if self.side == 1:
                                    if ghost_x < self.defense_line - 10:
                                        kill_ghost = 1
                                    else:
                                        kill_ghost = 0
                                else:
                                    if ghost_x > self.defense_line + 10:
                                        kill_ghost = 1
                                    else:
                                        kill_ghost = 0
                            else:
                                kill_ghost = 0

                            if self.enemy_nuke_alert == 1 and self.time - self.enemy_nuke_alert_time > 10:
                                if unit.distance_to(self.enemy_nuke_position) < 10:
                                    need_avoid = 1
                                else:
                                    need_avoid = 0
                            else:
                                need_avoid = 0
                            if self.time - self.enemy_tp_time > 1:
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                    closest_target = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(
                                        unit)
                                    if not unit.has_buff(BuffId.STIMPACK) and unit.health_percentage > 0.5:
                                        # 현재 스팀팩 사용중이 아니며, 체력이 50% 이상
                                        if self.time - self.evoked.get((unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                            # 1초 이전에 스팀팩을 사용한 적이 없음
                                            if unit.distance_to(enemy_cc) < 15:
                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                self.evoked[(unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                    if need_avoid == 1:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                    else:
                                        if kill_ghost == 1:
                                            actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).closest_to(unit)))
                                        else:
                                            actions.append(unit.attack(closest_target))
                                else:
                                    if need_avoid == 1:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                    else:
                                        if kill_ghost == 1:
                                            actions.append(unit.attack(self.known_enemy_units.of_type([UnitTypeId.GHOST]).closest_to(unit)))
                                        else:
                                            actions.append(unit.attack(unit.position))
                            else:
                                if not unit.has_buff(BuffId.STIMPACK) and unit.health_percentage > 0.5:
                                    # 현재 스팀팩 사용중이 아니며, 체력이 50% 이상
                                    if self.time - self.evoked.get((unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                        # 1초 이전에 스팀팩을 사용한 적이 없음
                                        if unit.distance_to(enemy_cc) < 15:
                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                            self.evoked[(unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                if need_avoid == 1:
                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                                else:
                                    if kill_ghost == 1:
                                        actions.append(unit.attack(
                                            self.known_enemy_units.of_type([UnitTypeId.GHOST]).closest_to(unit)))
                                    else:
                                        actions.append(unit.move(ally_cc))
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.BANSHEE]).exists:
                                closest_hazard = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.BANSHEE]).closest_to(unit)
                                if unit.distance_to(closest_hazard) < 9.5:
                                    m_x = unit.position.x - 3 * self.side
                                    m_y = unit.position.y
                                    actions.append(unit.move(Point2((m_x, m_y))))
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).closest_to(unit)
                                        if closest_hazard.type_id == UnitTypeId.HELLION or closest_hazard.type_id == UnitTypeId.MARAUDER:
                                            safe_dist = 10
                                        else:
                                            safe_dist = 8
                                        if unit.distance_to(closest_hazard) < safe_dist:
                                            m_x = unit.position.x - 5 * self.side
                                            m_y = unit.position.y
                                            actions.append(unit.move(Point2((m_x, m_y))))
                                        else:
                                            if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                                closest_target = self.known_enemy_units.of_type(
                                                    [UnitTypeId.VIKINGFIGHTER]).closest_to(unit)
                                                if self.side == 1:
                                                    if closest_target.position.x < self.defense_line - 6:
                                                        mar_attack_bool = 1
                                                    else:
                                                        mar_attack_bool = 0
                                                else:
                                                    if closest_target.position.x > self.defense_line + 6:
                                                        mar_attack_bool = 1
                                                    else:
                                                        mar_attack_bool = 0
                                                if mar_attack_bool == 1:
                                                    actions.append(unit.attack(closest_target))
                                                else:
                                                    if self.enemy_nuke_alert == 1:
                                                        if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                            actions.append(unit.move(
                                                                self.enemy_nuke_position.towards(unit, 11)))
                                                        else:
                                                            if self.need_kill_ghost == 1:
                                                                if self.known_enemy_units(
                                                                        UnitTypeId.GHOST).exists:
                                                                    enemy_ghost = self.known_enemy_units(
                                                                        UnitTypeId.GHOST).closest_to(unit)
                                                                    if unit.distance_to(enemy_ghost) < 25:
                                                                        actions.append(unit.attack(
                                                                            enemy_ghost.position.towards(unit, 1)))
                                                                    else:
                                                                        if self.time - self.move_start_time > 3:
                                                                            actions.append(unit.move(marine_target_position))
                                                                        else:
                                                                            if mar_num == 1:
                                                                                if not unit.has_buff(BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(marine_target_position) > 15:
                                                                                    if self.time - self.evoked.get((unit.tag,AbilityId.EFFECT_STIM),0) > 1.0:
                                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                            self.evoked[(unit.tag,AbilityId.EFFECT_STIM)] = self.time
                                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                            else:
                                                                                actions.append(unit.attack(unit.position))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(marine_target_position))
                                                                    else:
                                                                        if mar_num == 1:
                                                                            if not unit.has_buff(
                                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                    marine_target_position) > 15:
                                                                                if self.time - self.evoked.get(
                                                                                        (unit.tag, AbilityId.EFFECT_STIM),
                                                                                        0) > 1.0:
                                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                                        actions.append(
                                                                                            unit(AbilityId.EFFECT_STIM))
                                                                                        self.evoked[(unit.tag,
                                                                                                     AbilityId.EFFECT_STIM)] = self.time
                                                                            actions.append(
                                                                                unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                        else:
                                                                            actions.append(unit.attack(unit.position))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.need_kill_ghost == 1:
                                                            if self.known_enemy_units(
                                                                    UnitTypeId.GHOST).exists:
                                                                enemy_ghost = self.known_enemy_units(
                                                                    UnitTypeId.GHOST).closest_to(unit)
                                                                if unit.distance_to(enemy_ghost) < 25:
                                                                    actions.append(unit.attack(
                                                                        enemy_ghost.position.towards(unit, 1)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(marine_target_position))
                                                                    else:
                                                                        if mar_num == 1:
                                                                            if not unit.has_buff(
                                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                    marine_target_position) > 15:
                                                                                if self.time - self.evoked.get(
                                                                                        (unit.tag, AbilityId.EFFECT_STIM),
                                                                                        0) > 1.0:
                                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                                        actions.append(
                                                                                            unit(AbilityId.EFFECT_STIM))
                                                                                        self.evoked[(unit.tag,
                                                                                                     AbilityId.EFFECT_STIM)] = self.time
                                                                            actions.append(
                                                                                unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                        else:
                                                                            actions.append(unit.attack(unit.position))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                        actions.append(unit.move(
                                                            self.enemy_nuke_position.towards(unit, 11)))
                                                    else:
                                                        if self.need_kill_ghost == 1:
                                                            if self.known_enemy_units(
                                                                    UnitTypeId.GHOST).exists:
                                                                enemy_ghost = self.known_enemy_units(
                                                                    UnitTypeId.GHOST).closest_to(unit)
                                                                if unit.distance_to(enemy_ghost) < 25:
                                                                    actions.append(unit.attack(
                                                                        enemy_ghost.position.towards(unit, 1)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(marine_target_position))
                                                                    else:
                                                                        if mar_num == 1:
                                                                            if not unit.has_buff(
                                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                    marine_target_position) > 15:
                                                                                if self.time - self.evoked.get(
                                                                                        (unit.tag, AbilityId.EFFECT_STIM),
                                                                                        0) > 1.0:
                                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                                        actions.append(
                                                                                            unit(AbilityId.EFFECT_STIM))
                                                                                        self.evoked[(unit.tag,
                                                                                                     AbilityId.EFFECT_STIM)] = self.time
                                                                            actions.append(
                                                                                unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                        else:
                                                                            actions.append(unit.attack(unit.position))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(Point2((marine_target_position.x + self.side * 5, marine_target_position.y)))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))

                                    else:
                                        if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                            closest_target = self.known_enemy_units.of_type(
                                                [UnitTypeId.VIKINGFIGHTER]).closest_to(
                                                unit)
                                            if self.side == 1:
                                                if closest_target.position.x < self.defense_line - 6:
                                                    mar_attack_bool = 1
                                                else:
                                                    mar_attack_bool = 0
                                            else:
                                                if closest_target.position.x > self.defense_line + 6:
                                                    mar_attack_bool = 1
                                                else:
                                                    mar_attack_bool = 0
                                            if mar_attack_bool == 1:
                                                actions.append(unit.attack(closest_target))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                        actions.append(unit.move(
                                                            self.enemy_nuke_position.towards(unit, 11)))
                                                    else:
                                                        if self.need_kill_ghost == 1:
                                                            if self.known_enemy_units(
                                                                    UnitTypeId.GHOST).exists:
                                                                enemy_ghost = self.known_enemy_units(
                                                                    UnitTypeId.GHOST).closest_to(unit)
                                                                if unit.distance_to(enemy_ghost) < 25:
                                                                    actions.append(unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(marine_target_position))
                                                                    else:
                                                                        if mar_num == 1:
                                                                            if not unit.has_buff(
                                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                    marine_target_position) > 15:
                                                                                if self.time - self.evoked.get(
                                                                                        (unit.tag, AbilityId.EFFECT_STIM),
                                                                                        0) > 1.0:
                                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                                        actions.append(
                                                                                            unit(AbilityId.EFFECT_STIM))
                                                                                        self.evoked[(unit.tag,
                                                                                                     AbilityId.EFFECT_STIM)] = self.time
                                                                            actions.append(
                                                                                unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                        else:
                                                                            actions.append(unit.attack(unit.position))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                    actions.append(unit.move(
                                                        self.enemy_nuke_position.towards(unit, 11)))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))

                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(
                                                                unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if mar_num == 1:
                                                            if not unit.has_buff(
                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                    marine_target_position) > 15:
                                                                if self.time - self.evoked.get(
                                                                        (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                                                        self.evoked[
                                                                            (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                            actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                        else:
                                                            actions.append(unit.attack(unit.position))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.HELLION, UnitTypeId.MARAUDER]).closest_to(unit)
                                    if closest_hazard.type_id == UnitTypeId.HELLION or closest_hazard.type_id == UnitTypeId.MARAUDER:
                                        safe_dist = 10
                                    else:
                                        safe_dist = 8
                                    if unit.distance_to(closest_hazard) < safe_dist:
                                        m_x = unit.position.x - 5 * self.side
                                        m_y = unit.position.y
                                        actions.append(unit.move(Point2((m_x, m_y))))
                                    else:
                                        if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                            closest_target = self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).closest_to(unit)
                                            if self.side == 1:
                                                if closest_target.position.x < self.defense_line - 6:
                                                    mar_attack_bool = 1
                                                else:
                                                    mar_attack_bool = 0
                                            else:
                                                if closest_target.position.x > self.defense_line + 6:
                                                    mar_attack_bool = 1
                                                else:
                                                    mar_attack_bool = 0
                                            if mar_attack_bool == 1:
                                                actions.append(unit.attack(closest_target))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                        actions.append(unit.move(
                                                            self.enemy_nuke_position.towards(unit, 11)))
                                                    else:
                                                        if self.need_kill_ghost == 1:
                                                            if self.known_enemy_units(
                                                                    UnitTypeId.GHOST).exists:
                                                                enemy_ghost = self.known_enemy_units(
                                                                    UnitTypeId.GHOST).closest_to(unit)
                                                                if unit.distance_to(enemy_ghost) < 25:
                                                                    actions.append(unit.attack(
                                                                        enemy_ghost.position.towards(unit, 1)))
                                                                else:
                                                                    if self.time - self.move_start_time > 3:
                                                                        actions.append(unit.move(marine_target_position))
                                                                    else:
                                                                        if mar_num == 1:
                                                                            if not unit.has_buff(
                                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                    marine_target_position) > 15:
                                                                                if self.time - self.evoked.get(
                                                                                        (unit.tag, AbilityId.EFFECT_STIM),
                                                                                        0) > 1.0:
                                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                                        actions.append(
                                                                                            unit(AbilityId.EFFECT_STIM))
                                                                                        self.evoked[(unit.tag,
                                                                                                     AbilityId.EFFECT_STIM)] = self.time
                                                                            actions.append(
                                                                                unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                        else:
                                                                            actions.append(unit.attack(unit.position))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                    actions.append(unit.move(
                                                        self.enemy_nuke_position.towards(unit, 11)))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))

                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(
                                                                unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if mar_num == 1:
                                                            if not unit.has_buff(
                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                    marine_target_position) > 15:
                                                                if self.time - self.evoked.get(
                                                                        (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                                                        self.evoked[
                                                                            (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                            actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                        else:
                                                            actions.append(unit.attack(unit.position))

                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).exists:
                                        closest_target = self.known_enemy_units.of_type([UnitTypeId.VIKINGFIGHTER]).closest_to(
                                            unit)
                                        if self.side == 1:
                                            if closest_target.position.x < self.defense_line - 6:
                                                mar_attack_bool = 1
                                            else:
                                                mar_attack_bool = 0
                                        else:
                                            if closest_target.position.x > self.defense_line + 6:
                                                mar_attack_bool = 1
                                            else:
                                                mar_attack_bool = 0
                                        if mar_attack_bool == 1:
                                            actions.append(unit.attack(closest_target))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                    actions.append(unit.move(
                                                        self.enemy_nuke_position.towards(unit, 11)))
                                                else:
                                                    if self.need_kill_ghost == 1:
                                                        if self.known_enemy_units(
                                                                UnitTypeId.GHOST).exists:
                                                            enemy_ghost = self.known_enemy_units(
                                                                UnitTypeId.GHOST).closest_to(unit)
                                                            if unit.distance_to(enemy_ghost) < 25:
                                                                actions.append(unit.attack(
                                                                    enemy_ghost.position.towards(unit, 1)))
                                                            else:
                                                                if self.time - self.move_start_time > 3:
                                                                    actions.append(unit.move(marine_target_position))
                                                                else:
                                                                    if mar_num == 1:
                                                                        if not unit.has_buff(
                                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                                marine_target_position) > 15:
                                                                            if self.time - self.evoked.get(
                                                                                    (unit.tag, AbilityId.EFFECT_STIM),
                                                                                    0) > 1.0:
                                                                                if unit.distance_to(enemy_cc) < 15:
                                                                                    actions.append(
                                                                                        unit(AbilityId.EFFECT_STIM))
                                                                                    self.evoked[(unit.tag,
                                                                                                 AbilityId.EFFECT_STIM)] = self.time
                                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                    else:
                                                                        actions.append(unit.attack(unit.position))
                                                        else:
                                                            if self.time - self.move_start_time > 3:
                                                                actions.append(unit.move(marine_target_position))
                                                            else:
                                                                if mar_num == 1:
                                                                    if not unit.has_buff(
                                                                            BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                            marine_target_position) > 15:
                                                                        if self.time - self.evoked.get(
                                                                                (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                            if unit.distance_to(enemy_cc) < 15:
                                                                                actions.append(unit(AbilityId.EFFECT_STIM))
                                                                                self.evoked[(unit.tag,
                                                                                             AbilityId.EFFECT_STIM)] = self.time
                                                                    actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                                else:
                                                                    actions.append(unit.attack(unit.position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(
                                                                unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if mar_num == 1:
                                                            if not unit.has_buff(
                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                    marine_target_position) > 15:
                                                                if self.time - self.evoked.get(
                                                                        (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                                                        self.evoked[
                                                                            (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                            actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                        else:
                                                            actions.append(unit.attack(unit.position))

                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 10 and self.time - self.enemy_nuke_alert_time > 7:
                                                actions.append(unit.move(
                                                    self.enemy_nuke_position.towards(unit, 11)))
                                            else:
                                                if self.need_kill_ghost == 1:
                                                    if self.known_enemy_units(
                                                            UnitTypeId.GHOST).exists:
                                                        enemy_ghost = self.known_enemy_units(
                                                            UnitTypeId.GHOST).closest_to(unit)
                                                        if unit.distance_to(enemy_ghost) < 25:
                                                            actions.append(
                                                                unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                        else:
                                                            actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if self.time - self.move_start_time > 3:
                                                            actions.append(unit.move(marine_target_position))
                                                        else:
                                                            if mar_num == 1:
                                                                if not unit.has_buff(
                                                                        BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                        marine_target_position) > 15:
                                                                    if self.time - self.evoked.get(
                                                                            (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                        if unit.distance_to(enemy_cc) < 15:
                                                                            actions.append(unit(AbilityId.EFFECT_STIM))
                                                                            self.evoked[(
                                                                            unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                                actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                            else:
                                                                actions.append(unit.attack(unit.position))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if mar_num == 1:
                                                            if not unit.has_buff(
                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                    marine_target_position) > 15:
                                                                if self.time - self.evoked.get(
                                                                        (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                                                        self.evoked[
                                                                            (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                            actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                        else:
                                                            actions.append(unit.attack(unit.position))

                                        else:
                                            if self.need_kill_ghost == 1:
                                                if self.known_enemy_units(
                                                        UnitTypeId.GHOST).exists:
                                                    enemy_ghost = self.known_enemy_units(
                                                        UnitTypeId.GHOST).closest_to(unit)
                                                    if unit.distance_to(enemy_ghost) < 25:
                                                        actions.append(
                                                            unit.attack(enemy_ghost.position.towards(unit, 1)))
                                                    else:
                                                        actions.append(unit.move(marine_target_position))
                                                else:
                                                    if self.time - self.move_start_time > 3:
                                                        actions.append(unit.move(marine_target_position))
                                                    else:
                                                        if mar_num == 1:
                                                            if not unit.has_buff(
                                                                    BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                    marine_target_position) > 15:
                                                                if self.time - self.evoked.get(
                                                                        (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                    if unit.distance_to(enemy_cc) < 15:
                                                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                                                        self.evoked[
                                                                            (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                            actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                        else:
                                                            actions.append(unit.attack(unit.position))
                                            else:
                                                if self.time - self.move_start_time > 3:
                                                    actions.append(unit.move(marine_target_position))
                                                else:
                                                    if mar_num == 1:
                                                        if not unit.has_buff(
                                                                BuffId.STIMPACK) and unit.health_percentage > 0.5 and unit.distance_to(
                                                                marine_target_position) > 15:
                                                            if self.time - self.evoked.get(
                                                                    (unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                                                if unit.distance_to(enemy_cc) < 15:
                                                                    actions.append(unit(AbilityId.EFFECT_STIM))
                                                                    self.evoked[
                                                                        (unit.tag, AbilityId.EFFECT_STIM)] = self.time
                                                        actions.append(unit.move(Point2((marine_target_position.x + self.side * 5, marine_target_position.y))))
                                                    else:
                                                        actions.append(unit.attack(unit.position))
                    else:
                        if self.time - self.end_game_time > self.move_adjust[UnitTypeId.MARINE]:
                            actions.append(unit.attack(enemy_cc))
                            if not unit.has_buff(BuffId.STIMPACK) and unit.health_percentage > 0.5:
                                # 현재 스팀팩 사용중이 아니며, 체력이 50% 이상
                                if self.time - self.evoked.get((unit.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                                    # 1초 이전에 스팀팩을 사용한 적이 없음
                                    if unit.distance_to(enemy_cc) < 15:
                                        actions.append(unit(AbilityId.EFFECT_STIM))
                                        self.evoked[(unit.tag, AbilityId.EFFECT_STIM)] = self.time
                        else:
                            if self.enemy_tp == 1:
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                    target = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(unit)
                                    actions.append(unit.attack(target))
                                else:
                                    actions.append(unit.attack(ally_cc))
                            else:
                                if self.units(UnitTypeId.SIEGETANK).exists:
                                    actions.append(unit.attack(Point2(
                                        (self.units(UnitTypeId.SIEGETANK).closest_to(unit).position.x, unit.position.y))))
                                else:
                                    if self.units(UnitTypeId.SIEGETANKSIEGED).exists:
                                        actions.append(unit.attack(Point2(
                                            (self.units(UnitTypeId.SIEGETANKSIEGED).closest_to(unit).position.x, unit.position.y))))

                                    actions.append(unit.attack(Point2((unit.position.x, unit.position.y))))

                            # actions.append(unit.hold_position())

            elif unit.type_id is UnitTypeId.SIEGETANK:
                tank_list = list(self.tank_pos_num.values())
                tank_list.sort()
                tank_num = 0
                for i in range(len(tank_list)):
                    if i != tank_list[i] - 1:
                        tank_num = i
                        break
                    elif i == tank_list[i] - 1 and i == len(tank_list) - 1:
                        tank_num = i + 1
                    else:
                        continue
                tank_num = tank_num + 1

                if self.tank_pos_num.get(unit.tag, -2) == -2:
                    self.tank_pos_num[unit.tag] = tank_num
                    tank_target_pos_x, tank_target_pos_y = self.defense_position(tank_num,
                                                                                 UnitTypeId.SIEGETANK)
                    self.tank_position[(unit.tag, 'x')] = tank_target_pos_x
                    self.tank_position[(unit.tag, 'y')] = tank_target_pos_y
                    tank_target_position = Point2(Point2((tank_target_pos_x, tank_target_pos_y)))
                else:
                    tank_num = self.tank_pos_num[unit.tag]
                    tank_target_pos_x, tank_target_pos_y = self.defense_position(tank_num,UnitTypeId.SIEGETANK)
                    if self.tank_position[(unit.tag, 'x')] == tank_target_pos_x and self.tank_position[
                        (unit.tag, 'y')] == tank_target_pos_y:
                        tank_target_position = Point2(Point2(
                            (self.tank_position.get((unit.tag, 'x'), 0),
                             self.tank_position.get((unit.tag, 'y'), 0))))
                    else:
                        self.tank_position[(unit.tag, 'x')] = tank_target_pos_x
                        self.tank_position[(unit.tag, 'y')] = tank_target_pos_y
                        tank_target_position = Point2(Point2(
                            (self.tank_position.get((unit.tag, 'x'), 0),
                             self.tank_position.get((unit.tag, 'y'), 0))))

                if tank_num == 1:
                    self.moving_line[0] = unit.position.x + self.side * 20
                    self.moving_line[1] = self.time
                else:
                    if tank_num == 2:
                        if self.time - self.moving_line[1] > 0.5:
                            self.moving_line[0] = unit.position.x + self.side * 20
                            self.moving_line[1] = self.time
                        else:
                            pass
                    else:
                        if tank_num == 3:
                            if self.time - self.moving_line[1] > 0.5:
                                self.moving_line[0] = unit.position.x + self.side * 20
                                self.moving_line[1] = self.time
                            else:
                                pass
                        else:
                            pass



                if self.is_combat == 1:
                    if self.known_enemy_units.not_flying.exists:
                        if self.known_enemy_units.not_flying.filter(lambda u: u.distance_to(unit) < 13).amount > 2:
                            actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                        else:
                            if unit.distance_to(tank_target_position) < 0.1:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                                else:
                                    actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        actions.append(unit.move(tank_target_position))
                                else:
                                    actions.append(unit.move(tank_target_position))
                    else:
                        if self.known_enemy_units.not_flying.filter(lambda u: u.distance_to(unit) < 13).amount > 2:
                            actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                        else:
                            if unit.distance_to(tank_target_position) < 0.1:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                                else:
                                    actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 10:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                                    else:
                                        actions.append(unit.move(tank_target_position))
                                else:
                                    actions.append(unit.move(tank_target_position))

                elif self.is_combat == 0:
                    if unit.distance_to(tank_target_position) < 0.1:
                        if self.enemy_nuke_alert == 1:
                            if unit.distance_to(self.enemy_nuke_position) < 10:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                            else:
                                actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                        else:
                            actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                    else:
                        if self.enemy_nuke_alert == 1:
                            if unit.distance_to(self.enemy_nuke_position) < 10:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                            else:
                                actions.append(unit.move(tank_target_position))
                        else:
                            actions.append(unit.move(tank_target_position))
                else:
                    if unit.distance_to(enemy_cc) < 13:
                        actions.append(unit(AbilityId.SIEGEMODE_SIEGEMODE))
                    else:
                        actions.append(unit.attack(enemy_cc))

            elif unit.type_id is UnitTypeId.SIEGETANKSIEGED:

                tank_num = self.tank_pos_num[unit.tag]
                tank_target_pos_x, tank_target_pos_y = self.defense_position(tank_num,UnitTypeId.SIEGETANK)
                if self.tank_position[(unit.tag, 'x')] == tank_target_pos_x and self.tank_position[(unit.tag, 'y')] == tank_target_pos_y:
                    tank_target_position = Point2(Point2((self.tank_position.get((unit.tag, 'x'), 0),self.tank_position.get((unit.tag, 'y'), 0))))
                else:
                    self.tank_position[(unit.tag, 'x')] = tank_target_pos_x
                    self.tank_position[(unit.tag, 'y')] = tank_target_pos_y
                    tank_target_position = Point2(Point2((self.tank_position.get((unit.tag, 'x'), 0),self.tank_position.get((unit.tag, 'y'), 0))))

                if self.is_combat == 0:
                    t_x = self.tank_position.get((unit.tag, 'x'), 0)
                    t_y = self.tank_position.get((unit.tag, 'y'), 0)
                    if self.enemy_nuke_alert == 1:
                        if unit.distance_to(self.enemy_nuke_position) < 10:
                            actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                        else:
                            if unit.distance_to(Point2((t_x, t_y))) > 1:
                                actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                            else:
                                pass
                    else:
                        if unit.distance_to(Point2((t_x, t_y))) > 1:
                            actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                        else:
                            pass
                elif self.is_combat == 1:
                    t_x = self.tank_position.get((unit.tag, 'x'), 0)
                    t_y = self.tank_position.get((unit.tag, 'y'), 0)
                    if self.known_enemy_units.not_flying.exists:
                        if self.known_enemy_units.not_flying.filter(lambda u: u.distance_to(unit) < 13).amount < 1 and self.time - self.combat_start_time > 2:
                            if self.enemy_nuke_alert == 1:
                                if unit.distance_to(self.enemy_nuke_position) < 10:
                                    actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                                else:
                                    if unit.distance_to(Point2((t_x, t_y))) > 1:
                                        actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                                    else:
                                        pass
                            else:
                                if unit.distance_to(Point2((t_x, t_y))) > 1:
                                    actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                                else:
                                    pass
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.MARAUDER]).exists:
                                target = self.known_enemy_units.of_type([UnitTypeId.MARAUDER]).closest_to(unit)
                                if target.distance_to(unit) < 13 and target.distance_to(unit) > 3:
                                    #actions.append(unit.attack(target)) #불곰상대
                                    pass
                                else:
                                    pass
                            else:
                                pass
                    else:
                        if self.enemy_nuke_alert == 1:
                            if unit.distance_to(self.enemy_nuke_position) < 10:
                                actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                            else:
                                if unit.distance_to(Point2((t_x, t_y))) > 1:
                                    actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                                else:
                                    pass
                        else:
                            if unit.distance_to(Point2((t_x, t_y))) > 1:
                                actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                            else:
                                pass
                else:
                    if unit.distance_to(enemy_cc) > 13:
                        actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                    else:
                        pass

            elif unit.type_id is UnitTypeId.BATTLECRUISER:
                pass

            elif unit.type_id is UnitTypeId.MEDIVAC:
                pass

            elif unit.type_id is UnitTypeId.VIKINGASSAULT:
                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).amount > 0:
                    actions.append(unit(AbilityId.MORPH_VIKINGFIGHTERMODE))
                else:
                    if self.is_combat == 0:
                        actions.append(unit(AbilityId.MORPH_VIKINGFIGHTERMODE))
                    elif self.is_combat == 1:
                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BANSHEE]).amount > 1:
                            actions.append(unit(AbilityId.MORPH_VIKINGFIGHTERMODE))
                        else:
                            actions.append(unit.attack(enemy_cc))
                    else:
                        actions.append(unit.attack(enemy_cc))

            elif unit.type_id is UnitTypeId.VIKINGFIGHTER:
                viking_list = list(self.viking_pos_num.values())
                viking_list.sort()
                viking_num = 0
                for i in range(len(viking_list)):
                    if i != viking_list[i] - 1:
                        viking_num = i
                        break
                    elif i == viking_list[i] - 1 and i == len(viking_list) - 1:
                        viking_num = i + 1
                    else:
                        continue

                viking_num = viking_num + 1

                if self.viking_pos_num.get(unit.tag, -2) == -2:
                    self.viking_pos_num[unit.tag] = viking_num
                    viking_target_pos_x, viking_target_pos_y = self.defense_position(viking_num, UnitTypeId.VIKINGFIGHTER)
                    self.viking_position[(unit.tag, 'x')] = viking_target_pos_x
                    self.viking_position[(unit.tag, 'y')] = viking_target_pos_y
                    viking_target_position = Point2(Point2((viking_target_pos_x, viking_target_pos_y)))
                    self.viking_position[(unit.tag, 't')] = self.time
                else:
                    viking_num = self.viking_pos_num[unit.tag]
                    viking_target_pos_x, viking_target_pos_y = self.defense_position(viking_num,
                                                                                UnitTypeId.VIKINGFIGHTER)
                    if self.viking_position[(unit.tag, 'x')] == viking_target_pos_x and self.viking_position[(unit.tag, 'y')] == viking_target_pos_y:
                        viking_target_position = Point2(Point2(
                            (self.viking_position.get((unit.tag, 'x'), 0),
                            self.viking_position.get((unit.tag, 'y'), 0))))
                    else:
                        self.viking_position[(unit.tag, 'x')] = viking_target_pos_x
                        self.viking_position[(unit.tag, 'y')] = viking_target_pos_y
                        viking_target_position = Point2(Point2(
                            (self.viking_position.get((unit.tag, 'x'), 0),
                            self.viking_position.get((unit.tag, 'y'), 0))))

                if self.enemy_tp == 0:
                    if ((viking_num != 1) or ((viking_num == 1) and (self.banshee_harass_switch == 0)) or (self.game_time < 100)) and self.is_combat != 2:
                        if self.is_combat == 0 or self.is_combat == 1:
                            if (self.time - self.combat_start_time > 1.5) and self.is_combat == 1:
                                if self.known_enemy_units.not_structure.flying.exists or self.enemy_counter[UnitTypeId.VIKINGFIGHTER] > 0:
                                    pass
                                else:
                                    actions.append(unit(AbilityId.MORPH_VIKINGASSAULTMODE))
                            else:
                                pass
                            if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                closest_hazard = self.known_enemy_units.of_type([UnitTypeId.MARINE]).closest_to(
                                    unit)
                                if unit.distance_to(closest_hazard) < 7.3:
                                    actions.append(unit.move(closest_hazard.position.towards(unit, 10)))
                                    # Change Combat State
                                else:
                                    if self.known_enemy_units.of_type(
                                            [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.RAVEN,
                                            UnitTypeId.BANSHEE]).exists:
                                        closest_target = self.known_enemy_units.of_type(
                                            [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.RAVEN,
                                            UnitTypeId.BANSHEE]).closest_to(unit)
                                        if self.game_time < 120:
                                            if self.units(UnitTypeId.VIKINGFIGHTER).amount < self.enemy_counter[UnitTypeId.VIKINGFIGHTER]:
                                                dead_line = 10
                                            else:
                                                dead_line = 8
                                        else:
                                            dead_line = 6

                                        if self.side == 1:
                                            if closest_target.position.x < self.defense_line - dead_line:
                                                viking_attack = 1
                                            else:
                                                viking_attack = 0
                                        else:
                                            if closest_target.position.x > self.defense_line + dead_line:
                                                viking_attack = 1
                                            else:
                                                viking_attack = 0

                                        if viking_attack == 1:
                                            if unit.weapon_cooldown > 10:
                                                actions.append(unit.move(closest_target.position.towards(unit, 12)))
                                            else:
                                                actions.append(unit.attack(closest_target.position.towards(unit, 2)))
                                        else:
                                            if unit.distance_to(closest_target) < 12:
                                                actions.append(unit.move(closest_target.position.towards(unit,14)))
                                            else:
                                                if self.enemy_nuke_alert == 1:
                                                    if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                        actions.append(
                                                            unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(viking_target_position))

                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(viking_target_position))
                                    else:
                                        if self.enemy_nuke_alert == 1:
                                            if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                actions.append(
                                                    unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(viking_target_position))

                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(viking_target_position))
                            else:
                                if self.known_enemy_units.of_type(
                                        [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.RAVEN,
                                        UnitTypeId.BANSHEE]).exists:
                                    closest_target = self.known_enemy_units.of_type(
                                        [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER, UnitTypeId.RAVEN,
                                        UnitTypeId.BANSHEE]).closest_to(unit)
                                    if self.game_time < 120:
                                        if self.units(UnitTypeId.VIKINGFIGHTER).amount < self.enemy_counter[
                                            UnitTypeId.VIKINGFIGHTER]:
                                            dead_line = 10
                                        else:
                                            dead_line = 8
                                    else:
                                        dead_line = 6
                                    if self.side == 1:
                                        if closest_target.position.x < self.defense_line - dead_line:
                                            viking_attack = 1
                                        else:
                                            viking_attack = 0
                                    else:
                                        if closest_target.position.x > self.defense_line + dead_line:
                                            viking_attack = 1
                                        else:
                                            viking_attack = 0

                                    if viking_attack == 1:
                                        if unit.weapon_cooldown > 10:
                                            actions.append(unit.move(closest_target.position.towards(unit, 12)))
                                        else:
                                            actions.append(unit.attack(closest_target.position.towards(unit, 2)))
                                    else:
                                        if unit.distance_to(closest_target) < 12:
                                            actions.append(unit.move(closest_target.position.towards(unit, 14)))
                                        else:
                                            if self.enemy_nuke_alert == 1:
                                                if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                                    actions.append(
                                                        unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(viking_target_position))

                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(unit.move(viking_target_position))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if unit.distance_to(self.enemy_nuke_position) < 11 and self.time - self.enemy_nuke_alert_time > 8:
                                            actions.append(
                                                unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(viking_target_position))

                                    else:
                                        if self.time - self.move_start_time > 3.5:
                                            actions.append(unit.move(viking_target_position))

                    elif self.is_combat == 2:
                        if self.time - self.end_game_time > self.move_adjust[UnitTypeId.VIKINGFIGHTER]:
                            if self.time - self.end_game_time > self.move_adjust[UnitTypeId.VIKINGFIGHTER] + 1.5:
                                if not self.known_enemy_units.not_structure.flying.exists:
                                    actions.append(unit(AbilityId.MORPH_VIKINGASSAULTMODE))
                                else:
                                    actions.append(unit.attack(enemy_cc))
                            else:
                                actions.append(unit.attack(enemy_cc))
                        else:
                            if self.units(UnitTypeId.SIEGETANK).exists:
                                actions.append(unit.attack(Point2(
                                    (self.units(UnitTypeId.SIEGETANK).closest_to(unit).position.x, unit.position.y))))
                            else:
                                if self.side == 1:
                                    if 40 - unit.position.x > 0:
                                        actions.append(unit.attack(Point2((40, 31.5))))
                                    else:
                                        pass
                                else:
                                    if unit.position.x - (88) > 0:
                                        actions.append(unit.move(Point2((88, 31.5))))
                                    else:
                                        pass

                    else:# Harass With Banshee
                        banshee_h_point_x = self.bv_harass_bond[0]
                        banshee_h_point_y = self.bv_harass_bond[1]

                        viking_h_point = Point2((banshee_h_point_x, banshee_h_point_y)).towards(ally_cc, 4)
                        # actions.append(unit.move(viking_h_point))

                        if self.known_enemy_units.of_type(
                                [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER]).exists:
                            closest_hazard = self.known_enemy_units.of_type(
                                [UnitTypeId.VIKINGFIGHTER, UnitTypeId.BATTLECRUISER]).closest_to(unit)
                            if unit.distance_to(closest_hazard) < 14:
                                actions.append(unit.move(closest_hazard.position.towards(unit, 17)))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                    closest_hazard_m = self.known_enemy_units.of_type([UnitTypeId.MARINE]).closest_to(
                                        unit)
                                    if unit.distance_to(closest_hazard_m) < 7.5:
                                        actions.append(unit.move(closest_hazard_m.position.towards(unit, 15)))
                                    else:
                                        if self.known_enemy_units.of_type(
                                                [UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.exists:
                                            closest_target = self.known_enemy_units.of_type(
                                                [UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.closest_to(
                                                unit)
                                            if unit.weapon_cooldown > 2:
                                                actions.append(unit.move(viking_h_point))
                                            else:
                                                actions.append(unit.attack(closest_target.position.towards(unit, 4)))
                                        else:
                                            actions.append(unit.move(viking_h_point))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.exists:
                                        closest_target = self.known_enemy_units.of_type(
                                            [UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.closest_to(unit)
                                        if unit.weapon_cooldown > 2:
                                            actions.append(unit.move(viking_h_point))
                                        else:
                                            actions.append(unit.attack(closest_target.position.towards(unit, 4)))
                                    else:
                                        actions.append(unit.move(viking_h_point))
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.MARINE]).exists:
                                closest_hazard_m = self.known_enemy_units.of_type([UnitTypeId.MARINE]).closest_to(unit)
                                if unit.distance_to(closest_hazard_m) < 7.5:
                                    actions.append(unit.move(closest_hazard_m.position.towards(unit, 15)))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.exists:
                                        closest_target = self.known_enemy_units.of_type(
                                            [UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.closest_to(
                                            unit)
                                        if unit.weapon_cooldown > 2:
                                            actions.append(unit.move(viking_h_point))
                                        else:
                                            actions.append(unit.attack(closest_target.position.towards(unit, 8)))
                                    else:
                                        actions.append(unit.move(viking_h_point))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.exists:
                                    closest_target = self.known_enemy_units.of_type(
                                        [UnitTypeId.RAVEN, UnitTypeId.BANSHEE]).visible.closest_to(unit)
                                    if unit.weapon_cooldown > 2:
                                        actions.append(unit.move(viking_h_point))
                                    else:
                                        actions.append(unit.attack(closest_target.position.towards(unit, 8)))
                                else:
                                    actions.append(unit.move(viking_h_point))
                else: # self.enemy_tp == 1
                    if self.enemy_nuke_alert == 1 and self.time - self.enemy_nuke_alert_time > 10:
                        if unit.distance_to(self.enemy_nuke_position) < 10:
                            need_avoid = 1
                        else:
                            need_avoid = 0
                    else:
                        need_avoid = 0

                    if self.time - self.enemy_tp_time > 1:
                        if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                            closest_target = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(unit)
                            if need_avoid == 1:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                            else:
                                actions.append(unit.attack(closest_target))
                        else:
                            if need_avoid == 1:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                            else:
                                pass
                    else:
                        if need_avoid == 1:
                            actions.append(unit.move(self.enemy_nuke_position.towards(unit, 13)))
                        else:
                            actions.append(unit.move(self.enemy_tp_position))

            elif unit.type_id is UnitTypeId.GHOST:
                if self.is_combat != 2:
                    emp_range = 10
                    if self.enemy_nuke_alert == 1:
                        if unit.distance_to(self.enemy_nuke_position) < 10:
                            avoid_nuke = 1
                        else:
                            avoid_nuke = 0
                    else:
                        avoid_nuke = 0

                    if self.tacnuke != 2:
                        if unit.is_cloaked == True:
                            if self.time - self.my_nuke_launch_time > 15:
                                actions.append(unit(AbilityId.BEHAVIOR_CLOAKOFF_GHOST))
                            else:
                                pass
                        else:
                            pass
                        if avoid_nuke == 1:
                            actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                        else:
                            if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                closest_hazard = self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).closest_to(unit)
                                if unit.distance_to(closest_hazard) < 13:
                                    actions.append(unit.move(closest_hazard.position.towards(unit, 15)))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.BANSHEE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.BANSHEE]).closest_to(unit)
                                        if unit.distance_to(closest_hazard) < 8:
                                            actions.append(unit.move(closest_hazard.position.towards(unit, 11)))
                                        else:
                                            if unit.energy > 75:
                                                if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                    for emp_target in self.known_enemy_units.of_type([UnitTypeId.RAVEN]):
                                                        if unit.distance_to(emp_target) < 9:
                                                            emp_bool = 1
                                                        else:
                                                            emp_bool = 0
                                                        if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                                emp_target.tag, -2) == -2:
                                                            if self.time - self.combat_controller.get(unit.tag, 0) > 0.1:
                                                                # emp!
                                                                actions.append(
                                                                    unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                                self.combat_controller[unit.tag] = self.time
                                                                self.emp_target_dict[emp_target.tag] = 1
                                                            else:
                                                                pass
                                                        else:
                                                            if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                    emp_target.tag, -2) != -2:
                                                                del self.emp_target_dict[emp_target.tag]
                                                            else:
                                                                pass
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                    else:
                                        if unit.energy > 75:
                                            if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                for emp_target in self.known_enemy_units.of_type([UnitTypeId.RAVEN]):
                                                    if unit.distance_to(emp_target) < 9:
                                                        emp_bool = 1
                                                    else:
                                                        emp_bool = 0
                                                    if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                            emp_target.tag, -2) == -2:
                                                        if self.time - self.combat_controller.get(unit.tag, 0) > 0.1:
                                                            # emp!
                                                            actions.append(
                                                                unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                            self.combat_controller[unit.tag] = self.time
                                                            self.emp_target_dict[emp_target.tag] = 1
                                                        else:
                                                            pass
                                                    else:
                                                        if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                emp_target.tag, -2) != -2:
                                                            del self.emp_target_dict[emp_target.tag]
                                                        else:
                                                            pass
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(Point2((self.defense_line - self.side * 22, 32))))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.BANSHEE]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.MARINE, UnitTypeId.BANSHEE]).closest_to(unit)
                                    if unit.distance_to(closest_hazard) < 8:
                                        actions.append(unit.move(closest_hazard.position.towards(unit, 11)))
                                    else:
                                        if unit.energy > 75:
                                            if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                for emp_target in self.known_enemy_units.of_type([UnitTypeId.RAVEN]):
                                                    if unit.distance_to(emp_target) < 9:
                                                        emp_bool = 1
                                                    else:
                                                        emp_bool = 0
                                                    if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                            emp_target.tag, -2) == -2:
                                                        if self.time - self.combat_controller.get(unit.tag, 0) > 0.1:
                                                            # emp!
                                                            actions.append(
                                                                unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                            self.combat_controller[unit.tag] = self.time
                                                            self.emp_target_dict[emp_target.tag] = 1
                                                        else:
                                                            pass
                                                    else:
                                                        if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                emp_target.tag, -2) != -2:
                                                            del self.emp_target_dict[emp_target.tag]
                                                        else:
                                                            pass
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                else:
                                    if unit.energy > 75:
                                        if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                            for emp_target in self.known_enemy_units.of_type([UnitTypeId.RAVEN]):
                                                if unit.distance_to(emp_target) < 9:
                                                    emp_bool = 1
                                                else:
                                                    emp_bool = 0
                                                if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                        emp_target.tag, -2) == -2:
                                                    if self.time - self.combat_controller.get(unit.tag, 0) > 0.1:
                                                        # emp!
                                                        actions.append(
                                                            unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                        self.combat_controller[unit.tag] = self.time
                                                        self.emp_target_dict[emp_target.tag] = 1
                                                    else:
                                                        pass
                                                else:
                                                    if emp_target.energy < 5 and self.emp_target_dict.get(emp_target.tag,
                                                                                                          -2) != -2:
                                                        del self.emp_target_dict[emp_target.tag]
                                                    else:
                                                        pass
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                    else:
                                        if self.time - self.move_start_time > 3.5:
                                            actions.append(unit.move(Point2((self.defense_line - self.side * 22, 32))))
                    elif self.tacnuke == 2:  # NUKE !
                        if self.enemy_tank_line() != 999:
                            ghost_position = Point2((self.defense_line - self.side * 17, 32))
                        else:
                            ghost_position = Point2((self.defense_line - self.side * 16, 32))
                        # 조건 한번 더 추가하기

                        if self.side == 1:
                            if self.defense_line > 92.8:
                                absol_nuke = 1
                            else:
                                absol_nuke = 0
                        else:
                            if self.defense_line < 34.2:
                                absol_nuke = 1
                            else:
                                absol_nuke = 0
                        nuke_target_count = 0

                        if absol_nuke == 0:
                            if self.enemy_tank_line() != 999:
                                if self.side == 1:
                                    nuke_point = Point2((self.defense_line - 8, 31.5))
                                else:
                                    nuke_point = Point2((self.defense_line + 8, 31.5))
                            else:
                                if self.side == 1:
                                    nuke_point = Point2((self.defense_line - 5, 31.5))
                                else:
                                    nuke_point = Point2((self.defense_line + 5, 31.5))

                            if len(list(self.enemy_unit_dict.keys())) > 0:  # 전체 유닛으로
                                for enemy_ind_tag in list(self.enemy_unit_dict.keys()):
                                    if Point2((self.enemy_unit_dict[enemy_ind_tag][1],
                                               self.enemy_unit_dict[enemy_ind_tag][2])).distance_to(nuke_point) < 7.8:
                                        nuke_target_count += 1
                                    else:
                                        pass
                            else:
                                pass
                        predict_nuke_position = Point2((ghost_position.x + self.side * 12, ghost_position.y))
                        if absol_nuke == 0 and predict_nuke_position.distance_to(self.before_nuke_position) < 1 and self.nuke_kill_min == 0:
                            dont_nuke = 1
                        else:
                            dont_nuke = 0
                        if (absol_nuke == 1 or nuke_target_count > 5) and dont_nuke == 0 :
                            if unit.energy > 40:
                                if unit.is_cloaked == False:
                                    actions.append(unit(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                                else:
                                    pass
                            else:
                                pass

                            if unit.distance_to(ghost_position) < 1.5:
                                print("NUKE")
                                nuke_position = Point2((unit.position.x + self.side * 12, unit.position.y))
                                actions.append(unit(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target=nuke_position))
                                self.before_nuke_position = nuke_position
                                if self.time - self.my_nuke_launch_time > 15:
                                    self.my_nuke_launch_time = self.time
                                    self.enemy_nuke_alert_time = self.time
                                else:
                                    pass
                            else:
                                print("MOVE")
                                actions.append(unit.move(ghost_position))
                        else:
                            if avoid_nuke == 1:
                                actions.append(unit.move(self.enemy_nuke_position.towards(unit, 11)))
                            else:
                                if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER]).exists:
                                    closest_hazard = self.known_enemy_units.of_type(
                                        [UnitTypeId.BATTLECRUISER]).closest_to(unit)
                                    if unit.distance_to(closest_hazard) < 13:
                                        actions.append(unit.move(closest_hazard.position.towards(unit, 15)))
                                    else:
                                        if self.known_enemy_units.of_type(
                                                [UnitTypeId.MARINE, UnitTypeId.BANSHEE]).exists:
                                            closest_hazard = self.known_enemy_units.of_type(
                                                [UnitTypeId.MARINE, UnitTypeId.BANSHEE]).closest_to(unit)
                                            if unit.distance_to(closest_hazard) < 8:
                                                actions.append(unit.move(closest_hazard.position.towards(unit, 11)))
                                            else:
                                                if unit.energy > 75:
                                                    if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                        for emp_target in self.known_enemy_units.of_type(
                                                                [UnitTypeId.RAVEN]):
                                                            if unit.distance_to(emp_target) < 9:
                                                                emp_bool = 1
                                                            else:
                                                                emp_bool = 0
                                                            if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                                    emp_target.tag, -2) == -2:
                                                                if self.time - self.combat_controller.get(unit.tag,
                                                                                                          0) > 0.1:
                                                                    # emp!
                                                                    actions.append(
                                                                        unit(AbilityId.EMP_EMP,
                                                                             target=emp_target.position))
                                                                    self.combat_controller[unit.tag] = self.time
                                                                    self.emp_target_dict[emp_target.tag] = 1
                                                                else:
                                                                    pass
                                                            else:
                                                                if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                        emp_target.tag, -2) != -2:
                                                                    del self.emp_target_dict[emp_target.tag]
                                                                else:
                                                                    pass
                                                    else:
                                                        if self.time - self.move_start_time > 3.5:
                                                            actions.append(unit.move(
                                                                Point2((self.defense_line - self.side * 22, 32))))
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(
                                                            unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                        else:
                                            if unit.energy > 75:
                                                if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                    for emp_target in self.known_enemy_units.of_type(
                                                            [UnitTypeId.RAVEN]):
                                                        if unit.distance_to(emp_target) < 9:
                                                            emp_bool = 1
                                                        else:
                                                            emp_bool = 0
                                                        if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                                emp_target.tag, -2) == -2:
                                                            if self.time - self.combat_controller.get(unit.tag,
                                                                                                      0) > 0.1:
                                                                # emp!
                                                                actions.append(
                                                                    unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                                self.combat_controller[unit.tag] = self.time
                                                                self.emp_target_dict[emp_target.tag] = 1
                                                            else:
                                                                pass
                                                        else:
                                                            if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                    emp_target.tag, -2) != -2:
                                                                del self.emp_target_dict[emp_target.tag]
                                                            else:
                                                                pass
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(
                                                            unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                else:
                                    if self.known_enemy_units.of_type([UnitTypeId.MARINE, UnitTypeId.BANSHEE]).exists:
                                        closest_hazard = self.known_enemy_units.of_type(
                                            [UnitTypeId.MARINE, UnitTypeId.BANSHEE]).closest_to(unit)
                                        if unit.distance_to(closest_hazard) < 8:
                                            actions.append(unit.move(closest_hazard.position.towards(unit, 11)))
                                        else:
                                            if unit.energy > 75:
                                                if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                    for emp_target in self.known_enemy_units.of_type(
                                                            [UnitTypeId.RAVEN]):
                                                        if unit.distance_to(emp_target) < 9:
                                                            emp_bool = 1
                                                        else:
                                                            emp_bool = 0
                                                        if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                                emp_target.tag, -2) == -2:
                                                            if self.time - self.combat_controller.get(unit.tag,
                                                                                                      0) > 0.1:
                                                                # emp!
                                                                actions.append(
                                                                    unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                                self.combat_controller[unit.tag] = self.time
                                                                self.emp_target_dict[emp_target.tag] = 1
                                                            else:
                                                                pass
                                                        else:
                                                            if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                    emp_target.tag, -2) != -2:
                                                                del self.emp_target_dict[emp_target.tag]
                                                            else:
                                                                pass
                                                else:
                                                    if self.time - self.move_start_time > 3.5:
                                                        actions.append(
                                                            unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                    else:
                                        if unit.energy > 75:
                                            if self.known_enemy_units.of_type([UnitTypeId.RAVEN]).exists:
                                                for emp_target in self.known_enemy_units.of_type([UnitTypeId.RAVEN]):
                                                    if unit.distance_to(emp_target) < 9:
                                                        emp_bool = 1
                                                    else:
                                                        emp_bool = 0
                                                    if emp_target.energy > 49 and emp_bool == 1 and self.emp_target_dict.get(
                                                            emp_target.tag, -2) == -2:
                                                        if self.time - self.combat_controller.get(unit.tag, 0) > 0.1:
                                                            # emp!
                                                            actions.append(
                                                                unit(AbilityId.EMP_EMP, target=emp_target.position))
                                                            self.combat_controller[unit.tag] = self.time
                                                            self.emp_target_dict[emp_target.tag] = 1
                                                        else:
                                                            pass
                                                    else:
                                                        if emp_target.energy < 5 and self.emp_target_dict.get(
                                                                emp_target.tag,
                                                                -2) != -2:
                                                            del self.emp_target_dict[emp_target.tag]
                                                        else:
                                                            pass
                                            else:
                                                if self.time - self.move_start_time > 3.5:
                                                    actions.append(
                                                        unit.move(Point2((self.defense_line - self.side * 22, 32))))
                                        else:
                                            if self.time - self.move_start_time > 3.5:
                                                actions.append(
                                                    unit.move(Point2((self.defense_line - self.side * 22, 32))))
                else: # 어택땅!
                    if self.time - self.end_game_time > self.move_adjust[UnitTypeId.MARINE]:
                        actions.append(unit.attack(enemy_cc))
                    else:
                        if self.units(UnitTypeId.SIEGETANK).exists:
                            actions.append(unit.attack(Point2(
                                (self.units(UnitTypeId.SIEGETANK).closest_to(unit).position.x, unit.position.y))))
                        else:
                            actions.append(unit.attack(unit.position))

            elif unit.type_id is UnitTypeId.THOR:
                actions.append(unit(AbilityId.MORPH_THORHIGHIMPACTMODE))

            elif unit.type_id is UnitTypeId.THORAP:
                thor_list = list(self.thor_pos_num.values())
                thor_list.sort()
                thor_num = 0
                for i in range(len(thor_list)):
                    if i != thor_list[i] - 1:
                        thor_num = i
                        break
                    elif i == thor_list[i] - 1 and i == len(thor_list) - 1:
                        thor_num = i + 1
                    else:
                        continue

                thor_num = thor_num + 1
                if self.thor_pos_num.get(unit.tag, -2) == -2:
                    self.thor_pos_num[unit.tag] = thor_num
                    thor_target_pos_x, thor_target_pos_y = self.defense_position(thor_num, UnitTypeId.THOR)
                    self.thor_position[(unit.tag, 'x')] = thor_target_pos_x
                    self.thor_position[(unit.tag, 'y')] = thor_target_pos_y
                    thor_target_position = Point2(Point2((thor_target_pos_x, thor_target_pos_y)))
                    self.thor_position[(unit.tag, 't')] = self.time
                else:
                    thor_num = self.thor_pos_num[unit.tag]
                    thor_target_pos_x, thor_target_pos_y = self.defense_position(thor_num,
                                                                                 UnitTypeId.THOR)
                    if self.thor_position[(unit.tag, 'x')] == thor_target_pos_x:
                        thor_target_position = Point2(Point2(
                            (self.thor_position.get((unit.tag, 'x'), 0),
                             self.thor_position.get((unit.tag, 'y'), 0))))
                    else:
                        self.thor_position[(unit.tag, 'x')] = thor_target_pos_x
                        self.thor_position[(unit.tag, 'y')] = thor_target_pos_y
                        thor_target_position = Point2(Point2(
                            (self.thor_position.get((unit.tag, 'x'), 0),
                             self.thor_position.get((unit.tag, 'y'), 0))))
                if self.is_combat == 0 or self.is_combat == 1:
                    if self.known_enemy_units.of_type([UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BANSHEE]).visible.exists:
                        if self.known_enemy_units.of_type(
                                [UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BANSHEE]).visible.closest_to(
                                unit).distance_to(unit) < 11.5:
                            attack_target = self.known_enemy_units.of_type(
                                [UnitTypeId.BATTLECRUISER, UnitTypeId.VIKINGFIGHTER, UnitTypeId.BANSHEE]).visible.closest_to(
                                unit)
                            actions.append(unit.attack(attack_target))
                        else:
                            if self.known_enemy_units.not_structure.visible.exists:
                                attack_target = self.known_enemy_units.not_structure.visible.closest_to(unit)
                                if unit.distance_to(attack_target) < 8:
                                    actions.append(unit.attack(attack_target))
                                else:
                                    if self.enemy_nuke_alert == 1:
                                        if unit.distance_to(self.enemy_nuke_position) < 11:
                                            actions.append(unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                        else:
                                            if self.time - self.move_start_time > 0:
                                                actions.append(unit.attack(thor_target_position))
                                            else:
                                                pass
                                    else:
                                        if self.time - self.move_start_time > 0:
                                            actions.append(unit.attack(thor_target_position))
                                        else:
                                            pass
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                    else:
                                        if self.time - self.move_start_time > 0:
                                            actions.append(unit.attack(thor_target_position))
                                        else:
                                            pass
                                else:
                                    if self.time - self.move_start_time > 0:
                                        actions.append(unit.attack(thor_target_position))
                                    else:
                                        pass
                    else:
                        if self.known_enemy_units.not_structure.visible.exists:
                            attack_target = self.known_enemy_units.not_structure.visible.closest_to(unit)
                            if unit.distance_to(attack_target) < 8:
                                actions.append(unit.attack(attack_target))
                            else:
                                if self.enemy_nuke_alert == 1:
                                    if unit.distance_to(self.enemy_nuke_position) < 11:
                                        actions.append(unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                    else:
                                        if self.time - self.move_start_time > 0:
                                            actions.append(unit.attack(thor_target_position))
                                        else:
                                            pass
                                else:
                                    if self.time - self.move_start_time > 0:
                                        actions.append(unit.attack(thor_target_position))
                                    else:
                                        pass
                        else:
                            if self.enemy_nuke_alert == 1:
                                if unit.distance_to(self.enemy_nuke_position) < 11:
                                    actions.append(unit.move(self.enemy_nuke_position.towards(unit, 12)))
                                else:
                                    if self.time - self.move_start_time > 0:
                                        actions.append(unit.attack(thor_target_position))
                                    else:
                                        pass
                            else:
                                if self.time - self.move_start_time > 0:
                                    actions.append(unit.attack(thor_target_position))
                                else:
                                    pass
                else:
                    actions.append(unit.attack(enemy_cc))



        await self.do_actions(actions)


    def enemy_ground_line(self):
        enemy_x_min1 = 100
        enemy_x_min2 = 100
        enemy_x_min3 = 100
        enemy_x_max1 = 0
        enemy_x_max2 = 0
        enemy_x_max3 = 0
        # min1 < min2 < min3, max1 > max2 > max3

        if len(list(self.enemy_unit_dict.keys())) > 0: # 전체 유닛으로
            for enemy_ind_tag in list(self.enemy_unit_dict.keys()):
                if enemy_x_min1 > self.enemy_unit_dict[enemy_ind_tag][1]:
                    enemy_x_min3 = enemy_x_min2
                    enemy_x_min2 = enemy_x_max1
                    enemy_x_min1 = self.enemy_unit_dict[enemy_ind_tag][1]
                else:
                    if enemy_x_min2 > self.enemy_unit_dict[enemy_ind_tag][1]:
                        enemy_x_min3 = enemy_x_min2
                        enemy_x_min2 = self.enemy_unit_dict[enemy_ind_tag][1]
                    else:
                        if enemy_x_min3 > self.enemy_unit_dict[enemy_ind_tag][1]:
                            enemy_x_min3 = self.enemy_unit_dict[enemy_ind_tag][1]
                        else:
                            pass

                if enemy_x_max1 < self.enemy_unit_dict[enemy_ind_tag][1]:
                    enemy_x_max3 = enemy_x_max2
                    enemy_x_max2 = enemy_x_max1
                    enemy_x_max1 = self.enemy_unit_dict[enemy_ind_tag][1]
                else:
                    if enemy_x_max2 < self.enemy_unit_dict[enemy_ind_tag][1]:
                        enemy_x_max3 = enemy_x_min2
                        enemy_x_max2 = self.enemy_unit_dict[enemy_ind_tag][1]
                    else:
                        if enemy_x_max3 < self.enemy_unit_dict[enemy_ind_tag][1]:
                            enemy_x_max3 = self.enemy_unit_dict[enemy_ind_tag][1]
                        else:
                            pass

            if self.side == 1:
                if enemy_x_min3 != 100:
                    return enemy_x_min3
                else:
                    if enemy_x_min2 != 100:
                        return enemy_x_min2
                    else:
                        if enemy_x_min1 != 100:
                            return enemy_x_min1
                        else:
                            return 999
            else:
                if enemy_x_max3 != 0:
                    return enemy_x_max3
                else:
                    if enemy_x_max2 != 0:
                        return enemy_x_max2
                    else:
                        if enemy_x_max1 != 0:
                            return enemy_x_max1
                        else:
                            return 999
        else:
            return 999

    def enemy_tank_line(self):

        enemy_tank_x_min = 100
        enemy_tank_x_max = 0

        if (self.enemy_counter[UnitTypeId.SIEGETANKSIEGED] + self.enemy_counter[UnitTypeId.SIEGETANK]) > 0:
            for enemy_ind_tag in list(self.enemy_unit_dict.keys()):
                if self.enemy_unit_dict[enemy_ind_tag][0] == UnitTypeId.SIEGETANKSIEGED or \
                        self.enemy_unit_dict[enemy_ind_tag][0] == UnitTypeId.SIEGETANK:
                    if enemy_tank_x_min > self.enemy_unit_dict[enemy_ind_tag][1]:
                        enemy_tank_x_min = self.enemy_unit_dict[enemy_ind_tag][1]
                    else:
                        pass
                    if enemy_tank_x_max < self.enemy_unit_dict[enemy_ind_tag][1]:
                        enemy_tank_x_max = self.enemy_unit_dict[enemy_ind_tag][1]
                    else:
                        pass
                else:
                    pass

            if self.side == 1:
                return enemy_tank_x_min
            else:
                return enemy_tank_x_max
        else:
            return 999

    def defense_position(self, unit_num, unit_kind):
        if unit_kind == UnitTypeId.MARINE:
            defense_radius = 35

            a = 18

            if self.game_time < 120:
                a = a + 2
            else:
                pass

            if self.enemy_tank_line() != 999:
                if self.side == 1:
                    if self.enemy_tank_line() < self.defense_line + 1:
                        a = 11
                    else:
                        pass
                else:
                    if self.enemy_tank_line() > self.defense_line - 1:
                        a = 11
                    else:
                        pass
            else:
                pass



            b = 0

            if self.game_time < 170:
                a = 18
                if 18 < unit_num < 37:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 1.2
                    else:
                        a = a + 1.7
                elif 36 < unit_num < 55:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 2.4
                    else:
                        a = a + 3.4
                elif 54 < unit_num < 73:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 3.6
                    else:
                        a = a + 5.1
                elif 72 < unit_num:
                    a = a + 6.8

                if unit_num % 18 != 0:
                    unit_num = unit_num % 18
                else:
                    unit_num = 18

                min_dist = 1.1

                if unit_num > 9:
                    if unit_num % 2 == 1:
                        addi_angle_c = unit_num - 1
                    else:
                        addi_angle_c = unit_num
                    addi_angle_c = (addi_angle_c / 2) - 4
                else:
                    addi_angle_c = 0
            else:
                if 25 < unit_num < 51:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 1.2
                    else:
                        a = a + 1.7
                elif 50 < unit_num < 76:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 2.4
                    else:
                        a = a + 3.4
                elif 75 < unit_num < 101:
                    if (self.enemy_strategy == 1 and self.enemy_tank_line() == 999):
                        a = a + 3.6
                    else:
                        a = a + 5.1
                elif 100 < unit_num:
                    a = a + 6.8

                if unit_num % 25 != 0:
                    unit_num = unit_num % 25
                else:
                    unit_num = 25

                min_dist = 1.65

                if unit_num > 9:
                    if unit_num % 2 == 1:
                        addi_angle_c = unit_num - 1
                    else:
                        addi_angle_c = unit_num
                    addi_angle_c = (addi_angle_c / 2) - 4
                else:
                    addi_angle_c = 0

            min_angle = min_dist / defense_radius
            if self.enemy_strategy == 1 and self.enemy_tank_line() == 999:
                if self.game_time < 170:
                    min_dist = 1.2
                    min_angle = min_dist / defense_radius
                else:
                    min_dist = 1.5
                    min_angle = min_dist / defense_radius
            else:
                pass
            addi_angle = 0.001

            unit_ang = ((-1) ** (unit_num % 2)) * (unit_num // 2 * (min_angle + addi_angle * addi_angle_c))
            target_pos_x = self.defense_line - self.side * defense_radius * math.cos(unit_ang) + self.side * a
            target_pos_y = 31.5 + defense_radius * math.sin(unit_ang) + b * ((-1)**(unit_num))

            if self.enemy_nuke_alert == 1:
                if Point2((target_pos_x, target_pos_y)).distance_to(self.enemy_nuke_position) < 9:
                    if target_pos_y > self.enemy_nuke_position.y:
                        target_pos_y = self.enemy_nuke_position.y + math.sqrt(9.5*9.5 - (self.enemy_nuke_position.x - target_pos_x)**(2)) + (target_pos_y - self.enemy_nuke_position.y)
                        if target_pos_y > 62:
                            target_pos_y = self.enemy_nuke_position.y - math.sqrt(9.5*9.5 - (self.enemy_nuke_position.x - target_pos_x)**(2))
                        else:
                            pass
                    else:
                        target_pos_y = self.enemy_nuke_position.y - math.sqrt(9.5*9.5 - (self.enemy_nuke_position.x - target_pos_x)**(2)) - (self.enemy_nuke_position.y - target_pos_y)
                        if target_pos_y < 1:
                            target_pos_y = self.enemy_nuke_position.y + math.sqrt(9.5*9.5 - (self.enemy_nuke_position.x - target_pos_x)**(2))
                        else:
                            pass
                else:
                    pass
            else:
                pass

            return target_pos_x, target_pos_y

        elif unit_kind == UnitTypeId.RAVEN:
            return 1

        elif unit_kind == UnitTypeId.THOR:
            defense_radius = 40
            min_dist = 2
            min_angle = min_dist / defense_radius

            a = 21
            b = 0

            unit_ang = ((-1) ** (unit_num)) * (min_angle)
            target_pos_x = self.defense_line - self.side * defense_radius * math.cos(unit_ang) + self.side * a
            target_pos_y = 31.5 + defense_radius * math.sin(unit_ang) + b
            if self.enemy_nuke_alert == 1:
                if Point2((target_pos_x, target_pos_y)).distance_to(self.enemy_nuke_position) < 10:
                    if target_pos_y > self.enemy_nuke_position.y:
                        target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) + (target_pos_y - self.enemy_nuke_position.y)
                        if target_pos_y > 62:
                            target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                    else:
                        target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) - (self.enemy_nuke_position.y - target_pos_y)
                        if target_pos_y < 1:
                            target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                else:
                    pass
            else:
                pass
            return target_pos_x, target_pos_y

        elif unit_kind == UnitTypeId.VIKINGFIGHTER:
            defense_radius = 80
            min_dist = 7
            min_angle = min_dist / defense_radius

            a = 61
            b = 0

            if self.game_time < 120:
                a = a - 2

            if unit_num == 1:
                target_pos_x = self.defense_line - self.side * defense_radius + self.side * a
                target_pos_y = 31.5 + b
            else:
                unit_ang = ((-1) ** ((unit_num-2)//5)) * (((unit_num-2)//5+1)//2) * min_angle
                target_pos_x = self.defense_line - self.side * defense_radius * math.cos(unit_ang) + self.side * a
                target_pos_y = 31.5 + defense_radius * math.sin(unit_ang) + b

            if self.enemy_nuke_alert == 1:
                if Point2((target_pos_x, target_pos_y)).distance_to(self.enemy_nuke_position) < 9:
                    if target_pos_y > self.enemy_nuke_position.y:
                        target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                            9.5 * 9.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) + (target_pos_y - self.enemy_nuke_position.y)
                        if target_pos_y > 62:
                            target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                                9.5 * 9.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                    else:
                        target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                            9.5 * 9.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) - (self.enemy_nuke_position.y - target_pos_y)
                        if target_pos_y < 1:
                            target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                                9.5 * 9.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                else:
                    pass
            else:
                pass
            if unit_num == 2:
                if self.game_time > 120:
                    target_pos_x = target_pos_x + self.side * 2.5
                else:
                    pass
            if self.units(UnitTypeId.VIKINGFIGHTER).amount < self.enemy_counter[UnitTypeId.VIKINGFIGHTER]:
                target_pos_x = target_pos_x - self.side * 2.5
            else:
                pass
            return target_pos_x, target_pos_y

        elif unit_kind == UnitTypeId.SIEGETANK:
            defense_radius = 40
            min_dist = 4
            min_angle = min_dist / defense_radius

            a = 20
            b = 0

            if 19 < unit_num < 39:
                a = a - 3
            elif 38 < unit_num < 58:
                a = a - 6

            if unit_num % 19 != 0:
                unit_num = unit_num % 19
            else:
                unit_num = 19

            unit_ang = ((-1) ** (unit_num % 2)) * (unit_num // 2 * min_angle)
            target_pos_x = self.defense_line - self.side * defense_radius * math.cos(unit_ang) + self.side * a
            target_pos_y = 31.5 + defense_radius * math.sin(unit_ang) + b
            if self.enemy_nuke_alert == 1:
                if Point2((target_pos_x, target_pos_y)).distance_to(self.enemy_nuke_position) < 10:
                    if target_pos_y > self.enemy_nuke_position.y:
                        target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) + (target_pos_y - self.enemy_nuke_position.y)
                        if target_pos_y > 62:
                            target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                    else:
                        target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) - (self.enemy_nuke_position.y - target_pos_y)
                        if target_pos_y < 1:
                            target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                else:
                    pass
            else:
                pass
            return target_pos_x, target_pos_y

        elif unit_kind == UnitTypeId.BATTLECRUISER:
            return 1
        elif unit_kind == UnitTypeId.HELLION:
            defense_radius = 40
            min_dist = 2
            min_angle = min_dist / defense_radius
            a = 27

            if self.enemy_tank_line() != 999:
                if self.side == 1:
                    if self.enemy_tank_line() < self.defense_line - 3:
                        a = 16
                    else:
                        pass
                else:
                    if self.enemy_tank_line() > self.defense_line + 3:
                        a = 16
                    else:
                        pass
            else:
                pass

            b = 0

            if self.units.of_type([UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED]).amount > 2 and self.units(UnitTypeId.MARINE).amount > 20:
                b = 17
                a = 24
                if 10 < unit_num < 21:
                    a = a - 2
                    # b = 0.5
                elif 20 < unit_num < 31:
                    a = a - 4
                elif 30 < unit_num < 41:
                    a = a - 6
                    # b = 0.5
                elif 40 < unit_num:
                    a = a - 8

                if unit_num % 10 != 0:
                    unit_num = unit_num % 10
                else:
                    unit_num = 10
            else:
                a = 28
                if 20 < unit_num < 41:
                    a = a + 2
                    # b = 0.5
                elif 40 < unit_num < 61:
                    a = a + 4
                elif 61 < unit_num:
                    a = a - 8

                if unit_num % 20 != 0:
                    unit_num = unit_num % 20
                else:
                    unit_num = 20

            unit_ang = ((-1) ** (unit_num % 2)) * (unit_num // 2 * min_angle)
            unit_even_odd = ((-1) ** (unit_num % 2)) * b
            target_pos_x = self.defense_line - self.side * defense_radius * math.cos(unit_ang) + self.side * a
            target_pos_y = 31.5 + defense_radius * math.sin(unit_ang) + unit_even_odd
            if self.enemy_nuke_alert == 1:
                if Point2((target_pos_x, target_pos_y)).distance_to(self.enemy_nuke_position) < 10:
                    if target_pos_y > self.enemy_nuke_position.y:
                        target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) + (target_pos_y - self.enemy_nuke_position.y)
                        if target_pos_y > 62:
                            target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                    else:
                        target_pos_y = self.enemy_nuke_position.y - math.sqrt(
                            10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2)) - (self.enemy_nuke_position.y - target_pos_y)
                        if target_pos_y < 1:
                            target_pos_y = self.enemy_nuke_position.y + math.sqrt(
                                10.5 * 10.5 - (self.enemy_nuke_position.x - target_pos_x) ** (2))
                        else:
                            pass
                else:
                    pass
            else:
                pass
            return target_pos_x, target_pos_y
        else:
            return 1

    async def on_unit_destroyed(self, unit_tag):
        if unit_tag in self.unit_dict:
            self.my_death_min += self.unit_cost_data[self.unit_dict[unit_tag]][0]
            self.my_death_gas += self.unit_cost_data[self.unit_dict[unit_tag]][1]
            del self.unit_dict[unit_tag]

            if self.marine_pos_num.get(unit_tag, -2) != -2:
                del self.marine_pos_num[unit_tag]
                del self.marine_position[(unit_tag, 'x')]
                del self.marine_position[(unit_tag, 'y')]
            elif self.tank_pos_num.get(unit_tag, -2) != -2:
                del self.tank_pos_num[unit_tag]
                del self.tank_position[(unit_tag, 'x')]
                del self.tank_position[(unit_tag, 'y')]
            elif self.viking_pos_num.get(unit_tag, -2) != -2:
                del self.viking_pos_num[unit_tag]
                del self.viking_position[(unit_tag, 'x')]
                del self.viking_position[(unit_tag, 'y')]
            elif self.hellion_pos_num.get(unit_tag, -2) != -2:
                del self.hellion_pos_num[unit_tag]
                del self.hellion_position[(unit_tag, 'x')]
                del self.hellion_position[(unit_tag, 'y')]
            elif self.banshee_pos_num.get(unit_tag, -2) != -2:
                del self.banshee_pos_num[unit_tag]
                self.bv_harass_bond = [31.5, 31.5] #
                self.banshee_harass_switch = 0
        elif unit_tag in self.enemy_unit_dict:
            if self.enemy_unit_dict[unit_tag][0] == UnitTypeId.RAVEN:
                if self.emp_target_dict.get(unit_tag, -2) != -2:
                    del self.emp_target_dict[unit_tag]
                if self.game_time < 60:
                    self.enemy_has_raven = 0
                else:
                    pass
            elif self.enemy_unit_dict[unit_tag][0] == UnitTypeId.NUKE:
                if self.enemy_nuke_alert == 1:
                    self.enemy_nuke_boom_time = self.time
                else:
                    pass
            elif self.enemy_unit_dict[unit_tag][0] == UnitTypeId.GHOST:
                if self.enemy_nuke_alert == 1:
                    if self.time - self.enemy_nuke_alert_time < 10:
                        self.enemy_nuke_alert = 0
                    else:
                        pass
                else:
                    pass
            elif self.enemy_unit_dict[unit_tag][0] == UnitTypeId.BATTLECRUISER:
                for list_i in range(len(self.raven_matrix_target)):
                    if self.raven_matrix_target[list_i][0] == unit_tag:
                        del self.raven_matrix_target[list_i]
                        break
                    else:
                        pass
            elif self.enemy_unit_dict[unit_tag][0] == UnitTypeId.SIEGETANK or self.enemy_unit_dict[unit_tag][0] == UnitTypeId.SIEGETANKSIEGED:
                for list_i in range(len(self.raven_matrix_target)):
                    if self.raven_matrix_target[list_i][0] == unit_tag:
                        del self.raven_matrix_target[list_i]
                        break
                    else:
                        pass
            else:
                pass

            self.enemy_counter[self.enemy_unit_dict[unit_tag][0]] -= 1
            self.enemy_death_min += self.unit_cost_data[self.enemy_unit_dict[unit_tag][0]][0]
            self.enemy_death_gas += self.unit_cost_data[self.enemy_unit_dict[unit_tag][0]][1]
            del self.enemy_unit_dict[unit_tag]
        else:
            pass

    async def on_unit_created(self, unit: Unit):
        self.unit_dict[unit.tag] = unit.type_id
        if unit.type_id == UnitTypeId.BANSHEE:
            self.banshee_pos_num[unit.tag] = 2

