import json
import boto3
import requests
import re
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from .models import Recipe
from .forms import RecipeForm

# --- 1. LANDING PAGE ---

class LandingPageView(TemplateView):
    template_name = "landing.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('recipe_list')
        return super().dispatch(request, *args, **kwargs)


# --- 2. AI EXTRACTION ENGINE (AWS BEDROCK in ca-central-1) ---

@login_required
@require_http_methods(["GET"])
def scrape_recipe_api(request):
    """
    Fetches a URL, cleans it, and uses Bedrock to extract JSON.
    """
    target_url = request.GET.get('url')
    if not target_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)

    try:
        # Fetch and Clean HTML
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "svg"]):
            tag.decompose()
        
        text_content = soup.get_text(separator=' ', strip=True)[:15000]

        # Initialize Bedrock Client for Canada Central
        client = boto3.client('bedrock-runtime', region_name='ca-central-1')

        # Model: Claude 3.5 Haiku
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        system_prompt = (
            "You are a recipe data extractor. Return ONLY a raw JSON object with keys: "
            "'title', 'ingredients', 'instructions'. Do not include markdown backticks."
        )
        
        messages = [{"role": "user", "content": [{"text": f"Extract: {text_content}"}]}]

        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0}
        )
        
        ai_response_text = response['output']['message']['content'][0]['text']
        
        # Strip potential markdown backticks
        clean_json_str = re.sub(r'```json|```', '', ai_response_text).strip()
        recipe_data = json.loads(clean_json_str)

        return JsonResponse(recipe_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- 3. RECIPE CRUD VIEWS (Updated to use 'owner') ---

@login_required
def recipe_list(request):
    """List recipes belonging to the logged-in user."""
    # Fixed: Changed 'author' to 'owner'
    recipes = Recipe.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})

@login_required
def create_recipe(request):
    """Handles new recipe creation."""
    initial_data = {}
    import_url = request.GET.get('import_url', '')

    # 1. THE SCRAPER LOGIC (Premium Feature)
    if import_url:
        if request.user.is_paid_customer:
            try:
                # Assuming scrape_me() returns a dictionary-like object with title, ingredients, etc.
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
                messages.error(request, f"Could not scrape this site. You can still enter it manually! Error: {e}")
        else:
            messages.warning(request, "Web import is a Premium feature. Please upgrade to use it.")
            import_url = '' # Clear the URL to prevent re-attempt if not paid

    # 2. THE SAVE LOGIC
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            
            # Image Check (Premium Feature)
            if recipe.image and not request.user.is_paid_customer:
                recipe.image = None # Discard image if not a paid customer
                messages.warning(request, "Photos are a Premium feature. Recipe saved without image.")
            
            recipe.save()
            messages.success(request, "Recipe added to your cookbook!")
            return redirect('recipe_list')
        else:
            messages.error(request, f"Error saving recipe. Please check the fields below. {form.errors}")
    else:
        # Pre-fill the form with scraped data if it exists
        form = RecipeForm(initial=initial_data)
    
    return render(request, 'recipes/create.html', {'form': form, 'import_url': import_url})

@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            edited_recipe = form.save(commit=False)
            
            # Image Check (Premium Feature)
            if edited_recipe.image and not request.user.is_paid_customer:
                # Compare current image with the one from the database
                if edited_recipe.image != recipe.image: 
                    edited_recipe.image = recipe.image  # Revert to original image
                    messages.warning(request, "Photos are a Premium feature. Image change ignored.")
            
            edited_recipe.save()
            messages.success(request, "Recipe updated successfully!")
            return redirect('recipe_detail', pk=recipe.pk)
        else:
            messages.error(request, f"Error updating recipe. Please check the fields below. {form.errors}")
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/create.html', {'form': form, 'recipe': recipe, 'editing': True})

@login_required
def recipe_delete(request, pk):
    # Fixed: Changed 'author' to 'owner'
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/confirm_delete.html', {'recipe': recipe})

@login_required
def clone_recipe(request, pk):
    # Fixed: Changed 'author' to 'owner'
    original = get_object_or_404(Recipe, pk=pk, owner=request.user)
    
    cloned = original
    cloned.pk = None 
    cloned.title = f"Copy of {original.title}"
    cloned.save()
    
    return redirect('recipe_edit', pk=cloned.pk)