from django import forms
from .models import Recipe

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'ingredients', 'instructions', 'servings', 'prep_time', 'cook_time', 'image', 'source_url', 'is_public']
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter ingredients...'}),
            'instructions': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter cooking steps...'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mom\'s Lasagna'}),
            'servings': forms.NumberInput(attrs={'class': 'form-control'}),
            'prep_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'cook_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'source_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/recipe'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }