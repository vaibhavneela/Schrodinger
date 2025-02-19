from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'youshouldnotknowthis'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Calorie Tracker Model
class CalorieData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    goal = db.Column(db.String(10), nullable=False) 
    bmr = db.Column(db.Float, nullable=False)  # Basal Metabolic Rate

# Habit Tracker Model
class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    habit_name = db.Column(db.String(100), nullable=False)
    reminder_time = db.Column(db.String(10), nullable=True)
    completed = db.Column(db.Boolean, default=False)

# Create tables
with app.app_context():
    db.create_all()

# Utility function to calculate BMR
def calculate_bmr(weight, height, age, goal):
    bmr = 10 * weight + 6.25 * height - 5 * age + 5  # Mifflin-St Jeor Equation (for men)
    if goal == "gain":
        return bmr + 500  # Increase calories
    elif goal == "lose":
        return bmr - 500  # Decrease calories
    return bmr  # Maintain weight

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please login.", "danger")
            return redirect(url_for('login'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template('login.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# Calorie Tracker Route
@app.route('/calorie-tracker', methods=['GET', 'POST'])
def calorie_tracker():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        goal = request.form['goal']

        bmr = calculate_bmr(weight, height, age, goal)

        new_data = CalorieData(user_id=user_id, weight=weight, height=height, age=age, goal=goal, bmr=bmr)
        db.session.add(new_data)
        db.session.commit()
        flash("Calorie needs calculated!", "success")
        return redirect(url_for('calorie_tracker'))

    calorie_data = CalorieData.query.filter_by(user_id=user_id).first()
    return render_template('calorie_tracker.html', calorie_data=calorie_data)

# Reset Calorie Tracker Route
@app.route('/reset-calorie-tracker')
def reset_calorie_tracker():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    calorie_data = CalorieData.query.filter_by(user_id=user_id).first()

    if calorie_data:
        db.session.delete(calorie_data)
        db.session.commit()
        flash("Calorie tracker data reset successfully!", "info")

    return redirect(url_for('calorie_tracker'))

# Habit Tracker Route
@app.route('/habit-tracker', methods=['GET', 'POST'])
def habit_tracker():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        reminder_time = request.form['reminder_time']

        new_habit = Habit(user_id=user_id, habit_name=habit_name, reminder_time=reminder_time)
        db.session.add(new_habit)
        db.session.commit()
        flash("Habit added successfully!", "success")
        return redirect(url_for('habit_tracker'))

    habits = Habit.query.filter_by(user_id=user_id).all()
    return render_template('habit_tracker.html', habits=habits)

# Remove Habit Route
@app.route('/remove-habit/<int:habit_id>')
def remove_habit(habit_id):
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id == session['user_id']:
        db.session.delete(habit)
        db.session.commit()
        flash("Habit removed successfully.", "info")

    return redirect(url_for('habit_tracker'))

if __name__ == "__main__":
    app.run(debug=True)
