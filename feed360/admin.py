
from django.contrib import admin
from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse, FeedbackAggregate

try:
	from .models import Subject
	admin.site.register(Subject)
except ImportError:
	pass

admin.site.register(FeedbackForm)
admin.site.register(FeedbackQuestion)
admin.site.register(FeedbackResponse)
admin.site.register(FeedbackAggregate)
