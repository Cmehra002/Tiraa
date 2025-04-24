from project.model import User,Post,Like,Follow
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField, SubmitField,BooleanField, IntegerField
from wtforms.validators import DataRequired,Length,Email,EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user

class RegisterationForm(FlaskForm):
    username= StringField("Username", validators=[DataRequired(),Length(min=2,max=20)])
    email=StringField("Email", validators=[DataRequired(), Email()])
    password=PasswordField("Password",validators=[DataRequired()])
    confirm_password=PasswordField("Confirm Password",validators=[DataRequired(), EqualTo('password')])
    submit=SubmitField("SignUp")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exist. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exist. Please choose a different one.')


class LoginForm(FlaskForm):
    email=StringField("Email", validators=[DataRequired(), Email()])
    password=PasswordField("Password",validators=[DataRequired()])
    remember=BooleanField("Remember Me")
    submit=SubmitField("SignIn")

class AnchorForm(FlaskForm):
    email=StringField("Email", validators=[DataRequired(), Email()])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("SignIn")

class CreateNewsForm(FlaskForm):
    title=StringField('Title ',validators=[DataRequired()])
    news=StringField('News',validators=[DataRequired()])
    submit=SubmitField("Create News")

class DeleteNewsForm(FlaskForm):
    delete=IntegerField("Delete News",validators=[DataRequired()])
    submit=SubmitField("Delete")

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png','jpeg','jfif'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=2)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Password')