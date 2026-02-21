"""
Tests for smoothing algorithms
"""
import pytest
import time
import numpy as np

def test_one_euro_filter_initialization():
    """Test One Euro Filter initialization"""
    from smoothing import OneEuroFilter
    
    filter = OneEuroFilter(freq=30, mincutoff=1.0, beta=0.007)
    
    # Test initial state
    result = filter.filter(10.0)
    assert result == 10.0  # First value should pass through

def test_one_euro_filter_smoothing():
    """Test One Euro Filter smoothing behavior"""
    from smoothing import OneEuroFilter
    
    filter = OneEuroFilter(freq=30, mincutoff=0.1, beta=0.001)
    
    # Test jitter reduction
    values = [10.0, 10.2, 9.8, 10.1, 9.9, 10.0]
    results = []
    
    for value in values:
        result = filter.filter(value, time.time())
        results.append(result)
        time.sleep(0.001)  # Small delay for realistic timing
    
    # Results should be smoother than input
    input_variance = np.var(values)
    output_variance = np.var(results)
    assert output_variance <= input_variance

def test_one_euro_filter_reset():
    """Test One Euro Filter reset functionality"""
    from smoothing import OneEuroFilter
    
    filter = OneEuroFilter()
    
    # Process some values
    filter.filter(100.0)
    filter.filter(200.0)
    
    # Reset
    filter.reset()
    
    # Next value should pass through
    result = filter.filter(50.0)
    assert result == 50.0

def test_ema_filter_initialization():
    """Test EMA Filter initialization"""
    from smoothing import EMAFilter
    
    filter = EMAFilter(alpha=0.3)
    
    # First value should pass through
    result = filter.filter(42.0)
    assert result == 42.0

def test_ema_filter_smoothing():
    """Test EMA Filter smoothing behavior"""
    from smoothing import EMAFilter
    
    filter = EMAFilter(alpha=0.1)  # Heavy smoothing
    
    # Test step response
    results = []
    for i in range(10):
        result = filter.filter(10.0 if i < 5 else 20.0)
        results.append(result)
    
    # Should gradually approach new value
    assert results[6] > results[5]  # Should be increasing after step
    assert results[9] < 20.0  # Should not reach final value immediately

def test_ema_filter_reset():
    """Test EMA Filter reset functionality"""
    from smoothing import EMAFilter
    
    filter = EMAFilter(alpha=0.5)
    
    # Process some values
    filter.filter(100.0)
    filter.filter(200.0)
    
    # Reset
    filter.reset()
    
    # Next value should pass through
    result = filter.filter(50.0)
    assert result == 50.0

def test_point_smoother_initialization():
    """Test PointSmoother initialization"""
    from smoothing import PointSmoother
    
    # Test One Euro Point Smoother
    smoother = PointSmoother('one_euro', freq=30, mincutoff=1.0)
    result = smoother.filter((0.5, 0.3))
    assert result == (0.5, 0.3)  # First point should pass through
    
    # Test EMA Point Smoother
    smoother = PointSmoother('ema', alpha=0.3)
    result = smoother.filter((0.5, 0.3))
    assert result == (0.5, 0.3)  # First point should pass through

def test_point_smoother_smoothing():
    """Test PointSmoother 2D smoothing"""
    from smoothing import PointSmoother
    
    smoother = PointSmoother('ema', alpha=0.1)
    
    # Test with noisy points
    points = [(1.0, 1.0), (1.1, 0.9), (0.9, 1.1), (1.05, 0.95)]
    results = []
    
    for point in points:
        result = smoother.filter(point)
        results.append(result)
    
    # Results should be smoother
    x_values = [p[0] for p in points]
    y_values = [p[1] for p in points]
    result_x = [p[0] for p in results]
    result_y = [p[1] for p in results]
    
    assert np.var(result_x) <= np.var(x_values)
    assert np.var(result_y) <= np.var(y_values)

def test_point_smoother_reset():
    """Test PointSmoother reset functionality"""
    from smoothing import PointSmoother
    
    smoother = PointSmoother('one_euro')
    
    # Process some points
    smoother.filter((1.0, 1.0))
    smoother.filter((2.0, 2.0))
    
    # Reset
    smoother.reset()
    
    # Next point should pass through
    result = smoother.filter((0.5, 0.8))
    assert abs(result[0] - 0.5) < 1e-6
    assert abs(result[1] - 0.8) < 1e-6

def test_invalid_smoother_type():
    """Test invalid smoother type handling"""
    from smoothing import PointSmoother
    
    with pytest.raises(ValueError):
        PointSmoother('invalid_type')

def test_low_pass_filter():
    """Test LowPassFilter component"""
    from smoothing import LowPassFilter
    
    lpf = LowPassFilter(alpha=0.5)
    
    # First value should pass through
    result = lpf.filter(10.0)
    assert result == 10.0
    
    # Subsequent values should be filtered
    result = lpf.filter(20.0)
    assert 10.0 < result < 20.0  # Should be between previous and current
    
    # Reset test
    lpf.reset()
    result = lpf.filter(5.0)
    assert result == 5.0

def test_alpha_clamping():
    """Test that alpha values are properly clamped"""
    from smoothing import LowPassFilter, EMAFilter
    
    # Test LowPassFilter alpha clamping
    lpf = LowPassFilter(alpha=2.0)  # > 1.0
    assert lpf.alpha == 1.0
    
    lpf = LowPassFilter(alpha=-0.5)  # < 0.0  
    assert lpf.alpha == 0.0
    
    # Test EMAFilter alpha clamping
    ema = EMAFilter(alpha=1.5)  # > 1.0
    assert ema.alpha == 1.0
    
    ema = EMAFilter(alpha=-0.1)  # < 0.0
    assert ema.alpha == 0.0

def test_smoothing_performance():
    """Test smoothing performance with large datasets"""
    from smoothing import OneEuroFilter, EMAFilter
    
    # Generate test data
    data = np.random.normal(100, 10, 1000)
    
    # Test One Euro Filter
    one_euro = OneEuroFilter()
    start_time = time.time()
    for value in data:
        one_euro.filter(float(value))
    one_euro_time = time.time() - start_time
    
    # Test EMA Filter
    ema = EMAFilter()
    start_time = time.time()
    for value in data:
        ema.filter(float(value))
    ema_time = time.time() - start_time
    
    # Both should complete reasonably quickly
    assert one_euro_time < 1.0  # Should complete in under 1 second
    assert ema_time < 0.1      # EMA should be faster