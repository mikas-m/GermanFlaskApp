import os
from sqlalchemy.sql import func, or_
from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from sqlmodel import SQLModel, Field, create_engine, Session, select
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, length
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, template_folder='templates')
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
    schweiz_translated_german_word: str = Field(nullable=False, max_length=100)
    schweiz_translated_word: str = Field(nullable=False, max_length=100)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), length(min=4, max=20)])
    submit = SubmitField('Login')

SQLModel.metadata.create_all(engine)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

#helper function
def add_to_dictionary(html, first_word, new_form_word, new_form_translated_word, new_word_id, new_translated_word_id, table):
    with Session(engine) as session:
        user_id = current_user.id

        if request.method == "POST":
            for key in request.form:
                if key.startswith(f"{new_word_id}"):
                    word_id = key.split("_")[-1]
                    new_word = request.form.get(f"{new_word_id}{word_id}")
                    new_translated_word = request.form.get(f"{new_translated_word_id}{word_id}")

                    # Update the existing word in the database
                    old_word = session.exec(
                        select(table).where(table.user_id == user_id, table.id == word_id)
                    ).first()

                    if old_word:
                        if new_word != old_word.new_form_word:
                            old_word.new_form_word = new_word
                        if new_form_translated_word != old_word.new_form_translated_word:
                            old_word.new_form_translated_word = new_form_translated_word

            session.commit()
            return redirect(url_for(f"{html}"))

        # Retrieve the words to display
        words = session.exec(select(table).where(table.user_id == user_id)).all()
        print(words)
        return render_template(html, words=words)


#general
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
    return render_template("base.html")

@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        return session.get(User, int(user_id))



#insert view
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



#dictionary view
@app.route("/dictionary", methods=["GET", "POST"])
@login_required
def dictionary():
    return add_to_dictionary(
        html="dictionary.html",
        first_word="german_word",
        new_form_word="german_word",
        new_form_translated_word="german_translated_word",
        new_word_id="german_word_",
        new_translated_word_id="german_translated_word_",
        table=GermanWords
    )



#checkup view
@app.route("/checkup", methods= ["GET", "POST"])
@login_required
def checkup():
    return render_template('checkup.html')

@app.route("/checkup/generate_word", methods=["POST"])
@login_required
def generate_word():
    user_id = current_user.id
    word_type = request.json.get('word_type')

    with Session(engine) as session:
        word = session.exec(
            select(GermanWords)
            .where(GermanWords.user_id == user_id)
            .order_by(func.random())
            .limit(1)
        ).first()

        if word:
            if word_type == "generate-german":
                return jsonify(
                    generated_word=word.german_word,
                    correct_translation=word.german_translated_word
                )
            elif word_type == "generate-translation":
                return jsonify(
                    generated_word=word.german_translated_word,
                    correct_translation=word.german_word
                )

    return jsonify(
        generated_word="Dude, you have no words in your dictionary!",
        correct_translation=""
    )



#irregular verbs view
@app.route("/irregular", methods= ["GET", "POST"])
@login_required
def irregular():
    return render_template('irregular.html')



#notes view
@app.route("/notes", methods= ["GET", "POST"])
@login_required
def notes():
    return render_template('notes.html')



#schweiz view
@app.route("/schweiz")
@login_required
def schweiz():
    with Session(engine) as session:
        words = session.exec(select(SchweizWords).where(SchweizWords.user_id == current_user.id)).all()
        print(words)
        return render_template('schweiz.html', words=words)

@app.route("/schweiz/insert", methods= ["GET", "POST"])
@login_required
def schweiz_insert():
    if request.method == "POST":
        schweiz_word = request.form['schweiz_word']
        schweiz_translated_german_word = request.form['schweiz_translated_german_word']
        schweiz_translated_word = request.form['schweiz_translated_word']
        

        if schweiz_word and schweiz_translated_german_word and schweiz_translated_word:
            with Session(engine) as session:
                new_word = SchweizWords(user_id=current_user.id, schweiz_word=schweiz_word, schweiz_translated_german_word=schweiz_translated_german_word, schweiz_translated_word=schweiz_translated_word, )
                try:
                    session.add(new_word)
                    session.commit()
                    return redirect(url_for("schweiz"))
                except Exception as e:
                    return redirect(url_for("schweiz"))
        else:
            return render_template('schweiz.html')
        
    return render_template('schweiz.html')

@app.route("/schweiz_dictionary", methods= ["GET", "POST"])
@login_required
def schweiz_dictionary():
    return add_to_dictionary(
        html="schweiz.html",
        first_word="schweiz_word",
        new_form_word="schweiz_word",
        new_form_translated_word="schweiz_translated_word",
        new_word_id="schweiz_word_",
        new_translated_word_id="schweiz_translated_word_",
        table=SchweizWords
    )




@app.route("/")
def golden_gate():
    return render_template('base.html')

if __name__ == "__main__":
    app.run()



