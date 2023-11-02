# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


from civrealm.envs.freeciv_base_env import FreecivBaseEnv
from civrealm.freeciv.utils.unit_improvement_const import UNIT_TYPES
from civrealm.configs import fc_args
from civrealm.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES
from civrealm.freeciv.utils.language_agent_utility import TILE_INFO_TEMPLATE, DIR, get_valid_actions
from civrealm.freeciv.utils.language_agent_utility import action_mask
from civrealm.freeciv.players.player_const import DS_TXT

from civrealm.freeciv.utils.freeciv_logging import fc_logger


class FreecivCodeEnv(FreecivBaseEnv):
    """ CivRealm environment with code actions """

    def __init__(self, client_port: int = fc_args['client_port']):
        super().__init__(client_port=client_port)

    def get_actor_info(self, info, ctrl_type, actor_id, moves=0, utype=None):
        actor_info = dict()

        actor_name = None
        if ctrl_type == 'unit':
            actor_name = UNIT_TYPES[utype] + ' ' + str(actor_id)
        elif ctrl_type == 'city':
            actor_name = 'City' + ' ' + str(actor_id)
        actor_info[actor_name] = dict()
        actor_info[actor_name]['max_moves'] = moves

        avail_action_set = get_valid_actions(info, ctrl_type, actor_id)

        if not avail_action_set:
            return dict()
        else:
            if ctrl_type == 'unit':
                actor_info[actor_name]['avail_actions'] = avail_action_set
            elif ctrl_type == 'city':
                actor_info[actor_name]['avail_actions'] = action_mask(avail_action_set)

        return actor_info

    def get_mini_map_info(self, ctrl_type, ptile):
        x = ptile['x']
        y = ptile['y']
        mini_map_info = dict()

        tile_id = 0
        for ptile in TILE_INFO_TEMPLATE:
            mini_map_info[ptile] = []
            pdir = DIR[tile_id]
            dx = pdir[0]
            dy = pdir[1]

            map_state = self.civ_controller.map_ctrl.prop_state.get_state()
            (length, width) = map_state['status'].shape
            if not self.civ_controller.map_ctrl.is_out_of_map(x + dx, y + dy):
                new_x = x + dx
                new_y = y + dy
                if x + dx < 0:
                    new_x = length + x + dx
                if x + dx > (length - 1):
                    new_x = (x + dx) % (length - 1)

                if map_state['status'][new_x, new_y] == 0:
                    mini_map_info[ptile].append('unexplored')

                if map_state['terrain'][new_x, new_y] != 255:
                    terrain_id = map_state['terrain'][new_x, new_y]
                    terrain_str = TERRAIN_NAMES[terrain_id]
                    mini_map_info[ptile].append(terrain_str)

                for extra_id, extra_name in enumerate(EXTRA_NAMES):
                    if map_state['extras'][new_x, new_y, extra_id]:
                        mini_map_info[ptile].append(extra_name)

                for unit_id, unit_name in enumerate(UNIT_TYPES):
                    if map_state['unit'][new_x, new_y, unit_id]:
                        units_num = map_state['unit'][new_x, new_y, unit_id]
                        mini_map_info[ptile].append(str(int(units_num)) + ' ' + unit_name)

                if map_state['unit_owner'][new_x, new_y] != 255:
                    unit_owner = map_state['unit_owner'][new_x, new_y]
                    if unit_owner == self.civ_controller.player_ctrl.my_player_id:
                        units_dsp = 'Units belong to myself player_' + str(int(unit_owner))
                    else:
                        ds_of_units = self.civ_controller.dipl_ctrl.diplstates[unit_owner]
                        units_dsp = ('Units belong to a ' + DS_TXT[ds_of_units] + ' player_' + str(int(unit_owner)))
                    mini_map_info[ptile].append(units_dsp)

                if map_state['city_owner'][new_x, new_y] != 255:
                    city_owner = map_state['city_owner'][new_x, new_y]
                    if city_owner == self.civ_controller.player_ctrl.my_player_id:
                        city_dsp = '1 city belongs to myself player_' + str(city_owner)
                    else:
                        ds_of_city = self.civ_controller.dipl_ctrl.diplstates[city_owner]
                        city_dsp = '1 city belongs to a ' + DS_TXT[ds_of_city] + ' player_' + str(city_owner)
                    mini_map_info[ptile].append(city_dsp)

            tile_id += 1
        return mini_map_info

    def get_llm_info(self, info):

        llm_info = dict()
        if info['available_actions'] is not None:

            for ctrl_type in info['available_actions']:
                llm_info[ctrl_type] = dict()

                actors_can_act = None
                if ctrl_type in info['available_actions']:
                    actors_can_act = info['available_actions'][ctrl_type]

                if actors_can_act is None:
                    continue

                if ctrl_type == 'unit':
                    units = self.civ_controller.unit_ctrl.units

                    unit_dict = dict()
                    for punit in actors_can_act:
                        if units[punit]['activity'] != 0:
                            continue
                        ptile = self.civ_controller.map_ctrl.index_to_tile(units[punit]['tile'])

                        utype = units[punit]['type']
                        moves = units[punit]['movesleft']
                        actor_info = self.get_actor_info(info, ctrl_type, punit, moves, utype)
                        unit_dict.update(actor_info)
                        llm_info[ctrl_type][punit] = self.get_mini_map_info(ctrl_type, ptile)

                    llm_info[ctrl_type]['unit_dict'] = unit_dict

                elif ctrl_type == 'city':
                    cities = self.civ_controller.city_ctrl.cities

                    city_dict = dict()
                    for pcity in actors_can_act:
                        ptile = self.civ_controller.map_ctrl.index_to_tile(cities[pcity]['tile'])

                        if (self.civ_controller.turn_manager.turn == 1 or
                                self.civ_controller.turn_manager.turn == cities[pcity]['turn_last_built'] + 1):
                            actor_info = self.get_actor_info(info, ctrl_type, pcity, 1)
                        else:
                            actor_info = dict()
                        city_dict.update(actor_info)
                        llm_info[ctrl_type][pcity] = self.get_mini_map_info(ctrl_type, ptile)

                    llm_info[ctrl_type]['city_dict'] = city_dict

                else:
                    continue

        return llm_info

    def step(self, action):
        import time
        start_time = time.time()

        self.civ_controller.perform_action(action)
        info, observation = self._get_info_and_observation()

        llm_info = self.get_llm_info(info)
        info['llm_info'] = llm_info

        reward = self._get_reward()
        terminated = self._get_terminated()
        truncated = self._get_truncated()

        available_actions = info['available_actions']
        self._record_action(available_actions, action)

        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time > 15:
            fc_logger.debug('Running too slow.')
            assert (False)

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.civ_controller.init_network()
        info, observation = self._get_info_and_observation()

        llm_info = self.get_llm_info(info)
        info['llm_info'] = llm_info

        return observation, info