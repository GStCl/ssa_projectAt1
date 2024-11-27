from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()  # Deletes the user's account and all related data
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    return render(request, 'users/delete_account.html')


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
         user = form.save()
        messages.success(request, "Your account has been created! Please set up multi-factor authentication.")
        return redirect('two_factor:setup')  # Redirect to MFA setup page
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required(login_url='users:login')
def user(request):
    return render(request, "users/user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        recaptcha_response = request.POST.get("recaptcha-token")  # Updated
        # Verify reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR'),
        }
        recaptcha_verification = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data
        )
        result = recaptcha_verification.json()
        # Check reCAPTCHA response
        if not result.get("success"):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return redirect("users:login")  # Redirect back to the login page
        # Authenticate user if reCAPTCHA is valid
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, else default to user profile
            next_url = request.GET.get('next', reverse("users:user"))  # Simplified fallback
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')