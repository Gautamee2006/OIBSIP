"""
Database Management Module for Advanced BMI Calculator.

This module handles SQLite database operations including table creation,
inserting records, retrieving history, and filtering records by username.
Uses parameterized queries to prevent SQL injection and ensures safe connection handling.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


# Default database path in the current project directory
DEFAULT_DB_PATH = Path(__file__).parent / "bmi_history.db"


class BMIDatabase:
    """Manages SQLite operations for BMI calculation history."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        """Initialize the database manager with an optional custom path."""
        if db_path is None:
            self.db_path = DEFAULT_DB_PATH
        else:
            self.db_path = Path(db_path)
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Return a SQLite connection with timeout and foreign key support."""
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def init_db(self) -> None:
        """Create the bmi_records table if it does not already exist."""
        query = """
        CREATE TABLE IF NOT EXISTS bmi_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            bmi REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Database initialization failed: {exc}") from exc

    def add_record(
        self,
        username: str,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        created_at: Optional[str] = None
    ) -> int:
        """
        Insert a new BMI record into the database.

        Parameters:
            username: Name of the user (non-empty string)
            weight: Weight in kilograms (positive float)
            height: Height in meters (positive float)
            bmi: Calculated BMI value (rounded float)
            category: BMI category (Underweight, Normal, Overweight, Obese)
            created_at: Optional custom timestamp string (defaults to current time)

        Returns:
            The primary key (id) of the inserted record.
        """
        clean_user = username.strip()
        if not clean_user:
            raise ValueError("Username cannot be empty.")
        if weight <= 0:
            raise ValueError("Weight must be greater than zero.")
        if height <= 0:
            raise ValueError("Height must be greater than zero.")

        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
        INSERT INTO bmi_records (username, weight, height, bmi, category, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (clean_user, float(weight), float(height), float(bmi), str(category), str(created_at))
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to insert BMI record: {exc}") from exc

    def get_records(
        self,
        username: Optional[str] = None,
        order_by_id_asc: bool = False
    ) -> List[Tuple[int, str, float, float, float, str, str]]:
        """
        Retrieve BMI records from the database.

        Parameters:
            username: Optional username to filter by (case-insensitive)
            order_by_id_asc: If True, order by id ASC; if False, order by id DESC (newest first).

        Returns:
            List of tuples: (id, username, weight, height, bmi, category, created_at)
        """
        order_direction = "ASC" if order_by_id_asc else "DESC"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if username and username.strip():
                    query = f"""
                    SELECT id, username, weight, height, bmi, category, created_at
                    FROM bmi_records
                    WHERE LOWER(username) = LOWER(?)
                    ORDER BY id {order_direction};
                    """
                    cursor.execute(query, (username.strip(),))
                else:
                    query = f"""
                    SELECT id, username, weight, height, bmi, category, created_at
                    FROM bmi_records
                    ORDER BY id {order_direction};
                    """
                    cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to fetch records: {exc}") from exc

    def get_unique_usernames(self) -> List[str]:
        """Return a sorted list of unique usernames present in the records."""
        query = "SELECT DISTINCT username FROM bmi_records ORDER BY username COLLATE NOCASE ASC;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to fetch unique usernames: {exc}") from exc

    def delete_record(self, record_id: int) -> bool:
        """Delete a record by its ID. Returns True if a record was deleted."""
        query = "DELETE FROM bmi_records WHERE id = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (record_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to delete record ID {record_id}: {exc}") from exc

    def clear_all_records(self) -> None:
        """Clear all records from the table. Primarily for testing purposes."""
        query = "DELETE FROM bmi_records;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to clear table: {exc}") from exc
