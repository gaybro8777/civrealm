# Copyright (C) 2023  The Freeciv-gym project
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


import os
# Disable log deduplication of Ray. This ensures the print messages from all actors can be shown.
os.environ['RAY_DEDUP_LOGS'] = '0'
import ray
import gymnasium as gym


@ray.remote
class FreecivParallelEnv():
    def __init__(self, env_id,*args,**kwargs):
        # Note that when the env_id is FreecivTensor-v0, it will call its reset() inside the make process. Therefore, the FreecivTensor-v0 has already connected to the server after initializing the environment.
        self.env = gym.make(env_id,*args,**kwargs)
        # print(f'FreecivParallelEnv: {self.env.get_username()}')
        # self.port = port
    
    def step(self, action):
        # import time
        # time.sleep(3)
        # action = None
        return self.env.step(action)
        
        observation, reward, terminated, truncated, info = self.env.step(action)
        return self.env.civ_controller.get_turn(), 0, False, truncated, self.env.civ_controller.get_turn()
    
    def reset(self,**kwargs):
        # print('FreecivParallelEnv.reset...')
        return self.env.reset(**kwargs)
        
        observation, info = self.env.reset()
        return self.env.civ_controller.get_turn(), self.env.civ_controller.get_turn()

    def close(self):
        self.env.close()

    def get_port(self):
        return self.env.get_port()
    
    def get_username(self):
        return self.env.get_username()

    def getattr(self, attr):
        return getattr(self.env, attr)

    def get_final_score(self):
        return self.env.get_final_score()
