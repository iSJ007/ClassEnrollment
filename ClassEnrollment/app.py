from flask import Flask,render_template ,url_for, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from wtforms import validators as vl
from wtforms.fields import HiddenField

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


app = Flask (__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SECRET_KEY'] = 'cse106secretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#----------------FOR THE ADMIN-------------
admin = Admin(app)
#--------------------END-------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)



class Users(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False, unique= True)
    name = db.Column(db.String, nullable = False)
    password = db.Column(db.String(80), nullable = False)
    acc_type = db.Column(db.Integer, nullable = False)
 




class Classes(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    course_name = db.Column(db.String(30))
    teacher = db.Column(db.String, nullable = False)
    number_enrolled = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    time = db.Column(db.String, nullable = False)
    


class Enrollment(UserMixin, db.Model):
    users_id = db.Column(db.ForeignKey(Users.id), primary_key = True)
    class_id = db.Column( db.ForeignKey(Classes.id), primary_key = True)
    grade = db.Column(db.String(10))


#-----------------ADMIN MODEL STUFF-------------------
admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Classes, db.session))
admin.add_view(ModelView(Enrollment, db.session))
#-----------------END OF ADMIN MODEL STUFF-------------

class RegisterForm (FlaskForm):
  name = StringField( [InputRequired(), Length(min = 4, max =15)],render_kw={"placeholder": "Name"} )
  acctype = StringField( [InputRequired(), Length(min = 1, max =2)],render_kw={"placeholder": "1 student, 2 teacher, 3 admin"} )
  username = StringField( [InputRequired(), Length(min = 4, max =15)],render_kw={"placeholder": "Username"} )
  password = PasswordField([InputRequired()], render_kw={"placeholder": "Password"})
  submit = SubmitField("Login")

  def validate_username (self, username):
    existing_user_username = Users.query.filter_by (
        username= username.data).first()
    if existing_user_username:
        raise ValidationError ("Username already exists!")

class LoginForm (FlaskForm):
  username = StringField( [InputRequired(), Length(min = 4, max =15)],render_kw={"placeholder": "Username"} )
  password = PasswordField([InputRequired()], render_kw={"placeholder": "Password"})
  submit = SubmitField("Login")

class StudentEnrollmentForm(FlaskForm):
   course_name = HiddenField("", validators=[vl.InputRequired()])
   action = HiddenField("", validators=[vl.AnyOf(['add', 'remove'])])

class UpdateGradeForm(FlaskForm):
    grade = IntegerField("", validators=[vl.InputRequired(), vl.NumberRange(min=0, max = 100)])
    enroll_name = HiddenField("", validators=[vl.InputRequired()])
    submit = SubmitField("Commit")

@app.route("/logout", methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect (url_for('index'))



@app.route("/teacher/<course_name>/<student_name>", methods = [ 'POST'])
def teacheredit(course_name, student_name):
   if request.method == 'POST':
     update_grade_form = UpdateGradeForm()
     grade = update_grade_form.grade.data
     user = Users.query.filter_by(name = student_name).first()
     if user != None:
      course = Classes.query.filter_by(course_name = course_name).first()
      cId = course.id
      enroll = Enrollment.query.filter_by(users_id = user.id, class_id = cId).first()
      if enroll != None:
         enroll.grade = grade
         db.session.commit()
         return redirect(url_for('teacherdetail', course_name = course_name))
     
     

@app.route("/teacher/<course_name>", methods = ['GET'])
@login_required
def teacherdetail(course_name):
    listStudentIds = []
    listStudentNames = []

    grades = []
    course_details = Classes.query.filter_by(course_name = course_name).first()
    classId = course_details.id
    listEnrolled = Enrollment.query.filter_by(class_id = classId).order_by(Enrollment.users_id)
    for user in listEnrolled:
        grades.append(user.grade)
    for enrolled in listEnrolled:
        listStudentIds.append(enrolled.users_id)
    enrolled_users =  Users.query.filter(Users.id.in_(listStudentIds))
    for names in enrolled_users:
        listStudentNames.append(names.name)
    length = len(listStudentIds)

    teacher = current_user.name

    return render_template('teacherdetail.html', name = course_name, students = listStudentNames, grades = grades, length = length, tchname = teacher,update_grade_form=UpdateGradeForm() )

    


   
    

@app.route("/teacher", methods = ['GET', 'POST'])
@login_required
def teacher():
    taught_classes = Classes.query.filter_by(teacher = current_user.name)
    teacher = current_user.name
    return render_template('teacher.html', courses = taught_classes, tchname = teacher)

    


    


@app.route("/studentenroll", methods = ['GET', 'POST'])
@login_required
def studentenroll():
 
 
 if request.method=="POST":
    enroll_form = StudentEnrollmentForm()

     
    if enroll_form.validate_on_submit():
            course_name1 = enroll_form.course_name.data
            action = enroll_form.action.data

            if action == 'add':
                course = Classes.query.filter_by(course_name=course_name1).first()
                if course is not None and course.number_enrolled < course.capacity:
                  enrollment = Enrollment( users_id = current_user.id, class_id = course.id, grade = 0)
                  db.session.add(enrollment)
                  course.number_enrolled += 1
                  db.session.commit()
                  enrollment = Enrollment.query.filter_by(users_id = current_user.id)
                  enrolledClasses = []
                  for course in enrollment:
                   enrolledClasses.append(course.class_id)
                  return render_template('studentenroll.html', courses = Classes.query.all(), enrollment = enrolledClasses, enroll_form =StudentEnrollmentForm() )
            else:
                course = Classes.query.filter_by(course_name=course_name1).first()

                
                Enrollment.query.filter_by(users_id = current_user.id, class_id = course.id).delete()
                course.number_enrolled -= 1
                db.session.commit()
                enrollment = Enrollment.query.filter_by(users_id = current_user.id)
                enrolledClasses = []
                for course in enrollment:
                 enrolledClasses.append(course.class_id)


                return render_template('studentenroll.html', courses = Classes.query.all(), enrollment = enrolledClasses, enroll_form =StudentEnrollmentForm() )
        
 if request.method == 'GET':
  currentuser = current_user.id
  enrollment = Enrollment.query.filter_by(users_id = currentuser)
  enrolledClasses = []
  for course in enrollment:
        enrolledClasses.append(course.class_id)
  return render_template('studentenroll.html', courses = Classes.query.all(), enrollment = enrolledClasses, enroll_form =StudentEnrollmentForm() )

 

@app.route("/student", methods = ['GET', 'POST'])
@login_required
def student():
    listCourses = []
    currentuser = current_user.id
    enrolled_classes = Enrollment.query.filter_by(users_id = currentuser)
    for course in enrolled_classes:
        listCourses.append(course.class_id)
    classes = Classes.query.filter(Classes.id.in_(listCourses))
    studentname = current_user.name
    return render_template('student.html', courses = classes, stdname = studentname)



    #return render_template('student.html'  )


@app.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username = form.username.data).first()
        if user:
           if bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.acc_type == 1:
              return redirect(url_for('student'))
            elif user.acc_type == 2:
              return redirect(url_for('teacher'))
            else:
             return redirect("/admin")
            #return redirect(url_for('student'))

    
    return render_template('login.html', form = form  )


@app.route("/register" ,methods = ['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = Users(name = form.name.data, acc_type = form.acctype.data, username = form.username.data, password = hashed_password)
        print(form.acctype.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form = form)


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.app_context()
    with app.app_context():
        db.create_all()
    app.run()
