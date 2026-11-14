from doubly_linked_list import DoublyLinkedList
from node import Node

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
        while len(self._list) > self.capacity:
            self._list.pop_front()
        return node.url

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

    def __len__(self):
        return len(self._list)