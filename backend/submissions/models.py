from django.db import models


class Submission(models.Model):
    user = models.ForeignKey('users.CTFUser', on_delete=models.CASCADE, related_name='submissions')
    challenge = models.ForeignKey('challenges.Challenge', on_delete=models.CASCADE, related_name='submissions')
    flag = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.user} -> {self.challenge}"
