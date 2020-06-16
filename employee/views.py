from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import NewEmployeesAllowed
from .forms import UserChangeForm,PasswordChangeForm,UserSignupForm

def index(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    if request.method == 'POST':
        print(request.POST)
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return render(request, 'employee/index.html', {'form': form, 'message': "Your information has been updated"})
        else:
            return render(request, 'employee/index.html', {'form': form, 'messageError': "ERROR: Your information could NOT be updated"})
    else:
        form = UserChangeForm()

    return render(request, 'employee/index.html', {'form': form})

def change_password(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect(reverse('employee:changePassword'))
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'employee/change_password.html', {
        'form': form
    })

def signup(request):
    if request.user.is_authenticated or NewEmployeesAllowed.objects.get(id=1).is_open == False: 
        raise PermissionDenied
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Thanks so much! <br> You\'ll be able to access SLUGS once we permission you. Don\'t worry, We\'ll let you know as soon as we do! ')
            return redirect(reverse('auth:login'))
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = UserSignupForm()
    return render(request, 'employee/signup.html', {
        'form': form
    })