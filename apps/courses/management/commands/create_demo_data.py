from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import random

from apps.accounts.models import CustomUser, StudentProfile
from apps.courses.models import Course, Enrollment, CourseReview


class Command(BaseCommand):
    help = 'Creates students, enrolls them in ALL courses with uneven distribution, and adds unique reviews'

    COMMON_PASSWORD = "AIGA@2024!Secure#Learning"
    TOTAL_STUDENTS = 377

    UK_FIRST_NAMES = [
        "Oliver", "George", "Harry", "Jack", "Jacob", "Noah", "Charlie", "Thomas",
        "Oscar", "William", "James", "Henry", "Leo", "Alfie", "Freddie", "Archie",
        "Joshua", "Theo", "Logan", "Lucas", "Finley", "Max", "Ethan", "Isaac",
        "Muhammad", "Arthur", "Teddy", "Edward", "Harrison", "Benjamin", "Alexander", "Joseph",
        "Sebastian", "Samuel", "David", "Daniel", "Reuben", "Jude", "Elijah", "Jenson",
        "Rory", "Angus", "Hamish", "Callum", "Fraser", "Ewan", "Lachlan", "Cameron",
        "Alistair", "Rupert", "Hugo", "Tobias", "Jasper", "Felix", "Barnaby", "Piers",
        "Nigel", "Simon", "Martin", "Colin", "Graham", "Keith", "Trevor", "Derek",
        "Clive", "Roger", "Barry", "Terry", "Malcolm", "Gordon", "Stuart", "Ian",
        "Duncan", "Fergus", "Gavin", "Iain", "Kenneth", "Montgomery", "Neville", "Oswald",
        "Percival", "Quentin", "Reginald", "Stanley", "Wilfred", "Cyril", "Cecil", "Edwin",
        "Ernest", "Gilbert", "Herbert", "Leonard", "Norman", "Ralph", "Sidney", "Victor",
        "Walter", "Bernard", "Clifford", "Desmond", "Edmund", "Francis", "Geoffrey", "Horace",
        "Humphrey", "Laurence", "Maurice", "Raymond", "Olivia", "Amelia", "Isla", "Ava",
        "Emily", "Sophie", "Grace", "Mia", "Poppy", "Ella", "Charlotte", "Lily",
        "Sophia", "Isabella", "Evie", "Freya", "Daisy", "Florence", "Alice", "Phoebe",
        "Sienna", "Matilda", "Ivy", "Harriet", "Ruby", "Evelyn", "Willow", "Elsie",
        "Rosie", "Imogen", "Esme", "Maisie", "Arabella", "Beatrice", "Cordelia", "Delilah",
        "Eleanor", "Felicity", "Georgina", "Henrietta", "Jemima", "Katherine", "Lavinia", "Margot",
        "Penelope", "Philippa", "Rosalind", "Tabitha", "Victoria", "Winifred", "Agatha", "Beryl",
        "Cynthia", "Dorothy", "Edith", "Fiona", "Geraldine", "Hazel", "Iris", "Joan",
        "Kathleen", "Lorna", "Mabel", "Nora", "Olive", "Pamela", "Queenie", "Rita",
        "Sheila", "Tilly", "Ursula", "Vera", "Wendy", "Yvonne", "Zelda", "Audrey",
        "Brenda", "Carol", "Diana", "Eileen", "Gillian", "Helen", "Janet", "Karen",
        "Linda", "Margaret", "Nicola", "Patricia", "Rebecca", "Sandra", "Tracey", "Valerie",
    ]

    UK_LAST_NAMES = [
        "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies",
        "Robinson", "Wright", "Thompson", "Evans", "Walker", "White", "Roberts", "Green",
        "Hall", "Wood", "Jackson", "Clarke", "Patel", "Khan", "Lewis", "Harris",
        "Martin", "Lee", "Turner", "Cooper", "Hill", "Ward", "Morris", "Moore",
        "Clark", "King", "Baker", "Harrison", "Morgan", "Allen", "James", "Scott",
        "Phillips", "Watson", "Davis", "Parker", "Price", "Bennett", "Young", "Griffiths",
        "Mitchell", "Kelly", "Cook", "Carter", "Bailey", "Richardson", "Cox", "Howard",
        "Hughes", "Bell", "Shaw", "Murphy", "Miller", "Reed", "Simpson", "Marshall",
        "Collins", "Ellis", "Foster", "Gray", "Holmes", "Hunter", "Chapman", "Webb",
        "Mason", "Knight", "Stone", "Bishop", "Sharp", "Wells", "Dixon", "Gibson",
        "Grant", "Reid", "Murray", "Graham", "Hamilton", "Ferguson", "Stewart", "Cameron",
        "Campbell", "MacDonald", "Mackenzie", "Sinclair", "Wallace", "Burns", "Douglas", "Fraser",
        "Gordon", "Henderson", "Kennedy", "Lennox", "Montgomery", "Munro", "Ross", "Sutherland",
        "Balfour", "Barclay", "Chisholm", "Drummond", "Elliot", "Forbes", "Hay", "Innes",
        "Kerr", "Lamont", "MacLeod", "MacPherson", "Chamberlain", "Churchill", "Cromwell", "Disraeli",
        "Gladstone", "Pitt", "Thatcher", "Wellington", "Austen", "Bronte", "Dickens", "Eliot",
        "Hardy", "Keats", "Milton", "Shakespeare", "Tennyson", "Wilde", "Wordsworth", "Yeats",
        "Beckett", "Joyce", "Swift", "Armstrong", "Atkinson", "Barker", "Barnes", "Baxter",
        "Bentley", "Blake", "Bond", "Booth", "Bradley", "Briggs", "Brooks", "Burgess",
        "Burton", "Butler", "Byrne", "Carpenter", "Carr", "Chandler", "Cole", "Collier",
        "Connor", "Cross", "Curtis", "Dale", "Dalton", "Dawson", "Day", "Dean",
        "Dennis", "Dobson", "Dodd", "Doyle", "Drake", "Duffy", "Duncan", "Dunn",
        "Dyer", "Eaton", "Eden", "Edwards", "Ellison", "Farrell", "Field", "Finch",
        "Fisher", "Fletcher", "Flint", "Flynn", "Ford", "Forrest", "Fox", "Francis",
        "Franklin", "French", "Frost", "Gale", "Gardner", "Garner", "Gates", "Gibbs",
        "Gilbert", "Giles", "Gill", "Glover", "Goodman", "Goodwin", "Gore", "Gough",
        "Gould", "Graves", "Gregory", "Griffin", "Hale", "Hammond", "Hancock", "Harding",
        "Hardy", "Harper", "Harrington", "Hart", "Harvey", "Hawkins", "Hayes", "Haynes",
    ]

    NIGERIAN_NAMES = [
        ("Adeyemi", "Okafor"), ("Chidinma", "Eze"), ("Olumide", "Adebayo"),
        ("Ngozi", "Okonkwo"), ("Emeka", "Nwachukwu"), ("Aisha", "Mohammed"),
        ("Tunde", "Adeyemi"), ("Chiamaka", "Obi"), ("Ibrahim", "Suleiman"),
        ("Folake", "Adebisi"), ("Oluwaseun", "Ogunleye"), ("Chika", "Nwosu"),
    ]

    INTERNATIONAL_NAMES = [
        ("Lars", "Andersen"), ("Mette", "Nielsen"), ("Erik", "Johansson"), ("Astrid", "Lindgren"),
        ("Kai", "Kobayashi"), ("Yuki", "Tanaka"), ("Min-Jun", "Kim"), ("Ji-woo", "Park"),
        ("Wei", "Chen"), ("Li", "Wang"), ("Arjun", "Sharma"), ("Priya", "Patel"),
        ("Mateo", "Garcia"), ("Lucia", "Fernandez"), ("Lucas", "Silva"), ("Ana", "Santos"),
        ("Marco", "Rossi"), ("Giulia", "Bianchi"), ("Lukas", "Muller"), ("Anna", "Schmidt"),
        ("Pierre", "Dubois"), ("Marie", "Laurent"), ("Sven", "Van der Berg"), ("Emma", "Janssen"),
        ("Ivan", "Petrov"), ("Olga", "Ivanova"), ("Ahmed", "Hassan"), ("Fatima", "Ali"),
        ("Omar", "Khan"), ("Aisha", "Malik"), ("Carlos", "Mendoza"), ("Sofia", "Lopez"),
        ("David", "Cohen"), ("Sarah", "Levi"), ("John", "O'Brien"), ("Siobhan", "Murphy"),
        ("Dimitri", "Papadopoulos"), ("Eleni", "Nikolaou"), ("Hasan", "Yilmaz"), ("Zeynep", "Demir"),
        ("Jan", "Kowalski"), ("Anna", "Nowak"), ("Pavel", "Novak"), ("Jana", "Svobodova"),
        ("Raj", "Kumar"), ("Mei", "Zhang"), ("Hiroshi", "Sato"), ("Ingrid", "Larsson"),
        ("Bjorn", "Olsen"), ("Leila", "Haddad"), ("Tariq", "Aziz"), ("Nadia", "Karim"),
        ("Sergei", "Volkov"), ("Natasha", "Romanova"), ("Andre", "Moreau"), ("Claire", "Fontaine"),
        ("Hans", "Weber"), ("Greta", "Fischer"), ("Giovanni", "Romano"), ("Francesca", "Conti"),
        ("Joao", "Oliveira"), ("Maria", "Costa"), ("Piotr", "Wisniewski"), ("Katarzyna", "Wojcik"),
        ("Anders", "Lindholm"), ("Karin", "Bjork"), ("Mikhail", "Sokolov"), ("Anastasia", "Volkova"),
        ("Chen", "Wang"), ("Xiao", "Li"), ("Yuki", "Nakamura"), ("Sakura", "Yamamoto"),
        ("Ravi", "Patel"), ("Ananya", "Sharma"), ("Diego", "Hernandez"), ("Camila", "Torres"),
    ]

    # Reviews for each course
    GOVERNANCE_REVIEWS = [
        {"title": "Essential training for UK compliance professionals", "review": "This course provides exceptional insight into AI governance for UK organisations. The ICO guidance coverage is directly applicable to our compliance programme."},
        {"title": "Outstanding coverage of UK AI regulations", "review": "As a compliance officer, the sections on UK GDPR and the EU AI Act were incredibly relevant. The instructor demonstrates deep expertise."},
        {"title": "A must-have for governance professionals", "review": "The modules on building an AI governance framework were practical and immediately implementable. Highly recommended for UK organisations."},
        {"title": "Practical guidance on ICO expectations", "review": "A comprehensive exploration of what the ICO expects from organisations using AI. The risk management frameworks are excellent."},
        {"title": "Excellent insights into regulatory compliance", "review": "This training exceeded expectations with coverage of AI governance, data protection, and ethical considerations for UK organisations."},
        {"title": "Comprehensive AI governance training", "review": "The case studies on real-world AI compliance failures were eye-opening. This course has changed how our team approaches AI governance."},
        {"title": "Perfect for UK compliance teams", "review": "Excellent coverage of the UK's pro-innovation approach to AI regulation. The guidance on building compliant AI systems is invaluable."},
        {"title": "Invaluable resource for risk managers", "review": "The sections on AI risk assessment and management were particularly useful for our internal audit processes."},
        {"title": "Critical knowledge for UK organisations", "review": "The course provides thorough understanding of AI governance frameworks for the UK market. Exceptionally well-structured."},
        {"title": "Top-tier instruction on AI governance", "review": "This course gave me the knowledge needed to lead AI governance initiatives at my organisation. Highly recommended."},
        {"title": "Exceptional depth on UK regulatory frameworks", "review": "The modules on transparency and explainability were outstanding. Essential for anyone working with AI in the UK."},
        {"title": "Groundbreaking course for governance teams", "review": "The depth of coverage on AI risk assessment and application to UK organisations is impressive. Practical templates provided."},
        {"title": "Superb coverage of AI ethics in the UK", "review": "This course addresses unique challenges of responsible AI in UK organisations. The instructor's expertise is evident throughout."},
        {"title": "Masterclass in AI governance", "review": "The guidance on AI governance frameworks and stakeholder engagement was excellent. Significantly improved our approach."},
        {"title": "Indispensable training for UK leaders", "review": "Outstanding training bridging technical understanding and regulatory compliance. The EU AI Act sections were forward-thinking."},
        {"title": "World-class instruction on AI governance", "review": "Meticulously organised course covering AI fundamentals to advanced governance. Practical exercises reinforced my learning."},
        {"title": "Exceptional resource for compliance professionals", "review": "This stands out for depth and practical application. The instructor's real-world experience is evident."},
        {"title": "Comprehensive coverage of UK AI regulations", "review": "Excellent explanations of complex regulatory requirements. The ICO auditing framework sections were eye-opening."},
        {"title": "Practical AI governance for UK organisations", "review": "The templates and checklists provided are worth the price. I've implemented several governance practices already."},
        {"title": "Excellent course for compliance teams", "review": "Technical depth combined with clear governance guidance. Bridges the gap between IT and regulations perfectly."},
        {"title": "Vital training for AI-enabled organisations", "review": "AI governance frameworks and compliance implications were particularly relevant. A comprehensive learning experience."},
        {"title": "Professional development at its finest", "review": "This course has become essential for our team's development programme. Quality of instruction is consistently excellent."},
        {"title": "Forward-thinking AI governance education", "review": "Anticipates future regulatory trends in AI. I feel prepared for upcoming compliance changes in the UK."},
        {"title": "In-depth coverage of critical governance topics", "review": "From bias mitigation to algorithm transparency, every aspect is thoroughly addressed with practical examples."},
        {"title": "Excellent investment for career development", "review": "Completing this course has enhanced my professional credentials. Knowledge is directly applicable to my role."},
        {"title": "Comprehensive and up-to-date curriculum", "review": "Content reflects latest developments in AI regulation and UK best practices. Emerging frameworks well covered."},
        {"title": "Outstanding educational experience", "review": "Interactive elements and practical assignments made learning engaging. Actionable insights I can apply immediately."},
        {"title": "Must-take course for governance professionals", "review": "The most comprehensive course on AI governance for UK organisations available. Quality exceeds anything I've experienced."},
        {"title": "Excellent balance of theory and practice", "review": "Perfect balance between theoretical frameworks and practical application. Real UK case studies were valuable."},
        {"title": "Highly recommended for serious professionals", "review": "If you're serious about AI governance in the UK, this course is essential. The instructor's depth is impressive."},
    ]

    COMPLIANCE_REVIEWS = [
        {"title": "Essential for UK compliance officers", "review": "This course provides exceptional insight into AI compliance for UK organisations. The ICO enforcement sections are directly applicable."},
        {"title": "Outstanding coverage of compliance frameworks", "review": "As a compliance manager, the sections on DPIAs and algorithmic auditing were incredibly relevant and practical."},
        {"title": "A must-have for compliance teams", "review": "The modules on incident response and reporting were practical and immediately implementable. Highly recommended."},
        {"title": "Practical guidance on ICO expectations", "review": "A comprehensive exploration of what the ICO expects. The compliance monitoring frameworks are excellent."},
        {"title": "Excellent insights into AI compliance", "review": "This training exceeded expectations with coverage of bias testing, transparency, and compliance monitoring."},
        {"title": "Comprehensive AI compliance training", "review": "The case studies on real-world compliance failures were eye-opening. This course has changed our approach."},
        {"title": "Perfect for UK compliance professionals", "review": "Excellent coverage of UK AI compliance requirements. The guidance on DPIAs is invaluable."},
        {"title": "Invaluable resource for auditors", "review": "The sections on algorithmic auditing and bias testing were particularly useful for our audit processes."},
        {"title": "Critical knowledge for compliance teams", "review": "The course provides thorough understanding of AI compliance frameworks. Exceptionally well-structured."},
        {"title": "Top-tier instruction on compliance", "review": "This course gave me the knowledge needed to lead compliance initiatives. Highly recommended."},
        {"title": "Exceptional depth on compliance monitoring", "review": "The modules on ongoing compliance monitoring were outstanding. Essential for UK organisations."},
        {"title": "Groundbreaking course for compliance", "review": "The depth of coverage on AI auditing is impressive. Practical templates provided throughout."},
        {"title": "Superb coverage of compliance requirements", "review": "This course addresses unique challenges of AI compliance in the UK. The instructor's expertise is evident."},
        {"title": "Masterclass in AI compliance", "review": "The guidance on compliance frameworks was excellent. Significantly improved our approach."},
        {"title": "Indispensable training for compliance leaders", "review": "Outstanding training bridging technical and regulatory compliance. Forward-thinking content."},
        {"title": "World-class instruction on compliance", "review": "Meticulously organised course covering compliance fundamentals to advanced topics."},
        {"title": "Exceptional resource for compliance teams", "review": "This stands out for depth and practical application. Real-world experience is evident."},
        {"title": "Comprehensive coverage of compliance topics", "review": "Excellent explanations of complex requirements. The enforcement sections were eye-opening."},
        {"title": "Practical AI compliance for UK teams", "review": "The templates and checklists are worth the price. Implemented several practices already."},
        {"title": "Excellent course for compliance officers", "review": "Technical depth combined with clear compliance guidance. Bridges the gap perfectly."},
        {"title": "Vital training for compliance professionals", "review": "Compliance frameworks and implications were particularly relevant. Comprehensive experience."},
        {"title": "Professional development at its finest", "review": "This course has become essential for our compliance team. Quality is consistently excellent."},
        {"title": "Forward-thinking compliance education", "review": "Anticipates future trends in AI compliance. Prepared for upcoming changes."},
        {"title": "In-depth coverage of compliance topics", "review": "Every aspect thoroughly addressed with practical examples."},
        {"title": "Excellent investment for career growth", "review": "Enhanced my professional credentials. Knowledge directly applicable."},
        {"title": "Comprehensive and current curriculum", "review": "Content reflects latest developments. Emerging frameworks well covered."},
        {"title": "Outstanding educational experience", "review": "Interactive elements made learning engaging. Actionable insights."},
        {"title": "Must-take for compliance professionals", "review": "Most comprehensive AI compliance course available. Quality exceeds expectations."},
        {"title": "Excellent balance of theory and practice", "review": "Perfect balance between theory and application. Real UK case studies valuable."},
        {"title": "Highly recommended for compliance teams", "review": "Essential for AI compliance in the UK. Instructor's depth is impressive."},
    ]

    RESPONSIBLE_AI_REVIEWS = [
        {"title": "Excellent free introduction to responsible AI", "review": "This free course provides a solid foundation in responsible AI development. The UK ethical guidelines sections are excellent."},
        {"title": "Great starting point for AI ethics", "review": "As someone new to AI ethics, this course was perfect. The fairness and bias sections were particularly insightful."},
        {"title": "Valuable free resource for professionals", "review": "The transparency and explainability modules were outstanding. Excellent introduction to responsible AI."},
        {"title": "Perfect introduction to ethical AI", "review": "Clear, concise, and practical. The human oversight sections were particularly valuable for my work."},
        {"title": "Excellent overview of AI ethics in the UK", "review": "The UK-specific content was incredibly helpful. Great foundation for further study in AI governance."},
        {"title": "High-quality free course on responsible AI", "review": "The privacy and data protection modules were excellent. Well-structured and easy to follow."},
        {"title": "Essential introduction to AI accountability", "review": "The accountability and oversight frameworks were clearly explained. Valuable for anyone working with AI."},
        {"title": "Great educational resource for AI ethics", "review": "The safety and security sections were comprehensive. Excellent free course for beginners."},
        {"title": "Practical introduction to responsible AI", "review": "The bias detection guidance was immediately applicable. Highly recommended for professionals."},
        {"title": "Excellent foundation in AI ethics", "review": "The UK-specific examples made this course particularly relevant. Great learning experience."},
        {"title": "Outstanding free course on AI principles", "review": "The fairness and non-discrimination modules were excellent. Essential for responsible AI development."},
        {"title": "Valuable insights into AI transparency", "review": "The explainability sections were particularly useful. Great introduction to responsible AI."},
        {"title": "Excellent primer on ethical AI development", "review": "The privacy by design principles were clearly explained. Highly recommended for beginners."},
        {"title": "Comprehensive introduction to AI ethics", "review": "The human oversight sections were outstanding. Perfect starting point for AI governance."},
        {"title": "High-quality educational resource", "review": "The accountability frameworks were clearly explained. Excellent free course."},
        {"title": "Great introduction to responsible AI practices", "review": "The safety and security modules were comprehensive. Valuable for professionals."},
        {"title": "Essential free course on AI ethics", "review": "The UK ethical guidelines sections were excellent. Great foundation for further learning."},
        {"title": "Practical guidance on AI fairness", "review": "The bias reduction strategies were immediately applicable. Highly recommended."},
        {"title": "Excellent educational resource for beginners", "review": "Clear explanations of complex concepts. Great introduction to responsible AI."},
        {"title": "Outstanding introduction to AI accountability", "review": "The oversight frameworks were clearly explained. Valuable for professionals."},
        {"title": "Valuable free resource on AI ethics", "review": "The transparency sections were particularly insightful. Great learning experience."},
        {"title": "Excellent primer on responsible AI", "review": "The fairness and bias modules were outstanding. Perfect for beginners."},
        {"title": "High-quality introduction to AI governance", "review": "The UK-specific content was incredibly helpful. Great foundation."},
        {"title": "Comprehensive free course on AI ethics", "review": "The privacy sections were excellent. Well-structured and informative."},
        {"title": "Essential introduction to AI safety", "review": "The safety and security modules were comprehensive. Valuable for professionals."},
        {"title": "Great educational resource on responsible AI", "review": "The human oversight sections were outstanding. Excellent free course."},
        {"title": "Practical guidance on ethical AI development", "review": "The accountability frameworks were clearly explained. Highly recommended."},
        {"title": "Excellent foundation in AI ethics", "review": "The UK examples made this course particularly relevant. Great learning experience."},
        {"title": "Outstanding free course on AI principles", "review": "The fairness modules were excellent. Essential for responsible AI."},
        {"title": "Highly recommended introduction to AI ethics", "review": "Essential free course for anyone working with AI. Quality exceeds expectations."},
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting demo data creation and enrollment...'))
        
        courses = list(Course.objects.filter(status='published'))
        
        if not courses:
            self.stdout.write(self.style.ERROR('No published courses found!'))
            return
        
        self.stdout.write(f'Found {len(courses)} published courses')
        self.stdout.write(f'Common password: {self.COMMON_PASSWORD}')
        
        # Identify courses
        governance_course = None
        compliance_course = None
        responsible_ai_course = None
        other_courses = []
        
        for course in courses:
            if 'AI Governance' in course.title:
                governance_course = course
            elif 'Compliance' in course.title:
                compliance_course = course
            elif 'Responsible AI' in course.title or 'Responsible' in course.title:
                responsible_ai_course = course
            else:
                other_courses.append(course)
        
        self.stdout.write(f'   Governance Course: {governance_course.title if governance_course else "Not found"}')
        self.stdout.write(f'   Compliance Course: {compliance_course.title if compliance_course else "Not found"}')
        self.stdout.write(f'   Responsible AI Course: {responsible_ai_course.title if responsible_ai_course else "Not found"}')
        if other_courses:
            for oc in other_courses:
                self.stdout.write(f'   Other Course: {oc.title}')
        
        created_count = 0
        enrolled_count = 0
        review_count = 0
        governance_enrollments = 0
        compliance_enrollments = 0
        responsible_ai_enrollments = 0
        governance_reviews = 0
        compliance_reviews = 0
        responsible_ai_reviews = 0
        used_reviews = {}
        
        with open('student_credentials.txt', 'w') as f:
            f.write("AI GOVERNANCE ACADEMY - STUDENT CREDENTIALS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Common Password: {self.COMMON_PASSWORD}\n")
            f.write("=" * 60 + "\n")
            f.write("Format: Email | Full Name | Location\n")
            f.write("=" * 60 + "\n\n")
        
        with transaction.atomic():
            for i in range(1, self.TOTAL_STUDENTS + 1):
                email = f'student{i:03d}@aiga.ac'
                
                # Check if student exists, if not create
                user = CustomUser.objects.filter(email=email).first()
                
                if not user:
                    # Name distribution: UK 90%, Nigeria 3%, International 7%
                    if i <= 339:  # 90% UK
                        first_name = random.choice(self.UK_FIRST_NAMES)
                        last_name = random.choice(self.UK_LAST_NAMES)
                        location = "United Kingdom"
                    elif i <= 350:  # ~3% Nigeria
                        first_name, last_name = random.choice(self.NIGERIAN_NAMES)
                        location = "Nigeria"
                    else:  # ~7% International
                        first_name, last_name = random.choice(self.INTERNATIONAL_NAMES)
                        location = "International"
                    
                    user = CustomUser.objects.create_user(
                        email=email,
                        password=self.COMMON_PASSWORD,
                        first_name=first_name,
                        last_name=last_name,
                        user_type='STUDENT',
                        is_active=True,
                        is_verified=True,
                        email_verified=True,
                    )
                    
                    StudentProfile.objects.create(
                        user=user,
                        student_id=f'STU{i:04d}',
                        enrollment_date=timezone.now().date(),
                    )
                    
                    created_count += 1
                    created_now = True
                else:
                    first_name = user.first_name
                    last_name = user.last_name
                    location = "Existing"
                    created_now = False
                
                # ENROLLMENT LOGIC - Enroll regardless of whether student existed
                if governance_course:
                    if random.random() < 0.85:  # 85% enroll
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=user,
                            course=governance_course,
                            defaults={
                                'status': random.choice(['active', 'completed']),
                                'progress_percentage': random.randint(60, 100),
                            }
                        )
                        if created:
                            enrolled_count += 1
                            governance_enrollments += 1
                        
                        # 70% of enrolled students leave review
                        if random.random() < 0.70:
                            if not CourseReview.objects.filter(student=user, course=governance_course).exists():
                                review_index = self.get_unique_review_index(used_reviews, governance_course.title, len(self.GOVERNANCE_REVIEWS))
                                rating = random.choices([4, 5], weights=[25, 75])[0]
                                CourseReview.objects.create(
                                    student=user,
                                    course=governance_course,
                                    rating=rating,
                                    title=self.GOVERNANCE_REVIEWS[review_index]["title"],
                                    review=self.GOVERNANCE_REVIEWS[review_index]["review"],
                                    is_recommended=True,
                                )
                                review_count += 1
                                governance_reviews += 1
                
                if compliance_course:
                    if random.random() < 0.75:  # 75% enroll
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=user,
                            course=compliance_course,
                            defaults={
                                'status': random.choice(['active', 'completed']),
                                'progress_percentage': random.randint(60, 100),
                            }
                        )
                        if created:
                            enrolled_count += 1
                            compliance_enrollments += 1
                        
                        # 60% of enrolled students leave review
                        if random.random() < 0.60:
                            if not CourseReview.objects.filter(student=user, course=compliance_course).exists():
                                review_index = self.get_unique_review_index(used_reviews, compliance_course.title, len(self.COMPLIANCE_REVIEWS))
                                rating = random.choices([4, 5], weights=[30, 70])[0]
                                CourseReview.objects.create(
                                    student=user,
                                    course=compliance_course,
                                    rating=rating,
                                    title=self.COMPLIANCE_REVIEWS[review_index]["title"],
                                    review=self.COMPLIANCE_REVIEWS[review_index]["review"],
                                    is_recommended=True,
                                )
                                review_count += 1
                                compliance_reviews += 1
                
                if responsible_ai_course:
                    if random.random() < 0.60:  # 60% enroll (free course)
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=user,
                            course=responsible_ai_course,
                            defaults={
                                'status': random.choice(['active', 'completed']),
                                'progress_percentage': random.randint(60, 100),
                            }
                        )
                        if created:
                            enrolled_count += 1
                            responsible_ai_enrollments += 1
                        
                        # 50% of enrolled students leave review
                        if random.random() < 0.50:
                            if not CourseReview.objects.filter(student=user, course=responsible_ai_course).exists():
                                review_index = self.get_unique_review_index(used_reviews, responsible_ai_course.title, len(self.RESPONSIBLE_AI_REVIEWS))
                                rating = random.choices([4, 5], weights=[30, 70])[0]
                                CourseReview.objects.create(
                                    student=user,
                                    course=responsible_ai_course,
                                    rating=rating,
                                    title=self.RESPONSIBLE_AI_REVIEWS[review_index]["title"],
                                    review=self.RESPONSIBLE_AI_REVIEWS[review_index]["review"],
                                    is_recommended=True,
                                )
                                review_count += 1
                                responsible_ai_reviews += 1
                
                # Other courses - 40% enrollment
                for other_course in other_courses:
                    if random.random() < 0.40:
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=user,
                            course=other_course,
                            defaults={
                                'status': random.choice(['active', 'completed']),
                                'progress_percentage': random.randint(60, 100),
                            }
                        )
                        if created:
                            enrolled_count += 1
                
                # Update profile
                if hasattr(user, 'student_profile'):
                    student_profile = user.student_profile
                    student_profile.courses_enrolled = user.enrollments.filter(status='active').count()
                    student_profile.completed_courses = user.enrollments.filter(status='completed').count()
                    student_profile.save()
                
                with open('student_credentials.txt', 'a') as f:
                    f.write(f'{email} | {first_name} {last_name} | {location}\n')
                
                if i % 50 == 0:
                    self.stdout.write(f'   Processed {i} students so far...')
            
            self.stdout.write(self.style.SUCCESS('\nDEMO DATA CREATION AND ENROLLMENT COMPLETE!'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS(f'New Students Created: {created_count}'))
            self.stdout.write(self.style.SUCCESS(f'New Enrollments: {enrolled_count}'))
            self.stdout.write(self.style.SUCCESS(f'New Reviews: {review_count}'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS(f'AI Governance Enrollments: {governance_enrollments}'))
            self.stdout.write(self.style.SUCCESS(f'AI Governance Reviews: {governance_reviews}'))
            self.stdout.write(self.style.SUCCESS(f'AI Compliance Enrollments: {compliance_enrollments}'))
            self.stdout.write(self.style.SUCCESS(f'AI Compliance Reviews: {compliance_reviews}'))
            self.stdout.write(self.style.SUCCESS(f'Responsible AI Enrollments: {responsible_ai_enrollments}'))
            self.stdout.write(self.style.SUCCESS(f'Responsible AI Reviews: {responsible_ai_reviews}'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS(f'Common Password: {self.COMMON_PASSWORD}'))
            self.stdout.write(self.style.SUCCESS('Credentials saved to: student_credentials.txt'))
    
    def get_unique_review_index(self, used_reviews, course_key, pool_size):
        """Get a unique review index to avoid repetition"""
        if course_key not in used_reviews:
            used_reviews[course_key] = []
        
        available = list(range(pool_size))
        unused = [i for i in available if i not in used_reviews[course_key]]
        
        if not unused:
            used_reviews[course_key] = []
            unused = available
        
        index = random.choice(unused)
        used_reviews[course_key].append(index)
        return index