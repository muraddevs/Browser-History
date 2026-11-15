from doubly_linked_list import DoublyLinkedList
from node import Node
from stack import Stack

DEFAULT_CAPACITY = 50


# if no title is given we use the domain, e.g. "https://www.google.com/search" -> "www.google.com"
def _default_title(url):

    rest = url.split("://", 1)[-1]
    return rest.split("/", 1)[0] or url


class BrowserHistory:

    def __init__(self, homepage, capacity=DEFAULT_CAPACITY):
        # bool counts as int in python, so we block True/False on purpose
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be an integer >= 1")
        self.capacity = capacity
        self._list = DoublyLinkedList()
        self._current = None  # the page we are on right now
        # deleted pages, last deleted on top. each entry is (node, old_prev, old_next)
        # so restore() knows where to put the page back
        self._deleted = Stack()
        self.visit(homepage)

    # trims spaces and rejects empty urls or urls with spaces inside
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
        # visiting from the middle throws away the forward pages, like a real browser
        if self._current is not None:
            self._list.truncate_after(self._current)
        self._list.push_back(node)
        self._current = node
        self._prune_oldest(self.capacity)
        return node.url

    # removes pages from the head (oldest) until we have at most `limit`
    def _prune_oldest(self, limit):
        while len(self._list) > limit:
            oldest = self._list.head
            if oldest is self._current:
                self._current = oldest.next  # don't leave the cursor on a removed page
            self._list.pop_front()

    # go back one page at a time, stop early if there is no older page
    def back(self, steps=1):
        steps = self._check_steps(steps)
        if self._current is None:
            return None
        while steps > 0 and self._current.prev is not None:
            self._current = self._current.prev
            steps -= 1
        return self._current.url

    # same idea as back() but towards the newer pages
    def forward(self, steps=1):
        steps = self._check_steps(steps)
        if self._current is None:
            return None
        while steps > 0 and self._current.next is not None:
            self._current = self._current.next
            steps -= 1
        return self._current.url

    # only reads the state, nothing is moved
    def current_page(self):
        if self._current is None:
            return None
        info = self._current.metadata()
        info["position"] = self._list.index_of(self._current) + 1  # 1-based for the menu
        info["total"] = len(self._list)
        return info

    def urls(self):
        # oldest first, mostly used in the tests
        return [node.url for node in self._list]

    # Displaying
    # builds the history text, oldest at the top, current page marked with [<]
    def format_history(self):
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
        return text  # returned too so the tests can check it

    # Deleting and restoring
    # removes every page and also empties the restore stack
    def delete_history(self):
        removed = self._list.clear()
        self._current = None
        self._deleted.clear()
        return removed

    # deletes every page with this url and pushes each one onto the stack
    # returns how many were deleted (0 if the url wasn't there)
    def delete_url(self, url):
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
        # if we delete the page we are on, move to the older page (or newer if there is none)
        if node is self._current:
            self._current = old_prev if old_prev is not None else old_next
        self._list.unlink(node)
        self._deleted.push((node, old_prev, old_next))

    # puts the last deleted page back, returns its url or None if nothing to restore
    def restore(self):
        if self._deleted.is_empty():
            return None
        node, old_prev, old_next = self._deleted.pop()

        # make room first, otherwise the restored page could get pruned right away
        self._prune_oldest(self.capacity - 1)

        # try to put it back between its old neighbours, if they're gone add it at the end
        if old_prev is not None and self._list.contains(old_prev):
            self._list.insert_after(old_prev, node)
        elif old_next is not None and self._list.contains(old_next):
            self._list.insert_before(old_next, node)
        else:
            self._list.push_back(node)

        if self._current is None:
            self._current = node  # history was empty, so this is the only page
        return node.url

    # urls on the stack, the first one is the next to be restored
    def deleted_urls(self):
        return [entry[0].url for entry in self._deleted]

    # Export and import
    # file format: "# current: N" saves the cursor, then one page per line as
    # url<TAB>title<TAB>visited_at, oldest first
    def export_history(self, path):
        position = self.current_page()["position"] if self._current is not None else 0
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Browser history export (oldest first)\n")
            f.write(f"# current: {position}\n")
            for node in self._list:
                f.write(f"{node.url}\t{node.title}\t{node.visited_at}\n")
        return len(self._list)

    # replaces the history with the pages from the file. a file with just one url
    # per line also works. we read everything into a new list first, so if a line
    # is bad the old history stays as it was
    def import_history(self, path):
        new_list = DoublyLinkedList()
        cursor = None

        with open(path, "r", encoding="utf-8") as f:
            line_no = 0
            for raw in f:
                line_no += 1
                line = raw.rstrip("\r\n")
                if not line.strip():
                    continue
                # comment lines, the only one we care about is "# current: N"
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

        # too many pages for the capacity: keep the newest ones and shift the cursor
        dropped = 0
        while len(new_list) > self.capacity:
            new_list.pop_front()
            dropped += 1

        new_current = None
        if not new_list.is_empty():
            if cursor is None:
                cursor = len(new_list)  # no cursor saved, go to the newest page
            else:
                cursor = min(max(cursor - dropped, 1), len(new_list))
            new_current = new_list.node_at(cursor - 1)

        # everything was fine, now swap the old history for the new one
        self._list.clear()
        self._list = new_list
        self._current = new_current
        self._deleted.clear()
        return len(new_list)

    def __len__(self):
        return len(self._list)
