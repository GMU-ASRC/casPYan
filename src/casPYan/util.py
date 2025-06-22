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
            pass

        self.spikes = spikes or {}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.spikes.get(key, [])
        elif isinstance(key, slice):
            return [self.spikes.get(i, []) for i in range(0, key.stop)[key]]
        else:
            return self.spikes.get(key, [])

    def __setitem__(self, time, value):
        if isinstance(time, int):
            self.add_spike(value, time)
        elif isinstance(time, slice):
            for i in range(0, time.stop)[time]:
                self.spikes[i] = value[i]
        else:
            self.spikes[time] = value

    def add_spike(self, value: float, time: int = 0):
        if time < 0:
            msg = f"Cannot queue spike {time} time steps in the past to {self}"
            raise ValueError(msg)
        if time in self.spikes:
            self.spikes[time].append(value)
        else:
            self.spikes[time] = [value]

    def add_spikes(self, spikes: list[tuple[float, int]] | dict[float, int]):
        if isinstance(spikes, dict):
            spikes = spikes.items()
        for value, time in spikes:
            self.add_spike(value, time)

    def __delitem__(self, key):
        if isinstance(key, int):
            del self.spikes[key]
        elif isinstance(key, slice):
            for i in range(0, key.stop)[key]:
                del self.spikes[i]
        else:
            del self.spikes[key]

    def __len__(self):
        return len(self.spikes)

    def __iter__(self):
        return iter(self.spikes)

    def __repr__(self):
        return f"{self.__class__.__name__} at {id(self):x} with {len(self)} spikes"

    def __contains__(self, key):
        return key in self.spikes

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
            raise ValueError(f"Cannot add {value} of type {type(value)} to {self}")

    def __iadd__(self, value):
        if isinstance(value, (SpikeQueue, dict, list)):
            self.add_spikes(value.spikes if isinstance(value, SpikeQueue) else value)
            return self
        else:
            raise ValueError(f"Cannot add {value} of type {type(value)} to {self}")

    def step(self, dt: int = 1, delete: bool = True):
        if dt == 0:
            return
        if dt == 1:
            if 0 in self.spikes and delete:
                del self.spikes[0]
            self.spikes = {k - 1: v for k, v in self.spikes.items()}
        else:
            self.spikes = {k - dt: v for k, v in self.spikes.items() if not delete or (k - dt) >= 0}

    def append(self, value):
        if isinstance(value, (tuple, list)):
            self.add_spike(*value)
        elif isinstance(value, numbers.Real):
            self.add_spike(0, value)
        else:
            raise ValueError(f"Cannot append {value} of type {type(value)} to {self}")
