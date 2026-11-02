"""
Automated Unit Tests for Advanced BMI Calculator.

Covers:
- Standard BMI calculations (A, B, C, D)
- Boundary condition classifications (E)
- Input validation and exception handling (F)
- Database persistence, retrieval, and filtering in a temporary database (G)
- CSV export functionality and empty record handling (H)
"""

import sys
import csv
import unittest
import tempfile
import shutil
from pathlib import Path

# Ensure project root is in python path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bmi_calculator import (
    calculate_bmi,
    get_bmi_category,
    get_category_color,
    validate_inputs,
    export_records_to_csv,
    CATEGORY_COLORS,
)
from database import BMIDatabase


class TestBMICalculation(unittest.TestCase):
    """Test core BMI calculation and formula adherence."""

    def test_case_a_normal_weight(self):
        """Test Case A: Weight 60 kg, height 1.7 m -> BMI 20.76, Normal."""
        bmi = calculate_bmi(60.0, 1.7)
        self.assertEqual(bmi, 20.76)
        category = get_bmi_category(bmi)
        self.assertEqual(category, "Normal")

    def test_case_b_underweight(self):
        """Test Case B: Weight 45 kg, height 1.7 m -> BMI 15.57, Underweight."""
        bmi = calculate_bmi(45.0, 1.7)
        self.assertEqual(bmi, 15.57)
        category = get_bmi_category(bmi)
        self.assertEqual(category, "Underweight")

    def test_case_c_overweight(self):
        """Test Case C: Weight 80 kg, height 1.7 m -> BMI 27.68, Overweight."""
        bmi = calculate_bmi(80.0, 1.7)
        self.assertEqual(bmi, 27.68)
        category = get_bmi_category(bmi)
        self.assertEqual(category, "Overweight")

    def test_case_d_obese(self):
        """Test Case D: Weight 100 kg, height 1.7 m -> BMI 34.60, Obese."""
        bmi = calculate_bmi(100.0, 1.7)
        self.assertEqual(bmi, 34.60)
        category = get_bmi_category(bmi)
        self.assertEqual(category, "Obese")


class TestBMICategoryBoundaries(unittest.TestCase):
    """Test boundary values for all WHO BMI classifications."""

    def test_boundary_18_49_underweight(self):
        """Boundary: 18.49 -> Underweight."""
        self.assertEqual(get_bmi_category(18.49), "Underweight")

    def test_boundary_18_50_normal(self):
        """Boundary: 18.50 -> Normal."""
        self.assertEqual(get_bmi_category(18.50), "Normal")

    def test_boundary_24_99_normal(self):
        """Boundary: 24.99 -> Normal."""
        self.assertEqual(get_bmi_category(24.99), "Normal")

    def test_boundary_25_00_overweight(self):
        """Boundary: 25.00 -> Overweight."""
        self.assertEqual(get_bmi_category(25.00), "Overweight")

    def test_boundary_29_99_overweight(self):
        """Boundary: 29.99 -> Overweight."""
        self.assertEqual(get_bmi_category(29.99), "Overweight")

    def test_boundary_30_00_obese(self):
        """Boundary: 30.00 -> Obese."""
        self.assertEqual(get_bmi_category(30.00), "Obese")

    def test_category_colors_mapping(self):
        """Verify that color mappings are properly assigned for each category."""
        self.assertEqual(get_category_color("Underweight"), CATEGORY_COLORS["Underweight"])
        self.assertEqual(get_category_color("Normal"), CATEGORY_COLORS["Normal"])
        self.assertEqual(get_category_color("Overweight"), CATEGORY_COLORS["Overweight"])
        self.assertEqual(get_category_color("Obese"), CATEGORY_COLORS["Obese"])


class TestInputValidation(unittest.TestCase):
    """Test input validation across numeric, non-numeric, zero, negative, and empty inputs."""

    def test_valid_input_tuple(self):
        """Valid inputs should cleanly return parsed values."""
        username, weight, height = validate_inputs("Alice", "65.5", "1.70")
        self.assertEqual(username, "Alice")
        self.assertEqual(weight, 65.5)
        self.assertEqual(height, 1.70)

    def test_empty_username(self):
        """Empty or whitespace-only username must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("", "60", "1.7")
        self.assertIn("Username cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            validate_inputs("   ", "60", "1.7")
        self.assertIn("Username cannot be empty", str(ctx.exception))

    def test_non_numeric_weight(self):
        """Non-numeric weight input must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "sixty", "1.7")
        self.assertIn("valid numeric number", str(ctx.exception))

    def test_non_numeric_height(self):
        """Non-numeric height input must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "60", "one-point-seven")
        self.assertIn("valid numeric number", str(ctx.exception))

    def test_empty_weight(self):
        """Empty weight must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "", "1.7")
        self.assertIn("Weight cannot be empty", str(ctx.exception))

    def test_empty_height(self):
        """Empty height must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "60", "")
        self.assertIn("Height cannot be empty", str(ctx.exception))

    def test_zero_weight(self):
        """Zero weight must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "0", "1.7")
        self.assertIn("greater than zero", str(ctx.exception))

    def test_zero_height(self):
        """Zero height must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "60", "0")
        self.assertIn("greater than zero", str(ctx.exception))

    def test_negative_weight(self):
        """Negative weight must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "-55", "1.7")
        self.assertIn("greater than zero", str(ctx.exception))

    def test_negative_height(self):
        """Negative height must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_inputs("Bob", "60", "-1.65")
        self.assertIn("greater than zero", str(ctx.exception))

    def test_calculate_bmi_direct_rejection_of_invalid(self):
        """Direct call to calculate_bmi with non-positive values must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_bmi(0, 1.7)
        with self.assertRaises(ValueError):
            calculate_bmi(-10, 1.7)
        with self.assertRaises(ValueError):
            calculate_bmi(60, 0)
        with self.assertRaises(ValueError):
            calculate_bmi(60, -1.7)


class TestDatabaseOperations(unittest.TestCase):
    """Test SQLite database operations using an isolated temporary test database."""

    def setUp(self):
        """Create a temporary directory and test database for isolated testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = Path(self.test_dir) / "test_bmi.db"
        self.db = BMIDatabase(db_path=self.test_db_path)

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_table_creation(self):
        """Verify that bmi_records table is created and accessible."""
        records = self.db.get_records()
        self.assertEqual(records, [])

    def test_save_valid_record(self):
        """Test inserting a valid record and verifying returned ID."""
        record_id = self.db.add_record(
            username="Sarah",
            weight=55.0,
            height=1.65,
            bmi=20.20,
            category="Normal",
            created_at="2026-03-01 10:00:00"
        )
        self.assertIsInstance(record_id, int)
        self.assertGreater(record_id, 0)

    def test_retrieve_saved_history(self):
        """Test inserting multiple records and retrieving them."""
        self.db.add_record("Alice", 60.0, 1.70, 20.76, "Normal", "2026-03-01 09:00:00")
        self.db.add_record("Bob", 85.0, 1.75, 27.76, "Overweight", "2026-03-01 10:00:00")

        records = self.db.get_records(order_by_id_asc=True)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0][1], "Alice")
        self.assertEqual(records[1][1], "Bob")

    def test_filter_by_username(self):
        """Test filtering database records by specific username."""
        self.db.add_record("Alice", 60.0, 1.70, 20.76, "Normal", "2026-03-01 09:00:00")
        self.db.add_record("Bob", 85.0, 1.75, 27.76, "Overweight", "2026-03-01 10:00:00")
        self.db.add_record("Alice", 59.0, 1.70, 20.42, "Normal", "2026-03-02 09:00:00")

        alice_records = self.db.get_records(username="Alice")
        self.assertEqual(len(alice_records), 2)
        for row in alice_records:
            self.assertEqual(row[1], "Alice")

        bob_records = self.db.get_records(username="bob")  # Case-insensitive
        self.assertEqual(len(bob_records), 1)
        self.assertEqual(bob_records[0][1], "Bob")

    def test_empty_history(self):
        """Empty database should safely return an empty list without errors."""
        records = self.db.get_records()
        self.assertEqual(records, [])
        filtered = self.db.get_records(username="NonExistentUser")
        self.assertEqual(filtered, [])

    def test_unique_usernames(self):
        """Test fetching unique usernames list."""
        self.db.add_record("Charlie", 70.0, 1.75, 22.86, "Normal")
        self.db.add_record("Alice", 60.0, 1.70, 20.76, "Normal")
        self.db.add_record("Charlie", 71.0, 1.75, 23.18, "Normal")

        unique_users = self.db.get_unique_usernames()
        self.assertEqual(unique_users, ["Alice", "Charlie"])

    def test_delete_record(self):
        """Test deleting a specific record by ID."""
        r_id = self.db.add_record("Diana", 65.0, 1.68, 23.03, "Normal")
        self.assertTrue(self.db.delete_record(r_id))
        self.assertEqual(len(self.db.get_records()), 0)


class TestCSVExport(unittest.TestCase):
    """Test CSV export functionality."""

    def setUp(self):
        """Create a temporary directory for test CSV files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_records_with_headers(self):
        """Verify that exported CSV contains expected headers and data rows."""
        records = [
            (1, "Alice", 60.0, 1.70, 20.76, "Normal", "2026-03-01 09:00:00"),
            (2, "Bob", 85.0, 1.75, 27.76, "Overweight", "2026-03-01 10:00:00")
        ]
        out_csv = Path(self.test_dir) / "test_export.csv"
        count = export_records_to_csv(records, str(out_csv))

        self.assertEqual(count, 2)
        self.assertTrue(out_csv.exists())

        # Verify content
        with open(out_csv, mode="r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            self.assertEqual(len(reader), 3)  # Header + 2 data rows
            self.assertEqual(reader[0], ["Record ID", "Username", "Weight (kg)", "Height (m)", "BMI", "Category", "Date & Time"])
            self.assertEqual(reader[1][1], "Alice")
            self.assertEqual(reader[2][1], "Bob")

    def test_export_empty_history(self):
        """Verify that exporting empty records writes the header without errors."""
        records = []
        out_csv = Path(self.test_dir) / "empty_export.csv"
        count = export_records_to_csv(records, str(out_csv))

        self.assertEqual(count, 0)
        self.assertTrue(out_csv.exists())

        with open(out_csv, mode="r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            self.assertEqual(len(reader), 1)  # Only Header
            self.assertEqual(reader[0], ["Record ID", "Username", "Weight (kg)", "Height (m)", "BMI", "Category", "Date & Time"])


if __name__ == "__main__":
    unittest.main()
