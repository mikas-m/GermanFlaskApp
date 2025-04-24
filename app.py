import re
import os
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from flask import Flask, render_template, url_for, redirect, request, jsonify
from sqlmodel import SQLModel, Field, create_engine, Session, select
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from markupsafe import Markup, escape
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, length
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
db = os.getenv("SQL_DB")

engine = create_engine(db, echo=False, pool_recycle=280, pool_pre_ping=True)


class User(UserMixin, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, max_length=50)
    password: str = Field(nullable=False, max_length=50)


class GermanWords(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_word_id: int = Field(default=None, max_length=50)
    german_word: str = Field(nullable=False, max_length=100)
    german_translated_word: str = Field(nullable=False, max_length=100)

class Notes(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_note_id: int = Field(default=None, max_length=50)
    title: str = Field(nullable=False, max_length=100)
    body: str = Field(nullable=False, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))

class SchweizWords(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_word_id: int = Field(default=None, max_length=50)
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




@app.template_filter('nl2br')
def nl2br(value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))
    return Markup(result)


#helper function
def update_value(route_name, html, table, first_form_word, second_form_word, first_form_word_id, second_form_word_id, third_form_word, third_form_word_id):
    with Session(engine) as session:
        user_id = current_user.id

        if request.method == "POST":
            changes_made = False

            for key in request.form:
                if key.startswith(f"{first_form_word_id}"):
                    word_id = key.split("_")[-1]
                    new_first_word = request.form.get(f"{first_form_word_id}{word_id}")
                    new_second_word = request.form.get(f"{second_form_word_id}{word_id}")

                    old_word = session.exec(
                        select(table).where(table.user_id == user_id, table.id == word_id)
                    ).first()

                    if old_word:
                        updated = False
                        if new_first_word != getattr(old_word, first_form_word):
                            setattr(old_word, first_form_word, new_first_word)
                            updated = True
                        if new_second_word != getattr(old_word, second_form_word):
                            setattr(old_word, second_form_word, new_second_word)
                            updated = True

                        if third_form_word is not None and third_form_word_id is not None:
                            new_third_word = request.form.get(f"{third_form_word_id}{word_id}")
                            if new_third_word != getattr(old_word, third_form_word):
                                setattr(old_word, third_form_word, new_third_word)
                                updated = True

                        if updated:
                            changes_made = True

            if changes_made:
                session.commit()

            return redirect(url_for(f"{route_name}"))

        words = session.exec(select(table).where(table.user_id == user_id)).all()
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
                if password == user.password:
                    login_user(user, remember=True)
                    return redirect(url_for("insert"))

            else:
                new_user = User(username=username, password=password)
                session.add(new_user)
                session.commit()
                login_user(new_user, remember=True)
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
                last_word = session.exec(select(GermanWords).where(GermanWords.user_id == current_user.id).order_by(GermanWords.user_word_id.desc())).first()

                if last_word:
                    last_id = last_word.user_word_id + 1
                else:
                    last_id = 1

                new_word = GermanWords(user_word_id=last_id, user_id=current_user.id, german_translated_word=german_translated_word, german_word=german_word)
                try:
                    session.add(new_word)
                    session.commit()
                    return redirect(url_for("insert"))
                except Exception:
                    return redirect(url_for("insert"))
        else:
            return render_template('insert.html')

    with Session(engine) as session:
        words = session.exec(
            select(GermanWords).where(GermanWords.user_id == current_user.id)
        ).all()

    return render_template('insert.html', words=words)


    return update_value(
        route_name="dictionary",
        html="dictionary.html",
        table=GermanWords,
        first_form_word="german_word",
        second_form_word="german_translated_word",
        first_form_word_id="german_word_",
        second_form_word_id="german_translated_word_",
        third_form_word=None,
        third_form_word_id=None
    )


#dictionary view
@app.route("/dictionary", methods=["GET", "POST"])
@login_required
def dictionary():
    return update_value(
        route_name="dictionary",
        html="dictionary.html",
        table=GermanWords,
        first_form_word="german_word",
        second_form_word="german_translated_word",
        first_form_word_id="german_word_",
        second_form_word_id="german_translated_word_",
        third_form_word=None,
        third_form_word_id=None
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
        generated_word="-.-",
        correct_translation=""
    )



#irregular verbs view
@app.route("/irregular", methods= ["GET", "POST"])
@login_required
def irregular():
    return render_template('irregular.html')



@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    if request.method == "GET":
        with Session(engine) as session:
            notes = session.exec(
                select(Notes)
                .where(Notes.user_id == current_user.id)
                .order_by(Notes.created_at.desc())
            ).all()
            return render_template('notes.html', notes=notes)

    if request.method == "POST":
        data = request.get_json()
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()

        if not title or not body:
            return jsonify({"error": "Title and body required"}, 400)

        try:
            with Session(engine) as session:
                new_note = Notes(
                    user_id=current_user.id,
                    title=title,
                    body=body
                )
                session.add(new_note)
                session.commit()
                session.refresh(new_note)

                all_notes = session.exec(
                    select(Notes)
                    .where(Notes.user_id == current_user.id)
                    .order_by(Notes.created_at.desc())
                ).all()

                notes_list = []
                for note in all_notes:
                    notes_list.append({
                        "id": note.id,
                        "title": note.title,
                        "body": note.body,
                        "created_at": note.created_at.isoformat() if note.created_at else None  # Handle potential None
                    })

                return jsonify(notes=notes_list), 201

        except Exception as e:
            return jsonify({"error": "Database error", "details": str(e)}, 500)






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
                last_word = session.exec(select(SchweizWords).where(SchweizWords.user_id == current_user.id).order_by(SchweizWords.user_word_id.desc())).first()

                if last_word:
                    last_id = last_word.user_word_id +1
                else:
                    last_id = 1

                new_word = SchweizWords(user_id=current_user.id, user_word_id=last_id, schweiz_word=schweiz_word, schweiz_translated_german_word=schweiz_translated_german_word, schweiz_translated_word=schweiz_translated_word, )

                try:
                    session.add(new_word)
                    session.commit()
                    return redirect(url_for("schweiz"))
                except Exception:
                    return redirect(url_for("schweiz"))
        else:
            return render_template('schweiz.html')

    return render_template('schweiz.html')

@app.route("/schweiz_dictionary", methods= ["GET", "POST"])
@login_required
def schweiz_dictionary():
    return update_value(
            route_name="schweiz",
            html="schweiz.html",
            table=SchweizWords,
            first_form_word="schweiz_word",
            second_form_word="schweiz_translated_german_word",
            first_form_word_id="schweiz_word_",
            second_form_word_id="schweiz_translated_german_word_",
            third_form_word="schweiz_translated_word",
            third_form_word_id="schweiz_translated_word_"
        )

@app.route("/")
def golden_gate():
    return render_template('base.html')

if __name__ == "__main__":
    app.run()