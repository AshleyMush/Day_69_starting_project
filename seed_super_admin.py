#This is it set the very first admin when the app is launched
@app.before_request
def set_super_admin():
    with app.app_context():
        db.create_all()  # This creates the database tables

        # Create a super admin user
        super_admin_email = os.environ.get('SUPER_ADMIN_EMAIL')
        if super_admin_email:
            # Create the super admin user if it doesn't exist
            if not User.query.filter_by(email=super_admin_email).first():
                super_admin_user = User(
                    email=super_admin_email,
                    username='Admin1',  # Or whatever username you prefer
                    password=generate_password_hash('admin123', method='pbkdf2:sha256', salt_length=8),
                    is_admin=True,  # Make sure this attribute exists in your User model and is boolean
                    agree_to_terms = True
                )


                db.session.add(super_admin_user)
                db.session.commit()
                #Add a sample post
                new_post = Post(
                    author_id= 1,
                    title="This is a Title",
                    subtitle="This is a Subtitle",
                    body="<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse et elementum tellus. Morbi at luctus tellus.</p>",
                    img_url= "https://external-preview.redd.it/i-made-emonggs-hero-randomiser-mode-v0-sboyTNaiu-JKbYsYcerAy769NC1fV8jxo_veWoygsOk.jpg?width=640&crop=smart&auto=webp&s=201aabf108cad495ea85383ecc66467fe265256f",
                    date=date.today().strftime("%B %d, %Y")
                )
                db.session.add(new_post)
                db.session.commit()

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
    posts = relationship("Post", back_populates="user")
    # Essentially changes in POST class must populate back  on user (a var containing child's posts)


# CONFIGURE TABLES
class Post(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # 🟩Foreign Key (New column) |t creates a unique key  link between a Post object and a User object
    author_id = db.Column(db.Integer, ForeignKey("users.id"))

    # 🟩 DEFINE RELATIONSHIPS
    # Connect the Post back to the User, 'parent' is the attribute in User that relates to the Post.
    user = relationship("User", back_populates="posts")




