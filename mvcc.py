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
        """Commit transaction"""
        tx = self.transactions[tx_id]
        
        # Apply writes
        with self.lock:
            for key, value in tx.write_set.items():
                self.version_store.write(key, value)
        
        tx.commit()
        self.committed_count += 1
        self.latencies.append(tx.duration_ms())
        del self.transactions[tx_id]
        return True


def test_basic_versioning():
    """Test 1: Basic versioning"""
    print("\n" + "="*60)
    print("TEST 1: Basic Versioning")
    print("="*60)
    
    store = VersionStore()
    v1 = store.write('account', 100)
    v2 = store.write('account', 150)
    v3 = store.write('account', 200)
    
    assert store.read('account', 1) == 100
    assert store.read('account', 2) == 150
    assert store.read('account', 3) == 200
    
    print("✅ Versioning works")


def test_snapshot_isolation():
    """Test 2: Snapshot isolation"""
    print("\n" + "="*60)
    print("TEST 2: Snapshot Isolation")
    print("="*60)
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    store.write('account', 1000)
    
    tx1 = mgr.begin_transaction()
    tx2 = mgr.begin_transaction()
    
    val1 = mgr.read(tx1, 'account')
    val2 = mgr.read(tx2, 'account')
    
    assert val1 == val2 == 1000
    print(f"✅ Snapshot isolation working")

 
def test_simple_commit():
    """Test 3: Simple commit"""
    print("\n" + "="*60)
    print("TEST 3: Simple Commit")
    print("="*60)
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    store.write('x', 100)
    
    tx = mgr.begin_transaction()
    val = mgr.read(tx, 'x')
    mgr.write(tx, 'x', val + 50)
    result = mgr.commit(tx)
    
    assert result == True
    assert store.read('x', store.get_current_version()) == 150
    
    print("✅ Simple commit works")


def test_transaction_isolation():
    """Test 4: Transaction isolation"""
    print("\n" + "="*60)
    print("TEST 4: Transaction Isolation")
    print("="*60)
    
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


if __name__ == '__main__':
    print("\n" + "="*70)
    print("DAY 1 COMMIT 3: Transaction Management")
    print("="*70)
    
    test_basic_versioning()
    test_snapshot_isolation()
    test_simple_commit()
    test_transaction_isolation()
    
    print("\n" + "="*70)
    print("ALL 4 TESTS PASSED! ✅")
    print("="*70)
