"""
Cursor smoothing algorithms for HandControl
Implements One Euro Filter and Exponential Moving Average (EMA) smoothing
"""
import time
import math
from typing import Optional, Tuple, Any
from abc import ABC, abstractmethod

class Smoother(ABC):
    """Abstract base class for smoothing algorithms"""
    
    @abstractmethod
    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        """
        Apply smoothing filter to a value
        
        Args:
            value: Input value to smooth
            timestamp: Optional timestamp (current time used if None)
            
        Returns:
            Smoothed value
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset the filter state"""
        pass

class LowPassFilter:
    """Simple low-pass filter used by One Euro Filter"""
    
    def __init__(self, alpha: float = 0.1):
        """
        Initialize low-pass filter
        
        Args:
            alpha: Smoothing factor (0 = no smoothing, 1 = no filtering)
        """
        self.alpha = alpha
        self.prev_output: Optional[float] = None
        self.set_alpha(alpha)
    
    def set_alpha(self, alpha: float) -> None:
        """Set smoothing factor"""
        self.alpha = max(0.0, min(1.0, alpha))  # Clamp between 0 and 1
    
    def filter(self, value: float) -> float:
        """Apply low-pass filter"""
        if self.prev_output is None:
            self.prev_output = value
        else:
            self.prev_output = self.alpha * value + (1.0 - self.alpha) * self.prev_output
        
        return self.prev_output
    
    def reset(self) -> None:
        """Reset filter state"""
        self.prev_output = None

class OneEuroFilter(Smoother):
    """
    One Euro Filter - adapts smoothing based on movement speed
    Great for cursor control as it provides stability when stationary
    and responsiveness when moving quickly
    """
    
    def __init__(self, 
                 freq: float = 30.0,
                 mincutoff: float = 1.0,
                 beta: float = 0.007,
                 dcutoff: float = 1.0):
        """
        Initialize One Euro Filter
        
        Args:
            freq: Expected update frequency (Hz)
            mincutoff: Minimum cutoff frequency (stability when stationary)
            beta: Speed coefficient (how much speed affects smoothing) 
            dcutoff: Cutoff frequency for speed calculation
        """
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        
        # Filter components
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        
        # State
        self.prev_time: Optional[float] = None
        self.prev_value: Optional[float] = None
        
        print(f"OneEuroFilter initialized (freq={freq}, mincutoff={mincutoff}, beta={beta})")
    
    def _get_alpha(self, cutoff: float, dt: float) -> float:
        """Calculate alpha for given cutoff frequency and time delta"""
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
    
    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        """Apply One Euro Filter"""
        if timestamp is None:
            timestamp = time.time()
        
        # First value - no smoothing possible
        if self.prev_time is None or self.prev_value is None:
            self.prev_time = timestamp
            self.prev_value = value
            return value
        
        # Calculate time delta
        dt = timestamp - self.prev_time
        if dt <= 0:
            return value  # Invalid time delta
        
        # Estimate speed (derivative)
        dx = (value - self.prev_value) / dt
        
        # Smooth the speed estimate
        self.dx_filter.set_alpha(self._get_alpha(self.dcutoff, dt))
        dx_smooth = self.dx_filter.filter(dx)
        
        # Calculate adaptive cutoff frequency based on speed
        cutoff = self.mincutoff + self.beta * abs(dx_smooth)
        
        # Apply smoothing with adaptive cutoff
        self.x_filter.set_alpha(self._get_alpha(cutoff, dt))
        result = self.x_filter.filter(value)
        
        # Update state
        self.prev_time = timestamp
        self.prev_value = result
        
        return result
    
    def reset(self) -> None:
        """Reset filter state"""
        self.x_filter.reset()
        self.dx_filter.reset()
        self.prev_time = None
        self.prev_value = None

class EMAFilter(Smoother):
    """
    Exponential Moving Average (EMA) Filter
    Simple smoothing with fixed alpha
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize EMA filter
        
        Args:
            alpha: Smoothing factor (0 = maximum smoothing, 1 = no smoothing)
        """
        self.alpha = max(0.0, min(1.0, alpha))
        self.prev_value: Optional[float] = None
        
        print(f"EMAFilter initialized (alpha={self.alpha})")
    
    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        """Apply EMA smoothing"""
        if self.prev_value is None:
            self.prev_value = value
        else:
            self.prev_value = self.alpha * value + (1.0 - self.alpha) * self.prev_value
        
        return self.prev_value
    
    def reset(self) -> None:
        """Reset filter state"""
        self.prev_value = None

class PointSmoother:
    """
    2D point smoother using separate X and Y filters
    Handles cursor position smoothing
    """
    
    def __init__(self, smoother_type: str = 'one_euro', **kwargs):
        """
        Initialize point smoother
        
        Args:
            smoother_type: 'one_euro' or 'ema'
            **kwargs: Parameters passed to the underlying smoother
        """
        self.smoother_type = smoother_type
        
        if smoother_type == 'one_euro':
            self.x_smoother = OneEuroFilter(**kwargs)
            self.y_smoother = OneEuroFilter(**kwargs)
        elif smoother_type == 'ema':
            self.x_smoother = EMAFilter(**kwargs)
            self.y_smoother = EMAFilter(**kwargs)
        else:
            raise ValueError(f"Unknown smoother type: {smoother_type}")
        
        print(f"PointSmoother initialized with {smoother_type}")
    
    def filter(self, point: Tuple[float, float], timestamp: Optional[float] = None) -> Tuple[float, float]:
        """
        Smooth a 2D point
        
        Args:
            point: (x, y) coordinates to smooth
            timestamp: Optional timestamp
            
        Returns:
            Smoothed (x, y) coordinates
        """
        x, y = point
        
        smooth_x = self.x_smoother.filter(x, timestamp)
        smooth_y = self.y_smoother.filter(y, timestamp)
        
        return (smooth_x, smooth_y)
    
    def reset(self) -> None:
        """Reset both smoothers"""
        self.x_smoother.reset()
        self.y_smoother.reset()

def test_smoothing() -> bool:
    """Test smoothing algorithms with synthetic data"""
    import numpy as np
    import matplotlib.pyplot as plt
    
    print("Testing smoothing algorithms...")
    
    # Generate test signal: sine wave with noise
    t = np.linspace(0, 2, 200)  # 2 seconds at ~100Hz
    clean_signal = np.sin(2 * np.pi * t)
    noise = np.random.normal(0, 0.2, len(t))
    noisy_signal = clean_signal + noise
    
    # Test One Euro Filter
    one_euro = OneEuroFilter(freq=100, mincutoff=1.0, beta=0.01)
    one_euro_result = []
    
    for i, value in enumerate(noisy_signal):
        filtered = one_euro.filter(value, t[i])
        one_euro_result.append(filtered)
    
    # Test EMA Filter
    ema = EMAFilter(alpha=0.1)
    ema_result = []
    
    for value in noisy_signal:
        filtered = ema.filter(value)
        ema_result.append(filtered)
    
    # Test Point Smoother
    point_smoother = PointSmoother('one_euro', freq=100, mincutoff=1.0, beta=0.01)
    
    # Create 2D trajectory
    points = [(np.sin(2 * np.pi * ti), np.cos(2 * np.pi * ti)) for ti in t]
    noise_2d = [(np.random.normal(0, 0.1), np.random.normal(0, 0.1)) for _ in t]
    noisy_points = [(p[0] + n[0], p[1] + n[1]) for p, n in zip(points, noise_2d)]
    
    smoothed_points = []
    for i, point in enumerate(noisy_points):
        smoothed = point_smoother.filter(point, t[i])
        smoothed_points.append(smoothed)
    
    # Calculate metrics
    one_euro_error = np.mean((np.array(one_euro_result) - clean_signal) ** 2)
    ema_error = np.mean((np.array(ema_result) - clean_signal) ** 2)
    
    print(f"One Euro Filter MSE: {one_euro_error:.6f}")
    print(f"EMA Filter MSE: {ema_error:.6f}")
    
    # Test first value passthrough
    one_euro_fresh = OneEuroFilter()
    first_value = 42.0
    result = one_euro_fresh.filter(first_value)
    
    if abs(result - first_value) < 1e-6:
        print("✅ First value passthrough test PASSED")
        first_test_passed = True
    else:
        print(f"❌ First value passthrough test FAILED: {result} != {first_value}")
        first_test_passed = False
    
    # Test jitter reduction
    jittery_values = [10.0, 10.2, 9.8, 10.1, 9.9, 10.0]
    smoother = OneEuroFilter(mincutoff=0.1)  # Low cutoff for smoothing
    
    smoothed_values = []
    for value in jittery_values:
        smoothed_values.append(smoother.filter(value))
    
    # Check that smoothed values have less variance
    original_var = np.var(jittery_values)
    smoothed_var = np.var(smoothed_values)
    
    if smoothed_var < original_var:
        print("✅ Jitter reduction test PASSED")
        jitter_test_passed = True
    else:
        print(f"❌ Jitter reduction test FAILED: {smoothed_var} >= {original_var}")
        jitter_test_passed = False
    
    # Test large jump tracking
    jump_values = [5.0, 5.0, 5.0, 15.0, 15.0, 15.0]  # Large jump
    jump_smoother = OneEuroFilter(beta=0.1)  # Higher beta for responsiveness
    
    jump_results = []
    for value in jump_values:
        jump_results.append(jump_smoother.filter(value))
    
    # Should converge to new value within reasonable time
    final_values = jump_results[-2:]  # Last two values
    target_value = jump_values[-1]
    
    converged = all(abs(v - target_value) < 2.0 for v in final_values)
    
    if converged:
        print("✅ Large jump tracking test PASSED")
        jump_test_passed = True
    else:
        print(f"❌ Large jump tracking test FAILED: {final_values} not close to {target_value}")
        jump_test_passed = False
    
    # Test reset functionality
    reset_smoother = OneEuroFilter()
    reset_smoother.filter(100.0)  # Process a value
    reset_smoother.reset()
    reset_result = reset_smoother.filter(5.0)  # Should pass through
    
    if abs(reset_result - 5.0) < 1e-6:
        print("✅ Reset test PASSED")
        reset_test_passed = True
    else:
        print(f"❌ Reset test FAILED: {reset_result} != 5.0")
        reset_test_passed = False
    
    all_tests_passed = all([
        first_test_passed,
        jitter_test_passed, 
        jump_test_passed,
        reset_test_passed
    ])
    
    if all_tests_passed:
        print("🎉 All smoothing tests PASSED")
    else:
        print("❌ Some smoothing tests FAILED")
    
    return all_tests_passed

if __name__ == "__main__":
    test_smoothing()