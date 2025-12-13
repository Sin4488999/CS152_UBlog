# path: main_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.urls import reverse


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.CharField(default='This user is too lazy to write anything!', max_length=1000, blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.get_full_name()}'


class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    author = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='posts')
    published_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title

    @property
    def score(self):
        """Calculate score as upvotes minus downvotes"""
        # Use count() to avoid loading all objects into memory
        likes_count = self.like_set.count()
        downvotes_count = self.downvote_set.count()
        return likes_count - downvotes_count

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('postdetailview', kwargs={'pk': self.pk})


class Like(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"

    # Removed save() and delete() methods - we calculate score dynamically


class Downvote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} downvoted {self.post.title}"

    # Removed save() and delete() methods - we calculate score dynamically


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    like_count = models.IntegerField(default=0, blank=True)
    downvote_count = models.IntegerField(default=0, blank=True)
    content = models.CharField(max_length=2000)
    published_date = models.DateTimeField(default=timezone.now, blank=True)
    modified_date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.post.title}: {self.content[:40]}"

    def save(self, *args, **kwargs):
        self.modified_date = timezone.now()
        super().save(*args, **kwargs)

    def update_like_count(self):
        self.like_count = CommentLike.objects.filter(comment=self).count()
        self.save(update_fields=['like_count'])

    def update_downvote_count(self):
        self.downvote_count = CommentDownvote.objects.filter(comment=self).count()
        self.save(update_fields=['downvote_count'])

    @property
    def score(self) -> int:
        return int(self.like_count) - int(self.downvote_count)


class CommentLike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'comment')
        indexes = [
            models.Index(fields=['comment', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.comment.update_like_count()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.comment.update_like_count()


class CommentDownvote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'comment')
        indexes = [
            models.Index(fields=['comment', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} downvoted comment {self.comment.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.comment.update_downvote_count()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.comment.update_downvote_count()