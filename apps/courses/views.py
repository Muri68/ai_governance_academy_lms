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
    LessonProgress, CourseReview, Quiz, QuizQuestion, 
    QuizAnswer, QuizAttempt, QuizAnswerRecord, FinalExam,
    FinalExamQuestion, FinalExamAnswer, FinalExamAttempt, FinalExamAnswerRecord,
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
        Course.objects.prefetch_related('lessons__contents', 'lessons__quizzes'),
        slug=course_slug,
        status='published'
    )
    
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
        # Check if they actually passed the final exam (if exists)
        final_exam_check = FinalExam.objects.filter(course=course, is_active=True).first()
        
        if final_exam_check:
            passed_exam = FinalExamAttempt.objects.filter(
                exam=final_exam_check, student=request.user, passed=True
            ).exists()
            
            if passed_exam:
                messages.info(request, f'You have completed {course.title}. Feel free to review!')
            else:
                # They completed lessons but haven't passed final exam
                # Keep them as 'active' so they can take the exam
                enrollment.status = 'active'
                enrollment.save()
                messages.info(request, f'You have completed all lessons. You must now pass the final exam to complete the course.')
        else:
            messages.info(request, f'You have completed {course.title}. Feel free to review!')
    
    enrollment.last_accessed = timezone.now()
    enrollment.save()
    
    lessons = course.lessons.filter(is_published=True).order_by('order')
    
    # Get current lesson
    lesson_id = request.GET.get('lesson')
    current_lesson = None
    
    if lesson_id:
        try:
            current_lesson = lessons.get(id=lesson_id)
        except (Lesson.DoesNotExist, ValueError):
            current_lesson = lessons.first() if lessons.exists() else None
    elif lessons.exists():
        current_lesson = lessons.first()
    
    lesson_contents = []
    current_content = None
    current_content_index = 0
    current_quiz = None
    show_quiz = False
    
    if current_lesson:
        lesson_contents = list(current_lesson.contents.all().order_by('order'))
        
        # Get quiz
        current_quiz = current_lesson.quizzes.first()
        
        # CHECK QUIZ PARAM
        quiz_param = request.GET.get('quiz')
        
        if quiz_param == '1':
            show_quiz = True
        else:
            show_quiz = False
            content_id = request.GET.get('content')
            
            if content_id:
                try:
                    content_id_int = int(content_id)
                    for content in lesson_contents:
                        if content.id == content_id_int:
                            current_content = content
                            break
                except (ValueError, TypeError):
                    pass
            
            if not current_content and lesson_contents:
                current_content = lesson_contents[0]
            
            if current_content:
                for idx, c in enumerate(lesson_contents):
                    if c.id == current_content.id:
                        current_content_index = idx
                        break
    
    lesson_progress = {}
    completed_lesson_ids = set()
    
    if enrollment:
        for prog in LessonProgress.objects.filter(student=request.user, enrollment=enrollment):
            lesson_progress[prog.lesson_id] = prog
            if prog.completed:
                completed_lesson_ids.add(prog.lesson_id)
    
    total_lessons = lessons.count()
    completed_lessons = len(completed_lesson_ids)
    progress_percentage = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
    
    enrollment.progress_percentage = progress_percentage
    enrollment.save()
    
    # =====================================================
    # FINAL EXAM LOGIC
    # =====================================================
    final_exam = FinalExam.objects.filter(course=course, is_active=True).first()
    final_exam_passed = False
    final_exam_available = False
    show_certificate = False
    
    if final_exam:
        # Check if user has passed the final exam
        final_exam_passed = FinalExamAttempt.objects.filter(
            exam=final_exam, student=request.user, passed=True
        ).exists()
        
        # Final exam is available when ALL lessons are completed
        final_exam_available = completed_lessons >= total_lessons and total_lessons > 0
        
        # Certificate is ONLY visible if final exam is passed
        show_certificate = final_exam_passed and enrollment.certificate_issued
    else:
        # No final exam - certificate visible if course completed
        show_certificate = enrollment.status == 'completed' and enrollment.certificate_issued
    
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
        'current_quiz': current_quiz,
        'show_quiz': show_quiz,
        'final_exam': final_exam,
        'final_exam_passed': final_exam_passed,
        'final_exam_available': final_exam_available,
        'show_certificate': show_certificate,
    }
    
    return render(request, 'courses/learning.html', context)



from django.http import JsonResponse

def test_quiz(request, lesson_id):
    from .models import Quiz, QuizQuestion
    quiz = Quiz.objects.filter(lesson_id=lesson_id).first()
    if quiz:
        return JsonResponse({
            'exists': True,
            'quiz_id': quiz.id,
            'title': quiz.title,
            'questions': list(quiz.questions.values('id', 'question_text')),
        })
    return JsonResponse({'exists': False})


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
    
    # Get quiz for this lesson
    quiz = lesson.quizzes.filter(is_active=True).first()
    quiz_html = ''
    if quiz:
        quiz_html = build_quiz_html(quiz, request.user)
    
    # Build badge
    type_icons = {
        'video': 'fas fa-play-circle',
        'video_url': 'fas fa-link',
        'text': 'fas fa-file-alt',
        'pdf': 'fas fa-file-pdf',
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
        'quiz_html': quiz_html,
        'has_quiz': quiz is not None,
        'quiz_id': quiz.id if quiz else None,
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
    
    # For YouTube videos
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
        # Improved PDF viewer
        html = f'''
        <div class="pdf-container-improved" id="pdf-container-{content.id}" style="width:100%;margin:16px 0;">
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
                <div style="background:#0c1e2e;color:white;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-size:14px;font-weight:600;">
                        <i class="fas fa-file-pdf" style="margin-right:8px;color:#ef4444;"></i>
                        {content.title or 'PDF Document'}
                    </span>
                    <div style="display:flex;gap:8px;">
                        <button onclick="zoomPdf('{content.id}', -0.1)" style="background:rgba(255,255,255,0.1);color:white;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button onclick="zoomPdf('{content.id}', 0.1)" style="background:rgba(255,255,255,0.1);color:white;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button onclick="downloadPdf('{content.id}')" style="background:rgba(255,255,255,0.1);color:white;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </div>
                <div style="display:flex;align-items:center;justify-content:center;gap:16px;padding:12px;background:white;border-bottom:1px solid #e5e7eb;">
                    <button onclick="changePdfPage('{content.id}', -1)" id="pdf-prev-{content.id}" disabled style="background:#0c1e2e;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">
                        <i class="fas fa-chevron-left"></i> Prev
                    </button>
                    <span style="font-size:14px;color:#374151;">
                        Page <span id="pdf-current-page-{content.id}">1</span> of <span id="pdf-total-pages-{content.id}">?</span>
                    </span>
                    <button onclick="changePdfPage('{content.id}', 1)" id="pdf-next-{content.id}" disabled style="background:#0c1e2e;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                <div id="pdf-scroll-container-{content.id}" style="height:600px;overflow:auto;background:#525659;position:relative;">
                    <div id="pdf-pages-container-{content.id}" style="display:flex;flex-direction:column;align-items:center;gap:20px;padding:20px;min-height:100%;">
                        <canvas id="pdf-canvas-{content.id}" style="background:white;box-shadow:0 2px 8px rgba(0,0,0,0.3);"></canvas>
                    </div>
                    <div id="pdf-loading-{content.id}" style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(82,86,89,0.95);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:10;">
                        <i class="fas fa-spinner fa-spin" style="font-size:32px;color:white;margin-bottom:12px;"></i>
                        <p style="color:white;font-size:14px;">Loading PDF...</p>
                    </div>
                    <div id="pdf-error-{content.id}" style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(248,250,252,0.98);display:none;flex-direction:column;align-items:center;justify-content:center;z-index:11;text-align:center;padding:40px;">
                        <i class="fas fa-file-pdf" style="font-size:48px;color:#ef4444;margin-bottom:16px;"></i>
                        <h4 style="margin-bottom:8px;">Unable to Load PDF</h4>
                        <button onclick="retryPdfLoad('{content.id}')" style="background:#0c1e2e;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">
                            <i class="fas fa-redo"></i> Retry
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <script>setTimeout(function(){{ initPdfViewer('{content.id}'); }}, 100);</script>
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


def build_quiz_html(quiz, user):
    """Build quiz HTML for display"""
    if not quiz:
        return ''
    
    questions = quiz.get_randomized_questions(user)
    
    if not questions:
        return '<div class="alert alert-info">No questions available for this quiz.</div>'
    
    html = f'''
    <div class="quiz-modern-container" id="quiz-{quiz.id}" style="margin:20px 0;padding:24px;background:#f8fafc;border-radius:12px;border:1px solid #e5e7eb;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:16px;border-bottom:2px solid #e5e7eb;">
            <div>
                <h3 style="font-size:18px;font-weight:700;color:#0c1e2e;margin:0;">
                    <i class="fas fa-question-circle" style="color:#8b5cf6;margin-right:8px;"></i>
                    {quiz.title or 'Quiz'}
                </h3>
                <p style="font-size:12px;color:#6b7280;margin:4px 0 0;">
                    {len(questions)} questions • Passing score: {quiz.passing_score}%
                </p>
            </div>
            <span style="background:#8b5cf6;color:white;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">
                Quiz
            </span>
        </div>
        <form id="quizForm-{quiz.id}" onsubmit="submitModernQuiz(event, {quiz.id}, {quiz.passing_score})">
    '''
    
    for i, question in enumerate(questions):
        html += f'''
        <div style="background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="font-weight:600;color:#0c1e2e;margin-bottom:12px;">
                <span style="background:#8b5cf6;color:white;padding:2px 8px;border-radius:4px;font-size:12px;margin-right:8px;">Q{i+1}</span>
                {question.question_text}
                <span style="float:right;font-size:12px;color:#6b7280;">{question.points} pts</span>
            </p>
        '''
        
        if question.question_type == 'multiple_choice':
            for answer in question.get_randomized_answers():
                html += f'''
                <label style="display:flex;align-items:center;padding:10px 12px;margin-bottom:8px;border:1px solid #e5e7eb;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.borderColor='#8b5cf6'" onmouseout="this.style.borderColor='#e5e7eb'">
                    <input type="radio" name="question_{question.id}" value="{answer.id}" style="margin-right:10px;">
                    <span style="font-size:14px;">{answer.answer_text}</span>
                </label>
                '''
        elif question.question_type == 'true_false':
            for answer in question.get_randomized_answers():
                html += f'''
                <label style="display:flex;align-items:center;padding:10px 12px;margin-bottom:8px;border:1px solid #e5e7eb;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.borderColor='#8b5cf6'" onmouseout="this.style.borderColor='#e5e7eb'">
                    <input type="radio" name="question_{question.id}" value="{answer.id}" style="margin-right:10px;">
                    <span style="font-size:14px;">{answer.answer_text}</span>
                </label>
                '''
        elif question.question_type == 'short_answer':
            html += f'''
            <textarea name="question_{question.id}" rows="3" placeholder="Type your answer here..." style="width:100%;padding:10px;border:1px solid #e5e7eb;border-radius:6px;font-family:'Poppins',sans-serif;font-size:14px;"></textarea>
            '''
        
        html += '</div>'
    
    html += f'''
            <div style="display:flex;justify-content:flex-end;margin-top:20px;">
                <button type="submit" style="background:#8b5cf6;color:white;border:none;padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;font-family:'Poppins',sans-serif;transition:all 0.3s;" onmouseover="this.style.background='#7c3aed'" onmouseout="this.style.background='#8b5cf6'">
                    <i class="fas fa-check-circle" style="margin-right:8px;"></i> Submit Quiz
                </button>
            </div>
        </form>
        <div id="quizResult-{quiz.id}" style="display:none;margin-top:16px;padding:16px;border-radius:8px;"></div>
    </div>
    '''
    
    return html


# ===================== AJAX: SUBMIT QUIZ =====================

@login_required
def submit_quiz_ajax(request, quiz_id):
    """AJAX endpoint to submit quiz answers"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Create quiz attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user,
    )
    
    total_points = 0
    earned_points = 0
    
    for question_id, answer_value in answers.items():
        try:
            question = QuizQuestion.objects.get(id=question_id, quiz=quiz, is_active=True)
        except QuizQuestion.DoesNotExist:
            continue
        
        total_points += question.points
        is_correct = False
        points_earned = 0
        
        if question.question_type == 'short_answer':
            # For short answers, mark as incorrect for manual review
            QuizAnswerRecord.objects.create(
                attempt=attempt,
                question=question,
                text_answer=answer_value,
                is_correct=False,
                points_earned=0
            )
        else:
            try:
                selected_answer = QuizAnswer.objects.get(id=answer_value, question=question)
                is_correct = selected_answer.is_correct
                if is_correct:
                    points_earned = question.points
                    earned_points += question.points
                
                QuizAnswerRecord.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    points_earned=points_earned
                )
            except (QuizAnswer.DoesNotExist, ValueError):
                pass
    
    # Calculate score
    score_percentage = 0
    if total_points > 0:
        score_percentage = (earned_points / total_points) * 100
    
    attempt.score = earned_points
    attempt.passed = score_percentage >= quiz.passing_score
    attempt.completed_at = timezone.now()
    attempt.save()
    
    # If passed, mark lesson as complete
    if attempt.passed:
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=quiz.lesson.course,
            status__in=['active', 'completed']
        ).first()
        
        if enrollment:
            LessonProgress.objects.update_or_create(
                student=request.user,
                lesson=quiz.lesson,
                enrollment=enrollment,
                defaults={
                    'completed': True,
                    'completed_at': timezone.now(),
                }
            )
    
    return JsonResponse({
        'success': True,
        'score': round(score_percentage, 2),
        'passed': attempt.passed,
        'attempt_id': attempt.id,
        'total_points': total_points,
        'earned_points': earned_points,
        'passing_score': quiz.passing_score,
    })


# ===================== AJAX: MARK LESSON COMPLETE =====================

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
    
    # =====================================================
    # QUIZ CHECK - Must pass lesson quiz before completing
    # =====================================================
    quiz = lesson.quizzes.filter(is_active=True).first()
    
    if quiz:
        progress_check = LessonProgress.objects.filter(
            student=request.user, lesson=lesson, enrollment=enrollment
        ).first()
        
        is_uncompleting = progress_check and progress_check.completed
        
        if not is_uncompleting:
            passed_attempt = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user,
                passed=True
            ).first()
            
            if not passed_attempt:
                return JsonResponse({
                    'status': 'error',
                    'message': f'You must pass the quiz "{quiz.title or "Quiz"}" before completing this lesson.',
                    'code': 'QUIZ_REQUIRED',
                    'quiz_id': quiz.id,
                }, status=400)
    
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
    
    # =====================================================
    # FINAL EXAM CHECK - Do NOT complete course if exam exists
    # =====================================================
    final_exam = FinalExam.objects.filter(course=course, is_active=True).first()
    
    course_completed = False
    certificate_url = None
    
    if completed_lessons >= total_lessons and total_lessons > 0:
        if final_exam:
            # Course has final exam - DO NOT complete course
            # Just update progress and show exam available
            enrollment.save()
            
            return JsonResponse({
                'status': 'success',
                'completed': progress.completed,
                'progress': enrollment.progress_percentage,
                'enrollment_status': enrollment.status,
                'course_completed': False,
                'total_completed': completed_lessons,
                'total_lessons': total_lessons,
                'final_exam_required': True,
                'final_exam_id': final_exam.id,
                'final_exam_title': final_exam.title,
                'message': f'You have completed all lessons! You must now pass the Final Exam "{final_exam.title}" to complete the course and earn your certificate.',
            })
        else:
            # No final exam - complete course normally
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
            else:
                # Always use inline for PDFs to ensure they display in browser
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            # Add CORS headers for PDF.js
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            response['X-Content-Type-Options'] = 'nosniff'
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            
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






@login_required
def take_final_exam(request, exam_id):
    """Display final exam with timer"""
    exam = get_object_or_404(FinalExam, id=exam_id, is_active=True)
    course = exam.course
    
    # Check if user is enrolled
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course, status='active'
    ).first()
    
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to take the final exam.')
        return redirect('courses:course_learning', course_slug=course.slug)
    
    # Check remaining attempts
    attempts_used = FinalExamAttempt.objects.filter(exam=exam, student=request.user).count()
    
    if exam.max_attempts and attempts_used >= exam.max_attempts:
        messages.error(request, f'You have used all {exam.max_attempts} attempts for this exam.')
        return redirect('courses:course_learning', course_slug=course.slug)
    
    # Check if already passed
    passed_attempt = FinalExamAttempt.objects.filter(
        exam=exam, student=request.user, passed=True
    ).first()
    
    if passed_attempt:
        messages.info(request, f'You have already passed this exam with a score of {passed_attempt.percentage}%.')
        return redirect('courses:course_learning', course_slug=course.slug)
    
    # Get questions
    questions = exam.get_randomized_questions(request.user)
    
    context = {
        'exam': exam,
        'course': course,
        'questions': questions,
        'time_limit_minutes': exam.time_limit,
        'time_limit_seconds': exam.time_limit * 60,
        'remaining_attempts': exam.max_attempts - attempts_used if exam.max_attempts else None,
        'attempts_used': attempts_used,
    }
    
    return render(request, 'courses/final_exam.html', context)




@login_required
def submit_final_exam(request, exam_id):
    """Submit final exam answers and send congratulatory email with certificate"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    exam = get_object_or_404(FinalExam, id=exam_id, is_active=True)
    
    # Check attempts
    attempts_used = FinalExamAttempt.objects.filter(exam=exam, student=request.user).count()
    if exam.max_attempts and attempts_used >= exam.max_attempts:
        return JsonResponse({'error': 'Maximum attempts reached'}, status=400)
    
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {})
        time_taken_seconds = data.get('time_taken_seconds', 0)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Create attempt
    attempt = FinalExamAttempt.objects.create(
        exam=exam,
        student=request.user,
        time_taken=timezone.timedelta(seconds=int(time_taken_seconds)),
    )
    
    total_points = 0
    earned_points = 0
    
    for question_id, answer_value in answers.items():
        try:
            question = FinalExamQuestion.objects.get(id=question_id, exam=exam, is_active=True)
        except FinalExamQuestion.DoesNotExist:
            continue
        
        total_points += question.points
        is_correct = False
        points_earned = 0
        
        if question.question_type == 'short_answer':
            FinalExamAnswerRecord.objects.create(
                attempt=attempt,
                question=question,
                text_answer=answer_value,
                is_correct=False,
                points_earned=0
            )
        else:
            try:
                selected_answer = FinalExamAnswer.objects.get(id=answer_value, question=question)
                is_correct = selected_answer.is_correct
                if is_correct:
                    points_earned = question.points
                    earned_points += question.points
                
                FinalExamAnswerRecord.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct,
                    points_earned=points_earned
                )
            except (FinalExamAnswer.DoesNotExist, ValueError):
                pass
    
    score_percentage = 0
    if total_points > 0:
        score_percentage = (earned_points / total_points) * 100
    
    attempt.score = earned_points
    attempt.passed = score_percentage >= exam.passing_score
    attempt.completed_at = timezone.now()
    attempt.save()
    
    certificate_url = None
    
    # If passed, update enrollment and generate certificate
    if attempt.passed:
        enrollment = Enrollment.objects.filter(
            student=request.user, course=exam.course, status='active'
        ).first()
        
        if enrollment:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.progress_percentage = 100
            enrollment.save()
            
            # Generate certificate using existing logic
            if exam.course.has_certificate:
                cert_string = f"{request.user.id}-{exam.course.id}-{timezone.now().timestamp()}"
                cert_hash = hashlib.md5(cert_string.encode()).hexdigest()[:12].upper()
                cert_id = f"CERT-{cert_hash}"
                enrollment.certificate_url = reverse('courses:verify_certificate', kwargs={'cert_id': cert_id})
                enrollment.certificate_issued = True
                enrollment.save()
                certificate_url = reverse('courses:view_certificate', kwargs={'enrollment_id': enrollment.id})
            
            # Update student profile
            if hasattr(request.user, 'student_profile'):
                p = request.user.student_profile
                p.completed_courses = Enrollment.objects.filter(student=request.user, status='completed').count()
                p.save()
            
            # Send congratulatory email with certificate attached
            try:
                send_congratulation_email_with_certificate(
                    request, enrollment, exam, score_percentage, certificate_url
                )
            except Exception as e:
                print(f"Error sending congratulation email: {e}")
    
    # In submit_final_exam, add certificate_url to response:
    return JsonResponse({
        'success': True,
        'score': round(score_percentage, 2),
        'passed': attempt.passed,
        'remaining_attempts': exam.max_attempts - (attempts_used + 1) if exam.max_attempts else None,
        'passing_score': exam.passing_score,
        'certificate_url': certificate_url if attempt.passed and certificate_url else None,
    })


def send_congratulation_email_with_certificate(request, enrollment, exam, score_percentage, certificate_url=None):
    """
    Send professional congratulatory email with certificate PDF attached.
    Uses the EXISTING view_certificate logic to generate the PDF.
    """
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    
    student = enrollment.student
    course = enrollment.course
    
    subject = f"🎉 Congratulations! You've Completed {course.title}"
    
    # Build email context
    context = {
        'student_name': student.get_full_name(),
        'course_title': course.title,
        'exam_title': exam.title,
        'score': round(score_percentage, 2),
        'passing_score': exam.passing_score,
        'completion_date': timezone.now().strftime('%B %d, %Y'),
        'certificate_url': request.build_absolute_uri(certificate_url) if certificate_url else None,
        'site_url': request.build_absolute_uri('/'),
        'courses_url': request.build_absolute_uri(reverse('frontend:courses')),
    }
    
    # Render HTML email
    html_content = render_to_string('emails/congratulations.html', context)
    
    # Create email
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[student.email],
    )
    email.content_subtype = "html"
    
    # Attach certificate PDF using the EXISTING view_certificate function
    if certificate_url and course.has_certificate:
        try:
            cert_pdf = get_certificate_pdf_bytes(enrollment, request)
            if cert_pdf:
                filename = f"Certificate_{course.slug}_{student.get_full_name().replace(' ', '_')}.pdf"
                email.attach(filename, cert_pdf, 'application/pdf')
        except Exception as e:
            print(f"Error attaching certificate: {e}")
    
    email.send(fail_silently=False)


def get_certificate_pdf_bytes(enrollment, request):
    """
    Generate certificate PDF bytes by reusing the view_certificate logic.
    This does NOT change your existing view_certificate function.
    """
    # Get cert_id
    cert_id = None
    if enrollment.certificate_url:
        parts = enrollment.certificate_url.rstrip('/').split('/')
        for part in parts:
            if part.startswith('CERT-'):
                cert_id = part
                break
    
    if not cert_id:
        cert_string = f"{enrollment.student.id}-{enrollment.course.id}-{timezone.now().timestamp()}"
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
    
    # Handle signatures
    instructor_sig_temp = None
    director_sig_temp = None
    
    # Instructor signature
    instructor = enrollment.course.instructor
    try:
        instructor_profile = InstructorProfile.objects.get(user=instructor)
        if instructor_profile.signature:
            sig_path = instructor_profile.signature.path
            if os.path.exists(sig_path):
                instructor_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                instructor_sig_temp.close()
                convert_signature_to_white(sig_path, instructor_sig_temp.name)
    except InstructorProfile.DoesNotExist:
        pass
    
    # Director signature
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
        except Exception:
            pass
    
    # If no admin signature, try static file
    if not director_sig_temp:
        static_dirs = []
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            static_dirs.append(settings.STATIC_ROOT)
        if hasattr(settings, 'STATICFILES_DIRS'):
            static_dirs.extend(settings.STATICFILES_DIRS)
        
        for static_dir in static_dirs:
            if static_dir:
                test_path = os.path.join(static_dir, 'images', 'director-signature.png')
                if os.path.exists(test_path):
                    try:
                        director_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        director_sig_temp.close()
                        convert_signature_to_white(test_path, director_sig_temp.name)
                        break
                    except Exception:
                        pass
    
    # Director name
    director_name = admin_profile.user.get_full_name() if admin_profile else getattr(settings, 'CERTIFICATE_DIRECTOR_NAME', 'Dr. James Anderson')
    director_title = getattr(settings, 'CERTIFICATE_DIRECTOR_TITLE', 'Program Director')
    
    # Build PDF
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
    
    # Organization
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 65, getattr(settings, 'CERTIFICATE_ORGANIZATION', 'AI GOVERNANCE AUTHORITY'))
    
    # Title
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 115, "CERTIFICATE OF COMPLETION")
    
    # Gold line
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(2)
    c.line(width/2 - 180, height - 130, width/2 + 180, height - 130)
    
    # "This is to certify that"
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 165, "This is to certify that")
    
    # Student name
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 24)
    student_name = enrollment.student.get_full_name()
    c.drawCentredString(width/2, height - 205, student_name)
    
    # "has successfully completed"
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 240, "has successfully completed the course")
    
    # Course title
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 275, enrollment.course.title)
    
    # Date
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 11)
    completed_date = enrollment.completed_at.strftime("%B %d, %Y") if enrollment.completed_at else ""
    c.drawCentredString(width/2, height - 310, f"Completed on: {completed_date}")
    
    # Signatures
    sig_y_line = height - 390
    sig_y_text = height - 410
    sig_y_title = height - 425
    sig_y_image = height - 395
    
    # Instructor signature (Left)
    instructor_sig_box_x = 100
    instructor_sig_box_width = 180
    
    if instructor_sig_temp and os.path.exists(instructor_sig_temp.name):
        try:
            c.drawImage(instructor_sig_temp.name, instructor_sig_box_x + 20, sig_y_image, 
                       width=140, height=55, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    c.line(instructor_sig_box_x, sig_y_line, instructor_sig_box_x + instructor_sig_box_width, sig_y_line)
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_text, instructor.get_full_name())
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_title, "Instructor")
    
    # Director signature (Right)
    director_sig_box_x = width - 280
    director_sig_box_width = 180
    
    if director_sig_temp and os.path.exists(director_sig_temp.name):
        try:
            c.drawImage(director_sig_temp.name, director_sig_box_x + 20, sig_y_image, 
                       width=140, height=55, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    c.line(director_sig_box_x, sig_y_line, director_sig_box_x + director_sig_box_width, sig_y_line)
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_text, director_name)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_title, director_title)
    
    # QR Code
    qr_size = 80
    qr_x = width - qr_size - 55
    qr_y = 55
    
    try:
        c.drawImage(qr_temp.name, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True)
        c.setFont("Helvetica", 7)
        c.setFillColor(HexColor('#64748b'))
        c.drawCentredString(qr_x + qr_size/2, qr_y - 12, "Scan to verify")
    except Exception:
        pass
    
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
            except Exception:
                pass
    
    return pdf