# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License 
# for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.utils.fc_types as fc_types
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.utility import byte_to_bit_array, find_set_bits
from BitVector import BitVector

@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T154_2023-07-25-09_52')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_get_action_pro_spy(controller):
    fc_logger.info("test_get_action_pro_spy")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    # Get all units (including those controlled by other players)
    # for unit_id in unit_opt.unit_ctrl.units.keys():
    # Get all unit type information
    # for type in unit_opt.rule_ctrl.unit_types:
    #     name = unit_opt.rule_ctrl.unit_types[type]['name']
    #     if name == 'Nuclear' or name == 'Helicopter' or name == 'Horsemen':
    #         print(unit_opt.rule_ctrl.unit_types[type])
    #         print('===============')
    # Get all units controlled by the current player
    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]        
        ptile = unit_focus.ptile
        # print(
        #     f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")
        if unit_id == 1164:
            # The agent cannot move to sea.
            assert(unit_focus.action_prob[map_const.DIR8_SOUTHWEST][fc_types.ACTION_SPY_BRIBE_UNIT] == {'min': 200, 'max': 200})
        
        # for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        #     if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
        #         print(f'index: {i}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T154_2023-07-25-09_52')
    test_get_action_pro_spy(controller)


if __name__ == '__main__':
    main()