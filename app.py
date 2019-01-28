import os, hashlib, binascii
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
from flask_migrate import Migrate

app = Flask(__name__)

db_path = os.path.join(os.path.dirname(__file__), 'library.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./library.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


book_author = db.Table('book_author',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=True)
    subtitle = db.Column(db.String(80), unique=False, nullable=True)
    editor = db.Column(db.String(80), unique=False, nullable=True)
    description = db.Column(db.String(200), unique=False, nullable=True)
    url_image = db.Column(db.String(80), unique=False, nullable=True)
    authors = db.relationship('Author', secondary=book_author, lazy='subquery', backref=db.backref('books', lazy=True))

    def __repr__(self):
        return '<Book,{}>'.format(self.title)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=True)

    def __repr__(self):
        return '<Author,{}>'.format(self.name)


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
        book = Book(title=data.get('title'), subtitle=data.get('subtitle'))
        for author in auth:
            au = Author.query.filter_by(name=author).first()
            if au:
                book.authors.append(au)
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



db.create_all()

if __name__ == "main":
    app.run()
