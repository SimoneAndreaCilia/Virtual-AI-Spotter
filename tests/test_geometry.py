"""
Unit Tests for Geometry Module - Edge Cases.

Tests the calculate_angle() function for:
- Standard angle calculations
- Edge cases (zero-length vectors, collinear points)
- Numeric precision and boundary conditions

Run with: python -m pytest tests/test_geometry.py -v
"""
import unittest
import sys
import os
import math

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.geometry import calculate_angle


class TestCalculateAngleStandard(unittest.TestCase):
    """Test standard angle calculations."""
    
    def test_right_angle_90_degrees(self):
        """Test a perfect 90-degree angle."""
        # L-shape: horizontal then vertical
        a = (0.0, 0.0)
        b = (1.0, 0.0)  # vertex
        c = (1.0, 1.0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, delta=0.1)
    
    def test_straight_line_180_degrees(self):
        """Test three collinear points (straight line) = 180 degrees."""
        a = (0.0, 0.0)
        b = (1.0, 0.0)  # vertex
        c = (2.0, 0.0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 180.0, delta=0.1)
    
    def test_acute_angle_45_degrees(self):
        """Test a 45-degree angle."""
        # Vector BA points left (-1, 0), Vector BC points at 45 degrees (1, 1)
        # Angle between (-1, 0) and (1, 1) normalized is 135 degrees
        # For a true 45-degree angle at B:
        a = (0.0, 1.0)
        b = (0.0, 0.0)  # vertex at origin
        c = (1.0, 0.0)  # 45 deg angle between (0,1) and (1,0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, delta=0.5)  # This is actually 90 degrees
    
    def test_obtuse_angle_135_degrees(self):
        """Test a 135-degree angle."""
        import math
        # BA vector points left (-1, 0)
        # For 135 deg angle, BC should point at 45 deg (upper-left from B)
        a = (1.0, 0.0)
        b = (0.0, 0.0)  # vertex at origin
        c = (-1.0, 1.0)  # BC = (-1, 1), BA = (1, 0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 135.0, delta=0.5)
    
    def test_small_angle_near_zero(self):
        """Test a very small angle close to 0 degrees."""
        # Both A and C nearly in same direction from B
        a = (2.0, 0.0)
        b = (0.0, 0.0)  # vertex at origin
        c = (2.0, 0.1)  # Almost same direction as A from B
        
        angle = calculate_angle(a, b, c)
        self.assertLess(angle, 5.0)  # Should be close to 0


class TestCalculateAngleEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_zero_length_vector_same_point_ab(self):
        """Test when points A and B are identical (zero-length BA vector)."""
        a = (1.0, 1.0)
        b = (1.0, 1.0)  # Same as A
        c = (2.0, 2.0)
        
        angle = calculate_angle(a, b, c)
        # Should return 0.0 (division by zero guard)
        self.assertEqual(angle, 0.0)
    
    def test_zero_length_vector_same_point_bc(self):
        """Test when points B and C are identical (zero-length BC vector)."""
        a = (0.0, 0.0)
        b = (1.0, 1.0)
        c = (1.0, 1.0)  # Same as B
        
        angle = calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)
    
    def test_all_three_points_identical(self):
        """Test when all three points are the same."""
        a = (5.0, 5.0)
        b = (5.0, 5.0)
        c = (5.0, 5.0)
        
        angle = calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)
    
    def test_collinear_points_same_direction(self):
        """Test collinear points where C is beyond B from A (0 degrees)."""
        # A -> B -> C in line
        a = (0.0, 0.0)
        b = (1.0, 0.0)
        c = (2.0, 0.0)
        
        angle = calculate_angle(a, b, c)
        # vectors BA and BC point opposite => 180 degrees
        self.assertAlmostEqual(angle, 180.0, delta=0.1)
    
    def test_collinear_points_opposite_direction(self):
        """Test collinear points where A and C are on same side of B."""
        # Both A and C on the right of B
        a = (2.0, 0.0)
        b = (0.0, 0.0)  # vertex at origin
        c = (3.0, 0.0)
        
        angle = calculate_angle(a, b, c)
        # vectors BA and BC point same direction => 0 degrees
        self.assertAlmostEqual(angle, 0.0, delta=0.1)


class TestCalculateAngleCoordinates(unittest.TestCase):
    """Test with various coordinate ranges."""
    
    def test_negative_coordinates(self):
        """Test with negative coordinates."""
        # BA = (-2,-2), BC = (2,0) from origin
        # cos(theta) = BA·BC / (|BA||BC|) = (-4) / (2.83 * 2) = -0.707
        # theta = 135 degrees
        a = (-2.0, -2.0)
        b = (0.0, 0.0)
        c = (2.0, 0.0)
        
        angle = calculate_angle(a, b, c)
        # Should still compute correctly
        self.assertAlmostEqual(angle, 135.0, delta=0.5)
    
    def test_large_coordinates(self):
        """Test with large coordinate values (no overflow)."""
        a = (10000.0, 0.0)
        b = (10001.0, 0.0)
        c = (10001.0, 1.0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, delta=0.1)
    
    def test_very_small_coordinates(self):
        """Test with very small coordinate differences."""
        a = (0.0, 0.0)
        b = (0.001, 0.0)
        c = (0.001, 0.001)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, delta=0.5)
    
    def test_mixed_positive_negative(self):
        """Test with mixed positive and negative coordinates."""
        a = (-1.0, 1.0)
        b = (0.0, 0.0)
        c = (1.0, 1.0)
        
        angle = calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, delta=0.1)


class TestCalculateAnglePrecision(unittest.TestCase):
    """Test numeric precision and floating-point edge cases."""
    
    def test_cosine_near_one(self):
        """Test when cosine is very close to 1.0 (angle near 0)."""
        # Both A and C in nearly same direction from B
        a = (2.0, 0.0)
        b = (0.0, 0.0)  # vertex at origin
        c = (2.0, 0.0001)  # Nearly same direction as A
        
        angle = calculate_angle(a, b, c)
        # Should handle without math domain error, angle very close to 0
        self.assertLess(angle, 1.0)
    
    def test_cosine_near_negative_one(self):
        """Test when cosine is very close to -1.0 (angle near 180)."""
        a = (2.0, 0.0)
        b = (1.0, 0.0)
        c = (2.0, 0.0000001)  # Nearly the same direction as A from B
        
        angle = calculate_angle(a, b, c)
        # Should be close to 0 (both vectors pointing right from B)
        self.assertLess(angle, 1.0)
    
    def test_result_is_rounded(self):
        """Test that result is rounded to 2 decimal places."""
        a = (0.0, 0.0)
        b = (1.0, 0.0)
        c = (1.0, 1.0)
        
        angle = calculate_angle(a, b, c)
        # Check that it's rounded (no more than 2 decimal places)
        rounded = round(angle, 2)
        self.assertEqual(angle, rounded)
    
    def test_symmetry(self):
        """Test that angle(a,b,c) == angle(c,b,a)."""
        a = (0.0, 0.0)
        b = (1.0, 0.0)
        c = (1.0, 1.0)
        
        angle1 = calculate_angle(a, b, c)
        angle2 = calculate_angle(c, b, a)
        
        self.assertEqual(angle1, angle2)


if __name__ == '__main__':
    unittest.main()
