#import modules

import sqlite3
import tkinter as tk
from tkinter import ttk,messagebox
import re
from PIL import Image, ImageTk 

# Create database connection
connection = sqlite3.connect("drivingschool.db")
cursor = connection.cursor()

#creates instructor table
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblInstructor
(
    instructorID INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    surname TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    mobileNum TEXT,
    dateOfBirth DATE,
    postcode TEXT,
    email TEXT,
    bio TEXT,
    emergencyNum TEXT,
    role TEXT
)
"""
cursor.execute(sqlCommand)

#creates customer table (REMOVED memberStatus)
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblCustomer
(
    customerID INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    surname TEXT NOT NULL,
    mobileNum TEXT,
    dateOfBirth DATE,
    postcode TEXT,
    email TEXT,
    emergencyNum TEXT
)
"""
cursor.execute(sqlCommand)

#creates lesson table
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblLesson
(
    lessonID INTEGER PRIMARY KEY AUTOINCREMENT,
    lessonType TEXT NOT NULL,          -- Car / Motorbike / Lorry
    lessonDate DATE NOT NULL,
    lessonTime TEXT NOT NULL,
    duration INTEGER,                  -- minutes
    instructorID INTEGER,
    cost REAL,
    
    FOREIGN KEY (instructorID) REFERENCES tblInstructor(instructorID)
)
"""
cursor.execute(sqlCommand)

#creates booking table
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblBooking
(
    bookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    customerID INTEGER NOT NULL,
    lessonID INTEGER NOT NULL,
    amountPaid REAL,
    paidStatus TEXT,                   -- Paid / Unpaid
    
    FOREIGN KEY (customerID) REFERENCES tblCustomer(customerID),
    FOREIGN KEY (lessonID) REFERENCES tblLesson(lessonID)
)
"""
cursor.execute(sqlCommand)

#save and close
connection.commit()
connection.close()

# Global variables
current_user_id = None
current_user_role = None
current_user_name = None

#function that will perform a presence check to ensure all data is entered
def presenceCheck(rec):
    presence = True
    for x in range(len(rec)):
        if rec[x].strip() == "":
            presence = False
    return presence

#check entry fields to ensure that all characters entered are letters
def stringVal2(text):
    valid = True
    for x in range(len(text)):
        if ord(text[x]) not in range (65,91):
            if ord(text[x]) not in range(97,123):
                valid = False
    return valid

# Helper function to get ID from combobox string
def getID_from_combobox(text):
    try:
        return int(text.split()[-1])
    except:
        return None

# ============================================
# SETUP DEFAULT DATA - FIXED VERSION
# ============================================
def create_default_data():
    """Create default instructor and customer data for testing"""
    conn = sqlite3.connect("drivingschool.db")
    cur = conn.cursor()
    
    try:
        # Clear existing demo data to avoid duplicates
        cur.execute("DELETE FROM tblInstructor WHERE username IN ('admin', 'sarah', 'mike')")
        cur.execute("DELETE FROM tblCustomer WHERE firstName IN ('Alice', 'Bob', 'Charlie')")
        
        # Add default instructors
        default_instructors = [
            ("John", "Smith", "admin", "admin123", "07123456789", "01/01/1980", "AB1 2CD", "john@lddriving.com", "Experienced instructor", "07987654321", "Owner"),
            ("Sarah", "Johnson", "sarah", "sarah123", "07234567890", "15/05/1985", "CD2 3EF", "sarah@lddriving.com", "Friendly and patient", "07111111111", "Instructor"),
            ("Mike", "Brown", "mike", "mike123", "07345678901", "20/10/1990", "EF3 4GH", "mike@lddriving.com", "Specializes in motorway lessons", "07222222222", "Instructor")
        ]
        
        for instructor in default_instructors:
            cur.execute("""
                INSERT INTO tblInstructor 
                (firstName, surname, username, password, mobileNum, dateOfBirth, postcode, email, bio, emergencyNum, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, instructor)
        
        # Add default customers (NO memberStatus)
        default_customers = [
            ("Alice", "Wilson", "07456789012", "12/03/2000", "GH4 5IJ", "alice@email.com", "07555555555"),
            ("Bob", "Davis", "07567890123", "25/07/1998", "IJ5 6KL", "bob@email.com", "07666666666"),
            ("Charlie", "Miller", "07678901234", "03/11/1995", "KL6 7MN", "charlie@email.com", "07777777777")
        ]
        
        for customer in default_customers:
            cur.execute("""
                INSERT INTO tblCustomer 
                (firstName, surname, mobileNum, dateOfBirth, postcode, email, emergencyNum)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, customer)
        
        # Add some sample lessons
        import datetime
        
        today = datetime.date.today()
        for i in range(1, 8):
            lesson_date = today + datetime.timedelta(days=i)
            date_str = lesson_date.strftime("%Y-%m-%d")
            
            for time_slot in ["09:00", "11:00", "14:00", "16:00"]:
                lesson_types = ["Car", "Motorbike", "Lorry"]
                import random
                
                cur.execute("""
                    INSERT OR IGNORE INTO tblLesson 
                    (lessonType, lessonDate, lessonTime, duration, instructorID, cost)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (random.choice(lesson_types), date_str, time_slot, 60, random.randint(1, 3), random.choice([50, 60, 70])))
        
        conn.commit()
        print("✅ Default data created successfully!")
        print("   Admin: username='admin' password='admin123'")
        print("   Instructor: username='sarah' password='sarah123'")
        print("   Customers: Alice Wilson (07456789012), Bob Davis (07567890123)")
        
    except Exception as e:
        print(f"❌ Error creating default data: {e}")
        conn.rollback()
    finally:
        conn.close()

# ============================================
# LOGIN SYSTEM
# ============================================
def login_screen():
    """Proper login screen with validation"""
    global current_user_id, current_user_role, current_user_name
    
    # Create default data if needed
    create_default_data()
    
    root = tk.Tk()
    root.geometry("400x600")
    root.title("LD Driving School - Login")
    root.resizable(False, False)
    root.configure(bg="#7392F0")
    
    frame = tk.Frame(root, bg="#BCF0FE")
    frame.pack(padx=30, pady=30)
    
    tk.Label(frame, text="LD Driving School", font=("Aptos", 18, "bold"), bg="#BCF0FE").grid(row=0, column=0, columnspan=2, pady=20)
    
    # Try to load logo
    try:
        img = Image.open("logo.jpeg")
        img = img.resize((80, 80))
        logo_img = ImageTk.PhotoImage(img)
        logo_label = tk.Label(frame, image=logo_img, bg="#BCF0FE")
        logo_label.image = logo_img
        logo_label.grid(row=1, column=0, columnspan=2, pady=10)
    except:
        pass
    
    # Demo credentials box
    demo_frame = tk.LabelFrame(frame, text="Demo Credentials", bg="#BCF0FE", font=("Aptos", 10))
    demo_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=5, sticky="ew")
    
    tk.Label(demo_frame, text="Admin: admin / admin123", 
             bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    tk.Label(demo_frame, text="Instructor: sarah / sarah123", 
             bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    tk.Label(demo_frame, text="Customer: Alice Wilson / 07456789012", 
             bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    
    # Tab system for login type
    notebook = ttk.Notebook(frame)
    notebook.grid(row=3, column=0, columnspan=2, pady=10)
    
    # Instructor/Admin Login Tab
    instructor_frame = ttk.Frame(notebook)
    notebook.add(instructor_frame, text="Staff Login")
    
    tk.Label(instructor_frame, text="Username:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
    instructor_user = tk.Entry(instructor_frame, width=20)
    instructor_user.grid(row=0, column=1, padx=5, pady=10)
    instructor_user.insert(0, "admin")
    
    tk.Label(instructor_frame, text="Password:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
    instructor_pass = tk.Entry(instructor_frame, width=20, show="*")
    instructor_pass.grid(row=1, column=1, padx=5, pady=10)
    instructor_pass.insert(0, "admin123")
    
    # Customer Login Tab
    customer_frame = ttk.Frame(notebook)
    notebook.add(customer_frame, text="Customer Login")
    
    tk.Label(customer_frame, text="First Name:").grid(row=0, column=0, padx=5, pady=10, sticky="e")
    cust_first = tk.Entry(customer_frame, width=20)
    cust_first.grid(row=0, column=1, padx=5, pady=10)
    cust_first.insert(0, "Alice")
    
    tk.Label(customer_frame, text="Surname:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
    cust_last = tk.Entry(customer_frame, width=20)
    cust_last.grid(row=1, column=1, padx=5, pady=10)
    cust_last.insert(0, "Wilson")
    
    tk.Label(customer_frame, text="Mobile:").grid(row=2, column=0, padx=5, pady=10, sticky="e")
    cust_mobile = tk.Entry(customer_frame, width=20)
    cust_mobile.grid(row=2, column=1, padx=5, pady=10)
    cust_mobile.insert(0, "07456789012")
    
    def authenticate_instructor():
        username = instructor_user.get().strip()
        password = instructor_pass.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT instructorID, firstName, surname, role FROM tblInstructor WHERE username=? AND password=?", 
                   (username, password))
        result = cur.fetchone()
        conn.close()
        
        if result:
            global current_user_id, current_user_role, current_user_name
            current_user_id = result[0]
            current_user_name = f"{result[1]} {result[2]}"
            current_user_role = result[3]
            root.destroy()
            mainMenu()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    
    def authenticate_customer():
        first = cust_first.get().strip()
        last = cust_last.get().strip()
        mobile = cust_mobile.get().strip()
        
        if not all([first, last, mobile]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT customerID, firstName, surname FROM tblCustomer WHERE firstName=? AND surname=? AND mobileNum=?", 
                   (first, last, mobile))
        result = cur.fetchone()
        
        if result:
            global current_user_id, current_user_role, current_user_name
            current_user_id = result[0]
            current_user_name = f"{result[1]} {result[2]}"
            current_user_role = "Customer"
            root.destroy()
            mainMenu2()
        else:
            # Customer doesn't exist, ask if they want to register
            if messagebox.askyesno("Not Found", "Customer not found. Would you like to register?"):
                register_customer(first, last, mobile)
            conn.close()
    
    def register_customer(first, last, mobile):
        # Simple registration
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO tblCustomer (firstName, surname, mobileNum)
                VALUES (?, ?, ?)
            """, (first, last, mobile))
            conn.commit()
            
            # Get the new customer ID
            cur.execute("SELECT customerID FROM tblCustomer WHERE firstName=? AND surname=? AND mobileNum=?", 
                       (first, last, mobile))
            new_id = cur.fetchone()[0]
            
            global current_user_id, current_user_role, current_user_name
            current_user_id = new_id
            current_user_name = f"{first} {last}"
            current_user_role = "Customer"
            
            conn.close()
            root.destroy()
            mainMenu2()
            
        except Exception as e:
            conn.close()
            messagebox.showerror("Registration Error", str(e))
    
    tk.Button(instructor_frame, text="Login", width=15, bg="white", 
              command=authenticate_instructor).grid(row=2, column=0, columnspan=2, pady=20)
    
    tk.Button(customer_frame, text="Login/Register", width=15, bg="white",
              command=authenticate_customer).grid(row=3, column=0, columnspan=2, pady=20)
    
    root.mainloop()

# ============================================
# CUSTOMER MENU
# ============================================
def customerMenu():
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Customer Management")
    top.geometry("1100x520")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text=f"Customer Management - Welcome {current_user_name}", 
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    columns = ("ID", "First Name", "Surname", "Mobile", "DOB", "Postcode", "Email", "Emergency")
    tree_customers = ttk.Treeview(top, columns=columns, show="headings", height=10)

    for col in columns:
        tree_customers.heading(col, text=col)
        tree_customers.column(col, width=110)

    tree_customers.pack(pady=5)

    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)

    def DisplayForm():
        for item in tree_customers.get_children():
            tree_customers.delete(item)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM tblcustomer")
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            tree_customers.insert("", tk.END, values=r)

    def add():
        def addCustomer():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()

            data = (
                firstname.get(),
                surname.get(),
                mobileNum.get(),
                dob.get(),
                postcode.get(),
                email.get(),
                emergencyNum.get()
            )

            if not data[0] or not data[1]:
                messagebox.showerror("Error", "First Name and Surname required")
                return
            if len(data[2]) != 11 or not data[2].isdigit():
                messagebox.showerror("Error", "Mobile number must be 11 digits")
                return
            if len(data[6]) != 11 or not data[6].isdigit():
                messagebox.showerror("Error", "Emergency number must be 11 digits")
                return
            if not re.match(r"\d{2}/\d{2}/\d{4}", data[3]):
                messagebox.showerror("Error", "DOB must be DD/MM/YYYY")
                return

            cur.execute("INSERT INTO tblcustomer VALUES (NULL,?,?,?,?,?,?,?)", data)
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Customer added")
            root_add.destroy()
            DisplayForm()

        root_add = tk.Toplevel(top)
        root_add.geometry("500x400")
        root_add.title("Add Customer")
        root_add.configure(bg="#7392F0")

        frame = tk.Frame(root_add, bg="#BCF0FE")
        frame.pack(padx=10, pady=10)

        labels = [
            "First Name:", "Surname:", "Mobile Number:", "Date of Birth:",
            "Postcode:", "Email:", "Emergency Number:"
        ]

        for i, lbl in enumerate(labels):
            tk.Label(frame, text=lbl, bg="#BCF0FE").grid(row=i, column=0, sticky="e", pady=4)

        firstname = tk.Entry(frame, width=25)
        surname = tk.Entry(frame, width=25)
        mobileNum = tk.Entry(frame, width=25)
        dob = tk.Entry(frame, width=25)
        postcode = tk.Entry(frame, width=25)
        email = tk.Entry(frame, width=25)
        emergencyNum = tk.Entry(frame, width=25)

        entries = [firstname, surname, mobileNum, dob, postcode, email, emergencyNum]

        for i, e in enumerate(entries):
            e.grid(row=i, column=1, pady=4)

        tk.Button(frame, text="Submit", width=18, bg="white", command=addCustomer).grid(row=7, column=1, pady=12)

    def edit():
        def EditCustomer():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()

            cid = getID_from_combobox(search_cb.get())
            if not cid:
                messagebox.showerror("Error", "Select a customer")
                return

            if field.get() in ("mobileNum", "emergencyNum") and not value.get().isdigit():
                messagebox.showerror("Error", "Must be numeric")
                return

            if field.get() == "dateOfBirth" and not re.match(r"\d{2}/\d{2}/\d{4}", value.get()):
                messagebox.showerror("Error", "DOB must be DD/MM/YYYY")
                return

            cur.execute(f"UPDATE tblcustomer SET {field.get()} = ? WHERE customerID = ?", (value.get(), cid))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Customer updated")
            rootEdit.destroy()
            DisplayForm()

        rootEdit = tk.Toplevel(top)
        rootEdit.geometry("450x210")
        rootEdit.title("Edit Customer")
        rootEdit.configure(bg="#7392F0")

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        customers = [f"{r[0]} {r[1]} {r[2]}" for r in cur.execute("SELECT firstName, surname, customerID FROM tblcustomer")]
        conn.close()

        tk.Label(rootEdit, text="Customer:", bg="#BCF0FE").place(x=10, y=60)
        search_cb = ttk.Combobox(rootEdit, values=customers, width=28)
        search_cb.place(x=140, y=60)

        tk.Label(rootEdit, text="Field:", bg="#BCF0FE").place(x=10, y=95)
        field = ttk.Combobox(rootEdit, values=("firstName","surname","mobileNum","dateOfBirth","postcode","email","emergencyNum"), width=25)
        field.place(x=140, y=95)

        tk.Label(rootEdit, text="New Value:", bg="#BCF0FE").place(x=10, y=130)
        value = tk.Entry(rootEdit, width=29)
        value.place(x=140, y=130)

        tk.Button(rootEdit, text="Submit", width=16, bg="white", command=EditCustomer).place(x=140, y=165)

    def delete():
        def deleteCustomer():
            cid = getID_from_combobox(search_cb.get())
            if not cid:
                messagebox.showerror("Error", "Select a customer")
                return

            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this customer?"):
                conn = sqlite3.connect("drivingschool.db")
                cur = conn.cursor()
                cur.execute("DELETE FROM tblcustomer WHERE customerID = ?", (cid,))
                conn.commit()
                conn.close()

                messagebox.showinfo("Deleted", "Customer removed")
                rdelete.destroy()
                DisplayForm()

        rdelete = tk.Toplevel(top)
        rdelete.geometry("480x150")
        rdelete.title("Delete Customer")
        rdelete.configure(bg="#7392F0")

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        customers = [f"{r[0]} {r[1]} {r[2]}" for r in cur.execute("SELECT firstName, surname, customerID FROM tblcustomer")]
        conn.close()

        tk.Label(rdelete, text="Select Customer:", bg="#BCF0FE").place(x=20, y=50)
        search_cb = ttk.Combobox(rdelete, values=customers, width=30)
        search_cb.place(x=160, y=50)

        tk.Button(rdelete, text="Submit", width=13, bg="white", command=deleteCustomer).place(x=180, y=95)

    tk.Button(btn_frame, text="Add Customer", width=18, bg="white", command=add).grid(row=0, column=0, padx=8)
    tk.Button(btn_frame, text="Edit Customer", width=18, bg="white", command=edit).grid(row=0, column=1, padx=8)
    tk.Button(btn_frame, text="Delete Customer", width=18, bg="white", command=delete).grid(row=0, column=2, padx=8)
    tk.Button(btn_frame, text="Back", width=18, bg="white", command=destroy_menu).grid(row=1, column=1, pady=12)

    DisplayForm()

# ============================================
# CUSTOMER PAYMENT MENU (NEW - for customers to view/pay their bills)
# ============================================
def customerPaymentMenu():
    """Payment menu for customers to view and pay their bills"""
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("My Payments")
    top.geometry("1000x520")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text=f"My Payments - {current_user_name}", 
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    # Treeview for unpaid bookings
    columns = ("Booking ID", "Lesson", "Date", "Time", "Amount Due", "Total Cost", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.pack(pady=10, padx=10)

    def load_my_payments():
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        # Get this customer's unpaid/partially paid bookings
        cur.execute("""
            SELECT b.bookingID, 
                   l.lessonType || ' (' || l.duration || 'min)',
                   l.lessonDate,
                   l.lessonTime,
                   l.cost - COALESCE(b.amountPaid, 0),
                   l.cost,
                   b.paidStatus
            FROM tblBooking b
            JOIN tblLesson l ON b.lessonID = l.lessonID
            WHERE b.customerID = ?
            ORDER BY l.lessonDate
        """, (current_user_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        for row in rows:
            tree.insert("", tk.END, values=row)
    
    # Payment frame
    payment_frame = tk.Frame(top, bg="#BCF0FE")
    payment_frame.pack(pady=10)
    
    tk.Label(payment_frame, text="Booking ID:", bg="#BCF0FE").grid(row=0, column=0, padx=5)
    booking_id_entry = tk.Entry(payment_frame, width=15)
    booking_id_entry.grid(row=0, column=1, padx=5)
    
    tk.Label(payment_frame, text="Amount to Pay (£):", bg="#BCF0FE").grid(row=0, column=2, padx=5)
    amount_entry = tk.Entry(payment_frame, width=15)
    amount_entry.grid(row=0, column=3, padx=5)
    
    def process_payment():
        try:
            booking_id = int(booking_id_entry.get())
            amount = float(amount_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid numbers")
            return
        
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than 0")
            return
        
        # Verify this booking belongs to the current customer
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT customerID FROM tblBooking WHERE bookingID = ?", (booking_id,))
        result = cur.fetchone()
        
        if not result:
            messagebox.showerror("Error", "Booking not found")
            conn.close()
            return
        
        if result[0] != current_user_id:
            messagebox.showerror("Error", "You can only pay for your own bookings")
            conn.close()
            return
        
        try:
            # Get current payment status
            cur.execute("SELECT amountPaid, paidStatus FROM tblBooking WHERE bookingID = ?", (booking_id,))
            result = cur.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Booking not found")
                return
            
            current_paid, current_status = result
            
            # Get lesson cost
            cur.execute("""
                SELECT l.cost 
                FROM tblBooking b
                JOIN tblLesson l ON b.lessonID = l.lessonID
                WHERE b.bookingID = ?
            """, (booking_id,))
            lesson_cost_result = cur.fetchone()
            if not lesson_cost_result:
                messagebox.showerror("Error", "Lesson not found")
                return
            lesson_cost = lesson_cost_result[0]
            
            new_paid = current_paid + amount
            new_status = "Paid" if new_paid >= lesson_cost else "Partially Paid"
            
            # Update booking
            cur.execute("""
                UPDATE tblBooking 
                SET amountPaid = ?, paidStatus = ?
                WHERE bookingID = ?
            """, (new_paid, new_status, booking_id))
            
            conn.commit()
            
            messagebox.showinfo("Success", 
                              f"Payment processed: £{amount}\n"
                              f"Total paid: £{new_paid}/{lesson_cost}\n"
                              f"Status: {new_status}")
            
            booking_id_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            load_my_payments()
            
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()
    
    tk.Button(payment_frame, text="Make Payment", bg="green", fg="white",
             command=process_payment, width=15).grid(row=0, column=4, padx=5)
    
    # View all my bookings button
    def view_all_my_bookings():
        view_window = tk.Toplevel(top)
        view_window.title("All My Bookings")
        view_window.geometry("900x400")
        
        columns = ("Booking ID", "Lesson", "Date", "Time", "Amount Paid", "Status", "Total Cost")
        tree_view = ttk.Treeview(view_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree_view.heading(col, text=col)
            tree_view.column(col, width=120)
        
        tree_view.pack(pady=10, padx=10)
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT b.bookingID, 
                   l.lessonType,
                   l.lessonDate,
                   l.lessonTime,
                   b.amountPaid,
                   b.paidStatus,
                   l.cost
            FROM tblBooking b
            JOIN tblLesson l ON b.lessonID = l.lessonID
            WHERE b.customerID = ?
            ORDER BY l.lessonDate DESC
        """, (current_user_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        for row in rows:
            tree_view.insert("", tk.END, values=row)
    
    # Button frame
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="View All My Bookings", width=18, bg="white", command=view_all_my_bookings).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Refresh", width=18, bg="white", command=load_my_payments).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Back", width=18, bg="white", command=destroy_menu).pack(side="left", padx=5)
    
    # Load data initially
    load_my_payments()

# ============================================
# INSTRUCTOR MENU (No changes needed)
# ============================================
def instructorMenu():
    """Opens the Instructor Menu as a Toplevel window."""
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Instructor Menu")
    top.geometry("800x520")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text="Instructor Management", font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    # --- Search bar ---
    search_frame = tk.Frame(top, bg="#BCF0FE")
    search_frame.pack(pady=5)

    tk.Label(search_frame, text="Search:", bg="#BCF0FE").grid(row=0, column=0, padx=5)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.grid(row=0, column=1, padx=5)

    def search_instructors(*args):
        DisplayForm(search_var.get())

    search_var.trace_add("write", search_instructors)

    def clear_search():
        search_var.set("")
        DisplayForm()

    tk.Button(search_frame, text="Clear", width=10, bg="white", command=clear_search).grid(row=0, column=2, padx=5)

    # --- Treeview ---
    columns = ("ID", "First Name", "Surname", "Username", "Mobile", "Role")
    tree_instructors = ttk.Treeview(top, columns=columns, show="headings", height=10)
    for col in columns:
        tree_instructors.heading(col, text=col)
        tree_instructors.column(col, width=120 if col != "Username" else 140)
    tree_instructors.pack(pady=5)

    # --- Buttons frame ---
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)

    # --- DisplayForm ---
    def DisplayForm(search_text=None):
        if search_text is None:
            search_text = search_var.get()

        # Clear existing tree entries
        for item in tree_instructors.get_children():
            tree_instructors.delete(item)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()

        if search_text:
            like = f"%{search_text.lower()}%"
            cur.execute("""
                SELECT instructorID, firstName, surname, username, mobileNum, role
                FROM tblInstructor
                WHERE lower(firstName) LIKE ?
                   OR lower(surname) LIKE ?
                   OR lower(username) LIKE ?
                   OR lower(role) LIKE ?
            """, (like, like, like, like))
        else:
            cur.execute("""
                SELECT instructorID, firstName, surname, username, mobileNum, role
                FROM tblInstructor
            """)

        rows = cur.fetchall()
        conn.close()

        for r in rows:
            tree_instructors.insert("", tk.END, values=r)

    # --- ADD instructor ---
    def add():
        def addInstructor():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()

            iFirstName = firstname.get().strip().capitalize()
            iSurname = surname.get().strip().capitalize()
            iUsername = username.get().strip()
            iPassword = password.get().strip()
            iRole = role.get().strip()
            iMobileNum = mobileNum.get().strip()
            iDob = dob.get().strip()
            iPostcode = postcode.get().strip()
            iEmail = email.get().strip()
            iBlurb = blurb.get().strip()
            iEmergencyNum = emergencyNum.get().strip()

            instructorRec = [iFirstName, iSurname, iUsername, iPassword, iMobileNum,
                             iDob, iPostcode, iEmail, iBlurb, iEmergencyNum, iRole]

            validation = True

            # Required fields
            if len(iFirstName) == 0 or len(iSurname) == 0 or len(iUsername) == 0 or len(iPassword) == 0 or len(iRole) == 0:
                validation = False
                messagebox.showerror("Error", "Some required fields are empty")
                root_add.lift()
                conn.close()
                return

            # Length checks
            if len(iFirstName) > 15:
                validation = False
                messagebox.showerror("Error", "Length of the First Name must be below 15 characters")
                root_add.lift()
            elif len(iSurname) > 20:
                validation = False
                messagebox.showerror("Error", "Length of Surname must be below 20 characters")
                root_add.lift()
            elif len(iUsername) > 15:
                validation = False
                messagebox.showerror("Error", "Length of Username must be below 15 characters")
                root_add.lift()
            elif len(iPassword) > 15:
                validation = False
                messagebox.showerror("Error", "Length of Password must be below 15 characters")
                root_add.lift()
            elif len(iRole) > 30:
                validation = False
                messagebox.showerror("Error", "Length of Role must be below 30 characters")
                root_add.lift()
            elif iMobileNum and len(iMobileNum) != 11:
                validation = False
                messagebox.showerror("Error", "Length of Mobile Number must be 11 characters")
                root_add.lift()
            elif iDob and len(iDob) != 10:
                validation = False
                messagebox.showerror("Error", "Length of Date of Birth must be exactly 10 characters (DD/MM/YYYY)")
                root_add.lift()
            elif iPostcode and (len(iPostcode) > 8 or len(iPostcode) < 5):
                validation = False
                messagebox.showerror("Error", "Length of Postcode must be between 5 and 7 characters")
                root_add.lift()
            elif iEmail and len(iEmail) > 50:
                validation = False
                messagebox.showerror("Error", "Length of Email must be below 50 characters")
                root_add.lift()
            elif iBlurb and len(iBlurb) > 750:
                validation = False
                messagebox.showerror("Error", "Length of Blurb must be below 750 characters")
                root_add.lift()
            elif iEmergencyNum and len(iEmergencyNum) != 11:
                validation = False
                messagebox.showerror("Error", "Length of Emergency Number must be 11 characters")
                root_add.lift()

            # Type checks
            if not stringVal2(iSurname):
                validation = False
                messagebox.showerror("Error", "Surname must contain only letters")
                root_add.lift()
            if not stringVal2(iFirstName):
                validation = False
                messagebox.showerror("Error", "First name must contain only letters")
                root_add.lift()
            if iMobileNum and not iMobileNum.isdigit():
                validation = False
                messagebox.showerror("Error", "Mobile number must be numeric")
                root_add.lift()
            if iEmergencyNum and not iEmergencyNum.isdigit():
                validation = False
                messagebox.showerror("Error", "Emergency number must be numeric")
                root_add.lift()

            if iDob:
                ValidDOB = re.match(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$", iDob)
                if not ValidDOB:
                    validation = False
                    messagebox.showerror("Error", "Please enter Date of Birth in form DD/MM/YYYY")
                    root_add.lift()

            if validation:
                if presenceCheck(instructorRec):
                    try:
                        cur.execute("""
                            INSERT INTO tblInstructor
                            (firstName, surname, username, password, mobileNum, dateOfBirth, postcode, email, bio, emergencyNum, role)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (iFirstName, iSurname, iUsername, iPassword, iMobileNum,
                              iDob, iPostcode, iEmail, iBlurb, iEmergencyNum, iRole))
                        conn.commit()
                        messagebox.showinfo("Instructor Added", "Instructor successfully added")
                        root_add.destroy()
                        DisplayForm()
                    except sqlite3.IntegrityError as e:
                        messagebox.showerror("Database Error", f"Username must be unique.\n{e}")
                        conn.rollback()
                        root_add.lift()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")
                    root_add.lift()
            conn.close()

        # --- Add Window ---
        root_add = tk.Toplevel(top)
        root_add.geometry("600x600")
        root_add.title("Instructor Add Menu")
        root_add.resizable(False, False)
        root_add.configure(bg="#7392F0")

        frame_heading = tk.Frame(root_add, bg="#BCF0FE")
        frame_heading.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        tk.Label(frame_heading, text='Instructor Add Menu', font=('Aptos', 16), bg="#BCF0FE").grid(row=0, column=0, padx=10, pady=10)

        frame_add = tk.Frame(root_add, bg="#BCF0FE")
        frame_add.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        labels = ["Enter First Name:", "Enter Surname:", "Enter Username:", "Enter Password:",
                  "Enter Role:", "Enter Mobile Number:", "Enter Date of Birth (DD/MM/YYYY):",
                  "Enter Postcode:", "Enter Email:", "Enter Blurb:", "Enter Emergency Number:"]
        firstname = tk.Entry(frame_add, width=30)
        firstname.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[0], bg="#BCF0FE").grid(row=0, column=0, sticky="e")

        surname = tk.Entry(frame_add, width=30)
        surname.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[1], bg="#BCF0FE").grid(row=1, column=0, sticky="e")

        username = tk.Entry(frame_add, width=30)
        username.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[2], bg="#BCF0FE").grid(row=2, column=0, sticky="e")

        password = tk.Entry(frame_add, width=30)
        password.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[3], bg="#BCF0FE").grid(row=3, column=0, sticky="e")

        role = ttk.Combobox(frame_add, width=27, values=("Owner", "Leader", "Instructor"))
        role.grid(row=4, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[4], bg="#BCF0FE").grid(row=4, column=0, sticky="e")

        mobileNum = tk.Entry(frame_add, width=30)
        mobileNum.grid(row=5, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[5], bg="#BCF0FE").grid(row=5, column=0, sticky="e")

        dob = tk.Entry(frame_add, width=30)
        dob.grid(row=6, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[6], bg="#BCF0FE").grid(row=6, column=0, sticky="e")

        postcode = tk.Entry(frame_add, width=30)
        postcode.grid(row=7, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[7], bg="#BCF0FE").grid(row=7, column=0, sticky="e")

        email = tk.Entry(frame_add, width=30)
        email.grid(row=8, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[8], bg="#BCF0FE").grid(row=8, column=0, sticky="e")

        blurb = tk.Entry(frame_add, width=30)
        blurb.grid(row=9, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[9], bg="#BCF0FE").grid(row=9, column=0, sticky="e")

        emergencyNum = tk.Entry(frame_add, width=30)
        emergencyNum.grid(row=10, column=1, padx=5, pady=5)
        tk.Label(frame_add, text=labels[10], bg="#BCF0FE").grid(row=10, column=0, sticky="e")

        submit = tk.Button(frame_add, text='Submit', width=18, command=addInstructor, bg="white")
        submit.grid(row=11, column=1, padx=5, pady=15)

    # --- EDIT instructor ---
    def edit():
        def EditInstructor():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()

            field_edit = field.get()
            value_edit = value.get().strip()
            search_edit = search_cb.get()

            if not search_edit:
                messagebox.showerror("Error", "Please select an instructor to edit.")
                conn.close()
                return

            iInstructorID = getID_from_combobox(search_edit)

            if not all([field_edit, value_edit, search_edit]):
                messagebox.showerror("Error", "All fields must be filled.")
                conn.close()
                return

            if field_edit == "dateOfBirth":
                ValidDOB = re.match(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$", value_edit)
                if not ValidDOB:
                    messagebox.showerror("Error", "Enter Date of Birth in form DD/MM/YYYY")
                    conn.close()
                    rootEdit.lift()
                    return

            if field_edit in ("mobileNum", "emergencyNum") and not value_edit.isdigit():
                messagebox.showerror("Error", "Mobile/Emergency number must be numeric")
                conn.close()
                rootEdit.lift()
                return

            try:
                cur.execute(f"UPDATE tblInstructor SET {field_edit} = ? WHERE instructorID = ?", (value_edit, iInstructorID))
                conn.commit()
                messagebox.showinfo("Edit Instructor", "You have changed the instructor details")
                rootEdit.destroy()
                DisplayForm()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        # --- Edit window ---
        rootEdit = tk.Toplevel(top)
        rootEdit.geometry("450x210")
        rootEdit.title("Instructor Edit Menu")
        rootEdit.resizable(False, False)
        rootEdit.configure(bg="#7392F0")

        tk.Label(rootEdit, text="Instructor Edit Menu", font=('Aptos', 14), bg="#BCF0FE").place(x=120, y=10)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT firstName, surname, instructorID FROM tblInstructor")
        instructor_rows = cur.fetchall()
        conn.close()

        instructor_list = [f"{r[0]} {r[1]} {r[2]}" for r in instructor_rows]

        tk.Label(rootEdit, text="Instructor Name:", bg="#BCF0FE").place(x=10, y=70)
        search_cb = ttk.Combobox(rootEdit, values=instructor_list, width=28)
        search_cb.place(x=140, y=70)

        tk.Label(rootEdit, text="Field to Change:", bg="#BCF0FE").place(x=10, y=100)
        field = ttk.Combobox(rootEdit, values=("firstName","surname","username","password","mobileNum","dateOfBirth",
                                               "postcode","email","bio","emergencyNum","role"), width=25)
        field.place(x=140, y=100)

        tk.Label(rootEdit, text="New Value:", bg="#BCF0FE").place(x=10, y=130)
        value = tk.Entry(rootEdit, width=29)
        value.place(x=140, y=130)

        tk.Button(rootEdit, text="Submit", width=16, bg="white", command=EditInstructor).place(x=110, y=160)

    # --- DELETE instructor ---
    def delete():
        def deleteInstructor():
            instructor_ID = search_cb.get()
            if not instructor_ID:
                messagebox.showerror("Error", "Select an instructor to delete")
                return
            pk = getID_from_combobox(instructor_ID)

            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM tblInstructor WHERE instructorID = ?", (pk,))
                conn.commit()
                messagebox.showinfo("Instructor Delete", "Instructor has been successfully deleted")
                rdelete.destroy()
                DisplayForm()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        rdelete = tk.Toplevel(top)
        rdelete.geometry('480x150')
        rdelete.title('Instructor Delete Menu')
        rdelete.resizable(False, False)
        rdelete.configure(bg='#7392F0')

        tk.Label(rdelete, text="Instructor Delete Menu", font=('Aptos', 14), bg="#BCF0FE").place(x=120, y=10)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT firstName, surname, instructorID FROM tblInstructor")
        instructor_rows = cur.fetchall()
        conn.close()

        instructor_list = [f"{r[0]} {r[1]} {r[2]}" for r in instructor_rows]

        tk.Label(rdelete, text="Select Instructor:", bg="#BCF0FE", width=18).place(x=0, y=60)
        search_cb = ttk.Combobox(rdelete, values=instructor_list, width=30)
        search_cb.place(x=160, y=60)

        tk.Button(rdelete, text="Submit", width=13, bg="#BCF0FE", command=deleteInstructor).place(x=120, y=100)

    # --- Buttons ---
    tk.Button(btn_frame, text="Add Instructor", width=18, command=add, bg="white").grid(row=0, column=0, padx=8, pady=5)
    tk.Button(btn_frame, text="Edit Instructor", width=18, command=edit, bg="white").grid(row=0, column=1, padx=8, pady=5)
    tk.Button(btn_frame, text="Delete Instructor", width=18, command=delete, bg="white").grid(row=0, column=2, padx=8, pady=5)
    tk.Button(btn_frame, text="Back", width=18, command=destroy_menu, bg="white").grid(row=1, column=1, pady=12)

    DisplayForm()

# ============================================
# LESSON MENU (For Admin/Instructor to create lessons)
# ============================================
def lessonMenu():
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Lesson Management")
    top.geometry("1100x520")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text="Lesson Management (Create Available Slots)", 
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    # --- Search bar ---
    search_frame = tk.Frame(top, bg="#BCF0FE")
    search_frame.pack(pady=5)

    tk.Label(search_frame, text="Search:", bg="#BCF0FE").grid(row=0, column=0, padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.grid(row=0, column=1, padx=5)

    def search_lessons(*args):
        DisplayForm(search_var.get())

    search_var.trace_add("write", search_lessons)

    # --- Treeview ---
    columns = ("ID", "Type", "Date", "Time", "Duration", "Instructor", "Cost", "Status")
    tree_lessons = ttk.Treeview(top, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree_lessons.heading(col, text=col)
        tree_lessons.column(col, width=100)
    
    tree_lessons.pack(pady=10, padx=10)

    # --- Buttons frame ---
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)

    def DisplayForm(search_text=None):
        for item in tree_lessons.get_children():
            tree_lessons.delete(item)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        if search_text:
            like = f"%{search_text}%"
            cur.execute("""
                SELECT l.lessonID, l.lessonType, l.lessonDate, l.lessonTime, 
                       l.duration, i.firstName || ' ' || i.surname, l.cost,
                       CASE WHEN b.bookingID IS NULL THEN 'Available' ELSE 'Booked' END
                FROM tblLesson l
                LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
                LEFT JOIN tblBooking b ON l.lessonID = b.lessonID
                WHERE l.lessonType LIKE ? OR l.lessonDate LIKE ? 
                   OR i.firstName LIKE ? OR i.surname LIKE ?
                ORDER BY l.lessonDate, l.lessonTime
            """, (like, like, like, like))
        else:
            cur.execute("""
                SELECT l.lessonID, l.lessonType, l.lessonDate, l.lessonTime, 
                       l.duration, i.firstName || ' ' || i.surname, l.cost,
                       CASE WHEN b.bookingID IS NULL THEN 'Available' ELSE 'Booked' END
                FROM tblLesson l
                LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
                LEFT JOIN tblBooking b ON l.lessonID = b.lessonID
                ORDER BY l.lessonDate, l.lessonTime
            """)
        
        rows = cur.fetchall()
        conn.close()
        
        for r in rows:
            tree_lessons.insert("", tk.END, values=r)

    # --- ADD Lesson ---
    def add():
        def addLesson():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            
            lesson_type = type_combo.get()
            date = date_entry.get()
            time = time_combo.get()
            duration = duration_combo.get()
            instructor = instructor_combo.get()
            cost = cost_entry.get()
            
            # Validate
            if not all([lesson_type, date, time, duration]):
                messagebox.showerror("Error", "Please fill all required fields")
                return
            
            # Get instructor ID
            instructor_id = None
            if instructor:
                instructor_id = int(instructor.split()[-1])
            
            try:
                cur.execute("""
                    INSERT INTO tblLesson 
                    (lessonType, lessonDate, lessonTime, duration, instructorID, cost)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lesson_type, date, time, duration, instructor_id, cost))
                
                conn.commit()
                messagebox.showinfo("Success", "Lesson slot created successfully")
                root_add.destroy()
                DisplayForm()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        root_add = tk.Toplevel(top)
        root_add.geometry("500x400")
        root_add.title("Create Lesson Slot")
        root_add.configure(bg="#7392F0")
        
        frame = tk.Frame(root_add, bg="#BCF0FE")
        frame.pack(padx=20, pady=20)
        
        # Get instructors for combobox
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT firstName, surname, instructorID FROM tblInstructor")
        instructors = [f"{r[0]} {r[1]} {r[2]}" for r in cur.fetchall()]
        conn.close()
        
        tk.Label(frame, text="Lesson Type:", bg="#BCF0FE").grid(row=0, column=0, sticky="e", pady=10)
        type_combo = ttk.Combobox(frame, values=["Car", "Motorbike", "Lorry"], width=25)
        type_combo.grid(row=0, column=1, pady=10)
        
        tk.Label(frame, text="Date (YYYY-MM-DD):", bg="#BCF0FE").grid(row=1, column=0, sticky="e", pady=10)
        date_entry = tk.Entry(frame, width=27)
        date_entry.grid(row=1, column=1, pady=10)
        
        tk.Label(frame, text="Time:", bg="#BCF0FE").grid(row=2, column=0, sticky="e", pady=10)
        time_combo = ttk.Combobox(frame, values=["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"], width=25)
        time_combo.grid(row=2, column=1, pady=10)
        
        tk.Label(frame, text="Duration (mins):", bg="#BCF0FE").grid(row=3, column=0, sticky="e", pady=10)
        duration_combo = ttk.Combobox(frame, values=["60", "90", "120"], width=25)
        duration_combo.grid(row=3, column=1, pady=10)
        
        tk.Label(frame, text="Instructor:", bg="#BCF0FE").grid(row=4, column=0, sticky="e", pady=10)
        instructor_combo = ttk.Combobox(frame, values=instructors, width=25)
        instructor_combo.grid(row=4, column=1, pady=10)
        
        tk.Label(frame, text="Cost (£):", bg="#BCF0FE").grid(row=5, column=0, sticky="e", pady=10)
        cost_entry = tk.Entry(frame, width=27)
        cost_entry.insert(0, "50")
        cost_entry.grid(row=5, column=1, pady=10)
        
        tk.Button(frame, text="Create Slot", width=20, bg="white", command=addLesson).grid(row=6, column=0, columnspan=2, pady=20)

    # --- DELETE Lesson ---
    def delete():
        def deleteLesson():
            lesson_id = getID_from_combobox(lesson_combo.get())
            if not lesson_id:
                messagebox.showerror("Error", "Select a lesson")
                return
            
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this lesson slot?"):
                conn = sqlite3.connect("drivingschool.db")
                cur = conn.cursor()
                
                try:
                    # Check if lesson has bookings
                    cur.execute("SELECT COUNT(*) FROM tblBooking WHERE lessonID = ?", (lesson_id,))
                    booking_count = cur.fetchone()[0]
                    
                    if booking_count > 0:
                        messagebox.showerror("Cannot Delete", 
                                           "This lesson has bookings. Cancel bookings first.")
                        return
                    
                    cur.execute("DELETE FROM tblLesson WHERE lessonID = ?", (lesson_id,))
                    conn.commit()
                    messagebox.showinfo("Success", "Lesson slot deleted")
                    root_delete.destroy()
                    DisplayForm()
                except Exception as e:
                    messagebox.showerror("Database Error", str(e))
                finally:
                    conn.close()

        root_delete = tk.Toplevel(top)
        root_delete.geometry("500x200")
        root_delete.title("Delete Lesson Slot")
        root_delete.configure(bg="#7392F0")
        
        frame = tk.Frame(root_delete, bg="#BCF0FE")
        frame.pack(padx=20, pady=20)
        
        # Get lessons
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT lessonID, lessonType, lessonDate FROM tblLesson ORDER BY lessonDate")
        lessons = [f"{r[1]} {r[2]} ID:{r[0]}" for r in cur.fetchall()]
        conn.close()
        
        tk.Label(frame, text="Select Lesson to Delete:", bg="#BCF0FE").grid(row=0, column=0, sticky="e", pady=10)
        lesson_combo = ttk.Combobox(frame, values=lessons, width=30)
        lesson_combo.grid(row=0, column=1, pady=10)
        
        tk.Button(frame, text="Delete Slot", width=20, bg="white", command=deleteLesson).grid(row=1, column=0, columnspan=2, pady=20)

    tk.Button(btn_frame, text="Create Lesson Slot", width=18, bg="white", command=add).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Delete Lesson Slot", width=18, bg="white", command=delete).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Back", width=18, bg="white", command=destroy_menu).grid(row=0, column=2, padx=5)

    DisplayForm()

# ============================================
# BOOKING MENU (For Admin/Instructor to manage bookings)
# ============================================
def bookingMenu():
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Booking Management")
    top.geometry("1200x600")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text="Booking Management", font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)
    
    # Frame for main booking management
    main_frame = tk.Frame(top, bg="#BCF0FE")
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Treeview for bookings with cancel option
    columns = ("Booking ID", "Customer", "Lesson Type", "Date", "Time", "Instructor", "Amount Paid", "Status")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.pack(pady=10, padx=10, fill="both", expand=True)
    
    # Function to display bookings
    def display_bookings():
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Load data
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        # DEBUG: Check what's in the booking table
        cur.execute("SELECT * FROM tblBooking")
        all_bookings = cur.fetchall()
        print(f"DEBUG: Total bookings in database: {len(all_bookings)}")
        for booking in all_bookings:
            print(f"  Booking: {booking}")
        
        # Get the detailed booking view
        cur.execute("""
            SELECT b.bookingID, c.firstName || ' ' || c.surname,
                   l.lessonType, l.lessonDate, l.lessonTime,
                   i.firstName || ' ' || i.surname, b.amountPaid, b.paidStatus
            FROM tblBooking b
            JOIN tblCustomer c ON b.customerID = c.customerID
            JOIN tblLesson l ON b.lessonID = l.lessonID
            LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
            ORDER BY l.lessonDate, l.lessonTime
        """)
        
        rows = cur.fetchall()
        conn.close()
        
        print(f"DEBUG: Bookings to display: {len(rows)}")
        
        for row in rows:
            tree.insert("", tk.END, values=row)
    
    # Button frame for actions
    btn_frame = tk.Frame(main_frame, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    
    # Cancel booking function
    def cancel_booking():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking to cancel")
            return
        
        booking_id = tree.item(selected[0])['values'][0]
        
        if messagebox.askyesno("Confirm Cancel", f"Cancel booking {booking_id}?"):
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            
            try:
                cur.execute("DELETE FROM tblBooking WHERE bookingID = ?", (booking_id,))
                conn.commit()
                messagebox.showinfo("Success", "Booking cancelled")
                display_bookings()  # Refresh
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
    
    # Mark as paid function
    def mark_as_paid():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking")
            return
        
        booking_id = tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        try:
            # Get lesson cost
            cur.execute("""
                SELECT l.cost 
                FROM tblBooking b
                JOIN tblLesson l ON b.lessonID = l.lessonID
                WHERE b.bookingID = ?
            """, (booking_id,))
            result = cur.fetchone()
            
            if result:
                cost = result[0]
                
                # Update booking
                cur.execute("""
                    UPDATE tblBooking 
                    SET paidStatus = 'Paid', amountPaid = ?
                    WHERE bookingID = ?
                """, (cost, booking_id))
                
                conn.commit()
                messagebox.showinfo("Success", f"Booking {booking_id} marked as paid: £{cost}")
                display_bookings()
            else:
                messagebox.showerror("Error", "Booking not found")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
    
    # Add a test booking function for debugging
    def add_test_booking():
        """Add a test booking to see if it shows up"""
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        try:
            # Get first customer
            cur.execute("SELECT customerID FROM tblCustomer LIMIT 1")
            customer = cur.fetchone()
            
            # Get first available lesson
            cur.execute("""
                SELECT lessonID FROM tblLesson 
                WHERE lessonID NOT IN (SELECT lessonID FROM tblBooking)
                LIMIT 1
            """)
            lesson = cur.fetchone()
            
            if customer and lesson:
                customer_id = customer[0]
                lesson_id = lesson[0]
                
                cur.execute("""
                    INSERT INTO tblBooking (customerID, lessonID, amountPaid, paidStatus)
                    VALUES (?, ?, 0, 'Unpaid')
                """, (customer_id, lesson_id))
                
                conn.commit()
                print(f"DEBUG: Test booking added - Customer: {customer_id}, Lesson: {lesson_id}")
                messagebox.showinfo("Test", "Test booking added")
                display_bookings()
            else:
                messagebox.showerror("Error", "No customers or available lessons found")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
    
    # Buttons
    tk.Button(btn_frame, text="Refresh", width=18, bg="white", command=display_bookings).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Add Test Booking", width=18, bg="yellow", command=add_test_booking).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Mark as Paid", width=18, bg="white", command=mark_as_paid).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Cancel Booking", width=18, bg="red", fg="white", command=cancel_booking).grid(row=0, column=3, padx=5)
    
    # Back button
    tk.Button(top, text="Back", width=18, bg="white", command=destroy_menu).pack(pady=10)
    
    # Load initial data
    display_bookings()
# ============================================
# PAYMENT MENU (Admin only)
# ============================================
def paymentMenu():
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Payment Management")
    top.geometry("1000x520")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text="Payment Management", font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    # Treeview for unpaid bookings
    columns = ("Booking ID", "Customer", "Lesson", "Date", "Time", "Amount Due", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=12)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.pack(pady=10, padx=10)

    def load_unpaid_bookings():
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        # Get unpaid or partially paid bookings
        cur.execute("""
            SELECT b.bookingID, 
                   c.firstName || ' ' || c.surname,
                   l.lessonType || ' - ' || l.lessonTime,
                   l.lessonDate,
                   l.lessonTime,
                   l.cost - COALESCE(b.amountPaid, 0),
                   b.paidStatus
            FROM tblBooking b
            JOIN tblCustomer c ON b.customerID = c.customerID
            JOIN tblLesson l ON b.lessonID = l.lessonID
            WHERE b.paidStatus != 'Paid' OR b.amountPaid < l.cost
            ORDER BY l.lessonDate
        """)
        
        rows = cur.fetchall()
        conn.close()
        
        for row in rows:
            tree.insert("", tk.END, values=row)
    
    # Payment frame
    payment_frame = tk.Frame(top, bg="#BCF0FE")
    payment_frame.pack(pady=10)
    
    tk.Label(payment_frame, text="Booking ID:", bg="#BCF0FE").grid(row=0, column=0, padx=5)
    booking_id_entry = tk.Entry(payment_frame, width=15)
    booking_id_entry.grid(row=0, column=1, padx=5)
    
    tk.Label(payment_frame, text="Amount to Pay (£):", bg="#BCF0FE").grid(row=0, column=2, padx=5)
    amount_entry = tk.Entry(payment_frame, width=15)
    amount_entry.grid(row=0, column=3, padx=5)
    
    def process_payment():
        try:
            booking_id = int(booking_id_entry.get())
            amount = float(amount_entry.get())
        except:
            messagebox.showerror("Error", "Enter valid numbers")
            return
        
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than 0")
            return
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        try:
            # Get current payment status
            cur.execute("SELECT amountPaid, paidStatus FROM tblBooking WHERE bookingID = ?", (booking_id,))
            result = cur.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Booking not found")
                return
            
            current_paid, current_status = result
            
            # Get lesson cost
            cur.execute("""
                SELECT l.cost 
                FROM tblBooking b
                JOIN tblLesson l ON b.lessonID = l.lessonID
                WHERE b.bookingID = ?
            """, (booking_id,))
            lesson_cost_result = cur.fetchone()
            if not lesson_cost_result:
                messagebox.showerror("Error", "Lesson not found")
                return
            lesson_cost = lesson_cost_result[0]
            
            new_paid = current_paid + amount
            new_status = "Paid" if new_paid >= lesson_cost else "Partially Paid"
            
            # Update booking
            cur.execute("""
                UPDATE tblBooking 
                SET amountPaid = ?, paidStatus = ?
                WHERE bookingID = ?
            """, (new_paid, new_status, booking_id))
            
            conn.commit()
            
            messagebox.showinfo("Success", 
                              f"Payment processed: £{amount}\n"
                              f"Total paid: £{new_paid}/{lesson_cost}\n"
                              f"Status: {new_status}")
            
            booking_id_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            load_unpaid_bookings()
            
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()
    
    tk.Button(payment_frame, text="Process Payment", bg="green", fg="white",
             command=process_payment, width=15).grid(row=0, column=4, padx=5)
    
    # Load data initially
    load_unpaid_bookings()
    
    # Back button
    tk.Button(top, text="Back", width=18, bg="white", command=destroy_menu).pack(pady=10)

# ============================================
# CUSTOMER BOOKING MENU (For Customers only)
# ============================================
def customerBookingMenu():
    """Simple booking interface for customers to view available lessons"""
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Book a Lesson")
    top.geometry("900x500")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text=f"Book a Lesson - {current_user_name}", 
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)
    
    # Frame for available lessons
    frame = tk.Frame(top, bg="#BCF0FE")
    frame.pack(pady=10)
    
    tk.Label(frame, text="Available Lessons:", font=("Aptos", 12), bg="#BCF0FE").grid(row=0, column=0, columnspan=3, pady=10)
    
    # Treeview for available lessons
    columns = ("Date", "Time", "Type", "Duration", "Instructor", "Cost")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    
    tree.grid(row=1, column=0, columnspan=3, pady=10)
    
    def load_available_lessons():
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        # Get available lessons (not booked)
        cur.execute("""
            SELECT l.lessonDate, l.lessonTime, l.lessonType, l.duration, 
                   i.firstName || ' ' || i.surname, l.cost, l.lessonID
            FROM tblLesson l
            LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
            WHERE l.lessonID NOT IN (SELECT lessonID FROM tblBooking)
            AND l.lessonDate >= date('now')
            ORDER BY l.lessonDate, l.lessonTime
        """)
        
        lessons = cur.fetchall()
        conn.close()
        
        for lesson in lessons:
            # Display all but lessonID
            tree.insert("", tk.END, values=lesson[:-1], tags=(lesson[-1],))
    
    def book_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a lesson to book")
            return
        
        lesson_id = tree.item(selected[0])['tags'][0]
        
        if messagebox.askyesno("Confirm Booking", "Book this lesson?"):
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            
            try:
                cur.execute("""
                    INSERT INTO tblBooking (customerID, lessonID, amountPaid, paidStatus)
                    VALUES (?, ?, 0, 'Unpaid')
                """, (current_user_id, lesson_id))
                
                conn.commit()
                messagebox.showinfo("Success", "Lesson booked successfully!\nPlease visit the school to make payment.")
                load_available_lessons()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
    
    tk.Button(frame, text="Refresh Available Lessons", bg="white",
              command=load_available_lessons, width=20).grid(row=2, column=0, pady=10)
    
    tk.Button(frame, text="Book Selected Lesson", bg="green", fg="white",
              command=book_selected, width=20).grid(row=2, column=1, pady=10)
    
    tk.Button(frame, text="Back", bg="white", command=destroy_menu, width=20).grid(row=2, column=2, pady=10)
    
    # Load initially
    load_available_lessons()

# ============================================
# CUSTOMER VIEW BOOKINGS MENU
# ============================================
def customerViewBookings():
    """Customers can view their own bookings"""
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("My Bookings")
    top.geometry("1000x400")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text=f"My Bookings - {current_user_name}", 
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)
    
    # Treeview for bookings
    columns = ("Booking ID", "Lesson Type", "Date", "Time", "Instructor", "Amount Paid", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    
    tree.pack(pady=10, padx=10)
    
    def load_my_bookings():
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        
        # Get this customer's bookings
        cur.execute("""
            SELECT b.bookingID, l.lessonType, l.lessonDate, l.lessonTime,
                   i.firstName || ' ' || i.surname, b.amountPaid, b.paidStatus
            FROM tblBooking b
            JOIN tblLesson l ON b.lessonID = l.lessonID
            LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
            WHERE b.customerID = ?
            ORDER BY l.lessonDate, l.lessonTime
        """, (current_user_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        for row in rows:
            tree.insert("", tk.END, values=row)
    
    # Button frame
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="Refresh", bg="white", command=load_my_bookings, width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Back", bg="white", command=destroy_menu, width=15).pack(side="left", padx=5)
    
    # Load initially
    load_my_bookings()

def logout():
    global current_user_id, current_user_role, current_user_name
    current_user_id = None
    current_user_role = None
    current_user_name = None
    root.destroy()
    login_screen()

def mainMenu():
    global root
    root = tk.Tk()
    root.geometry("550x500")
    root.title(f"Main Menu - {current_user_name} ({current_user_role})")
    root.resizable(False, False)
    root.configure(bg="#7392F0")
    
    frametitle = tk.Frame(root, bg="#BCF0FE")
    frametitle.grid(row=0, column=0, padx=150, pady=20)

    try:
        img = Image.open("logo.jpeg")
        img = img.resize((150, 150))           
        logo_img = ImageTk.PhotoImage(img)
        logo_label = tk.Label(frametitle, image=logo_img, bg="#BCF0FE")
        logo_label.image = logo_img            
        logo_label.grid(row=0, column=0, padx=20, pady=20)
    except FileNotFoundError:
        tk.Label(frametitle, text="Logo not found", font=("Aptos", 16), bg="#BCF0FE").grid(row=0, column=0, padx=20, pady=20)

    framebutton = tk.Frame(root, bg="#BCF0FE")
    framebutton.grid(row=1, column=0, padx=20, pady=20)

    tk.Button(framebutton, text="Customer Menu", width=18, bg="white", command=customerMenu).grid(row=0, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="Instructor Menu", width=18, bg="white", command=instructorMenu).grid(row=0, column=1, padx=20, pady=15)

    tk.Button(framebutton, text="Lesson Menu", width=18, bg="white", command=lessonMenu).grid(row=1, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="Booking Menu", width=18, bg="white", command=bookingMenu).grid(row=1, column=1, padx=20, pady=15)

    tk.Button(framebutton, text="Payment Menu", width=18, bg="white", command=paymentMenu).grid(row=2, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="Log Out", width=18, bg="white", command=logout).grid(row=2, column=1, padx=20, pady=15)

def mainMenu2():
    """Customer Menu with Payment option added back"""
    global root
    root = tk.Tk()  
    root.geometry("280x650")  # Increased height for additional button
    root.title(f"Customer Menu - {current_user_name}")
    root.resizable(False, False)
    root.configure(bg="#7392F0")

    frametitle = tk.Frame(root, bg="#BCF0FE")
    frametitle.grid(row=0, column=0, padx=10, pady=10)
    
    try:
        img = Image.open("logo.jpeg")         
        img = img.resize((150, 150))          
        logo_img = ImageTk.PhotoImage(img)
        logo_label = tk.Label(frametitle, image=logo_img, bg="#BCF0FE")
        logo_label.image = logo_img           
        logo_label.grid(row=0, column=0, padx=20, pady=20)
    except FileNotFoundError:
        tk.Label(frametitle, text="Logo not found", font=("Aptos", 16), bg="#BCF0FE").grid(row=0, column=0, padx=20, pady=20)

    framebutton = tk.Frame(root, bg="#BCF0FE")
    framebutton.grid(row=1, column=0, padx=15, pady=15)

    # Customer menu options - WITH PAYMENT MENU ADDED BACK
    tk.Button(framebutton, text="Book a Lesson", bg="white", width=18, command=customerBookingMenu).grid(row=0, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="View My Bookings", bg="white", width=18, command=customerViewBookings).grid(row=1, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="My Payments", bg="white", width=18, command=customerPaymentMenu).grid(row=2, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="Log Out", bg="white", width=18, command=logout).grid(row=3, column=0, padx=20, pady=15)

# -----------------------------
# START THE APP
# -----------------------------
if __name__ == "__main__":
    login_screen()
    tk.mainloop()