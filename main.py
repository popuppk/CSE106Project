from flask import flash, Flask, jsonify, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__, template_folder='templates')
login_manager = LoginManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'
app.config['SECRET_KEY'] = 'adminkey'

login_manager.login_view = 'login'

db = SQLAlchemy(app)
admin = Admin(app, name='Admin Interface', template_mode='bootstrap3')


class Users(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    passwordhash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.passwordhash = generate_password_hash(password)
    
    def set_password(self, password):
        return check_password_hash(password)
    
    def get_id(self):
        return str(self.id)

class Inventory(db.Model):
    itemID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer,db.ForeignKey('users.userID'), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    def get_id(self):
        return str(self.id)

class SharedInventory(db.Model):
    shareID = db.Column(db.Integer, primary_key=True)
    sharedUserID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    itemID = db.Column(db.Integer, db.ForeignKey('inventory.itemID'), nullable=False)
    permissionLevel = db.Column(db.String(20), nullable=False)

class RestockInventory(db.Model):
    restockID = db.Column(db.Integer, primary_key=True)
    itemID = db.Column(db.Integer, db.ForeignKey('inventory.itemID'), nullable=False)
    quantityNeeded = db.Column(db.Integer, nullable=False)
    dateAdded = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(20), nullable=False)



class UsersAdminView(ModelView):
    column_list = ['userID', 'name', 'username', 'email']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['username', 'email'] 

class InventoryAdminView(ModelView):
    column_list = ['itemID', 'userID', 'itemName', 'quantity'] 
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['itemName']  

class SharedInventoryAdminView(ModelView):
    column_list = ['shareID', 'sharedUserID', 'itemID', 'permissionLevel']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['permissionLevel'] 

class RestockInventoryAdminView(ModelView):
    column_list = ['restockID', 'itemID', 'quantityNeeded', 'dateAdded', 'Status']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['Status'] 


admin.add_view(UsersAdminView(Users, db.session))
admin.add_view(InventoryAdminView(Inventory, db.session))
admin.add_view(SharedInventoryAdminView(SharedInventory, db.session))
admin.add_view(RestockInventoryAdminView(RestockInventory, db.session))


with app.app_context():
    db.create_all();


#login stuff:
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()

        if(username == "admin"):
            return redirect("/admin")
        

        if user and (user.check_password(password)):
            login_user(user)
            return render_template('index.html', username=current_user.username)
            
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        existing_user = Users.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists')
        else:
            new_user = Users(username=username,email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('You have successfully registered')
            return redirect(url_for('login')) 
    return render_template('registration.html')


#Navigation stuff
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    return render_template('index.html')

@app.route('/sharedinv')
def shared_inventory():
    return render_template('index.html')

@app.route('/restock')
def restock():
    return render_template('index.html')

@app.route('/add_row', methods=['POST'])
def add_row():
    data = request.json
    # Process the received data (e.g., database update, further validation, etc.)
    print(data)  
    return 'Data received'


@app.route('/registration', methods=['POST'])
def registration():
    return render_template('registration.html')



@app.route('/viewclass', methods=['POST'])
def viewclass():
    return render_template('viewClass.html', className=request.form['additional_parameter'])




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))



#Old Code for Reference:
"""

def get_classes_for_student():
    student = Students.query.filter_by(username=current_user.username).first()

    if student:
        classes_enrolled = student.classes

        class_details = []
        for enrollment in classes_enrolled:
            current_students = Enrollment.query.filter_by(class_id=enrollment.class_id).count()
            max_size = enrollment.clas.maxSize

            class_details.append({
                'class_name': enrollment.clas.name,
                'class_time': enrollment.clas.time,
                'teacher_name': enrollment.clas.teacher.username,
                'grade': enrollment.grade,
                'students_count': f'{current_students}/{max_size}'
            })

        return class_details
    else:
        return None

def get_all_classes_for_student():
    all_classes = Clas.query.all()
    student = Students.query.filter_by(username=current_user.username).first()

    student_classes = {enrollment.class_id: enrollment.grade for enrollment in student.classes}
    class_details = []

    for class_temp in all_classes:
        is_enrolled = class_temp.id in student_classes

        current_students = Enrollment.query.filter_by(class_id=class_temp.id).count()
        max_size = class_temp.maxSize

        class_details.append({
                'class_name': class_temp.name,
                'class_time': class_temp.time,
                'teacher_name': class_temp.teacher.username,
                'is_enrolled': is_enrolled,
                'students_count': f'{current_students}/{max_size}'
        })
        
    return class_details


    
@app.route('/getClassesForStudent', methods=['GET'])
def classes_for_student():
    classes = get_classes_for_student()
    return jsonify({'classes': classes})

@app.route('/getAllClassesForStudent', methods=['GET'])
def all_Classes_For_Student():
    classes = get_all_classes_for_student()
    return jsonify({'classes': classes})


def get_classes_for_teacher():
    teacher = Teacher.query.filter_by(username=current_user.username).first()
    
    if teacher:
        classes_Teaching = teacher.classes
        
        class_details = []
        for taught_class in classes_Teaching:
            current_students = Enrollment.query.filter_by(class_id=taught_class.id).count()
            max_size = taught_class.maxSize

            class_details.append({
                'class_name': taught_class.name,
                'class_time': taught_class.time,
                'teacher_name': current_user.username,
                'students_count': f'{current_students}/{max_size}'
            })

        return class_details
    else:
        return None

@app.route('/getClassesForTeacher', methods=['GET'])
def classes_for_teacher():
    classes = get_classes_for_teacher()

    return jsonify({'classes': classes})

def get_students_and_grades_for_class(class_name):
    class_obj = Clas.query.filter_by(name=class_name).first()

    enrollments = class_obj.enrollments

    student_details = []
    for enrollment in enrollments:
        student_details.append({
            'student_name': enrollment.students.username,
            'grade': enrollment.grade
        })

    return student_details

@app.route('/get_students_and_grades_for_class', methods=['GET'])
def students_and_grades_for_class():
    class_name = request.args.get('class_name')

    students_and_grades = get_students_and_grades_for_class(class_name)
    return jsonify({'students_and_grades': students_and_grades})
    
@app.route('/dropclass', methods=['POST'])
def dropclass():
    class_name = request.form.get('class_name')
    student_name = request.form.get('student_name')

    student = Students.query.filter_by(username=student_name).first()
    clas = Clas.query.filter_by(name=class_name).first()

    enrollment = Enrollment.query.filter_by(student_id=student.id, class_id=clas.id).first()

    db.session.delete(enrollment)
    db.session.commit()

    return render_template('student.html', username=current_user.username)

@app.route('/addclass', methods=['POST'])
def addclass():
    class_name = request.form.get('class_name')
    student_name = request.form.get('student_name')

    student = Students.query.filter_by(username=student_name).first()
    clas = Clas.query.filter_by(name=class_name).first()

    new_enrollment = Enrollment(student_id=student.id, class_id=clas.id, grade=100)
    db.session.add(new_enrollment)
    db.session.commit()

    return render_template('student.html', username=current_user.username)

@app.route('/changegrade', methods=['POST'])
def changegrade():
    student_name = request.form.get('student_name')
    class_name = request.form.get('class_name')
    new_grade = int(request.form.get('new_grade'))

    print(student_name)
    print(class_name)
    student = Students.query.filter_by(username=student_name).first()
    clas = Clas.query.filter_by(name=class_name).first()

    enrollment = Enrollment.query.filter_by(student_id=student.id, class_id=clas.id).first()

    enrollment.grade = new_grade
    db.session.commit()

    return render_template('viewClass.html', className=class_name)

"""