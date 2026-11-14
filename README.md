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

## Deliverables

- Source code (zip): Node class, doubly linked list, BrowserHistory driver
- Test suite covering edge cases (e.g. `back()` 100 times on a 2-page history, branching from the middle)
- Demo video (MP4, max 10 minutes)
- Report (PDF) with team names and IDs, class design, and testing approach

File names start with `Group<N>-ID <StudentID>-`, e.g. `Group6-ID 2345-Report.pdf`.
