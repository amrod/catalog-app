from wtforms import SelectField
from wtforms import StringField
from wtforms import BooleanField
from wtforms import TextAreaField
from wtforms import validators

from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired


class CuisineForm(Form):
    '''
    Form for creating and editing cuisines.
    '''
    name = StringField(
        u'Category Name',
        validators=[
            validators.Length(
                min=4,
                max=100,
                message=u'Name must be between 4 and 25 characters long.')])


class NewRecipeForm(Form):
    '''
    Form for creating a new recipe.
    '''
    name = StringField(
        u'Title',
        validators=[
            validators.Length(
                min=4,
                max=25,
                message=u'Name must be between 4 and 25 characters long.')])

    description = TextAreaField(
        u'Instructions', validators=[validators.Length(min=3, max=2000)])

    cuisine = SelectField(u'Category', coerce=int)

    photo = FileField(u'Photo', validators=[
        FileAllowed(['jpg', 'png'], u'Images of type .jpg or .png only!')
    ])


class EditRecipeForm(Form):
    '''
    Form for editing an existing recipe.
    '''
    name = StringField(
        u'Title',
        validators=[
            validators.Length(
                min=4,
                max=25,
                message=u'Name must be between 4 and 25 characters long.')])

    description = TextAreaField(
        u'Instructions', validators=[validators.Length(min=3, max=2000)])

    cuisine = SelectField(u'Category', coerce=int)

    photo = FileField(u'Photo', validators=[
        FileAllowed(['jpg', 'png'], u'Images of type .jpg or .png only!')
    ])


class DeleteRecipeForm(Form):
    '''
    Form for deleting a recipe.
    '''
    confirm_delete = BooleanField(
        u'I confirm I wish to delete this recipe.', [
            validators.Required("Check the box if you wish to delete this recipe.")])
