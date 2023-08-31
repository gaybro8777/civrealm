from typing import (
    Union,
    Tuple,
    Mapping,
    MutableMapping,
    Sequence,
    Callable,
    Hashable,
)
from collections.abc import Mapping, Sequence

import numpy as np
from gymnasium.core import Wrapper, ObservationWrapper, Env, spaces
from freeciv_gym.envs.freeciv_space import Onehot
from .utils import *

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")


class FilterObservation(ObservationWrapper):
    def __init__(
        self,
        env: Env,
        filter_keys: Union[Mapping, Sequence] = [],
        filter_out=False,
        cache_keys: Union[Mapping, Sequence] = [],
    ):
        super().__init__(env)

        self._env = env
        self.__cache_args = (filter_keys, filter_out, cache_keys)
        self._observation_space = None

        wrapped_observation_space = env.observation_space

        if not isinstance(wrapped_observation_space, spaces.Dict):
            # HACK: hacky part to avoid dynamic observation space handling
            if isinstance(wrapped_observation_space, spaces.Discrete):
                self._initialized = False
                return
            raise ValueError(
                f"FilterDictObservation is only usable with dict observations, "
                f"environment observation space is {type(wrapped_observation_space)}"
            )

        # HACK: I am so soryy about this. Later transfer this into more elegant code.
        self.init()

    def init(self):
        if self._initialized:
            return
        (filter_keys, filter_out, cache_keys) = self.__cache_args
        wrapped_observation_space = self._env.observation_space
        if not isinstance(wrapped_observation_space, spaces.Dict):
            # HACK hacky part to avoid dynamic observation space handling
            if isinstance(wrapped_observation_space, spaces.Discrete):
                self.__cache_args = (filter_keys, filter_out, cache_keys)
                self._initialized = False
                return self
            raise ValueError(
                f"FilterDictObservation is only usable with dict observations, "
                f"environment observation space is {type(wrapped_observation_space)}"
            )

        observation_keys = get_space_keys(wrapped_observation_space)

        if not filter_out:
            filter_keys = filter_keys if filter_keys else observation_keys
            missing_keys = get_missing_keys(observation_keys, filter_keys)
            if missing_keys:
                raise ValueError(
                    "All the filter_keys must be included in the original observation space.\n"
                    f"Filter keys: {filter_keys}\n"
                    f"Observation keys: {observation_keys}\n"
                    f"Missing keys: {missing_keys}"
                )

        full_filter_keys = complete_filter_keys(
            observation_keys, filter_keys, filter_out
        )
        self._observation_space = filter_space(
            wrapped_observation_space, full_filter_keys
        )
        self.__filter_kwargs = (filter_keys, filter_out)
        self.__full_filter_keys = full_filter_keys
        self.__full_cache_keys = complete_filter_keys(observation_keys, cache_keys)
        self.__cache = {}
        self._initialized = True

    def observation(self, observation):
        if not self._initialized:
            self.init()
        if self.__full_cache_keys:
            self.cache = filter_data(observation, self.__full_cache_keys)
        return filter_data(observation, self.__full_filter_keys)

    @property
    def observation_space(self):
        self.init()
        return (
            self._env.observation_space
            if not self._observation_space
            else self._observation_space
        )

    def pop_cache(self):
        result = self.__cache
        self.__cache = {}
        return result


class OnehotifyObservation(ObservationWrapper):
    def __init__(
        self,
        env: Env,
        categories: MutableMapping[Hashable, Tuple[Union[int, Sequence], Sequence]],
    ):
        super().__init__(env)

        self._env = env
        self.__cache_args = categories
        self._observation_space = None

        wrapped_observation_space = env.observation_space
        if not isinstance(wrapped_observation_space, spaces.Dict):
            # HACK: hacky part to avoid dynamic observation space handling
            if isinstance(wrapped_observation_space, spaces.Discrete):
                self._initialized = False
                return
            raise ValueError(
                f"FilterDictObservation is only usable with dict observations, "
                f"environment observation space is {type(wrapped_observation_space)}"
            )

        # HACK: I am so soryy about this. Later transfer this into more elegant code.
        self.init()

    def init(self):
        if self._initialized:
            return

        categories = self.__cache_args
        wrapped_observation_space = self._env.observation_space
        if not isinstance(wrapped_observation_space, spaces.Dict):
            raise ValueError(
                f"FilterDictObservation is only usable with dict observations, "
                f"environment observation space is {type(wrapped_observation_space)}"
            )

        observation_keys = get_space_keys(wrapped_observation_space)
        cate_keys = get_keys(categories)

        missing_keys = get_missing_keys(observation_keys, cate_keys)
        if missing_keys:
            raise ValueError(
                "All the filter_keys must be included in the original observation space.\n"
                f"Category keys: {cate_keys}\n"
                f"Observation keys: {observation_keys}\n"
                f"Missing keys: {missing_keys}"
            )

        categories_shape = nested_apply(
            categories,
            lambda pair: (
                *pair[1],
                len(pair[0]) if isinstance(pair[0], Sequence) else pair[0],
            ),
            True,
        )

        self.observation_space = filter_apply_space(
            wrapped_observation_space, self._make_onehot, categories_shape
        )

        self.__onehotifiers = nested_apply(
            categories, self._onehotifier_maker, copy=True
        )
        self.__cate_keys = cate_keys
        self.__categories = categories
        self.__categories_shape = categories_shape

        self._initialized = True

    def observation(self, observation):
        return filter_apply(observation, self.__onehotifiers)

    def _make_onehot(
        self,
        shape,
        sample_dim=-1,
    ):
        return Onehot(shape, sample_dim)

    def _onehotifier_maker(self, args):
        category, shape = args
        if isinstance(category, int):

            def onehot(obs):
                result = np.zeros([*shape, category])
                assert obs.shape == result.shape[:-1]
                with np.nditer(obs, op_flags=["readonly"], flags=["multi_index"]) as it:
                    for x in it:
                        index = (
                            *(it.multi_index),
                            x,
                        )
                        result[index] = 1
                return result

        elif isinstance(category, list):

            def onehot(obs):
                result = np.zeros([*shape, category])
                assert obs.shape == result.shape[:-1]
                with np.nditer(obs, op_flags=["readonly"], flags=["multi_index"]) as it:
                    for x in it:
                        index = (
                            *(it.multi_index),
                            category.index(x),
                        )
                        result[index] = 1
                return result

        else:
            raise NotImplemented("Hasn't implement more complex map for onehot encode.")
        return onehot
