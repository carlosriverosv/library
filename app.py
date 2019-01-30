import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
from flask_migrate import Migrate

import requests

app = Flask(__name__)

db_path = os.path.join(os.path.dirname(__file__), 'library.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./library.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

book_author = db.Table('book_author',
                       db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
                       db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
                       )

book_category = db.Table('book_category',
                         db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
                         db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
                         )


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)

    def __repr__(self):
        return '<Category, {}>'.format(self.name)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=True)
    subtitle = db.Column(db.String(80), unique=False, nullable=True)
    editor = db.Column(db.String(80), unique=False, nullable=True)
    description = db.Column(db.String(200), unique=False, nullable=True)
    url_image = db.Column(db.String(80), unique=False, nullable=True)
    authors = db.relationship('Author', secondary=book_author, lazy='subquery', backref=db.backref('books', lazy=True))
    categories = db.relationship('Category', secondary=book_category, lazy='subquery',
                                 backref=db.backref('books', lazy=True))

    def __repr__(self):
        return '<Book,{}>'.format(self.title)

    def __str__(self):
        return {"title": self.title, "subtitle": self.subtitle, "editor": self.editor,
                "description": self.description}


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __repr__(self):
        return '<Author,{}>'.format(self.name)


@app.route('/categories', methods=['GET', 'POST', 'DELETE'])
def categories():
    if request.method == 'POST':
        data = request.json
        category = Category(name=data.get('name'))
        try:
            db.session.add(category)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return jsonify({"error": {"description": "Category already exist"}}), 400
        else:
            return jsonify({"data": {"name": category.name}}), 201
    elif request.method == 'GET':
        categories_ = Category.query.all()
        result = [{"name": category.name} for category in categories_]
        return jsonify({"data": result}), 200


@app.route('/authors', methods=['GET', 'POST', 'DELETE'])
def authors():
    if request.method == 'POST':
        data = request.json
        author = Author(name=data.get('name'))
        try:
            db.session.add(author)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return jsonify({"error": {"description": "Author already exist"}}), 400
        else:
            return jsonify({"data": {"name": author.name}}), 201
    elif request.method == 'GET':
        authors_ = Author.query.all()
        result = [{"name": author.name} for author in authors_]
        return jsonify({"data": result}), 200


def retrieve_books(query_params=None, id_book=None):
    try:
        if id_book:
            payload = {'key': 'AIzaSyD5XeAWr1rtAVpwE6PjGmaryapYPKKeJE8'}
            url = 'https://www.googleapis.com/books/v1/volumes/' + str(id_book)
        else:
            payload = {'q': query_params, 'key': 'AIzaSyD5XeAWr1rtAVpwE6PjGmaryapYPKKeJE8'}
            url = 'https://www.googleapis.com/books/v1/volumes'
        response = requests.get(url, params=payload)
        print(response.url)
        if response.status_code == 200:
            items = response.json().get('items')
            if items:
                r = [dict(id=b.get('id'), title=b.get('volumeInfo').get('title'),
                          subtitle=b.get('volumeInfo').get('subtitle', ''),
                          authors=b.get('volumeInfo').get('authors'),
                          categories=b.get('volumeInfo').get('categories')) for b in items]
                print(r)
                return r
            b = response.json()
            r = dict(id=b.get('id'), title=b.get('volumeInfo').get('title'),
                     subtitle=b.get('volumeInfo').get('subtitle', ''),
                     authors=b.get('volumeInfo').get('authors'),
                     categories=b.get('volumeInfo').get('categories'))
            print(r)
            return r
    except ConnectionError:
        return jsonify({"error": 'Connection error'})


@app.route('/books', methods=['GET', 'POST', 'DELETE'])
def books():
    if request.method == "POST":
        data = request.json
        id_book = data.get('id')
        if id_book:
            book = retrieve_books(id_book=id_book)
            title = book.get('title', '')
            subtitle = book.get('subtitle', '')
            auth = book.get('authors', '')
            cat = book.get('categories', '')
        else:
            auth = data.get('authors')
            cat = data.get('categories')
            title = data.get('title')
            subtitle = data.get('subtitle')
        book = Book(title=title, subtitle=subtitle)
        if auth:
            for author in auth:
                au = Author.query.filter_by(name=author).first()
                if not au:
                    au = Author(name=author)
                    db.session.add(au)
                    db.session.commit()
                book.authors.append(au)
        if cat:
            for c in cat:
                category_ = Category.query.filter_by(name=c).first()
                if not category_:
                    category_ = Category(name=c)
                    db.session.add(category_)
                    db.session.commit()
                book.categories.append(category_)
        try:
            db.session.add(book)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return jsonify({"error": {"description": "Book already exist"}}), 400
        else:
            return jsonify({"data": {"title": book.title, "subtitle": book.subtitle}}), 201
    elif request.method == "GET":
        books_ = Book.query.all()
        result = [book.__str__() for book in books_]
        return jsonify({"data": result}), 200
    elif request.method == "DELETE":
        data = request.json
        book_title = data.get('title')
        book = Book.query.filter_by(title=book_title).first()
        if book:
            db.session.delete(book)
            try:
                db.session.commit()
                return jsonify({"error": {"description": "Book deleted"}}), 200
            except exc.SQLAlchemyError as e:
                print(e)
                return jsonify({"error": {"description": "Error while processing request"}}), 400
        else:
            return jsonify({"error": {"description": "Book does not exist"}}), 400


@app.route('/books/search/', methods=['GET'])
def search_books():
    if request.method == 'GET':
        print(request.args)
        title = request.args.get('title')
        subtitle = request.args.get('subtitle')
        author = request.args.get('author')
        param = ''
        if title:
            books_result = Book.query.filter_by(title=title)
            param = 'intitle:' + str(title)
        elif subtitle:
            books_result = Book.query.filter_by(subtitle=subtitle)
        elif author:
            pass
        if not books_result.count():
            books_result = retrieve_books(query_params=param)
        return jsonify({"data": books_result}), 200


db.create_all()

if __name__ == "main":
    app.run()
