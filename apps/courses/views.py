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

from .models import (
    Course, Lesson, LessonContent, Enrollment, 
    LessonProgress, CourseReview
)

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import HexColor


# ===================== COURSE LEARNING =====================

@login_required
def course_learning(request, course_slug):
    """Main course learning page"""
    course = get_object_or_404(
        Course.objects.prefetch_related('lessons__contents'),
        slug=course_slug,
        status='published'
    )
    
    # Get or create enrollment (no duplicates)
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
    
    # Get lesson contents
    lesson_contents = []
    if current_lesson:
        lesson_contents = current_lesson.contents.all().order_by('order')
    
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
    
    # Previous and next
    prev_lesson = None
    next_lesson = None
    if current_lesson and lessons.exists():
        lesson_list = list(lessons)
        try:
            idx = lesson_list.index(current_lesson)
            if idx > 0: prev_lesson = lesson_list[idx - 1]
            if idx < len(lesson_list) - 1: next_lesson = lesson_list[idx + 1]
        except ValueError:
            pass
    
    context = {
        'course': course, 'enrollment': enrollment, 'lessons': lessons,
        'current_lesson': current_lesson, 'lesson_contents': lesson_contents,
        'lesson_progress': lesson_progress, 'completed_lesson_ids': completed_lesson_ids,
        'prev_lesson': prev_lesson, 'next_lesson': next_lesson,
        'progress_percentage': progress_percentage,
        'completed_lessons': completed_lessons, 'total_lessons': total_lessons,
    }
    return render(request, 'courses/learning.html', context)


# ===================== LESSON ACTIONS =====================

@login_required
def mark_lesson_complete(request, course_slug, lesson_id):
    """
    AJAX endpoint to mark a lesson as complete.
    Enforces sequential completion - cannot skip lessons.
    Auto-completes enrollment when all lessons are done.
    """
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
    
    # ===== CHECK SEQUENTIAL ORDER =====
    # Get all published lessons ordered by their order field
    all_lessons = list(course.lessons.filter(is_published=True).order_by('order'))
    current_lesson_index = None
    
    # Find the current lesson's position
    for i, les in enumerate(all_lessons):
        if les.id == lesson.id:
            current_lesson_index = i
            break
    
    # If toggling OFF (uncompleting), allow it regardless of order
    progress = LessonProgress.objects.filter(
        student=request.user, lesson=lesson, enrollment=enrollment
    ).first()
    
    is_uncompleting = progress and progress.completed
    
    if not is_uncompleting and current_lesson_index is not None and current_lesson_index > 0:
        # Check if ALL previous lessons are completed
        previous_lessons = all_lessons[:current_lesson_index]
        incomplete_previous = []
        
        for prev_lesson in previous_lessons:
            prev_progress = LessonProgress.objects.filter(
                student=request.user,
                lesson=prev_lesson,
                enrollment=enrollment,
                completed=True
            ).first()
            if not prev_progress:
                incomplete_previous.append({
                    'id': prev_lesson.id,
                    'title': prev_lesson.title,
                    'order': prev_lesson.order
                })
        
        if incomplete_previous:
            # Build error message with links to incomplete lessons
            lesson_names = [f'"{l["title"]}"' for l in incomplete_previous[:3]]
            if len(incomplete_previous) > 3:
                lesson_names.append(f'and {len(incomplete_previous) - 3} more')
            
            return JsonResponse({
                'status': 'error',
                'message': f'You must complete the following lessons first: {", ".join(lesson_names)}.',
                'incomplete_lessons': incomplete_previous,
                'code': 'SEQUENTIAL_REQUIRED'
            }, status=400)
    
    # ===== TOGGLE COMPLETION =====
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
    
    # ===== RECALCULATE PROGRESS =====
    total_lessons = len(all_lessons)
    completed_lessons = LessonProgress.objects.filter(
        student=request.user, enrollment=enrollment, completed=True
    ).count()
    
    if total_lessons > 0:
        enrollment.progress_percentage = int((completed_lessons / total_lessons) * 100)
    
    # ===== AUTO-COMPLETE COURSE =====
    course_completed = False
    if enrollment.progress_percentage >= 100 and enrollment.status == 'active':
        enrollment.status = 'completed'
        enrollment.completed_at = timezone.now()
        
        cert_string = f"{request.user.id}-{course.id}-{timezone.now().timestamp()}"
        cert_hash = hashlib.md5(cert_string.encode()).hexdigest()[:12].upper()
        cert_id = f"CERT-{cert_hash}"
        
        enrollment.certificate_url = reverse('courses:verify_certificate', kwargs={'cert_id': cert_id})
        enrollment.certificate_issued = True
        course_completed = True
    
    enrollment.save()
    
    # Update student profile
    if hasattr(request.user, 'student_profile'):
        p = request.user.student_profile
        p.courses_enrolled = Enrollment.objects.filter(student=request.user, status='active').count()
        p.completed_courses = Enrollment.objects.filter(student=request.user, status='completed').count()
        p.save()
    
    # ===== FIND NEXT UNLOCKED LESSON =====
    next_lesson = None
    if progress.completed and current_lesson_index is not None:
        # Find the next lesson that is not completed
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
        response_data['message'] = f'Congratulations! You have completed "{course.title}"!'
        response_data['certificate_url'] = reverse('courses:view_certificate', kwargs={'enrollment_id': enrollment.id})
    
    return JsonResponse(response_data)


@login_required
def save_lesson_notes(request, course_slug, lesson_id):
    """AJAX: Save lesson notes"""
    if request.method == 'POST':
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
    return JsonResponse({'status': 'error'}, status=400)


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
    content_type = 'application/octet-stream'
    
    if content.content_type == 'pdf' and content.pdf_file:
        file_field = content.pdf_file
        content_type = 'application/pdf'
    elif content.content_type == 'video' and content.video_file:
        file_field = content.video_file
        # Detect video mime type
        file_ext = os.path.splitext(content.video_file.name)[1].lower()
        if file_ext == '.mp4':
            content_type = 'video/mp4'
        elif file_ext == '.webm':
            content_type = 'video/webm'
        elif file_ext == '.ogg':
            content_type = 'video/ogg'
        else:
            content_type = 'video/mp4'
    elif content.content_type == 'slides' and content.pdf_file:
        file_field = content.pdf_file
        content_type = 'application/pdf'
    
    if file_field:
        try:
            # Open the file
            file_handle = file_field.open('rb')
            
            # Create response
            response = FileResponse(file_handle, content_type=content_type)
            
            # Get the original filename
            filename = os.path.basename(file_field.name)
            
            # URL encode the filename for proper handling of special characters
            from urllib.parse import quote
            encoded_filename = quote(filename)
            
            # Check if download is requested
            download = request.GET.get('download', '')
            
            # Set Content-Disposition based on file type and request
            if download:
                # Force download
                response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            elif content_type == 'application/pdf':
                # Always try to display PDF inline
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            elif content_type.startswith('video/'):
                # Videos should play inline
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            else:
                # Default to inline
                response['Content-Disposition'] = f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            # Security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Cache control for better performance
            response['Cache-Control'] = 'public, max-age=3600, must-revalidate'
            response['Accept-Ranges'] = 'bytes'
            
            # For PDF files, add additional headers to ensure inline display
            if content_type == 'application/pdf':
                response['Content-Transfer-Encoding'] = 'binary'
                response['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'; object-src 'self'"
            
            return response
            
        except FileNotFoundError:
            raise Http404("File not found on server")
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error serving file: {str(e)}")
            raise Http404("Error serving file")
    
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

import qrcode
from PIL import Image, ImageOps, ImageFilter
from reportlab.lib.utils import ImageReader
from django.core.files.base import ContentFile
import tempfile
import os


def convert_signature_to_white(signature_path, output_path):
    """
    Convert a signature image to white color for dark backgrounds.
    Handles green, blue, black, or any color pen.
    """
    try:
        img = Image.open(signature_path).convert('RGBA')
        
        # Make the image white while preserving transparency
        data = img.getdata()
        new_data = []
        
        for item in data:
            r, g, b, a = item
            
            # If pixel is not transparent (has some opacity)
            if a > 50:
                # Calculate brightness - if it's dark enough (signature ink)
                brightness = (r + g + b) / 3
                if brightness < 200:  # This is part of the signature
                    # Convert to white, keep alpha
                    new_data.append((255, 255, 255, a))
                else:
                    # Background/noise - make transparent
                    new_data.append((255, 255, 255, 0))
            else:
                # Fully transparent
                new_data.append((255, 255, 255, 0))
        
        img.putdata(new_data)
        img.save(output_path, 'PNG')
        return output_path
    except Exception as e:
        print(f"Error converting signature: {e}")
        return signature_path  # Return original if conversion fails


@login_required
def view_certificate(request, enrollment_id):
    """Generate and download PDF certificate with QR code and signatures"""
    enrollment = get_object_or_404(
        Enrollment.objects.select_related('course', 'student', 'course__instructor__instructor_profile'),
        id=enrollment_id, student=request.user, status='completed'
    )
    
    # Get cert_id from stored URL
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
    
    # ===== GENERATE QR CODE =====
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="white", back_color="#0c1e2e")  # White QR on dark background
    
    qr_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    qr_img.save(qr_temp.name)
    qr_temp.close()
    
    # ===== PREPARE SIGNATURES (Convert to white) =====
    instructor_sig_temp = None
    director_sig_temp = None
    
    instructor = enrollment.course.instructor
    instructor_profile = getattr(instructor, 'instructor_profile', None)
    
    # Convert instructor signature to white
    if instructor_profile and instructor_profile.signature:
        try:
            sig_path = instructor_profile.signature.path
            if os.path.exists(sig_path):
                instructor_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                instructor_sig_temp.close()
                convert_signature_to_white(sig_path, instructor_sig_temp.name)
        except Exception:
            instructor_sig_temp = None
    
    # Convert director signature to white
    director_sig_path = None
    static_dirs = [settings.STATIC_ROOT] if settings.STATIC_ROOT else []
    if hasattr(settings, 'STATICFILES_DIRS'):
        static_dirs.extend(settings.STATICFILES_DIRS)
    
    for static_dir in static_dirs:
        if static_dir:
            test_path = os.path.join(static_dir, 'images', 'director-signature.png')
            if os.path.exists(test_path):
                director_sig_path = test_path
                break
    
    if director_sig_path and os.path.exists(director_sig_path):
        try:
            director_sig_temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            director_sig_temp.close()
            convert_signature_to_white(director_sig_path, director_sig_temp.name)
        except Exception:
            director_sig_temp = None
    
    # ===== BUILD PDF =====
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)  # 792 x 612
    
    # Background
    c.setFillColor(HexColor('#0c1e2e'))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Gold outer border
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(3)
    c.rect(25, 25, width - 50, height - 50, fill=False, stroke=True)
    
    # Gold inner border
    c.setLineWidth(1)
    c.rect(38, 38, width - 76, height - 76, fill=False, stroke=True)
    
    # Organization at top
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 65, getattr(settings, 'CERTIFICATE_ORGANIZATION', 'AI GOVERNANCE AUTHORITY'))
    
    # Certificate title
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 115, "CERTIFICATE OF COMPLETION")
    
    # Decorative line under title
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(2)
    c.line(width/2 - 180, height - 130, width/2 + 180, height - 130)
    
    # "This is to certify that"
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 165, "This is to certify that")
    
    # Student name (highlighted)
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 24)
    student_name = enrollment.student.get_full_name()
    c.drawCentredString(width/2, height - 205, student_name)
    
    # "has successfully completed"
    c.setFillColor(HexColor('#cbd5e1'))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height - 240, "has successfully completed the course")
    
    # Course name (highlighted)
    c.setFillColor(HexColor('#ad7a49'))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 275, enrollment.course.title)
    
    # Date
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont("Helvetica", 11)
    completed_date = enrollment.completed_at.strftime("%B %d, %Y") if enrollment.completed_at else ""
    c.drawCentredString(width/2, height - 310, f"Completed on: {completed_date}")
    
    # ===== SIGNATURES (Bottom area) =====
    sig_y_line = height - 390  # Y position for signature lines
    sig_y_text = height - 410  # Y position for name text
    sig_y_title = height - 425  # Y position for title text
    sig_y_image = height - 395  # Y position for signature images
    
    c.setStrokeColor(HexColor('#ad7a49'))
    c.setLineWidth(1)
    
    # --- Instructor Signature (Left side) ---
    instructor_sig_box_x = 100  # Left position
    instructor_sig_box_width = 180
    
    # Draw signature image if available
    sig_drawn = False
    if instructor_sig_temp and os.path.exists(instructor_sig_temp.name):
        try:
            c.drawImage(
                instructor_sig_temp.name,
                instructor_sig_box_x + 20,  # Centered in box
                sig_y_image,
                width=140,
                height=55,
                preserveAspectRatio=True,
                mask='auto'
            )
            sig_drawn = True
        except Exception:
            pass
    
    # Signature line
    c.line(instructor_sig_box_x, sig_y_line, instructor_sig_box_x + instructor_sig_box_width, sig_y_line)
    
    # Name
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_text, instructor.get_full_name())
    
    # Title
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(instructor_sig_box_x + instructor_sig_box_width/2, sig_y_title, "Instructor")
    
    # --- Director Signature (Right side) ---
    director_sig_box_x = width - 280  # Right position
    director_sig_box_width = 180
    
    director_name = getattr(settings, 'CERTIFICATE_DIRECTOR_NAME', 'Dr. James Anderson')
    director_title = getattr(settings, 'CERTIFICATE_DIRECTOR_TITLE', 'Program Director')
    
    # Draw director signature image if available
    if director_sig_temp and os.path.exists(director_sig_temp.name):
        try:
            c.drawImage(
                director_sig_temp.name,
                director_sig_box_x + 20,
                sig_y_image,
                width=140,
                height=55,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass
    
    # Signature line
    c.line(director_sig_box_x, sig_y_line, director_sig_box_x + director_sig_box_width, sig_y_line)
    
    # Name
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#ffffff'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_text, director_name)
    
    # Title
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#94a3b8'))
    c.drawCentredString(director_sig_box_x + director_sig_box_width/2, sig_y_title, director_title)
    
    # ===== QR CODE (Bottom Right Corner) =====
    qr_size = 80
    qr_x = width - qr_size - 55
    qr_y = 55
    
    try:
        c.drawImage(
            qr_temp.name,
            qr_x, qr_y,
            width=qr_size, height=qr_size,
            preserveAspectRatio=True
        )
        # QR Label
        c.setFont("Helvetica", 7)
        c.setFillColor(HexColor('#64748b'))
        c.drawCentredString(qr_x + qr_size/2, qr_y - 12, "Scan to verify")
    except Exception:
        pass
    
    # ===== BOTTOM TEXT =====
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
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Certificate_{enrollment.course.slug}_{student_name.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def verify_certificate(request, cert_id):
    """Public certificate verification"""
    verified = False
    enrollment = None
    
    # Find enrollment by certificate_url containing this cert_id
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