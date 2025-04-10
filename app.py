import os
from sqlalchemy.sql import func
from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from sqlmodel import SQLModel, Field, create_engine, Session, select
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, length
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
db = os.getenv("SQL_DB")

engine = create_engine(db, echo=True)

class User(UserMixin, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, max_length=50)
    password: str = Field(nullable=False, max_length=50)


class GermanWords(UserMixin, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    german_word: str = Field(nullable=False, max_length=100)
    german_translated_word: str = Field(nullable=False, max_length=100)
    

class SchweizWords(UserMixin, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    schweiz_word: str = Field(nullable=False, max_length=100)
    schweiz_translated_word: str = Field(nullable=False, max_length=100)



SQLModel.metadata.create_all(engine)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), length(min=4, max=20)])
    submit = SubmitField('Login')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        with Session(engine) as session:
            user = session.exec(select(User).where(User.username == username)).first()

            if user:
                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for("insert"))
                else:
                    flash("Invalid password.", "danger")
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password)
                session.add(new_user)
                session.commit()

                login_user(new_user)
                flash("Account created and logged in successfully!", "success")
                return redirect(url_for("insert"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return render_template("base.html")


@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        return session.get(User, int(user_id))


@app.route("/insert", methods= ["GET", "POST"])
@login_required
def insert():
    if request.method == "POST":
        german_translated_word = request.form['german_translated_word']
        german_word = request.form['german_word']

        if german_translated_word and german_word:
            with Session(engine) as session:
                new_word = GermanWords(user_id=current_user.id, german_translated_word=german_translated_word, german_word=german_word)
                try:
                    session.add(new_word)
                    session.commit()
                    return redirect(url_for("insert"))
                except Exception as e:
                    return redirect(url_for("insert"))
        else:
            return render_template('insert.html')
        
    return render_template('insert.html')


@app.route("/dictionary", methods=["GET", "POST"])
@login_required
def dictionary():
    with Session(engine) as session:
        user_id = current_user.id

        if request.method == "POST":
            for key in request.form:
                if key.startswith("german_word"):
                    word_id = key.split("_")[-1]
                    new_german_word = request.form.get(f"german_word_{word_id}")
                    new_user_word = request.form.get(f"german_translated_word_{word_id}")

                    old_word = session.exec(
                        select(GermanWords).where(GermanWords.user_id == user_id, GermanWords.id == word_id)
                    ).first()

                    if old_word:
                        if new_german_word != old_word.german_word:
                            old_word.german_word = new_german_word
                        if new_user_word != old_word.german_translated_word:
                            old_word.german_translated_word = new_user_word

            session.commit()
            return redirect(url_for("dictionary"))

        words = session.exec(select(GermanWords).where(GermanWords.user_id == user_id)).all()
        return render_template('dictionary.html', words=words)



@app.route("/checkup", methods= ["GET", "POST"])
@login_required
def checkup():
    return render_template('checkup.html')


@app.route("/checkup/generate_word", methods=["POST"])
@login_required
def generate_word():
    user_id = current_user.id
    function = request.json.get('word_type')
    print(f"Function: {function}")

    with Session(engine) as session:
        generated_word = None

        if function == "generate-german":
            generated_word = session.exec(
                select(GermanWords.german_word)
                .where(GermanWords.user_id == user_id)
                .order_by(func.random())
                .limit(1)
            ).first()

        if function == "generate-translation":
            generated_word = session.exec(
                select(GermanWords.german_translated_word)
                .where(GermanWords.user_id == user_id)
                .order_by(func.random())
                .limit(1)
            ).first()

        if generated_word:
            return jsonify(generated_word=generated_word)
        else:
            return jsonify(generated_word="Dude -.-")




@app.route("/checkup/show_translation", methods=["POST", "GET"])
@login_required
def show_translation():
    pass


@app.route("/irregular", methods= ["GET", "POST"])
@login_required
def irregular():
    return render_template('irregular.html')


@app.route("/notes", methods= ["GET", "POST"])
@login_required
def notes():
    return render_template('notes.html')


@app.route("/schweiz", methods= ["GET", "POST"])
@login_required
def schweiz():
    return render_template('schweiz.html')



@app.route("/")
def golden_gate():
    return render_template('base.html')

if __name__ == "__main__":
    app.run()