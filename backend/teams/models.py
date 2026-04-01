from django.db import models
import secrets


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    invite_code = models.CharField(max_length=20, unique=True, blank=True)
    # captain uses string ref to users.CTFUser — only one direction of real FK
    captain = models.ForeignKey(
        'users.CTFUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='captained_teams'
    )
    max_members = models.PositiveIntegerField(default=5)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = secrets.token_urlsafe(12)
        super().save(*args, **kwargs)

    @property
    def members(self):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.filter(team_id_ref=self.pk)

    def get_score(self):
        return sum(m.get_score() for m in self.members)

    def get_member_count(self):
        return self.members.count()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
