"""
Test script for generate_grades.py

Creates sample data to test the grade generation logic without requiring
actual Google Sheets connection.
"""

import csv
import os
from datetime import datetime
from generate_grades import (
    load_roster,
    match_student_name,
    generate_grade_csvs
)


def create_sample_sheet_records():
    """Create sample Google Sheet records for testing."""
    return [
        {
            'Timestamp': '2025-09-15 10:30:00',
            'Student Name': 'Kyleigh Adams',  # Free-form before cutoff
            'Scenario Title': 'Liberty Park Scenario',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice A → Choice B',
            'Reflection 1': 'Great learning experience',
            'Reflection 2': 'I would choose differently next time',
            'Reflection 3': 'Very educational',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-09-16 14:20:00',
            'Student Name': 'Toluwalase Adelakun',  # Free-form
            'Scenario Title': 'Liberty Park Scenario',
            'Scenario Outcome': 'compromise',
            'Choices Made': 'Choice A → Choice C',
            'Reflection 1': 'Interesting choices',
            'Reflection 2': 'Learned about consequences',
            'Reflection 3': 'Would recommend',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-10-15 09:00:00',
            'Student Name': 'Albelo, Lucero',  # Exact format after cutoff
            'Scenario Title': 'Civil Rights Realignment',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice A → Choice D',
            'Reflection 1': 'Very thought-provoking',
            'Reflection 2': 'Changed my perspective',
            'Reflection 3': 'Excellent scenario',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-10-16 11:30:00',
            'Student Name': 'Alexander, Jaelynn',  # Exact format
            'Scenario Title': 'Liberty Park Scenario',
            'Scenario Outcome': 'failure',
            'Choices Made': 'Choice B → Choice E',
            'Reflection 1': 'Learned from mistakes',
            'Reflection 2': 'Will try again',
            'Reflection 3': 'Good experience',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-10-17 15:45:00',
            'Student Name': 'Alexander, Jaelynn',  # Duplicate - should not create duplicate entry
            'Scenario Title': 'Liberty Park Scenario',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice A → Choice B',
            'Reflection 1': 'Better this time',
            'Reflection 2': 'Understood the choices',
            'Reflection 3': 'Great learning',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-09-20 12:00:00',
            'Student Name': 'Unknown Student',  # Should not match
            'Scenario Title': 'Liberty Park Scenario',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice A',
            'Reflection 1': 'Good',
            'Reflection 2': 'Good',
            'Reflection 3': 'Good',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-09-21 16:30:00',
            'Student Name': 'Alimi, Barakah',
            'Scenario Title': 'Civil Rights Realignment',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice C → Choice D',
            'Reflection 1': 'Insightful',
            'Reflection 2': 'Very relevant',
            'Reflection 3': 'Enjoyed it',
            'Completion Status': 'Completed'
        },
        {
            'Timestamp': '2025-09-22 10:00:00',
            'Student Name': 'Raymond Appleberry',  # First Last format
            'Scenario Title': 'Probable Cause Scenario',
            'Scenario Outcome': 'success',
            'Choices Made': 'Choice A → Choice B → Choice C',
            'Reflection 1': 'Complex decisions',
            'Reflection 2': 'Learned a lot',
            'Reflection 3': 'Challenging',
            'Completion Status': 'Completed'
        }
    ]


def test_name_matching():
    """Test the name matching logic."""
    print("Testing name matching logic...")
    print("=" * 60)

    roster_lastname_first, roster_firstname_last, all_names = load_roster()
    cutoff_date = datetime(2025, 10, 9)

    test_cases = [
        ("Kyleigh Adams", datetime(2025, 9, 15), "Should match with fuzzy"),
        ("Adams, Kyleigh", datetime(2025, 10, 15), "Should match exact after cutoff"),
        ("Unknown Person", datetime(2025, 9, 15), "Should NOT match"),
        ("Toluwalase Adelakun", datetime(2025, 9, 16), "Should match fuzzy"),
        ("Albelo, Lucero", datetime(2025, 10, 15), "Should match exact"),
    ]

    for name, date, description in test_cases:
        org_id = match_student_name(
            name, cutoff_date, date,
            roster_lastname_first, roster_firstname_last, all_names
        )
        status = "[OK] MATCHED" if org_id else "[FAIL] NO MATCH"
        print(f"{status}: '{name}' ({description})")
        if org_id:
            print(f"         -> {org_id}")

    print()


def test_grade_generation():
    """Test the full grade generation process."""
    print("Testing grade CSV generation...")
    print("=" * 60)

    # Load roster
    roster_lastname_first, roster_firstname_last, all_names = load_roster()

    # Create sample records
    records = create_sample_sheet_records()

    # Generate CSVs
    test_output_dir = "test_grade_outputs"
    csv_files = generate_grade_csvs(
        records,
        roster_lastname_first,
        roster_firstname_last,
        all_names,
        output_dir=test_output_dir
    )

    print(f"\n[OK] Generated {len(csv_files)} CSV files")

    # Display contents of generated files
    print("\nGenerated file contents:")
    print("-" * 60)
    for filename, count in csv_files:
        print(f"\nFile: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            print(f.read())


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GRADE GENERATION TEST SUITE")
    print("=" * 60 + "\n")

    test_name_matching()
    print("\n")
    test_grade_generation()

    print("\n" + "=" * 60)
    print("[OK] All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
