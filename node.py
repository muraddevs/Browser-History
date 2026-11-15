
from datetime import datetime


class Node:
    """prev = older page (towards head), next = newer page (towards tail)"""

    def __init__(self, url, title="", visited_at=None):
        self.url = url
        self.title = title
        # use the time we got (from an imported file), otherwise the time right now
        self.visited_at = visited_at or datetime.now().isoformat(timespec="seconds")
        self.prev = None
        self.next = None

    # page info as a dict, current_page() adds the position on top of this
    def metadata(self):
        return {"url": self.url, "title": self.title, "visited_at": self.visited_at}

    def __repr__(self):
        return f"Node({self.url!r})"
