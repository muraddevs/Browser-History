class DoublyLinkedList:

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def __iter__(self):
        current = self.head
        while current is not None:
            yield current
            current = current.next

    # Adding nodes
    def push_back(self, node):
        node.prev = self.tail
        node.next = None
        if self.tail is not None:
            self.tail.next = node
        else:
            self.head = node  
        self.tail = node
        self._size += 1

    def push_front(self, node):
        node.next = self.head
        node.prev = None
        if self.head is not None:
            self.head.prev = node
        else:
            self.tail = node  
        self.head = node
        self._size += 1

    def insert_after(self, ref, node):
        node.prev = ref
        node.next = ref.next
        if ref.next is not None:
            ref.next.prev = node
        else:
            self.tail = node  
        ref.next = node
        self._size += 1

    def insert_before(self, ref, node):
        node.next = ref
        node.prev = ref.prev
        if ref.prev is not None:
            ref.prev.next = node
        else:
            self.head = node  
        ref.prev = node
        self._size += 1

    # Removing nodes
    def unlink(self, node):
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next  
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev 
        node.prev = None
        node.next = None
        self._size -= 1
        return node

    def pop_front(self):
        if self.head is None:
            return None
        return self.unlink(self.head)

    def truncate_after(self, node):
        removed = 0
        current = node.next
        node.next = None
        self.tail = node
        while current is not None:
            next_node = current.next
            current.prev = None
            current.next = None
            current = next_node
            removed += 1
        self._size -= removed
        return removed

    def clear(self):
        removed = self._size
        current = self.head
        while current is not None:
            next_node = current.next
            current.prev = None
            current.next = None
            current = next_node
        self.head = None
        self.tail = None
        self._size = 0
        return removed

    # Searching
    def node_at(self, index):
        if not 0 <= index < self._size:
            raise IndexError(f"index {index} out of range (size {self._size})")
        if index <= self._size // 2:
            current = self.head
            for _ in range(index):
                current = current.next
        else:
            current = self.tail
            for _ in range(self._size - 1 - index):
                current = current.prev
        return current

    def index_of(self, node):
        index = 0
        current = self.head
        while current is not None:
            if current is node:
                return index
            current = current.next
            index += 1
        raise ValueError("Node is not in this list")

    def contains(self, node):
        # Compares by identity, so two pages with the same URL are different nodes.
        current = self.head
        while current is not None:
            if current is node:
                return True
            current = current.next
        return False

    # For testing
    def is_consistent(self):
        if self._size == 0:
            return self.head is None and self.tail is None
        if self.head is None or self.tail is None:
            return False
        if self.head.prev is not None or self.tail.next is not None:
            return False

        count = 1
        current = self.head
        while current.next is not None:
            if current.next.prev is not current:
                return False
            current = current.next
            count += 1
            if count > self._size:
                return False
        if current is not self.tail or count != self._size:
            return False

        count = 1
        current = self.tail
        while current.prev is not None:
            if current.prev.next is not current:
                return False
            current = current.prev
            count += 1
            if count > self._size:
                return False
        return current is self.head and count == self._size