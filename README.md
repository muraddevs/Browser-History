# Browser History Management

CSCI 2304 – Data Structures & Algorithms, group programming homework.

A browser history navigation and management system built on a doubly linked list
implemented from scratch (no built-in linked list or deque containers).

## Team

| Name | Student ID |
|------|------------|
|      |            |
|      |            |
|      |            |

## Required operations

- `BrowserHistory(homepage)`: start with a homepage as the current page
- `visit(url)`: drop forward history, append the new page, move the cursor to it
- `back(steps)` / `forward(steps)`: move up to `steps` pages, stopping at the ends; return the current URL
- `current_page()`: return the current URL and metadata without changing state
- `display_history()`: print head to tail, marking the current page with `[<]`
- Capacity limit (e.g. 50 pages): prune the oldest node when exceeded
- `delete_history()`: clear all pages
- Export / import history to and from `.txt` files
- Delete a specific URL and restore it later from a stack of deleted nodes

## Files

| File | What it holds |
|------|---------------|
| `node.py` | `Node`: one page (url, title, visited_at) with `prev` / `next` links |
| `doubly_linked_list.py` | `DoublyLinkedList` written from scratch: push, insert, unlink, truncate, clear, search |
| `stack.py` | `Stack` (singly linked, LIFO) used to keep deleted pages for restore |
| `browser_history.py` | `BrowserHistory`: navigation, capacity, display, delete/restore, export/import |
| `main.py` | Menu-driven program |
| `test_browser_history.py` | Unit tests (unittest) |
| `test_manual.py` | Quick assertion script for the core navigation |

## Running

Requires Python 3.8+ and no other packages.

```bash
python3 main.py                # capacity 50
python3 main.py --capacity 5   # small capacity to see pruning quickly
python3 -m unittest -v         # run all tests
```

## Design notes

- **List direction:** `head` is the oldest page and `tail` is the newest. `prev` points to the older page, `next` to the newer one.
- **Capacity:** after `visit()`, pages are pruned from the head (oldest) until the size is within the limit. If the active page is pruned, the cursor moves to the next newer page.
- **Delete a URL:** `delete_url(url)` removes every page with that URL. Each removed node is pushed onto the stack together with its old `prev` and `next` neighbours. If the active page is deleted, the cursor moves to the older neighbour (or the newer one if there is no older page).
- **Restore:** `restore()` pops the most recent deleted page and puts it back right after its old `prev` if that node is still in the list, otherwise right before its old `next`, otherwise at the tail. The cursor does not move unless the history was empty. If the history is full, the oldest page is pruned first so the restored page is kept.
- **Delete all:** `delete_history()` removes every page and empties the restore stack. The browser stays empty until the next `visit()` or import.
- **Export / import format:** plain text, oldest page first. Lines starting with `#` are comments, and `# current: N` saves the active position. Each page is `url<TAB>title<TAB>visited_at`. A file with only one URL per line also imports. Import replaces the whole history and clears the restore stack. It keeps only the newest pages if the file is over capacity, and leaves the history untouched if any line is invalid.

## Deliverables

- Source code (zip): Node class, doubly linked list, BrowserHistory driver
- Test suite covering edge cases (e.g. `back()` 100 times on a 2-page history, branching from the middle)
- Demo video (MP4, max 10 minutes)
- Report (PDF) with team names and IDs, class design, and testing approach

File names start with `Group<N>-ID <StudentID>-`, e.g. `Group6-ID 2345-Report.pdf`.
