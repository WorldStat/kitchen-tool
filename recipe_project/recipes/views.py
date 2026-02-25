import json
import boto3
import requests
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Recipe
from .forms import RecipeForm

# --- 1. THE AI AUTO-FILL LOGIC (AWS BEDROCK) ---

@login_required
@require_http_methods(["GET"])
def scrape_recipe_api(request):
    target_url = request.GET.get('url')
    if not target_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)

    try:
        # 1. Scrape & Clean
        res = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]): tag.decompose()
        text_content = soup.get_text(separator=' ', strip=True)[:15000]

        # 2. Bedrock Converse API
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        system_prompt = "Return ONLY a raw JSON object with keys: title, ingredients, instructions. No markdown."
        messages = [{"role": "user", "content": [{"text": f"Extract: {text_content}"}]}]

        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0}
        )
        
        raw_output = response['output']['message']['content'][0]['text']
        
        # 3. Clean Markdown Backticks if present
        clean_json_str = re.sub(r'```json|```', '', raw_output).strip()
        return JsonResponse(json.loads(clean_json_str))

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- 2. STANDARD RECIPE VIEWS ---

@login_required
def recipe_list(request):
    """Displays all public recipes and user's own recipes."""
    recipes = Recipe.objects.filter(is_public=True) | Recipe.objects.filter(author=request.user)
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes.distinct()})

@login_required
def add_recipe(request):
    """Handles manual recipe creation and form submission."""
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            return redirect('recipe_list')
    else:
        form = RecipeForm()
    
    return render(request, 'recipes/add_recipe.html', {'form': form})

@login_required
def edit_recipe(request, pk):
    """Edit an existing recipe (owner only)."""
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            return redirect('recipe_list')
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'recipes/edit_recipe.html', {'form': form, 'recipe': recipe})

@login_required
def delete_recipe(request, pk):
    """Delete a recipe."""
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/delete_confirm.html', {'recipe': recipe})