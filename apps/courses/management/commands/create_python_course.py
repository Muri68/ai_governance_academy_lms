from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import CourseCategory, Course, Lesson, LessonContent
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create complete Python Programming Masterclass with all text-based lessons'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating Python Programming Masterclass...')
        
        category, _ = CourseCategory.objects.get_or_create(
            slug='programming',
            defaults={
                'name': 'Programming & Development',
                'description': 'Learn programming languages and software development',
                'icon': 'fas fa-code',
            }
        )
        
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
        
        course, created = Course.objects.update_or_create(
            slug='python-programming-masterclass',
            defaults={
                'title': 'Python Programming Masterclass: From Zero to Hero',
                'instructor': instructor,
                'category': category,
                'description': 'Master Python from basics to advanced with hands-on projects.',
                'short_description': 'Master Python from basics to advanced with hands-on projects',
                'level': 'beginner',
                'duration': '12 Weeks',
                'language': 'English',
                'price': 49.99,
                'discount_price': 39.99,
                'is_free': False,
                'status': 'published',
                'is_featured': True,
                'has_certificate': True,
                'requirements': 'No prior programming experience required.',
                'what_you_learn': 'Python fundamentals, OOP, file handling, databases, web APIs, and deployment.',
                'published_at': timezone.now(),
            }
        )
        
        self.create_all_lessons(course)
        self.stdout.write(self.style.SUCCESS('Python Programming Masterclass created successfully!'))

    def make_quiz(self, questions_data):
        """Helper to create quiz data structure"""
        return {'questions': questions_data}

    def create_all_lessons(self, course):
        """Create all 12 lessons"""
        lessons = [
            # LESSON 1
            {
                'title': 'Getting Started with Python Programming',
                'order': 1, 'is_free_preview': True,
                'description': 'Set up Python and write your first program.',
                'contents': [
                    {'content_type': 'text', 'title': 'Welcome to Python Programming', 'order': 1, 'duration_minutes': 15, 'is_preview': True,
                     'text_content': '<h1>Welcome to Python Programming Masterclass</h1><p>Welcome to your journey into programming with Python! Python is a high-level, interpreted language created by Guido van Rossum in 1991. It emphasizes readability and is used by Google, Netflix, NASA, Instagram, and Spotify.</p><h2>Why Learn Python?</h2><ul><li>Easy to learn with clear syntax</li><li>Versatile: web dev, data science, AI, automation</li><li>High demand with excellent salaries</li><li>Huge community and library ecosystem</li></ul><h2>Course Structure</h2><p>12 lessons from basics to building real applications with hands-on exercises and quizzes.</p>'},
                    {'content_type': 'text', 'title': 'Setting Up Python', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>Setting Up Python</h1><h2>Step 1: Download</h2><p>Visit python.org/downloads and download Python 3.11+.</p><div style="background:#dbeafe;padding:15px;border-radius:8px;"><strong>Windows:</strong> Check "Add Python to PATH" during installation.</div><h2>Step 2: Verify</h2><pre><code>python --version</code></pre><h2>Step 3: VS Code</h2><p>Download from code.visualstudio.com. Install the Python extension.</p><h2>Step 4: First Program</h2><pre><code>print("Hello, World!")</code></pre>'},
                    {'content_type': 'quiz', 'title': 'Lesson 1 Quiz', 'order': 3,
                     'quiz_data': self.make_quiz([
                         {'question': 'Who created Python?', 'options': ['Dennis Ritchie', 'Guido van Rossum', 'James Gosling', 'Bjarne Stroustrup'], 'correct': 1},
                         {'question': 'When was Python first released?', 'options': ['1989', '1991', '1995', '2000'], 'correct': 1},
                         {'question': 'Which command checks Python version?', 'options': ['python -v', 'python --version', 'python check', 'python info'], 'correct': 1},
                         {'question': 'What is the Python file extension?', 'options': ['.java', '.py', '.python', '.pt'], 'correct': 1},
                         {'question': 'What function prints output?', 'options': ['console.log()', 'echo', 'print()', 'display()'], 'correct': 2},
                         {'question': 'Is Python case-sensitive?', 'options': ['Yes', 'No', 'Sometimes', 'Only strings'], 'correct': 0},
                         {'question': 'What does PATH allow?', 'options': ['More features', 'Run Python from any directory', 'Faster execution', 'Better syntax'], 'correct': 1},
                         {'question': 'Which editor is recommended?', 'options': ['Notepad', 'VS Code', 'Word', 'Excel'], 'correct': 1},
                         {'question': 'What symbol for comments?', 'options': ['//', '#', '/*', '--'], 'correct': 1},
                         {'question': 'Python is what type of language?', 'options': ['Compiled', 'Interpreted', 'Machine', 'Assembly'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 2
            {
                'title': 'Variables, Data Types, and Operators',
                'order': 2, 'is_free_preview': False,
                'description': 'Master variables, data types, and operators.',
                'contents': [
                    {'content_type': 'text', 'title': 'Variables and Data Types', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>Variables and Data Types</h1><h2>Variables</h2><p>Variables store data. Python is dynamically typed.</p><pre><code>name = "Alice"\nage = 25\nheight = 1.68\nis_student = True</code></pre><h2>Data Types</h2><ul><li><strong>int:</strong> Whole numbers (42, -10)</li><li><strong>float:</strong> Decimals (3.14, -0.5)</li><li><strong>str:</strong> Text ("Hello")</li><li><strong>bool:</strong> True/False</li><li><strong>None:</strong> No value</li></ul><h2>Type Checking</h2><pre><code>print(type(42))      # &lt;class \'int\'&gt;\nprint(type("Hello")) # &lt;class \'str\'&gt;</code></pre>'},
                    {'content_type': 'text', 'title': 'Type Conversion and Strings', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>Type Conversion</h1><pre><code>int("123")    # 123\nfloat("3.14") # 3.14\nstr(100)      # "100"\nbool(1)       # True</code></pre><h1>String Operations</h1><pre><code>text = "  Hello World  "\nprint(text.upper())    # "  HELLO WORLD  "\nprint(text.strip())    # "Hello World"\nprint(text.split())    # [\'Hello\', \'World\']\nprint(len(text))       # 15</code></pre><h1>F-Strings</h1><pre><code>name = "Alice"\nage = 25\nprint(f"{name} is {age} years old")\nprice = 49.99\nprint(f"Cost: ${price:.2f}")</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: Variables & Types', 'order': 3, 'duration_minutes': 25,
                     'text_content': '# Exercise 1: Personal Info\nname = "John"\nage = 28\nheight = 1.75\nprint(f"{name} is {age}, {height}m")\n\n# Exercise 2: BMI Calculator\nweight = 70\nheight_m = 1.75\nbmi = weight / (height_m ** 2)\nprint(f"BMI: {bmi:.2f}")\n\n# Exercise 3: Type Conversion\nnum_str = "100"\nnum = int(num_str)\nprint(f"Result: {num + 50}")\n\n# Exercise 4: String Methods\nemail = "  USER@EXAMPLE.COM  "\nclean = email.strip().lower()\nprint(f"Cleaned: {clean}")'},
                    {'content_type': 'quiz', 'title': 'Lesson 2 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'Which is a valid variable name?', 'options': ['2name', 'my-name', '_count', 'class'], 'correct': 2},
                         {'question': 'What type is 3.14?', 'options': ['int', 'float', 'str', 'bool'], 'correct': 1},
                         {'question': 'How to convert "123" to int?', 'options': ['str(123)', 'int("123")', 'float("123")', 'num("123")'], 'correct': 1},
                         {'question': 'What does len("Python") return?', 'options': ['5', '6', '7', 'Error'], 'correct': 1},
                         {'question': 'What type is True?', 'options': ['int', 'str', 'bool', 'NoneType'], 'correct': 2},
                         {'question': 'What does 5 // 2 give?', 'options': ['2.5', '2', '3', '2.0'], 'correct': 1},
                         {'question': 'Exponentiation operator?', 'options': ['^', '**', '^^', 'exp()'], 'correct': 1},
                         {'question': '"Hello" + " " + "World"?', 'options': ['HelloWorld', 'Hello World', 'Error', 'Hello+World'], 'correct': 1},
                         {'question': 'What is None?', 'options': ['0', 'Empty', 'No value', 'False'], 'correct': 2},
                         {'question': 'Format float to 2 decimals?', 'options': ['{v:2f}', '{v:.2f}', '{v:2.f}', '{v,2f}'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 3
            {
                'title': 'Control Flow: If Statements and Loops',
                'order': 3, 'is_free_preview': False,
                'description': 'Master if/elif/else, for loops, while loops, and list comprehensions.',
                'contents': [
                    {'content_type': 'text', 'title': 'If Statements', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>If Statements</h1><pre><code>score = 85\nif score >= 90: grade = "A"\nelif score >= 80: grade = "B"\nelif score >= 70: grade = "C"\nelse: grade = "F"</code></pre><h2>Logical Operators</h2><p>and, or, not</p><pre><code>age = 25\nhas_license = True\nif age >= 18 and has_license:\n    print("Can drive")</code></pre>'},
                    {'content_type': 'text', 'title': 'Loops and Comprehensions', 'order': 2, 'duration_minutes': 25,
                     'text_content': '<h1>For Loops</h1><pre><code>for i in range(5): print(i)  # 0-4\nfor fruit in ["apple","banana"]: print(fruit)</code></pre><h1>While Loops</h1><pre><code>count = 0\nwhile count < 5:\n    print(count)\n    count += 1</code></pre><h1>List Comprehensions</h1><pre><code>squares = [x**2 for x in range(5)]  # [0,1,4,9,16]\nevens = [x for x in range(10) if x%2==0]</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: Control Flow', 'order': 3, 'duration_minutes': 30,
                     'text_content': '# FizzBuzz\nfor i in range(1,21):\n    if i%3==0 and i%5==0: print("FizzBuzz")\n    elif i%3==0: print("Fizz")\n    elif i%5==0: print("Buzz")\n    else: print(i)\n\n# Find primes\nprimes = [n for n in range(2,50) if all(n%i!=0 for i in range(2,int(n**0.5)+1))]\nprint(f"Primes: {primes}")'},
                    {'content_type': 'quiz', 'title': 'Lesson 3 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'What keyword for alternative condition?', 'options': ['else if', 'elif', 'elseif', 'else when'], 'correct': 1},
                         {'question': 'What does range(5) give?', 'options': ['1-5', '0-4', '0-5', '1-4'], 'correct': 1},
                         {'question': 'What does break do?', 'options': ['Pauses', 'Exits loop', 'Restarts', 'Skips'], 'correct': 1},
                         {'question': '5 > 3 and 2 < 1?', 'options': ['True', 'False', 'Error', 'None'], 'correct': 1},
                         {'question': 'for i in range(3): loops?', 'options': ['2 times', '3 times', '4 times', '1 time'], 'correct': 1},
                         {'question': 'continue does what?', 'options': ['Exits', 'Skips iteration', 'Restarts', 'Ends'], 'correct': 1},
                         {'question': 'Equality operator?', 'options': ['=', '==', '!=', 'equals'], 'correct': 1},
                         {'question': 'Infinite while loop?', 'options': ['while False:', 'while True:', 'while 0:', 'while None:'], 'correct': 1},
                         {'question': '[x*2 for x in range(3)]?', 'options': ['[0,2,4]', '[1,2,3]', '[0,1,2]', '[2,4,6]'], 'correct': 0},
                         {'question': 'for letter in "AB": prints?', 'options': ['AB', 'A B', 'A then B', 'Error'], 'correct': 2},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 4
            {
                'title': 'Functions: Writing Reusable Code',
                'order': 4, 'is_free_preview': False,
                'description': 'Master functions, parameters, return values, lambda, and decorators.',
                'contents': [
                    {'content_type': 'text', 'title': 'Function Basics', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>Functions</h1><pre><code>def greet(name):\n    """Return greeting."""\n    return f"Hello, {name}!"\n\nprint(greet("Alice"))  # Hello, Alice!</code></pre><h2>Parameters</h2><ul><li>Positional: order matters</li><li>Keyword: name explicitly</li><li>Default: def func(x=10)</li></ul><h2>*args and **kwargs</h2><pre><code>def sum_all(*args): return sum(args)\ndef print_info(**kwargs):\n    for k,v in kwargs.items(): print(f"{k}:{v}")</code></pre>'},
                    {'content_type': 'text', 'title': 'Lambda and Scope', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>Lambda Functions</h1><pre><code>square = lambda x: x**2\nadd = lambda a,b: a+b\n\n# With sort\nstudents.sort(key=lambda s: s[1])</code></pre><h1>Scope (LEGB)</h1><p>Local → Enclosing → Global → Built-in</p>'},
                    {'content_type': 'code', 'title': 'Practice: Functions', 'order': 3, 'duration_minutes': 30,
                     'text_content': '# Calculator\ndef add(a,b): return a+b\ndef subtract(a,b): return a-b\ndef multiply(a,b): return a*b\ndef divide(a,b): return a/b if b!=0 else "Error"\n\n# Fibonacci\ndef fib(n):\n    a,b = 0,1\n    for _ in range(n): yield a; a,b = b,a+b'},
                    {'content_type': 'quiz', 'title': 'Lesson 4 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'Keyword to define function?', 'options': ['function', 'def', 'func', 'define'], 'correct': 1},
                         {'question': 'No return gives?', 'options': ['0', 'False', 'None', 'Error'], 'correct': 2},
                         {'question': '*args is for?', 'options': ['Keywords', 'Variable positional', 'Defaults', 'Return'], 'correct': 1},
                         {'question': 'Docstring is?', 'options': ['String var', 'Documentation', 'File path', 'Error'], 'correct': 1},
                         {'question': 'LEGB describes?', 'options': ['Loops', 'Scope', 'Functions', 'Imports'], 'correct': 1},
                         {'question': 'Function call function?', 'options': ['Yes', 'No', 'Only classes', 'Decorators only'], 'correct': 0},
                         {'question': 'Lambda is?', 'options': ['Named', 'Anonymous', 'Recursive', 'Built-in'], 'correct': 1},
                         {'question': 'Default param syntax?', 'options': ['def f(x=10)', 'def f(x:10)', 'def f(x 10)', 'def f(x->10)'], 'correct': 0},
                         {'question': '**kwargs collects?', 'options': ['List', 'Dict', 'All args', 'Defaults'], 'correct': 1},
                         {'question': 'Multiple return values?', 'options': ['No', 'Yes, tuple', 'Lists only', 'Python 3 only'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 5
            {
                'title': 'Data Structures: Lists, Tuples, Sets, Dictionaries',
                'order': 5, 'is_free_preview': False,
                'description': 'Master Python built-in data structures.',
                'contents': [
                    {'content_type': 'text', 'title': 'Lists and Tuples', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>Lists</h1><p>Ordered, mutable, allow duplicates.</p><pre><code>fruits = ["apple","banana"]\nfruits.append("orange")\nfruits.insert(1,"grape")\nfruits.remove("apple")\nprint(fruits[0])  # indexing\nprint(fruits[1:3]) # slicing</code></pre><h1>Tuples</h1><p>Ordered, immutable.</p><pre><code>point = (10, 20)\nx, y = point  # unpacking</code></pre>'},
                    {'content_type': 'text', 'title': 'Sets and Dictionaries', 'order': 2, 'duration_minutes': 25,
                     'text_content': '<h1>Sets</h1><p>Unordered, unique elements.</p><pre><code>a = {1,2,3}\nb = {3,4,5}\nprint(a | b)  # union: {1,2,3,4,5}\nprint(a & b)  # intersection: {3}</code></pre><h1>Dictionaries</h1><p>Key-value pairs.</p><pre><code>student = {"name":"Alice","age":25}\nprint(student["name"])\nprint(student.get("email","N/A"))\nfor k,v in student.items():\n    print(f"{k}: {v}")</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: Data Structures', 'order': 3, 'duration_minutes': 30,
                     'text_content': '# List operations\nnums = [1,2,3,4,5]\nprint(f"Sum: {sum(nums)}, Max: {max(nums)}")\n\n# Remove duplicates\nitems = [1,2,2,3,3,3,4]\nunique = list(set(items))\n\n# Word count\ntext = "hello world hello python"\nwords = text.split()\nfrom collections import Counter\nprint(Counter(words))'},
                    {'content_type': 'quiz', 'title': 'Lesson 5 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'Which is immutable?', 'options': ['List', 'Tuple', 'Set', 'Dict'], 'correct': 1},
                         {'question': 'How to add to list?', 'options': ['add()', 'insert()', 'append()', 'push()'], 'correct': 2},
                         {'question': 'Sets have?', 'options': ['Order', 'No duplicates', 'Indexing', 'Keys'], 'correct': 1},
                         {'question': 'Access dict value?', 'options': ['dict.key', 'dict[key]', 'dict->key', 'dict(key)'], 'correct': 1},
                         {'question': 'list.pop() does?', 'options': ['Adds', 'Removes last', 'Sorts', 'Copies'], 'correct': 1},
                         {'question': 'Tuples modifiable?', 'options': ['Yes', 'No', 'Sometimes', 'Methods only'], 'correct': 1},
                         {'question': 'len([1,2,3])?', 'options': ['2', '3', '4', 'Error'], 'correct': 1},
                         {'question': 'Remove list duplicates?', 'options': ['unique()', 'set(list)', 'distinct()', 'filter()'], 'correct': 1},
                         {'question': 'dict.get("k","d")?', 'options': ['Sets key', 'Returns value/default', 'Deletes', 'Checks'], 'correct': 1},
                         {'question': 'Ordered in Python 3.7+?', 'options': ['Set', 'Dict', 'Tuple only', 'Both Tuple and Dict'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 6
            {
                'title': 'Object-Oriented Programming',
                'order': 6, 'is_free_preview': False,
                'description': 'Deep dive into OOP: classes, objects, inheritance, encapsulation.',
                'contents': [
                    {'content_type': 'text', 'title': 'Classes and Objects', 'order': 1, 'duration_minutes': 30,
                     'text_content': '<h1>OOP Basics</h1><h2>Class Definition</h2><pre><code>class BankAccount:\n    def __init__(self, holder, balance=0):\n        self.holder = holder\n        self._balance = balance\n    \n    def deposit(self, amount):\n        if amount > 0:\n            self._balance += amount\n            return True\n        return False\n    \n    @property\n    def balance(self):\n        return self._balance</code></pre><h2>Inheritance</h2><pre><code>class SavingsAccount(BankAccount):\n    rate = 0.025\n    def apply_interest(self):\n        self._balance *= (1 + self.rate/12)</code></pre>'},
                    {'content_type': 'text', 'title': 'OOP Principles', 'order': 2, 'duration_minutes': 25,
                     'text_content': '<h1>Four Pillars</h1><ol><li><strong>Encapsulation:</strong> Hide internal state</li><li><strong>Inheritance:</strong> Reuse code from parent</li><li><strong>Polymorphism:</strong> Same interface, different behavior</li><li><strong>Abstraction:</strong> Hide complexity</li></ol><h2>Magic Methods</h2><pre><code>class Book:\n    def __str__(self): return f"Book: {self.title}"\n    def __len__(self): return self.pages\n    def __eq__(self, other): return self.title == other.title</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: OOP', 'order': 3, 'duration_minutes': 35,
                     'text_content': 'class Product:\n    def __init__(self, name, price):\n        self.name = name\n        self.price = price\n    def __str__(self):\n        return f"{self.name}: ${self.price:.2f}"\n\nclass Cart:\n    def __init__(self):\n        self.items = []\n    def add(self, product, qty=1):\n        self.items.append({"product":product,"qty":qty})\n    def total(self):\n        return sum(i["product"].price*i["qty"] for i in self.items)'},
                    {'content_type': 'quiz', 'title': 'Lesson 6 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'What is a class?', 'options': ['Object', 'Blueprint', 'Function', 'Variable'], 'correct': 1},
                         {'question': 'What is self?', 'options': ['Class', 'Instance reference', 'Module', 'Method'], 'correct': 1},
                         {'question': '__init__ is?', 'options': ['Destructor', 'Constructor', 'Method', 'Variable'], 'correct': 1},
                         {'question': 'Inheritance allows?', 'options': ['Code reuse', 'Speed', 'Smaller files', 'More vars'], 'correct': 0},
                         {'question': 'Encapsulation?', 'options': ['Hiding internals', 'Less code', 'Loops', 'Variables'], 'correct': 0},
                         {'question': 'super() does?', 'options': ['Creates class', 'Calls parent', 'Deletes', 'Returns None'], 'correct': 1},
                         {'question': 'Polymorphism?', 'options': ['Same interface, different impl', 'Multiple parents', 'Private methods', 'Static methods'], 'correct': 0},
                         {'question': '@property?', 'options': ['Creates class', 'Getter/setter', 'Deletes attr', 'Imports'], 'correct': 1},
                         {'question': 'Class variable shared?', 'options': ['Per instance', 'All instances', 'Local only', 'Global'], 'correct': 1},
                         {'question': 'Multiple inheritance?', 'options': ['No', 'Yes', 'Python 3 only', 'Interfaces only'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 7
            {
                'title': 'File Handling and Exception Management',
                'order': 7, 'is_free_preview': False,
                'description': 'Read/write files, work with JSON/CSV, handle errors.',
                'contents': [
                    {'content_type': 'text', 'title': 'File Operations', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>File Handling</h1><h2>Reading</h2><pre><code>with open("file.txt","r") as f:\n    content = f.read()\n    lines = f.readlines()</code></pre><h2>Writing</h2><pre><code>with open("output.txt","w") as f:\n    f.write("Hello\\n")</code></pre><h2>JSON</h2><pre><code>import json\ndata = {"name":"Alice"}\nwith open("data.json","w") as f:\n    json.dump(data, f, indent=2)</code></pre><h2>CSV</h2><pre><code>import csv\nwith open("data.csv","w",newline="") as f:\n    writer = csv.writer(f)\n    writer.writerow(["Name","Age"])</code></pre>'},
                    {'content_type': 'text', 'title': 'Exception Handling', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>Try/Except</h1><pre><code>try:\n    num = int(input("Number: "))\n    result = 100 / num\nexcept ValueError:\n    print("Invalid number")\nexcept ZeroDivisionError:\n    print("Cannot divide by zero")\nexcept Exception as e:\n    print(f"Error: {e}")\nelse:\n    print("Success!")\nfinally:\n    print("Done")</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: Files', 'order': 3, 'duration_minutes': 30,
                     'text_content': '# Write and read JSON\nimport json\nusers = [{"name":"Alice","age":25},{"name":"Bob","age":30}]\nwith open("users.json","w") as f:\n    json.dump(users,f,indent=2)\nwith open("users.json","r") as f:\n    loaded = json.load(f)\n    for user in loaded:\n        print(f"{user[\'name\']}: {user[\'age\']}")'},
                    {'content_type': 'quiz', 'title': 'Lesson 7 Quiz', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'Read mode?', 'options': ['"w"', '"r"', '"a"', '"x"'], 'correct': 1},
                         {'question': '"with" ensures?', 'options': ['Speed', 'File closes', 'Less memory', 'Syntax'], 'correct': 1},
                         {'question': 'JSON module?', 'options': ['csv', 'json', 'pickle', 'xml'], 'correct': 1},
                         {'question': 'Division by zero?', 'options': ['ValueError', 'TypeError', 'ZeroDivisionError', 'MathError'], 'correct': 2},
                         {'question': 'json.dump()?', 'options': ['Reads', 'Writes to file', 'Deletes', 'Validates'], 'correct': 1},
                         {'question': 'Always executes?', 'options': ['try', 'except', 'else', 'finally'], 'correct': 3},
                         {'question': '"a" mode?', 'options': ['Read', 'Overwrite', 'Append', 'Delete'], 'correct': 2},
                         {'question': 'csv.DictReader?', 'options': ['Write', 'Read as dicts', 'Sort', 'Validate'], 'correct': 1},
                         {'question': 'Open non-existent "r"?', 'options': ['Creates', 'None', 'FileNotFoundError', 'Empty'], 'correct': 2},
                         {'question': 'Multiple exceptions?', 'options': ['No', 'Yes, tuple', 'If only', 'Python 3 only'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 8
            {
                'title': 'Modules, Packages, and Virtual Environments',
                'order': 8, 'is_free_preview': False,
                'description': 'Organize code with modules, use pip, manage virtual environments.',
                'contents': [
                    {'content_type': 'text', 'title': 'Modules and Imports', 'order': 1, 'duration_minutes': 25,
                     'text_content': '<h1>Modules</h1><p>A module is a .py file containing functions and variables.</p><pre><code># mymodule.py\ndef greet(name):\n    return f"Hello, {name}!"\n\n# main.py\nimport mymodule\nfrom mymodule import greet\nfrom math import sqrt, pi\nimport datetime as dt</code></pre><h1>Packages</h1><p>A package is a directory with __init__.py file.</p>'},
                    {'content_type': 'text', 'title': 'pip and Virtual Environments', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>pip Commands</h1><pre><code>pip install package\npip install -r requirements.txt\npip list\npip freeze > requirements.txt\npip uninstall package</code></pre><h1>Virtual Environments</h1><pre><code>python -m venv myenv\nsource myenv/bin/activate  # Mac/Linux\nmyenv\\Scripts\\activate     # Windows\ndeactivate</code></pre>'},
                    {'content_type': 'quiz', 'title': 'Lesson 8 Quiz', 'order': 3,
                     'quiz_data': self.make_quiz([
                         {'question': 'What is a module?', 'options': ['Function', '.py file', 'Database', 'Server'], 'correct': 1},
                         {'question': 'Package marker file?', 'options': ['__init__.py', 'package.py', 'setup.py', 'main.py'], 'correct': 0},
                         {'question': 'pip stands for?', 'options': ['Python Installer Program', 'Pip Installs Packages', 'Python Internet Protocol', 'Package Install Process'], 'correct': 1},
                         {'question': 'Install package?', 'options': ['pip add pkg', 'pip install pkg', 'pip get pkg', 'pip download pkg'], 'correct': 1},
                         {'question': 'Virtual env?', 'options': ['Cloud', 'Isolated environment', 'Editor', 'Database'], 'correct': 1},
                         {'question': 'Import only sqrt?', 'options': ['import math.sqrt', 'from math import sqrt', 'import sqrt', 'math.import(sqrt)'], 'correct': 1},
                         {'question': 'import as alias?', 'options': ['Error', 'Creates alias', 'Duplicates', 'Nothing'], 'correct': 1},
                         {'question': 'Packages from?', 'options': ['GitHub', 'PyPI', 'npm', 'Docker'], 'correct': 1},
                         {'question': 'Save dependencies?', 'options': ['pip save', 'pip freeze > req.txt', 'pip export', 'pip list --save'], 'correct': 1},
                         {'question': 'Why venv?', 'options': ['Speed', 'Avoid conflicts', 'Smaller', 'Syntax'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 9
            {
                'title': 'Web Scraping with BeautifulSoup',
                'order': 9, 'is_free_preview': False,
                'description': 'Extract data from websites ethically.',
                'contents': [
                    {'content_type': 'text', 'title': 'Web Scraping Basics', 'order': 1, 'duration_minutes': 30,
                     'text_content': '<h1>Web Scraping</h1><p>Install: <code>pip install requests beautifulsoup4</code></p><h2>Ethics</h2><ul><li>Check robots.txt</li><li>Respect rate limits</li><li>Use proper User-Agent</li><li>Only scrape public data</li></ul><h2>Basic Scraper</h2><pre><code>import requests\nfrom bs4 import BeautifulSoup\n\nurl = "https://quotes.toscrape.com"\nresponse = requests.get(url)\nsoup = BeautifulSoup(response.text, "html.parser")\nquotes = soup.find_all("div", class_="quote")\nfor q in quotes:\n    text = q.find("span", class_="text").text\n    author = q.find("small", class_="author").text\n    print(f"{text} - {author}")</code></pre>'},
                    {'content_type': 'code', 'title': 'Practice: Web Scraper', 'order': 2, 'duration_minutes': 30,
                     'text_content': 'import requests\nfrom bs4 import BeautifulSoup\nimport csv\nimport time\n\nheaders = {"User-Agent": "Mozilla/5.0"}\nurl = "https://quotes.toscrape.com"\nresponse = requests.get(url, headers=headers)\nsoup = BeautifulSoup(response.text, "html.parser")\n\nquotes = soup.find_all("div", class_="quote")\nwith open("quotes.csv","w",newline="",encoding="utf-8") as f:\n    writer = csv.writer(f)\n    writer.writerow(["Quote","Author"])\n    for q in quotes:\n        text = q.find("span",class_="text").text\n        author = q.find("small",class_="author").text\n        writer.writerow([text,author])\nprint("Done!")'},
                    {'content_type': 'quiz', 'title': 'Lesson 9 Quiz', 'order': 3,
                     'quiz_data': self.make_quiz([
                         {'question': 'HTTP requests library?', 'options': ['BeautifulSoup', 'Requests', 'Scrapy', 'Selenium'], 'correct': 1},
                         {'question': 'BeautifulSoup does?', 'options': ['Requests', 'Parses HTML', 'JavaScript', 'Database'], 'correct': 1},
                         {'question': 'Check before scraping?', 'options': ['index.html', 'robots.txt', 'sitemap.xml', 'README'], 'correct': 1},
                         {'question': 'Find all elements?', 'options': ['find()', 'find_all()', 'select_one()', 'get()'], 'correct': 1},
                         {'question': 'Why delays?', 'options': ['JS load', 'Respect servers', 'Parsing', 'Required'], 'correct': 1},
                         {'question': 'User-Agent?', 'options': ['Password', 'Browser ID', 'Cookie', 'Token'], 'correct': 1},
                         {'question': 'Get attribute?', 'options': ['.text', '.get()', '.value', '.attr'], 'correct': 1},
                         {'question': 'Success status?', 'options': ['404', '500', '200', '301'], 'correct': 2},
                         {'question': 'Scrape private pages?', 'options': ['Always', 'Never', 'With auth', 'VPN'], 'correct': 2},
                         {'question': 'Ethical scraping?', 'options': ['Fast as possible', 'Respect rules', 'Private data', 'Ignore robots.txt'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 10
            {
                'title': 'Building REST APIs with Flask',
                'order': 10, 'is_free_preview': False,
                'description': 'Create web APIs with Flask framework.',
                'contents': [
                    {'content_type': 'text', 'title': 'Flask REST API', 'order': 1, 'duration_minutes': 30,
                     'text_content': '<h1>Flask API</h1><p>Install: <code>pip install flask flask-cors</code></p><h2>Basic API</h2><pre><code>from flask import Flask, jsonify, request\napp = Flask(__name__)\n\nbooks = [{"id":1,"title":"Python Basics"}]\n\n@app.route("/api/books", methods=["GET"])\ndef get_books():\n    return jsonify(books)\n\n@app.route("/api/books", methods=["POST"])\ndef create_book():\n    data = request.get_json()\n    book = {"id":len(books)+1, "title":data["title"]}\n    books.append(book)\n    return jsonify(book), 201\n\nif __name__ == "__main__":\n    app.run(debug=True)</code></pre><h2>HTTP Methods</h2><ul><li>GET - Read</li><li>POST - Create</li><li>PUT - Update</li><li>DELETE - Remove</li></ul>'},
                    {'content_type': 'code', 'title': 'Practice: Flask API', 'order': 2, 'duration_minutes': 35,
                     'text_content': 'from flask import Flask, jsonify, request, abort\napp = Flask(__name__)\n\ntasks = [{"id":1,"title":"Learn Python","done":False}]\n\n@app.route("/api/tasks",methods=["GET"])\ndef get_tasks():\n    return jsonify(tasks)\n\n@app.route("/api/tasks/<int:id>",methods=["GET"])\ndef get_task(id):\n    task = next((t for t in tasks if t["id"]==id),None)\n    if task is None: abort(404)\n    return jsonify(task)\n\n@app.route("/api/tasks/<int:id>",methods=["PUT"])\ndef update_task(id):\n    task = next((t for t in tasks if t["id"]==id),None)\n    if task is None: abort(404)\n    task["done"] = request.json.get("done",task["done"])\n    return jsonify(task)\n\n@app.route("/api/tasks/<int:id>",methods=["DELETE"])\ndef delete_task(id):\n    global tasks\n    tasks = [t for t in tasks if t["id"]!=id]\n    return jsonify({"message":"Deleted"})'},
                    {'content_type': 'quiz', 'title': 'Lesson 10 Quiz', 'order': 3,
                     'quiz_data': self.make_quiz([
                         {'question': 'Flask is?', 'options': ['Database', 'Web framework', 'Editor', 'Package manager'], 'correct': 1},
                         {'question': 'POST creates?', 'options': ['Yes', 'No', 'Sometimes', 'Only with GET'], 'correct': 0},
                         {'question': 'Created status code?', 'options': ['200', '201', '404', '500'], 'correct': 1},
                         {'question': 'jsonify() does?', 'options': ['Parses', 'Returns JSON response', 'Validates', 'Saves'], 'correct': 1},
                         {'question': 'Route is?', 'options': ['File path', 'URL mapping', 'Table', 'Template'], 'correct': 1},
                         {'question': '@app.route() does?', 'options': ['Imports', 'Maps URL to function', 'Creates DB', 'Renders template'], 'correct': 1},
                         {'question': 'Not Found code?', 'options': ['200', '201', '404', '500'], 'correct': 2},
                         {'question': 'CORS?', 'options': ['Database', 'Cross-Origin Resource Sharing', 'Template', 'Auth'], 'correct': 1},
                         {'question': 'Access JSON data?', 'options': ['request.data', 'request.json', 'request.body', 'request.params'], 'correct': 1},
                         {'question': 'REST stands for?', 'options': ['Real-Time State Transfer', 'Representational State Transfer', 'Remote Service Transfer', 'Request State Transport'], 'correct': 1},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 11
            {
                'title': 'Database Management with SQLite',
                'order': 11, 'is_free_preview': False,
                'description': 'Learn SQL and database operations with SQLite.',
                'contents': [
                    {'content_type': 'text', 'title': 'SQLite and SQL Basics', 'order': 1, 'duration_minutes': 30,
                     'text_content': '<h1>SQLite Database</h1><pre><code>import sqlite3\nconn = sqlite3.connect("mydb.db")\nc = conn.cursor()\n\n# Create table\nc.execute("""CREATE TABLE IF NOT EXISTS users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL,\n    email TEXT UNIQUE,\n    age INTEGER\n)""")\n\n# Insert\nc.execute("INSERT INTO users (name,email,age) VALUES (?,?,?)",\n          ("Alice","alice@email.com",25))\n\n# Query\nc.execute("SELECT * FROM users WHERE age > ?", (20,))\nfor row in c.fetchall():\n    print(row)\n\nconn.commit()\nconn.close()</code></pre><h2>CRUD Operations</h2><ul><li>Create: INSERT INTO</li><li>Read: SELECT</li><li>Update: UPDATE</li><li>Delete: DELETE</li></ul>'},
                    {'content_type': 'quiz', 'title': 'Lesson 11 Quiz', 'order': 2,
                     'quiz_data': self.make_quiz([
                         {'question': 'CRUD stands for?', 'options': ['Create,Read,Update,Delete', 'Copy,Run,Undo,Debug', 'Compile,Run,Upload,Download', 'Connect,Read,Use,Disconnect'], 'correct': 0},
                         {'question': 'Retrieve data command?', 'options': ['INSERT', 'SELECT', 'UPDATE', 'DELETE'], 'correct': 1},
                         {'question': 'Primary key is?', 'options': ['First column', 'Unique identifier', 'Foreign key', 'Index'], 'correct': 1},
                         {'question': 'Parameterized queries prevent?', 'options': ['Slow queries', 'SQL injection', 'Memory leaks', 'Syntax errors'], 'correct': 1},
                         {'question': 'SQLite stores data in?', 'options': ['Cloud', 'RAM', 'Single file', 'Multiple servers'], 'correct': 2},
                         {'question': 'Filter clause?', 'options': ['ORDER BY', 'WHERE', 'GROUP BY', 'HAVING'], 'correct': 1},
                         {'question': 'INSERT OR IGNORE?', 'options': ['Always inserts', 'Skips duplicates', 'Updates existing', 'Deletes old'], 'correct': 1},
                         {'question': 'Sort descending?', 'options': ['SORT DESC', 'ORDER BY col DESC', 'ORDER DESC', 'SORT col DESC'], 'correct': 1},
                         {'question': 'Foreign key?', 'options': ['Key from abroad', 'Link between tables', 'Encryption key', 'Primary key copy'], 'correct': 1},
                         {'question': 'SQLite for production?', 'options': ['Always', 'Never', 'Small/medium apps', 'Testing only'], 'correct': 2},
                     ]), 'passing_score': 70},
                ]
            },
            # LESSON 12
            {
                'title': 'Final Project: Building a Portfolio Website',
                'order': 12, 'is_free_preview': False,
                'description': 'Apply all skills to build and deploy a complete portfolio website.',
                'contents': [
                    {'content_type': 'text', 'title': 'Project Overview', 'order': 1, 'duration_minutes': 30,
                     'text_content': '<h1>Final Project: Portfolio Website</h1><p>Congratulations! Apply everything you\'ve learned to build a complete portfolio website with Flask and SQLite.</p><h2>Features</h2><ol><li>Home page with introduction</li><li>Projects page from database</li><li>Blog with CRUD operations</li><li>Contact form with database storage</li><li>Responsive design</li></ol><h2>Tech Stack</h2><ul><li>Flask (web framework)</li><li>SQLite (database)</li><li>HTML/CSS (templates)</li><li>Python (backend logic)</li></ul>'},
                    {'content_type': 'text', 'title': 'Deployment Guide', 'order': 2, 'duration_minutes': 20,
                     'text_content': '<h1>Deploying Your Application</h1><h2>Platforms</h2><ul><li><strong>PythonAnywhere:</strong> Free, easiest for beginners</li><li><strong>Render:</strong> Free tier, Git integration</li><li><strong>Railway:</strong> Modern, free tier available</li></ul><h2>Steps</h2><ol><li>Create requirements.txt: <code>pip freeze > requirements.txt</code></li><li>Push code to GitHub</li><li>Connect platform to your repository</li><li>Configure environment variables</li><li>Deploy!</li></ol>'},
                    {'content_type': 'assignment', 'title': 'Build Your Portfolio', 'order': 3,
                     'assignment_instructions': '<h3>Requirements (100 points)</h3><ol><li>Database setup (15 pts)</li><li>Home page (15 pts)</li><li>Projects page (20 pts)</li><li>Contact form (20 pts)</li><li>Responsive design (15 pts)</li><li>Deployment (15 pts)</li></ol><h4>Bonus (10 pts)</h4><ul><li>User authentication</li><li>File uploads</li><li>Admin panel</li></ul>',
                     'max_score': 100},
                    {'content_type': 'quiz', 'title': 'Lesson 12 Quiz: Final Review', 'order': 4,
                     'quiz_data': self.make_quiz([
                         {'question': 'Web framework used?', 'options': ['Django', 'Flask', 'FastAPI', 'Pyramid'], 'correct': 1},
                         {'question': 'Database used?', 'options': ['MySQL', 'PostgreSQL', 'SQLite', 'MongoDB'], 'correct': 2},
                         {'question': 'CRUD means?', 'options': ['Create,Read,Update,Delete', 'Copy,Run,Undo,Debug', 'Compile,Run,Upload,Deploy', 'None'], 'correct': 0},
                         {'question': 'Decorator function?', 'options': ['Design pattern', 'Function modifier', 'Class', 'Variable'], 'correct': 1},
                         {'question': 'requirements.txt?', 'options': ['Passwords', 'Dependencies list', 'Config', 'Docs'], 'correct': 1},
                         {'question': 'pip freeze does?', 'options': ['Stops pip', 'Lists installed packages', 'Uninstalls', 'Updates Python'], 'correct': 1},
                         {'question': 'Virtual environment?', 'options': ['Cloud', 'Isolated Python env', 'Editor', 'Database'], 'correct': 1},
                         {'question': 'POST creates?', 'options': ['Yes', 'No', 'Only with PUT', 'Only with GET'], 'correct': 0},
                         {'question': 'try/except purpose?', 'options': ['Loops', 'Error handling', 'Files', 'Database'], 'correct': 1},
                         {'question': 'Free deployment platform?', 'options': ['AWS only', 'PythonAnywhere', 'Word', 'Photoshop'], 'correct': 1},
                     ]), 'passing_score': 70},
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
                self.stdout.write(f'  ✓ Lesson {lesson.order}: {lesson.title}')
            else:
                self.stdout.write(f'  ⚠ Lesson exists: {lesson.title}')