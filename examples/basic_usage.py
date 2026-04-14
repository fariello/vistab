#!/usr/bin/env python3
"""
Basic Usage: Vistab
-------------------
This example demonstrates constructing a simple standard formatting layout manually pushing configurations.
"""
import sys
import os

# Ensure we map the local development src tree automatically!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from vistab import Vistab

def main():
    # 1. Instantiate the builder fluidly
    table = Vistab(style="round-header", padding=2)
    
    # 2. Add properties organically mapped
    table.set_title("Vistab Basic Demonstration")
    table.set_cols_dtype(["t", "f", "i"])
    table.set_precision(2)
    
    # 3. Add explicit data iteratively
    table.add_rows([
        ["Target Category", "Measured Value", "Raw Quantity"],
        ["Local Performance", 15.34005, 1024.0],
        ["Remote Overheads", 99.4, 256.12]
    ])
    
    # 4. Provide specific visual aesthetics structurally
    table.bold_header()
    table.color_row(-1, fg="red") # Warn the last row
    
    # 5. Execute outputs
    print(table.draw())

if __name__ == "__main__":
    main()
