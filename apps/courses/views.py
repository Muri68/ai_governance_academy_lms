from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, FileResponse, Http404, JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from io import BytesIO
import os
import json
import hashlib
import qrcode
import tempfile
from urllib.parse import quote

from apps.accounts.models import AdminProfile, InstructorProfile

from .models import (
    Course, Lesson, LessonContent, Enrollment, 
    LessonProgress, CourseReview
)

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image


# ===================== COURSE LEARNING =====================

@login_required
def course_learning(request, course_slug):
    """Main course learning page"""
    course = get_object_or_404(
        Course.objects.prefetch_related('lessons__contents'),
        slug=course_slug,
        status='published'
    )
    
    # Get or create enrollment
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()
    
    if not enrollment:
        enrollment = Enrollment.objects.create(
            student=request.user, course=course, status='active'
        )
        messages.success(request, f'You have been enrolled in {course.title}! Start learning!')
    elif enrollment.status == 'completed':
        messages.info(request, f'You have completed {course.title}. Feel free to review!')
    elif enrollment.status != 'active':
        enrollment.status = 'active'
        enrollment.save()
        messages.success(request, f'Welcome back to {course.title}!')
    
    enrollment.last_accessed = timezone.now()
    enrollment.save()
    
    # Get lessons
    lessons = course.lessons.filter(is_published=True).order_by('order')
    
    # Get current lesson
    lesson_id = request.GET.get('lesson')
    current_lesson = None
    
    if lesson_id:
        try:
            current_lesson = lessons.get(id=lesson_id)
        except Lesson.DoesNotExist:
            current_lesson = lessons.first() if lessons.exists() else None
    elif lessons.exists():
        current_lesson = lessons.first()
    
    # Get lesson contents and current content
    lesson_contents = []
    current_content = None
    current_content_index = 0
    
    if current_lesson:
        lesson_contents = current_lesson.contents.all().order_by('order')
        
        content_id = request.GET.get('content')
        if content_id:
            try:
                current_content = lesson_contents.get(id=content_id)
            except LessonContent.DoesNotExist:
                current_content = lesson_contents.first() if lesson_contents.exists() else None
        elif lesson_contents.exists():
            current_content = lesson_contents.first()
        
        # Calculate content index
        if current_content:
            for idx, c in enumerate(lesson_contents):
                if c.id == current_content.id:
                    current_content_index = idx
                    break
    
    # Get progress
    lesson_progress = {}
    completed_lesson_ids = set()
    
    if enrollment:
        for prog in LessonProgress.objects.filter(student=request.user, enrollment=enrollment):
            lesson_progress[prog.lesson_id] = prog
            if prog.completed:
                completed_lesson_ids.add(prog.lesson_id)
    
    # Calculate progress
    total_lessons = lessons.count()
    completed_lessons = len(completed_lesson_ids)
    progress_percentage = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
    
    enrollment.progress_percentage = progress_percentage
    enrollment.save()
    
    # Previous and next lesson
    prev_lesson = None
    next_lesson = None
    if current_lesson and lessons.exists():
        lesson_list = list(lessons)
        try:
            idx = lesson_list.index(current_lesson)
            if idx > 0: 
                prev_lesson = lesson_list[idx - 1]
            if idx < len(lesson_list) - 1: 
                next_lesson = lesson_list[idx + 1]
        except ValueError:
            pass
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'lessons': lessons,
        'current_lesson': current_lesson,
        'current_content': current_content,
        'lesson_contents': lesson_contents,
        'current_content_index': current_content_index,
        'lesson_progress': lesson_progress,
        'completed_lesson_ids': completed_lesson_ids,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'progress_percentage': progress_percentage,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
    }
    return render(request, 'courses/learning.html', context)


# ===================== AJAX: LOAD LESSON CONTENT =====================

@login_required
def load_lesson_content(request, course_slug, lesson_id, content_id):
    """AJAX endpoint to load specific lesson content without page refresh"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course, is_published=True)
    content = get_object_or_404(LessonContent, id=content_id, lesson=lesson)
    
    # Get all contents for this lesson
    all_contents = list(lesson.contents.all().order_by('order'))
    current_index = 0
    for i, c in enumerate(all_contents):
        if c.id == content.id:
            current_index = i
            break
    
    # Get next and previous content IDs
    prev_content_id = all_contents[current_index - 1].id if current_index > 0 else None
    next_content_id = all_contents[current_index + 1].id if current_index < len(all_contents) - 1 else None
    
    # Get next/prev lessons
    all_lessons = list(course.lessons.filter(is_published=True).order_by('order'))
    lesson_index = 0
    for i, l in enumerate(all_lessons):
        if l.id == lesson.id:
            lesson_index = i
            break
    
    next_lesson_id = all_lessons[lesson_index + 1].id if lesson_index < len(all_lessons) - 1 else None
    prev_lesson_id = all_lessons[lesson_index - 1].id if lesson_index > 0 else None
    
    # Get enrollment for notes
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    
    notes = ''
    if enrollment:
        progress = LessonProgress.objects.filter(
            student=request.user, lesson=lesson, enrollment=enrollment
        ).first()
        if progress:
            notes = progress.notes or ''
    
    # Build content HTML
    content_html = build_content_html(content, course)
    
    # Build badge
    type_icons = {
        'video': 'fas fa-play-circle',
        'video_url': 'fas fa-link',
        'text': 'fas fa-file-alt',
        'pdf': 'fas fa-file-pdf',
        'quiz': 'fas fa-question-circle',
        'assignment': 'fas fa-tasks',
        'code': 'fas fa-code',
        'slides': 'fas fa-desktop',
    }
    type_icon = type_icons.get(content.content_type, 'fas fa-file')
    type_display = dict(LessonContent.CONTENT_TYPE_CHOICES).get(content.content_type, content.content_type)
    
    badge_html = f'<span class="content-type-badge {content.content_type}"><i class="{type_icon}"></i> {type_display}</span>'
    
    response_data = {
        'status': 'success',
        'content': {
            'id': content.id,
            'title': content.title or type_display,
            'type': content.content_type,
            'type_display': type_display,
            'html': content_html,
            'badge_html': badge_html,
        },
        'lesson': {
            'id': lesson.id,
            'title': lesson.title,
            'order': lesson.order,
        },
        'navigation': {
            'current_content_index': current_index,
            'total_contents': len(all_contents),
            'prev_content_id': prev_content_id,
            'next_content_id': next_content_id,
            'prev_lesson_id': prev_lesson_id,
            'next_lesson_id': next_lesson_id,
        },
        'notes': notes,
    }
    
    return JsonResponse(response_data)


def build_content_html(content, course):
    """Helper function to build HTML for different content types"""
    content_type = content.content_type
    html = ''
    
    # FIX: Use the correct URL pattern
    serve_file_url = reverse('courses:serve_file', kwargs={
        'course_slug': course.slug,
        'content_id': content.id
    })
    
    # For YouTube videos, the script needs special handling
    if content_type == 'video_url' and content.video_url:
        html = f'''
        <div class="video-player-container">
            <div class="video-wrapper" id="vid-{content.id}"></div>
        </div>
        <script>
        (function(){{
            var url = '{content.video_url}';
            var el = document.getElementById('vid-{content.id}');
            if(!el||!url)return;
            var src = url;
            if(url.indexOf('youtube.com/watch')>-1){{
                var v = url.split('v=')[1];
                if(v.indexOf('&')>-1) v = v.split('&')[0];
                if(v.indexOf('#')>-1) v = v.split('#')[0];
                src = 'https://www.youtube.com/embed/'+v;
            }}else if(url.indexOf('youtu.be/')>-1){{
                src = 'https://www.youtube.com/embed/'+url.split('youtu.be/')[1].split('?')[0];
            }}else if(url.indexOf('vimeo.com/')>-1){{
                src = 'https://player.vimeo.com/video/'+url.split('vimeo.com/')[1].split('?')[0];
            }}
            setTimeout(function(){{
                el.innerHTML = '<iframe src="'+src+'" frameborder="0" allowfullscreen style="width:100%;height:100%;position:absolute;top:0;left:0;border:0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"></iframe>';
            }}, 100);
        }})();
        </script>
        '''
    
    elif content_type == 'video' and content.video_file:
        html = f'''
        <div class="video-player-container">
            <div class="video-wrapper">
                <video controls preload="metadata" playsinline style="width:100%;height:100%;" 
                       controlsList="nodownload" oncontextmenu="return false;">
                    <source src="{serve_file_url}" type="video/mp4">
                </video>
            </div>
        </div>
        '''
    
    elif content_type == 'text' and content.text_content:
        html = f'<div class="content-text">{content.text_content}</div>'
    
    elif content_type in ['pdf', 'slides'] and content.pdf_file:
        download_html = ''
        if content.allow_download:
            download_html = f'''
            <a href="{serve_file_url}?download=1" class="btn-header btn-header-outline" 
               style="display:inline-flex;text-decoration:none;margin-top:8px;color:var(--text-dark);border-color:rgba(0,0,0,0.2);">
               <i class="fas fa-download"></i> Download PDF
            </a>'''
        else:
            download_html = '<p class="download-locked"><i class="fas fa-lock"></i> Download not permitted</p>'
        
        loading_text = 'Loading PDF...' if content_type == 'pdf' else 'Loading Slides...'
        error_text = 'Unable to Load PDF' if content_type == 'pdf' else 'Unable to Load Slides'
        
        html = f'''
        <div class="pdf-viewer-container" id="pdf-viewer-{content.id}">
            <div class="pdf-viewer-inner" id="pdf-inner-{content.id}">
                <div class="pdf-canvas-wrapper">
                    <canvas class="pdf-page-canvas" id="pdf-canvas-{content.id}"></canvas>
                </div>
            </div>
            <div class="pdf-loading-overlay" id="pdf-loading-{content.id}">
                <div style="text-align:center;">
                    <i class="fas fa-spinner fa-spin" style="font-size:32px;display:block;margin-bottom:12px;"></i>
                    <p style="font-size:14px;">{loading_text}</p>
                </div>
            </div>
            <div class="pdf-error-overlay" id="pdf-error-{content.id}" style="display:none;">
                <i class="fas fa-file-pdf" style="font-size:48px;display:block;margin-bottom:16px;color:#ef4444;"></i>
                <h4>{error_text}</h4>
                <button onclick="retryPdfLoad('{content.id}')" 
                        style="background:#0c1e2e;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;margin-top:8px;">
                    <i class="fas fa-redo"></i> Retry
                </button>
            </div>
        </div>
        <div class="pdf-controls-bar" id="pdf-controls-{content.id}">
            <button onclick="changePdfPage('{content.id}', -1)" id="pdf-prev-{content.id}" disabled>
                <i class="fas fa-chevron-left"></i> Previous
            </button>
            <span style="font-size:12px;color:var(--text-dark);">
                Page 
                <input type="number" class="page-input" id="pdf-page-input-{content.id}" 
                       value="1" min="1" onchange="goToPdfPage('{content.id}', this.value)" 
                       onkeypress="if(event.key==='Enter')goToPdfPage('{content.id}', this.value)"
                       style="width:50px;text-align:center;padding:6px;border:1px solid #e5e7eb;border-radius:4px;font-size:12px;">
                of <span id="pdf-total-pages-{content.id}">?</span>
            </span>
            <button onclick="changePdfPage('{content.id}', 1)" id="pdf-next-{content.id}" disabled>
                Next <i class="fas fa-chevron-right"></i>
            </button>
        </div>
        {download_html}
        {f'<div class="content-text" style="margin-top:16px;">{content.text_content}</div>' if content_type == 'slides' and content.text_content else ''}
        <script>setTimeout(function(){{ initPdfViewer('{content.id}'); }}, 100);</script>
        '''
    
    elif content_type == 'quiz':
        questions_html = ''
        if content.quiz_data and content.quiz_data.get('questions'):
            for i, q in enumerate(content.quiz_data['questions']):
                options_html = ''
                for option in q.get('options', []):
                    options_html += f'<label class="quiz-option" onclick="selectQuizOption(this)"><span class="quiz-radio"></span> {option}</label>'
                questions_html += f'''
                <div class="quiz-question-block">
                    <div class="quiz-question">{i+1}. {q["question"]}</div>
                    {options_html}
                </div>'''
        
        html = f'''
        <div class="quiz-container" id="quiz-{content.id}">
            <h4>{content.title or "Quiz"}</h4>
            {f'<p class="content-text">{content.text_content}</p>' if content.text_content else ''}
            {questions_html}
            <button class="btn-submit-quiz" onclick="submitQuiz('{content.id}', {len(content.quiz_data.get('questions', []))}, {content.passing_score})">
                Submit Quiz
            </button>
            <div class="quiz-result" id="quiz-result-{content.id}"></div>
        </div>
        '''
    
    elif content_type == 'code' and content.text_content:
        html = f'<div class="code-block"><pre><code>{content.text_content}</code></pre></div>'
    
    elif content_type == 'assignment':
        instructions = content.assignment_instructions or content.text_content or ''
        html = f'''
        <div class="assignment-box">
            <h4>{content.title or "Assignment"}</h4>
            <span class="max-score">Max Score: {content.max_score}</span>
            <div style="margin-top:12px;white-space:pre-wrap;font-size:13px;color:#4a5568;">
                {instructions}
            </div>
        </div>
        '''
    
    return html


# ===================== AJAX: MARK LESSON COMPLETE =====================

@login_required
def mark_lesson_complete(request, course_slug, lesson_id):
    """AJAX endpoint to toggle lesson completion"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Get or create enrollment
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment:
        enrollment = Enrollment.objects.create(student=request.user, course=course, status='active')
    elif enrollment.status not in ['active', 'completed']:
        enrollment.status = 'active'
        enrollment.save()
    
    # Check sequential order
    all_lessons = list(course.lessons.filter(is_published=True).order_by('order'))
    current_lesson_index = None
    
    for i, les in enumerate(all_lessons):
        if les.id == lesson.id:
            current_lesson_index = i
            break
    
    progress = LessonProgress.objects.filter(
        student=request.user, lesson=lesson, enrollment=enrollment
    ).first()
    
    is_uncompleting = progress and progress.completed
    
    # ONLY check sequential order if user is trying to COMPLETE (not uncomplete)
    if not is_uncompleting and current_lesson_index is not None and current_lesson_index > 0:
        previous_lessons = all_lessons[:current_lesson_index]
        incomplete_previous = []
        
        for prev_lesson in previous_lessons:
            prev_progress = LessonProgress.objects.filter(
                student=request.user, lesson=prev_lesson, enrollment=enrollment, completed=True
            ).first()
            if not prev_progress:
                incomplete_previous.append({
                    'id': prev_lesson.id,
                    'title': prev_lesson.title,
                    'order': prev_lesson.order
                })
        
        if incomplete_previous:
            lesson_names = [f'"{l["title"]}"' for l in incomplete_previous[:3]]
            if len(incomplete_previous) > 3:
                lesson_names.append(f'and {len(incomplete_previous) - 3} more')
            
            return JsonResponse({
                'status': 'error',
                'message': f'You must complete these lessons first: {", ".join(lesson_names)}.',
                'incomplete_lessons': incomplete_previous,
                'code': 'SEQUENTIAL_REQUIRED'
            }, status=400)
    
    # Toggle completion
    if not progress:
        progress = LessonProgress.objects.create(
            student=request.user, lesson=lesson, enrollment=enrollment
        )
    
    if progress.completed:
        progress.completed = False
        progress.completed_at = None
    else:
        progress.completed = True
        progress.completed_at = timezone.now()
    
    progress.save()
    
    # Recalculate progress
    total_lessons = len(all_lessons)
    completed_lessons = LessonProgress.objects.filter(
        student=request.user, enrollment=enrollment, completed=True
    ).count()
    
    if total_lessons > 0:
        enrollment.progress_percentage = int((completed_lessons / total_lessons) * 100)
    
    # Auto-complete course - FIXED: Check if ALL lessons are completed
    course_completed = False
    certificate_url = None
    
    # Check if all lessons are completed and enrollment is still active
    if completed_lessons >= total_lessons and total_lessons > 0:
        if enrollment.status == 'active':
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            course_completed = True
            
            if course.has_certificate:
                cert_string = f"{request.user.id}-{course.id}-{timezone.now().timestamp()}"
                cert_hash = hashlib.md5(cert_string.encode()).hexdigest()[:12].upper()
                cert_id = f"CERT-{cert_hash}"
                enrollment.certificate_url = reverse('courses:verify_certificate', kwargs={'cert_id': cert_id})
                enrollment.certificate_issued = True
                certificate_url = reverse('courses:view_certificate', kwargs={'enrollment_id': enrollment.id})
            else:
                enrollment.certificate_issued = False
                enrollment.certificate_url = None
        elif enrollment.status == 'completed':
            # Already completed, check if certificate was issued
            course_completed = True
            if enrollment.certificate_issued and enrollment.certificate_url:
                certificate_url = reverse('courses:view_certificate', kwargs={'enrollment_id': enrollment.id})
    
    enrollment.save()
    
    # Update student profile
    if hasattr(request.user, 'student_profile'):
        p = request.user.student_profile
        p.courses_enrolled = Enrollment.objects.filter(student=request.user, status='active').count()
        p.completed_courses = Enrollment.objects.filter(student=request.user, status='completed').count()
        p.save()
    
    # Find next unlocked lesson
    next_lesson = None
    if progress.completed and current_lesson_index is not None:
        for i in range(current_lesson_index + 1, len(all_lessons)):
            next_les = all_lessons[i]
            next_progress = LessonProgress.objects.filter(
                student=request.user, lesson=next_les, enrollment=enrollment, completed=True
            ).first()
            if not next_progress:
                next_lesson = {'id': next_les.id, 'title': next_les.title, 'order': next_les.order}
                break
    
    response_data = {
        'status': 'success',
        'completed': progress.completed,
        'progress': enrollment.progress_percentage,
        'enrollment_status': enrollment.status,
        'course_completed': course_completed,
        'total_completed': completed_lessons,
        'total_lessons': total_lessons,
    }
    
    if next_lesson:
        response_data['next_lesson'] = next_lesson
    
    if course_completed:
        if certificate_url:
            response_data['message'] = f'Congratulations! You have completed "{course.title}"! Your certificate is ready.'
            response_data['certificate_url'] = certificate_url
        else:
            response_data['message'] = f'Congratulations! You have completed "{course.title}"!'
            response_data['certificate_url'] = None
    
    return JsonResponse(response_data)

# ===================== AJAX: SAVE NOTES =====================

@login_required
def save_lesson_notes(request, course_slug, lesson_id):
    """AJAX: Save lesson notes"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body)
        notes = data.get('notes', '')
    except json.JSONDecodeError:
        notes = request.POST.get('notes', '')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course, status__in=['active', 'completed']
    ).first()
    if not enrollment:
        enrollment = Enrollment.objects.create(student=request.user, course=course, status='active')
    
    progress, _ = LessonProgress.objects.get_or_create(
        student=request.user, lesson=lesson, enrollment=enrollment
    )
    progress.notes = notes
    progress.save()
    
    return JsonResponse({'status': 'success', 'message': 'Notes saved!'})


# ===================== FILE SERVING =====================

@login_required
def serve_protected_file(request, course_slug, content_id):
    """Serve protected course files with proper inline viewing support"""
    course = get_object_or_404(Course, slug=course_slug)
    content = get_object_or_404(LessonContent, id=content_id)
    
    # Check enrollment or create one
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course, status__in=['active', 'completed']
    ).first()
    if not enrollment and not content.is_preview:
        enrollment = Enrollment.objects.create(student=request.user, course=course, status='active')
    
    file_field = None
    mime_type = 'application/octet-stream'
    
    if content.content_type == 'pdf' and content.pdf_file:
        file_field = content.pdf_file
        mime_type = 'application/pdf'
    elif content.content_type == 'video' and content.video_file:
        file_field = content.video_file
        file_ext = os.path.splitext(content.video_file.name)[1].lower()
        mime_map = {'.mp4': 'video/mp4', '.webm': 'video/webm', '.ogg': 'video/ogg'}
        mime_type = mime_map.get(file_ext, 'video/mp4')
    elif content.content_type == 'slides' and content.pdf_file:
        file_field = content.pdf_file
        mime_type = 'application/pdf'
    
    if file_field:
        try:
            file_handle = file_field.open('rb')
            response = FileResponse(file_handle, content_type=mime_type)
            filename = os.path.basename(file_field.name)
            encoded_filename = quote(filename)
            
            download = request.GET.get('download', '')
            
            if download:
                response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            elif mime_type in ['application/pdf', 'video/mp4', 'video/webm', 'video/ogg']:
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            else:
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            response['X-Content-Type-Options'] = 'nosniff'
            response['Accept-Ranges'] = 'bytes'
            
            return response
            
        except FileNotFoundError:
            raise Http404("File not found")
        except Exception as e:
            raise Http404(f"Error serving file: {str(e)}")
    
    raise Http404("No file available")


# ===================== REVIEWS =====================

@login_required
def submit_review(request, course_slug):
    """Submit course review"""
    if request.method == 'POST':
        course = get_object_or_404(Course, slug=course_slug)
        
        existing = CourseReview.objects.filter(student=request.user, course=course).first()
        
        rating = request.POST.get('rating', 5)
        title = request.POST.get('title', '')
        review_text = request.POST.get('review', '')
        
        if existing:
            existing.rating = rating
            existing.title = title
            existing.review = review_text
            existing.save()
            messages.success(request, 'Your review has been updated!')
        else:
            CourseReview.objects.create(
                student=request.user, course=course,
                rating=rating, title=title, review=review_text
            )
            messages.success(request, 'Thank you for your review!')
        
        referer = request.META.get('HTTP_REFERER', '')
        if 'student' in referer:
            return redirect('accounts:student_courses')
        return redirect('frontend:course_detail', slug=course.slug)
    
    return redirect('frontend:index')


# ===================== CERTIFICATES =====================

def convert_signature_to_white(signature_path, output_path):
    """Convert signature image to white for dark backgrounds"""
    try:
        img = Image.open(signature_path).convert('RGBA')
        data = img.getdata()
        new_data = []
        
        for item in data:
            r, g, b, a = item
            if a > 50:
                brightness = (r + g + b) / 3
                if brightness < 200:
                    new_data.append((255, 255, 255, a))
                else:
                    new_data.append((255, 255, 255, 0))
            else:
                new_data.append((255, 255, 255, 0))
        
        img.putdata(new_data)
        img.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        print(f"Error converting signature: {e}")
        return signature_path


@login_required
def view_certificate(request, enrollment_id):
    """Generate and download PDF certificate with QR code and signatures"""
    enrollment = get_object_or_404(
        Enrollment.objects.select_related('course', 'student', 'course__instructor__instructor_profile'),
        id=enrollment_id, student=request.user, status='completed'
    )
    
    # Get cert_id
    cert_id = None
    if enrollment.certificate_url:
        parts = enrollment.certificate_url.rstrip('/').split('/')
        for part in parts:
            if part.startswith('CERT-'):
                cert_id = part
                break
    
    if not cert_id:
        cert_string = f"{request.user.id}-{enrollment.course.id}-{timezone.now().timestamp()}"
        cert_hash = hashlib.md5(cert_string.encode()).hexdigest()[:12].upper()
        cert_id = f"CERT-{cert_hash}"
        enrollment.certificate_url = reverse('courses:verify_certificate', kwargs={'cert_id': cert_id})
        enrollment.save()
    
    verification_url = request.build_absolute_uri(
        reverse('courses:verify_certificate', kwargs={'cert_id': cert_id})
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="white", back_color="#0c1e2e")
    
    qr_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    qr_img.save(qr_temp.name)
    qr_temp.close()
    
        # ===== HANDLE SIGNATURES =====
    instructor_sig_temp = None
    director_sig_temp = None
    
    # ===== INSTRUCTOR SIGNATURE =====
    instructor = enrollment.course.instructor
    print(f"Instructor: {instructor.email}, ID: {instructor.id}")
    
    # Check if instructor has a profile
    try:
        instructor_profile = InstructorProfile.objects.get(user=instructor)
        print(f"Instructor profile found: {instructor_profile.instructor_id}")
        print(f"Has signature: {bool(instructor_profile.signature)}")
        
        if instructor_profile.signature:
            print(f"Signature path: {instructor_profile.signature.path}")
            print(f"Signature exists: {os.path.exists(instructor_profile.signature.path)}")
    except InstructorProfile.DoesNotExist:
        instructor_profile = None
        print("No InstructorProfile found for this instructor!")
    
    if instructor_profile and instructor_profile.signature:
        try:
            sig_path = instructor_profile.signature.path
            if os.path.exists(sig_path):
                instructor_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                instructor_sig_temp.close()
                result = convert_signature_to_white(sig_path, instructor_sig_temp.name)
                print(f"Instructor signature converted. Result: {result}")
                # Verify the output file exists and has content
                if os.path.exists(instructor_sig_temp.name):
                    file_size = os.path.getsize(instructor_sig_temp.name)
                    print(f"Instructor temp file size: {file_size} bytes")
                    if file_size == 0:
                        print("WARNING: Instructor signature temp file is empty!")
                        instructor_sig_temp = None
        except Exception as e:
            print(f"ERROR processing instructor signature: {e}")
            import traceback
            traceback.print_exc()
            instructor_sig_temp = None
    else:
        print("No instructor signature available")
        if not instructor_profile:
            print("  - No instructor profile exists")
        elif not instructor_profile.signature:
            print("  - Instructor profile exists but no signature uploaded")
    
    # ===== DIRECTOR SIGNATURE (Admin Profile or Static Default) =====
    admin_profile = None
    director_name = None
    
    # Find any admin/superadmin with a signature
    admin_profile = AdminProfile.objects.filter(
        signature__isnull=False
    ).exclude(signature='').order_by('-access_level').first()
    
    if admin_profile and admin_profile.signature:
        try:
            sig_path = admin_profile.signature.path
            if os.path.exists(sig_path):
                director_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                director_sig_temp.close()
                convert_signature_to_white(sig_path, director_sig_temp.name)
                print(f"Admin signature processed: {director_sig_temp.name}")
        except Exception as e:
            print(f"Error processing admin signature: {e}")
            director_sig_temp = None
    
    # If no admin signature, fall back to default static file
    if not director_sig_temp:
        print("No admin signature found, trying static file...")
        static_dirs = []
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            static_dirs.append(settings.STATIC_ROOT)
        if hasattr(settings, 'STATICFILES_DIRS'):
            static_dirs.extend(settings.STATICFILES_DIRS)
        
        for static_dir in static_dirs:
            if static_dir:
                test_path = os.path.join(static_dir, 'images', 'director-signature.png')
                print(f"Checking: {test_path}")
                if os.path.exists(test_path):
                    try:
                        director_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        director_sig_temp.close()
                        convert_signature_to_white(test_path, director_sig_temp.name)
                        print(f"Static signature processed: {director_sig_temp.name}")
                        break
                    except Exception as e:
                        print(f"Error processing static signature: {e}")
                        director_sig_temp = None
    
    # ===== DIRECTOR NAME =====
    if admin_profile:
        director_name = admin_profile.user.get_full_name() or admin_profile.user.email
    else:
        director_name = getattr(settings, 'CERTIFICATE_DIRECTOR_NAME', 'Dr. James Anderson')
    
    director_title = getattr(settings, 'CERTIFICATE_DIRECTOR_TITLE', 'Program Director')
    
    print(f"Director name: {director_name}, Instructor sig: {instructor_sig_temp is not None}, Director sig: {director_sig_temp is not None}")
    
    # ===== BUILD PDF =====
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Background
    c.setFillColor(HexColor('#0c1e2e'))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Borders
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(3)
    c.rect(25, 25, width - 50, height - 50, fill=False, stroke=True)
    c.setLineWidth(1)
    c.rect(38, 38, width - 76, height - 76, fill=False, stroke=True)
    
    # Text
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 65, getattr(settings, 'CERTIFICATE_ORGANIZATION', 'AI GOVERNANCE AUTHORITY'))
    
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 115, "CERTIFICATE OF COMPLETION")
    
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(2)
    c.line(width/2 - 180, height - 130, width/2 + 180, height - 130)
    
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 165, "This is to certify that")
    
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 24)
    student_name = enrollment.student.get_full_name()
    c.drawCentredString(width/2, height - 205, student_name)
    
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 240, "has successfully completed the course")
    
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 275, enrollment.course.title)
    
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 11)
    completed_date = enrollment.completed_at.strftime("%B %d, %Y") if enrollment.completed_at else ""
    c.drawCentredString(width/2, height - 310, f"Completed on: {completed_date}")
    
    # ===== SIGNATURES SECTION =====
    sig_y_line = height - 390
    sig_y_text = height - 410
    sig_y_title = height - 425
    sig_y_image = height - 395
    
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(1)
    
    # ===== INSTRUCTOR SIGNATURE (Left) =====
    instructor_sig_box_x = 100
    instructor_sig_box_width = 180
    
    # Draw instructor signature image
    if instructor_sig_temp and os.path.exists(instructor_sig_temp.name):
        try:
            c.drawImage(instructor_sig_temp.name, instructor_sig_box_x + 20, sig_y_image, 
                       width=140, height=55, preserveAspectRatio=True, mask='auto')
            print("Instructor signature drawn on PDF")
        except Exception as e:
            print(f"Error drawing instructor signature: {e}")
    else:
        print("No instructor signature to draw")
    
    # Instructor line and name
    c.line(instructor_sig_box_x, sig_y_line, instructor_sig_box_x + instructor_sig_box_width, sig_y_line)
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_text, instructor.get_full_name())
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_title, "Instructor")
    
    # ===== DIRECTOR SIGNATURE (Right) =====
    director_sig_box_x = width - 280
    director_sig_box_width = 180
    
    # Draw director signature image
    if director_sig_temp and os.path.exists(director_sig_temp.name):
        try:
            c.drawImage(director_sig_temp.name, director_sig_box_x + 20, sig_y_image, 
                       width=140, height=55, preserveAspectRatio=True, mask='auto')
            print("Director signature drawn on PDF")
        except Exception as e:
            print(f"Error drawing director signature: {e}")
    else:
        print("No director signature to draw")
    
    # Director line and name
    c.line(director_sig_box_x, sig_y_line, director_sig_box_x + director_sig_box_width, sig_y_line)
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_text, director_name)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_title, director_title)
    
    # ===== QR CODE =====
    qr_size = 80
    qr_x = width - qr_size - 55
    qr_y = 55
    
    try:
        c.drawImage(qr_temp.name, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
        c.setFont("Helvetica", 7)
        c.setFillColor(HexColor('#64748b'))
        c.drawCentredString(qr_x + qr_size/2, qr_y - 12, "Scan to verify")
    except Exception as e:
        print(f"Error drawing QR code: {e}")
    
    # Bottom text
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor('#64748b'))
    c.drawCentredString(width/2, 55, f"Certificate ID: {cert_id}")
    c.drawCentredString(width/2, 42, f"Verify online: {verification_url}")
    
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    
    # Clean up temp files
    for temp_file in [qr_temp, instructor_sig_temp, director_sig_temp]:
        if temp_file:
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error cleaning up temp file: {e}")
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Certificate_{enrollment.course.slug}_{student_name.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def verify_certificate(request, cert_id):
    """Public certificate verification"""
    verified = False
    enrollment = None
    
    enrollment = Enrollment.objects.filter(
        certificate_url__icontains=cert_id,
        status='completed',
        certificate_issued=True
    ).select_related('student', 'course', 'course__instructor').first()
    
    if enrollment:
        verified = True
    
    context = {
        'enrollment': enrollment,
        'cert_id': cert_id,
        'verified': verified,
    }
    return render(request, 'courses/verify_certificate.html', context)