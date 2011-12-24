from flask import Flask, g, request, flash, url_for, redirect, jsonify, escape
from flask import render_template
from jinja2 import filters
from jinja2.utils import urlize
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

book_html = """
    <li class="%s">
    <div class="content" id="%s">
        <nav id="book_nav">
            <a href="#" class="edit">[edit]</a>
            <a href="#" class="finish">[finish]</a>
            <a href="#" class="remove">[remove]</a>
        </nav>
        <h3>%s</h3>
        <p class="desc">%s</p>
        <time>added: <strong>%s</strong></time>
    </div>

    <div class="edit" id="%s" style="display:none">
        <h3>edit book</h3>
        <p>
        <strong>Title</strong>
        <input class="edit_title" type="text" name="edit_title" value="%s">
        </p>
        <p>
        <strong>Description</strong>
        <textarea rows="10" cols="50" class="edit_desc" name="edit_desc">%s</textarea>
        </p>
        <button type="submit" name="edit_submit">save</button>
    </div>
    </li>
""".strip() 

date_format = "%b %d, %Y @ %H:%m"

def datetimeformat(value, format=date_format):
    return value.strftime(format)

filters.FILTERS['datetimeformat'] = datetimeformat

def convert_date(s):
    date = s.split('.')[0] 
    return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

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
def index():
    cur = g.db.execute('select * from books order by id desc')

    books = []
    
    for row in cur.fetchall():
        d = {}
        d['id'] = row[0]
        d['title'] = row[1]
        d['description'] = row[2]
        d['finished'] = row[3]
        d['created'] = convert_date(row[4]) 
        books.append(d)

    return render_template('index.html', books=books)

@app.route('/add', methods=['POST'])
def add_book():
   
    title = escape(request.form.get('title', ''))
    description = escape(request.form.get('description', ''))
    created = datetime.datetime.now()
    
    if title and description:
        
        error = None 
        
        #some basic dupe checking
        existing = g.db.execute('select * from books where title like (?)', [title]).fetchall()
        g.db.commit()

        if existing:
            error = u"A book with this title already exists! DUN DUN DUN ..."
       
        if request.is_xhr:
         
            if error:
                return jsonify(error=error)
            
            #create new book
            g.db.execute('insert into books (title, description, created) values (?, ?, ?)', [title, description, created])
            g.db.commit()
        
            book_id = g.db.execute('select id from books where title like (?)', [title]).fetchone()[0]

            html = book_html % (
                    'reading', #assume book is not finished if just added
                    book_id,
                    title,
                    urlize(description),
                    datetimeformat(created),
                    book_id,
                    title,
                    description,
            )

            return jsonify(html=html)
        
        else:
            return u"XHR requests only."
    
    else:
        return jsonify(error="Missing the stuffs!")

@app.route('/update', methods=['POST'])
def update_book():

    book_id = escape(request.form.get('book_id', ''))
    edit_title = escape(request.form.get('edit_title', ''))
    edit_desc = escape(request.form.get('edit_desc', ''))

    if book_id and edit_title and edit_desc:
        
        if request.is_xhr:
            
            #update the book informations and return html
            g.db.execute('update books SET title = ?, description = ? WHERE rowid = ?', (edit_title, edit_desc, int(book_id)))
            g.db.commit()

            book = g.db.execute('select * from books where id = ?', [int(book_id)]).fetchone()
            g.db.commit()

            html = book_html % (
                'finished' if book[3] else 'reading', #book could be finished 
                book[0], #id
                book[1], #title
                urlize(book[2]), #desc
                datetimeformat(convert_date(book[4])),
                book[0],
                book[1],
                book[2],
            )

            return jsonify(success=True, html=html) 
        
        else:
            return u"XHR requests only."
    
    else:
        return jsonify(error=u"Missing all the stuffs.")


@app.route('/remove', methods=['POST'])
def remove_book():
        
    book_id = escape(request.form.get('book_id', None))
   
    if book_id:
        if request.is_xhr:
          
            #delete book for id
            g.db.execute('delete from books where id is (?)' , [book_id])
            g.db.commit()
   
            return jsonify(msg=u"D: book was removed!")

        else:
            return u"XHR requests only."
    else:
        return jsonify(error="No book id? o.o")


@app.route('/finish', methods=['POST'])
def finish_book():
    
    book_id = escape(request.form.get('book_id', None))
   
    if book_id:

        if request.is_xhr:
            #update book, set finished to 1
            g.db.execute('update books SET finished = ? WHERE rowid = ?', [1, book_id])
            g.db.commit() 
            
            return jsonify(msg=u"Woot! You finished ze book! Hug yourself. Do it.")

        else:
            return u"XHR requests only."
    else:
        return jsonify(error=u"No book id? o.o")

@app.route('/sort', methods=['GET'])
def sort():
    #sort by: all | finished
    pass

@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404

if __name__ == '__main__':
    app.run()
