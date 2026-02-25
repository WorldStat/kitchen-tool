import json
import boto3
import requests
import re
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Recipe
from .forms import RecipeForm

# --- 1. AI EXTRACTION ENGINE (AWS BEDROCK) ---

@login_required
@require_http_methods(["GET"])
def scrape_recipe_api(request):
    """
    Fetches a URL, cleans it, and uses Bedrock in ca-central-1 to extract JSON.
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
        
        # Extract text content (limit to 15,000 characters for cost efficiency)
        text_content = soup.get_text(separator=' ', strip=True)[:15000]

        # Initialize Bedrock Client for Canada Central
        # Note: Ensure your IAM policy allows 'bedrock:InvokeModel'
        client = boto3.client('bedrock-runtime', region_name='ca-central-1')

        # Model: Claude 3.5 Haiku (Standard ID for 2026)
        model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        system_prompt = (
            "You are a recipe data extractor. Return ONLY a raw JSON object with keys: "
            "'title', 'ingredients', 'instructions'. Do not include markdown backticks or text."
        )
        
        messages = [{"role": "user", "content": [{"text": f"Extract: {text_content}"}]}]

        # Using the Converse API (Unified Standard)
        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0}
        )
        
        ai_response_text = response['output']['message']['content'][0]['text']
        
        # Regex safety: Strips ```json ... ``` blocks if the AI accidentally adds them
        clean_json_str = re.sub(r'```json|```', '', ai_response_text).strip()
        recipe_data = json.loads(clean_json_str)

        return JsonResponse(recipe_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- 2. RECIPE CRUD VIEWS ---

@login_required
def recipe_list(request):
    """List only the recipes belonging to the logged-in user."""
    recipes = Recipe.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})

@login_required
def create_recipe(request):
    """Handles new recipe creation (manual or via Auto-Fill)."""
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
def recipe_detail(request, pk):
    """View a single recipe."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

@login_required
def recipe_edit(request, pk):
    """Update an existing recipe (Owner only)."""
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    
    return render(request, 'recipes/add_recipe.html', {'form': form, 'recipe': recipe})

@login_required
def recipe_delete(request, pk):
    """Delete a recipe (Owner only)."""
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/delete_confirm.html', {'recipe': recipe})

@login_required
def clone_recipe(request, pk):
    """Creates a copy of an existing recipe for quick editing."""
    original = get_object_or_404(Recipe, pk=pk, author=request.user)
    
    # Create a copy by setting pk to None
    cloned = original
    cloned.pk = None 
    cloned.title = f"Copy of {original.title}"
    cloned.save()
    
    return redirect('recipe_edit', pk=cloned.pk)