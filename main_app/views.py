# path: main_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Exists, OuterRef, Value, BooleanField, Count, F
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator

from .forms import UserRegisterForm, PostForm, ProfileUpdateForm
from .models import (
    Post,
    Like,
    Comment,
    CustomUser,
    CommentLike,
    Downvote,
    CommentDownvote,
)

from .tokens import email_verification_token


# -------------------------------------------------------------------
# Themed HTML email builder (kept simple for email client support)
# -------------------------------------------------------------------
def _build_html_email(title: str, intro: str, button_text: str, button_url: str) -> str:
    primary = "#00c5ff"
    bg = "#f8f9fa"
    text = "#111827"
    card = "#ffffff"
    border = "#e0e0e0"
    return f"""
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:{bg};font-family:Inter,Segoe UI,Roboto,Arial,sans-serif;color:{text};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellpadding="0" cellspacing="0"
                 style="background:{card};border:1px solid {border};border-radius:12px;padding:24px">
            <tr><td align="center" style="font-weight:800;font-size:22px;letter-spacing:.02em;padding-bottom:8px">UBlog</td></tr>
            <tr><td style="font-size:18px;font-weight:700;padding-bottom:8px">{title}</td></tr>
            <tr><td style="font-size:15px;line-height:1.6;padding-bottom:18px">{intro}</td></tr>
            <tr>
              <td align="center" style="padding-bottom:18px">
                <a href="{button_url}"
                   style="display:inline-block;background:{primary};color:#ffffff;text-decoration:none;
                          padding:10px 16px;border-radius:8px;font-weight:700;">{button_text}</a>
              </td>
            </tr>
            <tr><td style="font-size:12px;color:#475569">If the button doesn't work, copy and paste this link:<br>
              <span style="word-break:break-all">{button_url}</span></td></tr>
          </table>
          <div style="font-size:12px;color:#6b7280;margin-top:10px">© {__import__('datetime').datetime.utcnow().year} UBlog</div>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()


# -------------------------------------------------------------------
# Email helpers
# -------------------------------------------------------------------
def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse("verify_email", kwargs={"uidb64": uid, "token": token})
    )
    subject = "Verify your UBlog email"
    text = (
        f"Hi {user.username},\n\n"
        "Please verify your email address by clicking the link below:\n"
        f"{verify_url}\n\n"
        "This link expires in 15 minutes."
    )
    html = _build_html_email(
        title="Verify your email",
        intro=f"Hi <b>{user.username}</b>, confirm your email to activate your account. "
              "This link expires in <b>15 minutes</b>.",
        button_text="Verify email",
        button_url=verify_url,
    )
    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html)


def send_password_reset_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = request.build_absolute_uri(
        reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    )
    subject = "Reset your UBlog password"
    text = (
        f"Hi {user.username},\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_url}\n\n"
        "This link expires in 15 minutes."
    )
    html = _build_html_email(
        title="Reset your password",
        intro=f"Hi <b>{user.username}</b>, click the button below to set a new password. "
              "The link expires in <b>15 minutes</b>.",
        button_text="Change password",
        button_url=reset_url,
    )
    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html)


# -------------------------------------------------------------------
# Landing / Auth
# -------------------------------------------------------------------
def homeview(request):
    if request.user.is_authenticated:
        return redirect("postlistview")
    return render(request, "main_app/landing.html")


def loginview(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')
        user = None
        if identifier and password:
            try:
                if '@' in identifier:
                    user_obj = CustomUser.objects.get(email__iexact=identifier)
                else:
                    user_obj = CustomUser.objects.get(username__iexact=identifier)
                user = authenticate(request, username=user_obj.email, password=password)
            except CustomUser.DoesNotExist:
                user = None
        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is not active yet. Please verify your email before logging in.")
            else:
                login(request, user)
                return redirect('homeview')
        else:
            messages.error(request, "Invalid email/username or password.")
    return render(request, 'main_app/login.html', context={})


def logoutview(request):
    logout(request)
    return redirect('loginview')


def signupview(request):
    form = UserRegisterForm()
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                send_verification_email(request, user)
                messages.success(request, "Account created! Check your email to verify your address before logging in.")
            except Exception:
                messages.error(request, "Account created, but we could not send a verification email.")
            return redirect('loginview')
        else:
            for _field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return render(request, 'main_app/signup.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()
            messages.success(request, "Your email has been verified. You can now log in.")
        else:
            messages.info(request, "Your email is already verified. You can log in.")
        return redirect('loginview')
    messages.error(request, "The verification link is invalid or has expired.")
    return redirect('signupview')


def resend_verification_request(request):
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        if not identifier:
            messages.error(request, "Enter your email or username.")
            return redirect("resend_verification")
        if "@" in identifier:
            user = CustomUser.objects.filter(email__iexact=identifier).first()
        else:
            user = CustomUser.objects.filter(username__iexact=identifier).first()
        if not user:
            messages.info(request, "If an account exists, a verification link has been sent.")
            return redirect("loginview")
        if user.is_active:
            messages.info(request, "Your email is already verified. You can log in.")
            return redirect("loginview")
        try:
            send_verification_email(request, user)
            messages.success(request, "Verification email sent. Please check your inbox.")
        except Exception:
            messages.error(request, "Could not send the verification email. Please try again later.")
        return redirect("loginview")
    initial_identifier = (request.GET.get("identifier") or "").strip()
    return render(request, "main_app/resend_verification.html", {"prefill_identifier": initial_identifier})


# -------------------------------------------------------------------
# Password reset (15-minute tokens)
# -------------------------------------------------------------------
def password_reset_request(request):
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        if not identifier:
            messages.error(request, "Enter your email or username.")
            return redirect("password_reset_request")
        if "@" in identifier:
            user = CustomUser.objects.filter(email__iexact=identifier).first()
        else:
            user = CustomUser.objects.filter(username__iexact=identifier).first()
        if not user:
            messages.info(request, "If an account exists, a reset link has been sent.")
            return redirect("loginview")
        if not user.is_active:
            messages.error(request, "Your account isn't active yet. Verify your email first.")
            return redirect("resend_verification")
        try:
            send_password_reset_email(request, user)
            messages.success(request, "We've sent a password reset link. It expires in 15 minutes.")
        except Exception:
            messages.error(request, "Could not send the reset email. Please try again later.")
        return redirect("loginview")
    return render(request, "main_app/password_reset_request.html", {})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect("password_reset_request")

    if request.method == "POST":
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""
        if p1 != p2:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                validate_password(p2, user=user)
                user.set_password(p2)
                user.save()
                messages.success(request, "Your password has been reset. You can now log in.")
                return redirect("loginview")
            except Exception as e:
                messages.error(request, str(e))
    return render(request, "main_app/password_reset_confirm.html", {"uidb64": uidb64, "token": token})


# -------------------------------------------------------------------
# Profile
# -------------------------------------------------------------------
@login_required
def profile_view(request, pk):
    custom_user = CustomUser.objects.get(id=pk)
    post_count = Post.objects.filter(author=custom_user).count()
    like_count = Like.objects.filter(user=custom_user).count()
    comment_count = Comment.objects.filter(user=custom_user).count()
    context = {
        'custom_user': custom_user,
        'post_count': post_count,
        'like_count': like_count,
        'comment_count': comment_count,
    }
    return render(request, 'main_app/profile.html', context=context)


@login_required
def update_profile(request, pk):
    if pk != request.user.id:
        return render(request, 'main_app/error.html')
    cur_user_profile = {
        'bio': request.user.profile.bio,
        'linkedin_link': getattr(request.user.profile, 'linkedin_link', ''),
    }
    if request.method == "POST":
        profile_update_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_update_form.is_valid():
            profile = profile_update_form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile updated successfully")
            return redirect('profileview', pk=request.user.id)
    else:
        profile_update_form = ProfileUpdateForm(initial=cur_user_profile)
    return render(request, 'main_app/update.html', {'profile_update_form': profile_update_form})


# -------------------------------------------------------------------
# Blog views with optimized score calculation
# -------------------------------------------------------------------
class PostListView(ListView):
    context_object_name = 'posts'
    model = Post
    template_name = 'main_app/postlist.html'
    ordering = ['-published_date']

    def get_queryset(self):
        qs = super().get_queryset().select_related('author')

        # Annotate with calculated score (likes - downvotes)
        # Use 'vote_score' to avoid conflict with Post.score property
        qs = qs.annotate(
            vote_score=Count('like', distinct=True) - Count('downvote', distinct=True)
        )

        user = self.request.user
        if user.is_authenticated:
            liked_subq = Like.objects.filter(post=OuterRef('pk'), user=user)
            downvoted_subq = Downvote.objects.filter(post=OuterRef('pk'), user=user)
            return qs.annotate(
                user_liked=Exists(liked_subq),
                user_downvoted=Exists(downvoted_subq),
            )
        return qs.annotate(
            user_liked=Value(False, output_field=BooleanField()),
            user_downvoted=Value(False, output_field=BooleanField()),
        )


class PostDetailView(LoginRequiredMixin, DetailView):
    context_object_name = 'post'
    model = Post
    template_name = 'main_app/postdetail.html'

    def get_object(self, queryset=None):
        # Get the post and annotate with user vote status
        post = super().get_object(queryset)

        # Add user_liked and user_downvoted as attributes
        user = self.request.user
        if user.is_authenticated:
            post.user_liked = Like.objects.filter(post=post, user=user).exists()
            post.user_downvoted = Downvote.objects.filter(post=post, user=user).exists()
        else:
            post.user_liked = False
            post.user_downvoted = False

        return post

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        user = self.request.user

        # Calculate score efficiently
        likes = Like.objects.filter(post=post).count()
        downvotes = Downvote.objects.filter(post=post).count()
        ctx['score'] = likes - downvotes

        # Annotate comments with user vote status
        if user.is_authenticated:
            comments = post.comments.select_related('user').prefetch_related('children')
            for comment in comments:
                comment.user_liked = CommentLike.objects.filter(comment=comment, user=user).exists()
                comment.user_downvoted = CommentDownvote.objects.filter(comment=comment, user=user).exists()

        return ctx


class AddPostView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'main_app/addpost.html'
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UpdatePostView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'main_app/addpost.html'
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return bool(self.request.user == post.author)


class DeletePostView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'main_app/deletepost.html'
    context_object_name = 'post'
    success_url = "/blog"

    def test_func(self):
        post = self.get_object()
        return bool(self.request.user == post.author)


def search(request):
    query = (request.GET.get('q') or "").strip()
    results = Post.objects.none()
    if query:
        base = (
            Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query))
            .select_related('author')
            .order_by('-published_date')
        )

        # Annotate with calculated score
        # Use 'vote_score' to avoid conflict with Post.score property
        base = base.annotate(
            vote_score=Count('like', distinct=True) - Count('downvote', distinct=True)
        )

        user = request.user
        if user.is_authenticated:
            liked_subq = Like.objects.filter(post=OuterRef('pk'), user=user)
            downvoted_subq = Downvote.objects.filter(post=OuterRef('pk'), user=user)
            results = base.annotate(
                user_liked=Exists(liked_subq),
                user_downvoted=Exists(downvoted_subq),
            )
        else:
            results = base.annotate(
                user_liked=Value(False, output_field=BooleanField()),
                user_downvoted=Value(False, output_field=BooleanField()),
            )
    return render(request, 'main_app/search.html', {'results': results, 'query': query})


# -------------------------------------------------------------------
# ATOMIC Likes / comments with safe 'next' redirect
# -------------------------------------------------------------------
@login_required
@transaction.atomic
def add_comment_like(request, pk):
    """
    Atomic voting and commenting operations
    """

    def _redirect_default():
        return redirect('postdetailview', pk=pk)

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = None

    if request.method == 'POST':
        if 'comment_button' in request.POST:
            # Lock the post row for update
            post = Post.objects.select_for_update().get(id=pk)
            parent_id = request.POST.get('parent_id')
            parent = get_object_or_404(Comment, id=parent_id, post=post) if parent_id else None
            comment_text = (request.POST.get('comment_text') or '').strip()
            if comment_text:
                Comment.objects.create(post=post, user=request.user, content=comment_text, parent=parent)
                messages.success(request, "Comment added")
            else:
                messages.error(request, "Please write something before posting.")

        elif 'like_button' in request.POST:
            # Lock the post row to prevent race conditions
            post_obj = Post.objects.select_for_update().get(id=pk)

            # Remove any downvote first (atomic)
            Downvote.objects.filter(post=post_obj, user=request.user).delete()

            # Toggle like
            like_obj = Like.objects.filter(post=post_obj, user=request.user).first()
            if like_obj:
                like_obj.delete()
            else:
                Like.objects.create(post=post_obj, user=request.user)

        elif 'downvote_button' in request.POST:
            # Lock the post row to prevent race conditions
            post_obj = Post.objects.select_for_update().get(id=pk)

            # Remove any like first (atomic)
            Like.objects.filter(post=post_obj, user=request.user).delete()

            # Toggle downvote
            dv = Downvote.objects.filter(post=post_obj, user=request.user).first()
            if dv:
                dv.delete()
            else:
                Downvote.objects.create(post=post_obj, user=request.user)

        elif 'comment_like' in request.POST:
            c_id = request.POST.get('comment_id')
            if c_id:
                # Lock the comment row
                comment = Comment.objects.select_for_update().get(id=c_id, post_id=pk)

                # Remove any downvote first (atomic)
                CommentDownvote.objects.filter(comment=comment, user=request.user).delete()

                # Toggle like
                cl = CommentLike.objects.filter(comment=comment, user=request.user).first()
                if cl:
                    cl.delete()
                else:
                    CommentLike.objects.create(comment=comment, user=request.user)

        elif 'comment_downvote' in request.POST:
            c_id = request.POST.get('comment_id')
            if c_id:
                # Lock the comment row
                comment = Comment.objects.select_for_update().get(id=c_id, post_id=pk)

                # Remove any like first (atomic)
                CommentLike.objects.filter(comment=comment, user=request.user).delete()

                # Toggle downvote
                cd = CommentDownvote.objects.filter(comment=comment, user=request.user).first()
                if cd:
                    cd.delete()
                else:
                    CommentDownvote.objects.create(comment=comment, user=request.user)

    return redirect(next_url) if next_url else _redirect_default()