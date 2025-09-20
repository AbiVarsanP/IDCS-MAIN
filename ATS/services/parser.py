
import io
import pdfplumber
import docx
import re
from .analyzer import call_ai_api

def extract_text(file):
	name = file.name.lower()
	if name.endswith('.pdf'):
		with pdfplumber.open(file) as pdf:
			text = ''
			for page in pdf.pages:
				text += page.extract_text() or ''
		return text
	elif name.endswith('.docx'):
		doc = docx.Document(file)
		return '\n'.join([p.text for p in doc.paragraphs])
	elif name.endswith('.txt'):
		return file.read().decode('utf-8')
	else:
		return ''


# Modular AI line analysis

# Modular AI section analysis


def ai_analyze_section(section_name, section_text, target_role=None):
	if not section_text.strip():
		return None
	lines = [l for l in section_text.splitlines() if l.strip()]
	analyzed_lines = []
	section_score_sum = 0
	for idx, line in enumerate(lines):
		print(f"[AI DEBUG] Calling AI for section '{section_name}', line {idx+1}/{len(lines)}: {line[:80]}")
		prompt = (
			f"This is a fresher resume for a student. Give only a short, actionable suggestion and scores. "
			f"For this line: '{line}', check grammar, clarity, and suggest a stronger version. "
			f"If any important job-related keywords are missing, include them in a missing_keywords field as a list. "
			f"Reply ONLY with JSON: {{clarity_score (0-10), impact_score (0-10), ats_compatibility (0-10), suggestion, missing_keywords (list)}}."
		)
		if target_role:
			prompt += f" Compare this line against job role requirements for {target_role}. If any keywords are missing, add them to missing_keywords."
		try:
			ai_response = call_ai_api(prompt)
			print(f"[AI DEBUG] AI response for section '{section_name}', line {idx+1}: {ai_response[:120]}")
			import json
			json_start = ai_response.find('{')
			json_end = ai_response.rfind('}') + 1
			if json_start != -1 and json_end != -1:
				ai_json = ai_response[json_start:json_end]
				data = json.loads(ai_json)
				analyzed_lines.append({
					"original": line,
					"suggestion": data.get("suggestion"),
					"clarity_score": int(data.get("clarity_score", 0)),
					"ats_compatibility": int(data.get("ats_compatibility", 0)),
					"impact_score": int(data.get("impact_score", 0)),
					"missing_keywords": data.get("missing_keywords", None)
				})
				section_score_sum += int(data.get("clarity_score", 0)) + int(data.get("ats_compatibility", 0)) + int(data.get("impact_score", 0))
			else:
				analyzed_lines.append({"original": line, "suggestion": ai_response, "clarity_score": 0, "ats_compatibility": 0, "impact_score": 0, "missing_keywords": None})
		except Exception as e:
			print(f"[AI DEBUG] AI error for section '{section_name}', line {idx+1}: {e}")
			analyzed_lines.append({"original": line, "suggestion": f"AI error: {e}", "clarity_score": 0, "ats_compatibility": 0, "impact_score": 0, "missing_keywords": None})
	# Section score: average of line scores (out of 30, scaled to 100)
	max_score = len(analyzed_lines) * 30 if analyzed_lines else 1
	section_score = int((section_score_sum / max_score) * 100) if analyzed_lines else 0
	return {"section_score": section_score, "lines": analyzed_lines}


def split_resume_sections(text):
	# Simple heuristic: split by common section headers
	section_headers = [
		"personal info", "personal information", "contact", "education", "academic", "experience", "work", "projects", "skills", "certifications", "achievements", "summary", "objective"
	]
	lines = text.splitlines()
	sections = {}
	current_section = "Other"
	buffer = []
	for line in lines:
		l = line.strip().lower()
		found = False
		for header in section_headers:
			if l.startswith(header):
				# Save previous section
				if buffer:
					sections[current_section] = '\n'.join(buffer).strip()
					buffer = []
				current_section = header.title()
				found = True
				break
		if not found:
			buffer.append(line)
	if buffer:
		sections[current_section] = '\n'.join(buffer).strip()
	return sections

def analyze_resume(text, target_role=None):
	sections = split_resume_sections(text)
	section_feedback = {}
	total_score = 0
	section_count = 0
	for section, section_text in sections.items():
		ai_result = ai_analyze_section(section, section_text, target_role=target_role)
		section_feedback[section] = ai_result
		total_score += int(ai_result.get("section_score", 0))
		section_count += 1
	overall_score = int(total_score / section_count) if section_count else 0
	return {
		"sections": section_feedback,
		"overall": {"score": overall_score}
	}
