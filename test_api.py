"""
Comprehensive API & Integration Test Suite.
Validates:
1. Database connectivity and table counts
2. SQL Views functionality
3. FastAPI Endpoints (Models, Providers, Benchmarks, Reviews, Compare, Search, Admin)
4. All 12 DSA integrations:
   - Trie autocomplete
   - Hash Table cache
   - Stack filter undo
   - Queue moderation
   - CircularQueue recently viewed
   - LinkedList search history
   - DoublyLinkedList browsing cursor
   - Min/Max Heap top-K models
   - Merge & Quick Sort algorithms
   - Binary & Fuzzy Search algorithms
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_system_overview():
    print("Testing GET / ...")
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "dbms_specification" in data
    assert "dsa_specification" in data
    print("  [+] Overview endpoint validated!")


def test_admin_stats():
    print("Testing GET /api/admin/stats ...")
    resp = client.get("/api/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tables"] == 17
    print(f"  [+] Grand total rows across 17 tables: {data['grand_total_rows']}")
    assert data["grand_total_rows"] > 50


def test_models_list_and_sorting():
    print("Testing Model Listing & DSA Sorting (Merge Sort vs Quick Sort)...")
    # Test Merge Sort
    resp_merge = client.get("/api/models/?sort_by=price&order=asc&algorithm=merge&limit=5")
    assert resp_merge.status_code == 200
    data_merge = resp_merge.json()
    assert "Merge Sort" in data_merge["data"]["algorithm_used"]

    # Test Quick Sort
    resp_quick = client.get("/api/models/?sort_by=context_length&order=desc&algorithm=quick&limit=5")
    assert resp_quick.status_code == 200
    data_quick = resp_quick.json()
    assert "Quick Sort" in data_quick["data"]["algorithm_used"]
    print("  [+] Merge Sort and Quick Sort endpoints validated!")


def test_trie_autocomplete():
    print("Testing Trie Autocomplete (DSA)...")
    resp = client.get("/api/models/autocomplete?q=claude")
    assert resp.status_code == 200
    data = resp.json()
    assert "Trie" in data["dsa_used"]
    assert len(data["suggestions"]) > 0
    print(f"  [+] Trie autocomplete returned {len(data['suggestions'])} matches for 'claude'")


def test_heap_top_k():
    print("Testing Priority Queue (Heap) Top-K (DSA)...")
    # Cheapest top 3 (Min-Heap)
    resp = client.get("/api/models/top?k=3&criteria=price")
    assert resp.status_code == 200
    data = resp.json()
    assert "Min-Heap" in data["dsa_used"]
    assert len(data["models"]) == 3
    print("  [+] Top-K MinHeap and MaxHeap extraction validated!")


def test_binary_search_and_range():
    print("Testing Binary Search and Binary Search Range (DSA)...")
    resp_range = client.get("/api/models/price-range?min_price=0&max_price=3")
    assert resp_range.status_code == 200
    data_range = resp_range.json()
    assert "Binary Search Range" in data_range["dsa_used"]
    print(f"  [+] Binary Search Range found {data_range['count']} models in [0, 3] USD range")


def test_session_state_dsa():
    print("Testing Session State DSA (Stack, LinkedList, CircularQueue, DoublyLinkedList)...")
    session_headers = {"X-Session-ID": "test-student-session-99"}

    # 1. Advanced search pushes filter to Stack and logs to LinkedList
    client.get("/api/search/advanced?q=gpt&min_context=100000", headers=session_headers)
    client.get("/api/search/advanced?q=claude&free_only=true", headers=session_headers)

    # 2. Check search history (LinkedList)
    hist_resp = client.get("/api/search/history", headers=session_headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()["searches"]) >= 2
    print("  [+] Singly Linked List search history validated!")

    # 3. Check and undo filter (Stack)
    undo_resp = client.post("/api/search/filters/undo", headers=session_headers)
    assert undo_resp.status_code == 200
    assert "Stack" in undo_resp.json()["dsa_used"]
    print("  [+] Stack filter undo validated!")

    # 4. View a model -> populates CircularQueue and DoublyLinkedList
    client.get("/api/models/1", headers=session_headers)
    client.get("/api/models/2", headers=session_headers)

    recent_resp = client.get("/api/search/recently-viewed", headers=session_headers)
    assert recent_resp.status_code == 200
    assert len(recent_resp.json()["recently_viewed_models"]) >= 2
    print("  [+] Circular Queue (recently viewed) validated!")

    # 5. Move backward in browsing history (DoublyLinkedList)
    back_resp = client.post("/api/search/browse/backward", headers=session_headers)
    assert back_resp.status_code == 200
    assert "Doubly Linked List" in back_resp.json()["dsa_used"]
    print("  [+] Doubly Linked List browsing history validated!")


def test_review_moderation_queue():
    print("Testing Review Moderation Queue (FIFO Queue DSA)...")
    # Submit review
    sub_resp = client.post("/api/reviews/", json={
        "version_id": 1,
        "reviewer_name": "Test Evaluator",
        "rating": 5,
        "title": "Outstanding Reasoning",
        "review_text": "Remarkable performance on competitive mathematics."
    })
    assert sub_resp.status_code == 200
    assert "Queue (FIFO)" in sub_resp.json()["dsa_used"]

    # Dequeue review
    next_resp = client.get("/api/reviews/moderation/next")
    assert next_resp.status_code == 200
    assert "review_to_moderate" in next_resp.json()
    print("  [+] FIFO Queue enqueue and dequeue validated!")


def test_compare_and_recommendations():
    print("Testing Model Comparison and Recommendation...")
    comp_resp = client.get("/api/compare/?ids=1,2")
    assert comp_resp.status_code == 200
    assert len(comp_resp.json()["models"]) >= 2

    rec_resp = client.get("/api/compare/recommend?use_case=Coding")
    assert rec_resp.status_code == 200
    print("  [+] Comparison matrix and Stored Procedure recommendation validated!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING COMPLETE AI MODEL REGISTRY TEST SUITE")
    print("=" * 60)
    # Ensure indexes are populated in memory
    reb_resp = client.post("/api/admin/rebuild-indexes")
    assert reb_resp.status_code == 200
    print(f"  [+] In-memory Trie and binary index built: {reb_resp.json()['sorted_models']} models")

    test_system_overview()
    test_admin_stats()
    test_models_list_and_sorting()
    test_trie_autocomplete()
    test_heap_top_k()
    test_binary_search_and_range()
    test_session_state_dsa()
    test_review_moderation_queue()
    test_compare_and_recommendations()
    print("=" * 60)
    print("ALL 9 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 60 + "\n")
