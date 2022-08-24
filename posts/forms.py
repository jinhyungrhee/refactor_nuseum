from django import forms

from consumptions.models import FoodImage

class FoodImageForm(forms.ModelForm):
  class Meta:
    model = FoodImage
    fields = '__all__'
