"""Tests for smoothing algorithms"""
import pytest
import time
import numpy as np


def test_one_euro_first_value():
    from smoothing import OneEuroFilter
    f = OneEuroFilter()
    assert f.filter(10.0) == 10.0


def test_one_euro_jitter_reduction():
    from smoothing import OneEuroFilter
    f = OneEuroFilter(freq=30, mincutoff=0.1, beta=0.001)
    values = [10.0, 10.2, 9.8, 10.1, 9.9, 10.0]
    results = [f.filter(v, time.time() + i * 0.033) for i, v in enumerate(values)]
    assert np.var(results) <= np.var(values)


def test_one_euro_reset():
    from smoothing import OneEuroFilter
    f = OneEuroFilter()
    f.filter(100.0)
    f.filter(200.0)
    f.reset()
    assert f.filter(50.0) == 50.0


def test_one_euro_large_jump():
    from smoothing import OneEuroFilter
    f = OneEuroFilter(beta=0.1)
    base = time.time()
    for i in range(3):
        f.filter(5.0, base + i * 0.033)
    for i in range(5):
        result = f.filter(15.0, base + (3 + i) * 0.033)
    assert abs(result - 15.0) < 3.0  # Should converge


def test_ema_first_value():
    from smoothing import EMAFilter
    assert EMAFilter(alpha=0.3).filter(42.0) == 42.0


def test_ema_smoothing():
    from smoothing import EMAFilter
    f = EMAFilter(alpha=0.1)
    results = []
    for i in range(10):
        results.append(f.filter(10.0 if i < 5 else 20.0))
    assert results[6] > results[5]
    assert results[9] < 20.0


def test_ema_reset():
    from smoothing import EMAFilter
    f = EMAFilter(alpha=0.5)
    f.filter(100.0)
    f.reset()
    assert f.filter(50.0) == 50.0


def test_point_smoother_one_euro():
    from smoothing import PointSmoother
    s = PointSmoother('one_euro', freq=30, mincutoff=1.0)
    assert s.filter((0.5, 0.3)) == (0.5, 0.3)


def test_point_smoother_ema():
    from smoothing import PointSmoother
    s = PointSmoother('ema', alpha=0.3)
    assert s.filter((0.5, 0.3)) == (0.5, 0.3)


def test_point_smoother_2d_smoothing():
    from smoothing import PointSmoother
    s = PointSmoother('ema', alpha=0.1)
    points = [(1.0, 1.0), (1.1, 0.9), (0.9, 1.1), (1.05, 0.95)]
    results = [s.filter(p) for p in points]
    assert np.var([r[0] for r in results]) <= np.var([p[0] for p in points])


def test_point_smoother_reset():
    from smoothing import PointSmoother
    s = PointSmoother('one_euro')
    s.filter((1.0, 1.0))
    s.reset()
    r = s.filter((0.5, 0.8))
    assert abs(r[0] - 0.5) < 1e-6


def test_invalid_smoother_type():
    from smoothing import PointSmoother
    with pytest.raises(ValueError):
        PointSmoother('invalid')


def test_low_pass_filter():
    from smoothing import LowPassFilter
    f = LowPassFilter(alpha=0.5)
    assert f.filter(10.0) == 10.0
    r = f.filter(20.0)
    assert 10.0 < r < 20.0
    f.reset()
    assert f.filter(5.0) == 5.0


def test_alpha_clamping():
    from smoothing import LowPassFilter, EMAFilter
    assert LowPassFilter(alpha=2.0).alpha == 1.0
    assert LowPassFilter(alpha=-0.5).alpha == 0.0
    assert EMAFilter(alpha=1.5).alpha == 1.0
    assert EMAFilter(alpha=-0.1).alpha == 0.0


def test_smoothing_performance():
    """1000 filter calls should complete in <100ms."""
    from smoothing import OneEuroFilter
    f = OneEuroFilter()
    start = time.time()
    base = start
    for i in range(1000):
        f.filter(float(i), base + i * 0.001)
    elapsed = time.time() - start
    assert elapsed < 0.1
