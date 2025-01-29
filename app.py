from flask import Flask, render_template, request, session, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
# Własne funkcje
from functions import *
from db import * 



app = Flask(__name__, template_folder="templates")
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# DB connection
db.init_app(app)
with app.app_context():
    try:
        db.create_all()
        print("Połączenie z bazą danych zostało nawiązane.")
    except Exception as e:
        print(f"Błąd połączenia z bazą danych: {e}")
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



@app.route("/", methods=["GET", "POST"])
def login():
    posts = Poster.query.all()
    if session.get('authorization') or session.get('post_updated'):
        session.pop('post_updated', None)  # Usunięcie flagi po jej użyciu
        return render_template("base.html", session=session, posts=posts)

   

    elif request.method == "POST":
        req  = request.form.to_dict()
        user_valid, message = user_exists(req)
        if user_valid:
            session['authorization'] = True 
            return render_template("base.html",session=session, posts=posts )
        else:
            return render_template("login.html", message=message)
    
    return render_template("login.html")

        
@app.route("/register", methods=["GET", "POST"])
def register(): 
    if request.method == "GET":
        return render_template("register.html")
    
    elif request.method == "POST":
        req  = request.form.to_dict()
        user_valid, message = create_user(req)
        if user_valid:
            session['authorization'] = True
            return redirect(url_for('login'))
        else:
            return render_template("register.html", message=message)
        

@app.route("/logout")
def logut():
    session.clear()
    return redirect(url_for('login'))

@app.route("/create")
def create():
    return render_template("create_post.html")

@app.route('/add', methods=['POST'])
def add_poster():
    """Funkcja do obsługi przesłania formularza z plikiem i opisem"""
    
    # Sprawdzamy, czy plik jest załączony w formularzu
    if 'image' not in request.files:
        return 'Brak pliku', 400  # Jeśli nie ma pliku
    
    image = request.files['image']
    description = request.form['description']
    
    # Jeśli plik jest dozwolony, zapisz go
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        
        # Tworzymy pełną ścieżkę do zapisu na serwerze
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Zapisz plik na serwerze
        image.save(filepath)

        # Zamiana backslash na slash, aby poprawnie zapisać ścieżkę do pliku
        filepath = filepath.replace("\\", "/")  # Zapewni, że używamy / zamiast \
        
        # Dodajemy rekord do bazy danych
        new_poster = Poster(
            text=description,
            img_path=filepath
        )
        db.session.add(new_poster)
        
        try:
            db.session.commit()  # Zapisz zmiany w bazie danych
        except Exception as e:
            db.session.rollback()  # Jeśli coś pójdzie źle, cofnij zmiany
            return f"Wystąpił błąd: {str(e)}", 500  # Zwróć błąd
        finally:
            session['post_updated'] = True
            return redirect(url_for('login'))
    
    return 'Niepoprawny plik', 400  # Jeśli plik nie jest dozwolony

@app.route('/delete-<id>', methods=['POST', 'GET'])
def delete_poster(id):
    # Znalezienie posta na podstawie ID
    post = Poster.query.get(id)
    if post:
        try:
            # Usunięcie posta z bazy danych
            db.session.delete(post)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

    # Przekierowanie na stronę główną lub inną
    session['post_updated'] = True
    return redirect(url_for('login'))

if __name__ == '__main__':    
    app.run(debug=True)