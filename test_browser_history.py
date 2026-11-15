"""Unit tests for the browser history project.

Run:  python3 -m unittest -v
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from browser_history import BrowserHistory
from doubly_linked_list import DoublyLinkedList
from node import Node
from stack import Stack


def make_browser(*urls, capacity=50):
    """Browser whose history is exactly `urls`, with the cursor on the last one."""
    browser = BrowserHistory(urls[0], capacity=capacity)
    for url in urls[1:]:
        browser.visit(url)
    return browser


class HistoryTestCase(unittest.TestCase):

    def assertValid(self, browser):
        """Check prev/next links, size, and that the cursor is a node in the list."""
        self.assertTrue(browser._list.is_consistent(), "prev/next pointers are broken")
        if browser._current is None:
            self.assertEqual(len(browser), 0, "cursor is None but the list is not empty")
        else:
            self.assertTrue(browser._list.contains(browser._current), "cursor is not in the list")

    def current_url(self, browser):
        page = browser.current_page()
        return page["url"] if page else None


class TestStack(unittest.TestCase):

    def test_last_in_first_out(self):
        stack = Stack()
        for value in (1, 2, 3):
            stack.push(value)
        self.assertEqual(len(stack), 3)
        self.assertEqual(stack.peek(), 3)
        self.assertEqual([stack.pop(), stack.pop(), stack.pop()], [3, 2, 1])
        self.assertTrue(stack.is_empty())

    def test_pop_and_peek_on_empty_stack_raise(self):
        stack = Stack()
        with self.assertRaises(IndexError):
            stack.pop()
        with self.assertRaises(IndexError):
            stack.peek()

    def test_iterates_from_top(self):
        stack = Stack()
        for value in "abc":
            stack.push(value)
        self.assertEqual(list(stack), ["c", "b", "a"])
        stack.clear()
        self.assertEqual(list(stack), [])
        self.assertEqual(len(stack), 0)


class TestDoublyLinkedList(unittest.TestCase):

    def test_insert_and_unlink_keep_links_consistent(self):
        dll = DoublyLinkedList()
        a, b, c, d = Node("a"), Node("b"), Node("c"), Node("d")
        dll.push_back(b)
        dll.push_front(a)
        dll.insert_after(b, d)
        dll.insert_before(d, c)
        self.assertEqual([n.url for n in dll], ["a", "b", "c", "d"])
        self.assertTrue(dll.is_consistent())

        dll.unlink(a)
        dll.unlink(d)
        self.assertEqual([n.url for n in dll], ["b", "c"])
        self.assertIs(dll.head, b)
        self.assertIs(dll.tail, c)
        self.assertTrue(dll.is_consistent())

    def test_contains_uses_identity(self):
        dll = DoublyLinkedList()
        inside = Node("same.com")
        dll.push_back(inside)
        self.assertTrue(dll.contains(inside))
        self.assertFalse(dll.contains(Node("same.com")))

    def test_node_at_from_both_ends(self):
        dll = DoublyLinkedList()
        for i in range(7):
            dll.push_back(Node(str(i)))
        self.assertEqual([dll.node_at(i).url for i in range(7)], [str(i) for i in range(7)])
        with self.assertRaises(IndexError):
            dll.node_at(7)


class TestNavigation(HistoryTestCase):

    def test_back_100_times_on_two_pages(self):
        browser = make_browser("a.com", "b.com")
        for _ in range(100):
            url = browser.back(1)
        self.assertEqual(url, "a.com")
        self.assertEqual(browser.urls(), ["a.com", "b.com"])
        self.assertValid(browser)

    def test_forward_100_times_on_two_pages(self):
        browser = make_browser("a.com", "b.com")
        browser.back(1)
        for _ in range(100):
            url = browser.forward(1)
        self.assertEqual(url, "b.com")
        self.assertValid(browser)

    def test_branching_from_the_middle_drops_forward_history(self):
        browser = make_browser("a.com", "b.com", "c.com", "d.com")
        self.assertEqual(browser.back(2), "b.com")
        browser.visit("x.com")
        self.assertEqual(browser.urls(), ["a.com", "b.com", "x.com"])
        self.assertEqual(browser.forward(10), "x.com")
        self.assertEqual(browser.back(1), "b.com")
        self.assertValid(browser)

    def test_branching_from_the_first_page(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.back(50)
        browser.visit("x.com")
        self.assertEqual(browser.urls(), ["a.com", "x.com"])
        self.assertValid(browser)

    def test_current_page_does_not_change_state(self):
        browser = make_browser("a.com", "b.com")
        first = browser.current_page()
        second = browser.current_page()
        self.assertEqual(first, second)
        self.assertEqual(browser.urls(), ["a.com", "b.com"])

    def test_capacity_prunes_oldest(self):
        browser = make_browser("p0", "p1", "p2", "p3", "p4", capacity=3)
        self.assertEqual(browser.urls(), ["p2", "p3", "p4"])
        self.assertEqual(browser.back(10), "p2")
        self.assertValid(browser)

    def test_bad_input_is_rejected(self):
        browser = make_browser("a.com")
        for bad_url in ("", "   ", "has space.com", None, 42):
            with self.assertRaises(ValueError):
                browser.visit(bad_url)
        for bad_steps in (-1, 1.5, "2", True):
            with self.assertRaises(ValueError):
                browser.back(bad_steps)
        self.assertEqual(browser.urls(), ["a.com"])


class TestDisplayHistory(HistoryTestCase):

    def test_marks_only_the_active_page(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.back(1)
        with redirect_stdout(io.StringIO()) as out:
            text = browser.display_history()
        self.assertEqual(out.getvalue().rstrip("\n"), text)

        lines = text.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(text.count("[<]"), 1)
        self.assertIn("b.com", lines[1])
        self.assertTrue(lines[1].endswith("[<]"))
        self.assertIn("a.com", lines[0])  # oldest first
        self.assertIn("c.com", lines[2])

    def test_empty_history(self):
        browser = make_browser("a.com")
        browser.delete_history()
        self.assertEqual(browser.format_history(), "(history is empty)")


class TestDeleteHistory(HistoryTestCase):

    def test_clears_pages_and_cursor(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.delete_url("b.com")
        self.assertEqual(browser.delete_history(), 2)
        self.assertEqual(len(browser), 0)
        self.assertIsNone(browser.current_page())
        self.assertIsNone(browser.back(1))
        self.assertIsNone(browser.forward(1))
        self.assertEqual(browser.deleted_urls(), [])
        self.assertIsNone(browser.restore())
        self.assertValid(browser)

    def test_visit_after_clearing_starts_new_history(self):
        browser = make_browser("a.com", "b.com")
        browser.delete_history()
        browser.visit("new.com")
        self.assertEqual(browser.urls(), ["new.com"])
        self.assertEqual(self.current_url(browser), "new.com")
        self.assertValid(browser)


class TestDeleteAndRestore(HistoryTestCase):

    def test_delete_middle_page_and_restore_in_place(self):
        browser = make_browser("a.com", "b.com", "c.com")
        self.assertEqual(browser.delete_url("b.com"), 1)
        self.assertEqual(browser.urls(), ["a.com", "c.com"])
        self.assertEqual(browser.deleted_urls(), ["b.com"])
        self.assertValid(browser)

        self.assertEqual(browser.restore(), "b.com")
        self.assertEqual(browser.urls(), ["a.com", "b.com", "c.com"])
        self.assertEqual(browser.deleted_urls(), [])
        self.assertValid(browser)

    def test_delete_head_and_tail(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.back(1)
        browser.delete_url("a.com")
        browser.delete_url("c.com")
        self.assertEqual(browser.urls(), ["b.com"])
        self.assertValid(browser)

        browser.restore()  # c.com goes back after b.com
        browser.restore()  # a.com goes back before b.com
        self.assertEqual(browser.urls(), ["a.com", "b.com", "c.com"])
        self.assertValid(browser)

    def test_restore_is_last_in_first_out(self):
        browser = make_browser("a.com", "b.com", "c.com", "d.com")
        browser.delete_url("b.com")
        browser.delete_url("d.com")
        self.assertEqual(browser.deleted_urls(), ["d.com", "b.com"])
        self.assertEqual(browser.restore(), "d.com")
        self.assertEqual(browser.restore(), "b.com")
        self.assertEqual(browser.urls(), ["a.com", "b.com", "c.com", "d.com"])

    def test_deleting_the_active_page_moves_cursor_back(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.back(1)
        browser.delete_url("b.com")
        self.assertEqual(self.current_url(browser), "a.com")
        self.assertValid(browser)

    def test_deleting_the_active_first_page_moves_cursor_forward(self):
        browser = make_browser("a.com", "b.com")
        browser.back(1)
        browser.delete_url("a.com")
        self.assertEqual(self.current_url(browser), "b.com")
        self.assertValid(browser)

    def test_restore_does_not_move_cursor(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.delete_url("c.com")
        self.assertEqual(self.current_url(browser), "b.com")
        browser.restore()
        self.assertEqual(self.current_url(browser), "b.com")
        self.assertEqual(browser.forward(1), "c.com")

    def test_delete_removes_every_copy_of_a_url(self):
        browser = make_browser("x.com", "a.com", "x.com", "x.com", "b.com", "x.com")
        self.assertEqual(browser.delete_url("x.com"), 4)
        self.assertEqual(browser.urls(), ["a.com", "b.com"])
        self.assertValid(browser)

        for _ in range(4):
            browser.restore()
        self.assertEqual(browser.urls(), ["x.com", "a.com", "x.com", "x.com", "b.com", "x.com"])
        self.assertValid(browser)

    def test_delete_unknown_url(self):
        browser = make_browser("a.com", "b.com")
        self.assertEqual(browser.delete_url("nope.com"), 0)
        self.assertEqual(browser.urls(), ["a.com", "b.com"])
        self.assertIsNone(browser.restore())

    def test_delete_only_page_then_restore(self):
        browser = make_browser("a.com")
        browser.delete_url("a.com")
        self.assertEqual(len(browser), 0)
        self.assertIsNone(browser.current_page())
        self.assertValid(browser)

        self.assertEqual(browser.restore(), "a.com")
        self.assertEqual(self.current_url(browser), "a.com")
        self.assertValid(browser)

    def test_restore_falls_back_to_next_neighbour(self):
        browser = make_browser("a.com", "b.com", "c.com", "d.com", capacity=4)
        browser.delete_url("b.com")      # old neighbours: a.com and c.com
        browser.visit("e.com")
        browser.visit("f.com")           # capacity prunes a.com
        self.assertEqual(browser.urls(), ["c.com", "d.com", "e.com", "f.com"])
        browser.back(3)
        browser.visit("g.com")           # branching from c.com frees up room
        browser.restore()
        self.assertEqual(browser.urls(), ["b.com", "c.com", "g.com"])
        self.assertValid(browser)

    def test_restore_falls_back_to_newest_when_neighbours_are_gone(self):
        browser = make_browser("a.com", "b.com", "c.com")
        browser.delete_url("b.com")      # old neighbours: a.com and c.com
        browser.delete_history()
        browser.visit("z.com")
        self.assertIsNone(browser.restore())  # delete_history() empties the stack too

        browser = make_browser("a.com", "b.com", "c.com")
        browser.back(1)
        browser.delete_url("c.com")      # old neighbours: b.com and none
        browser.back(1)
        browser.visit("z.com")           # branching drops b.com
        browser.restore()
        self.assertEqual(browser.urls(), ["a.com", "z.com", "c.com"])
        self.assertValid(browser)

    def test_restore_when_full_prunes_oldest_but_keeps_restored_page(self):
        browser = make_browser("a.com", "b.com", "c.com", capacity=3)
        browser.delete_url("b.com")
        browser.visit("d.com")           # full again: a, c, d
        self.assertEqual(browser.restore(), "b.com")
        self.assertEqual(len(browser), 3)
        self.assertIn("b.com", browser.urls())
        self.assertNotIn("a.com", browser.urls())
        self.assertValid(browser)

    def test_restore_when_full_and_cursor_on_oldest(self):
        browser = make_browser("a.com", "b.com", capacity=2)
        browser.delete_url("b.com")
        browser.visit("c.com")
        browser.back(1)                  # cursor on a.com, which will be pruned
        browser.restore()
        self.assertEqual(len(browser), 2)
        self.assertValid(browser)

    def test_capacity_one(self):
        browser = make_browser("a.com", "b.com", capacity=1)
        browser.delete_url("b.com")
        browser.visit("c.com")
        browser.restore()
        self.assertEqual(browser.urls(), ["b.com"])
        self.assertEqual(self.current_url(browser), "b.com")
        self.assertValid(browser)


class TestExportImport(HistoryTestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "history.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_round_trip_keeps_pages_titles_times_and_cursor(self):
        original = BrowserHistory("https://a.com")
        original.visit("https://b.com/page?q=1", "Bee Page")
        original.visit("https://c.com")
        original.back(1)
        self.assertEqual(original.export_history(self.path), 3)

        loaded = BrowserHistory("https://other.com")
        self.assertEqual(loaded.import_history(self.path), 3)
        self.assertEqual(loaded.urls(), original.urls())
        self.assertEqual(loaded.current_page(), original.current_page())
        self.assertEqual(
            [(n.title, n.visited_at) for n in loaded._list],
            [(n.title, n.visited_at) for n in original._list],
        )
        self.assertValid(loaded)

    def test_import_plain_url_list(self):
        self.write("# my pages\n\na.com\n  \nb.com\nc.com\n")
        browser = BrowserHistory("start.com")
        self.assertEqual(browser.import_history(self.path), 3)
        self.assertEqual(browser.urls(), ["a.com", "b.com", "c.com"])
        self.assertEqual(self.current_url(browser), "c.com")  # no cursor line: newest
        self.assertEqual(browser.current_page()["title"], "c.com")
        self.assertValid(browser)

    def test_import_replaces_history_and_clears_restore_stack(self):
        self.write("a.com\nb.com\n")
        browser = make_browser("old1.com", "old2.com")
        browser.delete_url("old1.com")
        browser.import_history(self.path)
        self.assertEqual(browser.urls(), ["a.com", "b.com"])
        self.assertIsNone(browser.restore())

    def test_import_more_than_capacity_keeps_newest(self):
        self.write("# current: 2\n" + "".join(f"p{i}\n" for i in range(10)))
        browser = BrowserHistory("start", capacity=4)
        self.assertEqual(browser.import_history(self.path), 4)
        self.assertEqual(browser.urls(), ["p6", "p7", "p8", "p9"])
        # The saved cursor (p1) was pruned, so the oldest kept page becomes active.
        self.assertEqual(self.current_url(browser), "p6")
        self.assertValid(browser)

    def test_import_cursor_shifts_when_pages_are_pruned(self):
        self.write("# current: 8\n" + "".join(f"p{i}\n" for i in range(10)))
        browser = BrowserHistory("start", capacity=4)
        browser.import_history(self.path)
        self.assertEqual(self.current_url(browser), "p7")

    def test_import_out_of_range_cursor_is_clamped(self):
        self.write("# current: 99\na.com\nb.com\n")
        browser = BrowserHistory("start")
        browser.import_history(self.path)
        self.assertEqual(self.current_url(browser), "b.com")

    def test_bad_file_leaves_history_unchanged(self):
        self.write("a.com\nnot a url\nc.com\n")
        browser = make_browser("keep1.com", "keep2.com")
        with self.assertRaises(ValueError) as caught:
            browser.import_history(self.path)
        self.assertIn("line 2", str(caught.exception))
        self.assertEqual(browser.urls(), ["keep1.com", "keep2.com"])
        self.assertValid(browser)

    def test_bad_cursor_line(self):
        self.write("# current: two\na.com\n")
        browser = make_browser("keep.com")
        with self.assertRaises(ValueError):
            browser.import_history(self.path)
        self.assertEqual(browser.urls(), ["keep.com"])

    def test_missing_file(self):
        browser = make_browser("keep.com")
        with self.assertRaises(FileNotFoundError):
            browser.import_history(os.path.join(self.tmp.name, "missing.txt"))
        self.assertEqual(browser.urls(), ["keep.com"])

    def test_export_and_import_empty_history(self):
        browser = make_browser("a.com", "b.com")
        browser.delete_history()
        self.assertEqual(browser.export_history(self.path), 0)

        other = make_browser("x.com")
        self.assertEqual(other.import_history(self.path), 0)
        self.assertEqual(len(other), 0)
        self.assertIsNone(other.current_page())
        other.visit("y.com")
        self.assertEqual(other.urls(), ["y.com"])
        self.assertValid(other)


if __name__ == "__main__":
    unittest.main()
