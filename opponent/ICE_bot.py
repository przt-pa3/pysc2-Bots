
__author__ = 'Team_Flash 주홍영 강지우'


import time
import math

import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.ids.effect_id import EffectId

class Bot(sc2.BotAI):
    """
    아무것도 하지 않는 봇 예제
    """

    theta_to = 0
    ghost_move_step = 1
   

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

        if self.start_location.distance_to(Point2((32.5, 31.5))) < 5.0:
            # self.enemy_cc = self.enemy_start_locations[0]  # 적 시작 위치
            self.enemy_cc = Point2(Point2((95.5, 31.5)))  # 적 시작 위치
        else:
            self.enemy_cc = Point2(Point2((32.5, 31.5)))  # 적 시작 위치

        self.banshee_move = dict()


    

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

        """
        생산명령 생성
        기본적으로 마린 생산, 가스 300 이상일 때 전투순양함 생산
        """

        ccs = self.units(UnitTypeId.COMMANDCENTER)  # 전체 유닛에서 사령부 검색
        ccs = ccs.idle  # 실행중인 명령이 없는 사령부 검색

      
        ally_cc = self.start_location   # 아군 시작위치
        enemy_cc = self.enemy_cc.position  # 적군 시작위치
        


        marines = self.units(UnitTypeId.MARINE)  # 해병 검색 할당
        battlecruisers = self.units(UnitTypeId.BATTLECRUISER) # 전투순양함 검색 할당
        ghosts = self.units(UnitTypeId.GHOST)
        ravens = self.units(UnitTypeId.RAVEN)
        banshees = self.units(UnitTypeId.BANSHEE)


        if ccs.exists:  # 사령부가 하나이상 존재할 경우
            cc = ccs.first  # 첫번째 사령부 선택

            if self.time < 50:
                if self.vespene >= 200:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                        self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time                       
            elif self.time >=50 and self.time <70:
                if self.vespene >= 85:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.GHOST))
                        self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time    
            elif self.time >= 70 and self.time < 102:
                if self.vespene >= 60:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.BANSHEE))
                        self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time   
            elif self.time >=102 and self.time < 117:
                if self.vespene >= 75:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc(AbilityId.BUILD_NUKE))
                        self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time                 
            elif self.time >= 117 and ghosts.amount == 1:
                if self.vespene >= 75:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc(AbilityId.BUILD_NUKE))
                        self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time                  

            else:
                if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                    actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                    self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                        actions.append(cc.train(UnitTypeId.MARINE))
                        self.evoked[(cc.tag, 'train')] = self.time                 

            



        # 밤까마귀 아군 command_center 선회

        # 밤까마귀 선회 위치

        

        move_to = ally_cc + (7.5 * math.cos(self.theta_to), 7.5 * math.sin(self.theta_to))

        if self.known_enemy_units(UnitTypeId.GHOST).exists:
            enemy_ghosts = self.known_enemy_units(UnitTypeId.GHOST)
            move_to = enemy_ghosts[0].position
        else:
            move_to = ally_cc + (7.5 * math.cos(self.theta_to), 7.5 * math.sin(self.theta_to))
            

        for raven in ravens:
            actions.append(raven(AbilityId.MOVE, target = move_to ))
            if raven.distance_to (move_to) < 2.5:
                self.theta_to = self.theta_to + math.pi/4
                # print(raven.radius)
            
    
        
        if self.known_enemy_units(UnitTypeId.GHOST).exists:
            enemy_ghosts = self.known_enemy_units(UnitTypeId.GHOST)
            for ghost in enemy_ghosts:
                print(ghost.position)


        banshee_move_p1 = ally_cc + (0, 30)

        if enemy_cc[0] < 64:
            banshee_move_p2 = banshee_move_p1 + (-63, 0)
        else :
            banshee_move_p2 = banshee_move_p1 + (63, 0)

        banshee_move_p3 = banshee_move_p2 + (0, -30)

        for banshee in banshees:
            if banshee.distance_to(ally_cc) < 10:
                actions.append(banshee.move(banshee_move_p1))
            
            if banshee.distance_to(banshee_move_p1) < 2:
                actions.append(banshee.move(banshee_move_p2))

            if banshee.distance_to(banshee_move_p2) < 2:
                actions.append(banshee.attack(enemy_cc))





        ghost_move_p1 = ally_cc + (0, -30)

        if enemy_cc[0] < 64:
            ghost_move_p2 = ghost_move_p1 + (-63, 0)
        else :
            ghost_move_p2 = ghost_move_p1 + (63, 0)

        ghost_move_p3 = ghost_move_p2 + (0, 30)

        for ghost in ghosts:      
            
            # 은신 타이밍 잡기
            if ghost.energy >= 100 or ghost.health < ghost.health_max:
                actions.append(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))

            # 아래의 코드는 저격위치로 이동하기위한 코드

            
            """
            if self.ghost_move_step == 1 and ghost._proto.buff_ids:
                위의 코드로 아래 조건문 바꾸면 cloak 상태일 때만 저격하러 출발
                full coak을 원하면 energy = 130
            """            
            
            if self.ghost_move_step == 1:
                actions.append(ghost(AbilityId.MOVE, target = ghost_move_p1 ))
                if ghost.distance_to(ghost_move_p1) < 1:
                    self.ghost_move_step = 2

            if self.ghost_move_step == 2:
                if enemy_cc[0] > 64:
                    actions.append(ghost(AbilityId.MOVE, target =  ghost_move_p2 ))
                else:
                    actions.append(ghost(AbilityId.MOVE, target =  ghost_move_p2 ))
                    
                
                if ghost.distance_to(ghost_move_p2) < 1:
                    self.ghost_move_step = 3
            
            if self.ghost_move_step == 3:
                actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = enemy_cc))
            #     if ghost.distance_to(ghost_move_p3) < 3:
            #         self.ghost_move_step = 4

            # if self.ghost_move_step == 4:
            #     if enemy_cc[0] > 64:
            #         actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = enemy_cc + (6.75, 0)))
            #     else:
            #         actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = enemy_cc + (-6.75, 0)))


      
        # if self.known_enemy_units(UnitTypeId.GHOST).exists:
        #     enemy_ghosts = self.known_enemy_units(UnitTypeId.GHOST)
        #     marine_target = enemy_ghosts[0].position
        # else:
        #     marine_target = ally_cc + (1,0)


        battle_has_matrix_count = 0
        for battle in battlecruisers:
            if battle.has_buff(BuffId.RAVENSCRAMBLERMISSILE):
                battle_has_matrix_count = battle_has_matrix_count + 1
                
            jump = False
            for effect in self.state.effects:
                if effect.id == EffectId.NUKEPERSISTENT:
                    jump = True

            if jump:
                actions.append(battle(AbilityId.EFFECT_TACTICALJUMP, target = enemy_cc  ))     
            if jump:
                actions.append(battle(AbilityId.EFFECT_TACTICALJUMP, target = enemy_cc  ))            
            elif self.known_enemy_structures(UnitTypeId.COMMANDCENTER).exists:
                ecc = self.known_enemy_structures(UnitTypeId.COMMANDCENTER).closest_to(battle)
                actions.append(battle(AbilityId.YAMATO_YAMATOGUN, target = ecc  ))
            elif self.known_enemy_units(UnitTypeId.BATTLECRUISER).exists:
                enemy_battle = self.known_enemy_units(UnitTypeId.BATTLECRUISER)
                if enemy_battle.exists:
                    actions.append(battle(AbilityId.YAMATO_YAMATOGUN, target = enemy_battle[0]  ))
            elif self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).exists:
                enemy_viking = self.known_enemy_units(UnitTypeId.VIKINGFIGHTER)
                if enemy_viking.exists:
                    actions.append(battle(AbilityId.YAMATO_YAMATOGUN, target = enemy_viking[0]  ))

        if battle_has_matrix_count >= 1:
            self.battle_has_matrix = 0
        else:
            self.battle_has_matrix = 0

        for battle in battlecruisers:
            jump = False
            for effect in self.state.effects:
                if effect.id == EffectId.NUKEPERSISTENT:
                    jump = True
            
            if jump:
                if self.known_enemy_units.not_structure.visible.exists:
                    enemy = self.known_enemy_units.not_structure.visible.closest_to(battle)
                    actions.append(battle.attack(enemy))
                else:
                    actions.append(battle.attack(enemy_cc))
            else:
                actions.append(battle.attack(ally_cc))
                    

            # if self.battle_has_matrix == 1:
            #     actions.append(battle.move(enemy_cc))
            # elif False: # self.time - self.Nuke_calldown_time > 10 and self.Nuke_calldown == True:
            #     if battle.distance_to(self.Nuke_pos) < 10:
            #         actions.append(battle.move(ally_cc))
            #     else:
            #         actions.append(battle.attack(target))
            # else:
            #     if self.known_enemy_units.visible.exists:
            #         enemy = self.known_enemy_units.visible.closest_to(battle)
            #         if self.known_enemy_structures(UnitTypeId.COMMANDCENTER).exists:
            #             ecc = self.known_enemy_structures(UnitTypeId.COMMANDCENTER).closest_to(battle)
            #             if self.known_enemy_units(UnitTypeId.MULE).exists:
            #                 mule = self.known_enemy_units(UnitTypeId.MULE).closest_to(battle)
            #                 if mule.distance_to(enemy_cc) < 4:
            #                     actions.append(battle.attack(mule))
            #                 else:
            #                     actions.append(battle.attack(ecc))
            #             elif self.known_enemy_units(UnitTypeId.RAVEN).exists:
            #                 raven = self.known_enemy_units(UnitTypeId.RAVEN).closest_to(battle)
            #                 if raven.distance_to(enemy_cc) < 6:
            #                     actions.append(battle.attack(raven))
            #                 else:
            #                     actions.append(battle.attack(ecc))                            
            #             else:
            #                 actions.append(battle.attack(ecc))
            #         elif enemy.is_cloaked:
            #             actions.append(battle.attack(ally_cc))

            #         elif battle.distance_to(enemy) < 7.2 + 0.375:    
            #             actions.append(battle.move(enemy.position.towards(battle,10)))
                    
            #         else:
            #             if self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).exists:
            #                 enemy_viking = self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).closest_to(battle)
            #                 if battle.distance_to(enemy_viking) < enemy_viking.radius + battle.radius + 10:
            #                     actions.append(battle.move(enemy.position.towards(battle,10)))
            #                 else:
            #                     actions.append(battle.attack(enemy))
            #             elif self.known_enemy_units(UnitTypeId.VIKINGASSAULT).exists:
            #                 enemy_viking = self.known_enemy_units(UnitTypeId.VIKINGASSAULT).closest_to(battle)
            #                 if battle.distance_to(enemy_viking) < enemy_viking.radius + battle.radius + 10:
            #                     actions.append(battle.move(enemy.position.towards(battle,10)))
            #                 else:
            #                     actions.append(battle.attack(enemy))                            
            #             else :
            #                 actions.append(battle.attack(enemy))

            #     else:
            #         actions.append(battle.attack(ally_cc))            

  

        for marine in marines:            
            if self.known_enemy_units.amount > 10:
                if self.known_enemy_units(UnitTypeId.GHOST).exists and self.time - self.evoked.get((marine.tag, 'stimpack'), 0) > 10.0:
                    actions.append(marine(AbilityId.EFFECT_STIM))
                    self.evoked[(marine.tag, 'stimpack')] = self.time
            
            if self.time > 102:
                actions.append(marine.attack(enemy_cc))
            else:
                if ally_cc[0] < 64:
                    actions.append(marine.attack(ally_cc + (8,0)))
                else:
                    actions.append(marine.attack(ally_cc + (-8,0)))
            

 
        await self.do_actions(actions)

