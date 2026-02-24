from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import messages
from recipe_scrapers import scrape_me
from django.shortcuts import render, redirect, get_object_or_404
from .models import Recipe  # Local to recipes app
from shopping.models import ShoppingList, ShoppingItem  # Pulling from shopping app

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
    from django.db.models import Q
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
                'source_url': import_url # Keep the link for reference
            }
            messages.info(request, "Data imported! You can now add a photo and save.")
        except Exception as e:
            messages.error(request, f"Could not scrape this site. You can still enter it manually!")

    # 2. THE SAVE LOGIC
    if request.method == 'POST':
        # CRITICAL: request.FILES must be here for the photo to save
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            
            # Premium Check
            if recipe.image and not request.user.is_paid_customer:
                recipe.image = None
                messages.warning(request, "Photos are a Premium feature. Recipe saved without image.")
            
            recipe.save()
            messages.success(request, "Recipe added to your cookbook!")
            return redirect('recipe_list')
        else:
            messages.error(request, "Error saving recipe. Please check the fields below.")
    else:
        # Pre-fill the form with scraped data if it exists
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
            edited_recipe = form.save(commit=False)
            
            # Premium Check
            if edited_recipe.image and not request.user.is_paid_customer:
                # If they tried to add/change an image but aren't paid, revert it
                # We check if the image has changed by comparing to the original
                if edited_recipe.image != recipe.image:
                    edited_recipe.image = recipe.image
                    messages.warning(request, "Photos are a Premium feature. Image change ignored.")
            
            edited_recipe.save()
            messages.success(request, "Recipe updated successfully!")
            return redirect('recipe_detail', pk=recipe.pk)
        else:
            messages.error(request, "Error updating recipe. Please check the fields below.")
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
