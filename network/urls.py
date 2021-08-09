from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("all_posts", views.allPosts, name="allPosts"),
    path("create_post", views.createPost, name="createPost"),
    path("edit_post/<int:postId>", views.editPost, name="editPost"),
    path("following", views.following, name="following"),
    path("follow_toggle/<int:target_user_id>", views.followToggle, name="followToggle"),
    path("likes_toggle", views.likesToggle, name="likesToggle"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("profile/<int:target_user>", views.profile, name="profile"),
    path("register", views.register, name="register")
]
