#!/usr/bin/env python3
"""
Styled Matrix: Vistab
---------------------
This example executes a highly stylized matrix pushing custom theme algorithms programmatically natively.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from vistab import Vistab

def main():
    table = Vistab(style="double")
    table.set_title("Vistab Complex Theme Mappings")
    
    # Generate mock test matrix logic natively
    table.add_rows([
        ["Target Architecture", "Uptime", "Capacity", "Status"],
        ["Database Primary", "365d", "88%", "Stable"],
        ["Compute Cluster A", "12d", "99%", "Critical"],
        ["Compute Cluster B", "14d", "15%", "Idle"],
        ["Edge Node Cache", "0d", "0%", "Offline"]
    ])
    
    # Apply a fluid dictionary tracking specific targets dynamically explicit reliably!
    custom_theme = {
        "padding": 3,
        "table": {"bg": "bright_black"}, # Global dark mode background
        "header": {"fg": "black", "bg": "white"}, # High contrast header
        "col_0": {"fg": "cyan"}, # Standard index columns
        "row_-1": {"fg": "red", "italic": True} # Dynamic styled failure logic
    }
    
    # Pushing mappings
    table.apply_theme(custom_theme)
    print(table.draw())

if __name__ == "__main__":
    main()
