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
import gymnasium
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args, fc_web_args
from civrealm.freeciv.utils.port_utils import Ports

@pytest.fixture(params=["enabled", "disabled"])
def tech_env(request):
    endvictory = request.param
    fc_args["endvictory"] = endvictory
    fc_args["debug.load_game"] = "testcontroller_T370_tech_victory"
    env = gymnasium.make("freeciv/FreecivBase-v0", client_port=Ports.get())
    yield env, endvictory
    env.close()

def test_tech_victory(tech_env):
    fc_logger.info("test_tech_victory")
    env, endvictory = tech_env
    _, info = env.reset()
    done = False
    end_turn = 375
    while not done:
        _, reward, terminated, truncated, info = env.step(None)
        done = terminated or truncated or (info["turn"] == end_turn)
    if endvictory == "enabled":
        assert info["turn"] == 373
    elif fc_web_args["tag"] >= "1.1":
        assert info["turn"] == end_turn, "To ensure that you have the latest version of freeciv-web/fciv-net image >= 1.1!"

