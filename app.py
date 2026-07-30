from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User, Exam, Question, Submission, Answer
import time

import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-later')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///exam_portal.db')

if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email already registered. Please login.')
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_pw,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route('/create-exam', methods=['GET', 'POST'])
@login_required
def create_exam():

    if current_user.role != 'admin':
        flash('Only admins can create exams.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        title = request.form['title']
        duration = request.form['duration']

        new_exam = Exam(
            title=title,
            duration_minutes=duration,
            created_by=current_user.id
        )

        db.session.add(new_exam)
        db.session.commit()

        flash('Exam created! Now add some questions.')

        return redirect(url_for('add_question', exam_id=new_exam.id))

    return render_template('create_exam.html')


@app.route('/add-question/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def add_question(exam_id):

    if current_user.role != 'admin':
        flash('Only admins can add questions.')
        return redirect(url_for('dashboard'))

    exam = db.session.get(Exam, exam_id)

    if not exam:
        flash('Exam not found.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        new_question = Question(
            exam_id=exam.id,
            question_text=request.form['question_text'],
            option_a=request.form['option_a'],
            option_b=request.form['option_b'],
            option_c=request.form['option_c'],
            option_d=request.form['option_d'],
            correct_option=request.form['correct_option']
        )

        db.session.add(new_question)
        db.session.commit()

        flash('Question added!')

        return redirect(url_for('add_question', exam_id=exam.id))

    return render_template('add_question.html', exam=exam)
@app.route('/edit-question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):

    if current_user.role != 'admin':
        flash('Only admins can edit questions.')
        return redirect(url_for('dashboard'))

    question = db.session.get(Question, question_id)

    if not question:
        flash('Question not found.')
        return redirect(url_for('dashboard'))

    exam = question.exam

    if exam.created_by != current_user.id:
        flash('You can only edit your own exams.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        question.question_text = request.form['question_text']
        question.option_a = request.form['option_a']
        question.option_b = request.form['option_b']
        question.option_c = request.form['option_c']
        question.option_d = request.form['option_d']
        question.correct_option = request.form['correct_option']

        db.session.commit()

        flash('Question updated!')
        return redirect(url_for('add_question', exam_id=exam.id))

    return render_template('edit_question.html', question=question, exam=exam)


@app.route('/publish-exam/<int:exam_id>')
@login_required
def publish_exam(exam_id):

    if current_user.role != 'admin':
        flash('Only admins can publish exams.')
        return redirect(url_for('dashboard'))

    exam = db.session.get(Exam, exam_id)

    if not exam:
        flash('Exam not found.')
        return redirect(url_for('dashboard'))

    if exam.created_by != current_user.id:
        flash('You can only publish exams you created.')
        return redirect(url_for('dashboard'))

    exam.is_published = True
    db.session.commit()

    flash(f'"{exam.title}" is now published!')

    return redirect(url_for('add_question', exam_id=exam.id))


@app.route('/exams')
@login_required
def exam_list():
    exams = Exam.query.filter_by(is_published=True).all()
    return render_template('exam_list.html', exams=exams)


@app.route('/join-exam', methods=['GET', 'POST'])
@login_required
def join_exam():

    if current_user.role != 'student':
        flash('Only students can join exams.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        code = request.form['access_code'].strip().upper()

        exam = Exam.query.filter_by(access_code=code, is_published=True).first()

        if not exam:
            flash('Invalid code, or this exam is not published yet.')
            return redirect(url_for('join_exam'))

        return redirect(url_for('take_exam', exam_id=exam.id))

    return render_template('join_exam.html')


@app.route('/take-exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):

    if current_user.role != 'student':
        flash('Only students can take exams.')
        return redirect(url_for('dashboard'))

    exam = db.session.get(Exam, exam_id)

    if not exam or not exam.is_published:
        flash('Exam not found.')
        return redirect(url_for('exam_list'))

    questions = Question.query.filter_by(exam_id=exam.id).all()

    session_key = f'exam_start_{exam_id}'

    if request.method == 'GET' and session_key not in session:
        session[session_key] = time.time()

    elapsed = time.time() - session.get(session_key, time.time())
    remaining_seconds = max(0, int(exam.duration_minutes * 60 - elapsed))

    if request.method == 'POST':

        score = 0

        submission = Submission(
            student_id=current_user.id,
            exam_id=exam.id
        )

        db.session.add(submission)
        db.session.commit()

        for question in questions:

            selected = request.form.get(f'question_{question.id}')

            answer = Answer(
                submission_id=submission.id,
                question_id=question.id,
                selected_option=selected
            )

            db.session.add(answer)

            if selected == question.correct_option:
                score += 1

        submission.score = score
        db.session.commit()

        session.pop(session_key, None)

        return redirect(url_for('result', submission_id=submission.id))

    return render_template(
        'take_exam.html',
        exam=exam,
        questions=questions,
        remaining_seconds=remaining_seconds
    )


@app.route('/result/<int:submission_id>')
@login_required
def result(submission_id):

    submission = db.session.get(Submission, submission_id)

    if not submission or submission.student_id != current_user.id:
        flash('Result not found.')
        return redirect(url_for('dashboard'))

    total_questions = Question.query.filter_by(exam_id=submission.exam_id).count()
    percentage = round((submission.score / total_questions) * 100) if total_questions else 0
    passed = percentage >= 50

    return render_template(
        'result.html',
        submission=submission,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed
    )


@app.route('/history')
@login_required
def history():

    submissions = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).all()

    results = []

    for s in submissions:
        total = Question.query.filter_by(exam_id=s.exam_id).count()
        percentage = round((s.score / total) * 100) if total else 0
        results.append({'submission': s, 'total': total, 'percentage': percentage})

    return render_template('history.html', results=results)


@app.route('/delete-submission/<int:submission_id>')
@login_required
def delete_submission(submission_id):

    submission = db.session.get(Submission, submission_id)

    if not submission or submission.student_id != current_user.id:
        flash('Submission not found.')
        return redirect(url_for('history'))

    db.session.delete(submission)
    db.session.commit()

    flash('Exam attempt deleted from your history.')
    return redirect(url_for('history'))


@app.route('/manage-exams')
@login_required
def manage_exams():

    if current_user.role != 'admin':
        flash('Only admins can manage exams.')
        return redirect(url_for('dashboard'))

    exams = Exam.query.filter_by(created_by=current_user.id).all()

    return render_template('manage_exams.html', exams=exams)


@app.route('/delete-exam/<int:exam_id>')
@login_required
def delete_exam(exam_id):

    if current_user.role != 'admin':
        flash('Only admins can delete exams.')
        return redirect(url_for('dashboard'))

    exam = db.session.get(Exam, exam_id)

    if not exam or exam.created_by != current_user.id:
        flash('Exam not found.')
        return redirect(url_for('manage_exams'))

    db.session.delete(exam)
    db.session.commit()

    flash(f'"{exam.title}" was deleted.')
    return redirect(url_for('manage_exams'))


@app.route('/exam-results/<int:exam_id>')
@login_required
def exam_results(exam_id):

    if current_user.role != 'admin':
        flash('Only admins can view results.')
        return redirect(url_for('dashboard'))

    exam = db.session.get(Exam, exam_id)

    if not exam or exam.created_by != current_user.id:
        flash('Exam not found.')
        return redirect(url_for('manage_exams'))

    submissions = Submission.query.filter_by(exam_id=exam.id).all()
    total_questions = Question.query.filter_by(exam_id=exam.id).count()

    results = []

    for s in submissions:
        percentage = round((s.score / total_questions) * 100) if total_questions else 0
        results.append({'submission': s, 'percentage': percentage})

    return render_template(
        'exam_results.html',
        exam=exam,
        results=results,
        total_questions=total_questions
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)