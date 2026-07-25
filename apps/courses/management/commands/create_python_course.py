from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import CourseCategory, Course, Lesson, LessonContent
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create complete Python Programming Masterclass with all lessons and content'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating Python Programming Masterclass...')
        
        # Get or create category
        category, _ = CourseCategory.objects.get_or_create(
            slug='programming',
            defaults={
                'name': 'Programming & Development',
                'description': 'Learn programming languages and software development',
                'icon': 'fas fa-code',
            }
        )
        
        # Get or create instructor
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
            )
            self.stdout.write(f'  Created instructor: {instructor.email}')
        
        # Create the course
        course, created = Course.objects.update_or_create(
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
                'requirements': (
                    '• No prior programming experience required\n'
                    '• A computer (Windows, Mac, or Linux) with internet connection\n'
                    '• Willingness to learn and practice regularly\n'
                    '• Basic computer literacy'
                ),
                'what_you_learn': (
                    '• Python fundamentals: variables, data types, operators, and control flow\n'
                    '• Functions, modules, and packages for organized code\n'
                    '• Object-Oriented Programming (OOP) with classes and inheritance\n'
                    '• File handling, JSON, and working with external data\n'
                    '• Error handling and debugging techniques\n'
                    '• Web scraping with BeautifulSoup and Requests\n'
                    '• Building REST APIs with Flask\n'
                    '• Database management with SQLite and SQLAlchemy\n'
                    '• Introduction to data analysis with Pandas\n'
                    '• Automation scripts for everyday tasks\n'
                    '• Git version control and collaborative development\n'
                    '• Deploying Python applications to production'
                ),
                'published_at': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(f'Created course: {course.title}')
        else:
            self.stdout.write(f'Updated course: {course.title}')
        
        # Create all lessons
        self.create_all_lessons(course)
        
        self.stdout.write(self.style.SUCCESS('Python Programming Masterclass created successfully!'))

    def create_all_lessons(self, course):
        """Create all 12 lessons with complete content"""
        
        lessons = [
            # ========== LESSON 1: Getting Started ==========
            {
                'title': 'Getting Started with Python Programming',
                'order': 1,
                'is_free_preview': True,
                'description': 'Set up your Python development environment and write your first program.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Welcome to Python Programming',
                        'order': 1,
                        'duration_minutes': 12,
                        'is_preview': True,
                        'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8',
                        'text_content': 'Introduction to Python, course overview, and what you will learn.',
                    },
                    {
                        'content_type': 'text',
                        'title': 'Installing Python and Setting Up Your IDE',
                        'order': 2,
                        'duration_minutes': 20,
                        'text_content': (
                            '<h2>Setting Up Python on Your Computer</h2>\n\n'
                            '<h3>Step 1: Download Python</h3>\n'
                            '<p>Visit <a href="https://python.org/downloads" target="_blank">python.org/downloads</a> '
                            'and download Python 3.11 or later for your operating system.</p>\n\n'
                            '<div style="background:#dbeafe;padding:15px;border-radius:8px;margin:15px 0;">\n'
                            '<strong>⚠️ Important:</strong> On Windows, check <em>"Add Python to PATH"</em> during installation.\n'
                            '</div>\n\n'
                            '<h3>Step 2: Verify Installation</h3>\n'
                            '<p>Open terminal/command prompt and type:</p>\n'
                            '<pre><code>python --version\n# Output: Python 3.11.x</code></pre>\n\n'
                            '<h3>Step 3: Install Visual Studio Code</h3>\n'
                            '<p>Download from <a href="https://code.visualstudio.com" target="_blank">code.visualstudio.com</a></p>\n'
                            '<p>Install the Python extension by Microsoft from the Extensions panel (Ctrl+Shift+X).</p>\n\n'
                            '<h3>Step 4: Create Your First Python File</h3>\n'
                            '<p>Create <code>hello.py</code>:</p>\n'
                            '<pre><code>print("Hello, World!")\nprint("I\'m learning Python!")</code></pre>\n'
                            '<p>Run with: <code>python hello.py</code></p>'
                        ),
                    },
                    {
                        'content_type': 'quiz',
                        'title': 'Quick Check: Environment Setup',
                        'order': 3,
                        'quiz_data': {
                            'questions': [
                                {
                                    'question': 'Which command checks your Python version?',
                                    'options': ['python -v', 'python --version', 'python check', 'python info'],
                                    'correct': 1
                                },
                                {
                                    'question': 'What extension should you install in VS Code for Python?',
                                    'options': ['Python by Microsoft', 'Code Runner', 'Prettier', 'Live Server'],
                                    'correct': 0
                                },
                                {
                                    'question': 'What function prints output in Python?',
                                    'options': ['console.log()', 'echo()', 'print()', 'System.out.println()'],
                                    'correct': 2
                                },
                            ]
                        },
                        'passing_score': 70,
                    },
                ]
            },
            
            # ========== LESSON 2: Variables and Data Types ==========
            {
                'title': 'Variables, Data Types, and Operators',
                'order': 2,
                'is_free_preview': False,
                'description': 'Master Python variables, data types, type conversion, and operators.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Understanding Variables and Data Types',
                        'order': 1,
                        'duration_minutes': 22,
                        'video_url': 'https://www.youtube.com/embed/rfscVS0vtbw',
                        'text_content': 'Learn Python variables, strings, integers, floats, booleans, and type conversion.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Variables and Data Types',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 2: VARIABLES AND DATA TYPES\n'
                            '# ====================================\n\n'
                            '# --- Part 1: Creating Variables ---\n'
                            'name = "Alice"              # String\n'
                            'age = 25                    # Integer\n'
                            'height = 1.68               # Float\n'
                            'is_student = True           # Boolean\n'
                            'certificates = ["Python", "SQL"]  # List\n'
                            'profile = {"name": "Alice", "age": 25}  # Dictionary\n\n'
                            '# --- Part 2: Type Checking ---\n'
                            'print(f"name is type: {type(name)}")\n'
                            'print(f"age is type: {type(age)}")\n'
                            'print(f"height is type: {type(height)}")\n'
                            'print(f"is_student is type: {type(is_student)}")\n\n'
                            '# --- Part 3: Type Conversion ---\n'
                            'str_num = "100"\n'
                            'int_num = int(str_num)      # String to Integer\n'
                            'float_num = float("3.14")    # String to Float\n'
                            'str_from_int = str(200)      # Integer to String\n'
                            'print(f"Converted: {int_num + 50}")  # 150\n\n'
                            '# --- Part 4: String Operations ---\n'
                            'first = "Hello"\n'
                            'last = "World"\n'
                            'full = first + " " + last    # Concatenation\n'
                            'print(full.upper())           # HELLO WORLD\n'
                            'print(full.lower())           # hello world\n'
                            'print(len(full))              # 11\n'
                            'print(full[0:5])              # Hello (slicing)\n\n'
                            '# --- Part 5: F-Strings ---\n'
                            'product = "Python Course"\n'
                            'price = 49.99\n'
                            'print(f"The {product} costs ${price}")\n\n'
                            '# --- EXERCISES ---\n'
                            '# 1. Create variables for your name, age, city\n'
                            '# 2. Calculate BMI: weight(kg) / height(m)²\n'
                            '# 3. Create a greeting using f-strings\n'
                            '# 4. Convert "25.5" to float and multiply by 2'
                        ),
                    },
                    {
                        'content_type': 'quiz',
                        'title': 'Knowledge Check: Variables & Types',
                        'order': 3,
                        'quiz_data': {
                            'questions': [
                                {
                                    'question': 'What type is the value True?',
                                    'options': ['int', 'str', 'bool', 'float'],
                                    'correct': 2
                                },
                                {
                                    'question': 'How do you convert "123" to an integer?',
                                    'options': ['str(123)', 'int("123")', 'float("123")', 'num("123")'],
                                    'correct': 1
                                },
                                {
                                    'question': 'What does len("Python") return?',
                                    'options': ['5', '6', '7', 'Error'],
                                    'correct': 1
                                },
                            ]
                        },
                        'passing_score': 70,
                    },
                ]
            },
            
            # ========== LESSON 3: Control Flow ==========
            {
                'title': 'Control Flow: If Statements and Loops',
                'order': 3,
                'is_free_preview': False,
                'description': 'Master conditional statements, for loops, while loops, and list comprehensions.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'If, Elif, Else and Loops Explained',
                        'order': 1,
                        'duration_minutes': 28,
                        'video_url': 'https://www.youtube.com/embed/DZwmZ8Usvnk',
                        'text_content': 'Learn if/elif/else, for loops, while loops, break, continue, and list comprehensions.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Control Flow Exercises',
                        'order': 2,
                        'duration_minutes': 35,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 3: CONTROL FLOW\n'
                            '# ====================================\n\n'
                            '# --- Part 1: If/Else Statements ---\n'
                            'age = 20\n'
                            'if age >= 18:\n'
                            '    print("You can vote!")\n'
                            'elif age >= 13:\n'
                            '    print("You are a teenager")\n'
                            'else:\n'
                            '    print("You are a child")\n\n'
                            '# --- Part 2: Multiple Conditions ---\n'
                            'score = 85\n'
                            'attendance = 90\n'
                            'if score >= 80 and attendance >= 85:\n'
                            '    print("Excellent! You passed with honors.")\n'
                            'elif score >= 60 or attendance >= 75:\n'
                            '    print("You passed.")\n'
                            'else:\n'
                            '    print("You need improvement.")\n\n'
                            '# --- Part 3: For Loops ---\n'
                            'fruits = ["apple", "banana", "orange", "mango"]\n'
                            'for fruit in fruits:\n'
                            '    print(f"I like {fruit}")\n\n'
                            '# Range loop\n'
                            'for i in range(1, 6):\n'
                            '    print(f"Count: {i}")  # 1 to 5\n\n'
                            '# --- Part 4: While Loops ---\n'
                            'count = 0\n'
                            'while count < 5:\n'
                            '    print(f"While count: {count}")\n'
                            '    count += 1\n\n'
                            '# --- Part 5: Break and Continue ---\n'
                            'for num in range(10):\n'
                            '    if num == 3:\n'
                            '        continue  # Skip 3\n'
                            '    if num == 7:\n'
                            '        break     # Stop at 7\n'
                            '    print(num)  # Prints: 0,1,2,4,5,6\n\n'
                            '# --- Part 6: List Comprehension ---\n'
                            'squares = [x**2 for x in range(1, 6)]  # [1,4,9,16,25]\n'
                            'evens = [x for x in range(10) if x % 2 == 0]  # [0,2,4,6,8]\n\n'
                            '# --- EXERCISES ---\n'
                            '# 1. FizzBuzz: Print 1-20, multiples of 3="Fizz", 5="Buzz", both="FizzBuzz"\n'
                            '# 2. Create a number guessing game\n'
                            '# 3. Find all prime numbers between 1-50\n'
                            '# 4. Create a simple calculator with if/elif'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 4: Functions ==========
            {
                'title': 'Functions: Writing Reusable Code',
                'order': 4,
                'is_free_preview': False,
                'description': 'Learn to create and use functions, parameters, return values, and lambda functions.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Python Functions and Scope',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/9Os0o3wzS_I',
                        'text_content': 'Master function definition, arguments, return values, *args, **kwargs, and scope.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Functions',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 4: FUNCTIONS\n'
                            '# ====================================\n\n'
                            '# --- Part 1: Basic Functions ---\n'
                            'def greet(name):\n'
                            '    """Greet a person by name."""\n'
                            '    return f"Hello, {name}!"\n\n'
                            'print(greet("Alice"))\n\n'
                            '# --- Part 2: Default Parameters ---\n'
                            'def create_profile(name, age=18, country="USA"):\n'
                            '    return {"name": name, "age": age, "country": country}\n\n'
                            'print(create_profile("Bob", 25))\n'
                            'print(create_profile("Charlie"))  # Uses defaults\n\n'
                            '# --- Part 3: *args and **kwargs ---\n'
                            'def sum_all(*args):\n'
                            '    return sum(args)\n\n'
                            'print(sum_all(1, 2, 3, 4, 5))  # 15\n\n'
                            'def print_info(**kwargs):\n'
                            '    for key, value in kwargs.items():\n'
                            '        print(f"{key}: {value}")\n\n'
                            'print_info(name="Alice", age=25, job="Developer")\n\n'
                            '# --- Part 4: Lambda Functions ---\n'
                            'square = lambda x: x ** 2\n'
                            'add = lambda a, b: a + b\n'
                            'print(square(5))  # 25\n'
                            'print(add(3, 7))  # 10\n\n'
                            '# Sorting with lambda\n'
                            'students = [("Alice", 85), ("Bob", 92), ("Charlie", 78)]\n'
                            'students.sort(key=lambda x: x[1], reverse=True)\n'
                            'print(students)  # Sorted by score\n\n'
                            '# --- Part 5: Decorators ---\n'
                            'def timer(func):\n'
                            '    import time\n'
                            '    def wrapper(*args, **kwargs):\n'
                            '        start = time.time()\n'
                            '        result = func(*args, **kwargs)\n'
                            '        end = time.time()\n'
                            '        print(f"{func.__name__} took {end-start:.4f}s")\n'
                            '        return result\n'
                            '    return wrapper\n\n'
                            '@timer\n'
                            'def slow_function():\n'
                            '    import time\n'
                            '    time.sleep(0.1)\n'
                            '    return "Done!"\n\n'
                            '# --- EXERCISES ---\n'
                            '# 1. Create a function that checks if a number is prime\n'
                            '# 2. Build a calculator with add, subtract, multiply, divide functions\n'
                            '# 3. Create a function that returns factorial of a number\n'
                            '# 4. Write a function that validates email format'
                        ),
                    },
                    {
                        'content_type': 'assignment',
                        'title': 'Mini-Project: To-Do List Application',
                        'order': 3,
                        'assignment_instructions': (
                            '<h3>Build a Command-Line To-Do List App</h3>\n\n'
                            '<h4>Requirements:</h4>\n'
                            '<ol>\n'
                            '<li>Create functions: <code>add_task()</code>, <code>view_tasks()</code>, '
                            '<code>complete_task()</code>, <code>delete_task()</code></li>\n'
                            '<li>Store tasks in a list of dictionaries</li>\n'
                            '<li>Implement a menu loop</li>\n'
                            '<li>Save/load tasks from JSON file</li>\n'
                            '<li>Add colored output for completed vs pending tasks</li>\n'
                            '</ol>\n\n'
                            '<h4>Sample Menu:</h4>\n'
                            '<pre>=== TO-DO LIST ===\n'
                            '1. Add Task\n2. View Tasks\n3. Complete Task\n'
                            '4. Delete Task\n5. Save & Exit\nChoice: </pre>'
                        ),
                        'max_score': 100,
                    },
                ]
            },
            
            # ========== LESSON 5: Data Structures ==========
            {
                'title': 'Python Data Structures: Lists, Tuples, Sets, Dictionaries',
                'order': 5,
                'is_free_preview': False,
                'description': 'Master Python\'s built-in data structures for efficient data manipulation.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Lists, Tuples, Sets, and Dictionaries Deep Dive',
                        'order': 1,
                        'duration_minutes': 30,
                        'video_url': 'https://www.youtube.com/embed/W8KRzm-HUcc',
                        'text_content': 'Learn list methods, tuple immutability, set operations, and dictionary manipulation.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Data Structures',
                        'order': 2,
                        'duration_minutes': 35,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 5: DATA STRUCTURES\n'
                            '# ====================================\n\n'
                            '# --- Lists ---\n'
                            'numbers = [1, 2, 3, 4, 5]\n'
                            'numbers.append(6)       # [1,2,3,4,5,6]\n'
                            'numbers.insert(0, 0)    # [0,1,2,3,4,5,6]\n'
                            'numbers.remove(3)       # [0,1,2,4,5,6]\n'
                            'popped = numbers.pop()  # [0,1,2,4,5], popped=6\n'
                            'print(numbers[1:4])     # [1,2,4] slicing\n'
                            'print(len(numbers))     # 5\n\n'
                            '# --- Tuples (immutable) ---\n'
                            'coordinates = (10, 20)\n'
                            'x, y = coordinates      # Unpacking\n'
                            'print(f"X: {x}, Y: {y}")\n\n'
                            '# --- Sets (unique, unordered) ---\n'
                            'set1 = {1, 2, 3, 4}\n'
                            'set2 = {3, 4, 5, 6}\n'
                            'print(set1 | set2)      # Union: {1,2,3,4,5,6}\n'
                            'print(set1 & set2)      # Intersection: {3,4}\n'
                            'print(set1 - set2)      # Difference: {1,2}\n\n'
                            '# Remove duplicates from list\n'
                            'duplicates = [1,2,2,3,3,3,4]\n'
                            'unique = list(set(duplicates))  # [1,2,3,4]\n\n'
                            '# --- Dictionaries ---\n'
                            'student = {\n'
                            '    "name": "Alice",\n'
                            '    "age": 25,\n'
                            '    "courses": ["Python", "SQL"],\n'
                            '    "grades": {"Python": 95, "SQL": 88}\n'
                            '}\n'
                            'print(student["name"])           # Alice\n'
                            'print(student.get("email", "N/A"))  # N/A (safe access)\n'
                            'student["email"] = "alice@email.com"  # Add key\n'
                            'del student["age"]               # Remove key\n\n'
                            '# Iterate dictionary\n'
                            'for key, value in student.items():\n'
                            '    print(f"{key}: {value}")\n\n'
                            '# --- EXERCISES ---\n'
                            '# 1. Find the most frequent element in a list\n'
                            '# 2. Merge two dictionaries\n'
                            '# 3. Find common elements between two lists\n'
                            '# 4. Group a list of words by their first letter'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 6: OOP ==========
            {
                'title': 'Object-Oriented Programming',
                'order': 6,
                'is_free_preview': False,
                'description': 'Deep dive into OOP: classes, objects, inheritance, encapsulation, and polymorphism.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Classes, Objects, and Inheritance',
                        'order': 1,
                        'duration_minutes': 35,
                        'video_url': 'https://www.youtube.com/embed/ZDa-Z5JzLYM',
                        'text_content': 'Master OOP concepts: classes, __init__, self, inheritance, polymorphism, magic methods.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: OOP - Bank System',
                        'order': 2,
                        'duration_minutes': 40,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 6: OOP - BANK SYSTEM\n'
                            '# ====================================\n\n'
                            'from datetime import datetime\n\n'
                            'class BankAccount:\n'
                            '    """Base bank account class"""\n'
                            '    \n'
                            '    def __init__(self, holder, balance=0):\n'
                            '        self.holder = holder\n'
                            '        self._balance = balance  # Protected\n'
                            '        self.__transactions = []  # Private\n'
                            '    \n'
                            '    @property\n'
                            '    def balance(self):\n'
                            '        return self._balance\n'
                            '    \n'
                            '    def deposit(self, amount):\n'
                            '        if amount > 0:\n'
                            '            self._balance += amount\n'
                            '            self.__log("deposit", amount)\n'
                            '            return True\n'
                            '        return False\n'
                            '    \n'
                            '    def withdraw(self, amount):\n'
                            '        if 0 < amount <= self._balance:\n'
                            '            self._balance -= amount\n'
                            '            self.__log("withdraw", amount)\n'
                            '            return True\n'
                            '        return False\n'
                            '    \n'
                            '    def __log(self, type_, amount):\n'
                            '        self.__transactions.append({\n'
                            '            "type": type_,\n'
                            '            "amount": amount,\n'
                            '            "date": datetime.now()\n'
                            '        })\n'
                            '    \n'
                            '    def __str__(self):\n'
                            '        return f"{self.holder}: ${self._balance:.2f}"\n\n'
                            'class SavingsAccount(BankAccount):\n'
                            '    """Savings account with interest"""\n'
                            '    RATE = 0.025  # Class constant\n'
                            '    \n'
                            '    def __init__(self, holder, balance=0):\n'
                            '        super().__init__(holder, balance)\n'
                            '        self.withdrawals = 0\n'
                            '    \n'
                            '    def apply_interest(self):\n'
                            '        interest = self._balance * self.RATE / 12\n'
                            '        self._balance += interest\n'
                            '        return interest\n'
                            '    \n'
                            '    def withdraw(self, amount):\n'
                            '        if self.withdrawals >= 6:\n'
                            '            print("Monthly limit reached!")\n'
                            '            return False\n'
                            '        if super().withdraw(amount):\n'
                            '            self.withdrawals += 1\n'
                            '            return True\n'
                            '        return False\n\n'
                            '# --- Test ---\n'
                            'acc = SavingsAccount("Alice", 1000)\n'
                            'acc.deposit(500)\n'
                            'acc.withdraw(200)\n'
                            'acc.apply_interest()\n'
                            'print(acc)  # Alice: $13xx.xx'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 7: File Handling ==========
            {
                'title': 'File Handling and Working with Data',
                'order': 7,
                'is_free_preview': False,
                'description': 'Learn to read/write files, work with JSON, CSV, and handle errors.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'File I/O, JSON, and CSV in Python',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/Uh2ebFW8OYM',
                        'text_content': 'Master file operations, JSON parsing, CSV processing, and error handling.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: File Operations',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            '# ====================================\n'
                            '# LESSON 7: FILE HANDLING\n'
                            '# ====================================\n\n'
                            '# --- Reading Files ---\n'
                            'with open("data.txt", "r") as f:\n'
                            '    content = f.read()\n'
                            '    lines = f.readlines()  # List of lines\n\n'
                            '# --- Writing Files ---\n'
                            'with open("output.txt", "w") as f:\n'
                            '    f.write("Hello, World!\\n")\n'
                            '    f.write("Second line\\n")\n\n'
                            '# --- Appending ---\n'
                            'with open("log.txt", "a") as f:\n'
                            '    f.write(f"Log entry at {datetime.now()}\\n")\n\n'
                            '# --- JSON ---\n'
                            'import json\n'
                            'data = {"name": "Alice", "age": 25, "skills": ["Python", "SQL"]}\n'
                            '# Write JSON\n'
                            'with open("data.json", "w") as f:\n'
                            '    json.dump(data, f, indent=2)\n'
                            '# Read JSON\n'
                            'with open("data.json", "r") as f:\n'
                            '    loaded = json.load(f)\n'
                            '    print(loaded["name"])  # Alice\n\n'
                            '# --- CSV ---\n'
                            'import csv\n'
                            '# Write CSV\n'
                            'with open("users.csv", "w", newline="") as f:\n'
                            '    writer = csv.writer(f)\n'
                            '    writer.writerow(["Name", "Email", "Age"])\n'
                            '    writer.writerow(["Alice", "alice@email.com", 25])\n'
                            '# Read CSV\n'
                            'with open("users.csv", "r") as f:\n'
                            '    reader = csv.DictReader(f)\n'
                            '    for row in reader:\n'
                            '        print(row["Name"], row["Email"])\n\n'
                            '# --- Error Handling ---\n'
                            'try:\n'
                            '    with open("nonexistent.txt", "r") as f:\n'
                            '        content = f.read()\n'
                            'except FileNotFoundError:\n'
                            '    print("File not found!")\n'
                            'except PermissionError:\n'
                            '    print("Permission denied!")\n'
                            'finally:\n'
                            '    print("Cleanup complete.")'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 8: Modules and Packages ==========
            {
                'title': 'Modules, Packages, and Virtual Environments',
                'order': 8,
                'is_free_preview': False,
                'description': 'Learn to organize code with modules, use pip, and manage virtual environments.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Python Modules and pip Explained',
                        'order': 1,
                        'duration_minutes': 20,
                        'video_url': 'https://www.youtube.com/embed/1fv_LAKCfJ8',
                        'text_content': 'Learn imports, creating modules, pip, virtual environments, and requirements.txt.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Modules & venv',
                        'order': 2,
                        'duration_minutes': 20,
                        'text_content': (
                            '# Create a virtual environment\n'
                            '# python -m venv myenv\n'
                            '# source myenv/bin/activate (Mac/Linux)\n'
                            '# myenv\\Scripts\\activate (Windows)\n\n'
                            '# Install packages\n'
                            '# pip install requests pandas flask\n'
                            '# pip freeze > requirements.txt\n\n'
                            '# --- Creating a module (utils.py) ---\n'
                            '# File: utils.py\n'
                            'def add(a, b):\n'
                            '    return a + b\n\n'
                            'def multiply(a, b):\n'
                            '    return a * b\n\n'
                            'PI = 3.14159\n\n'
                            '# --- Using the module (main.py) ---\n'
                            'import utils\n'
                            'from utils import add, PI\n'
                            'from datetime import datetime as dt\n\n'
                            'print(utils.add(5, 3))     # 8\n'
                            'print(add(10, 20))         # 30\n'
                            'print(PI)                  # 3.14159\n'
                            'print(dt.now())            # Current datetime'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 9: Web Scraping ==========
            {
                'title': 'Web Scraping with BeautifulSoup',
                'order': 9,
                'is_free_preview': False,
                'description': 'Learn to extract data from websites using BeautifulSoup and Requests.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Web Scraping with Python',
                        'order': 1,
                        'duration_minutes': 28,
                        'video_url': 'https://www.youtube.com/embed/ng2o98k983k',
                        'text_content': 'Learn Requests, BeautifulSoup, parsing HTML, and ethical scraping practices.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Web Scraper',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            '# Install: pip install requests beautifulsoup4\n\n'
                            'import requests\n'
                            'from bs4 import BeautifulSoup\n\n'
                            '# --- Basic Request ---\n'
                            'url = "https://quotes.toscrape.com"\n'
                            'response = requests.get(url)\n'
                            'print(f"Status: {response.status_code}")\n'
                            'print(f"Headers: {response.headers}")\n\n'
                            '# --- Parse HTML ---\n'
                            'soup = BeautifulSoup(response.text, "html.parser")\n\n'
                            '# Find all quotes\n'
                            'quotes = soup.find_all("div", class_="quote")\n'
                            'for quote in quotes[:5]:\n'
                            '    text = quote.find("span", class_="text").text\n'
                            '    author = quote.find("small", class_="author").text\n'
                            '    print(f"\\"{text}\\" - {author}")\n\n'
                            '# --- Scrape with headers ---\n'
                            'headers = {\n'
                            '    "User-Agent": "Mozilla/5.0 ..."\n'
                            '}\n'
                            'response = requests.get(url, headers=headers)\n\n'
                            '# --- Save data to CSV ---\n'
                            'import csv\n'
                            'with open("quotes.csv", "w", newline="") as f:\n'
                            '    writer = csv.writer(f)\n'
                            '    writer.writerow(["Quote", "Author"])\n'
                            '    for quote in quotes:\n'
                            '        text = quote.find("span", class_="text").text\n'
                            '        author = quote.find("small", class_="author").text\n'
                            '        writer.writerow([text, author])\n'
                            'print("Data saved to quotes.csv!")'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 10: Flask API ==========
            {
                'title': 'Building REST APIs with Flask',
                'order': 10,
                'is_free_preview': False,
                'description': 'Create your first web API using Flask framework.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Flask REST API Tutorial',
                        'order': 1,
                        'duration_minutes': 35,
                        'video_url': 'https://www.youtube.com/embed/Z1RJmh_OqeA',
                        'text_content': 'Build a complete REST API with Flask: routes, JSON responses, CRUD operations.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: Flask API',
                        'order': 2,
                        'duration_minutes': 40,
                        'text_content': (
                            '# Install: pip install flask\n\n'
                            '# --- app.py ---\n'
                            'from flask import Flask, jsonify, request\n\n'
                            'app = Flask(__name__)\n\n'
                            '# Sample data\n'
                            'books = [\n'
                            '    {"id": 1, "title": "Python Basics", "author": "John Doe"},\n'
                            '    {"id": 2, "title": "Flask Web", "author": "Jane Smith"},\n'
                            ']\n\n'
                            '# GET all books\n'
                            '@app.route("/api/books", methods=["GET"])\n'
                            'def get_books():\n'
                            '    return jsonify(books)\n\n'
                            '# GET single book\n'
                            '@app.route("/api/books/<int:book_id>", methods=["GET"])\n'
                            'def get_book(book_id):\n'
                            '    book = next((b for b in books if b["id"] == book_id), None)\n'
                            '    if book:\n'
                            '        return jsonify(book)\n'
                            '    return jsonify({"error": "Not found"}), 404\n\n'
                            '# POST new book\n'
                            '@app.route("/api/books", methods=["POST"])\n'
                            'def add_book():\n'
                            '    data = request.get_json()\n'
                            '    new_book = {\n'
                            '        "id": len(books) + 1,\n'
                            '        "title": data["title"],\n'
                            '        "author": data["author"]\n'
                            '    }\n'
                            '    books.append(new_book)\n'
                            '    return jsonify(new_book), 201\n\n'
                            'if __name__ == "__main__":\n'
                            '    app.run(debug=True)\n\n'
                            '# Run: python app.py\n'
                            '# Test: curl http://localhost:5000/api/books'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 11: Database with SQLite ==========
            {
                'title': 'Database Management with SQLite',
                'order': 11,
                'is_free_preview': False,
                'description': 'Learn SQL basics and database operations in Python using SQLite.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'SQLite and Python Database Tutorial',
                        'order': 1,
                        'duration_minutes': 25,
                        'video_url': 'https://www.youtube.com/embed/byHcYRpMgI4',
                        'text_content': 'Learn SQLite, CRUD operations, SQL queries, and database design.',
                    },
                    {
                        'content_type': 'code',
                        'title': 'Practice: SQLite Database',
                        'order': 2,
                        'duration_minutes': 30,
                        'text_content': (
                            'import sqlite3\n\n'
                            '# --- Connect to database ---\n'
                            'conn = sqlite3.connect("students.db")\n'
                            'cursor = conn.cursor()\n\n'
                            '# --- Create table ---\n'
                            'cursor.execute("""\n'
                            '    CREATE TABLE IF NOT EXISTS students (\n'
                            '        id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
                            '        name TEXT NOT NULL,\n'
                            '        email TEXT UNIQUE,\n'
                            '        grade REAL\n'
                            '    )\n'
                            '""")\n\n'
                            '# --- Insert data ---\n'
                            'cursor.execute(\n'
                            '    "INSERT INTO students (name, email, grade) VALUES (?, ?, ?)",\n'
                            '    ("Alice", "alice@email.com", 95.5)\n'
                            ')\n'
                            'cursor.executemany(\n'
                            '    "INSERT INTO students (name, email, grade) VALUES (?, ?, ?)",\n'
                            '    [("Bob", "bob@email.com", 88.0),\n'
                            '     ("Charlie", "charlie@email.com", 92.3)]\n'
                            ')\n'
                            'conn.commit()\n\n'
                            '# --- Query data ---\n'
                            'cursor.execute("SELECT * FROM students WHERE grade > ?", (90,))\n'
                            'rows = cursor.fetchall()\n'
                            'for row in rows:\n'
                            '    print(f"ID: {row[0]}, Name: {row[1]}, Grade: {row[3]}")\n\n'
                            '# --- Update ---\n'
                            'cursor.execute(\n'
                            '    "UPDATE students SET grade = ? WHERE name = ?",\n'
                            '    (97.0, "Alice")\n'
                            ')\n\n'
                            '# --- Delete ---\n'
                            'cursor.execute("DELETE FROM students WHERE name = ?", ("Bob",))\n\n'
                            'conn.commit()\n'
                            'conn.close()'
                        ),
                    },
                ]
            },
            
            # ========== LESSON 12: Final Project ==========
            {
                'title': 'Final Project: Portfolio Website with Flask',
                'order': 12,
                'is_free_preview': False,
                'description': 'Build and deploy a complete portfolio website.',
                'contents': [
                    {
                        'content_type': 'video',
                        'title': 'Project Overview and Deployment',
                        'order': 1,
                        'duration_minutes': 20,
                        'video_url': 'https://www.youtube.com/embed/goToXTC96Co',
                        'text_content': 'Final project walkthrough and deployment instructions.',
                    },
                    {
                        'content_type': 'assignment',
                        'title': 'Build Your Portfolio Website',
                        'order': 2,
                        'assignment_instructions': (
                            '<h2>Final Project: Personal Portfolio Website</h2>\n\n'
                            '<h3>Requirements:</h3>\n'
                            '<ol>\n'
                            '<li><strong>Home Page:</strong> Introduction, skills, and featured projects</li>\n'
                            '<li><strong>Projects Page:</strong> Display your Python projects with descriptions</li>\n'
                            '<li><strong>Blog Section:</strong> CRUD operations with SQLite database</li>\n'
                            '<li><strong>Contact Form:</strong> Send emails using Flask-Mail</li>\n'
                            '<li><strong>Responsive Design:</strong> Mobile-friendly with Bootstrap 5</li>\n'
                            '<li><strong>Deploy:</strong> Deploy to PythonAnywhere or Render</li>\n'
                            '</ol>\n\n'
                            '<h3>Project Structure:</h3>\n'
                            '<pre>\n'
                            'portfolio/\n'
                            '├── app.py\n'
                            '├── templates/\n'
                            '│   ├── base.html\n'
                            '│   ├── index.html\n'
                            '│   ├── projects.html\n'
                            '│   ├── blog.html\n'
                            '│   └── contact.html\n'
                            '├── static/\n'
                            '│   ├── css/style.css\n'
                            '│   └── js/main.js\n'
                            '├── database.db\n'
                            '└── requirements.txt\n'
                            '</pre>\n\n'
                            '<h3>Grading Rubric:</h3>\n'
                            '<ul>\n'
                            '<li>Functionality: 40%</li>\n'
                            '<li>Code Quality: 20%</li>\n'
                            '<li>Design/UX: 20%</li>\n'
                            '<li>Documentation: 10%</li>\n'
                            '<li>Deployment: 10%</li>\n'
                            '</ul>'
                        ),
                        'max_score': 100,
                    },
                ]
            },
        ]
        
        # Create all lessons
        for lesson_data in lessons:
            contents_data = lesson_data.pop('contents', [])
            
            lesson, created = Lesson.objects.update_or_create(
                course=course,
                title=lesson_data['title'],
                defaults={
                    'order': lesson_data['order'],
                    'is_free_preview': lesson_data.get('is_free_preview', False),
                    'description': lesson_data.get('description', ''),
                    'is_published': True,
                }
            )
            
            if created:
                for content_data in contents_data:
                    quiz_data = content_data.pop('quiz_data', None)
                    LessonContent.objects.create(
                        lesson=lesson,
                        quiz_data=quiz_data,
                        **content_data
                    )
                self.stdout.write(f'  ✓ Lesson {lesson.order}: {lesson.title} ({len(contents_data)} contents)')
            else:
                self.stdout.write(f'  ⚠ Lesson exists: {lesson.title}')