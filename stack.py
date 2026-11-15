# one item in the stack, it only needs to know the item below it
class _StackNode:

    def __init__(self, value, below=None):
        self.value = value
        self.below = below


# simple LIFO stack made with a singly linked list, push/pop/peek are all O(1)
# we use it to keep deleted pages so the last deleted one is restored first
class Stack:

    def __init__(self):
        self._top = None
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def push(self, value):
        # new item goes on top of the old top
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

    # goes from the top (last pushed) down to the bottom
    def __iter__(self):
        current = self._top
        while current is not None:
            yield current.value
            current = current.below
