from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import messages
from recipe_scrapers import scrape_me
from django.db.models import Q

from .models import Recipe
from .forms import RecipeForm

class LandingPageView(TemplateView):
    template_name = "landing.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('recipe_list')
        return super().dispatch(request, *args, **kwargs)

@login_required
def recipe_list(request):
    recipes = Recipe.objects.filter(owner=request.user)
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})

def recipe_detail(request, pk):
    # Allow viewing if public OR if the current user is the owner
    if request.user.is_authenticated:
        recipe = get_object_or_404(Recipe, Q(pk=pk) & (Q(owner=request.user) | Q(is_public=True)))
    else:
        recipe = get_object_or_404(Recipe, pk=pk, is_public=True)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

@login_required
def create_recipe(request):
    initial_data = {}
    import_url = request.GET.get('import_url', '')

    # 1. THE SCRAPER LOGIC
    if import_url:
        try:
            scraper = scrape_me(import_url)
            initial_data = {
                'title': scraper.title(),
                'ingredients': '\n'.join(scraper.ingredients()),
                'instructions': scraper.instructions(),
                'servings': scraper.yields(),
                'source_url': import_url
            }
            messages.info(request, "Data imported! You can now add a photo and save.")
        except Exception as e:
            messages.error(request, f"Could not scrape this site. You can still enter it manually!")

    # 2. THE SAVE LOGIC
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            recipe.save()
            messages.success(request, "Recipe added to your cookbook!")
            return redirect('recipe_list')
        else:
            messages.error(request, f"Error saving recipe: {form.errors}")
    else:
        form = RecipeForm(initial=initial_data)

    return render(request, 'recipes/create.html', {
        'form': form,
        'import_url': import_url
    })

@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    
    # Security Check
    if recipe.owner != request.user:
        messages.error(request, "You are not allowed to edit this recipe.")
        return redirect('recipe_list')

    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, "Recipe updated successfully!")
            return redirect('recipe_detail', pk=recipe.pk)
        else:
            messages.error(request, f"Error updating recipe: {form.errors}")
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/create.html', {'form': form, 'editing': True})

@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    
    if recipe.owner != request.user:
        messages.error(request, "You cannot delete this recipe.")
        return redirect('recipe_list')

    if request.method == "POST":
        recipe.delete()
        messages.success(request, "Recipe deleted.")
        return redirect('recipe_list')
    
    return render(request, 'recipes/confirm_delete.html', {'object': recipe})

@login_required
def clone_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, is_public=True)
    
    if recipe.owner == request.user:
        messages.info(request, "This recipe is already in your cookbook!")
        return redirect('recipe_detail', pk=pk)
    
    # Create a copy
    new_recipe = Recipe.objects.create(
        owner=request.user,
        title=f"{recipe.title} (Copy)",
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        servings=recipe.servings,
        image=recipe.image,
        source_url=recipe.source_url
    )
    
    messages.success(request, f"'{recipe.title}' has been added to your cookbook!")
    return redirect('recipe_detail', pk=new_recipe.pk)
