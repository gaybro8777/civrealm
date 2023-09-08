import gymnasium
import freeciv_gym
from freeciv_gym.freeciv.utils.freeciv_logging import ray_logger_setup
from freeciv_gym.envs.freeciv_parallel_env import FreecivParallelEnv
from freeciv_gym.configs import fc_args
import ray
import copy


class ParallelTensorEnv:
    def __init__(self, env_name, logger, epoch_num):
        # ray.init(local_mode=False, runtime_env={"worker_process_setup_hook": ray_logger_setup})
        # self.logger = ray_logger_setup()

        # Number of envs that run simultaneously
        self.batch_size_run = fc_args['batch_size_run']

        # Initialize envs
        self.envs = []
        self.env_name = env_name

        port_start = fc_args['port_start']
        for i in range(self.batch_size_run):
            temp_port = port_start+i*2
            env_core = gymnasium.make(env_name, client_port=temp_port)
            env = FreecivParallelEnv.remote(env_core)
            # breakpoint()
            self.envs.append(env)
            # breakpoint()


    def close(self):
        for env_id in range(self.batch_size_run):
            ray.get(self.envs[env_id].close.remote())

    def reset(self):
        result_ids = [self.envs[i].reset.remote() for i in range(self.batch_size_run)]
        results = ray.get(result_ids) # results: [(observation, info), ...]
        observations, infos = zip(*results)
        return observations, infos

    def step(self, actions):
        result_ids = []
        id_env_map = {}
        observations = [None] * self.batch_size_run
        rewards = [0]*self.batch_size_run
        infos = [None]*self.batch_size_run
        dones = [False]*self.batch_size_run
        terminated = [False]*self.batch_size_run
        truncated = [False]*self.batch_size_run
        
        for i in range(self.batch_size_run):
            id = self.envs[i].step.remote(actions[i])
            result_ids.append(id)
            id_env_map[id] = i

        # The num_returns=1 ensures ready length is 1.
        # ready, unready = ray.wait(result_ids, num_returns=1)
        unfinished = True
        while unfinished:
            ready, unready = ray.wait(unready, num_returns=1)
            # Get the env id corresponds to the given result id
            env_id = id_env_map[ready[0]]
            # print(f'env_id: {env_id}')
            try:
                result = ray.get(ready[0]) 
                # print(result)
                observations[env_id] = result[0]
                rewards[env_id] = result[1]
                terminated[env_id] = result[2]
                truncated[env_id] = result[3]
                infos[env_id] = result[4]
                dones[env_id] = terminated or truncated
                # , reward, terminated, truncated, infos[env_id] = result[0], result[1], result[2], result[3],
            except Exception as e:
                print(str(e))
                self.logger.warning(repr(e))
                dones[env_id] = True
            
            if dones[env_id]:
                env_port = ray.get(self.envs[env_id].get_port.remote())
                ray.get(self.envs[env_id].close.remote())
                new_env_port = env_port^1
                env_core = gymnasium.make(self.env_name, client_port=new_env_port)
                env = FreecivParallelEnv.remote(env_core, new_env_port)
                self.envs[env_id] = env

            if not unready:
                unfinished = False
            
        return observations, rewards, terminated, truncated, infos

