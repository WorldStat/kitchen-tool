from django import forms
from .models import Recipe

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'ingredients', 'instructions', 'servings', 'image', 'is_public']
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter ingredients...'}),
            'instructions': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter cooking steps...'}),
        }