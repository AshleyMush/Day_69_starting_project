from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import PostForm, RegisterForm, LoginForm, CreateAdminForm, CommentForm, LeaveCommentButton
from models import db, Post, User, Comment
from flask_migrate import Migrate
import os
from flask_login import current_user
from admin_checker import admin_only
from flask_gravatar import Gravatar
import smtplib
from email.mime.text import MIMEText

# ----Vars--------------------------------------------------

MAIL_ADDRESS = os.environ.get("EMAIL_KEY")
MAIL_APP_PW = os.environ.get("PASSWORD_KEY")

# ---------initialise flask app------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_APP_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

# -----------------Configure DB-------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db.init_app(app)

# Use for migration if needed
# Migrate the db to (Optional)
# migrate = Migrate(app, db)
# ------------Configure Flask-Login----------------------
login_manager = LoginManager()
login_manager.init_app(app)

# ---------For adding profile picture images in comments section-----
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user: {user_id}")
    user = User.query.get(int(user_id))
    if user:
        print(f"Loaded user: {user}")
    else:
        print(f"No user found with ID: {user_id}")
    return user


# ------Create App-------------
with app.app_context():
    db.create_all()


# ______________________________


@app.before_request
def check_for_admin():
    """
    Queries db if super_user_email Admin is in DB
    Admin account email: 'admin@email.com'
    Admin account password: 'admin123'
    :param: super_admin_email (undeletable admin)
    """

    super_admin_email = os.environ.get('SUPER_ADMIN_EMAIL')
    # Search db for this email
    user = User.query.filter_by(email=super_admin_email).first()
    if not user:
        print("😢User: Super ADMIN not found")
    else:
        print("🔐Admin Set and is in DB")


@app.route('/admin/manage', methods=['GET', 'POST'])
def manage_admins():
    """
    Handles the addition or removal of admin privileges for users

    :return: Renders 'make-admin.html' with the form. If the operation is successful, it flashes a success message.
            If the user does not exist or other errors occur, it flashes an appropriate warning or error message.
    """
    print("Entered manage_admins")

    form = CreateAdminForm()
    if form.validate_on_submit():
        # Check if user exists
        user = User.query.filter_by(email=form.email.data).first()
        # Check if 'Make Admin' was clicked
        if form.make_admin.data and user:
            user.is_admin = True
            db.session.commit()
            flash("User is now an admin.", "success")  # Green message

        # Check if 'Remove Admin' was clicked
        elif form.remove_admin.data and user:
            user.is_admin = False
            db.session.commit()
            flash("User is no longer an admin.", "danger")

        else:
            flash("User not found.", "warning")
    return render_template('make-admin.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles the user registration process.

    This route is responsible for both displaying the registration form (GET request) and processing the submitted form data (POST request).
    It performs several checks: password confirmation, uniqueness of email and username, and agreement to terms and conditions.
    If any check fails, it flashes an appropriate message and re-renders the registration form.

    Upon successful validation of all fields, the function creates a new user with hashed and salted passwords, saves the user to the database,
    logs the user in, and redirects to the 'get_all_posts' page.

    :return: Renders 'register.html' with the RegisterForm and current user's authentication status.
             Redirects to 'get_all_posts' on successful registration or remains on the registration page with relevant feedback on failure.
    """

    register_form = RegisterForm()

    if register_form.validate_on_submit():

        if register_form.password.data != register_form.confirm_password.data:
            flash("Passwords Do not Match")
            return render_template("register.html", form=register_form)

        form_email = register_form.email.data
        form_username = register_form.username.data
        form_password = register_form.password.data
        form_agree_to_terms = register_form.agree_to_terms.data

        existing_email = User.query.filter_by(email=form_email).first()
        existing_username = User.query.filter_by(username=form_username).first()

        if existing_email:
            flash("This email address already exists")
            return render_template("register.html", form=register_form)

        if existing_username:
            flash("This username already exists. Please pick another one")
            return render_template("register.html", form=register_form)

        if not form_agree_to_terms:
            flash("You must agree to the terms and conditions to register.")
            return render_template("register.html", form=register_form)

        hashed_and_salted_password = generate_password_hash(form_password, method='pbkdf2:sha256', salt_length=8)

        new_user = User(
            username=form_username,
            email=form_email,
            password=hashed_and_salted_password,
            agree_to_terms=form_agree_to_terms
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Log in successful")

        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=register_form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Authenticates a user and initiates a session.

    This route handles both the display of the login form (GET request) and the processing of the form data (POST request).
    It validates the user's email and password against the database. If validation fails (either the email does not exist
    or the password is incorrect), it flashes an appropriate error message and redirects back to the login page.

    If the validation is successful, it logs in the user and redirects to the 'get_all_posts' page.

    :return: Renders the 'login.html' template with the LoginForm and current user's authentication status.
             Redirects to different routes based on the outcome of the authentication process.
    """

    error = None
    login_form = LoginForm()
    if login_form.validate_on_submit():
        form_email = login_form.email.data
        form_password = login_form.password.data

        # Check if the form email is in DB
        existing_email = User.query.filter_by(email=form_email).first()

        if not existing_email:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
            # Password incorrect
        elif not check_password_hash(existing_email.password, form_password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            # Authenticate user with flask login
            login_user(existing_email)

            return redirect(url_for('get_all_posts'))
    print("Rendering login template")

    return render_template("login.html", form=login_form, current_user=current_user)


@app.route('/logout')
def logout():
    """
    Log out current user  and redirects them to the url for get_all_posts func

    :return: redirect to  the url for get_all_posts func
    """
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/', methods=['GET', 'POST'])
def get_all_posts():
    print("Entered get_all_posts")

    result = db.session.execute(db.select(Post))

    posts = result.scalars().all()

    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    comment_to_delete = Comment.query.get_or_404(comment_id)
    if comment_to_delete.author_id == current_user.id:
        db.session.delete(comment_to_delete)
        db.session.commit()
        flash('Comment deleted.', 'info')
    else:
        flash('You do not have permission to delete this comment.', 'error')
    return redirect(url_for('show_post', post_id=comment_to_delete.post_id))






@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    """
    Displays a specific blog post and handles commenting on the post.

    This route fetches and displays a blog post based on its unique post_id. It also manages the commenting process,
    including displaying a comment form and processing submitted comments. The function checks if the user is
    authenticated before allowing them to leave a comment. If not authenticated, it redirects to the login page.

    If the comment form is submitted and validated, it saves the new comment to the database and refreshes the post page
    to display the newly added comment.

    :param post_id: The unique identifier of the blog post to be displayed.
    :return: Renders 'post.html' with details of the blog post, the current user's authentication status,
             comment form visibility, existing comments, and IDs of comments owned by the current user.
    """

    requested_post = db.get_or_404(Post, post_id)
    comment_form = CommentForm()
    leave_comment = LeaveCommentButton()
    show_form = False

    blog_comments = requested_post.comments

    # Check if the current user is authenticated before accessing the id
    if current_user.is_authenticated:
        owned_comment_ids = [comment.id for comment in blog_comments if current_user.id == comment.author_id]
    else:
        owned_comment_ids = []
    # If the 'Leave a Comment' button was clicked, show the comment form
    if 'comment_button' in request.form:
        if current_user.is_authenticated:
            show_form = True
        else:
            flash("You must be logged in to comment on a post", "alert-danger")
            return redirect(url_for("login"))

    # If the comment form is submitted and valid, process the comment
    if comment_form.validate_on_submit():
        new_comment = Comment(
            text=comment_form.body.data,
            author_id=current_user.id,
            post_id=requested_post.id,
            comment_author=current_user

        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Your comment has been added.", "alert-info")
        return redirect(url_for('show_post', post_id=post_id))

    return render_template(
        "post.html",
        post=requested_post,
        current_user=current_user,
        show_form=show_form,
        form=comment_form,
        leave_comment=leave_comment,
        comments=blog_comments,
        owned_comment_ids=owned_comment_ids
    )


@admin_only
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = PostForm()

    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=True, current_user=current_user)


@admin_only
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    """
    Handles the editing of a specific blog post.

    This function is accessible only to admin users, enforced by the @admin_only decorator. On a GET request, it
    retrieves the post with the specified post_id and pre-populates an editing form with the post's existing data.
    On a POST request, it updates the post in the database with the new data provided through the form.

    If the editing form is submitted and validated, the post's data in the database is updated and the user is
    redirected to the page displaying the updated post. If accessed via GET, the editing form is displayed.

    :param post_id: The unique identifier of the blog post to be edited.
    :return: On a POST request with valid form data, redirects to the 'show_post' page for the edited post.
             On a GET request or if the form data is not valid, renders the 'make-post.html' template for editing.
    """
    post = db.get_or_404(Post, post_id)
    edit_form = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@admin_only
@app.route("/delete/<int:post_id>", methods=["GET", "POST"])
def delete_post(post_id):
    """
    Handles the deletion of a specific blog post.

    This function is accessible only to admin users (enforced by the @admin_only decorator). It looks up the post
    by the given post_id. If the post exists, it is deleted from the database. After successful deletion, it redirects
    the user to the 'get_all_posts' page which lists all the remaining posts.

    :param post_id: The unique identifier of the blog post to be deleted.
    :return: Redirects to the 'get_all_posts' route after the post is deleted.
    """
    post_to_delete = db.get_or_404(Post, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about", methods=["GET", "POST"])
def about():
    """
    Renders the about page

    :return: renders the 'about.html' template with the current_user details
    """
    return render_template("about.html", current_user=current_user)



@app.route("/contact", methods=["GET", "POST"])
def contact():
    """
    Handles the display and processing of the contact form.

    On a GET request, it displays the contact form. On a POST request, it gathers the form data and sends an email
    with the details entered by the user. It uses the 'send_email' function to handle the email sending process.

    After a successful POST request, indicating that the email has been sent, it re-renders the contact page with a
    confirmation message. Otherwise, it displays the contact form without the confirmation message.

    :return: Renders 'contact.html'. If an email is successfully sent, the page includes a confirmation message.
    """
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


def send_email(name, email, phone, message, service='gmail'):
    """
    Sends an email containing the details from a contact form.

    This function creates and sends an HTML-formatted email using the specified email service provider. The email
    includes the sender's name, email, and phone number, along with their message. It uses the SMTP settings
    corresponding to the chosen email service provider. The email is sent from and to the application's configured
    email address but includes a 'Reply-To' header set to the sender's email for easy responses.

    Parameters:
    - name (str): The sender's name as provided in the contact form.
    - email (str): The sender's email address as provided in the contact form.
    - phone (str): The sender's phone number as provided in the contact form.
    - message (str): The message body as provided in the contact form.
    - service (str, optional): The email service provider to use for sending the email. Defaults to 'gmail'. Supported
      options include 'gmail', 'yahoo', and 'outlook'.

    The function attempts to send the email using the SMTP settings for the specified service. If the service is not
    supported, it raises a ValueError. Any errors encountered during the sending process are caught and printed to the
    console.

    Raises:
    - ValueError: If the specified email service provider is not supported.

    Example:
    send_email("John Doe", "johndoe@example.com", "1234567890", "Your blog is awesome!", "yahoo")
    """
    email_message = f"New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}"

    email_content = render_template('email_template.html', name=name, email=email, phone=phone, message=message)

    # -- MIMETEXT logic ---

    msg = MIMEText(email_content, 'html')
    msg['From'] = MAIL_ADDRESS
    msg['To'] = MAIL_ADDRESS
    msg['Subject'] = f"Message from {name}"
    msg['Reply-To'] = email

    # ---SMTP logic-----

    smtp_settings = {
        'gmail': ('smtp.gmail.com', 587),
        'yahoo': ('smtp.mail.yahoo.com', 587),
        'outlook': ('smtp.office365.com', 587)
        # Add more services as needed
    }

    if service in smtp_settings:
        smtp_server, smtp_port = smtp_settings[service]
    else:
        raise ValueError("Unsupported email service")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as connection:
            connection.starttls()
            connection.login(MAIL_ADDRESS, MAIL_APP_PW)
            connection.sendmail(to_addrs=MAIL_ADDRESS, from_addr=email,msg=msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")





if __name__ == "__main__":
    app.run(debug=True, port=5002)
