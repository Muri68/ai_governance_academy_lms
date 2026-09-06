from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from apps.courses.models import (
    CourseCategory, Course, Lesson, LessonContent
)
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create sample courses with professional lessons and content'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample courses...')
        
        # Get or create categories
        categories = self.create_categories()
        
        # Get or create an instructor
        instructor = self.get_instructor()
        
        if not instructor:
            self.stdout.write(self.style.ERROR('No instructor found. Please create an instructor first.'))
            return
        
        # Create courses
        self.create_python_course(instructor, categories['programming'])
        self.create_cybersecurity_course(instructor, categories['cybersecurity'])
        self.create_ai_ethics_course(instructor, categories['ai-ethics'])
        self.create_web_dev_course(instructor, categories['programming'])
        
        self.stdout.write(self.style.SUCCESS('Successfully created 4 sample courses with professional content!'))

    def create_categories(self):
        """Create or get course categories"""
        categories_data = [
            {
                'name': 'Programming & Development',
                'slug': 'programming',
                'description': 'Learn programming languages and software development with hands-on projects',
                'icon': 'fas fa-code',
            },
            {
                'name': 'Cybersecurity',
                'slug': 'cybersecurity',
                'description': 'Master cybersecurity skills including threat detection, ethical hacking, and network defense',
                'icon': 'fas fa-shield-alt',
            },
            {
                'name': 'AI & Ethics',
                'slug': 'ai-ethics',
                'description': 'Explore artificial intelligence, machine learning, and ethical technology governance',
                'icon': 'fas fa-brain',
            },
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = CourseCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')
            categories[cat_data['slug']] = category
        
        return categories

    def get_instructor(self):
        """Get or create an instructor user"""
        instructor = CustomUser.objects.filter(user_type='INSTRUCTOR', is_active=True).first()
        
        if not instructor:
            instructor = CustomUser.objects.filter(user_type='ADMIN', is_active=True).first()
            
        if not instructor:
            instructor = CustomUser.objects.create_user(
                email='instructor@aiga.com',
                password='Instructor@123',
                first_name='Dr. Sarah',
                last_name='Chen',
                user_type='INSTRUCTOR',
                is_active=True,
                email_verified=True,
                is_staff=True,
            )
            self.stdout.write(f'  Created instructor: {instructor.email}')
        
        return instructor

    def create_lessons(self, course, lessons_data):
        """Helper method to create lessons and their content"""
        for lesson_data in lessons_data:
            contents_data = lesson_data.pop('contents', [])
            
            # Remove fields that don't belong to Lesson model
            lesson_data.pop('duration_minutes', None)
            
            # Only keep valid Lesson model fields
            valid_lesson_fields = ['title', 'description', 'order', 'is_free_preview', 'is_published']
            lesson_defaults = {k: v for k, v in lesson_data.items() if k in valid_lesson_fields}
            
            lesson, created = Lesson.objects.update_or_create(
                course=course,
                title=lesson_data['title'],
                defaults=lesson_defaults
            )
            
            if created:
                for content_data in contents_data:
                    # Extract quiz_data separately as it's JSON
                    quiz_data = content_data.pop('quiz_data', None)
                    
                    LessonContent.objects.create(
                        lesson=lesson,
                        quiz_data=quiz_data,
                        **content_data
                    )
                self.stdout.write(f'    ✓ Lesson {lesson.order}: {lesson.title} ({len(contents_data)} contents)')
            else:
                self.stdout.write(f'    ⚠ Lesson already exists: {lesson.title}')

    # ==================== PYTHON COURSE ====================
    
    def create_python_course(self, instructor, category):
        """Create Python Programming Masterclass"""
        course, created = Course.objects.get_or_create(
            slug='python-programming-masterclass',
            defaults={
                'title': 'Python Programming Masterclass: From Zero to Hero',
                'instructor': instructor,
                'category': category,
                'description': (
                    'Master Python programming from absolute basics to advanced concepts in this comprehensive masterclass. '
                    'Python is the world\'s most versatile programming language, powering everything from web applications '
                    'to artificial intelligence and data science.\n\n'
                    'This course takes you on a complete journey - from writing your first "Hello, World!" program '
                    'to building real-world applications. You\'ll learn through hands-on coding exercises, '
                    'real-world projects, and expert instruction.\n\n'
                    'By the end of this course, you\'ll have the skills to build web applications, automate tasks, '
                    'analyze data, and pursue careers in software development, data science, or machine learning.'
                ),
                'short_description': 'Master Python from basics to advanced with real-world projects and expert instruction',
                'level': 'beginner',
                'duration': '12 Weeks',
                'language': 'English',
                'price': 49.99,
                'discount_price': 39.99,
                'is_free': False,
                'status': 'published',
                'is_featured': True,
                'has_certificate': True,
                'requirements': 'No prior programming experience required',
                'what_you_learn': 'Python fundamentals, OOP, web development, data analysis, automation',
                'published_at': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(f'\n📘 Created course: {course.title}')
            self.add_python_lessons(course)

    def add_python_lessons(self, course):
        """Add professional Python lessons"""
        lessons_data = [
            {
                'title': 'Getting Started with Python Programming',
                'order': 1,
                'is_free_preview': True,
                'description': 'Learn what Python is, how to set up your development environment, and write your first program.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Introduction to Python and Course Overview',
                        'order': 1,
                        'duration_minutes': 12,
                        'is_preview': True,
                        'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8',
                        'text_content': (
                            'Welcome to Python Programming Masterclass! In this introductory video, you will learn:\n\n'
                            '• What is Python and why it\'s the most popular programming language\n'
                            '• Real-world applications of Python (Instagram, Spotify, Netflix all use Python)\n'
                            '• Course structure and learning path\n'
                            '• How to get the most out of this course\n\n'
                            'Python was created by Guido van Rossum in 1991 and has become the go-to language '
                            'for beginners and experts alike due to its readability and versatility.'
                        ),
                    },
                    {
                        'content_type': 'text',
                        'title': 'Setting Up Your Python Development Environment',
                        'order': 2,
                        'duration_minutes': 15,
                        'text_content': (
                            '<h2>Setting Up Python on Your Computer</h2>\n\n'
                            '<h3>Step 1: Download Python</h3>\n'
                            '<p>Visit <a href="https://python.org/downloads">python.org/downloads</a> and download '
                            'Python 3.11 or later for your operating system.</p>\n\n'
                            '<div class="alert alert-info">\n'
                            '<strong>Important:</strong> During installation on Windows, check the box that says '
                            '<em>"Add Python to PATH"</em>. This allows you to run Python from the command line.\n'
                            '</div>\n\n'
                            '<h3>Step 2: Verify Installation</h3>\n'
                            '<p>Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and type:</p>\n'
                            '<pre><code>python --version\n# Should output: Python 3.11.x</code></pre>\n\n'
                            '<h3>Step 3: Install VS Code</h3>\n'
                            '<p>Download and install <a href="https://code.visualstudio.com">Visual Studio Code</a>, '
                            'the most popular free code editor for Python development.</p>\n\n'
                            '<h3>Step 4: Install Python Extension</h3>\n'
                            '<p>Open VS Code, go to Extensions (Ctrl+Shift+X), and install the "Python" extension by Microsoft.</p>\n\n'
                            '<h3>Step 5: Create Your First Python File</h3>\n'
                            '<p>Create a new file called <code>hello.py</code> and type:</p>\n'
                            '<pre><code>print("Hello, World!")\nprint("Welcome to Python Programming!")</code></pre>\n'
                            '<p>Run it by pressing F5 or typing <code>python hello.py</code> in the terminal.</p>'
                        ),
                    },
                    {
                        'content_type': 'quiz',
                        'title': 'Quick Check: Python Setup',
                        'order': 3,
                        'quiz_data': {
                            'questions': [
                                {
                                    'question': 'What command is used to check Python version?',
                                    'options': ['python -v', 'python --version', 'python version', 'python check'],
                                    'correct': 1
                                },
                                {
                                    'question': 'Which IDE is recommended for Python development?',
                                    'options': ['Notepad', 'VS Code', 'Microsoft Word', 'Photoshop'],
                                    'correct': 1
                                },
                            ]
                        },
                        'passing_score': 70,
                    },
                ]
            },
            {
                'title': 'Python Fundamentals: Variables, Data Types, and Operators',
                'order': 2,
                'description': 'Master Python variables, data types, operators, and type conversion.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Understanding Variables and Data Types in Python',
                        'order': 1,
                        'duration_minutes': 20,
                        'video_url': 'https://www.youtube.com/embed/rfscVS0vtbw',
                        'text_content': (
                            'In this comprehensive lesson, you will master:\n\n'
                            '• Python variables and naming conventions (snake_case)\n'
                            '• Basic data types: int, float, str, bool, NoneType\n'
                            '• Type conversion and type checking with type()\n'
                            '• String operations: concatenation, slicing, formatting\n'
                            '• Numeric operations and math module\n'
                            '• Boolean logic and comparison operators\n\n'
                            'Practice exercises included to reinforce your learning.'
                        ),
                    },
                    {
                        'content_type': 'code',
                        'title': 'Hands-On Practice: Variables and Data Types',
                        'order': 2,
                        'duration_minutes': 25,
                        'text_content': (
                            '# ====================================\n'
                            '# PYTHON VARIABLES AND DATA TYPES\n'
                            '# ====================================\n\n'
                            '# 1. String variables\n'
                            'first_name = "John"\n'
                            'last_name = "Doe"\n'
                            'full_name = f"{first_name} {last_name}"\n'
                            'print(f"Full name: {full_name}")\n\n'
                            '# 2. Numeric variables\n'
                            'age = 28\n'
                            'height_meters = 1.75\n'
                            'weight_kg = 70.5\n'
                            'bmi = weight_kg / (height_meters ** 2)\n'
                            'print(f"BMI: {bmi:.2f}")\n\n'
                            '# 3. Type conversion\n'
                            'num_str = "100"\n'
                            'num_int = int(num_str)\n'
                            'price_float = float("19.99")\n'
                            'print(f"Converted values: {num_int + 50}, {price_float * 2}")\n\n'
                            '# EXERCISES:\n'
                            '# 1. Create variables for your name, age, and city\n'
                            '# 2. Print a sentence using f-strings\n'
                            '# 3. Calculate the area of a circle (π × r²)\n'
                            '# 4. Convert a temperature from Celsius to Fahrenheit'
                        ),
                    },
                    {
                        'content_type': 'quiz',
                        'title': 'Knowledge Check: Python Fundamentals',
                        'order': 3,
                        'quiz_data': {
                            'questions': [
                                {
                                    'question': 'What is the correct way to create a string variable in Python?',
                                    'options': ['string name = "John"', 'name = "John"', 'var name = "John"', 'let name = "John"'],
                                    'correct': 1
                                },
                                {
                                    'question': 'What will be the output of: type(3.14)?',
                                    'options': ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'bool'>"],
                                    'correct': 1
                                },
                                {
                                    'question': 'Which operator is used for exponentiation in Python?',
                                    'options': ['^', '**', '^^', 'exp()'],
                                    'correct': 1
                                },
                            ]
                        },
                        'passing_score': 70,
                    },
                ]
            },
            {
                'title': 'Control Flow: Making Decisions in Code',
                'order': 3,
                'description': 'Master if statements, for loops, while loops, and conditional logic.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'If Statements, Loops, and Conditional Logic',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/DZwmZ8Usvnk',
                        'text_content': (
                            'Master control flow in Python:\n\n'
                            '• if, elif, else statements with practical examples\n'
                            '• Nested conditionals and logical operators (and, or, not)\n'
                            '• for loops with range(), lists, and strings\n'
                            '• while loops and infinite loop prevention\n'
                            '• break, continue, and pass statements\n'
                            '• List comprehensions for concise code\n'
                            '• Real-world example: Building a simple calculator'
                        ),
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Control Flow Exercises',
                        'order': 2,
                        'duration_minutes': 20,
                        'text_content': (
                            '# ====================================\n'
                            '# CONTROL FLOW EXERCISES\n'
                            '# ====================================\n\n'
                            '# Exercise 1: Grade Calculator\n'
                            'score = 85\n'
                            'if score >= 90:\n'
                            '    grade = "A"\n'
                            'elif score >= 80:\n'
                            '    grade = "B"\n'
                            'elif score >= 70:\n'
                            '    grade = "C"\n'
                            'elif score >= 60:\n'
                            '    grade = "D"\n'
                            'else:\n'
                            '    grade = "F"\n'
                            'print(f"Score: {score}, Grade: {grade}")\n\n'
                            '# Exercise 2: FizzBuzz\n'
                            'for num in range(1, 21):\n'
                            '    if num % 3 == 0 and num % 5 == 0:\n'
                            '        print("FizzBuzz")\n'
                            '    elif num % 3 == 0:\n'
                            '        print("Fizz")\n'
                            '    elif num % 5 == 0:\n'
                            '        print("Buzz")\n'
                            '    else:\n'
                            '        print(num)'
                        ),
                    },
                ]
            },
            {
                'title': 'Functions: Writing Reusable Code',
                'order': 4,
                'description': 'Learn to write clean, reusable code with Python functions.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Python Functions and Modular Programming',
                        'order': 1,
                        'duration_minutes': 22,
                        'video_url': 'https://www.youtube.com/embed/9Os0o3wzS_I',
                        'text_content': (
                            'Learn to write clean, reusable code with functions:\n\n'
                            '• Defining functions with def keyword\n'
                            '• Parameters, arguments, and default values\n'
                            '• Return values and multiple returns\n'
                            '• *args and **kwargs for flexible functions\n'
                            '• Lambda functions (anonymous functions)\n'
                            '• Scope rules: local, enclosing, global, built-in\n'
                            '• Docstrings and function documentation'
                        ),
                    },
                    {
                        'content_type': 'assignment',
                        'title': 'Mini-Project: Build a To-Do List Application',
                        'order': 2,
                        'assignment_instructions': (
                            '<h3>Build a Command-Line To-Do List Application</h3>\n\n'
                            '<p>Create a functional to-do list manager using Python functions:</p>\n\n'
                            '<h4>Requirements:</h4>\n'
                            '<ol>\n'
                            '<li>Create functions for: add_task(), view_tasks(), complete_task(), delete_task()</li>\n'
                            '<li>Store tasks in a list of dictionaries</li>\n'
                            '<li>Implement a menu system that loops until user exits</li>\n'
                            '<li>Add input validation</li>\n'
                            '<li>Save tasks to a JSON file</li>\n'
                            '</ol>'
                        ),
                        'max_score': 100,
                    },
                ]
            },
            {
                'title': 'Object-Oriented Programming with Python',
                'order': 5,
                'description': 'Deep dive into OOP: classes, objects, inheritance, and polymorphism.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Mastering OOP: Classes, Objects, and Inheritance',
                        'order': 1,
                        'duration_minutes': 30,
                        'video_url': 'https://www.youtube.com/embed/ZDa-Z5JzLYM',
                        'text_content': (
                            'Deep dive into Object-Oriented Programming in Python:\n\n'
                            '• Classes and Objects: The blueprint and instance concept\n'
                            '• __init__ method and self parameter explained\n'
                            '• Instance variables vs Class variables\n'
                            '• Inheritance and method overriding\n'
                            '• Encapsulation: public, protected, private\n'
                            '• Magic methods (__str__, __repr__, __len__)\n'
                            '• Property decorators (@property)'
                        ),
                    },
                    {
                        'content_type': 'code',
                        'title': 'OOP Practice: Bank Account System',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            '# BANK ACCOUNT SYSTEM - OOP EXAMPLE\n\n'
                            'class BankAccount:\n'
                            '    bank_name = "Python National Bank"\n'
                            '    \n'
                            '    def __init__(self, holder_name, initial_balance=0):\n'
                            '        self.holder_name = holder_name\n'
                            '        self._balance = initial_balance\n'
                            '    \n'
                            '    def deposit(self, amount):\n'
                            '        if amount > 0:\n'
                            '            self._balance += amount\n'
                            '            return True\n'
                            '        return False\n'
                            '    \n'
                            '    def withdraw(self, amount):\n'
                            '        if 0 < amount <= self._balance:\n'
                            '            self._balance -= amount\n'
                            '            return True\n'
                            '        return False\n'
                            '    \n'
                            '    @property\n'
                            '    def balance(self):\n'
                            '        return self._balance\n'
                            '    \n'
                            '    def __str__(self):\n'
                            '        return f"{self.holder_name}: ${self._balance:.2f}"\n\n'
                            'class SavingsAccount(BankAccount):\n'
                            '    interest_rate = 0.025\n'
                            '    \n'
                            '    def apply_interest(self):\n'
                            '        interest = self._balance * self.interest_rate / 12\n'
                            '        self._balance += interest\n'
                            '        return interest\n\n'
                            '# Test the classes\n'
                            'checking = BankAccount("Alice", 1000)\n'
                            'savings = SavingsAccount("Alice", 5000)\n'
                            'checking.deposit(500)\n'
                            'savings.apply_interest()\n'
                            'print(checking)\n'
                            'print(savings)'
                        ),
                    },
                ]
            },
        ]
        
        self.create_lessons(course, lessons_data)

    # ==================== CYBERSECURITY COURSE ====================
    
    def create_cybersecurity_course(self, instructor, category):
        """Create Cybersecurity Professional course"""
        course, created = Course.objects.get_or_create(
            slug='cybersecurity-professional-bootcamp',
            defaults={
                'title': 'Cybersecurity Professional Bootcamp',
                'instructor': instructor,
                'category': category,
                'description': (
                    'Launch your career in cybersecurity with this comprehensive bootcamp. Learn to protect '
                    'organizations from cyber threats through hands-on training in network security, ethical hacking, '
                    'incident response, and security operations.\n\n'
                    'The cybersecurity field is experiencing massive growth with over 3.5 million unfilled positions '
                    'worldwide. This course prepares you for in-demand certifications including CompTIA Security+, '
                    'CEH, and CISSP.'
                ),
                'short_description': 'Complete cybersecurity training: network security, ethical hacking, SOC operations',
                'level': 'intermediate',
                'duration': '16 Weeks',
                'language': 'English',
                'price': 89.99,
                'discount_price': 69.99,
                'is_free': False,
                'status': 'published',
                'is_featured': True,
                'has_certificate': True,
                'requirements': 'Basic understanding of computer networks and operating systems',
                'what_you_learn': 'Network security, ethical hacking, SOC operations, incident response',
                'published_at': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(f'\n🛡️ Created course: {course.title}')
            self.add_cybersecurity_lessons(course)

    def add_cybersecurity_lessons(self, course):
        """Add cybersecurity lessons"""
        lessons_data = [
            {
                'title': 'Introduction to Cybersecurity',
                'order': 1,
                'is_free_preview': True,
                'description': 'Discover the cybersecurity field, career paths, and set up your lab environment.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'The Cybersecurity Landscape in 2024',
                        'order': 1,
                        'duration_minutes': 15,
                        'is_preview': True,
                        'video_url': 'https://www.youtube.com/embed/inWWhr5tnEA',
                        'text_content': (
                            'Discover the cybersecurity field:\n\n'
                            '• Current threat landscape and major breach case studies\n'
                            '• Cybersecurity job roles and career paths\n'
                            '• Salary expectations and certification roadmap\n'
                            '• The CIA Triad: Confidentiality, Integrity, Availability\n'
                            '• Key cybersecurity frameworks and standards'
                        ),
                    },
                    {
                        'content_type': 'text',
                        'title': 'Setting Up Your Cybersecurity Lab',
                        'order': 2,
                        'duration_minutes': 20,
                        'text_content': (
                            '<h2>Building Your Home Cybersecurity Lab</h2>\n\n'
                            '<h3>Required Software:</h3>\n'
                            '<ol>\n'
                            '<li><strong>VirtualBox</strong> - Free virtualization software</li>\n'
                            '<li><strong>Kali Linux VM</strong> - Penetration testing distribution</li>\n'
                            '<li><strong>Metasploitable 2</strong> - Intentionally vulnerable VM for practice</li>\n'
                            '<li><strong>Windows 10 VM</strong> - For testing Windows security</li>\n'
                            '<li><strong>Wireshark</strong> - Network protocol analyzer</li>\n'
                            '<li><strong>Nmap</strong> - Network discovery and security scanning</li>\n'
                            '</ol>\n\n'
                            '<div class="alert alert-warning">\n'
                            '<strong>⚠️ Ethical Notice:</strong> Only use these tools on systems you own '
                            'or have explicit permission to test. Unauthorized hacking is illegal.\n'
                            '</div>'
                        ),
                    },
                ]
            },
            {
                'title': 'Network Security Fundamentals',
                'order': 2,
                'description': 'Master network protocols, security concepts, and scanning techniques.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Understanding Network Protocols and Security',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/keeqnciDVOo',
                        'text_content': (
                            'Master network security concepts:\n\n'
                            '• OSI Model and TCP/IP stack explained\n'
                            '• Common protocols: HTTP/HTTPS, DNS, DHCP, SMTP, FTP\n'
                            '• Network devices: Routers, Switches, Firewalls, IDS/IPS\n'
                            '• Port scanning and service enumeration with Nmap\n'
                            '• Network segmentation and VLANs\n'
                            '• Introduction to firewall rules and ACLs'
                        ),
                    },
                    {
                        'content_type': 'code',
                        'title': 'Lab: Network Scanning with Nmap',
                        'order': 2,
                        'duration_minutes': 25,
                        'text_content': (
                            '# NETWORK SCANNING LAB EXERCISES\n'
                            '# Run in Kali Linux terminal\n\n'
                            '# 1. Basic host discovery\n'
                            'nmap -sn 192.168.1.0/24\n\n'
                            '# 2. Port scanning\n'
                            'nmap -sS -sV 192.168.1.100\n\n'
                            '# 3. OS detection\n'
                            'nmap -O 192.168.1.100\n\n'
                            '# 4. Aggressive scan\n'
                            'nmap -A 192.168.1.100\n\n'
                            '# 5. Save results\n'
                            'nmap -oN scan_results.txt 192.168.1.100'
                        ),
                    },
                ]
            },
            {
                'title': 'Ethical Hacking and Penetration Testing',
                'order': 3,
                'description': 'Learn professional penetration testing methodology and tools.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Penetration Testing Methodology',
                        'order': 1,
                        'duration_minutes': 30,
                        'video_url': 'https://www.youtube.com/embed/3Kq1MIfTWCE',
                        'text_content': (
                            'Learn professional penetration testing:\n\n'
                            '• Reconnaissance: Passive and active information gathering\n'
                            '• Scanning and enumeration techniques\n'
                            '• Vulnerability assessment with Nessus and OpenVAS\n'
                            '• Exploitation basics with Metasploit Framework\n'
                            '• Post-exploitation and maintaining access\n'
                            '• Writing professional penetration test reports'
                        ),
                    },
                ]
            },
            {
                'title': 'Security Operations Center (SOC)',
                'order': 4,
                'description': 'Become a skilled SOC Analyst with monitoring and detection skills.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'SOC Analyst: Monitoring and Detection',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/1lYmevNdePg',
                        'text_content': (
                            'Become a skilled SOC Analyst:\n\n'
                            '• SOC roles: Tier 1, Tier 2, Tier 3 analysts\n'
                            '• Security monitoring tools and dashboards\n'
                            '• Log analysis and correlation techniques\n'
                            '• Creating SIEM rules and alerts\n'
                            '• Investigating and triaging security events\n'
                            '• Escalation procedures and incident classification'
                        ),
                    },
                ]
            },
            {
                'title': 'Incident Response and Digital Forensics',
                'order': 5,
                'description': 'Master the incident response lifecycle and forensic techniques.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Incident Response Lifecycle',
                        'order': 1,
                        'duration_minutes': 28,
                        'video_url': 'https://www.youtube.com/embed/AvN1p-uZKxU',
                        'text_content': (
                            'Master incident response:\n\n'
                            '• Preparation: Building an IR team and plan\n'
                            '• Identification: Detecting and confirming incidents\n'
                            '• Containment: Short-term and long-term strategies\n'
                            '• Eradication: Removing threats from the environment\n'
                            '• Recovery: Restoring systems and services\n'
                            '• Lessons Learned: Post-incident review and improvement'
                        ),
                    },
                ]
            },
        ]
        
        self.create_lessons(course, lessons_data)

    # ==================== AI ETHICS COURSE ====================
    
    def create_ai_ethics_course(self, instructor, category):
        """Create AI Ethics & Governance course"""
        course, created = Course.objects.get_or_create(
            slug='ai-ethics-and-governance-framework',
            defaults={
                'title': 'AI Ethics & Governance Framework',
                'instructor': instructor,
                'category': category,
                'description': (
                    'Navigate the complex intersection of artificial intelligence, ethics, and governance. '
                    'As AI systems become more powerful and pervasive, organizations urgently need professionals '
                    'who can ensure these technologies are developed and deployed responsibly.\n\n'
                    'This course covers AI ethics principles, bias detection and mitigation, regulatory compliance '
                    '(GDPR, EU AI Act), and governance frameworks used by leading tech companies and governments.'
                ),
                'short_description': 'Master AI ethics, bias detection, and governance for responsible AI development',
                'level': 'intermediate',
                'duration': '8 Weeks',
                'language': 'English',
                'price': 0.00,
                'is_free': True,
                'status': 'published',
                'is_featured': True,
                'has_certificate': True,
                'requirements': 'Basic understanding of AI/ML concepts',
                'what_you_learn': 'AI ethics principles, bias detection, governance frameworks, regulatory compliance',
                'published_at': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(f'\n🤖 Created course: {course.title}')
            self.add_ai_ethics_lessons(course)

    def add_ai_ethics_lessons(self, course):
        """Add AI Ethics lessons"""
        lessons_data = [
            {
                'title': 'Why AI Ethics Matters',
                'order': 1,
                'is_free_preview': True,
                'description': 'Understanding the critical importance of ethics in AI development.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'The Ethical Imperative in AI Development',
                        'order': 1,
                        'duration_minutes': 18,
                        'is_preview': True,
                        'video_url': 'https://www.youtube.com/embed/aGwYtUzMQUk',
                        'text_content': (
                            'Understanding the critical importance of AI ethics:\n\n'
                            '• Famous AI failures: Amazon biased hiring, COMPAS recidivism\n'
                            '• The societal impact of unchecked AI deployment\n'
                            '• Why diverse teams build better AI\n'
                            '• The business case for ethical AI\n'
                            '• Introduction to key ethical frameworks'
                        ),
                    },
                    {
                        'content_type': 'text',
                        'title': 'Foundational Principles of AI Ethics',
                        'order': 2,
                        'duration_minutes': 15,
                        'text_content': (
                            '<h2>The Five Pillars of AI Ethics</h2>\n\n'
                            '<h3>1. Fairness and Non-Discrimination</h3>\n'
                            '<p>AI systems must treat all individuals equitably.</p>\n\n'
                            '<h3>2. Transparency and Explainability</h3>\n'
                            '<p>AI decisions should be explainable to affected individuals.</p>\n\n'
                            '<h3>3. Accountability</h3>\n'
                            '<p>Clear lines of responsibility must exist for AI outcomes.</p>\n\n'
                            '<h3>4. Privacy and Data Protection</h3>\n'
                            '<p>AI systems must respect individual privacy rights.</p>\n\n'
                            '<h3>5. Human Oversight</h3>\n'
                            '<p>Critical decisions should involve meaningful human review.</p>'
                        ),
                    },
                ]
            },
            {
                'title': 'Understanding and Detecting AI Bias',
                'order': 2,
                'description': 'Deep dive into AI bias types and detection methods.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Types of Bias in Machine Learning',
                        'order': 1,
                        'duration_minutes': 22,
                        'video_url': 'https://www.youtube.com/embed/59bMh59JQDo',
                        'text_content': (
                            'Deep dive into AI bias:\n\n'
                            '• Data bias: Sampling, measurement, and historical bias\n'
                            '• Algorithmic bias: How algorithms amplify existing biases\n'
                            '• Societal bias: Reflecting social inequalities\n'
                            '• Fairness metrics: Demographic parity, equal opportunity\n'
                            '• Tools: IBM AI Fairness 360, Google What-If Tool'
                        ),
                    },
                ]
            },
            {
                'title': 'AI Governance Frameworks',
                'order': 3,
                'description': 'Learn to implement AI governance in organizations.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Building Effective AI Governance',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/6ryNnL2G0qI',
                        'text_content': (
                            'Learn to implement AI governance:\n\n'
                            '• Google AI Principles and review process\n'
                            '• Microsoft Responsible AI framework\n'
                            '• OECD AI Principles\n'
                            '• NIST AI Risk Management Framework\n'
                            '• Creating an AI ethics board\n'
                            '• Algorithmic impact assessments'
                        ),
                    },
                ]
            },
            {
                'title': 'AI Regulations and Compliance',
                'order': 4,
                'description': 'Navigate global AI regulations and compliance requirements.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Global AI Regulations: GDPR, EU AI Act',
                        'order': 1,
                        'duration_minutes': 28,
                        'video_url': 'https://www.youtube.com/embed/5LZ3ajcR8Jk',
                        'text_content': (
                            'Navigate the regulatory landscape:\n\n'
                            '• GDPR and automated decision-making (Article 22)\n'
                            '• EU AI Act: Risk-based approach to AI regulation\n'
                            '• US Executive Order on AI\n'
                            '• Industry-specific regulations\n'
                            '• Compliance strategies for organizations'
                        ),
                    },
                ]
            },
            {
                'title': 'Building Responsible AI Systems',
                'order': 5,
                'description': 'Apply ethics principles to build responsible AI systems.',
                'contents': [
                    {
                        'content_type': 'assignment',
                        'title': 'Final Project: AI Ethics Audit',
                        'order': 1,
                        'assignment_instructions': (
                            '<h3>Conduct an AI Ethics Audit</h3>\n\n'
                            '<p>Choose a real or hypothetical AI system and perform a comprehensive ethics audit:</p>\n\n'
                            '<h4>Deliverables:</h4>\n'
                            '<ol>\n'
                            '<li><strong>System Description</strong>: What does the AI system do?</li>\n'
                            '<li><strong>Stakeholder Analysis</strong>: Identify all affected parties</li>\n'
                            '<li><strong>Bias Assessment</strong>: Potential biases in data and algorithm</li>\n'
                            '<li><strong>Fairness Evaluation</strong>: Which fairness metrics apply?</li>\n'
                            '<li><strong>Privacy Impact</strong>: Data collection and usage analysis</li>\n'
                            '<li><strong>Transparency Report</strong>: How explainable is the system?</li>\n'
                            '<li><strong>Governance Recommendations</strong>: Proposed oversight mechanisms</li>\n'
                            '<li><strong>Regulatory Compliance Checklist</strong>: Applicable laws and standards</li>\n'
                            '</ol>'
                        ),
                        'max_score': 100,
                    },
                ]
            },
        ]
        
        self.create_lessons(course, lessons_data)

    # ==================== WEB DEVELOPMENT COURSE ====================
    
    def create_web_dev_course(self, instructor, category):
        """Create Web Development course"""
        course, created = Course.objects.get_or_create(
            slug='full-stack-web-development',
            defaults={
                'title': 'Full Stack Web Development with Django',
                'instructor': instructor,
                'category': category,
                'description': (
                    'Build modern, production-ready web applications with Django, the web framework '
                    'for perfectionists with deadlines. This course takes you from HTML basics to '
                    'deploying full-stack applications with Django, PostgreSQL, and Docker.'
                ),
                'short_description': 'Build professional web applications with Django and modern frontend',
                'level': 'beginner',
                'duration': '14 Weeks',
                'language': 'English',
                'price': 59.99,
                'discount_price': 44.99,
                'is_free': False,
                'status': 'published',
                'is_featured': False,
                'has_certificate': True,
                'requirements': 'Basic Python knowledge (variables, functions, loops)',
                'what_you_learn': 'HTML5, CSS3, JavaScript, Django, PostgreSQL, REST APIs',
                'published_at': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(f'\n🌐 Created course: {course.title}')
            self.add_web_dev_lessons(course)

    def add_web_dev_lessons(self, course):
        """Add web development lessons"""
        lessons_data = [
            {
                'title': 'HTML5 Fundamentals',
                'order': 1,
                'is_free_preview': True,
                'description': 'Learn modern HTML5 semantic markup and structure.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Building Your First Web Pages with HTML5',
                        'order': 1,
                        'duration_minutes': 20,
                        'is_preview': True,
                        'video_url': 'https://www.youtube.com/embed/qz0aGYrrlhU',
                        'text_content': (
                            'Learn modern HTML5:\n\n'
                            '• HTML document structure and semantic elements\n'
                            '• Headings, paragraphs, lists, links, and images\n'
                            '• Forms and input types\n'
                            '• Tables and data presentation\n'
                            '• Multimedia: video and audio elements\n'
                            '• Accessibility basics\n'
                            '• SEO-friendly HTML practices'
                        ),
                    },
                ]
            },
            {
                'title': 'CSS3 and Modern Styling',
                'order': 2,
                'description': 'Master CSS3, Flexbox, Grid, and responsive design.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'CSS3: From Basics to Flexbox and Grid',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/1Rs2ND1ryYc',
                        'text_content': (
                            'Master CSS3 styling:\n\n'
                            '• Selectors, properties, and the cascade\n'
                            '• Box model: margin, padding, border\n'
                            '• Flexbox for one-dimensional layouts\n'
                            '• CSS Grid for two-dimensional layouts\n'
                            '• Responsive design with media queries\n'
                            '• CSS variables and custom properties\n'
                            '• Animations and transitions\n'
                            '• Bootstrap 5 framework overview'
                        ),
                    },
                ]
            },
            {
                'title': 'JavaScript Essentials',
                'order': 3,
                'description': 'Learn JavaScript for interactive web development.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'JavaScript for Web Developers',
                        'order': 1,
                        'duration_minutes': 28,
                        'video_url': 'https://www.youtube.com/embed/W6NZfCO5SIk',
                        'text_content': (
                            'Learn JavaScript for web development:\n\n'
                            '• Variables, functions, and control flow\n'
                            '• DOM manipulation and event handling\n'
                            '• Fetch API for AJAX requests\n'
                            '• ES6+ features: arrow functions, destructuring\n'
                            '• Form validation with JavaScript\n'
                            '• Local storage and session storage'
                        ),
                    },
                ]
            },
            {
                'title': 'Getting Started with Django',
                'order': 4,
                'description': 'Set up Django and understand MVT architecture.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Django Project Setup and MVT Architecture',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/rHux0gMZ3Eg',
                        'text_content': (
                            'Begin your Django journey:\n\n'
                            '• Installing Django and creating your first project\n'
                            '• Understanding MVT (Model-View-Template) architecture\n'
                            '• URL routing and view functions\n'
                            '• Django templates and template inheritance\n'
                            '• Static files management\n'
                            '• Django admin interface customization'
                        ),
                    },
                ]
            },
        ]
        
        self.create_lessons(course, lessons_data)