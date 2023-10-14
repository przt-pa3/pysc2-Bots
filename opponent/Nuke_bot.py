
__author__ = 'Team_Flash 주홍영 강지우'


import time

import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2

class Bot(sc2.BotAI):
    """
    아무것도 하지 않는 봇 예제
    """
    
    time_flag = 0

    def __init__(self, *args, **kwargs):
        super().__init__()

    def on_start(self):
        """
        새로운 게임마다 초기화
        """
        self.build_order = list()
        self.evoked = dict()
        self.evoked['target move time'] = self.time
        self.evoked['siege diameter'] = 3

        """
        아군과 적 커멘드센터 위치 할당
        """
        if self.start_location.distance_to(Point2((32.5, 31.5))) < 5.0:
            self.enemy_cc = Point2(Point2((95.5, 31.5)))  # 적 시작 위치
        else:
            self.enemy_cc = Point2(Point2((32.5, 31.5)))  # 적 시작 위치
        
        self.enemy_unit_dict = dict()
        self.enemy_counter = dict()

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
        self.enemy_counter[UnitTypeId.MARAUDER] = 0
        self.enemy_counter[UnitTypeId.REAPER] = 0
        
        self.enemy_category = list(self.enemy_counter.keys())

        self.enemy_tank_pos = dict()

    async def on_step(self, iteration: int):
        """
        :param int iteration: 이번이 몇 번째 스텝인지를 인자로 넘겨 줌

        매 스텝마다 호출되는 함수
        주요 AI 로직은 여기에 구현
        """

        # 유닛들이 수행할 액션은 리스트 형태로 만들어서,
        # do_actions 함수에 인자로 전달하면 게임에서 실행된다.
        # do_action 보다, do_actions로 여러 액션을 동시에 전달하는 
        # 것이 훨씬 빠르다.
        actions = list()

        if self.known_enemy_units.not_structure.exists:
            for enemy_ind in self.known_enemy_units.not_structure:
                if enemy_ind.tag in list(self.enemy_unit_dict.keys()):
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x, enemy_ind.position.y]
                else:
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x, enemy_ind.position.y]
                    if self.enemy_unit_dict[enemy_ind.tag][0] in self.enemy_category:
                        self.enemy_counter[self.enemy_unit_dict[enemy_ind.tag][0]] += 1

        """
        생산명령 생성
        기본적으로 마린 생산, 가스 300 이상일 때 전투순양함 생산
        """

        # if self.time - self.time_flag > 1:
        #     print('self.enemy_counter[UnitTypeId.SIEGETANKSIEGED]')
        #     print(self.enemy_counter[UnitTypeId.SIEGETANKSIEGED])
        #     print('self.enemy_counter[UnitTypeId.MARINE]')
        #     print(self.enemy_counter[UnitTypeId.MARINE])
        #     print('self.enemy_counter[UnitTypeId.RAVEN]')
        #     print(self.enemy_counter[UnitTypeId.RAVEN])
        #     print('self.enemy_counter[UnitTypeId.HELLION]')
        #     print(self.enemy_counter[UnitTypeId.HELLION])
        #     self.time_flag = self.time


        ccs = self.units(UnitTypeId.COMMANDCENTER)  # 전체 유닛에서 사령부 검색
        ccs = ccs.idle  # 실행중인 명령이 없는 사령부 검색
        if ccs.exists:  # 사령부가 하나이상 존재할 경우
            cc = ccs.first  # 첫번째 사령부 선택
            
            if self.minerals >= 150:
                if self.vespene >= 125 and self.units(UnitTypeId.GHOST).amount == 0 and self.can_afford(UnitTypeId.GHOST):
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.GHOST))
                        self.evoked[(cc.tag, 'train')] = self.time
                
                if self.minerals >= 200 and self.can_afford(UnitTypeId.MARINE):
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time

            if self.units(UnitTypeId.GHOST).amount >= 1 :
                if self.vespene >= 100 and self.minerals >= 100:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:                  
                        actions.append(cc(AbilityId.BUILD_NUKE))
                        self.evoked[(cc.tag, 'train')] = self.time
                    

        ally_cc = self.start_location
        enemy_cc = self.enemy_cc


            
        # if ccs.first.orders:
        #     print('CC order')
        #     print(ccs.first.orders)
            

            # if self.units(UnitTypeId.GHOST).amount >= 1 and self.can_afford(UnitTypeId.MARINE) and self.minerals >= 100:
            #     actions.append(cc.train(UnitTypeId.MARINE))

        

        

        marines = self.units(UnitTypeId.MARINE)  # 해병 검색 할당
        battlecruisers = self.units(UnitTypeId.BATTLECRUISER) # 전투순양함 검색 할당
        ghosts = self.units(UnitTypeId.GHOST)


        for ghost in ghosts:        
            if enemy_cc[0] > 64:
                # actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = enemy_cc + (-6.75, 0)))
                actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = Point2((85, 31.5 ))))
            else:
                actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = enemy_cc + (21, 0)))
            
            # 아래의 코드는 저격위치로 이동하기위한 코드
            
            # if enemy_cc[0] > 64 and not ghost.position == enemy_cc + (-18.75, 0):
            #     actions.append(ghost(AbilityId.MOVE, target = enemy_cc + (-18.75, 0)) )

            # if enemy_cc[0] > 64 and ghost.distance_to(enemy_cc + (-33, 0)) > 0.3:
            #     actions.append(ghost(AbilityId.MOVE, target = enemy_cc + (-33, 0)) )
            if enemy_cc[0] > 64 and ghost.distance_to(Point2((73, 31.5 ))) > 0.4:
                actions.append(ghost(AbilityId.MOVE, target = Point2((73, 31.5 ))) )

            elif enemy_cc[0] < 64 and ghost.distance_to(enemy_cc + (33, 0)) > 0.3:
                actions.append(ghost(AbilityId.MOVE, target = enemy_cc + (33, 0)) )

            if ghost.health < ghost.health_max or ghost.energy < 90:
                actions.append(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))

            
        
            




        target = ally_cc.position + 0.1*(enemy_cc.position - ally_cc.position)

        # for marine in marines:
        #     actions.append(marine.attack(target))
 
        await self.do_actions(actions)

    prev_unit_tag = 0
    async def on_unit_destroyed(self, unit_tag):
        
        if self.prev_unit_tag != unit_tag:
            print('unit destroyed')
            if unit_tag in list(self.enemy_unit_dict.keys()):
                if self.enemy_unit_dict[unit_tag][0] in self.enemy_category:
                    self.enemy_counter[self.enemy_unit_dict[unit_tag][0]] -= 1
                    del self.enemy_unit_dict[unit_tag]
            
            if unit_tag in list(self.enemy_tank_pos.keys()):
                del self.enemy_tank_pos[unit_tag]

            prev_unit_tag = unit_tag