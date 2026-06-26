import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Database helper functions
def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

def init_db():
    """Create the students table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            marks REAL NOT NULL,
            percentage REAL NOT NULL,
            result TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Home page
@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

# List all students with search by roll number
@app.route('/students', methods=['GET', 'POST'])
def students():
    """Display all students and handle search by roll number."""
    conn = get_db_connection()
    cursor = conn.cursor()

    search_roll = request.args.get('search_roll', '').strip()
    if search_roll:
        cursor.execute("SELECT * FROM students WHERE roll_number LIKE ?", ('%' + search_roll + '%',))
    else:
        cursor.execute("SELECT * FROM students")

    students_list = cursor.fetchall()
    total_students = len(students_list)
    conn.close()
    return render_template('students.html', students=students_list, total=total_students, search_roll=search_roll)

# Add student - GET (form) and POST (submit)
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    """Add a new student record."""
    if request.method == 'POST':
        # Get form data
        student_name = request.form.get('student_name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        marks = request.form.get('marks', '').strip()

        # Validation: check for empty fields
        if not student_name or not roll_number or not department or not marks:
            flash('All fields are required!', 'danger')
            return render_template('add_student.html')

        # Validate marks is numeric and in range 0-100
        try:
            marks = float(marks)
            if marks < 0 or marks > 100:
                flash('Marks must be between 0 and 100.', 'danger')
                return render_template('add_student.html')
        except ValueError:
            flash('Marks must be a valid number.', 'danger')
            return render_template('add_student.html')

        # Calculate percentage and result
        percentage = marks  # Since marks is out of 100
        result = 'Pass' if percentage >= 40 else 'Fail'

        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO students (student_name, roll_number, department, marks, percentage, result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_name, roll_number, department, marks, percentage, result))
            conn.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Roll number already exists. Please use a unique roll number.', 'danger')
            return render_template('add_student.html')
        finally:
            conn.close()

    return render_template('add_student.html')

# Update student - GET (populate form) and POST (update)
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    """Update an existing student record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Get form data
        student_name = request.form.get('student_name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        marks = request.form.get('marks', '').strip()

        # Validation
        if not student_name or not roll_number or not department or not marks:
            flash('All fields are required!', 'danger')
            # Re-fetch the student to re-populate form
            cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
            student = cursor.fetchone()
            conn.close()
            return render_template('update_student.html', student=student)

        try:
            marks = float(marks)
            if marks < 0 or marks > 100:
                flash('Marks must be between 0 and 100.', 'danger')
                cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
                student = cursor.fetchone()
                conn.close()
                return render_template('update_student.html', student=student)
        except ValueError:
            flash('Marks must be a valid number.', 'danger')
            cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
            student = cursor.fetchone()
            conn.close()
            return render_template('update_student.html', student=student)

        # Calculate percentage and result
        percentage = marks
        result = 'Pass' if percentage >= 40 else 'Fail'

        # Update database
        try:
            cursor.execute('''
                UPDATE students
                SET student_name = ?, roll_number = ?, department = ?, marks = ?, percentage = ?, result = ?
                WHERE id = ?
            ''', (student_name, roll_number, department, marks, percentage, result, id))
            conn.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Roll number already exists. Please use a unique roll number.', 'danger')
            cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
            student = cursor.fetchone()
            conn.close()
            return render_template('update_student.html', student=student)
        finally:
            conn.close()

    # GET request – populate form with existing data
    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    conn.close()
    if student is None:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))
    return render_template('update_student.html', student=student)

# Delete student
@app.route('/delete/<int:id>', methods=['POST'])  # Use POST to avoid accidental deletes via GET
def delete_student(id):
    """Delete a student record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('students'))

# Initialize database when the app starts
if __name__ == '__main__':
    init_db()
    app.run(debug=True)