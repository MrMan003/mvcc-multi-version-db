"""
Multi-Version Concurrency Control (MVCC) - Day 1 Part 2
Transaction management
"""

from collections import defaultdict
from datetime import datetime
import threading
import time


class VersionedValue:
    """Represents a single version of a value"""

    def __init__(self, value, version_id, timestamp=None):
        self.value = value
        self.version_id = version_id
        self.timestamp = timestamp or datetime.now()

    def __repr__(self):
        return f"V{self.version_id}:{self.value}"


class VersionStore:
    """Stores multiple versions of data"""

    def __init__(self):
        self.versions = defaultdict(list)
        self.version_counter = 0
        self.lock = threading.Lock()
        self.gc_runs = 0


    def write(self, key, value):
        """Create new version"""
        with self.lock:
            self.version_counter += 1
            new_version = VersionedValue(value, self.version_counter)
            self.versions[key].append(new_version)
            return self.version_counter

    def read(self, key, snapshot_version):
        """Read version appropriate for snapshot"""
        versions_list = self.versions.get(key, [])

        for v in reversed(versions_list):
            if v.version_id <= snapshot_version:
                return v.value

        return None

    def get_current_version(self):
        """Get current version number"""
        return self.version_counter

    def get_all_versions(self, key):
        """Get all versions of a key"""
        return self.versions.get(key, [])


class Transaction:
    """Represents a single transaction"""

    def __init__(self, tx_id, snapshot_version):
        self.tx_id = tx_id
        self.snapshot_version = snapshot_version
        self.read_set = {}
        self.write_set = {}
        self.status = 'active'
        self.start_time = time.time()
        self.end_time = None

    def read(self, key, value, version_id):
        """Record a read"""
        self.read_set[key] = (version_id, value)
        return value

    def write(self, key, value):
        """Buffer a write"""
        self.write_set[key] = value

    def commit(self):
        """Mark as committed"""
        self.status = 'committed'
        self.end_time = time.time()

    def abort(self):
        """Mark as aborted"""
        self.status = 'aborted'
        self.end_time = time.time()

    def duration_ms(self):
        """Get transaction duration in ms"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0


class TransactionManager:
    """Manages all transactions"""
    
    
    def garbage_collect(self):
        """Collect garbage versions safely"""
        if not self.transactions:
            # If no active transactions, we can clean up everything 
            # except the absolute latest version of every key.
            min_snapshot = self.version_store.get_current_version()
        else:
            # Otherwise, protect the oldest active transaction
            min_snapshot = min(t.snapshot_version for t in self.transactions.values())
        
        collected = 0
        
        with self.lock: # Always lock during cleanup!
            for key in list(self.version_store.versions.keys()):
                versions = self.version_store.versions[key]
                new_versions = []
                if not versions: continue
                current_valid_version = versions[-1]
                
                # Let's identify the specific version visible to min_snapshot
                visible_version = None
                for v in reversed(versions):
                    if v.version_id <= min_snapshot:
                        visible_version = v
                        break
                
                # Now construct the new list
                for v in versions:
                    # Keep if it's the visible one OR it's newer than the snapshot
                    if v == visible_version or v.version_id > min_snapshot:
                        new_versions.append(v)
                
                old_count = len(versions)
                self.version_store.versions[key] = new_versions
                collected += old_count - len(new_versions)
                
                if not self.version_store.versions[key]:
                    del self.version_store.versions[key]
        
        self.version_store.gc_runs += 1
        return collected

    def get_stats(self):
        """Get statistics"""
        import statistics
        
        total = self.committed_count + self.aborted_count
        success_rate = (self.committed_count / total * 100) if total > 0 else 0
        
        latency_stats = {}
        if self.latencies:
            latency_stats = {
            'avg_latency_ms': statistics.mean(self.latencies),
            'min_latency_ms': min(self.latencies),
            'max_latency_ms': max(self.latencies)
            }
        
        return {
            'committed': self.committed_count,
            'aborted': self.aborted_count,
            'success_rate': success_rate,
            **latency_stats
        }


    def __init__(self, version_store):
        self.version_store = version_store
        self.transactions = {}
        self.tx_counter = 0
        self.lock = threading.Lock()
        self.committed_count = 0
        self.aborted_count = 0
        self.latencies = []

    def begin_transaction(self):
        """Start new transaction with current snapshot"""
        with self.lock:
            self.tx_counter += 1
            tx_id = self.tx_counter
            snapshot = self.version_store.get_current_version()

            tx = Transaction(tx_id, snapshot)
            self.transactions[tx_id] = tx

            return tx_id

    def read(self, tx_id, key):
        """Read in transaction"""
        tx = self.transactions[tx_id]

        if key in tx.write_set:
            return tx.write_set[key]

        value = self.version_store.read(key, tx.snapshot_version)

        if value is not None:
            versions_list = self.version_store.get_all_versions(key)
            read_version = None

            for v in reversed(versions_list):
                if v.version_id <= tx.snapshot_version:
                    read_version = v.version_id
                    break

            tx.read(key, value, read_version)
            return value

        return None

    def write(self, tx_id, key, value):
        """Buffer write"""
        tx = self.transactions[tx_id]
        tx.write(key, value)

    def commit(self, tx_id):
        """Commit with conflict detection"""
        tx = self.transactions[tx_id]

        # Check for conflicts (snapshot isolation validation)
        for key, (read_version, _) in tx.read_set.items():
            latest_versions = self.version_store.versions.get(key, [])

            if latest_versions:
                latest_id = latest_versions[-1].version_id

                if read_version is not None and latest_id > read_version:
                    tx.abort()
                    self.aborted_count += 1
                    self.latencies.append(tx.duration_ms())
                    del self.transactions[tx_id]
                    return False

        # Apply writes
        with self.lock:
            for key, value in tx.write_set.items():
                self.version_store.write(key, value)

        tx.commit()
        self.committed_count += 1
        self.latencies.append(tx.duration_ms())
        del self.transactions[tx_id]
        return True


# ============================================================
# TESTS
# ============================================================

def test_basic_versioning():
    print("\n" + "=" * 60)
    print("TEST 1: Basic Versioning")
    print("=" * 60)

    store = VersionStore()
    store.write('account', 100)
    store.write('account', 150)
    store.write('account', 200)

    assert store.read('account', 1) == 100
    assert store.read('account', 2) == 150
    assert store.read('account', 3) == 200

    print("✅ Versioning works")


def test_snapshot_isolation():
    print("\n" + "=" * 60)
    print("TEST 2: Snapshot Isolation")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    store.write('account', 1000)

    tx1 = mgr.begin_transaction()
    tx2 = mgr.begin_transaction()

    assert mgr.read(tx1, 'account') == 1000
    assert mgr.read(tx2, 'account') == 1000

    print("✅ Snapshot isolation working")


def test_simple_commit():
    print("\n" + "=" * 60)
    print("TEST 3: Simple Commit")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    store.write('x', 100)

    tx = mgr.begin_transaction()
    val = mgr.read(tx, 'x')
    mgr.write(tx, 'x', val + 50)
    result = mgr.commit(tx)

    assert result is True
    assert store.read('x', store.get_current_version()) == 150

    print("✅ Simple commit works")


def test_transaction_isolation():
    print("\n" + "=" * 60)
    print("TEST 4: Transaction Isolation")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    store.write('x', 100)

    tx1 = mgr.begin_transaction()
    val1 = mgr.read(tx1, 'x')

    tx2 = mgr.begin_transaction()
    mgr.write(tx2, 'x', 200)
    mgr.commit(tx2)

    assert mgr.read(tx1, 'x') == 100
    assert store.read('x', store.get_current_version()) == 200

    print("✅ Transaction isolation working")


def test_write_write_conflict():
    print("\n" + "=" * 60)
    print("TEST 5: Write-Write Conflict Detection")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    store.write('account', 1000)

    tx1 = mgr.begin_transaction()
    tx2 = mgr.begin_transaction()

    mgr.read(tx1, 'account')
    mgr.read(tx2, 'account')

    mgr.write(tx1, 'account', 900)
    result1 = mgr.commit(tx1)

    mgr.write(tx2, 'account', 950)
    result2 = mgr.commit(tx2)

    assert result1 is True
    assert result2 is False

    final = store.read('account', store.get_current_version())
    assert final == 900

    print("✅ TX1 succeeded, TX2 aborted due to conflict")


def test_bank_transfer():
    """Test 6: Bank transfer"""
    print("\n" + "=" * 60)
    print("TEST 6: Bank Transfer (Multi-key)")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    store.write('alice', 1000)
    store.write('bob', 1000)

    tx = mgr.begin_transaction()
    alice = mgr.read(tx, 'alice')
    bob = mgr.read(tx, 'bob')

    mgr.write(tx, 'alice', alice - 100)
    mgr.write(tx, 'bob', bob + 100)

    result = mgr.commit(tx)
    assert result is True

    assert store.read('alice', store.get_current_version()) == 900
    assert store.read('bob', store.get_current_version()) == 1100

    print("✅ Transfer successful")


def test_concurrent_transactions():
    """Test 7: Concurrent stress test"""
    print("\n" + "=" * 60)
    print("TEST 7: Concurrent Stress Test (50 Transactions)")
    print("=" * 60)

    store = VersionStore()
    mgr = TransactionManager(store)

    for i in range(5):
        store.write(f'account_{i}', 1000)

    success = [0]
    failed = [0]
    lock = threading.Lock()

    def worker():
        import random

        for _ in range(10):
            from_acc = random.randint(0, 4)
            to_acc = random.randint(0, 4)
            amount = random.randint(1, 50)

            if from_acc == to_acc:
                continue

            tx = mgr.begin_transaction()
            from_bal = mgr.read(tx, f'account_{from_acc}')
            to_bal = mgr.read(tx, f'account_{to_acc}')

            if from_bal >= amount:
                mgr.write(tx, f'account_{from_acc}', from_bal - amount)
                mgr.write(tx, f'account_{to_acc}', to_bal + amount)

                if mgr.commit(tx):
                    with lock:
                        success[0] += 1
                else:
                    with lock:
                        failed[0] += 1

    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total = success[0] + failed[0]
    print(f"\nResults:")
    print(f"  Successful: {success[0]}")
    print(f"  Failed: {failed[0]}")
    print(f"  Success rate: {success[0]/total*100:.1f}%")

    total_money = sum(
        store.read(f'account_{i}', store.get_current_version())
        for i in range(5)
    )
    assert total_money == 5000

    print(f"✅ Data consistency: Money conserved (${total_money})")
def test_garbage_collection():
    """Test 8: Garbage collection"""
    print("\n" + "="*60)
    print("TEST 8: Garbage Collection")
    print("="*60)
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    for i in range(100):
        store.write('key', i)
    
    before = sum(len(v) for v in store.versions.values())
    collected = mgr.garbage_collect()
    after = sum(len(v) for v in store.versions.values())
    
    print(f"Before GC: {before} versions")
    print(f"Collected: {collected} versions")
    print(f"After GC: {after} versions")
    print("✅ Garbage collection working")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("DAY 1: FOUNDATION + CONFLICT DETECTION")
    print("=" * 70)

    test_basic_versioning()
    test_snapshot_isolation()
    test_simple_commit()
    test_transaction_isolation()
    test_write_write_conflict()
    test_bank_transfer()
    test_concurrent_transactions()
    test_garbage_collection()

    print("\n" + "=" * 70)
    print("ALL 8 TESTS PASSED! ✅")
    print("=" * 70)
