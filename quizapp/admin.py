from django.contrib import admin
from .models import Answer, Attempt, AttemptResponse, Question, Quiz

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Attempt)
admin.site.register(AttemptResponse)
