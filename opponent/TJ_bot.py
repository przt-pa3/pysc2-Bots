
__author__ = 'Team_Flash 주홍영 강지우'


import time

import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.data import Alert
from sc2.ids.effect_id import EffectId


class Bot(sc2.BotAI):
    """
    아무것도 하지 않는 봇 예제
    """
    time_flag = 0
    time_flag_2 = 0
    battle_has_matrix = 0
    need_repair = False
    fast_nuke = False
    strategy_num = 1
    Nuke_pos = Point2((0,0))
    Nuke_calldown = False
    Nuke_calldown_time = 0
    


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
         
        actions = list() # 명령을 하달하기 위한 list
        enemy_cc = self.enemy_cc
        ally_cc = self.start_location

        """
        패스트 전술핵 대응
        """
        if self.alert(Alert.NuclearLaunchDetected):
            self.fast_nuke = True

        """
        은신 유닛 대응
        """
        

        # if self.known_enemy_units.exists:
        #     enemys = self.known_enemy_units
            
        #     if self.time - self.time_flag > 1:           
        #         for enemy in enemys:
        #             print(enemy.type_id)
        #             print(enemy.is_cloaked)
        #             print(enemy.position)
        #             print('orders?')
        #             print(enemy._proto.orders)
        #             print('is enemy?')
        #             print(enemy.is_enemy)
                
        #         self.time_flag = self.time



        """
        유닛 검색 및 할당
        """
        ccs = self.units(UnitTypeId.COMMANDCENTER).idle         # 전체 유닛에서 사령부 검색
        marines = self.units(UnitTypeId.MARINE)                 # 해병 검색 할당
        battlecruisers = self.units(UnitTypeId.BATTLECRUISER)   # 전투순양함 검색 할당
        mules = self.units(UnitTypeId.MULE)                     # 지게로봇 검색 할당
        viking_assaults = self.units(UnitTypeId.VIKINGASSAULT)  # 바이킹(지상) 검색 할당
        viking_fighters = self.units(UnitTypeId.VIKINGFIGHTER)  # 바이킹(공중) 검색 할당
        ravens = self.units(UnitTypeId.RAVEN)                   # 밤까마귀 검색 할당
        ghosts = self.units(UnitTypeId.GHOST)                   # 유령 검색 할당
        hellions = self.units(UnitTypeId.HELLION)               # 화염차 검색 할당
        banshees = self.units(UnitTypeId.BANSHEE)                # 밴시 검색 할당
        

        """
        전술 정하는 알고리즘
        """

        # if self.known_enemy_units.not_structure.exists:
        #     for enemy_ind in self.known_enemy_units.not_structure:
        #         self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x, enemy_ind.position.y]
        #         print(self.enemy_unit_dict[enemy_ind.tag])

        # enemy_list = list(self.enemy_unit_dict.keys())

        # for enemy_ind in enemy_list:
        #     self.enemy_counter[self.enemy_unit_dict[enemy_ind.tag][0]] += 1


        

        if self.known_enemy_units.not_structure.exists:
            for enemy_ind in self.known_enemy_units.not_structure:
                if enemy_ind.tag in list(self.enemy_unit_dict.keys()):
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x, enemy_ind.position.y]
                else:
                    self.enemy_unit_dict[enemy_ind.tag] = [enemy_ind.type_id, enemy_ind.position.x, enemy_ind.position.y]
                    if self.enemy_unit_dict[enemy_ind.tag][0] in self.enemy_category:
                        self.enemy_counter[self.enemy_unit_dict[enemy_ind.tag][0]] += 1

                
        
        self.strategy_num = 1
        
        # for enemy in self.known_enemy_units:
        #     if enemy.is_cloaked and self.units(UnitTypeId.RAVEN).amount == 0:
        #         self.strategy_num = 5



        """
        커멘드센터 명령 생성
        """

        # 기본빌드
        if self.strategy_num == 1:
            if ccs.exists:  # 사령부가 하나이상 존재할 경우
                cc = ccs.first  # 첫번째 사령부 선택

                if self.minerals >= 450 :
                    

                    if self.can_afford(UnitTypeId.BATTLECRUISER):
                        if self.units(UnitTypeId.RAVEN).amount == 0:
                            pass
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                                self.evoked[(cc.tag, 'train')] = self.time

                    if self.can_afford(UnitTypeId.BANSHEE):
                        if self.units(UnitTypeId.RAVEN).amount == 0 and self.units(UnitTypeId.BANSHEE).amount == 0:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.BANSHEE))
                                self.evoked[(cc.tag, 'train')] = self.time

                        elif self.units(UnitTypeId.RAVEN).amount == 0:
                            if self.can_afford(UnitTypeId.RAVEN):
                                if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                    actions.append(cc.train(UnitTypeId.RAVEN))
                                    self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time                                    
                    else:
                        if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                            actions.append(cc.train(UnitTypeId.MARINE))
                            self.evoked[(cc.tag, 'train')] = self.time

                if cc.energy > 50 and self.need_repair:
                    actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target = self.start_location + (3,0)))

        # vs 전순함빌드
        if self.strategy_num == 2:
            if ccs.exists:  # 사령부가 하나이상 존재할 경우
                cc = ccs.first  # 첫번째 사령부 선택

                if self.enemy_counter[UnitTypeId.BATTLECRUISER] * 4 > viking_assaults.amount + viking_fighters.amount:
                    if self.minerals >= 200 :
                        if self.can_afford(UnitTypeId.VIKINGFIGHTER):
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.VIKINGFIGHTER))
                                self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.minerals >= 450 :
                        if self.can_afford(UnitTypeId.BATTLECRUISER):
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                                self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time

                    if cc.energy > 50 and self.need_repair:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target = self.start_location + (3,0)))


        # vs 공성전차빌드
        if self.strategy_num == 3:
            if ccs.exists:  # 사령부가 하나이상 존재할 경우
                cc = ccs.first  # 첫번째 사령부 선택

                if self.units(UnitTypeId.GHOST).amount == 0:
                    if self.minerals >= 150:
                        if self.can_afford(UnitTypeId.GHOST):
                            actions.append(cc.train(UnitTypeId.GHOST))

                else:
                    if self.minerals >= 450 :
                        if self.can_afford(UnitTypeId.BATTLECRUISER):
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                                self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.units(UnitTypeId.GHOST).amount >= 1 :
                                if self.vespene >= 100 and self.minerals >= 100:                  
                                    actions.append(cc(AbilityId.BUILD_NUKE))    
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time

                if cc.energy > 50 and self.need_repair:
                    actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target = self.start_location + (3,0)))

                

        # vs 바이킹빌드
        if self.strategy_num == 4:
            if ccs.exists:  # 사령부가 하나이상 존재할 경우
                cc = ccs.first  # 첫번째 사령부 선택
                viking_amount = self.enemy_counter[UnitTypeId.VIKINGASSAULT] + self.enemy_counter[UnitTypeId.VIKINGFIGHTER]
                if viking_amount + 2 >= viking_assaults.amount + viking_fighters.amount:
                    if self.minerals >= 200 :
                        if self.can_afford(UnitTypeId.VIKINGFIGHTER):
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.VIKINGFIGHTER))
                                self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time
                else:
                    if self.minerals >= 450 :
                        if self.can_afford(UnitTypeId.BATTLECRUISER):
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                                actions.append(cc.train(UnitTypeId.BATTLECRUISER))
                                self.evoked[(cc.tag, 'train')] = self.time
                        else:
                            if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                                actions.append(cc.train(UnitTypeId.MARINE))
                                self.evoked[(cc.tag, 'train')] = self.time

                    if cc.energy > 50 and self.need_repair:
                        actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target = self.start_location + (3,0)))
        
        # 은신 유닛 대응
        if self.strategy_num == 5:
            if ccs.exists:  # 사령부가 하나이상 존재할 경우
                cc = ccs.first  # 첫번째 사령부 선택

                if self.minerals >= 450 :
                    if self.can_afford(UnitTypeId.RAVEN):
                        if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                            actions.append(cc.train(UnitTypeId.RAVEN))
                            self.evoked[(cc.tag, 'train')] = self.time
                    else:
                        if self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0 :
                            actions.append(cc.train(UnitTypeId.MARINE))
                            self.evoked[(cc.tag, 'train')] = self.time

                if cc.energy > 50 and self.need_repair:
                    actions.append(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target = self.start_location + (3,0)))


        

        """
        유닛 명령 생성
        """

        # 타겟 설정
        target = ally_cc

        burst_time = 300

        if self.time >= burst_time:
            target = enemy_cc.position

        

        # 화염차 명령 생성
        for hellion in hellions:
            if self.time < burst_time:
                actions.append(hellion.attack(ally_cc))
            else:
                if self.known_enemy_units.not_structure.not_flying.exists:
                    enemy = self.known_enemy_units.not_structure.not_flying.closest_to(hellion)
                    if hellion.weapon_cooldown != 0:
                        actions.append(hellion.move(enemy.position.towards(hellion,10)))
                    else :
                        actions.append(hellion.attack(enemy))
                else:
                    actions.append(hellion.attack(target))



        

        # 전투순양함 명령 생성
        battle_has_matrix_count = 0

        for battle in battlecruisers:
            if battle.has_buff(BuffId.RAVENSCRAMBLERMISSILE):
                battle_has_matrix_count = battle_has_matrix_count + 1

            if self.time > burst_time + 3 and battle.distance_to(enemy_cc) > 10:
                if ally_cc[0] < 64:
                    actions.append(battle(AbilityId.EFFECT_TACTICALJUMP, target = enemy_cc + (24,0)  ))   
                else:
                    actions.append(battle(AbilityId.EFFECT_TACTICALJUMP, target = enemy_cc + (-24,0)  )) 
            elif burst_time < self.time and self.known_enemy_structures(UnitTypeId.COMMANDCENTER).exists:
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
                
        if self.time - self.time_flag_2 > 1:
            # print('self.time - self.Nuke_calldown_time')
            # print(self.time - self.Nuke_calldown_time)
            self.time_flag_2 = self.time
            


        for battle in battlecruisers:
            if self.time > burst_time + 3:
                if self.known_enemy_units(UnitTypeId.COMMANDCENTER).exists:
                    ecc = self.known_enemy_units(UnitTypeId.COMMANDCENTER).first
                    actions.append(battle.attack(ecc))
                else:
                    actions.append(battle.move(enemy_cc))
            else:
                actions.append(battle.attack(ally_cc))




        # 해병 명령 생성
        
        pos_min = 128
        pos_max = 0

        if False:   # self.strategy_num == 3 or self.enemy_counter[UnitTypeId.SIEGETANKSIEGED] + self.enemy_counter[UnitTypeId.SIEGETANK] >= 1:
           
            for enemy_tag in self.enemy_unit_dict.keys():
                if self.enemy_unit_dict[enemy_tag][0] == UnitTypeId.SIEGETANKSIEGED:
                    self.enemy_tank_pos[enemy_tag] = [self.enemy_unit_dict[enemy_tag][1], self.enemy_unit_dict[enemy_tag][2]]

            if self.start_location.distance_to(Point2((32.5, 31.5))) < 5.0:
                for pos in self.enemy_tank_pos: # 여기서 pos 는 tag로 출력됨 유의하셈
                    if self.enemy_tank_pos[pos][0] < pos_min:
                        pos_min = self.enemy_tank_pos[pos][0]
            else:
                for pos in self.enemy_tank_pos: # 여기서 pos 는 tag로 출력됨 유의하셈
                    if self.enemy_tank_pos[pos][0] > pos_max:  
                        pos_max = self.enemy_tank_pos[pos][0]
            
            for marine in marines:
                if self.start_location.distance_to(Point2((32.5, 31.5))) < 5.0:
                    if marine.position[0] > pos_min - 16:
                        actions.append(marine.move(ally_cc))
                    else:
                        actions.append(marine.attack(target))

                else:
                    if marine.position[0] < pos_max + 16:
                        actions.append(marine.move(ally_cc))
                    else:
                        actions.append(marine.attack(target))
        else:
            for marine in marines:
                if self.known_enemy_units.exists:
                    closest_enemy = self.known_enemy_units.closest_to(marine)
                    if self.known_enemy_units.amount >= 10 and marine.distance_to(closest_enemy) < 7.0:
                        if self.time - self.evoked.get((marine.tag, 'stimpack'), 0) > 10.0:
                            if marine.health_percentage > 0.5:
                                actions.append(marine(AbilityId.EFFECT_STIM))
                                self.evoked[(marine.tag, 'stimpack')] = self.time

                if self.time - self.Nuke_calldown_time > 10 and self.Nuke_calldown == True:
                    if marine.distance_to(self.Nuke_pos) < 10:
                        actions.append(marine.move(ally_cc))
                    else:
                        actions.append(marine.attack(target))
                else:
                    nuke = False
                    for effect in self.state.effects:
                        if effect.id == EffectId.NUKEPERSISTENT:
                            nuke = True
                            
                    if nuke:
                        actions.append(marine.move(ally_cc))     
                    else:               
                        if ally_cc[0] < 64:
                            actions.append(marine(AbilityId.ATTACK, target =  target + (15,0)))
                        else:
                            actions.append(marine(AbilityId.ATTACK, target =  target + (-15,0)))                        
        
        # 밴시 명령 생성
        for banshee in banshees:
            if self.time < 50:
                if self.known_enemy_units.not_structure.not_flying.exists:
                    if banshee.energy < 15:
                        actions.append(banshee.move(ally_cc))
                    else:
                        enemy = self.known_enemy_units.not_structure.not_flying.closest_to(banshee)
                        if self.known_enemy_units(UnitTypeId.MARINE).exists:
                            enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(banshee)
                            if banshee.distance_to(enemy_marine) < 6:
                                actions.append(banshee.move(ally_cc))
                            else :
                                actions.append(banshee.attack(enemy))
                        else:
                            actions.append(banshee.attack(enemy))
                    
                else:
                    if banshee.energy < 15:
                        actions.append(banshee.move(ally_cc))
                    else:
                        actions.append(banshee.attack(enemy_cc))
            else:
                if self.known_enemy_units.not_structure.not_flying.exists:
                    enemy = self.known_enemy_units.not_structure.not_flying.closest_to(banshee)
                    if self.known_enemy_units(UnitTypeId.MARINE).exists:
                        enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(banshee)
                        if banshee.distance_to(enemy_marine) < 6:
                            actions.append(banshee.move(ally_cc))
                        else :
                            actions.append(banshee.attack(enemy))
                    else:
                        actions.append(banshee.attack(enemy))               
                
                else:
                    actions.append(banshee.attack(enemy_cc))


            if banshee.health < banshee.health_max:
                actions.append(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))                   
         

        # 바이킹 명령 생성
        for viking in viking_fighters:
            if self.time < burst_time:
                if self.known_enemy_units.visible.flying.exists :
                    flying_enemys = self.known_enemy_units.visible.flying
                    viking_target = flying_enemys.closest_to(viking)

                    if viking.distance_to(flying_enemys.closest_to(viking)) < 20:

                        if self.known_enemy_units(UnitTypeId.MARINE).exists:
                            enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(viking)
                            if viking.distance_to(enemy_marine) < 7.5:
                                actions.append(viking.move(enemy_marine.position.towards(viking,10)))
                            else:
                                if viking.weapon_cooldown !=0:
                                    if viking_target.radius + 8.0 + viking.radius > viking.distance_to(viking_target):
                                        actions.append(viking.move(viking_target.position.towards(viking,10)))
                                    else :
                                        actions.append(viking.attack(viking_target))
                                else:
                                    actions.append(viking.attack(viking_target))

                        else:
                            if viking.weapon_cooldown != 0:
                                if viking_target.radius + 8.0 + viking.radius > viking.distance_to(viking_target):
                                    actions.append(viking.move(viking_target.position.towards(viking,10)))
                                else :
                                    actions.append(viking.attack(viking_target))
                            else:
                                actions.append(viking.attack(viking_target))      
                    else:
                        if self.known_enemy_units(UnitTypeId.MARINE).exists:
                            enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(viking)
                            if viking.distance_to(enemy_marine) < 7.5:
                                actions.append(viking.move(enemy_marine.position.towards(viking,10)))
                            else:
                                if ally_cc[0] > 64:
                                    actions.append(viking.attack(ally_cc + (5,0))) 
                                else:
                                    actions.append(viking.attack(ally_cc + (-5,0))) 
                        else:
                            if ally_cc[0] > 64:
                                actions.append(viking.attack(ally_cc + (5,0))) 
                            else:
                                actions.append(viking.attack(ally_cc + (-5,0)))                         
                else:
                    if self.known_enemy_units(UnitTypeId.MARINE).exists:
                        enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(viking)
                        if viking.distance_to(enemy_marine) < 7.5:
                            actions.append(viking.move(enemy_marine.position.towards(viking,10)))
                        else:
                            if ally_cc[0] > 64:
                                actions.append(viking.attack(ally_cc + (5,0))) 
                            else:
                                actions.append(viking.attack(ally_cc + (-5,0))) 
                    else:
                        if ally_cc[0] > 64:
                            actions.append(viking.attack(ally_cc + (5,0))) 
                        else:
                            actions.append(viking.attack(ally_cc + (-5,0))) 

            
            elif self.known_enemy_units.visible.flying.exists:
                flying_enemys = self.known_enemy_units.visible.flying
                viking_target = flying_enemys.closest_to(viking)

                if self.known_enemy_units(UnitTypeId.MARINE).exists:
                    enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(viking)
                    if viking.distance_to(enemy_marine) < 7.5:
                        actions.append(viking.move(enemy_marine.position.towards(viking,10)))
                    else:
                        if viking.weapon_cooldown !=0:
                            if viking_target.radius + 8.0 + viking.radius > viking.distance_to(viking_target):
                                actions.append(viking.move(viking_target.position.towards(viking,10)))
                            else :
                                actions.append(viking.attack(viking_target))
                        else:
                            actions.append(viking.attack(viking_target))

                else:
                    if viking.weapon_cooldown != 0:
                        if viking_target.radius + 8.0 + viking.radius > viking.distance_to(viking_target):
                            actions.append(viking.move(viking_target.position.towards(viking,10)))
                        else :
                            actions.append(viking.attack(viking_target))
                    else:
                        actions.append(viking.attack(viking_target))       
            else:
                if self.known_enemy_units(UnitTypeId.MARINE).exists:
                    enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(viking)
                    if viking.distance_to(enemy_marine) < 7.5:
                        actions.append(viking.move(enemy_marine.position.towards(viking,10)))
                    else:
                        if ally_cc[0] > 64:
                            actions.append(viking.attack(target + (5,0))) 
                        else:
                            actions.append(viking.attack(target + (-5,0))) 
                else:
                    if ally_cc[0] > 64:
                        actions.append(viking.attack(target + (5,0))) 
                    else:
                        actions.append(viking.attack(target + (-5,0)))               


            if self.enemy_counter[UnitTypeId.VIKINGFIGHTER] + self.enemy_counter[UnitTypeId.VIKINGASSAULT] + self.enemy_counter[UnitTypeId.BATTLECRUISER] + self.enemy_counter[UnitTypeId.BANSHEE] + self.enemy_counter[UnitTypeId.RAVEN] <= 0:
                if self.known_enemy_units.exists == False:
                    if viking.distance_to(enemy_cc) < 10:
                        actions.append(viking(AbilityId.MORPH_VIKINGASSAULTMODE))
                    else:
                        pass
                else:
                    actions.append(viking(AbilityId.MORPH_VIKINGASSAULTMODE))


        for viking in viking_assaults:
            flying_enemys = self.known_enemy_units.visible.flying
            if self.enemy_counter[UnitTypeId.VIKINGFIGHTER] + self.enemy_counter[UnitTypeId.VIKINGASSAULT] + self.enemy_counter[UnitTypeId.BATTLECRUISER] + self.enemy_counter[UnitTypeId.BANSHEE] + self.enemy_counter[UnitTypeId.RAVEN] >= 1:           
                actions.append(viking(AbilityId.MORPH_VIKINGFIGHTERMODE))
            else:
                actions.append(viking.attack(target))

        
        # 밤까마귀 명령 생성
        for raven in ravens:
            enemys = self.known_enemy_units
            if self.known_enemy_units.exists:           
                if self.known_enemy_units(UnitTypeId.BANSHEE).exists and self.time < 60 and self.units(UnitTypeId.AUTOTURRET).amount == 0 and self.known_enemy_units(UnitTypeId.BANSHEE).center.position.distance_to(ally_cc) < 25:
                    print('build_turret')

                    turret_target = self.known_enemy_units(UnitTypeId.BANSHEE).center.position
                    actions.append(raven(AbilityId.BUILDAUTOTURRET_AUTOTURRET , target = turret_target))                      

                elif self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).exists and self.known_enemy_units(UnitTypeId.MARINE).exists:
                    enemy_vikingfighter = self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).closest_to(raven)
                    enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(raven)
                    if raven.distance_to(enemy_vikingfighter) < 10 or raven.distance_to(enemy_marine) < 7: 
                        if raven.distance_to(enemy_vikingfighter) - 10 > raven.distance_to(enemy_marine) -7:
                            actions.append(raven.move(enemy_marine.position.towards(raven,10)))
                        else:
                            actions.append(raven.move(enemy_vikingfighter.position.towards(raven,10)))
                    else:
                        for enemy in enemys:
                            if enemy.is_cloaked:
                                actions.append(raven.move(enemy.position))
                            else:
                                actions.append(raven.move(self.units.center))


                            
                elif self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).exists:
                    enemy_vikingfighter = self.known_enemy_units(UnitTypeId.VIKINGFIGHTER).closest_to(raven)
                    if raven.distance_to(enemy_vikingfighter) < 10:
                        actions.append(raven.move(enemy_vikingfighter.position.towards(raven,10)))
                    else:
                        for enemy in enemys:
                            if enemy.is_cloaked:
                                actions.append(raven.move(enemy.position))
                            else:
                                actions.append(raven.move(self.units.center))

                
                elif self.known_enemy_units(UnitTypeId.MARINE).exists:
                    enemy_marine = self.known_enemy_units(UnitTypeId.MARINE).closest_to(raven)
                    if raven.distance_to(enemy_marine) < 7:
                        actions.append(raven.move(ally_cc))
                    else:
                        for enemy in enemys:
                            if enemy.is_cloaked:
                                actions.append(raven.move(enemy.position))
                            else:
                                actions.append(raven.move(self.units.center))
                else :
                    actions.append(raven.move(self.units.center))    

            else:
                actions.append(raven.move(self.units.center))


        # 유령 명령 생성
        for ghost in ghosts:        
            if enemy_cc[0] > 64:
                if ghost.is_cloaked or ghost.energy < 74:
                    actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = Point2((pos_min - 4, 32))))
            else:
                if ghost.is_cloaked or ghost.energy < 74:
                    actions.append(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target = Point2((pos_max + 4, 32))))
            
            # 아래의 코드는 저격위치로 이동하기위한 코드

            if ghost.energy >= 80:
                actions.append(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))

            if ghost.is_using_ability(AbilityId.TACNUKESTRIKE_NUKECALLDOWN):
                # 여기다가 print추가해서 이게 언제 활성화되는지 확인하기
                if self.units(UnitTypeId.NUKE).exists:
                    self.Nuke_calldown = True
                    if self.time - self.Nuke_calldown_time > 16: # 정확히 14초가 아니어서 뻑나는 느낌이 듭니다
                        self.Nuke_calldown_time = self.time
                        if enemy_cc[0] > 64:
                            self.Nuke_pos = Point2((pos_min - 4, 32))
                        else:
                            self.Nuke_pos = Point2((pos_max + 4, 32))
            else:
                self.Nuke_calldown = False
                self.Nuke_calldown_time = 0
            
        



        # 지게로봇 명령 생성
        for mule in mules:
            if battlecruisers.exists:
                battle = battlecruisers[0]
                actions.append(mule.repair(battle))
        
        for battle in battlecruisers:
                if battle.health < battle.health_max:
                    self.need_repair = True

                     

        await self.do_actions(actions)
    

    prev_unit_tag = 0
    async def on_unit_destroyed(self, unit_tag):
        if self.prev_unit_tag != unit_tag:
            if unit_tag in list(self.enemy_unit_dict.keys()):
                if self.enemy_unit_dict[unit_tag][0] in self.enemy_category:
                    self.enemy_counter[self.enemy_unit_dict[unit_tag][0]] -= 1
                    del self.enemy_unit_dict[unit_tag]
            
            if unit_tag in list(self.enemy_tank_pos.keys()):
                del self.enemy_tank_pos[unit_tag]

            prev_unit_tag = unit_tag

        
        
        # 뭔가 unit_tag가 사라져서 더이상 type이나 position을 못보는데 참조하려고 해서 오류가 생기는 느낌

    

            # for enemy_tag in list(self.enemy_unit_dict.keys()):
            #     if unit_tag == enemy_tag:
            #         if self.enemy_unit_dict[enemy_tag][0] in enemy_category:
            #             self.enemy_counter[self.enemy_unit_dict[enemy_tag][0]] -= 1

