from django import forms
from .models import ShoppingList, ShoppingItem

class ShoppingListForm(forms.ModelForm):
    class Meta:
        model = ShoppingList
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g., Weekly Groceries'}),
        }

class ShoppingItemForm(forms.ModelForm):
    class Meta:
        model = ShoppingItem
        fields = ['name', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name (e.g., Milk)'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qty (e.g., 2 liters)'}),
        }