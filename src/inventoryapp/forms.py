from wtforms import SelectField, StringField, DecimalField, IntegerField, BooleanField, validators
from flask_wtf import Form

class NewMaskForm(Form):
    mask_name = StringField('Mask Name', validators=[validators.Length(min=4, max=25)])
    form_factor = StringField('Form Factor', validators=[validators.Length(min=3, max=25)])
    quantity = IntegerField('Initial Quantity', validators=[validators.NumberRange(min=0)])


class EditMaskForm(Form):
    mask_name = StringField('Mask Name', validators=[validators.Length(min=4, max=25)])
    form_factor = StringField('Form Factor', validators=[validators.Length(min=3, max=25)])


class AddCardsForm(Form):
    quantity = IntegerField('Quantity', validators=[validators.NumberRange(min=1)])


class TransferCardsForm(Form):
    quantity = IntegerField('Quantity', validators=[validators.NumberRange(min=1)])
    destination = SelectField('Destination', coerce=int)

class EmptyTrashForm(Form):
    label = 'I confirm all cards in the Trash Bin have been properly destroyed. The count will be set to zero.'
    confirmation = BooleanField(label, validators=[validators.DataRequired()])

