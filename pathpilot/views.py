
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import PathPilotMap
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
from .utils import generate_course_plan
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
import pdfplumber
import docx

# AJAX endpoint to save a map to history
@require_POST
@login_required
def save_map(request):
	try:
		import logging
		logger = logging.getLogger('pathpilot')
		data = json.loads(request.body.decode('utf-8'))
		title = data.get('title') or 'PathPilot Map'
		plan = data.get('plan')
		role = data.get('role', '')
		# For staff, merge all chunks from session
		session_key = 'pathpilot_last_plan'
		if role == 'Staff' and session_key in request.session:
			try:
				session_plan = json.loads(request.session[session_key])
			except Exception:
				session_plan = {}
			# Merge session_plan and incoming plan
			if isinstance(plan, dict):
				session_plan.update(plan)
			plan = session_plan
		if not plan or not isinstance(plan, dict) or len(plan) == 0:
			logger.warning(f"Attempted to save empty map for user {request.user}")
			return JsonResponse({'success': False, 'error': 'Map is empty.'})
		plan_json_str = json.dumps(plan)
		logger.info(f"Saving map for user {request.user}: title={title}, role={role}, plan_json={plan_json_str[:200]}")
		PathPilotMap.objects.create(
			user=request.user,
			role=role,
			title=title,
			plan_json=plan_json_str
		)
		return JsonResponse({'success': True})
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)})

@login_required
def map_history(request):
	maps = PathPilotMap.objects.filter(user=request.user).order_by('-created_at')
	return render(request, 'pathpilot/map_history.html', {'maps': maps})


def cp(request):
	"""Render the Path Pilot form page. Handles PDF download if requested."""
	# If ?download=pdf, generate PDF from last plan in session
	if request.GET.get('download') == 'pdf':
		plan = request.session.get('pathpilot_last_plan')
		if not plan:
			return HttpResponse('No plan to download.', status=400)
		try:
			plan = json.loads(plan) if isinstance(plan, str) else plan
		except Exception:
			return HttpResponse('Invalid plan data.', status=400)
		# Generate PDF
		buffer = BytesIO()
		p = canvas.Canvas(buffer, pagesize=letter)
		width, height = letter
		y = height - 40
		p.setFont('Helvetica-Bold', 16)
		p.drawString(40, y, 'Path Pilot Roadmap')
		y -= 30
		p.setFont('Helvetica', 12)
		step_num = 1
		for _, details in plan.items():
			step_label = f"Step {step_num}"
			if y < 80:
				p.showPage()
				y = height - 40
				p.setFont('Helvetica', 12)
			p.setFont('Helvetica-Bold', 13)
			p.drawString(40, y, step_label)
			y -= 18
			p.setFont('Helvetica', 12)
			p.drawString(60, y, f"Topic: {details.get('Topic','')}")
			y -= 16
			p.drawString(60, y, f"Periods: {details.get('Periods','-')}")
			y -= 16
			p.drawString(60, y, f"Hints: {details.get('Hints','-')}")
			y -= 16
			p.drawString(60, y, f"Resources: {details.get('Resources','-')}")
			y -= 24
			step_num += 1
		p.save()
		buffer.seek(0)
		response = HttpResponse(buffer, content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename="pathpilot_roadmap.pdf"'
		return response
	return render(request, 'pathpilot/cp.html')

@csrf_exempt
def course_map(request):
	"""AJAX endpoint: Generate course/career map using Perplexity AI."""
	if request.method != 'POST':
		return JsonResponse({'error': 'Invalid request method.'}, status=405)
	try:
		data = json.loads(request.body.decode('utf-8'))
		role = data.get('role')
		if role == 'Student':
			branch = data.get('branch')
			year = data.get('year')
			degree = data.get('degree')
			skills = data.get('skills')
			career_goal = data.get('career_goal')
			if not all([branch, year, degree, skills, career_goal]):
				return JsonResponse({'error': 'Please fill all required fields.'}, status=400)
		else:
			branch = data.get('branch')
			subject = data.get('subject')
			syllabus = data.get('syllabus')
			total_periods = data.get('total_periods')
			duration = data.get('duration')
			if not all([branch, subject, syllabus, total_periods, duration]):
				return JsonResponse({'error': 'Please fill all required fields.'}, status=400)
			try:
				total_periods = int(total_periods)
				duration = int(duration)
				if total_periods < 1 or duration < 1:
					return JsonResponse({'error': 'Periods and duration must be positive numbers.'}, status=400)
			except Exception:
				return JsonResponse({'error': 'Periods and duration must be numbers.'}, status=400)
			# If syllabus is base64 (PDF or DOCX), extract text
			if syllabus and syllabus.startswith('data:'):
				try:
					header, b64data = syllabus.split(',', 1)
					if 'pdf' in header:
						pdf_bytes = base64.b64decode(b64data)
						with open('temp_syllabus.pdf', 'wb') as f:
							f.write(pdf_bytes)
						with pdfplumber.open('temp_syllabus.pdf') as pdf:
							text = ''
							for page in pdf.pages:
								text += page.extract_text() or ''
						syllabus = text.strip() or 'No text extracted from PDF.'
					elif 'doc' in header:
						docx_bytes = base64.b64decode(b64data)
						with open('temp_syllabus.docx', 'wb') as f:
							f.write(docx_bytes)
						doc = docx.Document('temp_syllabus.docx')
						text = '\n'.join([p.text for p in doc.paragraphs])
						syllabus = text.strip() or 'No text extracted from DOCX.'
					else:
						syllabus = 'Unsupported file type.'
					data['syllabus'] = syllabus
				except Exception as ex:
					return JsonResponse({'error': 'Failed to extract text from uploaded file.'}, status=400)
			else:
				data['syllabus'] = syllabus

		# Call utility to generate plan
		import logging
		logger = logging.getLogger('pathpilot')
		try:
			session_key = 'pathpilot_last_plan'
			if role == 'Staff':
				total_periods = int(data.get('total_periods'))
				start = int(data.get('start', 1))
				end = int(data.get('end', min(10, total_periods)))
				plan = generate_course_plan(data, start=start, end=end)
				if not plan:
					return JsonResponse({'error': 'Unable to generate roadmap right now. Please try again later.'}, status=500)
				step_plan = {}
				for idx, (k, v) in enumerate(plan.items(), start):
					step_plan[f'Period {idx}'] = v
				# Save/append to session
				if session_key in request.session:
					try:
						existing = json.loads(request.session[session_key])
					except Exception:
						existing = {}
					existing.update(step_plan)
					request.session[session_key] = json.dumps(existing)
				else:
					request.session[session_key] = json.dumps(step_plan)
				has_more = end < total_periods
				next_start = end + 1
				next_end = min(end + 10, total_periods)
				return JsonResponse({'plan': step_plan, 'has_more': has_more, 'next_start': next_start, 'next_end': next_end})
			else:
				# Student batching logic
				max_steps = int(data.get('max_steps', 10))
				start = int(data.get('start', 1))
				end = int(data.get('end', start + max_steps - 1))
				plan = generate_course_plan(data, start=start, end=end)
				if not plan:
					return JsonResponse({'error': 'Unable to generate roadmap right now. Please try again later.'}, status=500)
				step_plan = {}
				for idx, (k, v) in enumerate(plan.items(), start):
					step_plan[f'Step {idx}'] = v
				# Save/append to session
				if session_key in request.session:
					try:
						existing = json.loads(request.session[session_key])
					except Exception:
						existing = {}
					existing.update(step_plan)
					request.session[session_key] = json.dumps(existing)
				else:
					request.session[session_key] = json.dumps(step_plan)
				# Determine has_more for students
				has_more = len(step_plan) == max_steps
				next_start = end + 1
				next_end = end + max_steps
				return JsonResponse({'plan': step_plan, 'has_more': has_more, 'next_start': next_start, 'next_end': next_end})
		except json.JSONDecodeError as jde:
			logger.error(f"JSON decode error in course_map: {jde}")
			return JsonResponse({'error': 'Roadmap generation failed due to invalid response format. Please try again or reduce the number of periods.'}, status=400)
		except Exception as e:
			logger.error(f"Error in course_map: {e}")
			return JsonResponse({'error': 'Unable to generate roadmap right now. Please try again later.'}, status=500)
	except Exception as e:
		return JsonResponse({'error': 'Unable to generate roadmap right now. Please try again later.'}, status=500)
@login_required
def map_detail(request, map_id):
	import logging
	logger = logging.getLogger('pathpilot')
	try:
		map_obj = PathPilotMap.objects.get(id=map_id, user=request.user)
	except PathPilotMap.DoesNotExist:
		logger.warning(f"Map not found or access denied for user {request.user}, map_id={map_id}")
		return HttpResponse('Map not found or access denied.', status=404)
	# Parse plan_json if it's a string
	plan = map_obj.plan_json
	if isinstance(plan, str):
		try:
			plan = json.loads(plan)
		except Exception as e:
			logger.error(f"Failed to parse plan_json for map_id={map_id}: {e}")
			plan = {}
	else:
		plan = plan or {}
	logger.info(f"Rendering map detail for user {request.user}, map_id={map_id}, plan_keys={list(plan.keys())}")
	return render(request, 'pathpilot/map_detail.html', {'map': map_obj, 'plan': plan})
