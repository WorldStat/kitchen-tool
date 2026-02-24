from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

from django.contrib.auth.decorators import login_required
from recipes.models import Recipe
from shopping.models import ShoppingList

def register(request):
    # SECURITY/UX FIX: Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('recipe_list')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to the kitchen! Let's get cooking.")
            return redirect("recipe_list")
        else:
            # This triggers the specific field errors in the template
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "registration/register.html", {"form": form})

@login_required
def profile_view(request):
    recipe_count = Recipe.objects.filter(owner=request.user).count()
    public_recipe_count = Recipe.objects.filter(owner=request.user, is_public=True).count()
    list_count = ShoppingList.objects.filter(user=request.user).count()
    shared_list_count = ShoppingList.objects.filter(collaborators=request.user).count()
    
    return render(request, "users/profile.html", {
        "recipe_count": recipe_count,
        "public_recipe_count": public_recipe_count,
        "list_count": list_count,
        "shared_list_count": shared_list_count,
    })

def public_cookbook(request):
    # View to see all recipes shared by the community
    public_recipes = Recipe.objects.filter(is_public=True).order_by('-created_at')
    return render(request, "recipes/public_list.html", {"recipes": public_recipes})