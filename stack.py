class _StackNode:
    """One item in the stack. It only needs a link to the item below it."""

    def __init__(self, value, below=None):
        self.value = value
        self.below = below


class Stack:
    """LIFO stack built on a singly linked list. push, pop and peek are O(1).

    Used by BrowserHistory to keep deleted pages so the most recently
    deleted one can be restored first.
    """

    def __init__(self):
        self._top = None
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def push(self, value):
        # The new item sits on top of the old top.
        self._top = _StackNode(value, self._top)
        self._size += 1

    def pop(self):
        if self._top is None:
            raise IndexError("pop from empty stack")
        item = self._top
        self._top = item.below
        item.below = None
        self._size -= 1
        return item.value

    def peek(self):
        if self._top is None:
            raise IndexError("peek from empty stack")
        return self._top.value

    def clear(self):
        self._top = None
        self._size = 0

    def __iter__(self):
        """Yield items from the top (most recent) down to the bottom (oldest)."""
        current = self._top
        while current is not None:
            yield current.value
            current = current.below
