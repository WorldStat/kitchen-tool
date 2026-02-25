import json, boto3, requests, re
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Recipe
from .forms import RecipeForm

@login_required
def scrape_recipe_api(request):
    """The Bedrock-powered scraper."""
    target_url = request.GET.get('url')
    if not target_url:
        return JsonResponse({'error': 'No URL provided'}, status=400)

    try:
        # 1. Scrape & Clean
        res = requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]): 
            tag.decompose()
        text_content = soup.get_text(separator=' ', strip=True)[:15000]

        # 2. Bedrock Converse API Call
        client = boto3.client('bedrock-runtime', region_name='ca-central-1')
        model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        system_prompt = (
            "You are a recipe extractor. Return ONLY a raw JSON object with keys: "
            "'title', 'ingredients', 'instructions'. No markdown backticks."
        )
        messages = [{"role": "user", "content": [{"text": f"Extract recipe: {text_content}"}]}]

        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0}
        )
        
        raw_output = response['output']['message']['content'][0]['text']
        
        # 3. Clean and Parse JSON safely
        clean_json_str = re.sub(r'```json|```', '', raw_output).strip()
        data = json.loads(clean_json_str)
        return JsonResponse(data)

    except Exception as e:
        # Return the error as JSON instead of crashing the server (which causes 500)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_recipe(request):
    """Standard view to add a recipe."""
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

# Ensure these other views exist in your file as well...
@login_required
def recipe_list(request):
    recipes = Recipe.objects.filter(author=request.user)
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})

@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})