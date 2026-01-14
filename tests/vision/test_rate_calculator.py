"""Tests for RateCalculator."""

import pytest


class TestRateCalculator:
    """Tests for RateCalculator."""

    def test_rate_calculation_accuracy(self):
        """Rate calculated correctly from known stroke times."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0)

        # Add strokes at exactly 1 per second = 60/min
        for i in range(10):
            calc.add_stroke(float(i))

        rate = calc.get_rate(current_time=10.0)

        # Should be approximately 60 strokes/min
        assert 58 <= rate <= 62

    def test_rolling_window_excludes_old_strokes(self):
        """Strokes outside window not counted in rate."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=5.0)

        # Add strokes from time 0 to 20 (every 1 second)
        for i in range(21):
            calc.add_stroke(float(i))

        # At time 20, only strokes from 15-20 should count (6 strokes)
        rate = calc.get_rate(current_time=20.0)

        # 6 strokes spanning 5 seconds: rate = (6-1)/5 * 60 = 60 strokes/min
        assert 58 <= rate <= 62

    def test_rate_zero_with_no_strokes(self):
        """Returns 0 when no strokes recorded."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator()

        rate = calc.get_rate(current_time=10.0)

        assert rate == 0.0

    def test_rate_with_single_stroke(self):
        """Handles edge case of single stroke in window."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0)
        calc.add_stroke(5.0)

        rate = calc.get_rate(current_time=10.0)

        # With single stroke, can't calculate rate meaningfully
        assert rate == 0.0

    def test_stroke_count_cumulative(self):
        """Count includes all strokes, not just window."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=5.0)

        # Add strokes over longer period than window
        for i in range(100):
            calc.add_stroke(float(i))

        assert calc.get_stroke_count() == 100

    def test_reset_clears_history(self):
        """Reset clears all strokes."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator()

        for i in range(10):
            calc.add_stroke(float(i))

        assert calc.get_stroke_count() == 10

        calc.reset()

        assert calc.get_stroke_count() == 0
        assert calc.get_rate(current_time=10.0) == 0.0

    @pytest.mark.parametrize("expected_rate", [30, 45, 60, 75, 90])
    def test_various_rates(self, expected_rate: int):
        """Accurately calculates various stroke rates."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0)

        # Add strokes at the expected rate
        interval = 60.0 / expected_rate  # seconds between strokes
        for i in range(20):
            calc.add_stroke(i * interval)

        current_time = 19 * interval
        rate = calc.get_rate(current_time=current_time)

        # Allow +/- 5% tolerance
        tolerance = expected_rate * 0.05
        assert abs(rate - expected_rate) <= tolerance

    def test_rate_adapts_to_changing_pace(self):
        """Rate updates as swimmer changes pace."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=10.0)

        # Start slow (30 strokes/min = 2s interval)
        for i in range(6):
            calc.add_stroke(i * 2.0)  # 0, 2, 4, 6, 8, 10

        rate_slow = calc.get_rate(current_time=10.0)
        assert 28 <= rate_slow <= 32

        # Speed up (60 strokes/min = 1s interval)
        for i in range(10):
            calc.add_stroke(11.0 + i * 1.0)  # 11, 12, ..., 20

        rate_fast = calc.get_rate(current_time=20.0)
        # Window now contains mostly fast strokes
        assert rate_fast > rate_slow

    def test_rate_with_irregular_intervals(self):
        """Handles irregular stroke intervals."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0)

        # Irregular intervals
        stroke_times = [0.0, 0.8, 2.1, 2.9, 4.2, 5.0, 6.1, 7.0, 8.2, 9.0]
        for t in stroke_times:
            calc.add_stroke(t)

        rate = calc.get_rate(current_time=9.0)

        # Should calculate rate based on actual strokes in window
        # 10 strokes in 9 seconds ~= 66.7 strokes/min
        assert 60 <= rate <= 72

    def test_rate_history_recorded(self):
        """Rate samples recorded at regular intervals."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0, sample_interval=5.0)

        # Add strokes at 60/min and call get_rate at intervals
        for i in range(30):  # 30 seconds
            calc.add_stroke(float(i))
            calc.get_rate(current_time=float(i))

        history = calc.get_rate_history()

        # At 5s intervals over 30s, should have ~6 samples
        assert len(history) >= 5

    def test_rate_history_max_size(self):
        """Old rate samples discarded when history full."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(
            window_seconds=15.0,
            history_max_samples=5,
            sample_interval=1.0,
        )

        # Add many rate samples
        for i in range(20):
            calc.add_stroke(float(i))
            calc.get_rate(current_time=float(i))

        history = calc.get_rate_history()

        # Should be limited to max_samples
        assert len(history) <= 5

    def test_rate_history_get_last_n(self):
        """Can get last N rate samples."""
        from src.vision.rate_calculator import RateCalculator

        calc = RateCalculator(window_seconds=15.0, sample_interval=2.0)

        # Add strokes and trigger rate sampling
        for i in range(20):
            calc.add_stroke(float(i))
            calc.get_rate(current_time=float(i))

        # Get last 3 samples
        last_three = calc.get_rate_history(last_n=3)
        all_history = calc.get_rate_history()

        assert len(last_three) == 3
        assert last_three == all_history[-3:]

    def test_rate_history_contains_rate_samples(self):
        """Rate history contains RateSample objects with timestamp and rate."""
        from src.vision.rate_calculator import RateCalculator, RateSample

        calc = RateCalculator(window_seconds=15.0, sample_interval=5.0)

        # Add strokes at 60/min
        for i in range(15):
            calc.add_stroke(float(i))
        calc.get_rate(current_time=15.0)

        history = calc.get_rate_history()

        assert len(history) > 0
        sample = history[0]
        assert isinstance(sample, RateSample)
        assert hasattr(sample, "timestamp")
        assert hasattr(sample, "rate")
        assert sample.rate >= 0
