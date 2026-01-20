"""
Book Management System - Final Version
SQLite backend with Rich CLI interface
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

# =====================================
# CONSTANTS
# =====================================
DB_NAME = "ebookstore.db"
console = Console()

STYLES = {
    "info": "bold cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow"
}

TITLES = {
    "main": "📚 BOOK MANAGEMENT SYSTEM",
    "add": "➕ Add Book",
    "update": "✏️ Update Book",
    "delete": "🗑️ Delete Book",
    "search": "🔍 Search Books",
    "inventory": "📦 Inventory",
    "dashboard": "📊 Dashboard"
}

MESSAGES = {
    "bye": "👋 Goodbye!",
    "not_found": "❌ Book not found.",
    "added": "✅ Book added successfully!",
    "deleted": "🗑️ Book deleted successfully!",
    "updated": "✅ Book updated successfully!",
    "update_failed": "⚠️ No changes made or update failed.",
    "cancel": "🔙 Cancelled.",
    "add_failed": "❌ Failed to add book.",
    "no_changes": "ℹ️ No changes detected - book not updated",
    "duplicate": "❌ A book with this Title and Author already exists!",
    "id_exists": "❌ This ID already exists for another book!"
}


# =====================================
# DATABASE HANDLER
# =====================================
class BookDatabase:
    """Handles all database operations for the book management system."""

    def __init__(self, db_name: str = DB_NAME):
        """Initialize database connection and setup tables."""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        """Create database table and sample data if not exists."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0,
                date_added TEXT,
                last_updated TEXT
            )
            """
        )
        books = [
            (3001, "A Tale of Two Cities", "Charles Dickens", 30, 19.99),
            (3002, "Harry Potter", "J.K. Rowling", 40, 24.99),
            (3003, "The Lion, the Witch and the Wardrobe", "C.S. Lewis",
             25, 17.95),
            (3004, "The Lord of the Rings", "J.R.R. Tolkien", 37, 29.99),
            (3005, "Alice in Wonderland", "Lewis Carroll", 12, 14.95),
        ]
        now = datetime.now().isoformat()
        self.cursor.executemany(
            "INSERT OR IGNORE INTO books VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(*b, now, now) for b in books],
        )
        self.conn.commit()

    def add_book(self, data: Dict[str, Any]) -> bool:
        """
        Add a new book to the database.

        Args:
            data: Dictionary containing book details

        Returns:
            bool: True if book was added successfully
        """
        now = datetime.now().isoformat()
        try:
            self.cursor.execute(
                "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    data["id"], data["title"], data["author"],
                    data["quantity"], data["price"], now, now,
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def update_book(self, book_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing book's details.

        Args:
            book_id: ID of book to update
            updates: Dictionary of fields to update

        Returns:
            bool: True if update was successful
        """
        now = datetime.now().isoformat()
        try:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [now, book_id]
            self.cursor.execute(
             f"UPDATE books SET {set_clause}, last_updated = ? WHERE id = ?",
             values,
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def delete_book(self, book_id: int) -> bool:
        """
        Delete a book from the database.

        Args:
            book_id: ID of book to delete

        Returns:
            bool: True if deletion was successful
        """
        self.cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a book's details by ID.

        Args:
            book_id: ID of book to retrieve

        Returns:
            Optional[Dict]: Book details if found, None otherwise
        """
        self.cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = self.cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def search_books(self, **filters) -> List[Dict[str, Any]]:
        """
        Search books based on provided filters.

        Args:
            **filters: Keyword arguments for filtering

        Returns:
            List[Dict]: List of matching books
        """
        query = "SELECT * FROM books"
        params, conditions = [], []

        for field, value in filters.items():
            if field in ["title", "author"]:
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
            elif field == "id":
                conditions.append("id = ?")
                params.append(value)
            elif field == "max_price":
                conditions.append("price <= ?")
                params.append(value)
            elif field == "min_price":
                conditions.append("price >= ?")  # Fixed min_price filter
                params.append(value)
            elif field == "min_stock":
                conditions.append("quantity < ?")
                params.append(value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        self.cursor.execute(query, params)
        return [self._row_to_dict(row) for row in self.cursor.fetchall()]

    def get_all_books(self) -> List[Dict[str, Any]]:
        """Retrieve all books from the database."""
        self.cursor.execute("SELECT * FROM books")
        return [self._row_to_dict(row) for row in self.cursor.fetchall()]

    def is_duplicate_title_author(
        self, title: str, author: str, exclude_id: int = None
    ) -> bool:
        """
        Check if a title/author combination already exists.

        Args:
            title: Book title to check
            author: Book author to check
            exclude_id: Optional book ID to exclude from check

        Returns:
            bool: True if duplicate exists
        """
        query = "SELECT id FROM books WHERE lower(title)=? AND lower(author)=?"
        params = (title.lower(), author.lower())
        if exclude_id:
            query += " AND id != ?"
            params += (exclude_id,)
        self.cursor.execute(query, params)
        return self.cursor.fetchone() is not None

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to dictionary format."""
        return {
            "id": row[0],
            "title": row[1],
            "author": row[2],
            "quantity": row[3],
            "price": row[4],
            "date_added": row[5],
            "last_updated": row[6],
        }

    def close(self):
        """Close the database connection."""
        self.conn.close()


# =====================================
# BOOK MANAGER (MENUS & LOGIC)
# =====================================
class BookManager:
    """Handles CLI interaction and menus for book management."""

    def __init__(self):
        """Initialize the book manager with database connection."""
        self.db = BookDatabase()
        self.actions = {
            "1": self.add_book,
            "2": self.update_book,
            "3": self.delete_book,
            "4": self.search_books,
            "5": self.view_inventory,
            "6": self.dashboard
        }

    # =====================================
    # VALIDATION METHODS
    # =====================================
    def _validate_id(
            self, book_id: int, exclude_id: int = None) -> Tuple[bool, str]:
        """
        Validate a book ID.

        Args:
            book_id: ID to validate
            exclude_id: Optional ID to exclude from duplicate check

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if book_id <= 0:
            return False, "ID must be positive"
        existing_book = self.db.get_book(book_id)
        if existing_book and (exclude_id is None or existing_book["id"] !=
                              exclude_id):
            return False, MESSAGES["id_exists"]
        return True, ""

    def _validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate text input is not empty.

        Args:
            text: Text to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not text.strip():
            return False, "Field cannot be empty"
        return True, ""

    def _validate_quantity(self, qty: int) -> Tuple[bool, str]:
        """
        Validate quantity is non-negative.

        Args:
            qty: Quantity to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if qty < 0:
            return False, "Quantity must be 0 or more"
        return True, ""

    def _validate_price(self, price: float) -> Tuple[bool, str]:
        """
        Validate price is non-negative.

        Args:
            price: Price to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if price < 0:
            return False, "Price must be 0 or more"
        return True, ""

    def _validate_duplicate(
        self, title: str, author: str, exclude_id: int = None
    ) -> Tuple[bool, str]:
        """
        Validate title/author combination is unique.

        Args:
            title: Title to check
            author: Author to check
            exclude_id: Optional ID to exclude from check

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if self.db.is_duplicate_title_author(title, author, exclude_id):
            return False, MESSAGES["duplicate"]
        return True, ""

    def run(self):
        """Run the main program loop."""
        while True:
            console.print(Panel(TITLES["main"], style=STYLES["info"]))
            console.print(
                "1. Add Book\n2. Update Book\n3. Delete Book\n"
                "4. Search Books\n5. View Inventory\n6. Dashboard\nx. Exit"
            )
            choice = Prompt.ask(
                "Choose option",
                choices=list(self.actions) + ["x"]
            )
            if choice == "x":
                console.print(MESSAGES["bye"], style=STYLES["success"])
                self.db.close()
                break
            self.actions[choice]()

    def add_book(self):
        """Handle adding a new book with full validation."""
        while True:
            console.print(Panel(TITLES["add"], style=STYLES["info"]))
            book_data = {}

            # Get and validate ID
            val = Prompt.ask("Book ID (x to cancel)")
            if val.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            if not val.isdigit():
                console.print("❌ ID must be a number.", style=STYLES["error"])
                continue
            book_data["id"] = int(val)
            valid, msg = self._validate_id(book_data["id"])
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue

            # Get and validate Title
            title = Prompt.ask("Title (x to cancel)")
            if title.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            valid, msg = self._validate_text(title)
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue
            book_data["title"] = title.strip()

            # Get and validate Author
            author = Prompt.ask("Author (x to cancel)")
            if author.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            valid, msg = self._validate_text(author)
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue
            book_data["author"] = author.strip()

            # Validate title+author uniqueness
            valid, msg = self._validate_duplicate(
                book_data["title"], book_data["author"]
            )
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue

            # Get and validate Quantity
            qty = Prompt.ask("Quantity (x to cancel)")
            if qty.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            if not qty.isdigit():
                console.print("❌ Quantity must be a number.",
                              style=STYLES["error"])
                continue
            book_data["quantity"] = int(qty)
            valid, msg = self._validate_quantity(book_data["quantity"])
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue

            # Get and validate Price
            price = Prompt.ask("Price (x to cancel)")
            if price.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            try:
                book_data["price"] = float(price)
            except ValueError:
                console.print("❌ Price must be a number.",
                              style=STYLES["error"])
                continue
            valid, msg = self._validate_price(book_data["price"])
            if not valid:
                console.print(f"❌ {msg}", style=STYLES["error"])
                continue

            # Add book to database
            if self.db.add_book(book_data):
                console.print(MESSAGES["added"], style=STYLES["success"])
            else:
                console.print(MESSAGES["add_failed"], style=STYLES["error"])
            return

    def update_book(self):
        """Handle updating book details with full validation."""
        book = self._get_book_to_update()
        if not book:
            return

        while True:
            self._display_book_details(book)
            choice = self._get_update_choice()
            if choice == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return

            updates = self._process_update_choice(choice, book)
            if updates is None:
                # Validation failed, try again
                continue
            elif updates:
                self._apply_updates(book["id"], updates)
                # Refresh data
                book = self.db.get_book(updates.get("id", book["id"]))
            else:
                console.print(MESSAGES["no_changes"], style=STYLES["info"])

    def _get_book_to_update(self) -> Optional[Dict[str, Any]]:
        """Get a valid book ID from user for updating."""
        while True:
            console.print(Panel(TITLES["update"], style=STYLES["info"]))
            val = Prompt.ask("Book ID to update (x to cancel)")

            if val.lower() == "x":
                return None

            if not val.isdigit():
                console.print("❌ ID must be a number.", style=STYLES["error"])
                continue

            book = self.db.get_book(int(val))
            if not book:
                console.print(MESSAGES["not_found"], style=STYLES["error"])
                continue
            return book

    def _display_book_details(self, book: Dict[str, Any]):
        """Display current details of a book."""
        details = (
            f"[cyan]Current Book:[/cyan] "
            f"[yellow]ID:[/yellow] {book['id']} | "
            f"[yellow]Title:[/yellow] {book['title']} | "
            f"[yellow]Author:[/yellow] {book['author']} | "
            f"[yellow]Qty:[/yellow] {book['quantity']} | "
            f"[yellow]Price:[/yellow] R{book['price']:.2f}"
        )
        console.print(details)

    def _get_update_choice(self) -> str:
        """Get user's choice of field to update."""
        options = (
            "[bold]1.[/bold] ID | "
            "[bold]2.[/bold] Title | "
            "[bold]3.[/bold] Author | "
            "[bold]4.[/bold] Quantity | "
            "[bold]5.[/bold] Price | "
            "[bold]6.[/bold] Update All | "
            "[bold]x.[/bold] Back"
        )
        console.print(options)
        return Prompt.ask(
            "Select field to update",
            choices=["1", "2", "3", "4", "5", "6", "x"]
        )

    def _process_update_choice(
        self, choice: str, book: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process user's update choice and return updates dictionary.

        Returns:
            Optional[Dict]: Updates to apply, None if validation failed,
                           empty dict if no changes
        """
        updates = {}
        changes_made = False

        if choice in ("1", "6"):
            if self._handle_id_update(book, updates):
                changes_made = True

        if choice in ("2", "6"):
            if self._handle_title_update(book, updates):
                changes_made = True

        if choice in ("3", "6"):
            if self._handle_author_update(book, updates):
                changes_made = True

        if choice in ("4", "6"):
            if self._handle_quantity_update(book, updates):
                changes_made = True

        if choice in ("5", "6"):
            if self._handle_price_update(book, updates):
                changes_made = True

        # Final duplicate check if both title and author changed
        if "title" in updates and "author" in updates:
            if not self._validate_combined_update(updates, book["id"]):
                return None

        return updates if changes_made else {}

    def _handle_id_update(
        self, book: Dict[str, Any], updates: Dict[str, Any]
    ) -> bool:
        """
        Handle ID update with validation.

        Returns:
            bool: True if change was made, False otherwise
        """
        new_id = Prompt.ask(
                            "New ID (x to skip)",
                            default=str(book["id"])
        )
        if new_id.lower() == "x":
            return False

        try:
            new_id_val = int(new_id)
        except ValueError:
            console.print("❌ ID must be a number.", style=STYLES["error"])
            return False

        if new_id_val == book["id"]:
            console.print("ℹ️ ID unchanged", style=STYLES["info"])
            return False

        valid, msg = self._validate_id(new_id_val, exclude_id=book["id"])
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False

        updates["id"] = new_id_val
        return True

    def _handle_title_update(
        self, book: Dict[str, Any], updates: Dict[str, Any]
    ) -> bool:
        """
        Handle title update with validation.

        Returns:
            bool: True if change was made, False otherwise
        """
        title = Prompt.ask("New Title (x to skip)", default=book["title"])
        if title.lower() == "x":
            return False
        if title.strip() == book["title"]:
            console.print("ℹ️ Title unchanged", style=STYLES["info"])
            return False

        valid, msg = self._validate_text(title)
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False

        # Use current author for duplicate check unless it's also being updated
        author_to_check = updates.get("author", book["author"])
        valid_dup, msg_dup = self._validate_duplicate(
            title.strip(), author_to_check, book["id"]
        )
        if not valid_dup:
            console.print(f"❌ {msg_dup}", style=STYLES["error"])
            return False
        updates["title"] = title.strip()
        return True

    def _handle_author_update(
        self, book: Dict[str, Any], updates: Dict[str, Any]
    ) -> bool:
        """
        Handle author update with validation.

        Returns:
            bool: True if change was made, False otherwise
        """
        author = Prompt.ask("New Author (x to skip)", default=book["author"])
        if author.lower() == "x":
            return False
        if author.strip() == book["author"]:
            console.print("ℹ️ Author unchanged", style=STYLES["info"])
            return False

        valid, msg = self._validate_text(author)
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False

        # Use current title for duplicate check unless it's also being updated
        title_to_check = updates.get("title", book["title"])
        valid_dup, msg_dup = self._validate_duplicate(
            title_to_check, author.strip(), book["id"]
        )
        if not valid_dup:
            console.print(f"❌ {msg_dup}", style=STYLES["error"])
            return False

        updates["author"] = author.strip()
        return True

    def _handle_quantity_update(
        self, book: Dict[str, Any], updates: Dict[str, Any]
    ) -> bool:
        """
        Handle quantity update with validation.

        Returns:
            bool: True if change was made, False otherwise
        """
        qty = Prompt.ask("New Quantity (x to skip)",
                         default=str(book["quantity"]))
        if qty.lower() == "x":
            return False

        if not qty.isdigit():
            console.print("❌ Must be a number.", style=STYLES["error"])
            return False

        qty_val = int(qty)
        if qty_val == book["quantity"]:
            console.print("ℹ️ Quantity unchanged", style=STYLES["info"])
            return False

        valid, msg = self._validate_quantity(qty_val)
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False

        updates["quantity"] = qty_val
        return True

    def _handle_price_update(
        self, book: Dict[str, Any], updates: Dict[str, Any]
    ) -> bool:
        """
        Handle price update with validation.

        Returns:
            bool: True if change was made, False otherwise
        """
        price = Prompt.ask("New Price (x to skip)", default=str(book["price"]))
        if price.lower() == "x":
            return False

        try:
            price_val = float(price)
        except ValueError:
            console.print("❌ Must be a number.", style=STYLES["error"])
            return False

        if price_val == book["price"]:
            console.print("ℹ️ Price unchanged", style=STYLES["info"])
            return False

        valid, msg = self._validate_price(price_val)
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False

        updates["price"] = price_val
        return True

    def _validate_combined_update(
        self, updates: Dict[str, Any], book_id: int
    ) -> bool:
        """
        Validate combined title+author updates.

        Returns:
            bool: True if combination is valid, False if duplicate exists
        """
        valid, msg = self._validate_duplicate(
            updates["title"], updates["author"], book_id
        )
        if not valid:
            console.print(f"❌ {msg}", style=STYLES["error"])
            return False
        return True

    def _apply_updates(self, book_id: int, updates: Dict[str, Any]):
        """Apply validated updates to database with proper feedback."""
        if not updates:
            console.print(MESSAGES["no_changes"], style=STYLES["info"])
            return

        try:
            # Special handling for ID update
            if "id" in updates:
                # Need to update the primary key - requires special handling
                book = self.db.get_book(book_id)
                if not book:
                    console.print(MESSAGES["not_found"], style=STYLES["error"])
                    return

                # Create new book with updated ID
                new_book = {
                    "id": updates["id"],
                    "title": updates.get("title", book["title"]),
                    "author": updates.get("author", book["author"]),
                    "quantity": updates.get("quantity", book["quantity"]),
                    "price": updates.get("price", book["price"])
                }

                # Add new book and delete old one in a transaction
                self.db.conn.execute("BEGIN TRANSACTION")
                try:
                    if self.db.add_book(new_book):
                        self.db.delete_book(book_id)
                        self.db.conn.commit()
                        console.print(MESSAGES["updated"],
                                      style=STYLES["success"])
                    else:
                        self.db.conn.rollback()
                        console.print(MESSAGES["update_failed"],
                                      style=STYLES["warning"])
                except sqlite3.Error as e:
                    self.db.conn.rollback()
                    console.print(f"❌ Failed to update ID: {str(e)}",
                                  style=STYLES["error"])
            else:
                # Normal update for non-ID fields
                if self.db.update_book(book_id, updates):
                    console.print(MESSAGES["updated"], style=STYLES["success"])
                else:
                    console.print(MESSAGES["update_failed"],
                                  style=STYLES["warning"])
        except Exception as e:
            console.print(f"❌ Error during update: {str(e)}",
                          style=STYLES["error"])

    def delete_book(self):
        """Handle book deletion with confirmation."""
        while True:
            console.print(Panel(TITLES["delete"], style=STYLES["info"]))
            val = Prompt.ask("Book ID to delete (x to cancel)")
            if val.lower() == "x":
                console.print(MESSAGES["cancel"], style=STYLES["warning"])
                return
            if not val.isdigit():
                console.print("❌ Must be a number.", style=STYLES["error"])
                continue

            book_id = int(val)
            book = self.db.get_book(book_id)
            if not book:
                console.print(MESSAGES["not_found"], style=STYLES["error"])
                continue

            self._display_book(book)
            confirm = Prompt.ask(
                "❌ Confirm delete? (y/n)",
                choices=["y", "n"],
                default="n"
            )
            if confirm.lower() == "y":
                if self.db.delete_book(book_id):
                    console.print(MESSAGES["deleted"], style=STYLES["success"])
                else:
                    console.print("❌ Failed to delete book.",
                                  style=STYLES["error"])
            return

    def search_books(self):
        """Handle book search with various filters."""
        while True:
            console.print(Panel(TITLES["search"], style=STYLES["info"]))
            console.print(
                "1. By ID\n2. By Title\n3. By Author\n4. By Max Price\n"
                "5. By Min Price\n6. By Low Stock\nx. Back"
            )
            choice = Prompt.ask(
                "Choose search type",
                choices=["1", "2", "3", "4", "5", "6", "x"]
            )
            if choice == "x":
                return

            filters = {}
            if choice == "1":
                val = Prompt.ask("Enter Book ID (x to cancel)")
                if val.lower() == "x":
                    continue
                if not val.isdigit():
                    console.print("❌ Must be a number.", style=STYLES["error"])
                    continue
                filters["id"] = int(val)

            elif choice == "2":
                title = Prompt.ask("Enter Title (x to cancel)")
                if title.lower() == "x":
                    continue
                filters["title"] = title

            elif choice == "3":
                author = Prompt.ask("Enter Author (x to cancel)")
                if author.lower() == "x":
                    continue
                filters["author"] = author

            elif choice == "4":
                val = Prompt.ask("Enter Max Price (x to cancel)")
                if val.lower() == "x":
                    continue
                try:
                    filters["max_price"] = float(val)
                except ValueError:
                    console.print("❌ Must be a number.", style=STYLES["error"])
                    continue

            elif choice == "5":
                val = Prompt.ask("Enter Min Price (x to cancel)")
                if val.lower() == "x":
                    continue
                try:
                    filters["min_price"] = float(val)
                except ValueError:
                    console.print("❌ Must be a number.", style=STYLES["error"])
                    continue

            elif choice == "6":
                val = Prompt.ask("Show stock lower than (x to cancel)")
                if val.lower() == "x":
                    continue
                if not val.isdigit():
                    console.print("❌ Must be a number.", style=STYLES["error"])
                    continue
                filters["min_stock"] = int(val)

            results = self.db.search_books(**filters)
            if results:
                self._display_books(results)
            else:
                console.print(MESSAGES["not_found"], style=STYLES["error"])

    def view_inventory(self):
        """Display all books in inventory."""
        books = self.db.get_all_books()
        if books:
            self._display_books(books)
        else:
            console.print(MESSAGES["not_found"], style=STYLES["error"])

    def dashboard(self):
        """Display inventory dashboard with statistics."""
        books = self.db.get_all_books()
        if not books:
            console.print(MESSAGES["not_found"], style=STYLES["error"])
            return

        total_books = len(books)
        total_qty = sum(b["quantity"] for b in books)
        total_value = sum(b["price"] * b["quantity"] for b in books)
        low_stock = [b for b in books if b["quantity"] < 3]

        console.print(Panel(TITLES["dashboard"], style=STYLES["info"]))
        console.print(
            f"📊 [bold]Inventory Summary:[/bold]\n"
            f"• Total Books: [cyan]{total_books}[/cyan]\n"
            f"• Total Quantity: [cyan]{total_qty}[/cyan]\n"
            f"• Total Value: [green]R{total_value:.2f}[/green]"
        )

        if low_stock:
            console.print(
                "\n⚠️ [bold red]Low Stock Items (quantity < 3):"
                "[/bold red]")
            self._display_books(low_stock)
        else:
            console.print("\n✅ [green]All items have sufficient stock[/green]")

    def _display_books(self, books: List[Dict[str, Any]]):
        """Display multiple books in a formatted table."""
        table = Table(
            title="📚 Books",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", min_width=20)
        table.add_column("Author", min_width=18)
        table.add_column("Qty", justify="right", width=6)
        table.add_column("Price", justify="right", width=10)

        for book in books:
            stock_style = "red" if book["quantity"] < 3 else "green"
            table.add_row(
                str(book["id"]),
                book["title"],
                book["author"],
                f"[{stock_style}]{book['quantity']}[/{stock_style}]",
                f"R{book['price']:.2f}"
            )

        console.print(table)

    def _display_book(self, book: Dict[str, Any]):
        """Display a single book's details."""
        self._display_books([book])


# =====================================
# RUN APPLICATION
# =====================================
if __name__ == "__main__":
    manager = BookManager()
    manager.run()
