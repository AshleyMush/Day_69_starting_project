from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, Email, Length, ValidationError, InputRequired
from flask_ckeditor import CKEditorField
import re


# WTForm for creating a blog post
class PostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


#Function to complicate passwords
def password_complexity(form, field):
    password = field.data
    if not re.search("[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search("[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search("[0-9]", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")




class RegisterForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])


    email = StringField(label='email', validators=[DataRequired(),Email(message="You seem to be missing @ or .")])


    password = PasswordField(
        label="Password",
        validators=[
            DataRequired(message="Do not leave this field empty"),
            Length( min=8, message="Pasword must be 8 characters minimum"),
            password_complexity  # Adds complexity to password

        ]

    )
    confirm_password = PasswordField(
        label="Confirm Password",
        validators=[
            DataRequired(message="Do not leave this field empty"),
            Length(min=8)


        ]

    )

    agree_to_terms = BooleanField('I agree to the Terms and Conditions', validators=[InputRequired()])
    submit = SubmitField('Submit')




class LoginForm(FlaskForm):
    email = StringField(label='email', validators=[DataRequired(), Email(message="You seem to be missing @ or .")])

    password = PasswordField(
        label="Password",
        validators=[DataRequired(message="Do not leave this field empty"),Length(min=8, message="Pasword must be 8 characters minimum"),])

    submit = SubmitField('Submit')


class CreateAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    make_admin = SubmitField('Make Admin')
    remove_admin = SubmitField('Remove Admin')


class LeaveCommentButton(FlaskForm):
    comment_button = SubmitField('Leave A Comment')



class CommentForm(FlaskForm):

    body = CKEditorField('', validators=[DataRequired()])
    submit_button = SubmitField('Submit Comment')


