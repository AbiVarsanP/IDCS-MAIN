from django import forms

class ResumeUploadForm(forms.Form):
	file = forms.FileField(label='Upload Resume',
		help_text='Accepted formats: PDF, DOCX, TXT')

	def clean_file(self):
		file = self.cleaned_data['file']
		valid_mime_types = [
			'application/pdf',
			'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'text/plain'
		]
		valid_extensions = ['pdf', 'docx', 'txt']
		ext = file.name.split('.')[-1].lower()
		if ext not in valid_extensions:
			raise forms.ValidationError('Unsupported file extension.')
		if hasattr(file, 'content_type') and file.content_type not in valid_mime_types:
			raise forms.ValidationError('Unsupported file type.')
		return file
