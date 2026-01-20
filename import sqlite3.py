import sqlite3

# Connect to the SQLite database (creates it if not exists)
db = sqlite3.connect('invoice')
cursor = db.cursor()

# Create the book table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS client profile(
        id INTEGER PRIMARY KEY,
        name TEXT,
        address TEXT,
        email TEXT,
        invoice INTEGER
    )
''')
db.commit()


# Book class to add books programmatically
class Client:
    def __init__(self, id, name, address, email, invoice):
        self.id = id
        self.name = name
        self.address = address
        self.email = email
        self.invoice = invoice

    def save_to_db(self):
        cursor.execute('''
            INSERT OR IGNORE INTO book(id, title, author, qty)
            VALUES (?, ?, ?, ?)
        ''',(self.id, self.name, self.address, self.email,self.invoice))
        db.commit()


# Function to add a new Client
def new_client():
    try:
        id = int(input("Enter client ID: ").strip())
        if id < 1:
            print("❌ ID must be greater than 0.")
            return

        name = input("Enter client name: ").strip().capitalize()
        if not (3 <= len(name) <= 30):
            print("❌ Title must be between 3 and 30 characters.")
            return

        address = input("Enter client address: ").strip().capitalize()
        if not (3 <= len(address) <= 50):
            print("❌ Author name must be between 3 and 50 characters.")
            return

        email = int(input("Enter client email: ").strip())
        if not (3 <= len(email) <= 30):
            print("❌ email must be between 3 and 30 characters.")
            return
        
        invoice = int(input("Enter invoice number: ").strip())
        if invoice < 0:
            print("❌ Quantity cannot be negative.")
            return

        client = Client(id, name, address, email, invoice)
        client.save_to_db()
        print(f"✅ Book '{client}' added successfully.")

    except ValueError:
        print("❌ Invalid input. Please enter correct data types.\n" )


# Function to update a client's field
def update_client():
    try:
        input("Select client via id(1) or name(2) : ").strip
        if input == 1:
            id = int(input("Enter the client ID to update: ").strip())
            cursor.execute('SELECT * FROM Book WHERE id = ?', (id,))
            client = cursor.fetchone()
        elif input == 2:
            name = name(input("Enter client name to update: ").strip())
            cursor.execute('SELECT * FROM book WHERE id = ?', (id,))
            client = cursor.fetchone()

        else: 
            not client
            print("❌ Book ID not found.\n" + SYMBOL * WIDTH)
            return

        print("What would you like to edit?")
        print("1 - ID")
        print("2 - Name")
        print("3 - Address")
        print("4 - Email")
        print("5 Invoice")
        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            new_id = int(input("Enter new ID: ").strip())
            if new_id < 1:
                print("❌ ID must be greater than 0.")
                return
            cursor.execute("UPDATE client SET id = ? WHERE id = ?", (new_id, id))

        elif choice == "2":
            new_name = input("Enter new name: ").strip().capitalize()
            if not (3 <= len(new_name) <= 30):
                print("❌ Name must be 3–30 characters.")
                return
            cursor.execute("UPDATE book SET name = ? WHERE id = ?", (new_name, id))

        elif choice == "3":
            new_email = input("Enter new email: ").strip()
            if not (3 <= len(new_email) <= 50):
                print("❌ email name must be 3–50 characters.")
                return
            cursor.execute("UPDATE book SET email = ? WHERE id = ?", (new_email, id))

        elif choice == "4":
            new_qty = int(input("Enter new quantity: ").strip())
            if new_qty < 0:
                print("❌ Quantity cannot be negative.")
                return
            cursor.execute("UPDATE book SET qty = ? WHERE id = ?", (new_qty, id))

        else:
            print("❌ Invalid option.\n")
            return

        db.commit()
        print("✅ Client updated successfully.\n")

    except Exception as e:
        db.rollback()
        print("❌ An error occurred:", e, "\n")

