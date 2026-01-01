"""
MVCC Interactive Demonstration
Run this to see how the database handles time travel and conflicts!
"""

import time
import threading
import random
from mvcc import VersionStore, TransactionManager

def print_header(title):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def demo_time_travel():
    """
    DEMO 1: SNAPSHOT ISOLATION (Time Travel)
    Shows how a transaction sees the database 'as it was' when it started,
    ignoring changes that happen afterwards.
    """
    print_header("DEMO 1: Snapshot Isolation (Time Travel)")
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    # 1. Setup initial state
    store.write("price", 100)
    print(f"Step 1: Initial Price set to $100 (Version {store.get_current_version()})")
    
    # 2. Start a long-running transaction (The "Old" View)
    tx_slow = mgr.begin_transaction()
    print(f"Step 2: Started Reader Transaction (View: Version {mgr.transactions[tx_slow].snapshot_version})")
    
    # 3. Meanwhile, someone else updates the price
    store.write("price", 200)
    store.write("price", 300)
    print(f"Step 3: Database updated! Current Price is now $300 (Version {store.get_current_version()})")
    
    # 4. The slow transaction reads the price
    value = mgr.read(tx_slow, "price")
    print(f"Step 4: Reader Transaction reads 'price'...")
    
    print("-" * 40)
    print(f"Real-time Value: $300")
    print(f"Reader Sees:     ${value}")
    print("-" * 40)
    
    if value == 100:
        print("✅ SUCCESS: The transaction successfully ignored the new updates!")
    else:
        print("❌ FAILURE: Isolation leaked.")

def demo_lost_update_prevention():
    """
    DEMO 2: CONFLICT DETECTION
    Shows two users trying to modify the same data at the same time.
    First committer wins. Second committer aborts.
    """
    print_header("DEMO 2: Write-Write Conflict (The Race)")
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    store.write("tickets_left", 1)
    print("Initial State: 1 Ticket left")
    
    # User A and User B both load the page
    tx_a = mgr.begin_transaction()
    tx_b = mgr.begin_transaction()
    print("Step 1: Alice and Bob both start transactions")
    
    # Both see 1 ticket
    tickets_a = mgr.read(tx_a, "tickets_left")
    tickets_b = mgr.read(tx_b, "tickets_left")
    print(f"Step 2: Alice sees {tickets_a}, Bob sees {tickets_b}")
    
    # Alice buys the ticket
    print("Step 3: Alice buys the ticket (Decrements to 0)")
    mgr.write(tx_a, "tickets_left", tickets_a - 1)
    
    # Bob buys the ticket (Thinking there is still 1 left)
    print("Step 4: Bob buys the ticket (Decrements to 0)")
    mgr.write(tx_b, "tickets_left", tickets_b - 1)
    
    # Alice commits
    success_a = mgr.commit(tx_a)
    print(f"Step 5: Alice commits... {'✅ Success' if success_a else '❌ Failed'}")
    
    # Bob commits
    success_b = mgr.commit(tx_b)
    print(f"Step 6: Bob commits...   {'✅ Success' if success_b else '❌ Failed (Conflict Detected!)'}")
    
    final = store.read("tickets_left", store.get_current_version())
    print(f"\nFinal State: {final} Tickets left")
    
    if not success_b and final == 0:
        print("✅ SUCCESS: Double booking prevented!")

def demo_atomic_transfer():
    """
    DEMO 3: ATOMICITY
    Shows a bank transfer. Either both changes happen, or neither.
    """
    print_header("DEMO 3: Atomic Bank Transfer")
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    store.write("alice", 500)
    store.write("bob", 500)
    print("Initial: Alice=$500, Bob=$500")
    
    print("\n--- Scenarion A: Successful Transfer ---")
    tx1 = mgr.begin_transaction()
    mgr.write(tx1, "alice", 400)
    mgr.write(tx1, "bob", 600)
    mgr.commit(tx1)
    print(f"Transferred $100. Result: Alice=${store.read('alice', store.get_current_version())}, Bob=${store.read('bob', store.get_current_version())}")
    
    print("\n--- Scenario B: Broken Transaction (Simulated Crash) ---")
    tx2 = mgr.begin_transaction()
    
    # 1. Take money from Alice
    current_alice = mgr.read(tx2, "alice")
    mgr.write(tx2, "alice", current_alice - 100)
    print("Step 1: Debited Alice (in memory)")
    
    # 2. Something goes wrong before crediting Bob
    print("Step 2: ERROR! Transaction aborted before crediting Bob")
    mgr.transactions[tx2].abort() # Manual abort
    
    # Check data
    final_alice = store.read("alice", store.get_current_version())
    final_bob = store.read("bob", store.get_current_version())
    
    print(f"Final Result: Alice=${final_alice}, Bob=${final_bob}")
    
    if final_alice == 400: # Value from Scenario A
        print("✅ SUCCESS: The failed transaction rolled back perfectly.")

def demo_high_concurrency():
    """
    DEMO 4: HIGH CONCURRENCY SIMULATION
    Simulates a stock market with many traders.
    """
    print_header("DEMO 4: Stock Market Simulation")
    
    store = VersionStore()
    mgr = TransactionManager(store)
    
    # Setup: Apple (AAPL) stock price
    store.write("AAPL", 150.00)
    
    print("Starting 5 concurrent traders...")
    results = []
    
    def trader(name, price_change):
        tx = mgr.begin_transaction()
        # Simulate think time
        time.sleep(random.uniform(0.001, 0.005))
        
        curr = mgr.read(tx, "AAPL")
        mgr.write(tx, "AAPL", curr + price_change)
        
        # Simulate network latency
        time.sleep(random.uniform(0.001, 0.005))
        
        success = mgr.commit(tx)
        results.append((name, success))
    
    threads = [
        threading.Thread(target=trader, args=("Trader A", +1.0)),
        threading.Thread(target=trader, args=("Trader B", +2.0)),
        threading.Thread(target=trader, args=("Trader C", -1.0)),
        threading.Thread(target=trader, args=("Trader D", +5.0)),
        threading.Thread(target=trader, args=("Trader E", -0.5)),
    ]
    
    for t in threads: t.start()
    for t in threads: t.join()
    
    success_count = sum(1 for _, r in results if r)
    fail_count = sum(1 for _, r in results if not r)
    
    print(f"\nSimulation Complete:")
    for name, res in results:
        status = "COMMITTED" if res else "ABORTED (Retry needed)"
        print(f"  {name}: {status}")
        
    print(f"\nSummary: {success_count} succeeded, {fail_count} failed due to conflicts.")
    print("Note: In a real system, the aborted traders would auto-retry.")

if __name__ == "__main__":
    demo_time_travel()
    time.sleep(1)
    demo_lost_update_prevention()
    time.sleep(1)
    demo_atomic_transfer()
    time.sleep(1)
    demo_high_concurrency()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)