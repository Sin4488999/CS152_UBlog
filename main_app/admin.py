from django.contrib import admin

from .models import CustomUser, Post, Comment, Like, Profile
 
admin.site.register(CustomUser)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Profile)
