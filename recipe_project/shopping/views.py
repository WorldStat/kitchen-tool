from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ShoppingList, ShoppingItem

@login_required
def shopping_list_detail(request, pk):
    # Security: Ensure users can only see their own lists
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    items = shopping_list.items.all().order_by('is_purchased', 'name')
    return render(request, 'shopping/shopping_detail.html', {
        'shopping_list': shopping_list,
        'items': items
    })

@login_required
def toggle_item(request, item_id):
    # This is the "missing" function that was causing your error
    if request.method == "POST":
        item = get_object_or_404(ShoppingItem, id=item_id, shopping_list__user=request.user)
        item.is_purchased = not item.is_purchased
        item.save()
        return JsonResponse({'status': 'success', 'is_purchased': item.is_purchased})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def shopping_list_history(request):
    lists = ShoppingList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shopping/history.html', {'lists': lists})