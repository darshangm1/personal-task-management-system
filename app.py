from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "taskmanagersecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship("Task", backref="owner", lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("All fields are required")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please login")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid login")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    sort = request.args.get("sort", "new")  

    if sort == "old":
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.id.asc()).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.id.desc()).all()

    return render_template("dashboard.html", tasks=tasks, sort=sort)

@app.route("/add", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title", "").strip()

    if not title:
        flash("Task cannot be empty")
        return redirect(url_for("dashboard"))

    new_task = Task(title=title, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()

    flash("Task added")
    return redirect(url_for("dashboard"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        flash("Unauthorized access")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        new_title = request.form["title"].strip()

        if not new_title:
            flash("Task cannot be empty")
            return redirect(url_for("edit_task", id=id))

        task.title = new_title
        db.session.commit()
        flash("Task updated")
        return redirect(url_for("dashboard"))

    return render_template("edit.html", task=task)


@app.route("/delete/<int:id>")
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        flash("Unauthorized action")
        return redirect(url_for("dashboard"))

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted")

    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
