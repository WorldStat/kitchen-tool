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

@login_required
def recipe_detail(request, pk):
    # Ensure users can only see their own recipes
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

login_required
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
            form.save()
            messages.success(request, "Recipe updated successfully!")
            return redirect('recipe_detail', pk=recipe.pk)
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
def generate_shopping_list(request):
    if request.method == 'POST':
        recipe_ids = request.POST.getlist('selected_recipes')
        
        if not recipe_ids:
            messages.error(request, "No recipes were selected. Please check at least one box!")
            return redirect('recipe_list')
        
        try:
            # 1. Create the master list
            new_list = ShoppingList.objects.create(user=request.user)
            selected_recipes = Recipe.objects.filter(id__in=recipe_ids, owner=request.user)
            
            # 2. Extract ingredients and save as items
            for recipe in selected_recipes:
                new_list.recipes.add(recipe)
                for line in recipe.ingredients.splitlines():
                    if line.strip():
                        ShoppingItem.objects.create(
                            shopping_list=new_list,
                            name=line.strip(),
                            source_recipe=recipe
                        )
            
            messages.success(request, f"Generated list for {selected_recipes.count()} recipes!")
            # IMPORTANT: Redirect to the NEW list immediately
            return redirect('shopping_list_detail', pk=new_list.pk)
            
        except Exception as e:
            messages.error(request, f"Error generating list: {str(e)}")
            return redirect('recipe_list')

    return redirect('recipe_list')