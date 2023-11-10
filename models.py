from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin


db = SQLAlchemy()


# STEP 2 Define a Model
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable= False)
    password = db.Column(db.String(250), nullable=False)
    agree_to_terms = db.Column(db.Boolean, nullable= False)
    is_admin = db.Column(db.Boolean ,default=False)

    # 🟩 DEFINE RELATIONSHIPS
    # ---------- one-to-many relationship ----------
    # 'posts' is the attribute that will hold the user's posts
    # back_populates - ensures that changes on one side of the relationship are reflected back on the other side
    posts = relationship("Post", back_populates="author")
    # Essentially changes in POST class must populate back  on user (a var containing child's posts)
    comments = relationship("Comment", back_populates="comment_author" )



# CONFIGURE TABLES
class Post(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # 🟩Foreign Key (New column) |t creates a unique key  link between a Post object and a User object
    author_id = db.Column(db.Integer, ForeignKey("users.id"))

    # 🟩 DEFINE RELATIONSHIPS
    # Connect the Post back to the User, 'parent' is the attribute in User that relates to the Post.
    author = relationship("User", back_populates="posts")

    # ***************Parent Relationship with comments*************#
    comments = relationship("Comment", back_populates="parent_post") # One-to-many with comments



    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    # 🟩Foreign Key (New column) |t creates a unique key  link between a Post object and a User object
    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    post_id = db.Column(db.Integer, ForeignKey("blog_posts.id"))
    text = db.Column(db.Text, nullable=False)



    # ***************Child Relationship*************#
    comment_author = relationship("User", back_populates="comments")

    parent_post = relationship("Post", back_populates="comments")










