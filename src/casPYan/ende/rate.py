from __future__ import annotations

from functools import cache, cached_property
import math

# typing
from ..node import Node


class RateEncoder:
    int8 = True

    def __init__(self,
        interval: int,
        domain: tuple[float, float],
        # target: Node = None,
    ):
        self.interval = interval
        self.domain = domain
        # self.target = target

    def clear_cached_properties(self):
        del self.k
        del self.d

    @cached_property
    def amplitude(self):
        return 255 if self.int8 else 1.0

    @cached_property
    def k(self):
        return self.d / self.interval

    @cached_property
    def d(self):
        lmin, lmax = self.domain
        return abs(lmax - lmin)

    def discretize_input(self, x: float):
        x = x - min(self.domain)
        x /= self.k
        return math.ceil(x)

    def get_spikes(self, x: float):
        upto = self.discretize_input(x)
        return [(self.amplitude, delay) for delay in range(upto)]


class RateDecoder:
    def __init__(self,
        interval: int,
        domain: tuple[float, float],
        min_amplitude=1,
        # target: Node = None,
    ):
        self.interval = interval
        self.domain = domain
        self.min_amplitude = min_amplitude
        # self.target = target

    @cached_property
    def k(self):
        return self.d / self.interval

    @cached_property
    def d(self):
        lmin, lmax = self.domain
        return lmax - lmin

    def decode(self, history: list[float]):
        n = sum([1 for a in history[-self.interval:] if a >= self.min_amplitude])
        return self.domain[0] + n * self.k
