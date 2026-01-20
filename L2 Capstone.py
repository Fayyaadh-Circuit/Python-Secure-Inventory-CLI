import sqlite3

# Global constants for display formatting
SYMBOL = "-"
WIDTH = 40

# Connect to the SQLite database (creates it if not exists)
db = sqlite3.connect('ebookstore')
cursor = db.cursor()

# Create the book table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS book(
        id INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        qty INTEGER
    )
''')
db.commit()

# Initial book data to populate the table
book_list = [
    (3001, "A Tale of Two Cities", "Charles Dickens", 30),
    (3002, "Harry Potter and the Philosopher's Stone", "J.K. Rowling", 40),
    (3003, "The Lion, the Witch and the Wardrobe", "C. S. Lewis", 25),
    (3004, "The Lord of the Rings", "J.R.R Tolkien", 37),
    (3005, "Alice in Wonderland", "Lewis Carroll", 12)
]

# Insert data while ignoring duplicates
cursor.executemany('''
    INSERT OR IGNORE INTO book(id, title, author, qty)
    VALUES (?, ?, ?, ?)
''', book_list)
db.commit()


# Book class to add books programmatically
class Book:
    def __init__(self, id, title, author, qty):
        self.id = id
        self.title = title
        self.author = author
        self.qty = qty

    def save_to_db(self):
        cursor.execute('''
            INSERT OR IGNORE INTO book(id, title, author, qty)
            VALUES (?, ?, ?, ?)
        ''', (self.id, self.title, self.author, self.qty))
        db.commit()


# Function to add a new book
def new_book():
    try:
        id = int(input("Enter book ID: ").strip())
        if id < 1:
            print("❌ ID must be greater than 0.")
            return

        title = input("Enter book title: ").strip().capitalize()
        if not (3 <= len(title) <= 20):
            print("❌ Title must be between 3 and 20 characters.")
            return

        author = input("Enter author: ").strip().capitalize()
        if not (3 <= len(author) <= 20):
            print("❌ Author name must be between 3 and 20 characters.")
            return

        qty = int(input("Enter quantity: ").strip())
        if qty < 0:
            print("❌ Quantity cannot be negative.")
            return

        book = Book(id, title, author, qty)
        book.save_to_db()
        print(f"✅ Book '{title}' added successfully.\n" + SYMBOL * WIDTH)

    except ValueError:
        print("❌ Invalid input. Please enter correct data types.\n" + SYMBOL * WIDTH)


# Function to update a book's field
def update_book():
    try:
        id = int(input("Enter the book ID to update: ").strip())
        cursor.execute('SELECT * FROM book WHERE id = ?', (id,))
        book = cursor.fetchone()

        if not book:
            print("❌ Book ID not found.\n" + SYMBOL * WIDTH)
            return

        print("What would you like to edit?")
        print("1 - ID")
        print("2 - Title")
        print("3 - Author")
        print("4 - Quantity")
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            new_id = int(input("Enter new ID: ").strip())
            if new_id < 1:
                print("❌ ID must be greater than 0.")
                return
            cursor.execute("UPDATE book SET id = ? WHERE id = ?", (new_id, id))

        elif choice == "2":
            new_title = input("Enter new title: ").strip().capitalize()
            if not (3 <= len(new_title) <= 20):
                print("❌ Title must be 3–20 characters.")
                return
            cursor.execute("UPDATE book SET title = ? WHERE id = ?", (new_title, id))

        elif choice == "3":
            new_author = input("Enter new author: ").strip().capitalize()
            if not (3 <= len(new_author) <= 20):
                print("❌ Author name must be 3–20 characters.")
                return
            cursor.execute("UPDATE book SET author = ? WHERE id = ?", (new_author, id))

        elif choice == "4":
            new_qty = int(input("Enter new quantity: ").strip())
            if new_qty < 0:
                print("❌ Quantity cannot be negative.")
                return
            cursor.execute("UPDATE book SET qty = ? WHERE id = ?", (new_qty, id))

        else:
            print("❌ Invalid option.\n" + SYMBOL * WIDTH)
            return

        db.commit()
        print("✅ Book updated successfully.\n" + SYMBOL * WIDTH)

    except Exception as e:
        db.rollback()
        print("❌ An error occurred:", e, "\n" + SYMBOL * WIDTH)


# Function to delete a book
def delete_book():
    try:
        id = int(input("Enter the book ID to delete: ").strip())
        cursor.execute('SELECT title FROM book WHERE id = ?', (id,))
        result = cursor.fetchone()

        if result is None:
            print(f"❌ No book found with ID {id}.\n" + SYMBOL * WIDTH)
            return

        title = result[0]
        confirm = input(f"Are you sure you want to delete '{title}'? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❗ Deletion cancelled.\n" + SYMBOL * WIDTH)
            return

        cursor.execute('DELETE FROM book WHERE id = ?', (id,))
        db.commit()
        print(f"✅ '{title}' successfully deleted.\n" + SYMBOL * WIDTH)

    except Exception as e:
        db.rollback()
        print("❌ An error occurred:", e, "\n" + SYMBOL * WIDTH)


# Function to search for books
def search():
    try:
        print("Search by:")
        print("1 - ID")
        print("2 - Title")
        print("3 - Author")
        choice = input("Select one of the options (1-3): ").strip()

        if choice == "1":
            id = int(input("Enter the ID: ").strip())
            cursor.execute('SELECT * FROM book WHERE id = ?', (id,))
        elif choice == "2":
            title = input("Enter the title: ").strip().capitalize()
            cursor.execute('SELECT * FROM book WHERE title = ?', (title,))
        elif choice == "3":
            author = input("Enter the author: ").strip().capitalize()
            cursor.execute('SELECT * FROM book WHERE author = ?', (author,))
        else:
            print("❌ Invalid option.\n")
            return

        results = cursor.fetchall()
        if results:
            print("\n📚 Search Results:")
            for row in results:
                print(f"ID: {row[0]} | Title: {row[1]} | Author: {row[2]} | Quantity: {row[3]}")
            print()
        else:
            print("🔍 No results found.\n")

    except Exception as e:
        db.rollback()
        print("❌ An error occurred:", e, "\n")


# Function to view all books
def view_all_books():
    cursor.execute("SELECT * FROM book")
    rows = cursor.fetchall()
    print("\n📖 === All Books ===")
    for row in rows:
        print(f"ID: {row[0]} | Title: {row[1]} | Author: {row[2]} | Quantity: {row[3]}")
    print()


# Display the menu
def options():
    print(SYMBOL * WIDTH)
    print("📚 eBookStore Menu")
    print("1 - Enter a new book")
    print("2 - Update book")
    print("3 - Delete book")
    print("4 - Search books")
    print("5 - View all books")
    print("0 - Exit")
    print(SYMBOL * WIDTH)


# === Main Program Loop ===
try:
    while True:
        options()
        menu = input("Select one of the options (0-5): ").strip()

        if menu == "1":
            new_book()
        elif menu == "2":
            update_book()
        elif menu == "3":
            delete_book()
        elif menu == "4":
            search()
        elif menu == "5":
            view_all_books()
        elif menu == "0":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid input. Please try again.\n")

except Exception as e:
    print("❌ Unexpected error occurred:", e)

finally:
    db.close()  # Close DB connection when program ends
