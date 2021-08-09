from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


from django import forms
from .models import User, Post, Follow, Like
import datetime
import json

class PostForm(forms.Form):
    postBody = forms.CharField(label="",widget=forms.Textarea(attrs={'class': 'form-control col-md-6 col-lg-6', 'rows': 3}))

def allPosts(request):
    original_posts = Post.objects.all().values()
    ready_posts = setupPosts(original_posts, request.user)
    page = request.GET.get("page", 1)
    paginator = Paginator(ready_posts, 10)
    posts = paginator.page(page)

    return render(request,"network/all_posts.html", {"postForm": PostForm(), "posts": posts})


def createPost(request):
    form = PostForm(request.POST)

    if form.is_valid():
        postBody = form.cleaned_data["postBody"]
        Post(user=request.user, postBody=postBody, date=datetime.datetime.now(), likes=0).save()

        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request,"network/all_posts.html", {"form": PostForm()})


@csrf_exempt
@login_required
def editPost(request, postId):
    data = json.loads(request.body.decode("utf-8"))
    post = Post.objects.get(id=postId)
    post.postBody = data['postBody']
    post.save()

    return JsonResponse({"message": "Post updated."}, status=201)


def following(request):
    followed_users = Follow.objects.filter(follower=request.user).values()
    all_posts = Post.objects.all().values()
    original_posts = []

    for p in all_posts:
        for f in followed_users:
            if p["user_id"] == f["followed_id"]:
                original_posts.append(p)
    
    if not original_posts:
        return render(request,"network/following.html")
    else:
        ready_posts = setupPosts(original_posts, request.user)
        page = request.GET.get("page", 1)
        paginator = Paginator(ready_posts, 10)
        posts = paginator.page(page)

        return render(request,"network/following.html", {"posts": posts})


@csrf_exempt
@login_required
def followToggle(request, target_user_id):
    target_user = User.objects.get(id=target_user_id)
    following = Follow.objects.filter(followed=target_user_id, follower=request.user)

    if following:
        Follow.objects.filter(followed=target_user_id, follower=request.user).delete()
        followers = Follow.objects.filter(followed=target_user).count()
        follows = Follow.objects.filter(follower=target_user).count()

        return JsonResponse({
            "available_action": "Follow",
            "followers": followers,
            "follows": follows})
    else:
        Follow(followed=target_user, follower=request.user).save()
        followers = Follow.objects.filter(followed=target_user).count()
        follows = Follow.objects.filter(follower=target_user).count()

        return JsonResponse({
            "available_action": "Unfollow",
            "followers": followers,
            "follows": follows})


def index(request):
    return HttpResponseRedirect(reverse("allPosts"))


@csrf_exempt
@login_required
def likesToggle(request):
    data = json.loads(request.body.decode("utf-8"))
    like = Like.objects.filter(post=data['postId'], liker=data['likerId'])
    post = Post.objects.get(id=data['postId'])
    
    if (like):
        like.delete()
        post.likes -= 1
        post.save()

        return JsonResponse({"message": "doesn't like", "likes": post.likes}, status=201)
    else:
        liker = User.objects.get(id=data['likerId'])
        Like(post=post, liker=liker).save()
        post.likes += 1
        post.save()

        return JsonResponse({"message": "likes", "likes": post.likes}, status=201)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def profile(request, target_user):
    original_posts = Post.objects.filter(user=target_user).values()
    ready_posts = setupPosts(original_posts, request.user)
    page = request.GET.get("page", 1)
    paginator = Paginator(ready_posts, 10)
    posts = paginator.page(page)

    followers = Follow.objects.filter(followed=target_user).count()
    follows = Follow.objects.filter(follower=target_user).count()
    current_user_follows = Follow.objects.filter(followed=target_user, follower=request.user)
    
    return render(request,"network/profile.html", {"posts": posts, "followers": followers, "follows": follows, "current_user_follows": current_user_follows, "target_user": target_user})


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def setupPosts(original_posts, user):
    posts = []

    for p in original_posts:
        ready_post = {}
        ready_post["id"] = p["id"]
        ready_post["user_id"] = p["user_id"]
        ready_post["user"] = User.objects.get(id=p["user_id"])
        ready_post["postBody"] = p["postBody"]
        ready_post["date"] = p["date"]
        ready_post["likes"] = p["likes"]
        print(user)

        if (user.id != None):
            if (Like.objects.filter(post=p["id"], liker=user)):
                ready_post["liker"] = "yes"
            else:
                ready_post["liker"] = "no"

        posts.append(ready_post)
    
    posts.reverse()

    return(posts)