from django.http import HttpRequest, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import redirect
from django.contrib.auth.models import User
from . import page_skeleton, magic
from .form import Form, TextField, PlainText, TextArea, SubmitButton, NumberField, PasswordField, CheckBox, CheckEnum
from ..models import Profile, Media
from ..uitools.dataforge import get_csrf_form_element
from .magic import get_current_user
import logging


def render_edit_page(http_request: HttpRequest, action_url: str):

    user_id = None
    profile: Profile = None
    if http_request.GET.get("user_id"):
        user_id = int(http_request.GET["user_id"])
    if user_id is not None:
        profile = Profile.objects.get(pk=user_id)
    f = Form()
    f.action_url = action_url
    if profile:
        f.add_content(PlainText('<h3>Edit user "' + profile.authuser.username + '"</h3>'))
        f.add_content(PlainText('<a href="/admin/media/select?action_url=/admin/actions/change-user-avatar'
                                '&payload=' + str(user_id) + '"><img class="button-img" alt="Change avatar" '
                                'src="/staticfiles/frontpage/change-avatar.png"/></a><br />'))
    else:
        f.add_content(PlainText('<h3>Add new user</h3>'))
    if not profile:
        f.add_content(PlainText("username (can't be edited later on): "))
        f.add_content(TextField(name='username'))
    if http_request.GET.get('fault') and profile:
        f.add_content(PlainText("Unable to edit user due to: " + str(http_request.GET['fault'])))
    elif http_request.GET.get('fault'):
        f.add_content(PlainText("Unable to add user due to: " + str(http_request.GET['fault'])))
    current_user: Profile = get_current_user(http_request)
    if current_user.rights > 3:
        if not profile:
            f.add_content(CheckBox(name="active", text="User Active", checked=CheckEnum.CHECKED))
        else:
            m: CheckEnum = CheckEnum.CHECKED
            if not profile.active:
                m = CheckEnum.NOT_CHECKED
            f.add_content(CheckBox(name="active", text="User Active", checked=m))
    if profile:
        f.add_content(PlainText("Email address: "))
        f.add_content(TextField(name='email', button_text=str(profile.authuser.email)))
        f.add_content(PlainText("Display name: "))
        f.add_content(TextField(name='display_name', button_text=profile.displayName))
        f.add_content(PlainText('DECT: '))
        f.add_content(NumberField(name='dect', button_text=str(profile.dect), minimum=0))
        f.add_content(PlainText('Number of allowed reservations: '))
        f.add_content(NumberField(name='allowed_reservations', button_text=str(profile.number_of_allowed_reservations), minimum=0))
        f.add_content(PlainText("Rights: "))
        f.add_content(NumberField(name="rights", button_text=str(profile.rights), minimum=0, maximum=4))
        f.add_content(PlainText('Notes:<br/>'))
        f.add_content(TextArea(name='notes', text=str(profile.notes)))
    else:
        f.add_content(PlainText("Email address: "))
        f.add_content(TextField(name='email'))
        f.add_content(PlainText("Display name: "))
        f.add_content(TextField(name='display_name'))
        f.add_content(PlainText('DECT: '))
        f.add_content(NumberField(name='dect', minimum=0))
        f.add_content(PlainText('Number of allowed reservations: '))
        f.add_content(NumberField(name='allowed_reservations', button_text=str(1), minimum=0))
        f.add_content(PlainText("Rights: "))
        f.add_content(NumberField(name="rights", button_text=str(0), minimum=0, maximum=4))
        f.add_content(PlainText('Notes:<br/>'))
        f.add_content(TextArea(name='notes', placeholder="Hier könnte ihre Werbung stehen"))
    if profile:
        f.add_content(PlainText('<br /><br />Change password (leave blank in order to not change it):'))
    else:
        f.add_content(PlainText('<br />Choose a password: '))
    f.add_content(PasswordField(name='password', required=False))
    f.add_content(PlainText('Confirm your password: '))
    f.add_content(PasswordField(name='confirm_password', required=False))
    f.add_content(PlainText(get_csrf_form_element(http_request)))
    f.add_content(SubmitButton())
    # a = page_skeleton.render_headbar(http_request, "Edit User")
    a = '<div class="w3-row w3-padding-64 w3-twothird w3-container admin-popup">'
    a += f.render_html(http_request)
    # a += page_skeleton.render_footer(http_request)
    a += "</div>"
    return a


def check_password_conformity(pw1: str, pw2: str):
    if not (pw1 == pw2):
        return False
    if len(pw1) < 6:
        return False
    if pw1.isupper():
        return False
    if pw1.islower():
        return False
    return True


def recreate_form(reason: str):
    return redirect('/admin/users/edit?fault=' + str(reason))


def action_save_user(request: HttpRequest, default_forward_url: str = "/admin/users"):
    """
    This functions saves the changes to the user or adds a new one. It completely creates the HttpResponse
    :param request: the HttpRequest
    :param default_forward_url: The URL to forward to if nothing was specified
    :return: The crafted HttpResponse
    """
    forward_url = default_forward_url
    if request.GET.get("redirect"):
        forward_url = request.GET["redirect"]
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    profile = Profile.objects.get(authuser=request.user)
    if profile.rights < 2:
        return HttpResponseForbidden()
    try:
        if request.GET.get("user_id"):
            pid = int(request.GET["user_id"])
            displayname = str(request.POST["display_name"])
            dect = int(request.POST["dect"])
            notes = str(request.POST["notes"])
            pw1 = str(request.POST["password"])
            pw2 = str(request.POST["confirm_password"])
            mail = str(request.POST["email"])
            rights = int(request.POST["rights"])
            user: Profile = Profile.objects.get(pk=pid)
            user.displayName = displayname
            user.dect = dect
            user.notes = notes
            user.rights = rights
            user.number_of_allowed_reservations = int(request.POST["allowed_reservations"])
            if request.POST.get("active"):
                user.active = magic.parse_bool(request.POST["active"])
            au: User = user.authuser
            if check_password_conformity(pw1, pw2):
                logging.log(logging.INFO, "Set password for user: " + user.displayName)
                au.set_password(pw1)
            else:
                logging.log(logging.INFO, "Failed to set password for: " + user.displayName)
            au.email = mail
            au.save()
            user.save()
        else:
            # assume new user
            username = str(request.POST["username"])
            displayname = str(request.POST["display_name"])
            dect = int(request.POST["dect"])
            notes = str(request.POST["notes"])
            pw1 = str(request.POST["password"])
            pw2 = str(request.POST["confirm_password"])
            mail = str(request.POST["email"])
            rights = int(request.POST["rights"])
            if not check_password_conformity(pw1, pw2):
                recreate_form('password mismatch')
            auth_user: User = User.objects.create_user(username=username, email=mail, password=pw1)
            auth_user.save()
            user: Profile = Profile()
            user.rights = rights
            user.number_of_allowed_reservations = int(request.POST["allowed_reservations"])
            user.displayName = displayname
            user.authuser = auth_user
            user.dect = dect
            user.notes = notes
            user.active = True
            user.save()
            pass
        pass
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return redirect(forward_url)
