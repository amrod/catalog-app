from wtforms import SelectField, StringField, BooleanField, TextAreaField, SubmitField, validators
from flask_wtf import Form

class NewCategoryForm(Form):
    name = StringField(u'Category Name', validators=[validators.Length(min=4, max=100)])


class NewRecipeForm(Form):
    name = StringField(u'Title', validators=[validators.Length(min=4, max=25)])
    description = TextAreaField(u'Instructions', validators=[validators.Length(min=3, max=800)])
    category = SelectField(u'Category', coerce=int)

class EditRecipeForm(Form):
    name = StringField(u'Title', validators=[validators.Length(min=4, max=25)])
    description = TextAreaField(u'Instructions', validators=[validators.Length(min=3, max=800)])
    category = SelectField(u'Category', coerce=int)


class DeleteRecipeForm(Form):
    confirm_delete = BooleanField(u'I confirm I wish to delete this recipe.', [validators.Required()])
    submit = SubmitField(u'Delete')


