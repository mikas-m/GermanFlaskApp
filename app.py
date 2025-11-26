import re
import os
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field, create_engine, Session, select
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, session, current_app
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, length, EqualTo


load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
db = os.getenv("SQL_DB") or os.getenv("DATABASE_URL") or "sqlite:///germanflaskapp.db"
csrf = CSRFProtect(app)


engine = create_engine(db, echo=False, pool_recycle=280, pool_pre_ping=True)


class User(UserMixin, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, max_length=50)
    password: str = Field(nullable=False, max_length=500)

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
    body: str = Field(nullable=False, max_length=5000)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, 
        sa_column=Column(DateTime(timezone=True))
    )

class SchweizWords(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user_word_id: int = Field(default=None, max_length=50)
    schweiz_word: str = Field(nullable=False, max_length=100)
    schweiz_translated_german_word: str = Field(nullable=False, max_length=100)
    schweiz_translated_word: str = Field(nullable=False, max_length=100)

class irregularVerbs(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    infinitive: str = Field(nullable=False, max_length=100)
    second_third_infinitive: str = Field(nullable=False, max_length=100)
    preterit: str = Field(nullable=False, max_length=100)
    perfekt: str = Field(nullable=False, max_length=100)
    translation: str = Field(nullable=False, max_length=100)



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), length(min=4, max=20)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), length(min=6, max=200)])
    confirm = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')


SQLModel.metadata.create_all(engine)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)



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

def resequence_user_words(session, table, user_id, word_id_field):
    words = session.exec(
        select(table)
        .where(table.user_id == user_id)
        .order_by(table.id)
    ).all()

    for index, word in enumerate(words, start=1):
        setattr(word, word_id_field, index)

    

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
                    login_user(user, remember=form.remember.data)
                    logging.info("User logged in: %s", username)
                    return redirect(url_for("insert"))
                else:
                    logging.warning("Wrong password attempt for user: %s", username)
                    flash('Falsches Passwort', 'error')
            else:
                logging.warning("Login attempt for non-existent user: %s", username)
                flash('Benutzer nicht gefunden — bitte registrieren', 'error')

    return render_template("login.html", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        with Session(engine) as session:
            existing = session.exec(select(User).where(User.username == username)).first()
            if existing:
                logging.warning("Attempt to register existing username: %s", username)
                flash('Benutzername bereits vergeben', 'error')
                return render_template('register.html', form=form)

            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
            session.add(new_user)
            session.commit()
            logging.info("New user registered: %s", username)
            # Log the user in after successful registration
            login_user(new_user)
            flash('Registrierung erfolgreich — Willkommen!', 'success')
            return redirect(url_for('insert'))

    return render_template('register.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    remember_cookie_name = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    resp = redirect(url_for('login'))
    resp.set_cookie(remember_cookie_name, '', expires=0)

    return resp

@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        return session.get(User, int(user_id))



#dictionary views
@app.route("/insert", methods=["GET", "POST"])
@login_required
def insert():
    with Session(engine) as session:
        if request.method == "POST":
            german_word = request.form.get('german_word', '').strip()
            german_translated_word = request.form.get('german_translated_word', '').strip()

            if not german_word or not german_translated_word:
                logging.warning("Missing word or translation.")
                return redirect(url_for("insert"))

            try:
                last_word = session.exec(
                    select(GermanWords)
                    .where(GermanWords.user_id == current_user.id)
                    .order_by(GermanWords.user_word_id.desc())
                    .with_for_update()
                ).first()
                logging.debug(f"Last user word fetched successfully: {last_word}")

                user_word_id = (last_word.user_word_id + 1) if last_word else 1
                logging.info(f"Last user word id determined: {user_word_id}")


                new_word = GermanWords(
                    user_word_id=user_word_id,
                    user_id=current_user.id,
                    german_word=german_word,
                    german_translated_word=german_translated_word
                )
                session.add(new_word)
                session.commit()
                logging.info(f"New word added: {german_word}")
                flash('Wort erfolgreich hinzugefügt!')
                return redirect(url_for("insert"))

            except Exception:
                session.rollback()
                logging.exception("Error while adding new word.")
                return redirect(url_for("insert"))

        try:
            words = session.exec(
                select(GermanWords)
                .where(GermanWords.user_id == current_user.id)
                .order_by(GermanWords.user_word_id)
            ).all()
            logging.info(f"All words fetched for user: {current_user.id}")
        
        except Exception:
            logging.exception("Error while fetching words for user.")
            words = []

        return render_template("insert.html", words=words)
        
@app.route("/delete_word_insert", methods=["POST"])
@login_required
def delete_word_insert():
    word_id = request.form.get("word_id")
    logging.debug(f"Deleting word with id: {word_id}")

    if not word_id:
        logging.warning("No word_id received.")
        flash('Keine ID!', 'error')
        return redirect(url_for("insert"))
    
    try:
        word_id = int(word_id)
    except ValueError:
        logging.warning("Invalid word_id format.")
        flash('Ungültige ID!', 'error')
        return redirect(url_for("insert"))

    with Session(engine) as session:
        word = session.get(GermanWords, int(word_id))
        logging.debug(f"Word found: {word}")

        if word and word.user_id == current_user.id:
            session.delete(word)
            session.commit()
            logging.info("Word deleted, resequencing...")
            resequence_user_words(session, GermanWords, current_user.id, "user_word_id")
            logging.info("Resequencing done.")
            flash('Wort geloscht!', 'success')
        else:
            logging.warning("Word not found or does not belong to user.")
            flash('Das Wort wurde nicht gefunden!', 'error')


    return redirect(url_for("insert"))

@app.route("/dictionary", methods=["GET", "POST"])
@login_required
def dictionary():
    return update_value(
        route_name="insert",             
        html="insert.html",                  
        table=GermanWords,
        first_form_word="german_word",
        second_form_word="german_translated_word",
        first_form_word_id="german_word_",
        second_form_word_id="german_translated_word_",
        third_form_word=None,
        third_form_word_id=None
    )

@app.route("/dictionary/update", methods=["POST"])
@login_required
def update_word():
    data = request.get_json()
    word_id = data.get("id")
    column = data.get("column")
    value = data.get("value", "").strip()
    table_name = data.get("table", "GermanWords")
    
    if not word_id or not column:
        logging.warning("Missing parameters for update_word.")
        return jsonify({"error": "Missing parameters"}), 400

    try:
        word_id = int(word_id)
    except (ValueError, TypeError):
        logging.warning("Invalid word_id format for update_word.")
        return jsonify({"error": "Invalid word ID"}), 400

    allowed_tables = {
        'GermanWords': {
            'model': GermanWords,
            'columns': ["german_word", "german_translated_word"],
            'user_id': 'user_id'
        },
        'SchweizWords': {
            'model': SchweizWords,
            'columns': ["schweiz_word", "schweiz_translated_german_word", "schweiz_translated_word"],
            'user_id': 'user_id'
        },
    }

    if table_name not in allowed_tables:
        logging.warning("Invalid table name for update_word.")
        return jsonify({"error": "Invalid table"}), 400

    table_info = allowed_tables[table_name]

    if column not in table_info['columns']:
        logging.warning("Invalid column name for update_word.")
        return jsonify({"error": "Invalid column for table"}), 400


    try:
        with Session(engine) as session:
            model = table_info['model']
            user_id = table_info['user_id']

            if user_id:
                word = session.exec(
                    select(model)
                    .where(model.id == word_id, getattr(model, user_id) == current_user.id)
                ).first()
                logging.debug(f"Fetched word for update: {word}")
            else:
                word = session.exec(
                    select(model).where(model.id == word_id)
                ).first()
                logging.debug(f"Fetched word for update (no user_id): {word}")

            if not word:
                logging.warning("Word not found for update.")
                return jsonify({"error": "Word not found"}), 404
            

            setattr(word, column, value)

            session.add(word)
            session.commit()
            logging.info(f"Word updated successfully: {word}")
        return jsonify({"status": "ok", "message": "Änderung gespeichert.", "category": "success", "reload": False}), 200

    except Exception as e:
        logging.exception("Error while updating word.")
        return jsonify({"error": "Database error"}), 500
    


#irregular verbs view
@app.route("/irregular", methods=["GET", "POST"])
@login_required
def irregular():
    try:
        with Session(engine) as session:
            verbs = session.exec(select(irregularVerbs)).all()
            logging.info("Irregular verbs fetched successfully.")
    except Exception:
        logging.exception("Error while fetching irregular verbs.")
        verbs = []

    return render_template('irregular.html', verbs=verbs)



#notes views
@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    with Session(engine) as session:

        if request.method == "POST":
            
            data = request.get_json(silent=True) or {}

            title = data.get("title", "").strip()
            body  = data.get("body", "").strip()

            if not title or not body:
                logging.warning("Missing title or body for new note.")
                return jsonify({"error": "Bitte gib Titel und Inhalt ein."}), 400
            
            try:
                last_note_id = session.exec(
                    select(func.max(Notes.user_note_id))
                    .where(Notes.user_id == current_user.id)
                    .with_for_update()
                ).first()
                logging.debug(f"Last user note fetched successfully: {last_note_id}")

                last_note_id = (last_note_id or 0) + 1
                logging.info(f"Last user note id determined: {last_note_id}")   

                new_note = Notes(
                    user_id=current_user.id,
                    user_note_id=last_note_id,
                    title=title,
                    body=body
                )
                logging.info(f"New note created: {title}")
                session.add(new_note)
                session.commit()
                logging.info(f"New note added to database: {title}")

                return jsonify({
                    "success": True,
                    "message": "Notiz gespeichert.",
                    "category": "success",
                    "reload": False,
                    "note": {
                        "id": new_note.id,
                        "user_note_id": new_note.user_note_id,
                        "title": new_note.title,
                        "body": new_note.body
                    }
                }), 200

            except Exception as e:
                session.rollback()
                logging.exception("Error while adding a new note.")
                return jsonify({"error": "Datenbankfehler"}), 500


        notes = session.exec(
            select(Notes)
            .where(Notes.user_id == current_user.id)
            .order_by(Notes.created_at.desc())
        ).all()

        return render_template("notes.html", notes=notes)

@app.route("/notes/edit", methods=["POST"])
@login_required
def edit_note():
    data = request.get_json()
    note_id = data.get("id")
   
    if note_id:
        try:
            note_id = int(note_id)
        except ValueError:
            logging.warning("Invalid note_id format for edit_note.")
            return jsonify({"error": "Invalid note ID"}), 400

    title = data.get("title", "").strip()
    body = data.get("body", "").strip()

    if not note_id or not title or not body:
        logging.warning("Missing fields for edit_note.")
        return jsonify({"error": "Missing fields"}), 400

    try:
        with Session(engine) as session:
            note = session.exec(
                select(Notes)
                .where(Notes.id == note_id, Notes.user_id == current_user.id)
            ).first()
            logging.debug(f"Fetched note for edit: {note}")

            if not note:
                logging.warning("Note not found for edit_note.")
                return jsonify({"error": "Note not found"}), 404

            note.title = title
            note.body = body

            session.add(note)
            session.commit()
            logging.info(f"Note updated successfully: {note}")

            # return updated note to the client so UI can update without full reload
            return jsonify({"status": "ok", "message": "Notiz aktualisiert.", "category": "success", "reload": False,
                            "note": {"id": note.id, "user_note_id": note.user_note_id, "title": note.title, "body": note.body}}), 200

    except Exception:
        logging.exception("Error while editing note.")
        return jsonify({"error": "Server error"}), 500

@app.route("/delete_note", methods=["POST"])
@login_required 
def delete_note():
    note_id = request.form.get("note_id")
    try:
        note_id = int(request.form.get("note_id"))
    except (ValueError, TypeError):
        logging.warning("Invalid note_id format for delete_note.")
        return redirect(url_for("notes"))

    with Session(engine) as session:
        note_to_delete = session.get(Notes, note_id)
        logging.debug(f"Deleting note with id: {note_id}")
        if note_to_delete and note_to_delete.user_id == current_user.id:
            session.delete(note_to_delete)
            session.commit()
            logging.info("Note deleted successfully.")
        else:
            logging.warning("Note not found or does not belong to user.")
    return redirect(url_for("notes"))



#schweiz views
@app.route("/schweiz")
@login_required
def schweiz():
    words = []
    try:
        with Session(engine) as session:
            words = session.exec(select(SchweizWords).where(SchweizWords.user_id == current_user.id)).all()
            logging.info("Schweiz words fetched successfully.")
    except Exception:
        logging.exception("Error while fetching Schweiz words.")
        return render_template('schweiz.html', words=words)
    return render_template('schweiz.html', words=words)

@app.route("/schweiz/insert", methods= ["GET", "POST"])
@login_required
def schweiz_insert():
    if request.method == "POST":
        try:
            schweiz_word = request.form['schweiz_word']
            schweiz_translated_german_word = request.form['schweiz_translated_german_word']
            schweiz_translated_word = request.form['schweiz_translated_word']
        except KeyError:
            logging.warning("Missing form fields for schweiz_insert.")
            return render_template('schweiz.html')

        with Session(engine) as session:
            try:
                last_word = session.exec(select(SchweizWords).where(SchweizWords.user_id == current_user.id).order_by(SchweizWords.user_word_id.desc()).with_for_update()).first()
                logging.debug(f"Last Schweiz user word fetched successfully: {last_word}")
            except Exception:
                logging.exception("Error while fetching last Schweiz user word.")
                return render_template('schweiz.html')

            if last_word:
                last_id = last_word.user_word_id +1
            else:
                last_id = 1
            logging.info(f"Last Schweiz user word id: {last_id}")
            new_word = SchweizWords(user_id=current_user.id, user_word_id=last_id, schweiz_word=schweiz_word, schweiz_translated_german_word=schweiz_translated_german_word, schweiz_translated_word=schweiz_translated_word, )
            logging.info(f"New Schweiz word created: {schweiz_word}")

            session.add(new_word)
            session.commit()
            flash('Wort erfolgreich hinzugefügt!')
            logging.info(f"New Schweiz word added to database: {schweiz_word}")
            return redirect(url_for("schweiz"))

    return render_template('schweiz.html')

@app.route("/delete_word_schweiz", methods=["POST"])
@login_required
def delete_word_schweiz():
    word_id = request.form.get("word_id")
    try:
        word_id = int(request.form.get("word_id"))
        logging.debug(f"Deleting Schweiz word with id: {word_id}")
    except (ValueError, TypeError):
        logging.warning("Invalid word_id format for delete_word_schweiz.")
        return redirect(url_for("schweiz"))
    
    with Session(engine) as session:
        word = session.get(SchweizWords, int(word_id))
        logging.debug(f"Schweiz Word found: {word}")

        if word and word.user_id == current_user.id:
            session.delete(word)
            session.commit()
            logging.info("Schweiz Word deleted, resequencing...")
            resequence_user_words(session, SchweizWords, current_user.id, "user_word_id")
            session.commit()
            logging.info("Resequencing done.")
            flash('Wort geloscht!', 'success')
        else:
            logging.warning("Schweiz Word not found or does not belong to user.")
            flash('Das Wort wurde nicht gefunden!', 'error')

    return redirect(url_for("schweiz"))

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


#app route for homepage
@app.route("/")
def golden_gate():
    return render_template('base.html')

if __name__ == "__main__":
    app.run()