from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ShoppingItem
from django.contrib import messages
from .forms import ShoppingListForm, ShoppingItemForm


# 1. The Page You See
@login_required
def shopping_list_detail(request, pk):
    from django.db.models import Q
    shopping_list = get_object_or_404(ShoppingList, Q(pk=pk) & (Q(user=request.user) | Q(collaborators=request.user)))
    
    # Separate items so we can show "To Buy" and "Done" separately if we want
    # or just list them all.
    items = shopping_list.items.all().order_by('checked', 'name')
    
    # Form for adding new items
    item_form = ShoppingItemForm()
    
    return render(request, 'shopping/detail.html', {
        'shopping_list': shopping_list,
        'items': items,
        'item_form': item_form,
    })

# 2. The Invisible "Click" Handler
@login_required
@require_POST
def toggle_item(request, item_id):
    # Get the item, ensuring it belongs to a list owned or shared with the current user
    from django.db.models import Q
    item = get_object_or_404(
        ShoppingItem, 
        Q(pk=item_id) & (Q(shopping_list__user=request.user) | Q(shopping_list__collaborators=request.user))
    )
    
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

@login_required
def shopping_list_delete(request, pk):
    # This line is the 'security guard'. If the list.user != request.user, it returns a 404.
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    
    if request.method == "POST":
        shopping_list.delete()
        messages.success(request, "Shopping list permanently deleted.")
        return redirect('shopping_list_history')
    
    return render(request, 'recipes/confirm_delete.html', {
        'object': f"Shopping List #{shopping_list.pk}"
    })

@login_required
@require_POST
def generate_shopping_list(request):
    recipe_ids = request.POST.getlist('selected_recipes')
    if not recipe_ids:
        messages.warning(request, "Please select at least one recipe.")
        return redirect('recipe_list')

    # Create list with a default title based on date
    from django.utils import timezone
    default_title = f"List - {timezone.now().strftime('%b %d')}"
    
    new_list = ShoppingList.objects.create(user=request.user, title=default_title)
    
    selected_recipes = Recipe.objects.filter(id__in=recipe_ids)
    new_list.recipes.set(selected_recipes)

    for recipe in selected_recipes:
        for ingredient in recipe.ingredients.splitlines():
            if ingredient.strip():
                ShoppingItem.objects.create(shopping_list=new_list, name=ingredient.strip(), source_recipe=recipe)
            
    messages.success(request, "Shopping list created!")
    return redirect('shopping_list_detail', pk=new_list.pk)

# --- NEW: MANUALLY CREATE LIST ---
@login_required
def shopping_list_create(request):
    if request.method == 'POST':
        form = ShoppingListForm(request.POST)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.user = request.user
            new_list.save()
            messages.success(request, "New list started!")
            return redirect('shopping_list_detail', pk=new_list.pk)
    else:
        form = ShoppingListForm()
    
    return render(request, 'shopping/list_form.html', {'form': form, 'title': 'Start New List'})

# --- NEW: EDIT LIST NAME ---
@login_required
def shopping_list_edit(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ShoppingListForm(request.POST, instance=shopping_list)
        if form.is_valid():
            form.save()
            messages.success(request, "List renamed.")
            return redirect('shopping_list_detail', pk=shopping_list.pk)
    else:
        form = ShoppingListForm(instance=shopping_list)
        
    return render(request, 'shopping/list_form.html', {'form': form, 'title': 'Rename List'})

# --- NEW: ADD ITEM MANUALLY ---
@login_required
@require_POST
def add_item(request, pk):
    from django.db.models import Q
    shopping_list = get_object_or_404(ShoppingList, Q(pk=pk) & (Q(user=request.user) | Q(collaborators=request.user)))
    form = ShoppingItemForm(request.POST)
    
    if form.is_valid():
        item = form.save(commit=False)
        item.shopping_list = shopping_list
        item.save()
        messages.success(request, "Item added.")
    else:
        messages.error(request, "Could not add item. Check fields.")
        
    return redirect('shopping_list_detail', pk=pk)


# --- NEW: DELETE ITEM MANUALLY ---
@login_required
@require_POST
def delete_item(request, item_id):
    # Get the item, ensuring it belongs to a list owned or shared with the current user
    from django.db.models import Q
    item = get_object_or_404(
        ShoppingItem, 
        Q(pk=item_id) & (Q(shopping_list__user=request.user) | Q(shopping_list__collaborators=request.user))
    )
    
    # Delete the item
    item.delete()
    
    # Return success to JavaScript
    return JsonResponse({'status': 'success'})

@login_required
def manage_collaborators(request, pk):
    shopping_list = get_object_or_404(ShoppingList, pk=pk, user=request.user)
    
    if request.method == "POST":
        action = request.POST.get('action')
        username = request.POST.get('username')
        from users.models import CustomUser
        
        if action == "add":
            try:
                user_to_add = CustomUser.objects.get(username=username)
                if user_to_add == request.user:
                    messages.warning(request, "You are already the owner!")
                else:
                    shopping_list.collaborators.add(user_to_add)
                    messages.success(request, f"Added {username} as a collaborator.")
            except CustomUser.DoesNotExist:
                messages.error(request, f"User '{username}' not found.")
        
        elif action == "remove":
            try:
                user_to_remove = CustomUser.objects.get(username=username)
                shopping_list.collaborators.remove(user_to_remove)
                messages.success(request, f"Removed {username} from collaborators.")
            except CustomUser.DoesNotExist:
                pass
                
        return redirect('shopping_list_detail', pk=pk)
    
    return redirect('shopping_list_detail', pk=pk)

@login_required
def add_recipe_to_list(request, pk):
    """
    Creates a new shopping list from a single recipe's ingredients.
    """
    from recipes.models import Recipe
    from django.utils import timezone
    from django.db.models import Q
    
    # Allow adding from public recipes OR owned recipes
    recipe = get_object_or_404(Recipe, Q(pk=pk) & (Q(owner=request.user) | Q(is_public=True)))
    
    default_title = f"Shopping for {recipe.title}"
    new_list = ShoppingList.objects.create(user=request.user, title=default_title)
    new_list.recipes.add(recipe)

    # Process ingredients
    for ingredient in recipe.ingredients.splitlines():
        if ingredient.strip():
            ShoppingItem.objects.create(
                shopping_list=new_list, 
                name=ingredient.strip(), 
                source_recipe=recipe
            )
            
    messages.success(request, f"Shopping list created for {recipe.title}!")
    return redirect('shopping_list_detail', pk=new_list.pk)
