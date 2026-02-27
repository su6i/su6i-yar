---
name: data-science-workflow
description: Data Science Workflow Technical Encyclopedia: Polars Streaming, DuckDB Internal Vectorization, and Apache Arrow 22.0.0 Standards.
---

# Skill: Data Science Workflow (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for industrial-grade data science pipelines in the 2025 ecosystem. This document defines the standards for high-performance data processing, memory-efficient analytical querying, and robust DataOps integration.

---

## 1. High-Performance DataFrame Engines (Polars 1.x+)
Leveraging the Rust-powered, multi-threaded execution model for O(N) performance on multi-GB datasets.

### 1.1 Core Architecture & Memory Management
*   **Apache Arrow Backend:** Polars utilizes Arrow-native memory layout, enabling SIMD (Single Instruction, Multiple Data) optimizations and zero-copy transfers between Python, Rust, and C++.
*   **Query Optimization:** 
    *   **Predicate Pushdown:** Filtering data at the source (e.g., Parquet scan) rather than in memory.
    *   **Projection Pushdown:** Only loading relevant columns from disk.
    *   **Common Subplan Elimination:** Detecting and reusing intermediate computation results.
    *   **Expression Parallelism:** Automatically splitting column-wise expressions across all available CPU cores.

### 1.2 Streaming API Protocols (Out-of-Memory Processing)
When datasets exceed RAM (e.g., 100GB on a 32GB machine), the streaming mode must be engaged.
```python
import polars as pl
import os

# 1.2.1 Mandatory Lazy Protocol for Large-Scale Data
# Scanning vs Reading: Scanning creates a computation graph without loading data.
q = (
    pl.scan_parquet("data/*.parquet", low_memory=True, cache=False)
    .filter(pl.col("timestamp") > "2024-01-01")
    .with_columns([
        (pl.col("raw_value") * 0.95).alias("normalized_value"),
        pl.col("category").fill_null("unknown")
    ])
    .group_by("user_id")
    .agg([
        pl.col("normalized_value").mean().alias("mean_val"),
        pl.col("normalized_value").std().alias("std_val"),
        pl.col("user_id").count().alias("transaction_count")
    ])
    .sort("transaction_count", descending=True)
)

# 1.2.2 Execution with Streaming Flag
# The streaming engine processes data in batches (default ~32k rows).
# This prevents the memory resident set from growing linearly with data size.
df = q.collect(streaming=True)
```

### 1.3 Polars Performance Appendix: CLI & Environment Variables
*   `POLARS_MAX_THREADS`: Set the maximum number of threads used by Polars.
*   `POLARS_VERBOSE`: Enable verbose logging for query optimization plans.
*   `POLARS_STREAMING_CHUNK_SIZE`: Adjust the batch size for the streaming engine (default is ~122k).
*   `POLARS_FORCE_ASYNC`: Force asynchronous execution for network-based scans.

---

## 2. In-Process Analytical Databases (DuckDB 1.x+)
The "SQLite for Analytics" standard, utilizing a vectorized Push-Based execution engine.

### 2.1 Vectorized Execution Engine (Internal Logic)
DuckDB's execution engine is "push-based," where each operator pushes its output to the next operator in the pipeline.
*   **The Vector Block:** Data is processed in blocks of 2,048 elements (vectors) to ensure L1/L2 cache residency.
*   **Columnar Storage Internals:** DuckDB uses specialized compression (Bit-packing, FSST for strings, Chimp for floating points) to maximize I/O throughput.
*   **The Buffer Manager:** Dynamically offloading data to disk when query requirements exceed the `memory_limit` setting.

### 2.2 Technical SQL Standards for 2025
*   **AS OF Joins:** Native support for temporal joins (e.g., matching trades with the latest quote based on a timestamp).
    ```sql
    SELECT trades.*, quotes.price
    FROM trades
    AS OF JOIN quotes
    ON trades.symbol = quotes.symbol
    AND trades.time >= quotes.time;
    ```
*   **DuckDB Extensions:**
    *   `httpfs`: Reading data directly from S3/HTTP.
    *   `parquet`: Native, high-speed Parquet integration.
    *   `sqlite`: Querying SQLite databases directly.

---

## 3. The Apache Arrow 22.0.0 Standard
The foundational memory layer for 2025 data engineering.

### 3.1 Memory Layout & Alignment
*   **Validity Bitmaps:** Storing nulls in separate bit arrays to allow for dense mathematical operations on values.
*   **64-Byte Alignment:** Ensuring data blocks align with CPU cache lines.
*   **Dictionary Encoding:** Reducing memory footprint for categorical data.

### 3.2 Arrow Implementation Checklist
- [ ] Confirming data types align with Arrow's native kernels.
- [ ] Utilizing zero-copy IPC (Inter-Process Communication) for cross-language data transfer.
- [ ] Verifying SIMD instruction set support (AVX-512 / NEON) via `pyarrow`.

---

## 4. Technical Appendix: Comprehensive CLI Reference Table
| Command / Flag | Purpose | Environment |
| :--- | :--- | :--- |
| `polars.read_csv(..., low_memory=True)` | Minimize peak RAM during ingestion | Polars |
| `duckdb.connect(":memory:")` | Initialize transient high-speed database | DuckDB |
| `pyarrow.parquet.write_table()` | Serialize data with Arrow-native metadata | Arrow |
| `SET memory_limit='8GB'` | Hard cap on analytics buffer pool | DuckDB |

---

## 5. Industrial Case Study: 1TB Log Analysis (Streaming Architecture)
**Objective:** Processing 1TB of raw JSON logs on a workstation with 64GB RAM.
1.  **Format Migration:** Convert raw JSON to Partitioned Parquet using DuckDB in-place conversion.
2.  **Schema Definition:** Strict typing of all columns to minimize Arrow memory footprint.
3.  **Streaming Aggregation:** Utilizing Polars `scan_parquet` with `streaming=True` to calculate sliding-window error rates.
4.  **Result Persistence:** Outputting the Gold-layer aggregates to a DuckDB persistent file for BI dashboarding.

---

## 6. Glossary of Data Science Workflow Terms
*   **Predicate Pushdown:** The process of filtering data at the scan level rather than loading all data into memory first.
*   **Zero-Copy:** Sharing data between processes or languages by referencing the same physical memory addresses.
*   **SIMD (Single Instruction, Multiple Data):** CPU hardware acceleration for performing the same operation on multiple data points at once.
*   **Lakehouse:** A hybrid data architecture combining the storage efficiency of a Data Lake with the ACID transactions of a Data Warehouse.

---

## 7. Mathematical Foundations of Compression
*   **Run-Length Encoding (RLE):** Storing sequences of identical values as `(value, count)`.
*   **Delta-Encoding:** Storing the difference between subsequent values (e.g., `[100, 101, 102]` stored as `[100, 1, 1]`).
*   **Bit-Packing:** Using the minimum number of bits required to represent a range of values (e.g., 3 bits for values 0-7).

---

## 8. Troubleshooting & Performance Verification
*   **OOM (Out of Memory) Check:** Verifying that `pl.collect()` is only called on the final, filtered result set.
*   **Type Coercion Failures:** Handling mismatched types across multiple Parquet files via `schema_overwrites`.
*   **Disk Spill Monitoring:** Checking DuckDB's `temp_directory` for signs of excessive disk spilling during large joins.

---
[Back to README](../../README.md)
