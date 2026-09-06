
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import CourseCategory, Course, Lesson, LessonContent
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = "Create the Basic AI Ethics & Governance course without quizzes"

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating Basic AI Ethics & Governance course...")

        category, _ = CourseCategory.objects.get_or_create(
            slug="ai-ethics-governance",
            defaults={
                "name": "AI Ethics & Governance",
                "description": (
                    "Responsible artificial intelligence, AI ethics, governance, "
                    "risk management, accountability and trustworthy AI."
                ),
                "icon": "fas fa-scale-balanced",
            },
        )

        instructor = CustomUser.objects.filter(
            user_type="INSTRUCTOR", is_active=True
        ).first()

        if not instructor:
            instructor = CustomUser.objects.filter(
                user_type="ADMIN", is_active=True
            ).first()

        if not instructor:
            instructor = CustomUser.objects.create_user(
                email="ai.ethics.instructor@aiga.ac",
                password="Instructor@123",
                first_name="AI",
                last_name="Governance",
                user_type="INSTRUCTOR",
                is_active=True,
                email_verified=True,
            )

        course, _ = Course.objects.update_or_create(
            slug="basic-ai-ethics-governance",
            defaults={
                "title": "Basic AI Ethics & Governance",
                "instructor": instructor,
                "category": category,
                "description": (
                    "A beginner-friendly course introducing the principles, practices "
                    "and responsibilities involved in developing, deploying and "
                    "governing artificial intelligence responsibly. Learners explore "
                    "fairness, transparency, privacy, accountability, safety, human "
                    "oversight, AI risk management and practical governance."
                ),
                "short_description": (
                    "Learn the fundamentals of responsible AI, ethical decision-making "
                    "and practical AI governance."
                ),
                "level": "beginner",
                "duration": "6 Weeks",
                "language": "English",
                "price": 39.99,
                "is_free": False,
                "status": "published",
                "has_certificate": True,
                "requirements": (
                    "No technical AI background is required. Basic computer literacy "
                    "and an interest in responsible technology are sufficient."
                ),
                "what_you_learn": (
                    "AI ethics fundamentals, responsible AI principles, fairness, "
                    "bias, transparency, explainability, privacy, data governance, "
                    "accountability, human oversight, AI safety, risk management, "
                    "governance frameworks and practical organizational controls."
                ),
                "published_at": timezone.now(),
            },
        )

        self.create_lessons(course)

        self.stdout.write(
            self.style.SUCCESS(
                "Basic AI Ethics & Governance course created successfully!"
            )
        )

    def text(
        self,
        title,
        order,
        html,
        minutes=30,
        preview=False,
    ):
        return {
            "content_type": "text",
            "title": title,
            "order": order,
            "duration_minutes": minutes,
            "is_preview": preview,
            "text_content": html,
        }

    def assignment(
        self,
        title,
        order,
        instructions,
        score=100,
        minutes=45,
    ):
        return {
            "content_type": "assignment",
            "title": title,
            "order": order,
            "duration_minutes": minutes,
            "assignment_instructions": instructions,
            "max_score": score,
        }

    def make_lesson(
        self,
        title,
        order,
        description,
        contents,
        preview=False,
    ):
        return {
            "title": title,
            "order": order,
            "description": description,
            "is_free_preview": preview,
            "contents": contents,
        }

    def create_lessons(self, course):
        lessons = [

            self.make_lesson(
                "Introduction to AI Ethics and Responsible AI",
                1,
                (
                    "Understand what AI ethics means, why responsible AI matters, "
                    "and the responsibilities of people and organizations using AI."
                ),
                [
                    self.text(
                        "What Is AI Ethics?",
                        1,
                        """<h1>What Is AI Ethics?</h1>

<p><strong>AI ethics</strong> is the study and practical application of principles
that help ensure artificial intelligence is designed, developed, deployed and used
in ways that respect people, rights, safety and society.</p>

<h2>Why AI Ethics Matters</h2>
<p>AI systems can influence important decisions involving employment, education,
finance, healthcare, security, public services and many other areas. When these
systems are poorly designed or poorly governed, they can create unfair outcomes,
privacy risks, safety problems or other forms of harm.</p>

<h2>Core Questions</h2>
<ul>
<li>Is the system being used for a legitimate and appropriate purpose?</li>
<li>Could the system unfairly disadvantage particular people or groups?</li>
<li>Are people informed about meaningful AI use?</li>
<li>Can the organization explain important decisions?</li>
<li>Is personal or sensitive information protected?</li>
<li>Who is responsible when something goes wrong?</li>
<li>Can humans intervene when necessary?</li>
</ul>

<div style="background:#dbeafe;padding:15px;border-radius:8px;">
<strong>Key idea:</strong> Responsible AI is not only a technical problem.
It requires technology, people, policies, processes and organizational accountability.
</div>""",
                        30,
                        True,
                    ),
                    self.text(
                        "Responsible AI Principles",
                        2,
                        """<h1>Responsible AI Principles</h1>

<p>Organizations often use a collection of principles to guide responsible AI.
The exact wording varies between organizations, but several themes appear repeatedly.</p>

<h2>Important Principles</h2>
<ul>
<li><strong>Fairness:</strong> Avoid unjustified discrimination and unfair outcomes.</li>
<li><strong>Transparency:</strong> Provide appropriate information about AI use and processes.</li>
<li><strong>Explainability:</strong> Make important AI-supported outcomes understandable where appropriate.</li>
<li><strong>Privacy:</strong> Protect personal information and respect privacy expectations.</li>
<li><strong>Accountability:</strong> Ensure responsible people and organizations can be identified.</li>
<li><strong>Safety:</strong> Reduce foreseeable risks and harmful failures.</li>
<li><strong>Human Oversight:</strong> Keep meaningful human involvement where appropriate.</li>
<li><strong>Security:</strong> Protect AI systems, data and models against misuse and attacks.</li>
</ul>

<h2>Principles Need Practical Controls</h2>
<p>A policy saying “AI must be fair” is not enough by itself. Organizations need
processes for identifying risks, testing systems, documenting decisions, monitoring
performance and responding to problems.</p>""",
                        35,
                    ),
                    self.assignment(
                        "Responsible AI Reflection",
                        3,
                        """<h3>Scenario</h3>
<p>Your organization plans to introduce an AI system that helps managers shortlist
job applicants.</p>

<h3>Task</h3>
<p>Write a short professional assessment identifying:</p>
<ol>
<li>Three possible ethical risks.</li>
<li>Three questions the organization should answer before deployment.</li>
<li>Three controls that could reduce the identified risks.</li>
<li>Who should be accountable for the final decision.</li>
</ol>

<p>Focus on fairness, privacy, transparency and human oversight.</p>""",
                        100,
                        40,
                    ),
                ],
                preview=True,
            ),

            self.make_lesson(
                "Understanding AI Systems, Data and Their Limitations",
                2,
                (
                    "Learn the basic relationship between AI models, data, outputs, "
                    "training processes and limitations."
                ),
                [
                    self.text(
                        "How AI Systems Work at a High Level",
                        1,
                        """<h1>AI Systems at a High Level</h1>

<p>Artificial intelligence is a broad field containing many different technologies.
Modern AI systems may use statistical models, machine learning, deep learning,
natural language processing, computer vision and generative AI.</p>

<h2>Simple Model</h2>
<ol>
<li><strong>Data:</strong> Information used to train, configure or operate a system.</li>
<li><strong>Model:</strong> A computational representation that learns patterns or relationships.</li>
<li><strong>Input:</strong> Information provided to the system.</li>
<li><strong>Processing:</strong> The system applies its model or rules.</li>
<li><strong>Output:</strong> A prediction, recommendation, classification, generated response or action.</li>
</ol>

<h2>Why This Matters for Ethics</h2>
<p>The quality and characteristics of data can influence model behavior. Design
choices can affect what a system optimizes for. Deployment context can also change
the consequences of an incorrect output.</p>""",
                        35,
                    ),
                    self.text(
                        "AI Limitations and Human Judgment",
                        2,
                        """<h1>AI Is Not Automatically Correct</h1>

<p>AI systems can produce incorrect, incomplete, biased or misleading results.
Generative AI can also produce convincing information that is factually incorrect.</p>

<h2>Common Limitations</h2>
<ul>
<li>Incomplete or poor-quality data</li>
<li>Bias in training or evaluation data</li>
<li>Distribution changes after deployment</li>
<li>Incorrect assumptions</li>
<li>Overconfidence in automated outputs</li>
<li>Unexpected behavior in unusual situations</li>
<li>Security and manipulation risks</li>
</ul>

<h2>Human Responsibility</h2>
<p>Human users should understand when AI outputs require verification. In high-impact
contexts, organizations should establish clear procedures for human review,
escalation and correction.</p>

<div style="background:#fef3c7;padding:15px;border-radius:8px;">
<strong>Remember:</strong> Automation can improve efficiency without eliminating
human responsibility.
</div>""",
                        35,
                    ),
                    self.assignment(
                        "AI System Risk Identification",
                        3,
                        """Choose an AI system you are familiar with, such as a chatbot,
recommendation system, fraud detection system or document-processing system.

Prepare a one-page analysis covering:
<ol>
<li>What the system is intended to do.</li>
<li>What data it may use.</li>
<li>What its outputs are.</li>
<li>Three limitations.</li>
<li>Two possible harms from incorrect outputs.</li>
<li>Where human review should occur.</li>
</ol>""",
                        100,
                        45,
                    ),
                ],
            ),

            self.make_lesson(
                "Fairness, Bias and Non-Discrimination in AI",
                3,
                (
                    "Understand algorithmic bias, sources of unfairness and practical "
                    "approaches for improving fairness."
                ),
                [
                    self.text(
                        "Understanding Bias in AI",
                        1,
                        """<h1>AI Bias</h1>

<p><strong>Bias</strong> can occur when an AI system systematically produces outcomes
that are unfair, inaccurate or disadvantageous for certain people or groups.</p>

<h2>Possible Sources</h2>
<ul>
<li>Historical patterns in data</li>
<li>Under-representation of groups</li>
<li>Measurement errors</li>
<li>Incorrect labels</li>
<li>Sampling problems</li>
<li>Features that act as proxies for protected characteristics</li>
<li>Design assumptions</li>
<li>Differences between development and deployment environments</li>
</ul>

<h2>Important Distinction</h2>
<p>Not every difference in outcomes automatically proves discrimination. Fairness
assessment requires understanding the purpose of the system, relevant populations,
context, data and applicable legal or organizational requirements.</p>""",
                        35,
                    ),
                    self.text(
                        "Practical Fairness Controls",
                        2,
                        """<h1>Managing Fairness Risk</h1>

<h2>Before Deployment</h2>
<ul>
<li>Identify potentially affected groups.</li>
<li>Review training and evaluation data.</li>
<li>Define appropriate fairness measures.</li>
<li>Test performance across relevant populations.</li>
<li>Document limitations and assumptions.</li>
</ul>

<h2>After Deployment</h2>
<ul>
<li>Monitor outcomes for unexpected disparities.</li>
<li>Provide channels for complaints or corrections.</li>
<li>Review changes in data and usage.</li>
<li>Investigate significant deviations.</li>
<li>Reassess the model periodically.</li>
</ul>

<p>Fairness is not always solved by one technical metric. It requires a combination
of technical evaluation, domain knowledge, governance and human judgment.</p>""",
                        35,
                    ),
                    self.assignment(
                        "Fairness Case Study",
                        3,
                        """<h3>Scenario</h3>
<p>An AI system helps prioritize applicants for a training program. After deployment,
staff notice that applicants from one demographic group are selected less frequently.</p>

<h3>Prepare an assessment</h3>
<ol>
<li>List possible explanations without assuming discrimination is proven.</li>
<li>Identify the data you would inspect.</li>
<li>Describe tests you would conduct.</li>
<li>Identify stakeholders who should participate in the review.</li>
<li>Recommend actions if an unfair pattern is confirmed.</li>
</ol>""",
                        100,
                        50,
                    ),
                ],
            ),

            self.make_lesson(
                "Transparency, Explainability and Human Oversight",
                4,
                (
                    "Learn how organizations can make AI use understandable and keep "
                    "meaningful human control over important decisions."
                ),
                [
                    self.text(
                        "Transparency and Explainability",
                        1,
                        """<h1>Transparency</h1>

<p>Transparency means providing appropriate information about how and why AI is
being used, its purpose, important limitations and relevant responsibilities.</p>

<h2>Explainability</h2>
<p>Explainability concerns the ability to provide meaningful information about how
an AI system arrived at an output or why an output was produced.</p>

<h2>Different Audiences Need Different Information</h2>
<ul>
<li><strong>Users:</strong> What the system does and how to use it safely.</li>
<li><strong>Managers:</strong> Risks, controls and accountability.</li>
<li><strong>Technical teams:</strong> Model, data and performance details.</li>
<li><strong>Affected individuals:</strong> Relevant information about AI-supported decisions and available review mechanisms.</li>
<li><strong>Auditors:</strong> Evidence that controls and governance processes are operating.</li>
</ul>""",
                        35,
                    ),
                    self.text(
                        "Human-in-the-Loop and Human-on-the-Loop",
                        2,
                        """<h1>Human Oversight</h1>

<p>Human oversight should be meaningful rather than merely placing a person
somewhere in a workflow.</p>

<h2>Human-in-the-Loop</h2>
<p>A human reviews or approves an AI output before an important action is taken.</p>

<h2>Human-on-the-Loop</h2>
<p>The system operates with ongoing human monitoring and the ability to intervene
when predefined conditions or concerns arise.</p>

<h2>Good Oversight Requires</h2>
<ul>
<li>Clearly defined authority</li>
<li>Relevant training</li>
<li>Access to sufficient information</li>
<li>Ability to challenge or override outputs</li>
<li>Escalation procedures</li>
<li>Enough time and resources for meaningful review</li>
</ul>

<p>A human reviewer who is unable to understand, challenge or stop a system may
provide only superficial oversight.</p>""",
                        40,
                    ),
                    self.assignment(
                        "Human Oversight Design",
                        3,
                        """Design a human oversight process for an AI system used to
recommend whether a customer should receive an important service.

Your submission should explain:
<ol>
<li>What the AI is allowed to do automatically.</li>
<li>When human review is mandatory.</li>
<li>What information the reviewer receives.</li>
<li>How a reviewer can challenge the AI.</li>
<li>How decisions are documented.</li>
<li>What happens when the AI is unavailable or unreliable.</li>
</ol>""",
                        100,
                        45,
                    ),
                ],
            ),

            self.make_lesson(
                "Privacy, Data Protection and Responsible AI Data Use",
                5,
                (
                    "Understand privacy principles, responsible data handling, data "
                    "minimization and privacy risks in AI systems."
                ),
                [
                    self.text(
                        "Privacy and AI",
                        1,
                        """<h1>Privacy in AI</h1>

<p>AI systems can process large volumes of information, including information
that may identify individuals or reveal sensitive details about them.</p>

<h2>Privacy Questions</h2>
<ul>
<li>What information is being collected?</li>
<li>Why is it needed?</li>
<li>Is the intended use appropriate?</li>
<li>Who can access it?</li>
<li>How long will it be retained?</li>
<li>Could the information be reused for another purpose?</li>
<li>What happens if the data is exposed?</li>
</ul>

<h2>Data Minimization</h2>
<p>Data minimization means avoiding unnecessary collection or use of personal
information for the intended purpose.</p>""",
                        35,
                    ),
                    self.text(
                        "Responsible AI Data Governance",
                        2,
                        """<h1>Data Governance for AI</h1>

<p>AI governance should address data throughout its lifecycle.</p>

<h2>Key Controls</h2>
<ul>
<li>Data classification</li>
<li>Access controls</li>
<li>Purpose limitation</li>
<li>Retention policies</li>
<li>Data quality checks</li>
<li>Documentation of data sources</li>
<li>Secure storage and transmission</li>
<li>Deletion and disposal processes</li>
<li>Privacy impact assessment where appropriate</li>
</ul>

<p>Organizations should also consider whether information supplied to AI tools
could be retained, exposed or reused in ways that are inconsistent with policy
or applicable requirements.</p>

<div style="background:#fee2e2;padding:15px;border-radius:8px;">
<strong>Practical rule:</strong> Do not put confidential or personal information
into an AI service unless its use has been authorized and appropriate safeguards
are in place.
</div>""",
                        40,
                    ),
                    self.assignment(
                        "AI Privacy Review",
                        3,
                        """Review a hypothetical organization that wants employees to
paste customer emails into a public AI chatbot to generate summaries.

Write a privacy and governance assessment covering:
<ol>
<li>Potential privacy risks.</li>
<li>Data classification questions.</li>
<li>Authorization questions.</li>
<li>Minimum safeguards required.</li>
<li>When the practice should be prohibited.</li>
<li>A safer alternative workflow.</li>
</ol>""",
                        100,
                        45,
                    ),
                ],
            ),

            self.make_lesson(
                "Accountability, Governance Roles and AI Policies",
                6,
                (
                    "Learn who should be responsible for AI systems and how policies "
                    "turn responsible AI principles into organizational practice."
                ),
                [
                    self.text(
                        "AI Accountability",
                        1,
                        """<h1>Accountability in AI</h1>

<p><strong>Accountability</strong> means that people and organizations can be held
responsible for decisions, controls, outcomes and actions involving AI.</p>

<h2>Potential Responsibilities</h2>
<ul>
<li>Business owner</li>
<li>AI/model development team</li>
<li>Data owners</li>
<li>Information security</li>
<li>Privacy/legal/compliance</li>
<li>Risk management</li>
<li>Internal audit</li>
<li>Senior management</li>
<li>End users and operators</li>
</ul>

<p>Responsibilities should be assigned clearly rather than assuming that
“the AI” is responsible for its own decisions.</p>""",
                        35,
                    ),
                    self.text(
                        "Building an AI Governance Policy",
                        2,
                        """<h1>AI Governance Policy</h1>

<p>A practical AI policy should establish expectations for the responsible use
of AI throughout an organization's lifecycle.</p>

<h2>Policy Topics</h2>
<ul>
<li>Approved and prohibited AI uses</li>
<li>Roles and responsibilities</li>
<li>Risk assessment requirements</li>
<li>Data protection</li>
<li>Security requirements</li>
<li>Human oversight</li>
<li>Transparency and disclosure</li>
<li>Vendor and third-party requirements</li>
<li>Monitoring and incident reporting</li>
<li>Documentation and recordkeeping</li>
<li>Training and awareness</li>
<li>Review and continuous improvement</li>
</ul>

<p>A policy should be understandable, enforceable and connected to operational
procedures.</p>""",
                        40,
                    ),
                    self.assignment(
                        "Draft a Basic AI Acceptable Use Policy",
                        3,
                        """Create a concise AI Acceptable Use Policy for a medium-sized organization.

Include:
<ol>
<li>Purpose and scope.</li>
<li>Approved AI use.</li>
<li>Prohibited or restricted use.</li>
<li>Confidential and personal data requirements.</li>
<li>Human review requirements.</li>
<li>Accuracy and verification expectations.</li>
<li>Security responsibilities.</li>
<li>Incident reporting.</li>
<li>Employee accountability.</li>
<li>Policy review frequency.</li>
</ol>

<p>Write it in a professional organizational policy style.</p>""",
                        100,
                        60,
                    ),
                ],
            ),

            self.make_lesson(
                "AI Risk Management and Impact Assessment",
                7,
                (
                    "Learn how to identify, assess, prioritize and treat risks associated "
                    "with AI systems."
                ),
                [
                    self.text(
                        "AI Risk Identification",
                        1,
                        """<h1>AI Risk Management</h1>

<p>AI risk management is the structured process of identifying potential harms,
assessing their likelihood and impact, selecting controls and monitoring residual risk.</p>

<h2>Risk Categories</h2>
<ul>
<li>Fairness and discrimination</li>
<li>Privacy</li>
<li>Security</li>
<li>Safety</li>
<li>Reliability and accuracy</li>
<li>Transparency</li>
<li>Accountability</li>
<li>Legal and regulatory compliance</li>
<li>Reputational risk</li>
<li>Operational and financial risk</li>
</ul>

<h2>Basic Risk Statement</h2>
<p>A useful risk statement describes the event, cause, affected asset or people,
potential consequence and existing controls.</p>""",
                        35,
                    ),
                    self.text(
                        "AI Impact Assessment",
                        2,
                        """<h1>AI Impact Assessment</h1>

<p>An AI impact assessment helps an organization understand how a proposed system
may affect people, operations and society before or during deployment.</p>

<h2>Assessment Questions</h2>
<ol>
<li>What is the purpose of the AI system?</li>
<li>Who may be affected?</li>
<li>What data is involved?</li>
<li>What decisions or actions can the system influence?</li>
<li>What could go wrong?</li>
<li>How severe could the consequences be?</li>
<li>What controls reduce the risk?</li>
<li>What evidence shows that the controls work?</li>
<li>Who approves deployment?</li>
<li>How will the system be monitored after deployment?</li>
</ol>""",
                        40,
                    ),
                    self.assignment(
                        "AI Risk Register Exercise",
                        3,
                        """Create a risk register for an AI-powered customer support
assistant.

Include at least 8 risks. For each risk, provide:
<ul>
<li>Risk description</li>
<li>Cause</li>
<li>Affected people/assets</li>
<li>Potential impact</li>
<li>Likelihood: Low/Medium/High</li>
<li>Impact: Low/Medium/High</li>
<li>Overall priority</li>
<li>Existing control</li>
<li>Recommended additional control</li>
<li>Risk owner</li>
</ul>""",
                        100,
                        60,
                    ),
                ],
            ),

            self.make_lesson(
                "AI Safety, Security and Misuse Prevention",
                8,
                (
                    "Understand safety, cybersecurity and misuse risks associated with "
                    "AI systems and practical controls for reducing them."
                ),
                [
                    self.text(
                        "AI Safety",
                        1,
                        """<h1>AI Safety</h1>

<p>AI safety concerns whether a system behaves reliably and whether foreseeable
failures can cause unacceptable harm.</p>

<h2>Safety Questions</h2>
<ul>
<li>What happens when the model is uncertain?</li>
<li>What happens when it receives unusual input?</li>
<li>Can users override unsafe outputs?</li>
<li>Are there safeguards for high-impact actions?</li>
<li>How are failures detected and reported?</li>
<li>Can the system be safely disabled?</li>
</ul>

<p>Safety controls should be proportionate to the potential consequences of failure.</p>""",
                        35,
                    ),
                    self.text(
                        "AI Security and Misuse",
                        2,
                        """<h1>AI Security</h1>

<p>AI systems introduce traditional cybersecurity concerns as well as AI-specific
risks.</p>

<h2>Examples</h2>
<ul>
<li>Unauthorized access</li>
<li>Data leakage</li>
<li>Malicious or manipulated inputs</li>
<li>Prompt injection in applicable systems</li>
<li>Model or application abuse</li>
<li>Supply-chain risks</li>
<li>Insecure integrations</li>
<li>Improper permissions</li>
<li>Abuse of automated capabilities</li>
</ul>

<h2>Basic Controls</h2>
<ul>
<li>Strong authentication and authorization</li>
<li>Least privilege</li>
<li>Input and output validation</li>
<li>Secure development practices</li>
<li>Logging and monitoring</li>
<li>Data protection</li>
<li>Testing and red teaming where appropriate</li>
<li>Incident response procedures</li>
</ul>""",
                        40,
                    ),
                    self.assignment(
                        "AI Security Control Plan",
                        3,
                        """Create a security control plan for an internal generative AI
assistant used by employees.

Cover:
<ol>
<li>Authentication.</li>
<li>Authorization and role separation.</li>
<li>Data protection.</li>
<li>Prompt/input handling.</li>
<li>Output validation.</li>
<li>Logging and monitoring.</li>
<li>Abuse detection.</li>
<li>Incident response.</li>
<li>Vendor/security review.</li>
<li>Periodic security testing.</li>
</ol>""",
                        100,
                        50,
                    ),
                ],
            ),

            self.make_lesson(
                "AI Governance Lifecycle and Third-Party AI",
                9,
                (
                    "Learn how governance applies before procurement, during development, "
                    "deployment and throughout the operational lifecycle."
                ),
                [
                    self.text(
                        "The AI Governance Lifecycle",
                        1,
                        """<h1>AI Governance Lifecycle</h1>

<p>Responsible AI governance should continue throughout the lifecycle rather than
being treated as a one-time approval.</p>

<ol>
<li><strong>Idea:</strong> Define purpose and intended use.</li>
<li><strong>Assessment:</strong> Identify risks and affected stakeholders.</li>
<li><strong>Design:</strong> Establish data, security and oversight requirements.</li>
<li><strong>Development:</strong> Test and document the system.</li>
<li><strong>Approval:</strong> Review evidence and authorize appropriate deployment.</li>
<li><strong>Deployment:</strong> Introduce controls and monitoring.</li>
<li><strong>Operation:</strong> Monitor performance, incidents and changes.</li>
<li><strong>Review:</strong> Reassess risk as circumstances change.</li>
<li><strong>Retirement:</strong> Decommission securely and manage retained data.</li>
</ol>""",
                        40,
                    ),
                    self.text(
                        "Third-Party AI and Vendor Governance",
                        2,
                        """<h1>Third-Party AI</h1>

<p>Organizations often consume AI capabilities from external vendors. This does
not eliminate the organization's responsibility for appropriate governance.</p>

<h2>Vendor Questions</h2>
<ul>
<li>What data does the provider receive?</li>
<li>How is data stored and protected?</li>
<li>Is customer data used for training or other purposes?</li>
<li>Where is information processed?</li>
<li>What security controls are provided?</li>
<li>How are incidents reported?</li>
<li>What happens when the contract ends?</li>
<li>Can the organization audit or obtain relevant evidence?</li>
<li>What service and availability commitments exist?</li>
<li>What subcontractors or third parties are involved?</li>
</ul>""",
                        40,
                    ),
                    self.assignment(
                        "AI Vendor Assessment",
                        3,
                        """Create a vendor assessment checklist for an organization
considering an external generative AI platform.

Organize your checklist into:
<ul>
<li>Privacy</li>
<li>Security</li>
<li>Data usage</li>
<li>Reliability</li>
<li>Transparency</li>
<li>Compliance</li>
<li>Incident response</li>
<li>Contractual controls</li>
<li>Business continuity</li>
<li>Exit/decommissioning</li>
</ul>

<p>Identify at least five questions that should be answered before approval.</p>""",
                        100,
                        50,
                    ),
                ],
            ),

            self.make_lesson(
                "AI Documentation, Monitoring and Audit Readiness",
                10,
                (
                    "Learn what should be documented and monitored to support accountability, "
                    "continuous improvement and audit readiness."
                ),
                [
                    self.text(
                        "AI Documentation",
                        1,
                        """<h1>AI Documentation</h1>

<p>Documentation creates an organizational record of what an AI system is,
why it exists, how it is governed and what risks have been considered.</p>

<h2>Useful Documentation</h2>
<ul>
<li>System purpose and scope</li>
<li>System owner</li>
<li>Data sources and characteristics</li>
<li>Model or system description</li>
<li>Risk assessment</li>
<li>Impact assessment where appropriate</li>
<li>Testing results</li>
<li>Known limitations</li>
<li>Human oversight procedures</li>
<li>Security controls</li>
<li>Monitoring plan</li>
<li>Approval records</li>
<li>Incident and change history</li>
</ul>""",
                        35,
                    ),
                    self.text(
                        "Monitoring and Audit Readiness",
                        2,
                        """<h1>Monitoring AI Systems</h1>

<p>AI systems can change in behavior as data, users, models, integrations or
operating environments change. Monitoring helps identify emerging problems.</p>

<h2>Potential Monitoring Areas</h2>
<ul>
<li>Accuracy and performance</li>
<li>Fairness indicators</li>
<li>Security events</li>
<li>Privacy incidents</li>
<li>User complaints</li>
<li>Unexpected outputs</li>
<li>System availability</li>
<li>Model or configuration changes</li>
<li>Human override frequency</li>
<li>High-risk decisions</li>
</ul>

<h2>Audit Readiness</h2>
<p>An organization should be able to demonstrate not only that it has policies,
but also that controls were implemented, responsibilities assigned, decisions
documented and monitoring performed.</p>""",
                        40,
                    ),
                    self.assignment(
                        "AI Governance Documentation Pack",
                        3,
                        """Prepare a mini documentation pack for a fictional AI
customer service assistant.

Create:
<ol>
<li>System purpose statement.</li>
<li>System owner and responsibilities.</li>
<li>Data inventory.</li>
<li>Risk summary.</li>
<li>Human oversight plan.</li>
<li>Security controls.</li>
<li>Monitoring metrics.</li>
<li>Incident escalation process.</li>
<li>Change management requirements.</li>
<li>Review schedule.</li>
</ol>""",
                        100,
                        60,
                    ),
                ],
            ),

            self.make_lesson(
                "Ethical AI Decision-Making in the Workplace",
                11,
                (
                    "Apply ethical reasoning to common workplace AI decisions and "
                    "learn how to challenge questionable AI use."
                ),
                [
                    self.text(
                        "Ethical Decision-Making Framework",
                        1,
                        """<h1>Making Responsible AI Decisions</h1>

<p>When evaluating an AI use case, combine ethical reasoning with organizational
policy, technical evidence, stakeholder input and applicable requirements.</p>

<h2>A Practical Framework</h2>
<ol>
<li><strong>Purpose:</strong> What problem are we trying to solve?</li>
<li><strong>Necessity:</strong> Is AI actually necessary?</li>
<li><strong>Stakeholders:</strong> Who benefits and who could be harmed?</li>
<li><strong>Risks:</strong> What could go wrong?</li>
<li><strong>Alternatives:</strong> Is there a lower-risk approach?</li>
<li><strong>Controls:</strong> What safeguards are required?</li>
<li><strong>Accountability:</strong> Who owns the decision?</li>
<li><strong>Monitoring:</strong> How will we know whether the system remains appropriate?</li>
</ol>""",
                        35,
                    ),
                    self.text(
                        "Speaking Up About AI Risks",
                        2,
                        """<h1>Responsible Challenge</h1>

<p>Employees should have appropriate channels to raise concerns about AI systems
without being expected to solve every technical or legal issue themselves.</p>

<h2>Raise Concerns When</h2>
<ul>
<li>AI is being used outside its approved purpose.</li>
<li>Personal or confidential data is being handled improperly.</li>
<li>Important decisions are being made without required human oversight.</li>
<li>Testing identifies significant unfairness or safety problems.</li>
<li>AI output is being treated as fact without verification.</li>
<li>Security controls are inadequate.</li>
<li>There is uncertainty about responsibility or approval.</li>
</ul>

<p>A mature governance culture encourages evidence-based questions and constructive
challenge rather than hiding problems.</p>""",
                        35,
                    ),
                    self.assignment(
                        "AI Ethics Decision Memo",
                        3,
                        """<h3>Scenario</h3>
<p>A company wants to use an AI tool to automatically evaluate employee performance
and recommend promotions. Management wants the system to make the process faster.</p>

<p>Write a decision memo addressing:</p>
<ol>
<li>Potential benefits.</li>
<li>Ethical risks.</li>
<li>Fairness concerns.</li>
<li>Privacy concerns.</li>
<li>Transparency requirements.</li>
<li>Human oversight.</li>
<li>Governance approvals.</li>
<li>Recommended safeguards.</li>
<li>Whether you recommend deployment, limited deployment or postponement.</li>
</ol>""",
                        100,
                        55,
                    ),
                ],
            ),

            self.make_lesson(
                "AI Governance Frameworks, Standards and Organizational Controls",
                12,
                (
                    "Become familiar with major AI governance concepts and learn how "
                    "organizations translate principles into practical controls."
                ),
                [
                    self.text(
                        "AI Governance Frameworks",
                        1,
                        """<h1>AI Governance Frameworks</h1>

<p>Organizations can use frameworks and standards to structure responsible AI
programs. Frameworks help establish common language, processes and controls.</p>

<h2>Examples of Framework Themes</h2>
<ul>
<li>Risk identification and management</li>
<li>Governance and accountability</li>
<li>Data management</li>
<li>Transparency and explainability</li>
<li>Fairness</li>
<li>Privacy</li>
<li>Security</li>
<li>Safety and reliability</li>
<li>Monitoring and continuous improvement</li>
</ul>

<p>Examples of widely discussed resources include the <strong>NIST AI Risk Management
Framework</strong>, the <strong>OECD AI Principles</strong>, and the
<strong>ISO/IEC 42001</strong> AI management system standard. Organizations should
select and adapt frameworks according to their context and applicable requirements.</p>""",
                        40,
                    ),
                    self.text(
                        "From Principles to Controls",
                        2,
                        """<h1>Turning Principles into Governance</h1>

<p>A governance program becomes useful when broad principles are converted into
specific responsibilities and measurable controls.</p>

<table style="width:100%;border-collapse:collapse;">
<tr>
<th style="border:1px solid #ccc;padding:8px;">Principle</th>
<th style="border:1px solid #ccc;padding:8px;">Possible Control</th>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:8px;">Fairness</td>
<td style="border:1px solid #ccc;padding:8px;">Pre-deployment and ongoing fairness testing</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:8px;">Privacy</td>
<td style="border:1px solid #ccc;padding:8px;">Data classification, minimization and access controls</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:8px;">Transparency</td>
<td style="border:1px solid #ccc;padding:8px;">AI use notices and system documentation</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:8px;">Accountability</td>
<td style="border:1px solid #ccc;padding:8px;">Named system owner and approval workflow</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:8px;">Safety</td>
<td style="border:1px solid #ccc;padding:8px;">Testing, monitoring and incident response</td>
</tr>
</table>

<p>The objective is not to create paperwork for its own sake. Governance should
help an organization make better decisions and demonstrate responsible practice.</p>""",
                        40,
                    ),
                    self.assignment(
                        "AI Governance Control Matrix",
                        3,
                        """Create a governance control matrix with at least 10 controls.

For every control provide:
<ul>
<li>AI ethics/governance principle</li>
<li>Risk addressed</li>
<li>Control description</li>
<li>Control owner</li>
<li>Evidence produced</li>
<li>Monitoring frequency</li>
<li>What happens if the control fails</li>
</ul>

Use a fictional organization as your example.""",
                        100,
                        60,
                    ),
                ],
            ),

            self.make_lesson(
                "Final Project: Build a Basic AI Governance Program",
                13,
                (
                    "Apply the complete course to design a practical AI governance "
                    "program for an organization."
                ),
                [
                    self.text(
                        "Final Project Scenario",
                        1,
                        """<h1>Final Project: Responsible AI Governance Program</h1>

<p>You have been appointed to help a medium-sized organization establish its
first formal AI governance program.</p>

<h2>Current Situation</h2>
<ul>
<li>Employees use several generative AI tools.</li>
<li>Some teams process customer information with AI services.</li>
<li>Management wants to introduce AI into recruitment.</li>
<li>There is no formal AI policy.</li>
<li>AI vendors are selected by individual departments.</li>
<li>There is no centralized AI inventory.</li>
<li>Employees have received limited responsible AI training.</li>
</ul>

<h2>Your Mission</h2>
<p>Design a practical governance program that reduces risk without unnecessarily
blocking useful innovation.</p>""",
                        40,
                    ),
                    self.assignment(
                        "Final AI Ethics & Governance Project",
                        2,
                        """<h1>Final Project Requirements</h1>

<p>Submit a professional AI Ethics & Governance Program for the organization
described in the previous lesson.</p>

<h2>Your submission must contain</h2>

<ol>
<li><strong>Executive Summary</strong></li>
<li><strong>AI Governance Policy</strong></li>
<li><strong>AI Inventory Process</strong></li>
<li><strong>AI Risk Classification</strong></li>
<li><strong>AI Impact Assessment Process</strong></li>
<li><strong>Data Privacy and Protection Controls</strong></li>
<li><strong>Fairness and Bias Management</strong></li>
<li><strong>Transparency and Explainability Requirements</strong></li>
<li><strong>Human Oversight Requirements</strong></li>
<li><strong>Security Controls</strong></li>
<li><strong>Third-Party AI Vendor Assessment</strong></li>
<li><strong>Monitoring and Audit Plan</strong></li>
<li><strong>Incident Reporting and Escalation</strong></li>
<li><strong>Employee Training Plan</strong></li>
<li><strong>Roles and Responsibilities</strong></li>
<li><strong>Implementation Roadmap</strong></li>
</ol>

<h2>Suggested Risk Categories</h2>
<ul>
<li>Privacy</li>
<li>Security</li>
<li>Fairness</li>
<li>Safety</li>
<li>Accuracy</li>
<li>Transparency</li>
<li>Accountability</li>
<li>Legal/compliance</li>
<li>Third-party/vendor</li>
<li>Operational risk</li>
</ul>

<h2>Recommended Project Structure</h2>
<p>Use tables, headings, risk registers and control matrices where appropriate.
Your final document should be suitable for presentation to senior management.</p>

<h2>Assessment Rubric - 100 Points</h2>
<ul>
<li>AI ethics understanding: 15 points</li>
<li>Risk identification: 15 points</li>
<li>Governance structure: 15 points</li>
<li>Privacy and data governance: 10 points</li>
<li>Fairness and transparency: 10 points</li>
<li>Security and safety: 10 points</li>
<li>Accountability and oversight: 10 points</li>
<li>Monitoring and auditability: 5 points</li>
<li>Implementation roadmap: 5 points</li>
<li>Professional presentation: 5 points</li>
</ul>""",
                        100,
                        120,
                    ),
                    self.text(
                        "Course Completion and Professional Takeaways",
                        3,
                        """<h1>Congratulations</h1>

<p>You have completed the <strong>Basic AI Ethics & Governance</strong> learning
program.</p>

<h2>Key Takeaways</h2>
<ul>
<li>Responsible AI requires more than technical performance.</li>
<li>AI systems should have clear purposes and accountable owners.</li>
<li>Fairness and bias should be assessed using evidence and context.</li>
<li>Privacy should be considered throughout the AI lifecycle.</li>
<li>Transparency should be appropriate to the audience and risk.</li>
<li>Human oversight must be meaningful.</li>
<li>AI security and safety require continuous attention.</li>
<li>Risk assessments should lead to practical controls.</li>
<li>Third-party AI still requires organizational governance.</li>
<li>Monitoring, documentation and continuous improvement are essential.</li>
</ul>

<div style="background:#dcfce7;padding:18px;border-radius:8px;">
<strong>Professional principle:</strong> Responsible AI is a continuous organizational
practice. Good governance helps people use AI confidently while understanding,
managing and taking responsibility for its risks.
</div>""",
                        30,
                    ),
                ],
            ),
        ]

        for lesson_data in lessons:
            contents = lesson_data.pop("contents")

            lesson, created = Lesson.objects.update_or_create(
                course=course,
                title=lesson_data["title"],
                defaults={
                    "order": lesson_data["order"],
                    "is_free_preview": lesson_data.get("is_free_preview", False),
                    "description": lesson_data.get("description", ""),
                    "is_published": True,
                },
            )

            # Make the command repeatable without duplicating lesson content.
            if not created:
                LessonContent.objects.filter(lesson=lesson).delete()

            for content in contents:
                LessonContent.objects.create(
                    lesson=lesson,
                    **content,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Lesson {lesson.order}: {lesson.title}"
                )
            )
