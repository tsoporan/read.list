from flask import Flask, g, request, flash, url_for, redirect
from flask import render_template
from contextlib import closing
import sqlite3
import os
import datetime

#CONFIG
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
SCHEMA_PATH = os.path.join(PROJECT_PATH, 'schema.sql')
DATABASE = os.path.join(PROJECT_PATH, 'readlist.db')
SECRET_KEY = 'iloveponies'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

def init_db():
    print app.config
    with closing(connect_db()) as db:
        with app.open_resource(app.config['SCHEMA_PATH']) as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_requrest():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def book_list():
    cur = g.db.execute('select * from books order by id desc')

    books = [
        dict(
            id=row[0],
            title=row[1],
            description=row[2],
            finished=row[3], 
            created=row[4]) for row in cur.fetchall()
    ]
    
    return render_template('book_list.html', books=books)

@app.route('/add', methods=['POST'])
def add_book():
    
    title = request.form['title']
    description = request.form['description']
    created = datetime.datetime.now()

    g.db.execute('insert into books (title, description, created) values (?, ?, ?)', [title, description, created])

    g.db.commit()
    flash('New book entry was successfully posted!')
    return redirect(url_for('book_list'))


@app.route('/remove/<int:book_id>')
def remove_book(book_id):
    g.db.execute('delete from books where id is (?)' , [book_id])
    g.db.commit()
    flash("Book was removed.")
    return redirect(url_for('book_list')) 

@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404

if __name__ == '__main__':
    app.run()
