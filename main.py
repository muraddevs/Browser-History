# menu program for the browser history
# run: python3 main.py  (or python3 main.py --capacity 5 to see pruning faster)

import argparse

from browser_history import DEFAULT_CAPACITY, BrowserHistory

DEFAULT_HOMEPAGE = "https://www.google.com"
DEFAULT_FILE = "history.txt"

MENU = """
 1. Visit a page          7. Restore last deleted
 2. Back                  8. Show deleted pages
 3. Forward               9. Delete all history
 4. Show current page    10. Export history
 5. Show history         11. Import history
 6. Delete a URL          0. Quit"""


def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or (default if default is not None else "")


def ask_steps():
    text = ask("Steps", "1")
    try:
        return int(text)
    except ValueError:
        raise ValueError("steps must be a whole number") from None


def status_line(browser):
    page = browser.current_page()
    if page is None:
        return "Current page: (none, history is empty)"
    return f"Current page: {page['url']}  ({page['position']}/{page['total']})"


def show_current(browser):
    page = browser.current_page()
    if page is None:
        print("History is empty.")
        return
    print(f"URL:        {page['url']}")
    print(f"Title:      {page['title']}")
    print(f"Visited at: {page['visited_at']}")
    print(f"Position:   {page['position']} of {page['total']}")


# runs one menu option, returns False when the user wants to quit
def handle(choice, browser):
    if choice == "0":
        return False
    if choice == "1":
        url = ask("URL")
        title = ask("Title (optional)")
        browser.visit(url, title or None)
        print(f"Visited {url}")
    elif choice in ("2", "3"):
        move = browser.back if choice == "2" else browser.forward
        url = move(ask_steps())
        print(f"Now at: {url}" if url else "History is empty")
    elif choice == "4":
        show_current(browser)
    elif choice == "5":
        browser.display_history()
    elif choice == "6":
        url = ask("URL to delete")
        removed = browser.delete_url(url)
        if removed:
            print(f"Deleted {removed} page(s) with {url}")
        else:
            print(f"{url} is not in the history")
    elif choice == "7":
        url = browser.restore()
        print(f"Restored {url}" if url else "Nothing to restore")
    elif choice == "8":
        urls = browser.deleted_urls()
        if not urls:
            print("No deleted pages")
        for i, url in enumerate(urls, start=1):
            label = "  <- restored next" if i == 1 else ""
            print(f"{i:>3}. {url}{label}")
    elif choice == "9":
        if ask("Delete ALL history? (y/n)", "n").lower() == "y":
            print(f"Deleted {browser.delete_history()} page(s)")
        else:
            print("Cancelled")
    elif choice == "10":
        path = ask("File", DEFAULT_FILE)
        print(f"Exported {browser.export_history(path)} page(s) to {path}")
    elif choice == "11":
        path = ask("File", DEFAULT_FILE)
        print(f"Imported {browser.import_history(path)} page(s) from {path}")
    else:
        print("Unknown option")
    return True


def main():
    parser = argparse.ArgumentParser(description="Browser history manager")
    parser.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY,
                        help=f"maximum number of pages kept (default {DEFAULT_CAPACITY})")
    args = parser.parse_args()

    try:
        homepage = ask("Homepage", DEFAULT_HOMEPAGE)
        browser = BrowserHistory(homepage, capacity=args.capacity)
        running = True
        while running:
            print()
            print(status_line(browser))
            print(MENU)
            choice = input("> ").strip()
            try:
                running = handle(choice, browser)
            except (ValueError, OSError) as error:
                print(f"Error: {error}")
    except (EOFError, KeyboardInterrupt):
        print()
    except ValueError as error:
        print(f"Error: {error}")
    print("Bye")


if __name__ == "__main__":
    main()
