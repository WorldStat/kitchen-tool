from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

def register(request):
    # SECURITY/UX FIX: Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('recipe_list')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to the kitchen! Let's get cooking.")
            return redirect("recipe_list")
        else:
            # This triggers the specific field errors in the template
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "registration/register.html", {"form": form})