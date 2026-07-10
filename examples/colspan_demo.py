#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstration of horizontal Column Spanning (Colspan) support in Vistab.
"""

from vistab import Vistab, ColSpan

def run_demo():
    print("=== Vistab Column Spanning (Colspan) Demo ===\n")

    # 1. Inline ColSpan Declarations
    print("--- 1. Inline Spans in Headers and Rows ---")
    table = Vistab(style="round", padding=1)
    
    # "Sub-header Block" spans 2 columns (index 1 and 2)
    table.set_header(["Category", ColSpan("Sub-header Block", 2), "Status"])
    
    # "Data block spanning 2 columns" spans index 1 and 2
    table.add_row(["Engine", ColSpan("Data block spanning 2 columns", 2), "Active"])
    table.add_row(["Memory", "16 GB", "LPDDR5", "Healthy"])
    
    print(table.draw())
    print()

    # 2. Programmatic Post-Ingestion Spanning
    print("--- 2. Programmatic Coordinate Mutators ---")
    table2 = Vistab(style="light", padding=1)
    
    # Ingest standard row data
    table2.set_header(["Name", "", "", "Status"])
    table2.add_row(["Alice", "Age: 25", "City: Paris", "Active"])
    table2.add_row(["Bob", "", "", "Inactive"])
    
    # Apply spans post-ingestion
    # Merges name headers: "Name" spans 3 columns (covers 0, 1, 2)
    table2.set_header_span(0, 3)
    
    # Merges Bob's details: empty cells at index 1 and 2 are spanned
    table2.set_cell_span(1, 1, 2)
    
    print(table2.draw())
    print()

    # 3. Content Merging & Overwrite Guardrails
    print("--- 3. Content Merging & Overwrite Guardrails ---")
    table3 = Vistab(style="light", padding=1)
    table3.set_header(["Name", "Age", "City"])
    table3.add_row(["Alice", 25, "Paris"])
    
    print("Pre-merged table:")
    print(table3.draw())
    
    # Merge cells at 0, 0 spanning 3 columns.
    # By default, combine=" " will merge "Alice", 25, and "Paris" into "Alice 25 Paris"
    table3.set_cell_span(0, 0, 3, combine=", ")
    print("Post-merged table (combine=', '):")
    print(table3.draw())
    
    # Demonstrate combine=None strict mode error
    print("Trying to overwrite a non-empty cell with combine=None:")
    table4 = Vistab(style="light")
    table4.set_header(["A", "B"])
    table4.add_row(["1", "2"])
    try:
        table4.set_cell_span(0, 0, 2, combine=None)
    except ValueError as e:
        print(f"  Caught expected error: {e}")
        
    print("\nAll demos executed successfully!")

if __name__ == "__main__":
    run_demo()
