from __future__ import annotations
from copy import copy, deepcopy
import numbers


def NONCE():
    return


def NONCE1(x):
    return None


def ID1(x):
    return x


class SpikeQueue:
    def __init__(self, spikes=None):
        if spikes is None:
            self.spikes = {}
        elif isinstance(spikes, dict):
            self.spikes = spikes
        elif isinstance(spikes, list):
            self.spikes = {}
            self.add_spikes(spikes)
        else:
            msg = f"Cannot initialize {self} with {spikes} of type {type(spikes)}"
            raise ValueError(msg)

        self.t = 0

    def __getitem__(self, key) -> float:
        if isinstance(key, int):
            return self.spikes.get(key + self.t, 0.0)
        elif isinstance(key, slice):
            return [self.spikes.get(i + self.t, 0.0) for i in range(0, key.stop)[key]]
        else:
            return self.spikes.get(key, 0.0)

    def __setitem__(self, time, value):
        if isinstance(time, int):
            self.add_spike(value, time + self.t)
        elif isinstance(time, slice):
            for i in range(0, time.stop)[time]:
                self.spikes[i + self.t] = value[i]
        else:
            self.spikes[time + self.t] = value

    def add_spike(self, value: float, time: int = 0):
        if time < 0:
            msg = f"Cannot queue spike {time} time steps in the past to {self}"
            raise ValueError(msg)
        time += self.t
        if time in self.spikes:
            self.spikes[time] += value
        else:
            self.spikes[time] = value

    def add_spikes(self, spikes: list[tuple[float, int]] | dict[float, int]):
        if isinstance(spikes, dict):
            spikes = spikes.items()
        for value, time in spikes:
            self.add_spike(value, time)

    def __delitem__(self, key):
        if isinstance(key, int):
            del self.spikes[key + self.t]
        elif isinstance(key, slice):
            for i in range(0, key.stop)[key]:
                if i + self.t in self.spikes:
                    del self.spikes[i + self.t]
        else:
            del self.spikes[key]

    def __len__(self):
        return len(self.spikes)

    def __iter__(self):
        return iter(self.spikes)

    def __repr__(self):
        return f"{self.__class__.__name__} at {id(self):x} with {len(self)} spikes"

    def __contains__(self, key):
        return key + self.t in self.spikes

    def __eq__(self, value):
        return self.spikes == value

    def copy(self):
        return copy(self)

    def __add__(self, value):
        if isinstance(value, (SpikeQueue, dict, list)):
            new = self.copy()
            new.add_spikes(value.spikes if isinstance(value, SpikeQueue) else value)
            return new
        else:
            msg = f"Cannot add {value} of type {type(value)} to {self}"
            raise ValueError(msg)

    def __iadd__(self, value):
        if isinstance(value, (SpikeQueue, dict, list)):
            self.add_spikes(value.spikes if isinstance(value, SpikeQueue) else value)
            return self
        else:
            msg = f"Cannot add {value} of type {type(value)} to {self}"
            raise ValueError(msg)

    def step(self, dt: int = 1, delete: bool = True):
        if dt == 0:
            return
        if dt == 1:
            if delete and self.t in self.spikes:
                del self.spikes[self.t]
            self.t += 1
        else:
            if delete:
                del self[self.t : self.t + dt]
            self.t += dt

    @property
    def current(self):
        return self.spikes.get(self.t, 0.0)

    def __call__(self, dt: int = 1, delete: bool = True):
        temp = self[0:dt]
        self.step(dt, delete)
        return temp

    def append(self, value):
        if isinstance(value, (tuple, list)):
            self.add_spike(*value)
        elif isinstance(value, numbers.Real):
            self.add_spike(float(value), 0)
        else:
            msg = f"Cannot append {value} of type {type(value)} to {self}"
            raise ValueError(msg)
