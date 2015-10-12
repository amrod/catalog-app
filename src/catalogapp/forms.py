from wtforms import SelectField, StringField, BooleanField, TextAreaField, SubmitField, validators
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired



class NewCategoryForm(Form):
    name = StringField(u'Category Name', validators=[validators.Length(min=4, max=100,
                                                     message=u'Name must be between 4 and 25 characters long.')])


class NewRecipeForm(Form):
    name = StringField(u'Title',
                       validators=[validators.Length(min=4, max=25,
                                                     message=u'Name must be between 4 and 25 characters long.')])

    description = TextAreaField(u'Instructions', validators=[validators.Length(min=3, max=2000)])
    category = SelectField(u'Category', coerce=int)

    photo = FileField(u'Photo', validators=[
        FileAllowed(['jpg', 'png'], u'Images of type .jpg or .png only!')
    ])


class EditRecipeForm(Form):
    name = StringField(u'Title', validators=[validators.Length(min=4, max=25,
                                                             message=u'Name must be between 4 and 25 characters long.')])
    description = TextAreaField(u'Instructions', validators=[validators.Length(min=3, max=2000)])
    category = SelectField(u'Category', coerce=int)
    photo = FileField(u'Photo', validators=[
        FileAllowed(['jpg', 'png'], u'Images of type .jpg or .png only!')
    ])


class DeleteRecipeForm(Form):
    confirm_delete = BooleanField(u'I confirm I wish to delete this recipe.',
                                  [validators.Required("Check the box if you wish to delete this recipe.")])



