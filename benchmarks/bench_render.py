import time
import sys
import os

# Adjust path to import vistab from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from vistab import Vistab

def generate_test_data(rows, cols):
    # Generates a matrix of rows x cols
    data = []
    # Header
    header = [f"Col{i}" for i in range(cols)]
    # Rows
    for r in range(rows):
        row = []
        for c in range(cols):
            # Interleave float, int, text
            if c % 3 == 0:
                row.append(f"Text_{r}_{c}")
            elif c % 3 == 1:
                row.append(r * 10 + c)
            else:
                row.append(r * 1.23 + c)
        data.append(row)
    return header, data

def run_benchmark():
    print("=== VISTAB RENDERING BENCHMARK ===")

    # 1k rows x 8 cols
    h1k, d1k = generate_test_data(1000, 8)

    # 10k rows x 8 cols
    h10k, d10k = generate_test_data(10000, 8)

    scenarios = [
        ("1k rows x 8 cols", h1k, d1k, 10),
        ("10k rows x 8 cols", h10k, d10k, 2)
    ]

    for label, header, data, iterations in scenarios:
        print(f"\nScenario: {label} ({iterations} iterations)")

        # --- COLD PATH (Fresh object each iteration) ---
        cold_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            # Fresh instance
            t = Vistab(data, header=header, padding=1)
            t.draw()
            end = time.perf_counter()
            cold_times.append(end - start)

        avg_cold = sum(cold_times) / iterations
        cold_rows_sec = len(data) / avg_cold
        print(f"  COLD path (fresh Vistab):  {avg_cold * 1000:.2f} ms/render | {cold_rows_sec:.2f} rows/sec")

        # --- WARM PATH (Reused object) ---
        warm_times = []
        t_warm = Vistab(data, header=header, padding=1)
        # Run once to warm cache / memoize width
        t_warm.draw()
        for _ in range(iterations):
            start = time.perf_counter()
            t_warm.draw()
            end = time.perf_counter()
            warm_times.append(end - start)

        avg_warm = sum(warm_times) / iterations
        warm_rows_sec = len(data) / avg_warm
        print(f"  WARM path (reused Vistab): {avg_warm * 1000:.2f} ms/render | {warm_rows_sec:.2f} rows/sec")

        # --- STREAMING PATH (streamed rows, default sample 100) ---
        stream_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            t_stream = Vistab(padding=1)
            if header:
                t_stream.set_header(header)
            # stream returns an iterator of formatted lines
            lines = list(t_stream.stream(data, sample_size=100))
            end = time.perf_counter()
            stream_times.append(end - start)
        avg_stream = sum(stream_times) / iterations
        stream_rows_sec = len(data) / avg_stream
        print(f"  STREAM path (sample 100):  {avg_stream * 1000:.2f} ms/stream | {stream_rows_sec:.2f} rows/sec")

if __name__ == "__main__":
    run_benchmark()
