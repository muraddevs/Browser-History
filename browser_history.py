from doubly_linked_list import DoublyLinkedList
from node import Node
from stack import Stack

DEFAULT_CAPACITY = 50


def _default_title(url):

    rest = url.split("://", 1)[-1]
    return rest.split("/", 1)[0] or url


class BrowserHistory:

    def __init__(self, homepage, capacity=DEFAULT_CAPACITY):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be an integer >= 1")
        self.capacity = capacity
        self._list = DoublyLinkedList()
        self._current = None
        # Deleted pages, most recent on top. Each entry is (node, old_prev, old_next)
        # so restore() can put the page back between its old neighbours.
        self._deleted = Stack()
        self.visit(homepage)

    @staticmethod
    def _clean_url(url):
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        url = url.strip()
        if not url:
            raise ValueError("URL must not be empty")
        if any(ch.isspace() for ch in url):
            raise ValueError("URL must not contain whitespace")
        return url

    @staticmethod
    def _check_steps(steps):
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise ValueError("steps must be an integer")
        if steps < 0:
            raise ValueError("steps must not be negative")
        return steps

    def visit(self, url, title=None):
        url = self._clean_url(url)  
        title = " ".join(title.split()) if title else _default_title(url)
        node = Node(url, title)
        if self._current is not None:
            self._list.truncate_after(self._current)
        self._list.push_back(node)
        self._current = node
        self._prune_oldest(self.capacity)
        return node.url

    def _prune_oldest(self, limit):
        """Drop pages from the oldest end (head) until at most `limit` remain."""
        while len(self._list) > limit:
            oldest = self._list.head
            if oldest is self._current:
                self._current = oldest.next
            self._list.pop_front()

    def back(self, steps=1):
        steps = self._check_steps(steps)
        if self._current is None:
            return None
        while steps > 0 and self._current.prev is not None:
            self._current = self._current.prev
            steps -= 1
        return self._current.url

    def forward(self, steps=1):
        steps = self._check_steps(steps)
        if self._current is None:
            return None
        while steps > 0 and self._current.next is not None:
            self._current = self._current.next
            steps -= 1
        return self._current.url

    def current_page(self):
        if self._current is None:
            return None
        info = self._current.metadata()
        info["position"] = self._list.index_of(self._current) + 1
        info["total"] = len(self._list)
        return info

    def urls(self):

        return [node.url for node in self._list]

    # Displaying
    def format_history(self):
        """Return the history from oldest (head) to newest (tail) as text.

        The active page is marked with [<].
        """
        if self._list.is_empty():
            return "(history is empty)"
        lines = []
        position = 1
        for node in self._list:
            marker = "  [<]" if node is self._current else ""
            lines.append(f"{position:>3}. {node.url}  \"{node.title}\"  {node.visited_at}{marker}")
            position += 1
        return "\n".join(lines)

    def display_history(self):
        text = self.format_history()
        print(text)
        return text

    # Deleting and restoring
    def delete_history(self):
        """Delete every page and empty the restore stack.

        The browser stays empty until the next visit() or import_history().
        Returns how many pages were removed.
        """
        removed = self._list.clear()
        self._current = None
        self._deleted.clear()
        return removed

    def delete_url(self, url):
        """Delete every page with this URL and push each one onto the restore stack.

        If the active page is deleted, the cursor moves to the older neighbour,
        or to the newer one when there is no older page.
        Returns how many pages were deleted (0 if the URL was not found).
        """
        url = self._clean_url(url)
        removed = 0
        node = self._list.head
        while node is not None:
            next_node = node.next  # save it before unlink() clears node.next
            if node.url == url:
                self._delete_node(node)
                removed += 1
            node = next_node
        return removed

    def _delete_node(self, node):
        old_prev, old_next = node.prev, node.next
        if node is self._current:
            self._current = old_prev if old_prev is not None else old_next
        self._list.unlink(node)
        self._deleted.push((node, old_prev, old_next))

    def restore(self):
        """Put the most recently deleted page back. Returns its URL, or None.

        The page goes back right after its old previous neighbour if that page
        is still in the history, otherwise right before its old next neighbour,
        otherwise it is added as the newest page. The cursor does not move,
        unless the history was empty.
        """
        if self._deleted.is_empty():
            return None
        node, old_prev, old_next = self._deleted.pop()

        # Make room first so the restored page itself is never pruned.
        self._prune_oldest(self.capacity - 1)

        if old_prev is not None and self._list.contains(old_prev):
            self._list.insert_after(old_prev, node)
        elif old_next is not None and self._list.contains(old_next):
            self._list.insert_before(old_next, node)
        else:
            self._list.push_back(node)

        if self._current is None:
            self._current = node
        return node.url

    def deleted_urls(self):
        """URLs on the restore stack, from the next one to be restored downwards."""
        return [entry[0].url for entry in self._deleted]

    # Export and import
    def export_history(self, path):
        """Save the history to a text file, oldest page first.

        Lines starting with '#' are comments. The '# current: N' line stores the
        position of the active page (1-based, 0 when the history is empty).
        Every other line is: url<TAB>title<TAB>visited_at
        Returns how many pages were written.
        """
        position = self.current_page()["position"] if self._current is not None else 0
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Browser history export (oldest first)\n")
            f.write(f"# current: {position}\n")
            for node in self._list:
                f.write(f"{node.url}\t{node.title}\t{node.visited_at}\n")
        return len(self._list)

    def import_history(self, path):
        """Replace the history with the pages in a text file.

        Accepts files written by export_history(), or plain files with one URL
        per line. Blank lines and '#' comments are skipped. If there is no
        '# current' line, the newest page becomes active. If the file holds more
        pages than the capacity, only the newest ones are kept.
        The whole file is read before anything changes, so a bad file leaves the
        current history untouched. Returns how many pages were loaded.
        """
        new_list = DoublyLinkedList()
        cursor = None

        with open(path, "r", encoding="utf-8") as f:
            line_no = 0
            for raw in f:
                line_no += 1
                line = raw.rstrip("\r\n")
                if not line.strip():
                    continue
                if line.lstrip().startswith("#"):
                    key, _, value = line.lstrip()[1:].partition(":")
                    if key.strip().lower() == "current":
                        try:
                            cursor = int(value.strip())
                        except ValueError:
                            raise ValueError(f"line {line_no}: bad current position {value.strip()!r}") from None
                    continue

                parts = line.split("\t")
                if len(parts) > 3:
                    raise ValueError(f"line {line_no}: expected url, title, visited_at separated by tabs")
                try:
                    url = self._clean_url(parts[0])
                except ValueError as error:
                    raise ValueError(f"line {line_no}: {error}") from None
                title = parts[1] if len(parts) > 1 else ""
                title = " ".join(title.split()) or _default_title(url)
                visited_at = parts[2].strip() if len(parts) > 2 else ""
                new_list.push_back(Node(url, title, visited_at or None))

        # Keep only the newest pages, and shift the cursor by however many were dropped.
        dropped = 0
        while len(new_list) > self.capacity:
            new_list.pop_front()
            dropped += 1

        new_current = None
        if not new_list.is_empty():
            if cursor is None:
                cursor = len(new_list)
            else:
                cursor = min(max(cursor - dropped, 1), len(new_list))
            new_current = new_list.node_at(cursor - 1)

        # Swap in the new history. Clearing the old list breaks its links.
        self._list.clear()
        self._list = new_list
        self._current = new_current
        self._deleted.clear()
        return len(new_list)

    def __len__(self):
        return len(self._list)