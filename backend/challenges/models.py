from django.db import models
import math
import hashlib


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#ff1744')

    def __str__(self): return self.name
    class Meta: verbose_name_plural = 'Categories'


class Challenge(models.Model):
    DIFFICULTY = [('easy','Easy'),('medium','Medium'),('hard','Hard'),('insane','Insane')]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='challenges')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY)
    points = models.PositiveIntegerField(default=100)
    flag = models.CharField(max_length=500)
    hints = models.JSONField(default=list, blank=True)
    files = models.JSONField(default=list, blank=True)
    url = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_dynamic = models.BooleanField(default=False)
    max_points = models.PositiveIntegerField(default=500)
    min_points = models.PositiveIntegerField(default=100)
    decay = models.PositiveIntegerField(default=50)
    author = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_solve_count(self):
        from submissions.models import Submission
        return Submission.objects.filter(challenge=self, is_correct=True).count()

    def get_current_points(self):
        if not self.is_dynamic:
            return self.points
        n = self.get_solve_count()
        if n == 0:
            return self.max_points
        decay_factor = (self.max_points - self.min_points) / (self.decay ** 2)
        return max(int(self.max_points - decay_factor * (n ** 2)), self.min_points)
    
    def set_flag(self, raw_flag):
        self.flag = hashlib.sha256(raw_flag.encode()).hexdigest()

    def check_flag(self, submitted_flag):
        submitted = submitted_flag.strip()
        # Support plaintext flags stored directly via admin
        if self.flag == submitted:
            return True
        # Support hashed flags stored via set_flag()
        return hashlib.sha256(submitted.encode()).hexdigest() == self.flag

    def __str__(self): return f"[{self.category}] {self.title}"
    class Meta: ordering = ['category', 'points']


class Hint(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='hint_objects')
    text = models.TextField()
    cost = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['order']
    def __str__(self): return f"Hint {self.order} for {self.challenge.title}"


class HintUnlock(models.Model):
    user = models.ForeignKey('users.CTFUser', on_delete=models.CASCADE)
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ['user', 'hint']


class Event(models.Model):
    name = models.CharField(max_length=200, default='CTF Event')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    class Meta:
        verbose_name = 'CTF Event'
        verbose_name_plural = 'CTF Events'

