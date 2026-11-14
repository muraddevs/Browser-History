
from browser_history import BrowserHistory


def check_pointers(browser):
    assert browser._list.is_consistent()
    if browser._current is not None:
        assert any(node is browser._current for node in browser._list)


# Test 1: Going back too far
browser = BrowserHistory("google.com")
browser.visit("youtube.com")
assert browser.back(100) == "google.com"
assert browser.back(100) == "google.com"
check_pointers(browser)

# Test 2: Forward when already at the newest page
assert browser.forward(100) == "youtube.com"
assert browser.forward(1) == "youtube.com"
check_pointers(browser)

# Test 3: Visiting from the middle
browser = BrowserHistory("google.com")
browser.visit("youtube.com")
browser.visit("github.com")
browser.back(1)
browser.visit("netflix.com")
assert browser.urls() == ["google.com", "youtube.com", "netflix.com"]
assert browser.forward(5) == "netflix.com"
check_pointers(browser)

# Test 4: Capacity limit
browser = BrowserHistory("google.com", capacity=3)
browser.visit("youtube.com")
browser.visit("github.com")
browser.visit("netflix.com")
assert browser.urls() == ["youtube.com", "github.com", "netflix.com"]
check_pointers(browser)

# Test 5: Default capacity of 50
browser = BrowserHistory("page0")
for i in range(1, 120):
    browser.visit("page" + str(i))
assert len(browser) == 50
assert browser.urls()[0] == "page70"
check_pointers(browser)

# Test 6: Zero and negative steps
browser = BrowserHistory("google.com")
browser.visit("youtube.com")

assert browser.back(0) == "youtube.com"
assert browser.forward(0) == "youtube.com"

try:
    browser.back(-1)
    assert False, "negative steps should raise ValueError"
except ValueError:
    pass

try:
    browser.forward(-1)
    assert False, "negative steps should raise ValueError"
except ValueError:
    pass

assert browser.current_page()["url"] == "youtube.com"
check_pointers(browser)

# Test 7: Capacity of 1
browser = BrowserHistory("a.com", capacity=1)
browser.visit("b.com")
browser.visit("c.com")
assert browser.urls() == ["c.com"]
assert browser.back(5) == "c.com"
assert browser.forward(5) == "c.com"
check_pointers(browser)

# Test 8: Invalid capacity
try:
    BrowserHistory("a.com", capacity=0)
    assert False, "capacity 0 should raise ValueError"
except ValueError:
    pass

# Test 9: Current page information
browser = BrowserHistory("google.com")
browser.visit("youtube.com", "YouTube")
browser.visit("github.com")

browser.back(1)
page = browser.current_page()

assert page["url"] == "youtube.com"
assert page["title"] == "YouTube"
assert page["position"] == 2
assert page["total"] == 3
assert "visited_at" in page
check_pointers(browser)

print("All core navigation tests passed")