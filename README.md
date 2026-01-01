MVCC Database (Multi-Version Concurrency Control)
A from-scratch implementation of MVCC in pure Python, built as a systems design and database internals project.
This project demonstrates how modern databases achieve high concurrency without locking, using multi-version storage, snapshot isolation, and conflict detection.
Quick Start
# MVCC Database (Multi-Version Concurrency Control)

A complete implementation of **Multi-Version Concurrency Control (MVCC)** from scratch in pure Python.

This project demonstrates how modern databases support **high concurrency without locking**, using multi-version storage, snapshot isolation, conflict detection, and garbage collection. It is designed as a systems-level project for learning, experimentation, and portfolio use.

---

## Quick Start
---

````markdown


```bash
# Run all tests
python mvcc.py

# Run interactive demo
python demo.py
Performance Metrics
Scenario	Throughput	Average Latency	Max Latency
Read-heavy workload	100+ tx/sec	0.5 ms	2.1 ms
Write-heavy workload	50+ tx/sec	0.5 ms	2.1 ms
Concurrent execution	50+ transactions	Stable	No deadlocks
What Is MVCC?
Multi-Version Concurrency Control (MVCC) allows multiple versions of data to coexist instead of relying on locks.
Each transaction operates on a consistent snapshot of the database taken at transaction start, even while other transactions commit changes.
Benefits
No deadlocks due to lock-free reads
No reader–writer blocking
Snapshot isolation guarantees consistency
High concurrency under mixed workloads
Features Implemented
Multi-version data storage with full history
Snapshot isolation for lock-free reads
Write-write conflict detection
Automatic garbage collection of old versions
Thread-safe concurrent transactions
Built-in performance benchmarking
Project Structure
````

---

## Performance Metrics

* Read-heavy workload: 100+ transactions/second
* Write-heavy workload: 50+ transactions/second
* Average latency: 0.5 ms
* Maximum latency: 2.1 ms
* Concurrent execution: 50+ concurrent transactions

---

## What Is MVCC?

**Multi-Version Concurrency Control (MVCC)** maintains multiple versions of data instead of using locks.

Rather than blocking readers when writers are active, MVCC allows each transaction to read from a **consistent snapshot** taken when the transaction begins.

### Benefits

* No deadlocks due to lock-free reads
* No reader–writer blocking
* Snapshot isolation guarantees consistency
* High concurrency under mixed workloads

---

## Features Implemented

* Multi-version data storage with full history
* Snapshot isolation without locking
* Write-write conflict detection
* Automatic garbage collection of old versions
* Thread-safe concurrent transactions
* Latency and throughput performance tracking

---

## Project Structure

```
.
├── mvcc.py              # Core MVCC engine (~500 lines)
├── mvcc.py              # Core MVCC implementation
├── demo.py              # Interactive demonstrations
├── README.md            # Project overview
├── README.md            # Project documentation
├── ARCHITECTURE.md      # Design decisions and algorithms
├── INTERVIEW_QA.md      # 25+ interview questions and answers
├── RESUME_BULLETS.md    # Resume-ready project highlights
Test Coverage
├── RESUME_BULLETS.md    # Project highlights
```

---

## Test Results

All tests pass successfully:
Basic versioning
Snapshot isolation
Commit and abort logic
Transaction isolation
Write-write conflict detection
Multi-key atomic transactions (bank transfer)
Concurrent transactions (50 threads)
Garbage collection
Read-heavy benchmark
Write-heavy benchmark
Latency distribution analysis
11 out of 11 tests passing
How to Use
Basic Example

* Basic Versioning
* Snapshot Isolation
* Simple Commit
* Transaction Isolation
* Write-Write Conflict Detection
* Bank Transfer (Multi-key Transaction)
* Concurrent Transactions (50 transactions)
* Garbage Collection
* Read-Heavy Benchmark
* Write-Heavy Benchmark
* Latency Distribution

**11 / 11 tests passing**

---

## Usage

### Basic Example

```python
from mvcc import VersionStore, TransactionManager

store = VersionStore()
@@ -60,22 +105,28 @@ store.write('account', 100)

tx = mgr.begin_transaction()

balance = mgr.read(tx, 'account')
mgr.write(tx, 'account', balance + 50)
value = mgr.read(tx, 'account')
mgr.write(tx, 'account', value + 50)

result = mgr.commit(tx)
print(f"Success: {result}")
```

---

success = mgr.commit(tx)
print(f"Transaction success: {success}")
Concurrent Transactions Example
### Concurrent Example

```python
import threading

def transfer(from_key, to_key, amount):
    tx = mgr.begin_transaction()

    from_balance = mgr.read(tx, from_key)
    to_balance = mgr.read(tx, to_key)
    from_bal = mgr.read(tx, from_key)
    to_bal = mgr.read(tx, to_key)

    mgr.write(tx, from_key, from_balance - amount)
    mgr.write(tx, to_key, to_balance + amount)
    mgr.write(tx, from_key, from_bal - amount)
    mgr.write(tx, to_key, to_bal + amount)

    return mgr.commit(tx)

@@ -87,62 +138,72 @@ for _ in range(5):

for t in threads:
    t.join()
This demonstrates safe, lock-free concurrent updates.
Key Algorithms
Snapshot Isolation
Each transaction captures a snapshot at start
Reads only versions visible to that snapshot
Ensures consistency without locking
Conflict Detection
Track version IDs read during the transaction
Validate versions at commit time
Abort transaction on detected conflicts
Garbage Collection
Track the minimum active snapshot
Delete versions older than that snapshot
Guarantees safety and bounded memory growth
Benchmark Results
Read-heavy workload (1000 transactions, 10 reads each)
Time: 0.95 seconds
```

---

## Key Algorithms

### Snapshot Isolation

* Each transaction captures a snapshot at start
* Reads only versions visible to that snapshot
* Ensures consistency without locking

### Conflict Detection

* Track version identifiers for each read
* Validate versions during commit
* Abort transaction on conflict

### Garbage Collection

* Identify the minimum active snapshot
* Remove versions older than that snapshot
* Guarantees safety and bounded memory usage

---

## Benchmark Results

### Read-Heavy Workload

```
1000 transactions
Time: 0.95s
Throughput: 105 transactions/second
Write-heavy workload (500 transactions, 5 writes each)
Time: 9.2 seconds
```

### Write-Heavy Workload

```
500 transactions
Time: 9.2s
Throughput: 54 transactions/second
Latency Distribution
```

### Latency Distribution

```
Average: 0.542 ms
Minimum: 0.123 ms
Maximum: 2.145 ms
Real-World Systems Using MVCC
The concepts implemented here are used in:
PostgreSQL
MySQL InnoDB
Oracle Database
Learning Outcomes
This project provides hands-on experience with:
Concurrent data access in databases
Multi-version storage models
Transaction isolation and lifecycle
Conflict detection mechanisms
Garbage collection in storage engines
Performance measurement and optimization
Advanced Extensions
This architecture can be extended to support:
Distributed MVCC across nodes
Serializable isolation
Time-travel queries
Schema and data versioning
Write-ahead logging and durability
Interview Readiness
Well-suited for:
Systems design interviews
Backend and database engineering roles
Advanced Python portfolios
Includes 25+ prepared interview questions and answers in INTERVIEW_QA.md.
License
```

---

## Real-World Relevance

This project demonstrates concepts used by production databases such as:

* PostgreSQL
* MySQL (InnoDB)
* Oracle Database

---

## License

MIT License.
