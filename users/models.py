from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet

class CustomUser(AbstractUser):
    # We will only store essential data: email and nickname
    nickname = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    is_profile_public = models.BooleanField(default=False)
    def __str__(self):
        return self.nickname
# Generate a key for encryption (store this securely, such as in environment variables)
key = Fernet.generate_key()
cipher_suite = Fernet(key)
class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=30, unique=True)
    email = models.CharField(max_length=256, unique=True)
    def save(self, *args, **kwargs):
        # Encrypt the email before saving
        self.email = cipher_suite.encrypt(self.email.encode()).decode()
        super().save(*args, **kwargs)
                     


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)  # Safely create the profile without duplicating

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):  # Ensure profile exists before trying to save
        instance.profile.save()

def validate_unique_nickname(nickname, instance=None):
    if instance:
        # Exclude the current instance from the uniqueness check
        if Profile.objects.filter(nickname=nickname).exclude(pk=instance.pk).exists():
            raise ValidationError(f"Nickname '{nickname}' is already taken.")
    else:
        if Profile.objects.filter(nickname=nickname).exists():
            raise ValidationError(f"Nickname '{nickname}' is already taken.")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    nickname = models.CharField(max_length=30, unique=True, null=False, blank=False)
    max_spend = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)  # Max spend for each event
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)  # User's current balance

    def clean(self):
        validate_unique_nickname(self.nickname, instance=self)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)    

    def __str__(self):
        return self.user.username
    
class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    total_spend = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')  # Can be 'Pending' or 'Active'
    group = models.ForeignKey(Group, related_name='events', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='event_memberships', blank=True)  

    def calculate_share(self):
        members_count = self.group.members.count()
        if members_count == 0:
            return 0
        return self.total_spend / members_count

    def check_status(self):
        """ Check if all members' max spend can cover the event. """
        share = self.calculate_share()
        for member in self.group.members.all():
            if member.profile.max_spend < share:
                self.status = 'Pending'
                return False
        self.status = 'Active'
        return True