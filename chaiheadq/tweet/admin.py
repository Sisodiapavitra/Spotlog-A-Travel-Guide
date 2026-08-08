from django.contrib import admin
from .models import Tweet, UserProfile, Follow
# Register your models here.


admin.site.register(Tweet)
admin.site.register(UserProfile)
admin.site.register(Follow)