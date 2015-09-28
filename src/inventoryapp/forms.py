from wtforms import SelectField, StringField, DecimalField, IntegerField, BooleanField, TextAreaField, validators
from flask_wtf import Form

class NewCategoryForm(Form):
    category_name = StringField(u'Category Name', validators=[validators.Length(min=4, max=100)])


class NewRecipeForm(Form):
    item_name = StringField(u'Mask Name', validators=[validators.Length(min=4, max=25)])
    description = TextAreaField(u'Description', validators=[validators.Length(min=3, max=800)])
    category = SelectField(u'Category', coerce=int)

class EditRecipeForm(Form):
    recipe_name = StringField(u'Mask Name', validators=[validators.Length(min=4, max=25)])
    description = TextAreaField(u'Description', validators=[validators.Length(min=3, max=800)])
    category = SelectField(u'Category', coerce=int)


