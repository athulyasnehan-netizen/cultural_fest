from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import date, datetime

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/fest_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)

# ==========================================
# Database Models (All Entities)
# ==========================================

class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Department(db.Model):
    __tablename__ = 'department'
    dept_id = db.Column(db.String(20), primary_key=True)
    dept_name = db.Column(db.String(100), nullable=False)
    championship_points = db.Column(db.Integer, default=0)

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.String(20), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    m_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    age = db.Column(db.Integer)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_no = db.Column(db.String(15))
    year = db.Column(db.Integer)
    dept_id = db.Column(db.String(20), db.ForeignKey('department.dept_id'))

class Coordinator(db.Model):
    __tablename__ = 'coordinator'
    coordinator_id = db.Column(db.String(20), primary_key=True)
    role = db.Column(db.String(50))
    responsibility = db.Column(db.String(100))
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'))
    event_id = db.Column(db.String(20), db.ForeignKey('event.event_id'))
    
    student = db.relationship('Student', backref='coordinators')
    event = db.relationship('Event', backref='coordinators')

class Venue(db.Model):
    __tablename__ = 'venue'
    venue_id = db.Column(db.String(20), primary_key=True)
    venue_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    capacity = db.Column(db.Integer)

class Event(db.Model):
    __tablename__ = 'event'
    event_id = db.Column(db.String(20), primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    description = db.Column(db.Text)
    no_of_participants = db.Column(db.Integer, default=0)
    venue_id = db.Column(db.String(20), db.ForeignKey('venue.venue_id'))

class Judge(db.Model):
    __tablename__ = 'judge'
    judge_id = db.Column(db.String(20), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    qualification = db.Column(db.String(100))
    phone_no = db.Column(db.String(15))

class JudgeEvent(db.Model):
    __tablename__ = 'judge_event'
    judge_id = db.Column(db.String(20), db.ForeignKey('judge.judge_id'), primary_key=True)
    event_id = db.Column(db.String(20), db.ForeignKey('event.event_id'), primary_key=True)

class Registration(db.Model):
    __tablename__ = 'registration'
    registration_id = db.Column(db.String(20), primary_key=True)
    registration_date = db.Column(db.Date, nullable=False)
    registration_type = db.Column(db.String(20))
    payment_status = db.Column(db.String(20))
    payment_mode = db.Column(db.String(20))
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'))
    event_id = db.Column(db.String(20), db.ForeignKey('event.event_id'))
    
    student = db.relationship('Student', backref='registrations')
    event = db.relationship('Event', backref='registrations')
class Result(db.Model):
    __tablename__ = 'result'
    result_id = db.Column(db.String(20), primary_key=True)
    score = db.Column(db.Numeric(5, 2))
    ranking = db.Column(db.Integer)
    status = db.Column(db.String(20))
    event_id = db.Column(db.String(20), db.ForeignKey('event.event_id'))
    registration_id = db.Column(db.String(20), db.ForeignKey('registration.registration_id'))
    
    registration = db.relationship('Registration', backref='results')
    event = db.relationship('Event', backref='results')

# Auto-create table schemas if not present
with app.app_context():
    db.create_all()

# ==========================================
# Routes & Business Logic
# ==========================================

@app.route('/')
def home():
    events = Event.query.all()
    departments = Department.query.order_by(Department.championship_points.desc()).all()
    return render_template('index.html', events=events, departments=departments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if role == 'student':
            student = db.session.get(Student, username) or Student.query.filter_by(email=username).first()
            if student:
                return redirect(url_for('student_dashboard', student_id=student.student_id))
            else:
                error = 'Invalid Student ID or Email.'
        elif role == 'admin':
            admin_user = Admin.query.filter((Admin.username == username) | (Admin.email == username)).first()
            if (admin_user and admin_user.password == password) or (username == 'admin' and password == 'admin123'):
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid Admin username or password.'
                
    return render_template('login.html', error=error)

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing = Admin.query.filter((Admin.username == username) | (Admin.email == email)).first()
        if existing or username == 'admin':
            error = 'Username or email already exists.'
        else:
            try:
                new_admin = Admin(
                    admin_id="ADM-" + uuid.uuid4().hex[:6].upper(),
                    username=username,
                    email=email,
                    password=password
                )
                db.session.add(new_admin)
                db.session.commit()
                success = 'Admin account created successfully! You can now log in.'
            except Exception as e:
                db.session.rollback()
                error = f"Database error: {e}"
                
    return render_template('register_admin.html', error=error, success=success)

@app.route('/student/dashboard/<student_id>')
def student_dashboard(student_id):
    student = db.get_or_404(Student, student_id)
    events = Event.query.all()
    registrations = Registration.query.filter_by(student_id=student_id).all()
    reg_ids = [reg.registration_id for reg in registrations]
    results = Result.query.filter(Result.registration_id.in_(reg_ids)).all() if reg_ids else []
    departments = Department.query.order_by(Department.championship_points.desc()).all()
    return render_template('student_dashboard.html', student=student, events=events, registrations=registrations, results=results, departments=departments)

@app.route('/student/register/<student_id>', methods=['POST'])
def register_event(student_id):
    event_id = request.form.get('event_id')
    existing = Registration.query.filter_by(student_id=student_id, event_id=event_id).first()
    if not existing:
        new_reg = Registration(
            registration_id="REG-" + uuid.uuid4().hex[:6].upper(),
            registration_date=date.today(),
            registration_type="Solo",
            payment_status="Completed",
            payment_mode="Online",
            student_id=student_id,
            event_id=event_id
        )
        db.session.add(new_reg)
        db.session.commit()
    return redirect(url_for('student_dashboard', student_id=student_id))

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    departments = Department.query.all()
    events = Event.query.all()
    error = None
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        first_name = request.form.get('first_name')
        m_name = request.form.get('m_name')
        last_name = request.form.get('last_name')
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        dob = date.fromisoformat(dob_str) if dob_str else None
        age = int(request.form.get('age')) if request.form.get('age') else None
        email = request.form.get('email')
        phone_no = request.form.get('phone_no')
        year = int(request.form.get('year')) if request.form.get('year') else None
        dept_id = request.form.get('dept_id')
        event_id = request.form.get('event_id')
        
        existing = db.session.get(Student, student_id)
        if existing:
            error = 'Student ID already exists. Please use a unique ID.'
        else:
            try:
                new_student = Student(student_id=student_id, first_name=first_name, m_name=m_name, last_name=last_name, gender=gender, dob=dob, age=age, email=email, phone_no=phone_no, year=year, dept_id=dept_id)
                db.session.add(new_student)
                if event_id:
                    new_reg = Registration(
                        registration_id="REG-" + uuid.uuid4().hex[:6].upper(),
                        registration_date=date.today(),
                        registration_type="Solo",
                        payment_status="Completed",
                        payment_mode="Online",
                        student_id=student_id,
                        event_id=event_id
                    )
                    db.session.add(new_reg)
                db.session.commit()
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                error = f"Database Error: {e}"
    return render_template('register_student.html', departments=departments, events=events, error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    events = Event.query.all()
    registrations = Registration.query.all()
    judges = Judge.query.all()
    results = Result.query.all()
    students = Student.query.all()
    coordinators = Coordinator.query.all()
    departments = Department.query.all()
    venues = Venue.query.all()
    return render_template('admin_dashboard.html', events=events, registrations=registrations, judges=judges, results=results, students=students, coordinators=coordinators, departments=departments, venues=venues)

# --- Event CRUD ---
@app.route('/admin/add_event', methods=['POST'])
def add_event():
    try:
        event_id = request.form.get('event_id')
        event_name = request.form.get('event_name')
        category = request.form.get('category')
        date_str = request.form.get('date')
        event_date = date.fromisoformat(date_str) if date_str else None
        time_str = request.form.get('time')
        event_time = datetime.strptime(time_str, '%H:%M').time() if time_str else None
        description = request.form.get('description')
        venue_id = request.form.get('venue_id')
        
        new_event = Event(event_id=event_id, event_name=event_name, category=category, date=event_date, time=event_time, description=description, venue_id=venue_id)
        db.session.add(new_event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving event: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_event/<event_id>', methods=['POST'])
def edit_event(event_id):
    try:
        event = db.get_or_404(Event, event_id)
        event.event_name = request.form.get('event_name')
        event.category = request.form.get('category')
        date_str = request.form.get('date')
        event.date = date.fromisoformat(date_str) if date_str else None
        time_str = request.form.get('time')
        event.time = datetime.strptime(time_str, '%H:%M').time() if time_str else None
        event.description = request.form.get('description')
        event.venue_id = request.form.get('venue_id')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating event: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    try:
        event = db.get_or_404(Event, event_id)
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting event: {e}")
    return redirect(url_for('admin_dashboard'))

# --- Student CRUD ---
@app.route('/admin/add_student', methods=['POST'])
def add_student():
    try:
        student_id = request.form.get('student_id')
        first_name = request.form.get('first_name')
        m_name = request.form.get('m_name')
        last_name = request.form.get('last_name')
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        dob = date.fromisoformat(dob_str) if dob_str else None
        age = int(request.form.get('age')) if request.form.get('age') else None
        email = request.form.get('email')
        phone_no = request.form.get('phone_no')
        year = int(request.form.get('year')) if request.form.get('year') else None
        dept_id = request.form.get('dept_id')
        
        new_student = Student(student_id=student_id, first_name=first_name, m_name=m_name, last_name=last_name, gender=gender, dob=dob, age=age, email=email, phone_no=phone_no, year=year, dept_id=dept_id)
        db.session.add(new_student)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving student: {e}")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    try:
        student = db.get_or_404(Student, student_id)
        db.session.delete(student)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student: {e}")
    return redirect(url_for('admin_dashboard'))

# --- Judge CRUD ---
@app.route('/admin/add_judge', methods=['POST'])
def add_judge():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    qualification = request.form.get('qualification')
    phone_no = request.form.get('phone_no')
    new_judge = Judge(judge_id="JDG-" + uuid.uuid4().hex[:6].upper(), first_name=first_name, last_name=last_name, qualification=qualification, phone_no=phone_no)
    db.session.add(new_judge)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_judge/<judge_id>', methods=['POST'])
def delete_judge(judge_id):
    try:
        judge = db.get_or_404(Judge, judge_id)
        db.session.delete(judge)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting judge: {e}")
    return redirect(url_for('admin_dashboard'))

# --- Coordinator CRUD ---
@app.route('/admin/add_coordinator', methods=['POST'])
def add_coordinator():
    coordinator_id = "CRD-" + uuid.uuid4().hex[:6].upper()
    role = request.form.get('role')
    responsibility = request.form.get('responsibility')
    student_id = request.form.get('student_id')
    event_id = request.form.get('event_id')
    new_coord = Coordinator(coordinator_id=coordinator_id, role=role, responsibility=responsibility, student_id=student_id, event_id=event_id)
    db.session.add(new_coord)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_coordinator/<coordinator_id>', methods=['POST'])
def delete_coordinator(coordinator_id):
    try:
        coord = db.get_or_404(Coordinator, coordinator_id)
        db.session.delete(coord)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting coordinator: {e}")
    return redirect(url_for('admin_dashboard'))

# --- Result CRUD ---
@app.route('/admin/add_result', methods=['POST'])
def add_result():
    event_id = request.form.get('event_id')
    registration_id = request.form.get('registration_id')
    score = request.form.get('score')
    ranking = request.form.get('ranking')
    new_result = Result(result_id="RES-" + uuid.uuid4().hex[:6].upper(), score=score, ranking=ranking, status="Published", event_id=event_id, registration_id=registration_id)
    db.session.add(new_result)
    
    if int(ranking) == 1:
        reg = db.session.get(Registration, registration_id)
        if reg and reg.student:
            dept = db.session.get(Department, reg.student.dept_id)
            if dept:
                dept.championship_points = (dept.championship_points or 0) + 10
                
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_result/<result_id>', methods=['POST'])
def delete_result(result_id):
    try:
        result = db.get_or_404(Result, result_id)
        if result.ranking == 1:
            reg = db.session.get(Registration, result.registration_id)
            if reg and reg.student:
                dept = db.session.get(Department, reg.student.dept_id)
                if dept:
                    dept.championship_points = max(0, (dept.championship_points or 0) - 10)
                    
        db.session.delete(result)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting result: {e}")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)