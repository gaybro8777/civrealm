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


from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.envs.freeciv_wrapper import LLMWrapper
from civrealm.agents import BaseAgent, NoOpAgent, RandomAgent, ControllerAgent, RandomLLMAgent
from civrealm.configs import fc_args
from civrealm.freeciv.utils.data_handler import H5pyWriter
from civrealm.freeciv.utils.port_utils import Ports
import civrealm
import gymnasium

fc_args['debug.headless'] = True
fc_args['debug.window_size_x'] = 320
fc_args['debug.window_size_y'] = 320
fc_args['debug.get_webpage_image'] = ['map_tab']

def main():
    env = gymnasium.make('civrealm/FreecivBase-v0')
    env = LLMWrapper(env)
    agent = RandomLLMAgent()
    writer = H5pyWriter("test_dataset")

    observations, info = env.reset(client_port=Ports.get())
    done = False
    step = 0
    while not done:
        try:
            action = agent.act(observations, info)
            old_observations, old_info = observations, info
            observations, reward, terminated, truncated, info = env.step(
                action)
            if action is None:
                action = ['game', -1, 'end_turn']
            artifical_obs = {
                'entity_type': action[0],
                'action_name': action[2],
                'step_reward': reward,
            }
            writer.insert([artifical_obs, old_info, old_observations])
            print(
                f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
                f'Truncated: {truncated}, action: {action}')
            step += 1
            done = terminated or truncated
            if step >= 200:
                break
        except Exception as e:
            fc_logger.error(repr(e))
            raise e
    writer.close()
    env.close()

    '''
    players, tags, turns, evaluations = env.evaluate_game()
    '''
    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)

if __name__ == '__main__':
    main()
