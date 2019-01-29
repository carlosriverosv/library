import os

from flask import Flask, jsonify, request, render_template, Response
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


@app.route('/books', methods=['GET', 'POST', 'DELETE'])
def books():
    if request.method == "POST":
        data = request.json
        auth = data.get('authors')
        cat = data.get('categories')
        book = Book(title=data.get('title'), subtitle=data.get('subtitle'))
        if auth:
            for author in auth:
                au = Author.query.filter_by(name=author).first()
                if au:
                    book.authors.append(au)
        if cat:
            for c in cat:
                category_ = Category.query.filter_by(name=c).first()
                if category_:
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
        result = [{"title": book.title, "subtitle": book.subtitle} for book in books_]
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


@app.route('/books/search/', methods=['GET', 'POST', 'DELETE'])
def search_books():
    if request.method == 'GET':
        print(request.args)
        title = request.args.get('title')
        subtitle = request.args.get('subtitle')
        books_result = []
        if title:
            books_result = Book.query.filter_by(title=title)
            if not books_result.count():
                try:
                    payload = {'q': 'intitle:' + title, 'key': 'AIzaSyD5XeAWr1rtAVpwE6PjGmaryapYPKKeJE8'}
                    response = requests.get('https://www.googleapis.com/books/v1/volumes', params=payload)
                    if response.status_code == 200:
                        items = response.json().get('items')
                        r = [dict(id=b.get('id'), title=b.get('volumeInfo').get('title'),
                                  subtitle=b.get('volumeInfo').get('subtitle', ''),
                                  authors=b.get('volumeInfo').get('authors')) for b in items]
                        return jsonify({"data": r, "msg": "response from google books"}), 200
                        #return Response(r, mimetype='application/json')
                        #response = response.json()
                        #return jsonify({"msg": "response from google books", "data": response}), 200
                except ConnectionError:
                    return jsonify({"error": 'Connection error'})

        elif subtitle:
            books_result = Book.query.filter_by(subtitle=subtitle)
        result = [{"title": book.title, "subtitle": book.subtitle} for book in books_result]
        return jsonify({"data": result}), 200

db.create_all()

if __name__ == "main":
    app.run()
