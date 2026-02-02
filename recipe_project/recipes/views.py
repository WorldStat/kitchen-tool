from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Recipe
from .forms import RecipeForm # You need to create this standard ModelForm
from recipe_scrapers import scrape_me
from django.contrib import messages

@login_required
def create_recipe(request):
    initial_data = {}
    
    # 1. URL Scraping Logic
    if 'import_url' in request.GET:
        url = request.GET.get('import_url')
        try:
            scraper = scrape_me(url)
            initial_data = {
                'title': scraper.title(),
                'ingredients': '\n'.join(scraper.ingredients()),
                'instructions': scraper.instructions(),
                'servings': scraper.yields()
            }
            messages.success(request, "Recipe imported! Add an image or save.")
        except Exception as e:
            messages.error(request, "Could not scrape that URL.")

    # 2. Form Handling
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            
            # Paid Gate for Image
            if recipe.image and not request.user.is_paid_customer:
                recipe.image = None
                messages.warning(request, "Image removed. Upgrade to Premium to save photos.")
            
            recipe.save()
            return redirect('recipe_list') # Assume you have a list view
    else:
        form = RecipeForm(initial=initial_data)

    return render(request, 'recipes/create.html', {'form': form})