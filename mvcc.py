"""
Multi-Version Concurrency Control (MVCC) - Day 1 Part 1
Version storage system
"""

from collections import defaultdict
from datetime import datetime
import threading


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


def test_basic_versioning():
    """Test 1: Basic versioning works"""
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
    assert store.read('account', 10) == 200
    
    print("✅ Versioning works correctly")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("DAY 1 COMMIT 2: VersionStore Implementation")
    print("="*70)
    
    test_basic_versioning()
    
    print("\n" + "="*70)
    print("TEST PASSED! ✅")
    print("="*70)
