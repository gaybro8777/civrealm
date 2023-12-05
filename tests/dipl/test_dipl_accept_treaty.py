# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import random
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option
import civrealm.freeciv.players.player_const as player_const


@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter(
        'debug.load_game', 'testcontroller_T169_2023-07-26-10_28')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def find_keys_with_keyword(dictionary, keyword):
    keys = []
    for key in dictionary:
        if keyword in key:
            keys.append(dictionary[key])
    return keys


def test_dipl_accept_treaty(controller):
    fc_logger.info("test_dipl_accept_treaty")
    _, options = get_first_observation_option(controller)

    player_opt = options['dipl']
    accept_treaty_act = find_keys_with_keyword(
        player_opt.get_actions(3, valid_only=True), 'accept_treaty')[0]

    assert (accept_treaty_act.is_action_valid())
    emb_1 = player_opt.players[3]['real_embassy'][0]

    accept_treaty_act.trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    emb_2 = player_opt.players[3]['real_embassy'][0]

    assert (emb_1 == 0 and emb_2 == 1)
