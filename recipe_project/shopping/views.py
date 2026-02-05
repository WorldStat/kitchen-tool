from django.shortcuts import render, get_object_or_404
from .models import ShoppingList
from django.contrib.auth.decorators import login_required

@login_required
def shopping_list_detail(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    return render(request, 'shopping/shopping_detail.html', {
        'shopping_list': shopping_list,
        'items': shopping_list.items.all()
    })