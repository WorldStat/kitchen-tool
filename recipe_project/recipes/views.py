from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import messages
from recipe_scrapers import scrape_me

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
def create_recipe(request):
    initial_data = {}
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
            messages.success(request, "Recipe imported! Check details below.")
        except Exception:
            messages.error(request, "Could not scrape that URL.")

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            if recipe.image and not request.user.is_paid_customer:
                recipe.image = None
                messages.warning(request, "Upgrade to Premium to save images!")
            recipe.save()
            return redirect('recipe_list')
    else:
        form = RecipeForm(initial=initial_data)
    return render(request, 'recipes/create.html', {'form': form})