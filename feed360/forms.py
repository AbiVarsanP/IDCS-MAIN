
from django import forms
from django.forms import modelform_factory, inlineformset_factory
from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse, Subject

from core.constants import YEAR, SECTION


class FeedbackFormCreateForm(forms.ModelForm):
	answer_type = forms.ChoiceField(choices=[('stars', 'Stars'), ('text', 'Text'), ('both', 'Stars & Text')], label='Answer Type (common for all questions)')
	subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False, label='Subject (common for all questions)')
	subject_text = forms.CharField(max_length=100, required=False, label='Subject Text (if no subject)')

	def clean(self):
		cleaned_data = super().clean()
		# If department is missing, set it from initial (HOD's department)
		dept = cleaned_data.get('department')
		if not dept and self.fields['department'].initial:
			cleaned_data['department'] = self.fields['department'].initial
		return cleaned_data

	def save(self, commit=True):
		instance = super().save(commit=False)
		# Ensure department is set as string name
		dept = self.cleaned_data.get('department')
		if not dept and self.fields['department'].initial:
			dept = self.fields['department'].initial
		instance.department = str(dept) if dept else ''
		# Ensure year and section are stored as string (if needed)
		year = self.cleaned_data.get('year')
		section = self.cleaned_data.get('section')
		instance.year = int(year) if year else None
		instance.section = str(section) if section is not None else ''
		# Debug: print what is being saved
		import logging
		logger = logging.getLogger('django')
		logger.warning(f"Saving FeedbackForm: department={instance.department}, year={instance.year}, section={instance.section}")
		if commit:
			instance.save()
		return instance

	class Meta:
		model = FeedbackForm
		fields = ['title', 'year', 'section', 'active', 'department']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super().__init__(*args, **kwargs)
		# Set department as hidden and required False
		self.fields['department'].widget = forms.HiddenInput()
		self.fields['department'].required = False
		dept_name = None
		if user and hasattr(user, 'staff') and user.staff.department:
			dept_name = getattr(user.staff.department, 'name', None)
		if dept_name:
			self.fields['department'].initial = dept_name
			self.data = self.data.copy()
			if 'department' not in self.data or not self.data['department']:
				self.data['department'] = dept_name
		# Use dropdowns for year and section
		self.fields['year'].widget = forms.Select(choices=YEAR)
		self.fields['section'].widget = forms.Select(choices=SECTION)

# Inline formset for adding multiple questions to a FeedbackForm
FeedbackQuestionFormSet = inlineformset_factory(
	FeedbackForm,
	FeedbackQuestion,
	fields=['text'],  # Only question text is per-question
	extra=3,  # Show 3 question forms by default
	can_delete=True
)

# Server-side approach for adding multiple questions: use FeedbackQuestionFormSet in the view
# For JS dynamic addition, use a blank form template and clone rows client-side (see template comments in later steps)

class StudentFeedbackSubmissionForm(forms.Form):
	# This form will be built dynamically per question/subject in the view
	# Helper for validating star ratings
	def clean(self):
		cleaned_data = super().clean()
		# Example: validate that star ratings are present for 'stars' questions
		# Actual implementation will depend on dynamic form construction in the view
		return cleaned_data
