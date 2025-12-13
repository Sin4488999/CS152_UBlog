# main_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Landing / Auth
    path('', views.homeview, name='homeview'),
    path('login/', views.loginview, name='loginview'),
    path('logout/', views.logoutview, name='logoutview'),
    path('signup/', views.signupview, name='signupview'),

    # Verification
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_request, name='resend_verification'),

    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),

    # Blog
    path('blog/', views.PostListView.as_view(), name='postlistview'),
    path('blog/<int:pk>/', views.PostDetailView.as_view(), name='postdetailview'),
    path('blog/add-post/', views.AddPostView.as_view(), name='addpostview'),
    path('blog/<int:pk>/update/', views.UpdatePostView.as_view(), name='updatePostView'),
    path('blog/<int:pk>/delete/', views.DeletePostView.as_view(), name='deletePostView'),
    path('blog/<int:pk>/add_comment_like/', views.add_comment_like, name='add_comment_like'),

    # Profile
    path('profile/<int:pk>/', views.profile_view, name='profileview'),
    path('profile/<int:pk>/update/', views.update_profile, name='updateprofileview'),

    # Search
    path('search/', views.search, name='search'),
]
