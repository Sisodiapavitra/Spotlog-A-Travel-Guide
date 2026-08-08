from django.shortcuts import render
from .models import Tweet, Follow
from .forms import TweetForm , UserRegistrationForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.models import Q

# Create your views here.

def index(request):
    return render(request, 'index.html')


def home(request):
    latest_tweets = Tweet.objects.all().order_by('-created_at')[:5]
    return render(request, 'home.html', {'latest_tweets': latest_tweets})


def tweet_list(request):
    tweets = Tweet.objects.all().order_by('-created_at')
    # Handle location search
    location = request.GET.get('location', '').strip()
    if location:
        tweets = tweets.filter(location_name__icontains=location)
    return render(request, 'tweet_list.html', {'tweets': tweets, 'search_location': location})

@login_required
def tweet_create(request):
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('tweet_list')
    else:
        form = TweetForm()
    return render(request, 'tweet_form.html', {'form':form})

@login_required
def tweet_edit(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('tweet_list')
    else:
        form = TweetForm(instance = tweet)
    return render(request, 'tweet_form.html', {'form':form})

@login_required
def tweet_delete(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id, user=request.user)
    if request.method == 'POST':
        tweet.delete()
        return redirect('tweet_list')
    return render(request, 'tweet_confirm_delete.html', {'tweet': tweet})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect('tweet_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html',{'form': form})


def user_profile(request, username):
    """Display a user's profile page with their tweets grouped by category"""
    profile_user = get_object_or_404(User, username=username)
    user_tweets = Tweet.objects.filter(user=profile_user).order_by('-created_at')
    
    # Group tweets by category
    categories = {
        'Food': user_tweets.filter(travel_category='Food'),
        'Budget': user_tweets.filter(travel_category='Budget'),
        'Hidden Gem': user_tweets.filter(travel_category='Hidden Gem'),
        'Accommodation': user_tweets.filter(travel_category='Accommodation'),
        'Others': user_tweets.filter(Q(travel_category__isnull=True) | Q(travel_category='')),
    }
    
    # Remove empty categories but keep count of total
    categories = {k: v for k, v in categories.items() if v.exists()}
    
    # Check if current user is following this profile user
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    # Get follower and following counts
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    
    context = {
        'profile_user': profile_user,
        'user_tweets': user_tweets,
        'tweet_count': user_tweets.count(),
        'categories': categories,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'profile.html', context)


def search_users(request):
    """Search for users by username"""
    query = request.GET.get('q', '').strip()
    users = []
    
    if query:
        users = User.objects.filter(username__icontains=query)
    
    return render(request, 'search_users.html', {'users': users, 'query': query})


@login_required
def follow_user(request, username):
    """Follow a user"""
    user_to_follow = get_object_or_404(User, username=username)
    
    # Prevent users from following themselves
    if request.user == user_to_follow:
        return redirect('user_profile', username=username)
    
    # Create follow relationship if it doesn't exist
    Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    
    return redirect('user_profile', username=username)


@login_required
def unfollow_user(request, username):
    """Unfollow a user"""
    user_to_unfollow = get_object_or_404(User, username=username)
    
    # Delete follow relationship
    Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
    
    return redirect('user_profile', username=username)


@login_required
def edit_profile(request):
    """Edit user profile"""
    from .forms import UserProfileForm
    
    try:
        user_profile = request.user.profile
    except:
        from .models import UserProfile
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            
            # Update User model fields
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            
            user_profile.save()
            return redirect('user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=user_profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    
    return render(request, 'edit_profile.html', {'form': form})