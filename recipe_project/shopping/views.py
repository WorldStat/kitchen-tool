from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ShoppingItem

# 1. The Page You See
@login_required
def shopping_list_detail(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    
    # Separate items so we can show "To Buy" and "Done" separately if we want
    # or just list them all.
    items = shopping_list.items.all().order_by('checked', 'name')
    
    return render(request, 'shopping/detail.html', {
        'shopping_list': shopping_list,
        'items': items
    })

# 2. The Invisible "Click" Handler
@login_required
@require_POST
def toggle_item(request, item_id):
    # Get the item, ensuring it belongs to a list owned by the current user
    item = get_object_or_404(ShoppingItem, pk=item_id, shopping_list__user=request.user)
    
    # Flip the status
    item.checked = not item.checked
    item.save()
    
    # Return success to JavaScript
    return JsonResponse({'status': 'success', 'checked': item.checked})

@login_required
def shopping_list_history(request):
    # 1. Make sure you are filtering by the current user
    # 2. Make sure you are ordering by date (newest first)
    # 3. Use 'prefetch_related' to get the recipes and items in one go
    user_lists = ShoppingList.objects.filter(user=request.user).prefetch_related('recipes', 'items').order_by('-created_at')
    
    # Debugging tip: print the count to your terminal to see if any exist
    print(f"Found {user_lists.count()} lists for user {request.user}")

    return render(request, 'shopping/history.html', {'user_lists': user_lists})