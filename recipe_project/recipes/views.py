import json
import boto3
import requests
import re
from bs4 import BeautifulSoup
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from recipe_scrapers import scrape_me
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
            "You are a recipe data extractor. Return ONLY a raw JSON object with these keys: "
            "'title', 'ingredients' (list of strings), 'instructions' (string), "
            "'servings' (integer), 'prep_time' (integer, minutes), 'cook_time' (integer, minutes). "
            "Do not include markdown backticks."
        )
        
        bedrock_messages = [{"role": "user", "content": [{"text": f"Extract: {text_content}"}]}]

        response = client.converse(
            modelId=model_id,
            messages=bedrock_messages,
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
    """Handles new recipe creation with AI-powered scraping."""
    initial_data = {}
    import_url = request.GET.get('import_url', '').strip()

    # 1. THE SCRAPER LOGIC
    if import_url:
        try:
            # 1a. Fetch the page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            res = requests.get(import_url, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')

            # 1b. Social Media Fallback (Instagram/TikTok/etc)
            # These sites often block the main body but leave OpenGraph tags readable
            text_to_parse = ""
            if "instagram.com" in import_url or "tiktok.com" in import_url:
                meta_desc = soup.find("meta", property="og:description")
                if meta_desc:
                    text_to_parse = meta_desc.get("content", "")
                
            # If not social media or meta-desc failed, use standard body text
            if not text_to_parse:
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "svg"]):
                    tag.decompose()
                text_to_parse = soup.get_text(separator=' ', strip=True)[:15000]

            if not text_to_parse or len(text_to_parse) < 20:
                raise ValueError("Could not extract enough text from the page. The site might be blocking us.")

            # 1c. AI Extraction via Bedrock
            client = boto3.client('bedrock-runtime', region_name='ca-central-1')
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            system_prompt = (
                "You are a master chef and recipe data extractor. Extract data from the text into a raw JSON object with these keys: "
                "'title' (string, use professional Title Case), "
                "'ingredients' (list of strings, include precise quantities), "
                "'instructions' (string, step-by-step), "
                "'servings' (integer), "
                "'prep_time' (integer, minutes), "
                "'cook_time' (integer, minutes). "
                "Return ONLY raw JSON, no markdown backticks."
            )
            
            bedrock_messages = [{"role": "user", "content": [{"text": f"Extract recipe from: {text_to_parse}"}]}]
            
            response = client.converse(
                modelId=model_id,
                messages=bedrock_messages,
                system=[{"text": system_prompt}],
                inferenceConfig={"temperature": 0}
            )
            
            ai_data_raw = response['output']['message']['content'][0]['text']
            ai_data_str = re.sub(r'```json|```', '', ai_data_raw).strip()
            ai_data = json.loads(ai_data_str)
            
            initial_data = {
                'title': ai_data.get('title', '').strip().title(),
                'ingredients': '\n'.join(ai_data.get('ingredients', [])),
                'instructions': ai_data.get('instructions', ''),
                'servings': ai_data.get('servings', 1) or 1,
                'prep_time': ai_data.get('prep_time', 0) or 0,
                'cook_time': ai_data.get('cook_time', 0) or 0,
                'source_url': import_url
            }
            messages.success(request, "AI extracted recipe data successfully!")

        except Exception as e:
            # Last resort fallback: rule-based scraper
            try:
                scraper = scrape_me(import_url)
                initial_data = {
                    'title': scraper.title(),
                    'ingredients': '\n'.join(scraper.ingredients()),
                    'instructions': scraper.instructions(),
                    'servings': scraper.yields(),
                    'source_url': import_url
                }
                messages.info(request, "Imported via standard scraper. Review and save.")
            except Exception as e2:
                messages.error(request, f"Magic Import failed. You can still enter it manually! (Error: {e})")

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
            messages.error(request, f"Error saving recipe. Please check the fields below. {form.errors}")
    else:
        form = RecipeForm(initial=initial_data)
    
    return render(request, 'recipes/create.html', {'form': form, 'import_url': import_url})
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.owner = request.user
            recipe.save()
            messages.success(request, "Recipe added to your cookbook!")
            return redirect('recipe_list')
        else:
            messages.error(request, f"Error saving recipe. Please check the fields below. {form.errors}")
    else:
        form = RecipeForm(initial=initial_data)
    
    return render(request, 'recipes/create.html', {'form': form, 'import_url': import_url})

def recipe_detail(request, pk):
    # Allow viewing if public OR if the current user is the owner
    from django.db.models import Q
    if request.user.is_authenticated:
        recipe = get_object_or_404(Recipe, Q(pk=pk) & (Q(owner=request.user) | Q(is_public=True)))
    else:
        recipe = get_object_or_404(Recipe, pk=pk, is_public=True)
    return render(request, 'recipes/recipe_detail.html', {'recipe': recipe})

@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
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
    # Allow cloning if it's public or owned by the user
    from django.db.models import Q
    original = get_object_or_404(Recipe, Q(pk=pk) & (Q(owner=request.user) | Q(is_public=True)))
    
    # Create a fresh copy
    cloned = Recipe.objects.create(
        owner=request.user,
        title=f"Copy of {original.title}",
        ingredients=original.ingredients,
        instructions=original.instructions,
        servings=original.servings,
        prep_time=original.prep_time,
        cook_time=original.cook_time,
        image=original.image,
        source_url=original.source_url,
        is_public=False  # New copy is private by default
    )
    
    messages.success(request, f"Cloned '{original.title}' to your cookbook!")
    return redirect('recipe_edit', pk=cloned.pk)