# resumebuilder/forms.py
from django import forms
from .models import Resume, Skill, Education, Achievement, Project, Social, Language

class ResumeForm(forms.ModelForm):
	class Meta:
		model = Resume
		fields = ['img', 'role', 'bio', 'template_id']

class SkillForm(forms.ModelForm):
	class Meta:
		model = Skill
		fields = ['name', 'level']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class EducationForm(forms.ModelForm):
	class Meta:
		model = Education
		fields = ['institution', 'degree', 'field', 'start_year', 'end_year']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class AchievementForm(forms.ModelForm):
	class Meta:
		model = Achievement
		fields = ['title', 'description', 'date']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['name', 'description', 'link']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class SocialForm(forms.ModelForm):
	class Meta:
		model = Social
		fields = ['platform', 'url']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class LanguageForm(forms.ModelForm):
	class Meta:
		model = Language
		fields = ['name', 'proficiency']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance
