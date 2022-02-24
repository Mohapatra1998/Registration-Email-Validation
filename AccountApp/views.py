from django.urls import reverse
import re

from django.http import HttpResponse, HttpResponseRedirect
from AccountApp.models import Profile
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
import uuid
from AccountApp.helpers import send_forget_password_mail
from django.db.models import Q
# Create your views here.
@login_required
def home(request):
    return render(request, 'home.html')

def login_attempt(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_obj = User.objects.filter(username = username).first()
            if user_obj is None:
                messages.success(request, 'user not found')
                return redirect('/accounts/login')
            profile_obj = Profile.objects.filter(user = user_obj).first()
            if not profile_obj.is_verified:
                messages.success(request, 'Profile is not verified please check email')
                return redirect('/accounts/login')
            user = authenticate(username = username, password = password)
            if user is None:
                messages.success(request, 'Wrong password')
                return redirect('/accounts/login')
            login(request, user)
            return redirect('/')
        return render(request, 'login.html')
    else:
        return redirect('/')


def register_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(password)
        try:
            if User.objects.filter(username = username).first():
                messages.success(request, 'Username is Taken')
                return redirect('/register')
            if User.objects.filter(email = email).first():
                messages.success(request, 'Email is taken')
                return redirect('/register')
            user_obj = User(username = username, email = email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj = Profile.objects.create(user = user_obj, auth_token= auth_token)
            profile_obj.save()
            send_mail_after_registration(email, auth_token)
            return redirect('/token')
        except Exception as e:
            print(e)
    return render(request, 'register.html')
def success(request):
    return render(request, 'success.html')

def token_send(request):
    return render(request, 'token_send.html')

def verify(request, auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token = auth_token).first()
        if profile_obj:
            if profile_obj.is_verified:
                messages.success(request, 'Your Account is already verified.')
                return redirect('/accounts/login')
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, 'your account has been verified')
            return redirect('/accounts/login')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)
        return redirect('/')
def error_page(request):
    return render(request, 'error.html')


def send_mail_after_registration(email , token):
    subject = 'Your accounts need to be verified'
    message = f'Hi paste the link to verify your account http://127.0.0.1:8000/verify/{token}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message , email_from ,recipient_list )
    
def logout_attempt(request):
    logout(request)
    return redirect('/accounts/login')


def ForgetPassword(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            if not User.objects.filter(Q(username=username) | Q(email=username)).first():
                messages.success(request, 'Not user found with this username')
                return redirect('/forget-password/')
            # user_obj = User.objects.get(username=username)
            user_obj = User.objects.get(Q(username=username) | Q(email=username))
            token = str(uuid.uuid4())
            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.save()
            send_forget_password_mail(user_obj.email, token)
            messages.success(request, 'An email is sent')
            return redirect('/forget-password/')
    except Exception as e:
        print(e)
        return render(request, 'forget-password.html')
    return render(request, 'forget-password.html')


def ChangePassword(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(forget_password_token=token).first()
        context = {'user_id': profile_obj.user.id}
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')
            user_id = int(user_id)
            # print(type(user_id))
            if user_id is None:
                messages.success(request, 'No user id found.')
                # return redirect(f'/change-password/{token}/')
                return HttpResponseRedirect(reverse('change_password'))
            if new_password != confirm_password:
                messages.success(request, 'Both should be equel.')
                # return redirect(f'/change-password/{token}/')
                return HttpResponseRedirect(reverse('change_password'))
            user_obj = User.objects.get(id = user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            return redirect('/accounts/login')
    except Exception as e:
        print(e)
        return render(request, 'change-password.html')
    return render(request, 'change-password.html', context)

        
