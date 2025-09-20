
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import ResumeUploadForm
from .models import UploadedResume, ResumeAnalysis
from .services.parser import extract_text, analyze_resume
from core.models import Student

# Loading page for resume analysis
@login_required
@ensure_csrf_cookie
def resume_loading(request, resume_id):
    resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
    # The URL to redirect to after loading (analysis result)
    analysis_url = reverse('ATS:resume_analysis', args=[resume.id])
    return render(request, 'ATS/resume_loading.html', {
        'resume': resume,
        'analysis_url': analysis_url,
    })


@login_required
def ats_dashboard(request):
	user = request.user
	if user.is_staff:
		return render(request, 'ATS/ats_dashboard.html', {'error': 'Only students can access the dashboard.'})

	try:
		student = Student.objects.get(user=user)
	except Student.DoesNotExist:
		return render(request, 'ATS/ats_dashboard.html', {'error': 'Only students can access the dashboard.'})

	resumes = UploadedResume.objects.filter(student=student).order_by('-uploaded_at')
	resume_data = []
	for resume in resumes:
		analysis_obj = ResumeAnalysis.objects.filter(resume=resume).order_by('-created_at').first()
		ats_score = None
		if analysis_obj:
			ats_score = analysis_obj.results.get('overall', {}).get('ats')
		resume_data.append({
			'resume': resume,
			'ats_score': ats_score,
		})

	return render(request, 'ATS/ats_dashboard.html', {
		'resume_data': resume_data,
	})

@login_required
def upload_resume(request):
	user = request.user
	try:
		student = Student.objects.get(user=user)
	except Student.DoesNotExist:
		return render(request, 'ATS/upload_resume.html', {'form': None, 'error': 'Only students can upload resumes.'})

	if request.method == 'POST':
		form = ResumeUploadForm(request.POST, request.FILES)
		if form.is_valid():
			file = form.cleaned_data['file']
			text = extract_text(file)
			resume = UploadedResume.objects.create(
				student=student,
				file=file,
				extracted_text=text
			)
			return redirect('ATS:resume_preview', resume_id=resume.id)
	else:
		form = ResumeUploadForm()
	return render(request, 'ATS/upload_resume.html', {'form': form})

@login_required
def resume_preview(request, resume_id):
	resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
	return render(request, 'ATS/resume_preview.html', {'resume': resume})




@login_required
def resume_analysis(request, resume_id):
	resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
	# Only allow students (not staff)
	if request.user.is_staff:
		return render(request, 'ATS/resume_analysis.html', {'resume': resume, 'error': 'Only students can access analysis.'})

	# Check for cached analysis
	analysis_obj = ResumeAnalysis.objects.filter(resume=resume).order_by('-created_at').first()
	if analysis_obj:
		analysis = analysis_obj.results
	else:
		analysis = analyze_resume(resume.extracted_text)
		ResumeAnalysis.objects.create(resume=resume, results=analysis)

	# For new section-based analysis
	sections = analysis.get('sections', {})
	# Fix: get overall score from any nonzero section, else 0
	section_scores = [s.get('section_score', 0) for s in sections.values() if isinstance(s, dict)]
	overall_score = int(sum(section_scores) / len(section_scores)) if section_scores else 0
	overall = {'score': overall_score}

	# Only show lines that need improvement (clarity, impact, or ats < 7)
	lines_to_improve = []
	for section, data in sections.items():
		for line in data.get('lines', []):
			if (
				line.get('clarity_score', 10) < 7 or
				line.get('impact_score', 10) < 7 or
				line.get('ats_compatibility', 10) < 7
			):
				lines_to_improve.append({
					'section': section,
					'original': line.get('original', ''),
					'suggestion': line.get('suggestion', ''),
					'clarity_score': line.get('clarity_score', 0),
					'impact_score': line.get('impact_score', 0),
					'ats_compatibility': line.get('ats_compatibility', 0),
					'missing_keywords': line.get('missing_keywords', None),
				})

	return render(request, 'ATS/resume_analysis.html', {
		'resume': resume,
		'analysis': analysis,
		'sections': sections,
		'overall': overall,
		'lines_to_improve': lines_to_improve,
		'resume_text': resume.extracted_text,
	})
