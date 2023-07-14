# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# #  Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import random
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const

@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def find_keys_with_keyword(dictionary, keyword):
    keys = []
    for key in dictionary:
        if keyword in key:
            keys.append(dictionary[key])
    return keys


def test_city_change_unit_prod(controller):
    controller.init_network()
    controller.get_observation()
    options = controller.turn_manager.get_available_actions()

    city_opt = options['city']

    for city_id in city_opt.cities.keys():
        pcity = city_opt.cities[city_id]

        valid_unit_prod_actions = find_keys_with_keyword(city_opt._action_dict[city_id], 'change_unit_prod')
        unit_prod_action = random.choice(valid_unit_prod_actions)
        assert (unit_prod_action.is_action_valid())

        prod_kind_1 = pcity['production_kind']
        prod_value_1 = pcity['production_value']

        unit_prod_action.trigger_action(controller.ws_client)
        controller.get_observation()
        prod_kind_2 = pcity['production_kind']
        prod_value_2 = pcity['production_value']

        assert (prod_kind_1 == prod_kind_2 and prod_value_1 != prod_value_2)
