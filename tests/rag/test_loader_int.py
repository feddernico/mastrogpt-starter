import os
import time
import requests as req

def test_loader_int():
    base_url = os.environ.get("OPSDEV_HOST") + "/api/my/rag/loader"

    # Drop collection if API supports it via input or params
    args = {"input": "!!test"}
    req.post(base_url, json=args)

    # Insert first message
    args = {"state": "test:30", "input": "@test"}
    res = req.post(base_url, json=args).json()
    assert res.get("state").startswith("test:")

    args = {"state": "test:30", "input": "Hello, loader."}
    res = req.post(base_url, json=args).json()
    assert "Inserted" in res.get("output")

    # Insert second message
    args = {"state": "test:30", "input": "Hello again."}
    res = req.post(base_url, json=args).json()
    assert "Inserted" in res.get("output")

    # Insert third message
    args = {"state": "test:30", "input": "Goodbye, loader."}
    res = req.post(base_url, json=args).json()
    assert "Inserted" in res.get("output")

    # Search for "Hello"
    args = {"state": "test:30", "input": "*Hello"}
    found = False
    for i in range(10):
        res = req.post(base_url, json=args).json()
        out = res.get("output", "")
        if out.startswith("Found:") and out.count("Hello") >= 2:
            found = True
            print(f"✅ Found at attempt {i}")
            break
        time.sleep(0.5)
    assert found, "Expected at least 2 matches for 'Hello'"

    # Delete items with substring "Hello"
    args = {"state": "test:30", "input": "!Hello"}
    res = req.post(base_url, json=args).json()
    assert "Deleted" in res.get("output")

    # Delete items with substring "Goodbye"
    args = {"state": "test:30", "input": "!Goodbye"}
    res = req.post(base_url, json=args).json()
    assert "Deleted" in res.get("output")

    # Check that search now fails
    args = {"state": "test:30", "input": "*Hello"}
    res = req.post(base_url, json=args).json()
    assert "Not found" in res.get("output")
