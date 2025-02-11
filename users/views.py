"""
This module contains the views for the users app.

Author: Georgios Tsakoumakis, Jonathan Muse, Ziad El Krekshi, Ayesha Suleman
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .decorators import ban_forbidden, anonymous_required
from django.contrib.auth.models import auth
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
import logging
from .models import CustomUser, ProfessionalUser, Education, Employments
from django.views.defaults import page_not_found
from chatbot.models import Session
from forum.models import Post, Comment
from .forms import (
    UpdateDetailsForm,
    UpdatePasswordForm,
    DeactivateAccountForm,
    UpdateDescriptionForm,
    UpdateFlairForm,
    UpdateEducationForm,
    UpdateEmploymentsForm, BanForm,
)

logger = logging.getLogger('login_attempts')


def index(request):
    """
    Renders the index page at /.
    :param request: Request object
    :return: Rendered index page
    """
    return render(request, "index.html")


@anonymous_required(redirect_url="chatbot/")
def register(request):
    """
    Handles the registration form.
    :param request: Request object
    :return: Redirect to login page if registration is successful, otherwise render the registration page
    """
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        user_type = request.POST["user_type"]
        try:
            flair = request.POST["flair"]
        except:
            flair = None

        try:
            validate_password(password)
        except Exception:
            messages.info(request, "Password not strong enough")
            return redirect("register")

        if password != password2:
            messages.info(request, "Password not matching")
            return redirect("register")

        is_professional = False
        if user_type == "standard":
            is_professional = False
            flair = None
        elif user_type == "professional":
            is_professional = True

        if CustomUser.objects.filter(username=username).exists():
            messages.info(request, "Username already exists")
            return redirect("register")
        elif CustomUser.objects.filter(email=email).exists():
            messages.info(request, "Email already exists")
            return redirect("register")
        else:
            # Save user to database
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.save()
            if is_professional:
                prof = ProfessionalUser(user=user, flair=flair)
                prof.save()
                logger.info(f'Successful account created: {username}')
            return redirect("login")

    return render(request, "register.html")


@anonymous_required(redirect_url="chatbot/")
def login(request):
    """
    Handles the login form.
    :param request: Request object
    :return: Redirect to chatbot page if login is successful, otherwise render the login page
    """
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            session_ids = Session.objects.filter(user=user).values_list(
                "session_id", flat=True
            )
            request.session["session_ids"] = list(session_ids)
            logger.info(f'Successful login attempt for user: {username}')
            return redirect("chatbot/")
        else:
            messages.info(request, "Invalid credentials")
            logger.info(f'Failed login attempt for user: {username}')
            return redirect("login")

    return render(request, "login.html")


@login_required
@ban_forbidden(redirect_url="/banned/")
def dashboard(request):
    """
    Handles all POST requests from the dashboard page.

    Depending on the action in the POST request, different functions are called
    to handle the respective form submissions (update details, change password,
    deactivate account, update description).

    If the request method is GET, the dashboard page is rendered with the user's
    details and forms for updating the user's details, password, description, and flair.

    :param request: Request object
    :return: Rendered dashboard page
    """

    # Initialize forms with the current user's data
    user = CustomUser.objects.get(username=request.user.username)

    # Check if the user is a professional user and get their education and employments
    if user.is_professional:
        professional_user = ProfessionalUser.objects.get(user=request.user)
        try:
            education = Education.objects.get(prof_id=professional_user)
        except Education.DoesNotExist:
            education = None
        try:
            employments = Employments.objects.get(prof_id=professional_user)
        except Employments.DoesNotExist:
            employments = None

        update_education_form = UpdateEducationForm(instance=education)
        update_employments_form = UpdateEmploymentsForm(instance=employments)

    # Initialize forms with the current user's data
    update_details_form = UpdateDetailsForm(instance=request.user)
    update_password_form = UpdatePasswordForm(instance=request.user)
    deactivate_account_form = DeactivateAccountForm(instance=request.user)
    update_description_form = UpdateDescriptionForm(instance=request.user)
    update_flair_form = UpdateFlairForm(instance=request.user)

    # Handle POST requests from the dashboard page based on the action in the request
    if request.method == "POST":
        if "update_details" in request.POST:
            return update_details(request)
        elif "change_password" in request.POST:
            return change_password(request)
        elif "deactivate_account" in request.POST:
            return deactivate_account(request)
        elif "update_description" in request.POST:
            return update_description(request)
        elif "update_flair" in request.POST:
            return update_flair(request)
        elif "update_education" in request.POST:
            return update_education(request)
        elif "update_employments" in request.POST:
            return update_employments(request)

    # Pass the forms to the context for rendering in the template
    if user.is_professional:
        context = {
            "update_details_form": update_details_form,
            "update_password_form": update_password_form,
            "deactivate_account": deactivate_account_form,
            "update_description_form": update_description_form,
            "update_flair_form": update_flair_form,
            "update_education_form": update_education_form,
            "update_employments_form": update_employments_form,
        }
    else:
        context = {
            "update_details_form": update_details_form,
            "update_password_form": update_password_form,
            "deactivate_account": deactivate_account_form,
            "update_description_form": update_description_form,
            "update_flair_form": update_flair_form,
        }

    return render(request, "dashboard.html", context)


@login_required
@ban_forbidden(redirect_url="/banned/")
def deactivate_account(request):
    """
    Deactivates the user's account.

    If the form is valid and the 'deactivate_profile' checkbox is checked,
    the user's account is set to inactive, and the user is redirected to the index page
    with a success message.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the index page with a success message if the account is deactivated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        # Creates a form instance and populates it with data from the request
        form = DeactivateAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            # Check if the 'deactivate_profile' checkbox was checked in the form
            if form.cleaned_data["deactivate_profile"]:
                # Set the user's is_active attribute to False
                request.user.is_active = False
                request.user.save()
                messages.success(request, "Account deactivated successfully")
                return redirect("index")
            else:
                messages.info(request, "Please check the box to deactivate your account")
        else:
            return render(request, "dashboard.html", {"deactivate_account_form": form})
    return redirect("dashboard")


@login_required
@ban_forbidden(redirect_url="/banned/")
def change_password(request):
    """
    Handles the change password form submission.

    If the form is valid, the user's password is updated, the user is kept logged in,
    and a success message is displayed. The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the password is updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        form = UpdatePasswordForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Password updated successfully")
            # Keep the user logged in
            auth.login(request, request.user)
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"change_password_form": form})
    return redirect("dashboard")


@login_required
@ban_forbidden(redirect_url="/banned/")
def update_details(request):
    """
    Handles the update details form submission.

    If the form is valid, the user's details are updated, and a success message is displayed.
    The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the details are updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        form = UpdateDetailsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Details updated successfully")
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"update_details_form": form})
    return redirect("dashboard")


@login_required
@ban_forbidden(redirect_url="/banned/")
def update_description(request):
    """
    Handles the update description form submission.

    If the form is valid, the user's description is updated, and a success message is displayed.
    The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the description is updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        form = UpdateDescriptionForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Description updated successfully")
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"update_description_form": form})


@login_required
@ban_forbidden(redirect_url="/banned/")
def update_flair(request):
    """
    Handles the update flair form submission.

    If the form is valid, the user's flair is updated, and a success message is displayed.
    The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the flair is updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        # Get the professional user profile if it exists, otherwise creates it
        profile, created = ProfessionalUser.objects.get_or_create(user=request.user)

        form = UpdateFlairForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Flair updated successfully")
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"update_flair_form": form})


@login_required
@ban_forbidden(redirect_url="/banned/")
def update_education(request):
    """
    Handles the update education form submission.

    If the form is valid, the user's education is updated, and a success message is displayed.
    The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the education is updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        professional_user = ProfessionalUser.objects.get(user=request.user)
        try:
            # Try to get an existing Education instance
            education = Education.objects.get(prof_id=professional_user)
            # If an instance exists, create a form with the POST data and the existing instance
            form = UpdateEducationForm(request.POST, instance=education)
        except ObjectDoesNotExist:
            # If no instance exists, create a new form with the POST data
            form = UpdateEducationForm(request.POST)
        if form.is_valid():
            # Save the form data to the instance
            education = form.save(commit=False)
            education.prof_id = professional_user
            education.save()
            messages.success(request, "Education updated successfully")
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"update_education_form": form})


@login_required
@ban_forbidden(redirect_url="/banned/")
def update_employments(request):
    """
    Handles the update employments form submission.

    If the form is valid, the user's employments are updated, and a success message is displayed.
    The user is then redirected to the dashboard.

    If the form is not valid, the user is redirected to the dashboard page.

    :param request: Request object
    :return: Redirect to the dashboard page with a success message if the employments are updated successfully,
                otherwise redirect to the dashboard page
    """
    if request.method == "POST":
        professional_user = ProfessionalUser.objects.get(user=request.user)
        try:
            # Try to get an existing Employment instance
            employment = Employments.objects.get(prof_id=professional_user)
            # If an instance exists, create a form with the POST data and the existing instance
            form = UpdateEmploymentsForm(request.POST, instance=employment)
        except ObjectDoesNotExist:
            # If no instance exists, create a new form with the POST data
            form = UpdateEmploymentsForm(request.POST)
        if form.is_valid():
            # Save the form data to the instance
            employment = form.save(commit=False)
            employment.prof_id = professional_user
            employment.save()
            messages.success(request, "Employment updated successfully")
            return redirect("dashboard")
        else:
            return render(request, "dashboard.html", {"update_employments_form": form})


@login_required
def logout(request):
    """
    Logs the user out and redirects them to the index page.
    :param request: Request object
    :return: Redirect to the index page
    """
    request.session.pop("session_ids", None)
    auth.logout(request)
    return redirect("/")


@login_required
@ban_forbidden(redirect_url="/banned/")
def profile(request, username):
    """
    Renders the user profile page for the specified user.
    The user's recent posts and comments are displayed on the page.
    :param request: Request object
    :param username: Username of the user whose profile is being viewed
    :return: Rendered user profile page
    """
    user = CustomUser.objects.get(username=username)
    educations = Education.objects.filter(prof_id__user=user)
    employments = Employments.objects.filter(prof_id__user=user)
    recent_posts = (
        Post.objects.filter(user=user)
        .filter(is_deleted=False)
        .order_by("-created_at")[:3]
    )
    recent_comments = (
        Comment.objects.filter(user=user)
        .filter(is_deleted=False)
        .order_by("-created_at")[:3]
    )
    context = {
        "viewed_user": user,
        "recent_posts": recent_posts,
        "recent_comments": recent_comments,
        "educations": educations,
        "employments": employments,
    }
    return render(request, "user_profile.html", context)


@login_required
def ban_user(request, username):
    """
    Bans a user from the platform. Only superusers can ban users.
    Banned users cannot access any part of the platform, including the chatbot and forum.
    :param request: Request object
    :param username: Username of the user to ban
    """
    if request.user.is_superuser:
        selected_user = get_object_or_404(CustomUser, username=username)
        if request.method == "POST":
            form = BanForm(request.POST, instance=selected_user)
            if form.is_valid():
                selected_user.is_banned = True
                selected_user.reason_banned = form.cleaned_data["reason_banned"]
                selected_user.save()
                messages.success(request, f"User {selected_user.username} has been banned")
                return redirect("profile", username=selected_user.username)
        else:
            form = BanForm(instance=selected_user)
        context = {"form": form, "selected_user": selected_user}
        return render(request, "banpage.html", context)
    else:
        # Return 403 Forbidden
        return render(request, "errors/403.html", status=403)


@login_required
def banned(request):
    """
    Renders the banned page.
    :param request: Request object
    :return: Rendered banned page
    """
    return render(request, "errors/banned.html")


@login_required
def delete_education(request):
    """
    Deletes the education credentials of the user.
    :param request: Request object
    :return: Redirect to the dashboard page
    """
    professional_user = ProfessionalUser.objects.get(user=request.user)
    try:
        education = Education.objects.get(prof_id=professional_user)
        education.delete()
        messages.success(request, "Education credentials deleted successfully")
    except Education.DoesNotExist:
        messages.error(request, "No education credentials found")
    return redirect("dashboard")


@login_required
def delete_employments(request):
    """
    Deletes the employment credentials of the user.
    :param request: Request object
    :return: Redirect to the dashboard page
    """
    professional_user = ProfessionalUser.objects.get(user=request.user)
    try:
        employments = Employments.objects.get(prof_id=professional_user)
        employments.delete()
        messages.success(request, "Employment credentials deleted successfully")
    except Employments.DoesNotExist:
        messages.error(request, "No employment credentials found")
    return redirect("dashboard")


def codeofconduct(request):
    """
    Renders the code of conduct page.
    :param request: Request object
    :return: Rendered code of conduct page
    """
    return render(request, "codeofconduct.html")


def handler400(request, *args, **argv):
    """
    Custom error handler bad request
    :param request: Request object
    :return: Rendered 400 error page
    """
    return render(request, "errors/400.html", status=400)


def handler403(request, *args, **argv):
    """
    Custom error handler forbidden
    :param request: Request object
    :return: Rendered 403 error page
    """
    return render(request, "errors/403.html", status=403)


def handler404(request, exception):
    """
    Custom error handler page not found
    :param request: Request object
    :param exception: Exception object
    :return: Rendered 404 error page
    """
    return page_not_found(request, exception, template_name="errors/404.html")


def handler500(request, *args, **argv):
    """
    Custom error handler internal server error
    :param request: Request object
    :return: Rendered 500 error page
    """
    return render(request, "errors/500.html", status=500)


def handler503(request, *args, **argv):
    """
    Custom error handler service unavailable
    :param request: Request object
    :return: Rendered 503 error page
    """
    return render(request, "errors/503.html", status=503)
