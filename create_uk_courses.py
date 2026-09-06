"""
Create 3 professional UK AI Governance courses with lessons, content, and quizzes
Run: python manage.py shell < create_uk_courses.py
"""

import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.courses.models import (
    Course, CourseCategory, Lesson, LessonContent,
    Quiz, QuizQuestion, QuizAnswer
)

User = get_user_model()

# Get or create instructor
instructor = User.objects.filter(user_type='INSTRUCTOR', is_active=True).first()
if not instructor:
    instructor = User.objects.filter(is_superuser=True).first()
if not instructor:
    instructor = User.objects.first()

print(f"Instructor: {instructor.get_full_name() or instructor.email}")

# Get or create categories
cat_governance, created_gov = CourseCategory.objects.get_or_create(
    slug='ai-governance',
    defaults={
        'name': 'AI Governance',
        'description': 'Courses on AI governance for UK organisations',
        'is_active': True
    }
)

cat_compliance, created_comp = CourseCategory.objects.get_or_create(
    slug='ai-compliance',
    defaults={
        'name': 'AI Compliance',
        'description': 'AI compliance training aligned with UK and EU regulations',
        'is_active': True
    }
)

cat_ethics, created_eth = CourseCategory.objects.get_or_create(
    slug='ai-ethics',
    defaults={
        'name': 'AI Ethics',
        'description': 'Ethical AI development and deployment practices',
        'is_active': True
    }
)

print(f"Categories ready: {cat_governance.name}, {cat_compliance.name}, {cat_ethics.name}")


def create_quiz(lesson, quiz_title, quiz_description, passing_score, questions_data):
    """Create a quiz with questions and answers for a lesson"""
    quiz, created = Quiz.objects.get_or_create(
        lesson=lesson,
        title=quiz_title,
        defaults={
            'description': quiz_description,
            'passing_score': passing_score,
            'allow_retake': True,
            'randomize_questions': False,
            'randomize_answers': False,
            'show_correct_answers': True,
            'is_active': True,
        }
    )
    
    # Clear existing questions if any
    if not created:
        quiz.questions.all().delete()
    
    for q_order, q_data in enumerate(questions_data):
        question = QuizQuestion.objects.create(
            quiz=quiz,
            question_text=q_data['question'],
            question_type='multiple_choice',
            points=1,
            order=q_order + 1,
            explanation=q_data.get('explanation', ''),
            is_active=True,
        )
        
        for a_order, option in enumerate(q_data['options']):
            QuizAnswer.objects.create(
                question=question,
                answer_text=option,
                is_correct=(a_order == q_data['correct_answer']),
                order=a_order + 1,
            )
    
    return quiz


def create_lesson_with_content(course, title, description, content_title, content_text, order, is_preview=True):
    """Create a lesson with text content"""
    lesson = Lesson.objects.create(
        course=course,
        title=title,
        description=description,
        order=order,
        is_published=True
    )
    
    LessonContent.objects.create(
        lesson=lesson,
        content_type='text',
        title=content_title,
        order=1,
        text_content=content_text,
        is_preview=is_preview,
    )
    
    return lesson


# =====================================================
# COURSE 1: AI Governance for UK Organisations
# =====================================================
print("\n" + "=" * 60)
print("Creating Course 1: AI Governance for UK Organisations")
print("=" * 60)

# Delete existing course if it exists (for clean re-creation)
Course.objects.filter(slug='ai-governance-uk-organisations').delete()

course1 = Course.objects.create(
    title='AI Governance for UK Organisations',
    slug='ai-governance-uk-organisations',
    instructor=instructor,
    category=cat_governance,
    short_description='Master AI governance frameworks aligned with UK regulations, ICO guidance, and the EU AI Act.',
    description='<h2>About This Course</h2><p>Comprehensive training on AI governance for UK organisations.</p>',
    level='beginner',
    duration='10 Weeks',
    price=399.00,
    is_free=False,
    has_certificate=True,
    status='published',
    language='English',
    badge='bestseller',
    badge_updated_at=timezone.now(),
)

print(f"Created: {course1.title}")

# Lessons for Course 1
lessons_1 = [
    ('Introduction to AI Governance', 'Understanding AI governance fundamentals.', 'What is AI Governance?', '<h3>What is AI Governance?</h3><p>AI governance refers to frameworks ensuring responsible AI deployment.</p>'),
    ('UK Regulatory Landscape for AI', 'UK regulatory framework for AI.', 'UK AI Regulatory Framework', '<h3>The UK Approach</h3><p>The UK uses a pro-innovation approach relying on existing regulators.</p>'),
    ('The EU AI Act and UK Implications', 'Understanding the EU AI Act.', 'EU AI Act Overview', '<h3>The EU AI Act</h3><p>The world\'s first comprehensive AI regulation.</p>'),
    ('Building an AI Governance Framework', 'Step-by-step framework building.', 'Framework Components', '<h3>Building Your Framework</h3><p>Key components of AI governance frameworks.</p>'),
    ('AI Risk Assessment and Management', 'Risk assessment methodologies.', 'Risk Assessment', '<h3>AI Risk Assessment</h3><p>Identifying and mitigating AI risks.</p>'),
    ('Data Protection and AI (UK GDPR)', 'UK GDPR requirements for AI.', 'UK GDPR and AI', '<h3>UK GDPR Requirements</h3><p>Data protection principles for AI systems.</p>'),
    ('Transparency and Explainability', 'Making AI transparent.', 'Explainable AI', '<h3>Transparency</h3><p>Making AI decisions explainable.</p>'),
    ('Bias, Fairness, and Ethics in AI', 'Identifying AI bias.', 'AI Bias and Fairness', '<h3>Understanding Bias</h3><p>Sources and mitigation of AI bias.</p>'),
    ('AI Governance Implementation', 'Putting governance into practice.', 'Implementation', '<h3>Implementation</h3><p>Successful AI governance implementation.</p>'),
]

for i, (title, desc, ct, ctext) in enumerate(lessons_1):
    lesson = create_lesson_with_content(course1, title, desc, ct, ctext, i + 1, is_preview=True)
    print(f"  Lesson {i+1}: {title}")

# Quiz Lesson for Course 1
quiz_lesson_1 = create_lesson_with_content(
    course1,
    'Module Check-In Quiz',
    'Test your knowledge of AI Governance.',
    'Quiz Instructions',
    '<h3>Module Check-In Quiz</h3><p>Answer all 10 questions. Pass with 70% or higher.</p>',
    len(lessons_1) + 1,
    is_preview=False
)

# Quiz Questions for Course 1
quiz1_questions = [
    {'question': 'Which UK regulator provides guidance on AI and data protection?', 'options': ['FCA', 'ICO', 'Ofcom', 'CMA'], 'correct_answer': 1, 'explanation': 'The ICO provides guidance on AI and data protection.'},
    {'question': 'What approach has the UK taken to AI regulation?', 'options': ['New AI-specific legislation', 'Pro-innovation relying on existing regulators', 'Complete ban on AI', 'Self-regulation only'], 'correct_answer': 1, 'explanation': 'The UK uses a pro-innovation approach.'},
    {'question': 'Which framework is the EU\'s comprehensive AI regulation?', 'options': ['GDPR', 'AI Act', 'Data Protection Act', 'NIS Regulations'], 'correct_answer': 1, 'explanation': 'The EU AI Act is comprehensive AI regulation.'},
    {'question': 'What is the highest risk category under the EU AI Act?', 'options': ['High Risk', 'Limited Risk', 'Unacceptable Risk', 'Minimal Risk'], 'correct_answer': 2, 'explanation': 'Unacceptable Risk AI is banned.'},
    {'question': 'Which UK legislation governs data protection in AI?', 'options': ['UK GDPR', 'Freedom of Information Act', 'Computer Misuse Act', 'Copyright Act'], 'correct_answer': 0, 'explanation': 'UK GDPR governs data protection.'},
    {'question': 'What is a key component of AI governance?', 'options': ['Only technical documentation', 'Clear roles and responsibilities', 'Avoiding all AI use', 'Outsourcing decisions'], 'correct_answer': 1, 'explanation': 'Clear roles are essential.'},
    {'question': 'What does the ICO AI auditing framework help with?', 'options': ['Marketing', 'Assessing AI compliance', 'Building AI', 'Selling data'], 'correct_answer': 1, 'explanation': 'It helps assess AI compliance.'},
    {'question': 'Which principle requires AI to be understandable?', 'options': ['Privacy', 'Transparency', 'Security', 'Efficiency'], 'correct_answer': 1, 'explanation': 'Transparency requires understandability.'},
    {'question': 'What causes AI bias?', 'options': ['Only malicious intent', 'Biased training data', 'Fast processors', 'Cloud computing'], 'correct_answer': 1, 'explanation': 'Biased training data causes AI bias.'},
    {'question': 'What is essential for AI governance success?', 'options': ['Executive sponsorship', 'Avoiding documentation', 'Minimal training', 'Ignoring risks'], 'correct_answer': 0, 'explanation': 'Executive sponsorship is essential.'},
]

quiz1 = create_quiz(quiz_lesson_1, 'AI Governance Check-In Quiz', 'Test your knowledge of AI governance for UK organisations.', 70, quiz1_questions)
print(f"  Quiz created with {quiz1.question_count} questions")


# =====================================================
# COURSE 2: UK AI Compliance Masterclass
# =====================================================
print("\n" + "=" * 60)
print("Creating Course 2: UK AI Compliance Masterclass")
print("=" * 60)

Course.objects.filter(slug='uk-ai-compliance-masterclass').delete()

course2 = Course.objects.create(
    title='UK AI Compliance Masterclass',
    slug='uk-ai-compliance-masterclass',
    instructor=instructor,
    category=cat_compliance,
    short_description='Comprehensive training on UK AI compliance requirements and practical strategies.',
    description='<h2>About This Course</h2><p>In-depth training on AI compliance for UK organisations.</p>',
    level='intermediate',
    duration='8 Weeks',
    price=449.00,
    is_free=False,
    has_certificate=True,
    status='published',
    language='English',
    badge='trending',
    badge_updated_at=timezone.now(),
)

print(f"Created: {course2.title}")

lessons_2 = [
    ('UK AI Compliance Landscape', 'Overview of UK AI compliance.', 'Compliance Overview', '<h3>UK AI Compliance</h3><p>Understanding the compliance landscape.</p>'),
    ('ICO Enforcement and Expectations', 'ICO enforcement trends.', 'ICO Enforcement', '<h3>ICO Enforcement</h3><p>What the ICO expects from organisations.</p>'),
    ('Data Protection Impact Assessments', 'DPIAs for AI systems.', 'DPIA for AI', '<h3>Conducting DPIAs</h3><p>Essential for high-risk AI systems.</p>'),
    ('Algorithmic Auditing', 'AI auditing techniques.', 'AI Auditing', '<h3>Algorithmic Auditing</h3><p>Ensuring AI compliance through auditing.</p>'),
    ('Bias Testing and Fairness', 'Bias detection methods.', 'Bias Detection', '<h3>Testing for Bias</h3><p>Systematic bias testing.</p>'),
    ('Transparency Requirements', 'AI transparency obligations.', 'AI Transparency', '<h3>Transparency Obligations</h3><p>Being transparent about AI use.</p>'),
    ('Incident Response and Reporting', 'Handling AI incidents.', 'Incident Response', '<h3>AI Incident Response</h3><p>Robust incident response plans.</p>'),
    ('Compliance Monitoring', 'Ongoing compliance.', 'Monitoring', '<h3>Ongoing Compliance</h3><p>Continuous monitoring is essential.</p>'),
]

for i, (title, desc, ct, ctext) in enumerate(lessons_2):
    lesson = create_lesson_with_content(course2, title, desc, ct, ctext, i + 1, is_preview=True)
    print(f"  Lesson {i+1}: {title}")

quiz_lesson_2 = create_lesson_with_content(
    course2,
    'Module Check-In Quiz',
    'Test your knowledge of UK AI Compliance.',
    'Quiz Instructions',
    '<h3>Module Check-In Quiz</h3><p>Answer all 10 questions.</p>',
    len(lessons_2) + 1,
    is_preview=False
)

quiz2_questions = [
    {'question': 'Which UK body enforces AI compliance?', 'options': ['FCA', 'ICO', 'Ofcom', 'CMA'], 'correct_answer': 1},
    {'question': 'What does DPIA stand for?', 'options': ['Data Protection Impact Assessment', 'Digital Privacy Investigation Act', 'Data Processing Internal Audit', 'Direct Personal Information Access'], 'correct_answer': 0},
    {'question': 'When should a DPIA be conducted for AI?', 'options': ['Only after a breach', 'For high-risk processing', 'Never', 'Only for large companies'], 'correct_answer': 1},
    {'question': 'What does algorithmic auditing assess?', 'options': ['Code quality only', 'Compliance and fairness', 'Server speed', 'Marketing'], 'correct_answer': 1},
    {'question': 'ICO stance on AI transparency?', 'options': ['Optional', 'Required for high-risk AI', 'Prohibited', 'Only public sector'], 'correct_answer': 1},
    {'question': 'How often should AI compliance be reviewed?', 'options': ['Once', 'Continuously', 'Every 10 years', 'Never'], 'correct_answer': 1},
    {'question': 'AI incident response plan should include?', 'options': ['Only technical fixes', 'Communication and escalation', 'Marketing', 'Budget'], 'correct_answer': 1},
    {'question': 'Who is responsible for AI compliance?', 'options': ['Only CEO', 'Everyone', 'Consultants only', 'No one'], 'correct_answer': 1},
    {'question': 'Key benefit of algorithmic auditing?', 'options': ['Faster processing', 'Identifying bias', 'Reducing costs', 'Avoiding docs'], 'correct_answer': 1},
    {'question': 'Framework for AI compliance monitoring?', 'options': ['ICO AI auditing framework', 'Agile', 'Waterfall', 'Six Sigma'], 'correct_answer': 0},
]

quiz2 = create_quiz(quiz_lesson_2, 'UK AI Compliance Check-In Quiz', 'Test your knowledge of UK AI compliance.', 70, quiz2_questions)
print(f"  Quiz created with {quiz2.question_count} questions")


# =====================================================
# COURSE 3: Responsible AI Development (Free)
# =====================================================
print("\n" + "=" * 60)
print("Creating Course 3: Responsible AI Development")
print("=" * 60)

Course.objects.filter(slug='responsible-ai-development-uk').delete()

course3 = Course.objects.create(
    title='Responsible AI Development in the UK',
    slug='responsible-ai-development-uk',
    instructor=instructor,
    category=cat_ethics,
    short_description='Free introductory course on responsible AI development principles.',
    description='<h2>About This Course</h2><p>Foundation in responsible AI development.</p>',
    level='beginner',
    duration='4 Weeks',
    price=0.00,
    is_free=True,
    has_certificate=False,
    status='published',
    language='English',
    badge='new',
    badge_updated_at=timezone.now(),
)

print(f"Created: {course3.title}")

lessons_3 = [
    ('Introduction to Responsible AI', 'What is responsible AI?', 'Responsible AI', '<h3>What is Responsible AI?</h3><p>Fair, transparent, and accountable AI.</p>'),
    ('UK Ethical AI Guidelines', 'UK AI ethics framework.', 'UK AI Ethics', '<h3>UK Ethical Guidelines</h3><p>Ethical principles for AI.</p>'),
    ('Fairness and Non-Discrimination', 'Ensuring AI fairness.', 'AI Fairness', '<h3>Fairness in AI</h3><p>Ensuring non-discrimination.</p>'),
    ('Transparency and Explainability', 'Building transparent AI.', 'Transparent AI', '<h3>Transparency</h3><p>Making AI understandable.</p>'),
    ('Privacy and Data Protection', 'Privacy in AI development.', 'Privacy', '<h3>Privacy by Design</h3><p>Integrating privacy from start.</p>'),
    ('Accountability and Oversight', 'AI accountability.', 'Accountability', '<h3>Accountability</h3><p>Clear responsibility for AI.</p>'),
    ('Safety and Security', 'AI safety and security.', 'AI Safety', '<h3>Safety and Security</h3><p>Ensuring AI is safe.</p>'),
    ('Human Oversight', 'Human-in-the-loop.', 'Human Oversight', '<h3>Human Oversight</h3><p>Maintaining human control.</p>'),
]

for i, (title, desc, ct, ctext) in enumerate(lessons_3):
    lesson = create_lesson_with_content(course3, title, desc, ct, ctext, i + 1, is_preview=True)
    print(f"  Lesson {i+1}: {title}")

quiz_lesson_3 = create_lesson_with_content(
    course3,
    'Module Check-In Quiz',
    'Test your knowledge of Responsible AI.',
    'Quiz Instructions',
    '<h3>Module Check-In Quiz</h3><p>Answer all 10 questions.</p>',
    len(lessons_3) + 1,
    is_preview=False
)

quiz3_questions = [
    {'question': 'Key principle of responsible AI?', 'options': ['Maximising profit', 'Fairness', 'Avoiding docs', 'Speed'], 'correct_answer': 1},
    {'question': 'Which UK body provides ethical AI guidance?', 'options': ['ICO', 'FCA', 'Both ICO and FCA', 'Neither'], 'correct_answer': 2},
    {'question': 'What does fairness in AI mean?', 'options': ['Equal outcomes', 'Non-discrimination', 'Random decisions', 'Ignoring differences'], 'correct_answer': 1},
    {'question': 'What is explainability?', 'options': ['Faster AI', 'Understanding decisions', 'Hiding algorithms', 'Avoiding docs'], 'correct_answer': 1},
    {'question': 'What is privacy by design?', 'options': ['Adding privacy later', 'Integrating from start', 'Ignoring privacy', 'Outsourcing'], 'correct_answer': 1},
    {'question': 'Who is accountable for AI decisions?', 'options': ['No one', 'The organisation', 'Only developers', 'Only regulators'], 'correct_answer': 1},
    {'question': 'What is human oversight?', 'options': ['Removing humans', 'Maintaining control', 'Full automation', 'Avoiding responsibility'], 'correct_answer': 1},
    {'question': 'What is AI bias?', 'options': ['Always intentional', 'Systematic unfairness', 'Technical feature', 'Impossible to avoid'], 'correct_answer': 1},
    {'question': 'How to reduce AI bias?', 'options': ['Diverse training data', 'Ignore it', 'Remove oversight', 'Speed up'], 'correct_answer': 0},
    {'question': 'What builds trust in AI?', 'options': ['Secrecy', 'Transparency', 'Complexity', 'Avoiding questions'], 'correct_answer': 1},
]

quiz3 = create_quiz(quiz_lesson_3, 'Responsible AI Check-In Quiz', 'Test your knowledge of responsible AI development.', 70, quiz3_questions)
print(f"  Quiz created with {quiz3.question_count} questions")


print("\n" + "=" * 60)
print("ALL COURSES CREATED SUCCESSFULLY")
print("=" * 60)
print(f"\n1. {course1.title} - {course1.price_display} ({course1.total_lessons} lessons)")
print(f"2. {course2.title} - {course2.price_display} ({course2.total_lessons} lessons)")
print(f"3. {course3.title} - {course3.price_display} ({course3.total_lessons} lessons)")