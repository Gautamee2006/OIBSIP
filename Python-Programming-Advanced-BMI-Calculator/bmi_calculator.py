"""
Advanced BMI Calculator
Oasis Infobyte Python Programming Internship

A modern desktop GUI application built with Python 3, Tkinter/ttk, SQLite3, and Matplotlib.
Implements BMI calculation, health category classification, multi-user history tracking,
trend visualization, and CSV export.
"""

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Optional

# Matplotlib imports for trend visualization
import matplotlib
matplotlib.use("TkAgg")  # Ensure Tkinter backend is used
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from database import BMIDatabase, DEFAULT_DB_PATH


# ============================================================================
# Core Calculation & Validation Logic (Decoupled from GUI for Testability)
# ============================================================================

CATEGORY_COLORS = {
    "Underweight": "#0284C7",  # Vibrant Blue
    "Normal": "#16A34A",       # Vibrant Green
    "Overweight": "#EA580C",   # Vibrant Orange
    "Obese": "#DC2626"         # Vibrant Red
}

CATEGORY_DESCRIPTIONS = {
    "Underweight": "BMI is below 18.5. You may need to gain weight. Consult a healthcare provider.",
    "Normal": "BMI is between 18.5 and 24.9. Your weight is within the healthy recommended range.",
    "Overweight": "BMI is between 25.0 and 29.9. Consider a balanced diet and regular physical activity.",
    "Obese": "BMI is 30.0 or higher. Consult a healthcare professional for guidance on healthy living."
}


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    Calculate Body Mass Index (BMI).
    Formula: BMI = weight (kg) / (height (m) * height (m))
    Returns rounded float to 2 decimal places.
    Raises ValueError if weight or height is non-positive.
    """
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")
    if height_m <= 0:
        raise ValueError("Height must be greater than zero.")
    
    raw_bmi = weight_kg / (height_m ** 2)
    return round(raw_bmi, 2)


def get_bmi_category(bmi: float) -> str:
    """
    Classify BMI into standard WHO health categories:
      - Underweight: BMI < 18.5
      - Normal: 18.5 <= BMI < 25.0
      - Overweight: 25.0 <= BMI < 30.0
      - Obese: BMI >= 30.0
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal"
    elif bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"


def get_category_color(category: str) -> str:
    """Return the assigned hex color for a given BMI category."""
    return CATEGORY_COLORS.get(category, "#4B5563")


def validate_inputs(username: str, weight_str: str, height_str: str) -> Tuple[str, float, float]:
    """
    Validate user inputs.
    Returns (cleaned_username, weight_float, height_float) on success.
    Raises ValueError with a friendly message on invalid input.
    """
    clean_username = username.strip() if username else ""
    if not clean_username:
        raise ValueError("Username cannot be empty. Please enter your name.")

    # Check for empty weight or height
    if not weight_str or not weight_str.strip():
        raise ValueError("Weight cannot be empty. Please enter your weight in kilograms.")
    if not height_str or not height_str.strip():
        raise ValueError("Height cannot be empty. Please enter your height in meters.")

    # Validate numeric conversion
    try:
        weight_val = float(weight_str.strip())
    except ValueError:
        raise ValueError("Weight must be a valid numeric number (e.g., 68.5).")

    try:
        height_val = float(height_str.strip())
    except ValueError:
        raise ValueError("Height must be a valid numeric number (e.g., 1.75).")

    # Validate positive bounds
    if weight_val <= 0:
        raise ValueError("Weight must be greater than zero.")
    if height_val <= 0:
        raise ValueError("Height must be greater than zero.")

    # Reasonable physiological checks
    if height_val > 3.0:
        raise ValueError("Height seems too large. Please enter height in meters (e.g., 1.75 m instead of 175 cm).")
    if weight_val > 600.0:
        raise ValueError("Weight value exceeds realistic range. Please enter weight in kg.")

    return clean_username, weight_val, height_val


def export_records_to_csv(records: List[Tuple], file_path: str) -> int:
    """
    Export database records to a CSV file.
    Returns the number of records exported.
    """
    headers = ["Record ID", "Username", "Weight (kg)", "Height (m)", "BMI", "Category", "Date & Time"]
    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in records:
            writer.writerow(row)
    return len(records)


# ============================================================================
# GUI Application Implementation
# ============================================================================

class BMICalculatorApp(tk.Tk):
    """Main Application Window for Advanced BMI Calculator."""

    def __init__(self, db: Optional[BMIDatabase] = None) -> None:
        super().__init__()
        self.db = db if db is not None else BMIDatabase()

        self.title("Advanced BMI Calculator | Oasis Infobyte")
        self.geometry("1020x720")
        self.minsize(880, 620)
        self.configure(bg="#F1F5F9")  # Clean slate light background

        # Configure styles
        self._setup_styles()

        # Build Interface
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        # Load initial history table
        self.refresh_history()

    def _setup_styles(self) -> None:
        """Configure modern ttk styles for light theme aesthetics."""
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # Colors
        bg_main = "#F1F5F9"
        card_bg = "#FFFFFF"
        text_dark = "#0F172A"

        self.style.configure(".", background=bg_main, foreground=text_dark, font=("Segoe UI", 10))
        
        # Frames
        self.style.configure("Card.TFrame", background=card_bg, relief="flat")
        self.style.configure("Header.TFrame", background="#FFFFFF", relief="flat")

        # Labels
        self.style.configure("HeaderTitle.TLabel", background="#FFFFFF", foreground="#0F172A", font=("Segoe UI", 18, "bold"))
        self.style.configure("HeaderSub.TLabel", background="#FFFFFF", foreground="#64748B", font=("Segoe UI", 10))
        self.style.configure("CardTitle.TLabel", background=card_bg, foreground="#1E293B", font=("Segoe UI", 13, "bold"))
        self.style.configure("FieldLabel.TLabel", background=card_bg, foreground="#334155", font=("Segoe UI", 10, "bold"))
        self.style.configure("HintLabel.TLabel", background=card_bg, foreground="#94A3B8", font=("Segoe UI", 9))
        self.style.configure("Status.TLabel", background="#E2E8F0", foreground="#475569", font=("Segoe UI", 9))

        # Buttons
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#2563EB",
            foreground="#FFFFFF",
            padding=(12, 8),
            borderwidth=0
        )
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8")])

        self.style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            background="#E2E8F0",
            foreground="#1E293B",
            padding=(10, 6),
            borderwidth=0
        )
        self.style.map("Secondary.TButton", background=[("active", "#CBD5E1")])

        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#7C3AED",
            foreground="#FFFFFF",
            padding=(10, 6),
            borderwidth=0
        )
        self.style.map("Accent.TButton", background=[("active", "#6D28D9")])

        self.style.configure(
            "Success.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#059669",
            foreground="#FFFFFF",
            padding=(10, 6),
            borderwidth=0
        )
        self.style.map("Success.TButton", background=[("active", "#047857")])

        # Treeview styling
        self.style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            rowheight=28,
            font=("Segoe UI", 9)
        )
        self.style.configure(
            "Treeview.Heading",
            background="#F8FAFC",
            foreground="#0F172A",
            font=("Segoe UI", 9, "bold"),
            padding=(4, 6)
        )
        self.style.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])

    def _build_header(self) -> None:
        """Create the top branded header banner."""
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(20, 14))
        header_frame.pack(fill="x", side="top", padx=0, pady=(0, 10))

        title_lbl = ttk.Label(header_frame, text="Advanced BMI Calculator", style="HeaderTitle.TLabel")
        title_lbl.pack(anchor="w")

        sub_lbl = ttk.Label(
            header_frame,
            text="Oasis Infobyte Internship | Python Programming Track • Multi-User Tracking & Analytics",
            style="HeaderSub.TLabel"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

    def _build_main_layout(self) -> None:
        """Construct the two-column split layout: Left = Inputs & Results, Right = History Table & Actions."""
        main_container = ttk.Frame(self, padding=(16, 6))
        main_container.pack(fill="both", expand=True)

        # Left Column: Inputs & Results Card
        left_col = ttk.Frame(main_container, style="Card.TFrame", padding=16)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_col.configure(width=360)
        left_col.pack_propagate(False)

        self._build_input_section(left_col)
        self._build_result_section(left_col)

        # Right Column: History Table & Visualization Card
        right_col = ttk.Frame(main_container, style="Card.TFrame", padding=16)
        right_col.pack(side="right", fill="both", expand=True)

        self._build_history_section(right_col)

    def _build_input_section(self, parent: ttk.Frame) -> None:
        """Build user data input fields and calculate button."""
        title = ttk.Label(parent, text="Calculate Your BMI", style="CardTitle.TLabel")
        title.pack(anchor="w", pady=(0, 12))

        # Username
        ttk.Label(parent, text="User Name:", style="FieldLabel.TLabel").pack(anchor="w")
        self.user_entry = ttk.Entry(parent, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(2, 8))

        # Weight
        ttk.Label(parent, text="Weight (in kilograms):", style="FieldLabel.TLabel").pack(anchor="w")
        self.weight_entry = ttk.Entry(parent, font=("Segoe UI", 10))
        self.weight_entry.pack(fill="x", pady=(2, 2))
        ttk.Label(parent, text="Example: 70.5", style="HintLabel.TLabel").pack(anchor="w", pady=(0, 8))

        # Height
        ttk.Label(parent, text="Height (in meters):", style="FieldLabel.TLabel").pack(anchor="w")
        self.height_entry = ttk.Entry(parent, font=("Segoe UI", 10))
        self.height_entry.pack(fill="x", pady=(2, 2))
        ttk.Label(parent, text="Example: 1.75 (use meters, not cm)", style="HintLabel.TLabel").pack(anchor="w", pady=(0, 12))

        # Button Row
        btn_row = ttk.Frame(parent, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(4, 14))

        self.calc_btn = ttk.Button(
            btn_row,
            text="Calculate & Save",
            style="Primary.TButton",
            command=self.calculate_and_save
        )
        self.calc_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.clear_btn = ttk.Button(
            btn_row,
            text="Clear Inputs",
            style="Secondary.TButton",
            command=self.clear_inputs
        )
        self.clear_btn.pack(side="right", fill="x", expand=False)

    def _build_result_section(self, parent: ttk.Frame) -> None:
        """Build the dynamic result card that shows BMI value, category badge, and health tips."""
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", pady=(4, 12))

        res_title = ttk.Label(parent, text="Calculation Result", style="CardTitle.TLabel")
        res_title.pack(anchor="w", pady=(0, 8))

        # Result display container with subtle border
        self.result_container = tk.Frame(parent, bg="#F8FAFC", bd=1, relief="solid", highlightthickness=0)
        self.result_container.pack(fill="x", pady=(0, 10), ipady=12, ipadx=10)

        self.bmi_value_lbl = tk.Label(
            self.result_container,
            text="--.--",
            font=("Segoe UI", 32, "bold"),
            bg="#F8FAFC",
            fg="#0F172A"
        )
        self.bmi_value_lbl.pack(pady=(0, 4))

        # Category Badge
        self.category_badge = tk.Label(
            self.result_container,
            text="Awaiting Input",
            font=("Segoe UI", 11, "bold"),
            bg="#E2E8F0",
            fg="#475569",
            padx=14,
            pady=4
        )
        self.category_badge.pack(pady=(2, 6))

        # Health tip label
        self.tip_lbl = tk.Label(
            self.result_container,
            text="Enter your details above and click Calculate & Save.",
            font=("Segoe UI", 9),
            bg="#F8FAFC",
            fg="#64748B",
            wraplength=300,
            justify="center"
        )
        self.tip_lbl.pack(padx=8, pady=(4, 0))

        # Reference Category Key Table
        ref_frame = tk.Frame(parent, bg="#FFFFFF")
        ref_frame.pack(fill="x", pady=(6, 0))

        ttk.Label(ref_frame, text="BMI Categories Reference:", style="FieldLabel.TLabel").pack(anchor="w", pady=(0, 4))

        categories_guide = [
            ("Underweight", "< 18.5", CATEGORY_COLORS["Underweight"]),
            ("Normal", "18.5 – 24.9", CATEGORY_COLORS["Normal"]),
            ("Overweight", "25.0 – 29.9", CATEGORY_COLORS["Overweight"]),
            ("Obese", "≥ 30.0", CATEGORY_COLORS["Obese"])
        ]

        for cat, rng, color in categories_guide:
            row = tk.Frame(ref_frame, bg="#FFFFFF")
            row.pack(fill="x", pady=1)

            bullet = tk.Label(row, text="●", fg=color, bg="#FFFFFF", font=("Segoe UI", 10))
            bullet.pack(side="left", padx=(4, 6))

            cat_txt = tk.Label(row, text=f"{cat}:", font=("Segoe UI", 9, "bold"), fg="#334155", bg="#FFFFFF")
            cat_txt.pack(side="left")

            rng_txt = tk.Label(row, text=rng, font=("Segoe UI", 9), fg="#64748B", bg="#FFFFFF")
            rng_txt.pack(side="right")

    def _build_history_section(self, parent: ttk.Frame) -> None:
        """Build the history table, filter bar, and action buttons."""
        top_bar = ttk.Frame(parent, style="Card.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))

        title = ttk.Label(top_bar, text="BMI History & User Records", style="CardTitle.TLabel")
        title.pack(side="left", anchor="w")

        # Filter bar
        filter_box = ttk.Frame(top_bar, style="Card.TFrame")
        filter_box.pack(side="right")

        ttk.Label(filter_box, text="Filter User:", style="HintLabel.TLabel").pack(side="left", padx=(0, 4))
        self.filter_entry = ttk.Entry(filter_box, width=14, font=("Segoe UI", 9))
        self.filter_entry.pack(side="left", padx=(0, 6))

        filter_btn = ttk.Button(filter_box, text="Filter", style="Secondary.TButton", command=self.apply_filter)
        filter_btn.pack(side="left", padx=(0, 4))

        reset_btn = ttk.Button(filter_box, text="Show All / Refresh", style="Secondary.TButton", command=self.refresh_history)
        reset_btn.pack(side="left")

        # Treeview with Scrollbars
        table_container = ttk.Frame(parent, style="Card.TFrame")
        table_container.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("id", "username", "weight", "height", "bmi", "category", "created_at")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="User Name")
        self.tree.heading("weight", text="Weight (kg)")
        self.tree.heading("height", text="Height (m)")
        self.tree.heading("bmi", text="BMI")
        self.tree.heading("category", text="Category")
        self.tree.heading("created_at", text="Date & Time")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("username", width=120, anchor="w")
        self.tree.column("weight", width=85, anchor="center")
        self.tree.column("height", width=85, anchor="center")
        self.tree.column("bmi", width=75, anchor="center")
        self.tree.column("category", width=110, anchor="center")
        self.tree.column("created_at", width=150, anchor="center")

        v_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        # Configure category tag colors for treeview rows
        self.tree.tag_configure("Underweight", foreground=CATEGORY_COLORS["Underweight"])
        self.tree.tag_configure("Normal", foreground=CATEGORY_COLORS["Normal"])
        self.tree.tag_configure("Overweight", foreground=CATEGORY_COLORS["Overweight"])
        self.tree.tag_configure("Obese", foreground=CATEGORY_COLORS["Obese"])

        # When an item is selected, populate fields
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Action Buttons under Table
        action_bar = ttk.Frame(parent, style="Card.TFrame")
        action_bar.pack(fill="x", pady=(4, 0))

        self.chart_btn = ttk.Button(
            action_bar,
            text="📈 Show BMI Trend Chart",
            style="Accent.TButton",
            command=self.show_bmi_chart
        )
        self.chart_btn.pack(side="left", padx=(0, 8))

        self.export_btn = ttk.Button(
            action_bar,
            text="📥 Export to CSV",
            style="Success.TButton",
            command=self.export_to_csv_dialog
        )
        self.export_btn.pack(side="left", padx=(0, 8))

        self.delete_btn = ttk.Button(
            action_bar,
            text="🗑️ Delete Selected",
            style="Secondary.TButton",
            command=self.delete_selected_record
        )
        self.delete_btn.pack(side="right")

    def _build_status_bar(self) -> None:
        """Construct bottom status message bar."""
        status_bar = ttk.Frame(self, style="Header.TFrame", padding=(16, 4))
        status_bar.pack(fill="x", side="bottom")

        self.status_lbl = ttk.Label(status_bar, text="Ready. Enter details to compute BMI.", style="Status.TLabel")
        self.status_lbl.pack(side="left")

        self.record_count_lbl = ttk.Label(status_bar, text="Records: 0", style="Status.TLabel")
        self.record_count_lbl.pack(side="right")

    def set_status(self, message: str) -> None:
        """Update the status bar text."""
        self.status_lbl.config(text=message)

    # ========================================================================
    # Event Handlers & Controller Logic
    # ========================================================================

    def calculate_and_save(self) -> None:
        """Validate inputs, calculate BMI, update display, and save to SQLite database."""
        raw_user = self.user_entry.get()
        raw_weight = self.weight_entry.get()
        raw_height = self.height_entry.get()

        try:
            username, weight, height = validate_inputs(raw_user, raw_weight, raw_height)
        except ValueError as err:
            messagebox.showwarning("Validation Error", str(err))
            self.set_status(f"Validation error: {err}")
            return

        # Perform calculation
        bmi = calculate_bmi(weight, height)
        category = get_bmi_category(bmi)
        color = get_category_color(category)

        # Update Result View
        self.bmi_value_lbl.config(text=f"{bmi:.2f}")
        self.category_badge.config(text=category, bg=color, fg="#FFFFFF")
        self.tip_lbl.config(text=CATEGORY_DESCRIPTIONS.get(category, ""))

        # Save to SQLite Database
        try:
            record_id = self.db.add_record(
                username=username,
                weight=weight,
                height=height,
                bmi=bmi,
                category=category
            )
            self.set_status(f"Success: Record #{record_id} saved for '{username}' (BMI: {bmi:.2f} - {category}).")
            messagebox.showinfo(
                "Calculation Complete",
                f"BMI: {bmi:.2f}\nCategory: {category}\n\nRecord saved to database successfully!"
            )
        except Exception as exc:
            messagebox.showerror("Database Error", f"Failed to save record to database:\n{exc}")
            self.set_status(f"Database error: {exc}")
            return

        # Refresh table
        self.refresh_history(highlight_user=username)

    def clear_inputs(self) -> None:
        """Clear user input fields and reset the result display."""
        self.user_entry.delete(0, tk.END)
        self.weight_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.bmi_value_lbl.config(text="--.--")
        self.category_badge.config(text="Awaiting Input", bg="#E2E8F0", fg="#475569")
        self.tip_lbl.config(text="Enter your details above and click Calculate & Save.")
        self.set_status("Inputs cleared.")

    def refresh_history(self, highlight_user: Optional[str] = None) -> None:
        """Fetch all records from SQLite and reload the treeview table."""
        self.filter_entry.delete(0, tk.END)
        self._load_table_data(records=self.db.get_records(order_by_id_asc=False))
        if highlight_user:
            self.set_status(f"History refreshed. Highlighted user '{highlight_user}'.")
        else:
            self.set_status("History loaded (all users).")

    def apply_filter(self) -> None:
        """Filter history records by username typed into the filter box."""
        filter_user = self.filter_entry.get().strip()
        if not filter_user:
            self.refresh_history()
            return

        filtered_records = self.db.get_records(username=filter_user, order_by_id_asc=False)
        self._load_table_data(records=filtered_records)
        self.set_status(f"Filter active: '{filter_user}' ({len(filtered_records)} records found).")

    def _load_table_data(self, records: List[Tuple]) -> None:
        """Clear treeview and insert given list of records."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in records:
            # row: (id, username, weight, height, bmi, category, created_at)
            cat = row[5]
            formatted_weight = f"{row[2]:.2f}"
            formatted_height = f"{row[3]:.2f}"
            formatted_bmi = f"{row[4]:.2f}"

            display_row = (row[0], row[1], formatted_weight, formatted_height, formatted_bmi, cat, row[6])
            self.tree.insert("", "end", values=display_row, tags=(cat,))

        self.record_count_lbl.config(text=f"Records: {len(records)}")

    def _on_tree_select(self, event: tk.Event) -> None:
        """When user clicks a row in the table, populate input fields for quick review."""
        selected = self.tree.selection()
        if not selected:
            return
        item_vals = self.tree.item(selected[0], "values")
        if item_vals:
            # item_vals: (id, username, weight, height, bmi, category, created_at)
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, item_vals[1])
            self.weight_entry.delete(0, tk.END)
            self.weight_entry.insert(0, item_vals[2])
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, item_vals[3])

            # Also update result card
            bmi_val = float(item_vals[4])
            cat_val = item_vals[5]
            color = get_category_color(cat_val)
            self.bmi_value_lbl.config(text=f"{bmi_val:.2f}")
            self.category_badge.config(text=cat_val, bg=color, fg="#FFFFFF")
            self.tip_lbl.config(text=CATEGORY_DESCRIPTIONS.get(cat_val, ""))

    def delete_selected_record(self) -> None:
        """Delete selected record from database and table."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a record from the table to delete.")
            return

        item_vals = self.tree.item(selected[0], "values")
        record_id = int(item_vals[0])
        user_name = item_vals[1]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete record #{record_id} for '{user_name}'?"
        )
        if confirm:
            try:
                self.db.delete_record(record_id)
                self.tree.delete(selected[0])
                self.set_status(f"Record #{record_id} deleted successfully.")
                # update count
                count = len(self.tree.get_children())
                self.record_count_lbl.config(text=f"Records: {count}")
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to delete record: {exc}")

    def show_bmi_chart(self) -> None:
        """
        Display a Matplotlib trend chart of BMI over time for a specific user.
        Validates that at least two records exist for the selected user.
        """
        # Determine username to chart: first from filter entry, then from username entry, or from selection
        target_user = self.filter_entry.get().strip()
        if not target_user:
            target_user = self.user_entry.get().strip()

        # If still empty, check if row selected in tree
        if not target_user:
            selected = self.tree.selection()
            if selected:
                target_user = self.tree.item(selected[0], "values")[1]

        # If no user specified, prompt or show list
        if not target_user:
            unique_users = self.db.get_unique_usernames()
            if not unique_users:
                messagebox.showinfo("No Records", "No records found in database. Calculate and save records first.")
                return
            target_user = unique_users[0]

        # Fetch records for target_user in chronological order (ASC)
        user_records = self.db.get_records(username=target_user, order_by_id_asc=True)

        if len(user_records) == 0:
            messagebox.showinfo(
                "No Records Found",
                f"No records found for user '{target_user}'.\nPlease calculate and save records first."
            )
            return

        if len(user_records) < 2:
            messagebox.showinfo(
                "Insufficient Records for Trend",
                f"User '{target_user}' has only 1 saved record.\n\n"
                f"At least two records over time are required to plot a trend chart.\n"
                f"Please calculate and save another record for '{target_user}'."
            )
            return

        # Prepare data for plotting
        dates = [row[6] for row in user_records]
        bmis = [row[4] for row in user_records]

        # Shorten timestamp labels for clear X-axis readability (e.g. MM-DD HH:MM)
        short_dates = []
        for d in dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                short_dates.append(dt.strftime("%m/%d %H:%M"))
            except Exception:
                short_dates.append(d)

        # Create TopLevel window for chart
        chart_window = tk.Toplevel(self)
        chart_window.title(f"BMI Trend Chart — {target_user}")
        chart_window.geometry("820x560")
        chart_window.configure(bg="#FFFFFF")

        # Matplotlib figure with clean light theme aesthetics
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#F8FAFC")

        # Plot BMI line
        ax.plot(
            short_dates,
            bmis,
            marker="o",
            markersize=7,
            linewidth=2.5,
            color="#2563EB",
            label="BMI Value",
            zorder=4
        )

        # Annotate each data point
        for x, y in zip(short_dates, bmis):
            ax.annotate(
                f"{y:.2f}",
                xy=(x, y),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                fontweight="bold",
                color="#1E293B"
            )

        # Category guideline spans / reference lines
        y_min = min(bmis) - 2.0
        y_max = max(bmis) + 2.0
        ax.set_ylim(max(10, y_min), max(35, y_max))

        # Category background bands
        ax.axhspan(0, 18.5, color="#0284C7", alpha=0.08, label="Underweight (<18.5)")
        ax.axhspan(18.5, 25.0, color="#16A34A", alpha=0.10, label="Normal (18.5–24.9)")
        ax.axhspan(25.0, 30.0, color="#EA580C", alpha=0.08, label="Overweight (25–29.9)")
        ax.axhspan(30.0, 60.0, color="#DC2626", alpha=0.08, label="Obese (≥30.0)")

        # Threshold lines
        ax.axhline(18.5, color="#0284C7", linestyle="--", linewidth=1, alpha=0.6)
        ax.axhline(25.0, color="#16A34A", linestyle="--", linewidth=1, alpha=0.6)
        ax.axhline(30.0, color="#DC2626", linestyle="--", linewidth=1, alpha=0.6)

        ax.set_title(f"BMI History Trend for User: {target_user}", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
        ax.set_xlabel("Date & Time Recorded", fontsize=10, fontweight="bold", labelpad=8, color="#334155")
        ax.set_ylabel("BMI Value (kg/m²)", fontsize=10, fontweight="bold", labelpad=8, color="#334155")

        ax.grid(True, linestyle=":", alpha=0.6, color="#94A3B8")
        ax.tick_params(axis="x", rotation=25, labelsize=9)
        ax.tick_params(axis="y", labelsize=9)
        ax.legend(loc="upper left", frameon=True, facecolor="#FFFFFF", framealpha=0.9, fontsize=8)

        fig.tight_layout()

        # Embed into Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, chart_window)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.set_status(f"Displayed trend chart for user '{target_user}'.")

    def export_to_csv_dialog(self) -> None:
        """Prompt user with save dialog and export current table history to CSV."""
        filter_user = self.filter_entry.get().strip()
        records = self.db.get_records(username=filter_user if filter_user else None, order_by_id_asc=True)

        if not records:
            messagebox.showinfo("No Records", "There are no records available to export.")
            return

        default_filename = f"bmi_records_{filter_user if filter_user else 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export BMI History to CSV",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV (Comma Separated Values)", "*.csv"), ("All Files", "*.*")]
        )

        if not file_path:
            # User cancelled the save dialog gracefully
            self.set_status("CSV export cancelled by user.")
            return

        try:
            count = export_records_to_csv(records, file_path)
            messagebox.showinfo(
                "Export Successful",
                f"Successfully exported {count} record(s) to:\n{file_path}"
            )
            self.set_status(f"Successfully exported {count} records to CSV.")
        except PermissionError:
            messagebox.showerror(
                "Permission Denied",
                f"Cannot write to file '{file_path}'.\nPlease verify that the file is not opened in another application."
            )
            self.set_status("CSV export failed: Permission denied.")
        except Exception as exc:
            messagebox.showerror("Export Failed", f"An unexpected error occurred during export:\n{exc}")
            self.set_status(f"CSV export error: {exc}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Launch the Advanced BMI Calculator application."""
    app = BMICalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
