#import modules

import sqlite3
import tkinter as tk
from tkinter import ttk,messagebox
import re
from PIL import Image, ImageTk
import datetime
import random

# ============================================
# DATABASE SETUP (with UNIQUE constraints)
# ============================================
connection = sqlite3.connect("drivingschool.db")
cursor = connection.cursor()

# Instructor table
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

# Customer table – now with UNIQUE to prevent duplicates
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblCustomer
(
    customerID INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    surname TEXT NOT NULL,
    mobileNum TEXT UNIQUE,
    dateOfBirth DATE,
    postcode TEXT,
    email TEXT,
    emergencyNum TEXT,
    UNIQUE(firstName, surname, mobileNum)
)
"""
cursor.execute(sqlCommand)

# Lesson table
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblLesson
(
    lessonID INTEGER PRIMARY KEY AUTOINCREMENT,
    lessonType TEXT NOT NULL,
    lessonDate DATE NOT NULL,
    lessonTime TEXT NOT NULL,
    duration INTEGER,
    instructorID INTEGER,
    cost REAL,
    FOREIGN KEY (instructorID) REFERENCES tblInstructor(instructorID)
)
"""
cursor.execute(sqlCommand)

# Booking table
sqlCommand = """
CREATE TABLE IF NOT EXISTS tblBooking
(
    bookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    customerID INTEGER NOT NULL,
    lessonID INTEGER NOT NULL,
    amountPaid REAL,
    paidStatus TEXT,
    FOREIGN KEY (customerID) REFERENCES tblCustomer(customerID),
    FOREIGN KEY (lessonID) REFERENCES tblLesson(lessonID)
)
"""
cursor.execute(sqlCommand)

connection.commit()
connection.close()

# ============================================
# GLOBAL VARIABLES
# ============================================
current_user_id = None
current_user_role = None
current_user_name = None

# ============================================
# HELPER FUNCTIONS
# ============================================
def presenceCheck(rec):
    presence = True
    for x in range(len(rec)):
        if rec[x].strip() == "":
            presence = False
    return presence

def stringVal2(text):
    valid = True
    for x in range(len(text)):
        if ord(text[x]) not in range (65,91) and ord(text[x]) not in range(97,123):
            valid = False
    return valid

def getID_from_combobox(text):
    try:
        return int(text.split()[-1])
    except:
        return None

# ============================================
# DEFAULT DATA – NEVER DELETES, PRESERVES IDs
# ============================================
def create_default_data():
    """Create default demo data ONLY if it doesn't already exist."""
    conn = sqlite3.connect("drivingschool.db")
    cur = conn.cursor()
    
    try:
        # ----- INSTRUCTORS (INSERT OR IGNORE) -----
        default_instructors = [
            ("John", "Smith", "admin", "admin123", "07123456789", "01/01/1980", "AB1 2CD",
             "john@lddriving.com", "Experienced instructor", "07987654321", "Owner"),
            ("Sarah", "Johnson", "sarah", "sarah123", "07234567890", "15/05/1985", "CD2 3EF",
             "sarah@lddriving.com", "Friendly and patient", "07111111111", "Instructor"),
            ("Mike", "Brown", "mike", "mike123", "07345678901", "20/10/1990", "EF3 4GH",
             "mike@lddriving.com", "Specializes in motorway lessons", "07222222222", "Instructor")
        ]
        for inst in default_instructors:
            cur.execute("""
                INSERT OR IGNORE INTO tblInstructor 
                (firstName, surname, username, password, mobileNum, dateOfBirth, postcode, email, bio, emergencyNum, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, inst)

        # ----- CUSTOMERS – only insert if not already present -----
        default_customers = [
            ("Alice", "Wilson", "07456789012", "12/03/2000", "GH4 5IJ", "alice@email.com", "07555555555"),
            ("Bob", "Davis", "07567890123", "25/07/1998", "IJ5 6KL", "bob@email.com", "07666666666"),
            ("Charlie", "Miller", "07678901234", "03/11/1995", "KL6 7MN", "charlie@email.com", "07777777777")
        ]
        for cust in default_customers:
            cur.execute("SELECT COUNT(*) FROM tblCustomer WHERE firstName=? AND surname=? AND mobileNum=?",
                       (cust[0], cust[1], cust[2]))
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO tblCustomer 
                    (firstName, surname, mobileNum, dateOfBirth, postcode, email, emergencyNum)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, cust)

        # ----- LESSONS – only if none exist -----
        cur.execute("SELECT COUNT(*) FROM tblLesson")
        if cur.fetchone()[0] == 0:
            today = datetime.date.today()
            for i in range(1, 8):
                lesson_date = today + datetime.timedelta(days=i)
                date_str = lesson_date.strftime("%Y-%m-%d")
                for time_slot in ["09:00", "11:00", "14:00", "16:00"]:
                    lesson_types = ["Car", "Motorbike", "Lorry"]
                    cur.execute("SELECT instructorID FROM tblInstructor ORDER BY RANDOM() LIMIT 1")
                    row = cur.fetchone()
                    instructor_id = row[0] if row else 1
                    cur.execute("""
                        INSERT OR IGNORE INTO tblLesson 
                        (lessonType, lessonDate, lessonTime, duration, instructorID, cost)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (random.choice(lesson_types), date_str, time_slot, 60,
                          instructor_id, random.choice([50, 60, 70])))

        conn.commit()
        print("✅ Default data verified – IDs are stable.")
        print("   Admin: admin / admin123")
        print("   Instructor: sarah / sarah123")
        print("   Customers: Alice Wilson (07456789012), Bob Davis (07567890123)")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

# ============================================
# LOGIN SYSTEM
# ============================================
def login_screen():
    global current_user_id, current_user_role, current_user_name
    create_default_data()
    
    root = tk.Tk()
    root.geometry("400x650")
    root.title("LD Driving School - Login")
    root.resizable(False, False)
    root.configure(bg="#7392F0")
    
    frame = tk.Frame(root, bg="#BCF0FE")
    frame.pack(padx=30, pady=30)
    
    tk.Label(frame, text="LD Driving School", font=("Aptos", 18, "bold"),
             bg="#BCF0FE").grid(row=0, column=0, columnspan=2, pady=20)
    
    # Logo
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
    tk.Label(demo_frame, text="Admin: admin / admin123", bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    tk.Label(demo_frame, text="Instructor: sarah / sarah123", bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    tk.Label(demo_frame, text="Customer: Alice Wilson / 07456789012", bg="#BCF0FE", font=("Arial", 9)).pack(pady=2)
    
    notebook = ttk.Notebook(frame)
    notebook.grid(row=3, column=0, columnspan=2, pady=10)
    
    # ---------- Staff Login ----------
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
    
    tk.Button(instructor_frame, text="Login", width=15, bg="white",
              command=authenticate_instructor).grid(row=2, column=0, columnspan=2, pady=20)
    
    # ---------- Customer Login ----------
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
            if messagebox.askyesno("Not Found", "Customer not found. Would you like to register?"):
                register_customer(first, last, mobile)
            conn.close()
    
    def register_customer(first, last, mobile):
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO tblCustomer (firstName, surname, mobileNum)
                VALUES (?, ?, ?)
            """, (first, last, mobile))
            conn.commit()
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
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Mobile number already registered.")
        except Exception as e:
            conn.close()
            messagebox.showerror("Registration Error", str(e))
    
    tk.Button(customer_frame, text="Login/Register", width=15, bg="white",
              command=authenticate_customer).grid(row=3, column=0, columnspan=2, pady=20)
    
    root.mainloop()

# ============================================
# ADMIN/INSTRUCTOR MENUS
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
    
    # ---------- ADD CUSTOMER ----------
    def add():
        def addCustomer():
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            data = (
                firstname.get(), surname.get(), mobileNum.get(),
                dob.get(), postcode.get(), email.get(), emergencyNum.get()
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
            try:
                cur.execute("INSERT INTO tblcustomer VALUES (NULL,?,?,?,?,?,?,?)", data)
                conn.commit()
                messagebox.showinfo("Success", "Customer added")
                root_add.destroy()
                DisplayForm()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Mobile number already exists.")
            finally:
                conn.close()
        
        root_add = tk.Toplevel(top)
        root_add.geometry("500x400")
        root_add.title("Add Customer")
        root_add.configure(bg="#7392F0")
        frame = tk.Frame(root_add, bg="#BCF0FE")
        frame.pack(padx=10, pady=10)
        labels = ["First Name:", "Surname:", "Mobile Number:", "Date of Birth:",
                  "Postcode:", "Email:", "Emergency Number:"]
        entries = []
        for i, lbl in enumerate(labels):
            tk.Label(frame, text=lbl, bg="#BCF0FE").grid(row=i, column=0, sticky="e", pady=4)
            e = tk.Entry(frame, width=25)
            e.grid(row=i, column=1, pady=4)
            entries.append(e)
        firstname, surname, mobileNum, dob, postcode, email, emergencyNum = entries
        tk.Button(frame, text="Submit", width=18, bg="white", command=addCustomer).grid(row=7, column=1, pady=12)
    
    # ---------- EDIT CUSTOMER ----------
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
            try:
                cur.execute(f"UPDATE tblcustomer SET {field.get()} = ? WHERE customerID = ?", (value.get(), cid))
                conn.commit()
                messagebox.showinfo("Success", "Customer updated")
                rootEdit.destroy()
                DisplayForm()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Mobile number already in use.")
            finally:
                conn.close()
        
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
    
    # ---------- DELETE CUSTOMER ----------
    def delete():
        def deleteCustomer():
            cid = getID_from_combobox(search_cb.get())
            if not cid:
                messagebox.showerror("Error", "Select a customer")
                return
            if messagebox.askyesno("Confirm Delete", "Are you sure?"):
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

def instructorMenu():
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
    
    # Search bar
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
    
    # Treeview
    columns = ("ID", "First Name", "Surname", "Username", "Mobile", "Role")
    tree_instructors = ttk.Treeview(top, columns=columns, show="headings", height=10)
    for col in columns:
        tree_instructors.heading(col, text=col)
        tree_instructors.column(col, width=120 if col != "Username" else 140)
    tree_instructors.pack(pady=5)
    
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    
    def DisplayForm(search_text=None):
        if search_text is None:
            search_text = search_var.get()
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
    
    # ---------- ADD INSTRUCTOR ----------
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
            if len(iFirstName) == 0 or len(iSurname) == 0 or len(iUsername) == 0 or len(iPassword) == 0 or len(iRole) == 0:
                validation = False
                messagebox.showerror("Error", "Some required fields are empty")
                conn.close()
                return
            if len(iFirstName) > 15:
                validation = False
                messagebox.showerror("Error", "First Name must be below 15 characters")
            elif len(iSurname) > 20:
                validation = False
                messagebox.showerror("Error", "Surname must be below 20 characters")
            elif len(iUsername) > 15:
                validation = False
                messagebox.showerror("Error", "Username must be below 15 characters")
            elif len(iPassword) > 15:
                validation = False
                messagebox.showerror("Error", "Password must be below 15 characters")
            elif len(iRole) > 30:
                validation = False
                messagebox.showerror("Error", "Role must be below 30 characters")
            elif iMobileNum and len(iMobileNum) != 11:
                validation = False
                messagebox.showerror("Error", "Mobile Number must be 11 digits")
            elif iDob and len(iDob) != 10:
                validation = False
                messagebox.showerror("Error", "DOB must be exactly 10 characters (DD/MM/YYYY)")
            elif iPostcode and (len(iPostcode) > 8 or len(iPostcode) < 5):
                validation = False
                messagebox.showerror("Error", "Postcode must be between 5-7 characters")
            elif iEmail and len(iEmail) > 50:
                validation = False
                messagebox.showerror("Error", "Email must be below 50 characters")
            elif iBlurb and len(iBlurb) > 750:
                validation = False
                messagebox.showerror("Error", "Bio must be below 750 characters")
            elif iEmergencyNum and len(iEmergencyNum) != 11:
                validation = False
                messagebox.showerror("Error", "Emergency number must be 11 digits")
            if not stringVal2(iSurname):
                validation = False
                messagebox.showerror("Error", "Surname must contain only letters")
            if not stringVal2(iFirstName):
                validation = False
                messagebox.showerror("Error", "First name must contain only letters")
            if iMobileNum and not iMobileNum.isdigit():
                validation = False
                messagebox.showerror("Error", "Mobile number must be numeric")
            if iEmergencyNum and not iEmergencyNum.isdigit():
                validation = False
                messagebox.showerror("Error", "Emergency number must be numeric")
            if iDob:
                ValidDOB = re.match(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$", iDob)
                if not ValidDOB:
                    validation = False
                    messagebox.showerror("Error", "DOB must be DD/MM/YYYY")
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
                    except sqlite3.IntegrityError:
                        messagebox.showerror("Error", "Username must be unique.")
                        conn.rollback()
                else:
                    messagebox.showerror("Error", "All fields must be filled.")
            conn.close()
        
        # Add window
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
    
    # ---------- EDIT INSTRUCTOR ----------
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
                    return
            if field_edit in ("mobileNum", "emergencyNum") and not value_edit.isdigit():
                messagebox.showerror("Error", "Mobile/Emergency number must be numeric")
                conn.close()
                return
            try:
                cur.execute(f"UPDATE tblInstructor SET {field_edit} = ? WHERE instructorID = ?", (value_edit, iInstructorID))
                conn.commit()
                messagebox.showinfo("Edit Instructor", "Instructor details updated")
                rootEdit.destroy()
                DisplayForm()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()
        
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
    
    # ---------- DELETE INSTRUCTOR ----------
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
                messagebox.showinfo("Instructor Delete", "Instructor deleted successfully")
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
    
    # Buttons
    tk.Button(btn_frame, text="Add Instructor", width=18, command=add, bg="white").grid(row=0, column=0, padx=8, pady=5)
    tk.Button(btn_frame, text="Edit Instructor", width=18, command=edit, bg="white").grid(row=0, column=1, padx=8, pady=5)
    tk.Button(btn_frame, text="Delete Instructor", width=18, command=delete, bg="white").grid(row=0, column=2, padx=8, pady=5)
    tk.Button(btn_frame, text="Back", width=18, command=destroy_menu, bg="white").grid(row=1, column=1, pady=12)
    
    DisplayForm()

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
    
    # Search bar
    search_frame = tk.Frame(top, bg="#BCF0FE")
    search_frame.pack(pady=5)
    tk.Label(search_frame, text="Search:", bg="#BCF0FE").grid(row=0, column=0, padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.grid(row=0, column=1, padx=5)
    def search_lessons(*args):
        DisplayForm(search_var.get())
    search_var.trace_add("write", search_lessons)
    
    # Treeview
    columns = ("ID", "Type", "Date", "Time", "Duration", "Instructor", "Cost", "Status")
    tree_lessons = ttk.Treeview(top, columns=columns, show="headings", height=10)
    for col in columns:
        tree_lessons.heading(col, text=col)
        tree_lessons.column(col, width=100)
    tree_lessons.pack(pady=10, padx=10)
    
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
    
    # ---------- ADD LESSON ----------
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
            if not all([lesson_type, date, time, duration]):
                messagebox.showerror("Error", "Please fill all required fields")
                return
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
        time_combo = ttk.Combobox(frame, values=["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00"], width=25)
        time_combo.grid(row=2, column=1, pady=10)
        tk.Label(frame, text="Duration (mins):", bg="#BCF0FE").grid(row=3, column=0, sticky="e", pady=10)
        duration_combo = ttk.Combobox(frame, values=["60","90","120"], width=25)
        duration_combo.grid(row=3, column=1, pady=10)
        tk.Label(frame, text="Instructor:", bg="#BCF0FE").grid(row=4, column=0, sticky="e", pady=10)
        instructor_combo = ttk.Combobox(frame, values=instructors, width=25)
        instructor_combo.grid(row=4, column=1, pady=10)
        tk.Label(frame, text="Cost (£):", bg="#BCF0FE").grid(row=5, column=0, sticky="e", pady=10)
        cost_entry = tk.Entry(frame, width=27)
        cost_entry.insert(0, "50")
        cost_entry.grid(row=5, column=1, pady=10)
        tk.Button(frame, text="Create Slot", width=20, bg="white", command=addLesson).grid(row=6, column=0, columnspan=2, pady=20)
    
    # ---------- DELETE LESSON ----------
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
                    cur.execute("SELECT COUNT(*) FROM tblBooking WHERE lessonID = ?", (lesson_id,))
                    booking_count = cur.fetchone()[0]
                    if booking_count > 0:
                        messagebox.showerror("Cannot Delete", "This lesson has bookings. Cancel bookings first.")
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

def bookingMenu():
    global root
    root.withdraw()
    top = tk.Toplevel(root)
    top.title("Booking Management")
    top.geometry("1300x600")
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")
    
    def destroy_menu():
        top.destroy()
        root.deiconify()
    
    tk.Label(top, text="Booking Management", font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)
    
    main_frame = tk.Frame(top, bg="#BCF0FE")
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    columns = ("Booking ID", "Customer ID", "Customer Name", "Lesson ID", "Lesson Type", "Date", "Time", "Instructor", "Amount Paid", "Status")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
    col_widths = {"Booking ID":80, "Customer ID":80, "Customer Name":150, "Lesson ID":80,
                  "Lesson Type":100, "Date":100, "Time":80, "Instructor":150, "Amount Paid":100, "Status":100}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths[col])
    tree.pack(pady=10, padx=10, fill="both", expand=True)
    
    def display_bookings():
        for item in tree.get_children():
            tree.delete(item)
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    b.bookingID,
                    b.customerID,
                    COALESCE(c.firstName || ' ' || c.surname, 'DELETED CUSTOMER') as customer_name,
                    b.lessonID,
                    COALESCE(l.lessonType, 'DELETED LESSON') as lesson_type,
                    COALESCE(l.lessonDate, 'N/A') as lesson_date,
                    COALESCE(l.lessonTime, 'N/A') as lesson_time,
                    COALESCE(i.firstName || ' ' || i.surname, 'NO INSTRUCTOR') as instructor_name,
                    COALESCE(b.amountPaid, 0) as amount_paid,
                    COALESCE(b.paidStatus, 'UNKNOWN') as status
                FROM tblBooking b
                LEFT JOIN tblCustomer c ON b.customerID = c.customerID
                LEFT JOIN tblLesson l ON b.lessonID = l.lessonID
                LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
                ORDER BY
                    CASE WHEN l.lessonDate IS NULL THEN 1 ELSE 0 END,
                    l.lessonDate, l.lessonTime
            """)
            rows = cur.fetchall()
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()
    
    def fix_foreign_keys():
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        issues_found = False
        fixes_applied = 0
        print("\n" + "="*50)
        print("FOREIGN KEY CHECK & FIX")
        print("="*50)
        cur.execute("SELECT bookingID, customerID, lessonID FROM tblBooking")
        bookings = cur.fetchall()
        for booking_id, customer_id, lesson_id in bookings:
            print(f"\nChecking booking {booking_id}: CustomerID {customer_id}, LessonID {lesson_id}")
            cur.execute("SELECT COUNT(*) FROM tblCustomer WHERE customerID = ?", (customer_id,))
            customer_exists = cur.fetchone()[0] > 0
            cur.execute("SELECT COUNT(*) FROM tblLesson WHERE lessonID = ?", (lesson_id,))
            lesson_exists = cur.fetchone()[0] > 0
            if not customer_exists:
                print(f"  ❌ Customer {customer_id} does not exist!")
                issues_found = True
                cur.execute("SELECT customerID FROM tblCustomer LIMIT 1")
                valid_customer = cur.fetchone()
                if valid_customer:
                    new_customer_id = valid_customer[0]
                    cur.execute("UPDATE tblBooking SET customerID = ? WHERE bookingID = ?", (new_customer_id, booking_id))
                    print(f"  ✅ Fixed: Updated to CustomerID {new_customer_id}")
                    fixes_applied += 1
                else:
                    print("  ❌ No valid customers found!")
            if not lesson_exists:
                print(f"  ❌ Lesson {lesson_id} does not exist!")
                issues_found = True
                cur.execute("SELECT lessonID FROM tblLesson LIMIT 1")
                valid_lesson = cur.fetchone()
                if valid_lesson:
                    new_lesson_id = valid_lesson[0]
                    cur.execute("UPDATE tblBooking SET lessonID = ? WHERE bookingID = ?", (new_lesson_id, booking_id))
                    print(f"  ✅ Fixed: Updated to LessonID {new_lesson_id}")
                    fixes_applied += 1
                else:
                    print("  ❌ No valid lessons found!")
            if customer_exists and lesson_exists:
                print(f"  ✅ All foreign keys valid")
        if fixes_applied > 0:
            conn.commit()
            print(f"\n✅ Applied {fixes_applied} fixes")
        else:
            print(f"\n✅ No issues found")
        conn.close()
        messagebox.showinfo("Foreign Key Check", f"Fixes applied: {fixes_applied}")
        display_bookings()
    
    def cancel_booking():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking to cancel")
            return
        booking_id = tree.item(selected[0])['values'][0]
        customer_name = tree.item(selected[0])['values'][2]
        if messagebox.askyesno("Confirm Cancel", f"Cancel booking {booking_id} for {customer_name}?"):
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM tblBooking WHERE bookingID = ?", (booking_id,))
                conn.commit()
                messagebox.showinfo("Success", f"Booking {booking_id} cancelled")
                display_bookings()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
    
    def mark_as_paid():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a booking")
            return
        booking_id = tree.item(selected[0])['values'][0]
        lesson_id = tree.item(selected[0])['values'][3]
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        try:
            cur.execute("SELECT cost FROM tblLesson WHERE lessonID = ?", (lesson_id,))
            result = cur.fetchone()
            cost = result[0] if result else 50
            cur.execute("UPDATE tblBooking SET paidStatus = 'Paid', amountPaid = ? WHERE bookingID = ?", (cost, booking_id))
            conn.commit()
            messagebox.showinfo("Success", f"Booking {booking_id} marked as paid: £{cost}")
            display_bookings()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
    
    def create_manual_booking():
        manual_window = tk.Toplevel(top)
        manual_window.title("Create Manual Booking")
        manual_window.geometry("500x350")
        manual_window.configure(bg="#7392F0")
        tk.Label(manual_window, text="Create Manual Booking", font=("Aptos", 14), bg="#BCF0FE").pack(pady=10)
        frame = tk.Frame(manual_window, bg="#BCF0FE")
        frame.pack(padx=20, pady=10)
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
        cur.execute("SELECT customerID, firstName, surname FROM tblCustomer ORDER BY surname")
        customers = cur.fetchall()
        cur.execute("""
            SELECT l.lessonID, l.lessonType, l.lessonDate, l.lessonTime,
                   i.firstName || ' ' || i.surname as instructor
            FROM tblLesson l
            LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
            WHERE l.lessonID NOT IN (SELECT lessonID FROM tblBooking)
            AND l.lessonDate >= date('now')
            ORDER BY l.lessonDate, l.lessonTime
        """)
        available_lessons = cur.fetchall()
        conn.close()
        if not customers:
            messagebox.showerror("Error", "No customers in database!")
            manual_window.destroy()
            return
        if not available_lessons:
            messagebox.showerror("Error", "No available lessons!")
            manual_window.destroy()
            return
        tk.Label(frame, text="Customer:", bg="#BCF0FE").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        customer_var = tk.StringVar()
        customer_list = [f"{c[1]} {c[2]} (ID: {c[0]})" for c in customers]
        customer_combo = ttk.Combobox(frame, textvariable=customer_var, values=customer_list, width=35)
        customer_combo.grid(row=0, column=1, padx=5, pady=5)
        customer_combo.current(0)
        tk.Label(frame, text="Available Lesson:", bg="#BCF0FE").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        lesson_var = tk.StringVar()
        lesson_list = [f"{l[2]} {l[3]} - {l[1]} with {l[4]} (ID: {l[0]})" for l in available_lessons]
        lesson_combo = ttk.Combobox(frame, textvariable=lesson_var, values=lesson_list, width=35)
        lesson_combo.grid(row=1, column=1, padx=5, pady=5)
        if lesson_list:
            lesson_combo.current(0)
        tk.Label(frame, text="Payment Status:", bg="#BCF0FE").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        status_var = tk.StringVar(value="Unpaid")
        status_combo = ttk.Combobox(frame, textvariable=status_var, values=["Paid", "Unpaid"], width=32)
        status_combo.grid(row=2, column=1, padx=5, pady=5)
        def save_manual_booking():
            if not customer_var.get() or not lesson_var.get():
                messagebox.showerror("Error", "Select both customer and lesson")
                return
            try:
                customer_text = customer_var.get()
                customer_id = int(customer_text.split("ID: ")[1].strip(")"))
                lesson_text = lesson_var.get()
                lesson_id = int(lesson_text.split("ID: ")[1].strip(")"))
            except (IndexError, ValueError):
                messagebox.showerror("Error", "Invalid selection format")
                return
            conn = sqlite3.connect("drivingschool.db")
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM tblBooking WHERE lessonID = ?", (lesson_id,))
                if cur.fetchone()[0] > 0:
                    messagebox.showerror("Error", "This lesson was just booked by someone else!")
                    conn.close()
                    return
                amount_paid = 50 if status_var.get() == "Paid" else 0
                cur.execute("""
                    INSERT INTO tblBooking (customerID, lessonID, amountPaid, paidStatus)
                    VALUES (?, ?, ?, ?)
                """, (customer_id, lesson_id, amount_paid, status_var.get()))
                conn.commit()
                messagebox.showinfo("Success", f"Booking created!\nCustomer ID: {customer_id}\nLesson ID: {lesson_id}")
                manual_window.destroy()
                display_bookings()
            except sqlite3.IntegrityError as e:
                messagebox.showerror("Database Error", f"Foreign key error: {e}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()
        tk.Button(frame, text="Create Booking", bg="green", fg="white",
                 command=save_manual_booking, width=20).grid(row=3, column=1, pady=15)
    
    btn_frame = tk.Frame(main_frame, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Refresh", width=18, bg="white", command=display_bookings).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Manual Booking", width=18, bg="white", command=create_manual_booking).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Mark as Paid", width=18, bg="white", command=mark_as_paid).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="Cancel Booking", width=18, bg="red", fg="white", command=cancel_booking).grid(row=0, column=3, padx=5)
    tk.Button(btn_frame, text="Fix Foreign Keys", width=18, bg="yellow", command=fix_foreign_keys).grid(row=0, column=4, padx=5)
    
    tk.Button(top, text="Back", width=18, bg="white", command=destroy_menu).pack(pady=10)
    display_bookings()

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
    
    columns = ("Booking ID", "Customer", "Lesson", "Date", "Time", "Amount Due", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=12)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(pady=10, padx=10)
    
    def load_unpaid_bookings():
        for item in tree.get_children():
            tree.delete(item)
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
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
            cur.execute("SELECT amountPaid, paidStatus FROM tblBooking WHERE bookingID = ?", (booking_id,))
            result = cur.fetchone()
            if not result:
                messagebox.showerror("Error", "Booking not found")
                return
            current_paid, current_status = result
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
            cur.execute("UPDATE tblBooking SET amountPaid = ?, paidStatus = ? WHERE bookingID = ?",
                       (new_paid, new_status, booking_id))
            conn.commit()
            messagebox.showinfo("Success", f"Payment processed: £{amount}\nTotal paid: £{new_paid}/{lesson_cost}\nStatus: {new_status}")
            booking_id_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            load_unpaid_bookings()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()
    
    tk.Button(payment_frame, text="Process Payment", bg="green", fg="white",
              command=process_payment, width=15).grid(row=0, column=4, padx=5)
    
    load_unpaid_bookings()
    tk.Button(top, text="Back", width=18, bg="white", command=destroy_menu).pack(pady=10)

# ============================================
# CUSTOMER MENUS
# ============================================
def customerPaymentMenu():
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
    
    columns = ("Booking ID", "Lesson", "Date", "Time", "Amount Due", "Total Cost", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(pady=10, padx=10)
    
    def load_my_payments():
        for item in tree.get_children():
            tree.delete(item)
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
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
            cur.execute("SELECT amountPaid, paidStatus FROM tblBooking WHERE bookingID = ?", (booking_id,))
            result = cur.fetchone()
            if not result:
                messagebox.showerror("Error", "Booking not found")
                return
            current_paid, current_status = result
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
            cur.execute("UPDATE tblBooking SET amountPaid = ?, paidStatus = ? WHERE bookingID = ?",
                       (new_paid, new_status, booking_id))
            conn.commit()
            messagebox.showinfo("Success", f"Payment processed: £{amount}\nTotal paid: £{new_paid}/{lesson_cost}\nStatus: {new_status}")
            booking_id_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            load_my_payments()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()
    
    tk.Button(payment_frame, text="Make Payment", bg="green", fg="white",
              command=process_payment, width=15).grid(row=0, column=4, padx=5)
    
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
    
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="View All My Bookings", width=18, bg="white", command=view_all_my_bookings).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Refresh", width=18, bg="white", command=load_my_payments).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Back", width=18, bg="white", command=destroy_menu).pack(side="left", padx=5)
    
    load_my_payments()

# ============================================
# CUSTOMER BOOKING MENU (with Calendar)
# ============================================
def customerBookingMenu():
    """Simple booking interface for customers – now with calendar date picker."""
    global root
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Book a Lesson")
    top.geometry("900x550")  
    top.resizable(False, False)
    top.configure(bg="#BCF0FE")

    def destroy_menu():
        top.destroy()
        root.deiconify()

    tk.Label(top, text=f"Book a Lesson - {current_user_name}",
             font=("Aptos", 16), bg="#BCF0FE").pack(pady=10)

    # --- Date selection frame ---
    date_frame = tk.Frame(top, bg="#BCF0FE")
    date_frame.pack(pady=5)

    tk.Label(date_frame, text="Select Date:", bg="#BCF0FE", font=("Aptos", 11)).grid(row=0, column=0, padx=5)

    
    try:
        from tkcalendar import DateEntry
        date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        date_picker.grid(row=0, column=1, padx=5)
        calendar_available = True
    except ImportError:
        
        date_picker = tk.Entry(date_frame, width=15)
        date_picker.insert(0, "YYYY-MM-DD")
        date_picker.grid(row=0, column=1, padx=5)
        calendar_available = False
        tk.Label(date_frame, text="(install tkcalendar for picker)", 
                 bg="#BCF0FE", fg="gray").grid(row=0, column=2, padx=5)

    # Buttons for date actions
    btn_load_date = tk.Button(date_frame, text="Load Lessons for Date", bg="white",
                              command=lambda: load_available_lessons(date_picker.get()))
    btn_load_date.grid(row=0, column=2 if calendar_available else 3, padx=10)

    btn_show_all = tk.Button(date_frame, text="Show All Lessons", bg="white",
                             command=lambda: load_available_lessons(None))
    btn_show_all.grid(row=0, column=3 if calendar_available else 4, padx=10)

    # --- Available lessons display ---
    frame = tk.Frame(top, bg="#BCF0FE")
    frame.pack(pady=10)

    tk.Label(frame, text="Available Lessons:", font=("Aptos", 12), bg="#BCF0FE").grid(row=0, column=0, columnspan=3, pady=10)

    columns = ("Date", "Time", "Type", "Duration", "Instructor", "Cost")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.grid(row=1, column=0, columnspan=3, pady=10)

    # --- Load lessons (with optional date filter) ---
    def load_available_lessons(date_filter=None):
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)

        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()

        # Base query
        query = """
            SELECT l.lessonDate, l.lessonTime, l.lessonType, l.duration,
                   COALESCE(i.firstName || ' ' || i.surname, 'No Instructor') as instructor,
                   l.cost, l.lessonID
            FROM tblLesson l
            LEFT JOIN tblInstructor i ON l.instructorID = i.instructorID
            WHERE l.lessonID NOT IN (SELECT lessonID FROM tblBooking)
            AND l.lessonDate >= date('now')
        """
        params = []

        # Add date filter if provided
        if date_filter and date_filter not in ("YYYY-MM-DD", ""):
            query += " AND l.lessonDate = ?"
            params.append(date_filter)

        query += " ORDER BY l.lessonDate, l.lessonTime"

        cur.execute(query, params)
        lessons = cur.fetchall()
        conn.close()

        for lesson in lessons:
            tree.insert("", tk.END, values=lesson[:-1], tags=(lesson[-1],))

    # --- Booking function ---
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
                load_available_lessons(None)  # Refresh all lessons
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

    # Buttons for booking
    btn_frame = tk.Frame(frame, bg="#BCF0FE")
    btn_frame.grid(row=2, column=0, columnspan=3, pady=10)

    tk.Button(btn_frame, text="Refresh Available Lessons", bg="white",
              command=lambda: load_available_lessons(None), width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Book Selected Lesson", bg="green", fg="white",
              command=book_selected, width=20).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Back", bg="white",
              command=destroy_menu, width=20).pack(side="left", padx=5)

    # Initial load: show all future lessons
    load_available_lessons(None)

    
def customerViewBookings():
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
    
    columns = ("Booking ID", "Lesson Type", "Date", "Time", "Instructor", "Amount Paid", "Status")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=10)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(pady=10, padx=10)
    
    def load_my_bookings():
        for item in tree.get_children():
            tree.delete(item)
        conn = sqlite3.connect("drivingschool.db")
        cur = conn.cursor()
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
    
    btn_frame = tk.Frame(top, bg="#BCF0FE")
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Refresh", bg="white", command=load_my_bookings, width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Back", bg="white", command=destroy_menu, width=15).pack(side="left", padx=5)
    
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
    except:
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
    global root
    root = tk.Tk()
    root.geometry("280x650")
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
    except:
        tk.Label(frametitle, text="Logo not found", font=("Aptos", 16), bg="#BCF0FE").grid(row=0, column=0, padx=20, pady=20)
    
    framebutton = tk.Frame(root, bg="#BCF0FE")
    framebutton.grid(row=1, column=0, padx=15, pady=15)
    tk.Button(framebutton, text="Book a Lesson", bg="white", width=18, command=customerBookingMenu).grid(row=0, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="View My Bookings", bg="white", width=18, command=customerViewBookings).grid(row=1, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="My Payments", bg="white", width=18, command=customerPaymentMenu).grid(row=2, column=0, padx=20, pady=15)
    tk.Button(framebutton, text="Log Out", bg="white", width=18, command=logout).grid(row=3, column=0, padx=20, pady=15)

# ============================================
# START THE APP
# ============================================
if __name__ == "__main__":
    login_screen()
    tk.mainloop()