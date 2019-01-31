from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)

    def __repr__(self):
        return '<Category, {}>'.format(self.name)

    def __str__(self):
        return self.name


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=True)
    subtitle = db.Column(db.String(80), unique=False, nullable=True)
    editor = db.Column(db.String(80), unique=False, nullable=True)
    description = db.Column(db.String(200), unique=False, nullable=True)
    url_image = db.Column(db.String(80), unique=False, nullable=True)
    authors = db.relationship('Author', secondary=book_author, backref=db.backref('books', lazy=True))
    categories = db.relationship('Category', secondary=book_category, lazy='subquery',
                                 backref=db.backref('books', lazy=True))

    def __repr__(self):
        return '<Book,{}>'.format(self.title)

    def __str__(self):
        return {"id": self.id, "title": self.title, "subtitle": self.subtitle, "editor": self.editor,
                "description": self.description, "authors": [ath.__str__() for ath in list(self.authors)],
                "categories": [cat.__str__() for cat in list(self.categories)],
                "image": self.url_image}


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __repr__(self):
        return '<Author,{}>'.format(self.name)

    def __str__(self):
        return self.name


book_author = db.Table('book_author',
                       db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
                       db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
                       )

book_category = db.Table('book_category',
                         db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
                         db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
                         )