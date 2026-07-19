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

def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _bench_once(build):
    import gc
    gc.collect()
    start = time.perf_counter()
    build()
    return time.perf_counter() - start


def run_summary(iterations=5):
    """Deterministic us/row summary for fixed scenarios, for before/after comparison.

    Prints one line per scenario: median wall time and microseconds/row. NOT a pass/fail
    gate (absolute timings vary by machine); it is an informational harness for judging
    optimization changes. See .agents/plans .../assess-performance.
    """
    from vistab import ColSpan

    h, d = generate_test_data(1000, 8)

    def build_plain():
        Vistab(d, header=h, padding=1, max_width=120).draw()

    def build_colspan():
        t = Vistab(padding=1)
        t.set_header(["ID", ColSpan("Contact", 2), "Notes"])
        for r in range(1000):
            t.add_row([r, f"name{r}", f"n{r}@x.io", f"note {r}"])
        t.set_cell_span(0, 1, 2)
        t.draw()

    def build_rtl():
        t = Vistab(padding=1)
        t.set_header(["ID", "Name", "Notes"])
        for r in range(1000):
            t.add_row([r, "\u0627\u0644\u062e\u0648\u0627\u0631\u0632\u0645\u064a", f"note {r}"])
        t.draw()

    scenarios = [("plain_1000x8", build_plain, 1000),
                 ("colspan_1000x4", build_colspan, 1000),
                 ("rtl_1000x3", build_rtl, 1000)]

    print("=== VISTAB BENCH SUMMARY (informational; us/row; not a CI gate) ===")
    for label, build, nrows in scenarios:
        build()  # warm-up (fill lru caches)
        times = [_bench_once(build) for _ in range(iterations)]
        med = _median(times)
        print(f"  {label:16s}  {med * 1000:8.2f} ms/render  {med / nrows * 1e6:7.1f} us/row")


if __name__ == "__main__":
    if "--summary" in sys.argv:
        run_summary()
    else:
        run_benchmark()
