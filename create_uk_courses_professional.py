"""
Professional UK AI Governance / Compliance / Responsible AI course builder.

Run:
    python manage.py shell < create_uk_courses_professional.py

WARNING: This script deletes and recreates the three courses identified
by slug. Back up existing course data before running in production.

Educational note:
This content is written as professional training material. It is not legal
advice. Regulatory/legal statements should be reviewed against current UK
primary sources before publication as regulated/certification material.
"""

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.courses.models import Course, CourseCategory, Lesson, LessonContent, Quiz, QuizQuestion, QuizAnswer

User = get_user_model()


def instructor():
    user = User.objects.filter(user_type='INSTRUCTOR', is_active=True).first()
    if not user:
        user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter(is_active=True).first()
    if not user:
        raise RuntimeError('No active instructor, superuser or active user exists.')
    return user


def category(slug, name, description):
    obj, _ = CourseCategory.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'description': description, 'is_active': True},
    )
    return obj


def course(**kwargs):
    Course.objects.filter(slug=kwargs['slug']).delete()
    return Course.objects.create(**kwargs)


def lesson(course_obj, title, description, html, order, preview=False):
    obj = Lesson.objects.create(
        course=course_obj,
        title=title,
        description=description,
        order=order,
        is_published=True,
    )
    LessonContent.objects.create(
        lesson=obj,
        content_type='text',
        title=title,
        order=1,
        text_content=html,
        is_preview=preview,
    )
    return obj


def quiz(lesson_obj, title, description, questions, passing=70):
    qz = Quiz.objects.create(
        lesson=lesson_obj,
        title=title,
        description=description,
        passing_score=passing,
        allow_retake=True,
        randomize_questions=False,
        randomize_answers=False,
        show_correct_answers=True,
        is_active=True,
    )
    for i, item in enumerate(questions, 1):
        q = QuizQuestion.objects.create(
            quiz=qz,
            question_text=item['question'],
            question_type='multiple_choice',
            points=item.get('points', 1),
            order=i,
            explanation=item.get('explanation', ''),
            is_active=True,
        )
        for j, option in enumerate(item['options'], 1):
            QuizAnswer.objects.create(
                question=q,
                answer_text=option,
                is_correct=(j - 1 == item['correct_answer']),
                order=j,
            )
    return qz


def content(title, objectives, sections, case, activity, takeaways, references=None):
    """Build a rich, mobile-friendly lesson body as HTML."""
    html = [f'<article class="ai-course-lesson"><h2>{title}</h2>']
    html.append('<h3>Learning objectives</h3><ul>')
    for x in objectives:
        html.append(f'<li>{x}</li>')
    html.append('</ul>')
    for heading, body in sections:
        html.append(f'<h3>{heading}</h3>{body}')
    html.append('<h3>Professional case study</h3>')
    html.append(case)
    html.append('<h3>Practical activity</h3>')
    html.append(activity)
    html.append('<h3>Key takeaways</h3><ul>')
    for x in takeaways:
        html.append(f'<li>{x}</li>')
    html.append('</ul>')
    if references:
        html.append('<h3>Further reading / source-check points</h3><ul>')
        for x in references:
            html.append(f'<li>{x}</li>')
        html.append('</ul>')
    html.append('</article>')
    return ''.join(html)


# ---------------------------------------------------------------------------
# COURSE 1: AI GOVERNANCE
# ---------------------------------------------------------------------------

def build_governance(user, cat):
    c = course(
        title='AI Governance for UK Organisations',
        slug='ai-governance-uk-organisations',
        instructor=user, category=cat,
        short_description='A practical professional programme for designing, implementing and assuring AI governance in UK organisations.',
        description='''<h2>Professional AI Governance Programme</h2><p>This course teaches learners how to govern AI as an organisational capability rather than treating it as a purely technical project. It combines governance theory with practical risk assessment, accountability, procurement, privacy, fairness, transparency, human oversight, incident management and assurance.</p><p>Learners work through realistic organisational scenarios and finish with a practical governance implementation exercise.</p>''',
        level='intermediate', duration='10 Weeks', price=399.00, is_free=False,
        has_certificate=True, status='published', language='English', badge='bestseller',
        badge_updated_at=timezone.now(),
    )

    L = []
    L.append(('01 - Foundations of AI Governance','Understand governance as an organisational control system.',content(
        'Foundations of AI Governance',
        ['Define AI governance in operational terms.','Distinguish governance, ethics, compliance and risk management.','Explain why governance must cover the full AI lifecycle.','Identify decisions that require accountable human ownership.'],
        [
            ('What governance actually does', '''<p>AI governance is the system through which an organisation decides <strong>which AI uses are acceptable, who may approve them, what evidence is required, how risks are controlled, and how performance is monitored over time</strong>. It is not simply a policy document. A policy can state that employees must not put confidential information into an unapproved generative AI service; governance creates the ownership, approval route, technical controls, training, monitoring and escalation process that makes the policy meaningful.</p><p>A mature governance model begins before procurement or development. It asks whether AI is appropriate for the business problem at all. It then follows the system through design, testing, deployment, operation, change and retirement.</p>'''),
            ('Four related disciplines', '''<p><strong>Ethics</strong> considers whether a proposed use is responsible and acceptable. <strong>Compliance</strong> considers applicable legal and regulatory duties. <strong>Risk management</strong> asks what could go wrong, how severe the consequences could be and which controls reduce exposure. <strong>Governance</strong> brings these questions into an accountable decision structure.</p><p>These disciplines overlap but should not be collapsed into one. A system may be technically compliant yet poorly governed if nobody owns it, its supplier changes the model without review, or there is no mechanism to suspend it.</p>'''),
            ('The AI lifecycle', '''<ol><li>Identify a business need.</li><li>Determine whether AI is appropriate.</li><li>Define purpose, users and affected people.</li><li>Assess data and risks.</li><li>Design controls.</li><li>Develop or procure.</li><li>Validate and approve.</li><li>Deploy with monitoring.</li><li>Review changes and incidents.</li><li>Retire when the system is no longer appropriate.</li></ol><p>The governance requirement changes at each stage. Early decisions are about purpose and proportionality; later decisions focus on testing, monitoring and operational control.</p>'''),
        ],
        '<p>A UK retailer proposes an AI recruitment ranking tool. The supplier demonstrates high overall accuracy and asks the retailer to sign off immediately. A governance professional should resist the idea that supplier accuracy equals organisational acceptability. The retailer must examine purpose, data provenance, fairness, privacy, transparency, human review, supplier obligations, monitoring and the authority to stop the system.</p>',
        '<p>Create a one-page governance map for an AI recruitment system. Identify the executive sponsor, system owner, HR owner, privacy lead, security lead, procurement owner and escalation authority. For each, state one decision they own.</p>',
        ['AI governance is an accountability system, not just an AI policy.','Governance starts before deployment and continues through retirement.','A technically successful model can still create unacceptable organisational risk.','Every material AI use should have an identifiable owner.'],
        ['Review current UK regulator guidance and organisational AI governance expectations before final certification publication.'])) )

    L.append(('02 - Governance Roles, Committees and Accountability','Design clear ownership for AI decisions.',content(
        'Governance Roles, Committees and Accountability',
        ['Identify the minimum ownership roles for an AI use case.','Design escalation and approval routes.','Avoid responsibility gaps between business and technical teams.'],
        [
            ('Ownership versus accountability', '''<p>The <strong>system owner</strong> is normally responsible for ensuring that a particular AI application is operated as intended. The <strong>business owner</strong> owns the business process. Technical teams may own implementation and operational performance. Privacy, legal, security and compliance teams provide specialist challenge. Executive leadership provides strategic direction and accepts material organisational risk.</p><p>These roles should be documented. Saying that "everyone is responsible" often means nobody has clear authority to act when a problem occurs.</p>'''),
            ('The governance committee', '''<p>A proportionate AI governance committee can review higher-risk use cases, exceptions, incidents and material changes. It should have enough independence to challenge project sponsors. A committee should not become a bottleneck for every low-risk tool; risk-tiered governance is more practical.</p><p>Typical evidence presented to a committee includes the use-case statement, risk assessment, data assessment, testing results, proposed controls, human oversight plan and monitoring plan.</p>'''),
            ('RACI thinking', '''<p>Use a RACI-style model to distinguish who is <strong>Responsible</strong>, <strong>Accountable</strong>, <strong>Consulted</strong> and <strong>Informed</strong>. For example, a data science team may be responsible for model validation, while the business owner remains accountable for the business use. A privacy specialist may be consulted, while the final deployment authority sits with a designated governance role.</p>'''),
        ],
        '<p>An organisation discovers that an employee deployed an AI customer-service tool without formal approval. IT says the business team owns it; the business team says IT supplied the account; procurement has no record of the supplier. This is a governance failure before it is a technology failure. The corrective action should include ownership, inventory, approval criteria, procurement controls and a route for employees to disclose existing AI use.</p>',
        '<p>Draft a RACI matrix for procurement, approval, deployment, monitoring, incident response and retirement of one AI system.</p>',
        ['Accountability must be explicit.','Governance committees should be proportionate to risk.','Shadow AI is a visibility and governance problem, not merely an employee behaviour problem.'],
    )))

    L.append(('03 - UK AI Regulatory and Legal Landscape','Understand how existing UK legal and regulatory regimes can apply to AI.',content(
        'UK AI Regulatory and Legal Landscape',
        ['Explain the UK context without treating AI regulation as one single statute.','Identify common legal and regulatory domains relevant to AI.','Map a use case to relevant internal specialists and regulators.'],
        [
            ('A use-case approach', '''<p>Organisations should not begin with the question, "What is the UK AI law?" They should begin with, "What does this AI system do, who is affected, what data is processed, and which legal or regulatory domains are engaged?" The answer can involve data protection, equality, consumer protection, employment, financial services, product safety, intellectual property, cyber security or sector-specific rules.</p>'''),
            ('Regulatory ecosystem', '''<p>Different UK regulators have different remits. The Information Commissioner's Office is particularly important where personal data and privacy are involved. Other regulators may be relevant depending on the sector and use case. A governance professional therefore needs a method for identifying the appropriate regulatory stakeholders rather than assuming that one regulator covers every AI risk.</p>'''),
            ('Evidence and defensibility', '''<p>Good compliance practice requires evidence. An organisation should be able to show what it knew, what assessment it performed, what controls it selected, who approved the decision and how it monitors the system. This is why governance records are valuable even where no incident occurs.</p>'''),
        ],
        '<p>A financial-services firm wants to use generative AI to draft customer communications. The project team asks the AI governance lead for a single "AI compliance approval". The professional response is to map the use case across data protection, financial-services conduct requirements, information security, customer communications, intellectual property and supplier risk, then identify the relevant control owners.</p>',
        '<p>Create a regulatory mapping table with columns for AI use case, affected people, data, legal/regulatory domain, internal owner, evidence required and review date.</p>',
        ['UK AI compliance is use-case and sector dependent.','Existing legal and regulatory duties can apply to AI.','Governance records create evidence of responsible decision-making.'],
        ['Before publishing, verify current primary UK legislation, regulator guidance and sector-specific requirements relevant to the course audience.'])) )

    L.append(('04 - AI Risk Assessment and Impact Management','Perform a structured AI risk assessment.',content(
        'AI Risk Assessment and Impact Management',
        ['Separate inherent risk from residual risk.','Identify affected stakeholders and potential harms.','Select controls that address specific risks.','Document risk acceptance and review triggers.'],
        [
            ('Start with the use case', '''<p>Risk assessment should describe the actual decision or task, not merely the model. "We use a large language model" is too vague. A useful statement might be: "The customer-service team uses an external generative AI service to draft responses to complaints; a human agent reviews the draft before sending." The latter allows the assessor to examine data, decision impact and human control.</p>'''),
            ('Risk categories', '''<ul><li>Privacy and data protection</li><li>Fairness and discrimination</li><li>Safety and reliability</li><li>Cybersecurity and misuse</li><li>Transparency and contestability</li><li>Operational resilience</li><li>Third-party and concentration risk</li><li>Reputational and financial harm</li></ul>'''),
            ('Controls and residual risk', '''<p>Controls should directly address identified risks. If the risk is confidential data entering a public AI service, a generic "AI policy" may be insufficient; technical restrictions, approved tools, data-loss prevention, training and monitoring may be needed. After controls are selected, the remaining exposure is residual risk. Someone with appropriate authority must decide whether that residual risk is acceptable.</p>'''),
        ],
        '<p>A retailer wants an AI model to predict which customers are likely to stop buying. The system uses purchase history and behavioural data. The risk assessment identifies privacy, accuracy, profiling, fairness and customer-experience risks. The governance team recommends data minimisation, documented purpose, validation, monitoring, access controls and a defined review process before deployment.</p>',
        '<p>Complete a 5x5 likelihood/impact assessment for the retailer scenario. For each high-risk item, propose one preventive control and one detective control.</p>',
        ['Risk assessment must be tied to the actual use case.','Controls should be specific to the risk they mitigate.','Residual risk requires an accountable decision.'],
    )))

    L.append(('05 - AI Inventories, Classification and Approval Gates','Build visibility and proportionate governance.',content(
        'AI Inventories, Classification and Approval Gates',
        ['Build an AI inventory.','Define useful classification fields.','Create risk-based approval gates.'],
        [
            ('The AI inventory', '''<p>An AI register should provide management with visibility of systems in development, procurement and production. Useful fields include system name, purpose, owner, supplier, data categories, affected people, decision role, risk rating, approval status, monitoring requirements and next review date.</p>'''),
            ('Classification', '''<p>Classification should be based on impact, not on whether a vendor labels a product "AI". A simple internal model can distinguish low-impact productivity assistance from systems that influence employment, access to essential services, financial decisions, safety or other consequential outcomes.</p>'''),
            ('Approval gates', '''<ol><li>Business justification.</li><li>Initial risk screen.</li><li>Privacy/security/legal review where triggered.</li><li>Testing evidence.</li><li>Human oversight design.</li><li>Formal approval.</li><li>Post-deployment monitoring.</li></ol>'''),
        ],
        '<p>An organisation has 47 AI-enabled tools but only 12 appear in its official register. A discovery exercise reveals staff are using consumer generative AI, AI meeting tools and automated transcription services. The governance team introduces an AI disclosure channel, approved-tool catalogue, procurement questionnaire and risk-based inventory process.</p>',
        '<p>Design an AI register with at least 15 fields. Mark which fields should be mandatory before production approval.</p>',
        ['You cannot govern what you cannot see.','Classification should reflect potential impact.','Approval gates should be proportionate and evidence-based.'],
    )))

    L.append(('06 - Data Governance, UK GDPR and AI','Apply privacy and data governance principles to AI.',content(
        'Data Governance, UK GDPR and AI',
        ['Identify personal-data questions in AI projects.','Apply data-governance thinking before deployment.','Recognise when privacy specialists should be involved.'],
        [
            ('Data is part of the system', '''<p>AI governance must consider input data, training or reference data, prompts, logs, outputs and downstream use. Personal data can appear in any of these locations. Governance therefore requires a data-flow view rather than focusing only on the model.</p>'''),
            ('Core privacy questions', '''<p>Consider purpose, lawful basis, transparency, minimisation, accuracy, retention, security and individual rights. The organisation should also understand where data is sent, who can access it and whether a supplier uses it for its own purposes.</p>'''),
            ('DPIA thinking', '''<p>Where processing is likely to result in high risk to individuals, a Data Protection Impact Assessment may be required. A DPIA is not merely a form; it is a structured analysis of processing, necessity, proportionality, risks and mitigation. AI projects should bring privacy assessment early enough to influence design.</p>'''),
        ],
        '<p>A company wants to paste customer complaint emails into an external generative AI tool to produce summaries. The team initially believes the task is low risk because the AI is only summarising. A governance review identifies personal data, supplier processing, retention, access, confidentiality and transparency questions. The project is redesigned to use an approved environment with appropriate controls.</p>',
        '<p>Draw the data flow from customer input to AI service to output to business record. Identify every point where personal or confidential information could be exposed.</p>',
        ['AI governance must follow the data, not just the model.','Privacy should influence architecture and process design early.','A DPIA is a risk-management process, not paperwork for its own sake.'],
    )))

    L.append(('07 - Fairness, Bias and Equality Risk','Identify and manage discriminatory or unfair AI outcomes.',content(
        'Fairness, Bias and Equality Risk',
        ['Identify common sources of AI bias.','Distinguish measurement from interpretation.','Design a practical fairness testing process.'],
        [
            ('How bias enters', '''<p>Bias can enter through historical decisions, sampling, labels, missing data, measurement choices, feature selection, model optimisation and deployment context. Removing a protected attribute does not automatically remove all fairness risk because other variables can correlate with protected characteristics or encode historical inequality.</p>'''),
            ('Testing', '''<p>Testing should be designed around the actual decision and affected population. Teams may compare error rates, selection rates or other relevant measures across groups, but no single metric determines fairness in every context. Results require domain, legal and ethical interpretation.</p>'''),
            ('Mitigation', '''<p>Possible interventions include improving data, changing features, rebalancing training sets, modifying thresholds, adding human review, narrowing the use case or deciding not to deploy. Mitigation should be tested for unintended side effects.</p>'''),
        ],
        '<p>An AI recruitment tool selects candidates for interview. The overall model accuracy is strong, but one demographic group has a substantially lower selection rate. The vendor says the model is "statistically accurate". The organisation pauses deployment, investigates the disparity, reviews historical data and tests mitigation options. It documents the decision and creates ongoing fairness monitoring.</p>',
        '<p>Write a fairness test plan for a recruitment model. Include population, outcomes, comparison groups, test frequency, escalation thresholds and evidence to retain.</p>',
        ['Accuracy and fairness are different dimensions.','Fairness testing must be contextual.','A material disparity should trigger investigation rather than automatic acceptance or rejection.'],
    )))

    L.append(('08 - Transparency, Explainability and Human Oversight','Design understandable and challengeable AI processes.',content(
        'Transparency, Explainability and Human Oversight',
        ['Explain transparency and explainability in practical terms.','Design meaningful human review.','Reduce automation bias.'],
        [
            ('Transparency', '''<p>Transparency means communicating relevant information about AI use, purpose, role and limitations. The appropriate level depends on the audience: board members need governance evidence; operators need system limitations and escalation instructions; affected individuals may need understandable information about the use of AI and relevant rights or challenge routes.</p>'''),
            ('Explainability', '''<p>Explainability is context-dependent. A technical explanation of model architecture may be useless to a customer. A useful explanation should help the relevant person understand the factors or process sufficiently to review, challenge or respond to an outcome.</p>'''),
            ('Human oversight', '''<p>Meaningful human oversight requires authority, competence, information and time. A reviewer who is measured on speed and sees only the model\'s recommendation may simply rubber-stamp it. Governance should monitor override rates, reviewer training and escalation behaviour.</p>'''),
        ],
        '<p>An insurer introduces an AI claims-triage tool. Staff receive a probability score but no explanation of the factors behind it. Complaints increase because agents cannot explain why certain cases are prioritised. The organisation redesigns the workflow to provide decision-support information, clearer limitations, review criteria and an escalation route.</p>',
        '<p>Design a human-review checklist containing five questions an employee must answer before accepting a high-impact AI recommendation.</p>',
        ['Transparency is audience-specific.','Explainability should support meaningful understanding, not merely technical disclosure.','Human oversight is ineffective if reviewers lack authority or competence.'],
    )))

    L.append(('09 - AI Procurement, Third-Party Risk and Generative AI','Govern external AI suppliers and employee use.',content(
        'AI Procurement, Third-Party Risk and Generative AI',
        ['Conduct AI-specific supplier due diligence.','Identify contractual and operational controls.','Govern generative AI use without blocking useful innovation.'],
        [
            ('Supplier due diligence', '''<p>Ask suppliers what the system does, what data it processes, where data is handled, how models are tested, how updates are controlled, what assurance evidence exists and how incidents are reported. Procurement should involve privacy, security and legal specialists where the use case warrants it.</p>'''),
            ('Contractual controls', '''<p>Depending on the service, contracts may need provisions covering data use, confidentiality, security, incident notification, subprocessors, audit or assurance information, service continuity, change management and exit. The exact requirements depend on the risk and relationship.</p>'''),
            ('Generative AI', '''<p>Generative AI introduces additional risks including hallucinated content, confidential-data leakage, prompt injection, intellectual-property questions, uncontrolled employee use and over-reliance. Governance should provide approved tools, prohibited uses, training, data-handling rules and a reporting mechanism.</p>'''),
        ],
        '<p>An employee uploads a confidential client document into an unapproved AI assistant to create a summary. The employee intended to save time, but the organisation has no assurance about the service\'s data handling. A mature programme responds through both incident assessment and prevention: approved tools, clear rules, technical controls, training and a safe way for employees to disclose experimentation.</p>',
        '<p>Create a 12-question AI supplier due-diligence questionnaire covering privacy, security, model changes, data use, assurance, incidents and exit.</p>',
        ['Vendor risk remains organisational risk.','Contracts and technical controls should reinforce governance.','Generative AI needs usable controls rather than vague prohibition alone.'],
    )))

    L.append(('10 - AI Monitoring, Incidents, Audit and Continuous Improvement','Operate governance after deployment.',content(
        'AI Monitoring, Incidents, Audit and Continuous Improvement',
        ['Define meaningful post-deployment monitoring.','Build an AI incident response process.','Use audit evidence to improve governance.'],
        [
            ('Monitoring', '''<p>Monitor the dimensions that matter for the use case: performance, accuracy, fairness indicators, data quality, security events, complaints, human overrides, model changes and unexpected behaviour. Monitoring thresholds should trigger defined actions rather than merely producing dashboards.</p>'''),
            ('Incident management', '''<p>An AI incident can involve privacy exposure, harmful output, material bias, unsafe behaviour, security compromise or an incorrect consequential decision. A response process should identify, contain, assess, escalate, investigate, remediate and learn. Relevant legal or regulatory notification duties must be considered by the appropriate specialists.</p>'''),
            ('Assurance and audit', '''<p>Internal audit or independent assurance can test whether governance controls actually operate. Evidence can include approval records, risk assessments, testing results, monitoring reports, incidents, training completion and change approvals. A mature programme uses findings to improve policies and controls.</p>'''),
        ],
        '<p>A customer-facing AI assistant begins generating inaccurate policy information after a supplier model update. No one changed the organisation\'s configuration, so the business initially assumes there is no governance issue. A mature control environment treats the supplier update as a change event, investigates the impact, limits the affected function, informs stakeholders as appropriate and updates change-management requirements.</p>',
        '<p>Build a monthly AI assurance dashboard with 10 indicators. Include at least one indicator for fairness, privacy, security, performance, incidents, human oversight and supplier changes.</p>',
        ['Deployment is the beginning of operational governance, not the end.','Monitoring should have thresholds and actions.','Incidents should produce governance learning as well as technical remediation.'],
    )))

    for i, (t,d,h) in enumerate(L,1): lesson(c,t,d,h,i,preview=i<=2)
    assessment = lesson(c,'Final Professional Governance Assessment','Apply governance principles to realistic organisational scenarios.',content(
        'Final Professional Governance Assessment',
        ['Apply governance principles to a complete AI use case.','Identify risks and controls.','Make defensible approval and escalation recommendations.'],
        [('Assessment approach','''<p>This assessment is designed to test judgement rather than memorisation. Read the scenario, identify what matters, determine what evidence is missing and choose the most defensible governance response.</p>''')],
        '<p>A UK retailer is considering an AI system for recruitment, customer segmentation and employee analytics. The supplier hosts the service externally and updates the model regularly. Prepare a governance recommendation addressing purpose, risk, data, fairness, transparency, oversight, procurement, monitoring and incident response.</p>',
        '<p>Produce a two-page governance decision paper with: recommendation, key risks, required controls, evidence required before approval, accountable owner and review triggers.</p>',
        ['Good governance is proportionate, evidence-based and accountable.','The correct response is often to pause, investigate or redesign rather than simply approve or reject.'],
    ),len(L)+1,False)
    quiz(assessment,'AI Governance Professional Final Assessment','Scenario-based final assessment.',[
        {'question':'A vendor says its AI recruitment model is compliant. What is the strongest governance response?','options':['Accept the claim as sufficient','Perform proportionate organisational assessment and retain evidence','Deploy first and assess later','Ask marketing to approve it'],'correct_answer':1,'explanation':'Vendor claims do not replace the deploying organisation’s own risk, privacy, fairness and governance assessment.'},
        {'question':'Which item most directly establishes accountability?','options':['A generic AI brochure','A named owner with decision authority and documented responsibilities','A model accuracy score','A supplier logo'],'correct_answer':1,'explanation':'Accountability requires identifiable ownership and authority.'},
        {'question':'Why maintain an AI register?','options':['To make every AI system high risk','To maintain organisational visibility and support proportionate governance','To replace testing','To prevent all AI use'],'correct_answer':1,'explanation':'Visibility is a prerequisite for governance.'},
        {'question':'A fairness test shows a substantial disparity. What is the best immediate governance action?','options':['Ignore it','Investigate cause, impact and mitigation before proceeding','Delete the metric','Publish the model immediately'],'correct_answer':1,'explanation':'A material disparity warrants investigation and risk-based action.'},
        {'question':'What makes human oversight meaningful?','options':['The person is named on the policy','The reviewer has competence, information, authority and time to challenge outputs','The reviewer never disagrees','The system cannot be overridden'],'correct_answer':1,'explanation':'Oversight requires real capability and authority.'},
        {'question':'What is residual risk?','options':['Risk before controls','Risk remaining after controls','A supplier invoice','A model score'],'correct_answer':1,'explanation':'Residual risk is the exposure remaining after mitigation.'},
        {'question':'What should happen after a material AI incident?','options':['Delete all records','Remediate and examine why controls failed or were insufficient','Blame the model','Continue without review'],'correct_answer':1,'explanation':'Incident management should include corrective action and governance learning.'},
        {'question':'Which is a sensible generative-AI control?','options':['No rules at all','Approved tools, data-handling rules, training and reporting routes','Allow confidential uploads','Assume outputs are always correct'],'correct_answer':1,'explanation':'Effective governance combines policy, approved technology, training and monitoring.'},
        {'question':'Why should AI governance cover supplier changes?','options':['Model behaviour can change when suppliers update systems','Supplier changes never matter','Only finance cares','It is purely a marketing issue'],'correct_answer':0,'explanation':'Changes can alter performance, risk and data handling.'},
        {'question':'What is the best description of governance evidence?','options':['Only the final policy','Records showing decisions, assessments, controls, approvals and monitoring','Marketing screenshots','A vendor slogan'],'correct_answer':1,'explanation':'Evidence demonstrates how governance decisions were made and operated.'},
    ],70)
    return c


# ---------------------------------------------------------------------------
# COURSE 2: COMPLIANCE
# ---------------------------------------------------------------------------

def build_compliance(user, cat):
    c = course(
        title='UK AI Compliance Masterclass', slug='uk-ai-compliance-masterclass', instructor=user, category=cat,
        short_description='A practical masterclass in AI compliance, data protection, impact assessment, auditing, fairness, supplier controls and continuous assurance.',
        description='''<h2>UK AI Compliance Masterclass</h2><p>This programme teaches learners to translate AI compliance requirements into operational controls and evidence. It is designed for compliance, privacy, risk, governance, legal, audit and technology professionals.</p><p>The course uses practical scenarios rather than relying on definitions alone.</p>''',
        level='intermediate', duration='8 Weeks', price=449.00, is_free=False, has_certificate=True,
        status='published', language='English', badge='trending', badge_updated_at=timezone.now(),
    )
    data = [
        ('01 - Compliance Scoping for AI','Determine which compliance domains apply.',content('Compliance Scoping for AI',['Map an AI use case before choosing controls.','Identify relevant legal, regulatory and internal requirements.','Define evidence and accountable owners.'],[
            ('Start with the process','''<p>Compliance analysis should begin with the business activity, not the marketing label attached to the technology. Identify what the system does, whose information it uses, whose interests are affected and whether it makes, recommends or supports decisions.</p>'''),
            ('Build a compliance map','''<p>Map the use case to data protection, equality, consumer, employment, financial, security, intellectual property and sector-specific considerations as appropriate. Then identify the internal owner and specialist function responsible for each domain.</p>'''),
            ('Evidence','''<p>A compliance conclusion should be supported by evidence: system description, data flow, assessment, controls, testing, approvals and monitoring. "The vendor said it is compliant" is not a complete evidence trail.</p>''')],
            '<p>A business team wants to deploy an AI chatbot for customers. The first draft of the project plan contains only software requirements. The compliance lead adds a use-case statement, data map, customer transparency assessment, security review, supplier due diligence, incident route and monitoring plan.</p>',
            '<p>Create a compliance scoping worksheet for the chatbot. Mark each domain as applicable, potentially applicable or not currently applicable, with a reason.</p>',
            ['Compliance is contextual.','Evidence and ownership matter as much as policy language.'],
        )),
        ('02 - UK GDPR, Personal Data and AI','Apply data protection principles to AI processing.',content('UK GDPR, Personal Data and AI',['Identify personal data in AI workflows.','Apply core data protection principles.','Know when specialist privacy assessment is needed.'],[
            ('Follow the data flow','''<p>Map prompts, training/reference datasets, logs, outputs, analytics and downstream records. Personal data may appear unexpectedly in free-text fields and generated outputs.</p>'''),
            ('Principles in practice','''<p>Purpose limitation asks why data is being used. Minimisation asks whether all information is necessary. Accuracy asks whether information and outputs are reliable for the purpose. Security asks whether access, transmission and storage are appropriately protected. Accountability requires evidence that these decisions were considered.</p>'''),
            ('Transparency and rights','''<p>AI does not remove applicable transparency and individual-rights responsibilities. Organisations should understand the role of automated processing and design processes that allow relevant rights and complaints to be handled appropriately.</p>''')],
            '<p>An HR team wants to use historical employee data to build a prediction model. The project is initially described as "internal analytics". A privacy review asks whether the new purpose is compatible, whether the data is necessary, what lawful basis applies, how long information will be retained and what information employees should receive.</p>',
            '<p>Produce a data-flow diagram and list five privacy questions that must be answered before development starts.</p>',
            ['AI systems inherit the data-protection responsibilities associated with their processing.','Data flows are often more informative than product descriptions.'],
        )),
        ('03 - DPIAs and AI Impact Assessments','Conduct structured impact assessment.',content('DPIAs and AI Impact Assessments',['Explain the purpose of a DPIA.','Separate privacy impact from wider AI impact.','Create actionable mitigation measures.'],[
            ('DPIA structure','''<ol><li>Describe processing.</li><li>Explain purpose and necessity.</li><li>Assess proportionality.</li><li>Identify risks to individuals.</li><li>Identify controls.</li><li>Record residual risk and consultation.</li></ol>'''),
            ('Broader AI impact','''<p>Some organisations use broader AI impact assessments to consider fairness, safety, human rights, accessibility, security and social impacts in addition to privacy. The assessment should be integrated with governance rather than creating disconnected paperwork.</p>'''),
            ('When assessment changes the design','''<p>A good assessment is allowed to change the project. It may lead to data minimisation, additional human review, a narrower purpose, different supplier, technical controls or a decision not to deploy.</p>''')],
            '<p>A public-facing service plans to use AI to prioritise applications. An impact assessment identifies that errors could affect vulnerable people. The team changes the workflow so AI provides triage support rather than making final decisions, adds human review and introduces monitoring for disparate outcomes.</p>',
            '<p>Write the "necessity and proportionality" section for that use case and identify three design changes resulting from the assessment.</p>',
            ['An assessment is valuable when it changes decisions.','Impact assessment should be connected to governance approval.'],
        )),
        ('04 - Automated Decisions and Individual Rights','Understand high-impact automated decision workflows.',content('Automated Decisions and Individual Rights',['Identify the degree of automation.','Design meaningful review and challenge routes.','Recognise the importance of explaining process and limitations.'],[
            ('Decision spectrum','''<p>AI can assist a human, recommend an outcome, rank options or make a decision with little or no human intervention. Governance should document where the system sits on this spectrum and what consequences follow.</p>'''),
            ('Meaningful intervention','''<p>A reviewer must have enough information and authority to disagree with the system. Merely pressing an approval button is not meaningful review. Organisations should also consider workload, incentives and training because these can determine whether oversight works in practice.</p>'''),
            ('Challenge and correction','''<p>Where an AI-assisted process affects people, there should be a route for errors to be identified, investigated and corrected. Governance should define who handles complaints and how recurring errors feed back into model or process improvement.</p>''')],
            '<p>A lender uses an AI score to prioritise applications for manual review. Staff rarely override it because they are measured on processing speed. The governance review identifies automation bias and redesigns performance measures, reviewer training and escalation requirements.</p>',
            '<p>Design a human-review SOP with decision criteria, evidence requirements, override authority and escalation rules.</p>',
            ['Automation level matters.','Human review must be meaningful, not ceremonial.'],
        )),
        ('05 - Algorithmic Auditing and Assurance','Plan an AI audit that produces useful evidence.',content('Algorithmic Auditing and Assurance',['Define audit objectives.','Select evidence and tests.','Report findings in a way decision-makers can act on.'],[
            ('Audit scope','''<p>Define the system, purpose, period, version, data and controls being assessed. Avoid the vague statement "audit the AI". Specify what assurance question the audit will answer.</p>'''),
            ('Evidence','''<ul><li>Model or system documentation</li><li>Data documentation</li><li>Testing results</li><li>Access logs</li><li>Change records</li><li>Incident records</li><li>Monitoring reports</li><li>Approval evidence</li></ul>'''),
            ('Findings','''<p>Good audit findings explain condition, criteria, cause, impact and recommended action. Findings should be prioritised according to risk and assigned owners with due dates.</p>''')],
            '<p>An internal audit finds that an AI system passed its original validation but has no evidence of fairness testing after deployment. The finding is not that the model is automatically discriminatory; it is that the monitoring control is insufficient to demonstrate continued fitness.</p>',
            '<p>Create an audit programme with five objectives and two tests per objective.</p>',
            ['Audit should answer a defined assurance question.','Missing evidence is itself a governance signal.'],
        )),
        ('06 - Fairness, Bias and Equality Risk','Assess discriminatory outcomes and controls.',content('Fairness, Bias and Equality Risk',['Identify bias sources.','Plan outcome testing.','Connect technical findings to organisational decisions.'],[
            ('Bias sources','''<p>Historical data can reproduce past inequalities. Sampling can underrepresent groups. Labels can reflect subjective or biased decisions. Features can act as proxies. Deployment can differ from the environment in which the system was tested.</p>'''),
            ('Testing and interpretation','''<p>Testing should compare appropriate outcomes across relevant groups. The chosen metric must fit the use case. A statistical disparity is a reason to investigate, not a complete legal or ethical conclusion.</p>'''),
            ('Control options','''<p>Controls can include improved data, revised features, threshold changes, additional human review, restricted use, monitoring or withdrawal. The organisation should test whether a mitigation introduces new problems.</p>''')],
            '<p>A customer eligibility model has a lower approval rate for one group. The compliance team asks the data team to investigate data quality, historical patterns and model features, then asks legal and business specialists to interpret the result and determine appropriate action.</p>',
            '<p>Create a fairness test plan and define what result would trigger escalation.</p>',
            ['Fairness requires both measurement and contextual judgement.','A single accuracy number cannot establish fairness.'],
        )),
        ('07 - AI Transparency, Records and Documentation','Create a defensible AI compliance evidence trail.',content('AI Transparency, Records and Documentation',['Identify core AI records.','Design documentation that supports operations.','Explain why evidence must be kept current.'],[
            ('Core records','''<p>Useful records include use-case statement, system description, data map, risk assessment, DPIA where relevant, testing, approvals, supplier due diligence, monitoring, incidents and change history.</p>'''),
            ('Documentation quality','''<p>Documentation should be understandable to its audience and specific enough to support action. A 50-page document that nobody uses is less useful than concise records embedded in the approval and monitoring workflow.</p>'''),
            ('Change control','''<p>AI systems change through model updates, new data, new prompts, supplier changes and altered business processes. Records should identify what changed, who approved it and whether reassessment was triggered.</p>''')],
            '<p>A supplier silently changes a model version. The organisation discovers the change only after customer complaints. The compliance programme is strengthened by contractual change notification, inventory version tracking and a re-assessment trigger.</p>',
            '<p>Design a one-page AI system record containing at least 12 fields and a change log.</p>',
            ['Documentation is a control, not decoration.','Change management is part of AI compliance.'],
        )),
        ('08 - Supplier Compliance and Contract Controls','Manage AI compliance in third-party services.',content('Supplier Compliance and Contract Controls',['Perform proportionate vendor due diligence.','Identify contractual controls.','Monitor supplier changes.'],[
            ('Due diligence','''<p>Assess privacy, security, data location, subprocessors, model training, testing, incident response, resilience and assurance. The depth should match the use case.</p>'''),
            ('Contract controls','''<p>Depending on the service, consider data-use restrictions, confidentiality, security standards, incident notification, audit information, change notification, service continuity and exit arrangements.</p>'''),
            ('Ongoing oversight','''<p>Supplier risk is not finished when procurement signs a contract. Review assurance evidence, incidents, material changes and service performance throughout the relationship.</p>''')],
            '<p>A supplier refuses to explain how customer data is handled and will not provide meaningful security assurance. The project sponsor wants to proceed because the product is cheap. The compliance recommendation is to treat the missing evidence as a risk decision and escalate rather than allowing price alone to determine acceptance.</p>',
            '<p>Create a supplier scorecard with privacy, security, fairness, transparency, resilience and change-management categories.</p>',
            ['Supplier controls should be risk-based.','Unanswered due-diligence questions are risk information.'],
        )),
        ('09 - AI Incidents and Regulatory Escalation','Respond to AI compliance incidents.',content('AI Incidents and Regulatory Escalation',['Classify AI incidents.','Build an escalation path.','Coordinate technical, legal, privacy and business response.'],[
            ('Incident examples','''<p>Examples include personal-data exposure, materially harmful decisions, systemic bias, unsafe outputs, security compromise, unauthorised use and supplier failures.</p>'''),
            ('Response','''<ol><li>Detect.</li><li>Record.</li><li>Contain.</li><li>Assess severity and affected people.</li><li>Escalate.</li><li>Investigate.</li><li>Consider notification duties.</li><li>Remediate.</li><li>Document lessons.</li></ol>'''),
            ('Avoid premature conclusions','''<p>Incident teams should preserve evidence and avoid assuming the model is solely responsible. The issue may involve data, configuration, human process, supplier change or inadequate controls.</p>''')],
            '<p>An AI assistant exposes a fragment of confidential information in a customer response. The incident team immediately disables the affected feature, preserves logs, identifies the data involved, assesses scope and brings privacy, security, legal and business owners into the response.</p>',
            '<p>Write an AI incident escalation matrix with severity levels and required functions.</p>',
            ['Containment and evidence preservation come first.','Legal/regulatory notification decisions should be made by appropriate specialists based on facts.'],
        )),
        ('10 - Continuous Compliance Monitoring','Turn compliance into an ongoing programme.',content('Continuous Compliance Monitoring',['Define compliance indicators.','Create review cycles.','Use monitoring to trigger action.'],[
            ('What to monitor','''<ul><li>Risk status</li><li>Fairness results</li><li>Privacy incidents</li><li>Complaints</li><li>Security events</li><li>Model changes</li><li>Supplier changes</li><li>Human overrides</li><li>Training completion</li></ul>'''),
            ('Trigger-based review','''<p>Review should occur not only on a calendar but after material changes, incidents, new data sources, new purposes, supplier changes or significant performance deterioration.</p>'''),
            ('Management reporting','''<p>Executives need concise information: number of AI systems, risk distribution, overdue reviews, material incidents, unresolved high risks and key control failures. A dashboard should support decisions rather than become another administrative report.</p>''')],
            '<p>An organisation reviews every AI system annually but misses a major supplier model update between reviews. The compliance team introduces event-driven reassessment triggers alongside periodic review.</p>',
            '<p>Design a quarterly compliance dashboard with 10 indicators and define the action triggered by each red status.</p>',
            ['Continuous compliance combines periodic and event-driven review.','Metrics matter only when they lead to action.'],
        )),
    ]
    for i,(t,d,h) in enumerate(data,1): lesson(c,t,d,h,i,preview=i<=2)
    a=lesson(c,'Final Compliance Case Study','Demonstrate practical compliance judgement.',content('Final Compliance Case Study',['Build a compliance plan for a consequential AI use case.','Identify missing evidence and controls.'],[('Scenario','''<p>A UK employer proposes an AI recruitment platform supplied by a third party. The system ranks applicants, processes CV information and receives periodic model updates. The supplier provides a general compliance statement but limited technical evidence.</p>'''),('Your task','''<p>Determine what the organisation should assess before approval, what evidence it should require, which specialists should be involved and how compliance should be monitored after launch.</p>''')],'<p>Your recommendation should address privacy, fairness, transparency, human review, supplier assurance, documentation, incidents and monitoring.</p>','<p>Write a compliance decision paper: approve, approve with conditions, defer or reject. Defend the decision using evidence requirements and controls.</p>',['Compliance is a continuous management process.','Good compliance recommendations are specific, proportionate and evidence-based.']),len(data)+1,False)
    quiz(a,'UK AI Compliance Professional Final Assessment','Scenario-based final assessment.',[
        {'question':'What should determine compliance scope?','options':['The vendor marketing label','The actual use case, data, impact and applicable requirements','The cheapest option','The model size alone'],'correct_answer':1,'explanation':'Scope depends on what the system does and the risks and obligations engaged.'},
        {'question':'What is the purpose of a DPIA?','options':['Model optimisation','Identify and mitigate data-protection risks','Marketing approval','Supplier pricing'],'correct_answer':1,'explanation':'A DPIA is a structured privacy risk assessment.'},
        {'question':'A fairness disparity appears after deployment. What should happen?','options':['Ignore it','Investigate, assess impact and apply appropriate mitigation','Delete the monitoring system','Blame the supplier automatically'],'correct_answer':1,'explanation':'Post-deployment disparities require investigation and risk-based action.'},
        {'question':'Which is strong compliance evidence?','options':['A vendor slogan','Documented assessment, testing, approval and monitoring records','An informal conversation','A product screenshot'],'correct_answer':1,'explanation':'Evidence should demonstrate how compliance controls operated.'},
        {'question':'Why monitor supplier changes?','options':['They can change system behaviour or risk','They never matter','Only finance needs to know','It is optional for every AI system'],'correct_answer':0,'explanation':'Material changes can alter risk and may require reassessment.'},
        {'question':'What is meaningful human review?','options':['Automatic approval','A competent reviewer able to challenge and override','A name on a policy','No human involvement'],'correct_answer':1,'explanation':'Human review requires real authority and capability.'},
        {'question':'Which is an incident-response priority?','options':['Hide the incident','Contain harm and preserve evidence','Delete logs','Continue unchanged'],'correct_answer':1,'explanation':'Containment and evidence support effective investigation and remediation.'},
        {'question':'Why should compliance monitoring use triggers?','options':['Material changes can occur between scheduled reviews','Annual reviews always catch everything','Triggers replace governance','Triggers remove documentation'],'correct_answer':0,'explanation':'Event-driven review catches important changes sooner.'},
    ],70)
    return c


# ---------------------------------------------------------------------------
# COURSE 3: RESPONSIBLE AI
# ---------------------------------------------------------------------------

def build_responsible(user, cat):
    c = course(
        title='Responsible AI Development in the UK', slug='responsible-ai-development-uk', instructor=user, category=cat,
        short_description='A practical foundation in fairness, privacy, transparency, safety, security, accountability and human-centred AI development.',
        description='''<h2>Responsible AI Development</h2><p>This course introduces the principles and practical habits required to build and deploy AI responsibly. Learners move from ethical concepts to concrete development and governance activities.</p>''',
        level='beginner', duration='6 Weeks', price=0.00, is_free=True, has_certificate=False,
        status='published', language='English', badge='new', badge_updated_at=timezone.now(),
    )
    data=[
        ('01 - What Responsible AI Means','Understand the purpose of responsible AI.',content('What Responsible AI Means',['Define responsible AI.','Identify core principles.','Understand why technical performance is not enough.'],[
            ('Beyond accuracy','''<p>An AI system can be accurate and still create unacceptable harm. Responsible development considers people, context, consequences, accessibility, privacy, security, fairness and accountability alongside technical performance.</p>'''),
            ('Principles','''<p>Common principles include fairness, transparency, accountability, privacy, safety, security, human oversight and reliability. The practical challenge is translating principles into design requirements and operational controls.</p>'''),
            ('Lifecycle mindset','''<p>Responsible AI starts with deciding whether AI is appropriate for the problem. It continues through data collection, development, testing, deployment, monitoring and retirement.</p>''')],
            '<p>A company proposes an AI system to analyse employee productivity. The technical team focuses on prediction accuracy. Responsible AI review adds proportionality, privacy, employee impact, bias, security and human review questions.</p>',
            '<p>Choose an AI use case and write one responsible-AI requirement for fairness, privacy, transparency, security and human oversight.</p>',
            ['Responsible AI is broader than technical accuracy.','Principles become useful when translated into controls and decisions.'],
        )),
        ('02 - Problem Definition and AI Appropriateness','Decide whether AI should be used at all.',content('Problem Definition and AI Appropriateness',['Define the problem before selecting technology.','Evaluate whether AI is proportionate.','Avoid automation for its own sake.'],[
            ('Start with the problem','''<p>Teams sometimes begin with a technology and search for a use. Responsible development reverses the order: define the outcome, understand constraints and compare AI with simpler alternatives.</p>'''),
            ('Appropriateness questions','''<ul><li>Does AI materially improve the process?</li><li>What happens when it is wrong?</li><li>Can a simpler rule-based process achieve the same result?</li><li>Is the data suitable?</li><li>Can affected people challenge outcomes?</li></ul>''')],
            '<p>A business wants facial analysis simply because the technology is available. A responsible assessment finds that the actual business need can be met by a less intrusive process and recommends not deploying the AI system.</p>',
            '<p>Write a one-page AI appropriateness assessment for a proposed use case.</p>',
            ['Responsible AI includes the option not to use AI.','Proportionality should influence technology selection.'],
        )),
        ('03 - Data Quality, Provenance and Minimisation','Build responsible data practices.',content('Data Quality, Provenance and Minimisation',['Assess data quality and representativeness.','Understand provenance.','Minimise unnecessary information.'],[
            ('Quality','''<p>AI systems inherit weaknesses in data. Missing values, historical bias, inconsistent labels and measurement errors can produce misleading outputs. Data quality must therefore be assessed against the actual use case.</p>'''),
            ('Provenance','''<p>Teams should understand where important datasets came from, what permissions or restrictions apply, how they were transformed and who is responsible for maintaining them.</p>'''),
            ('Minimisation','''<p>More data is not automatically better. Unnecessary personal or confidential information increases privacy and security exposure and can make governance more difficult.</p>''')],
            '<p>A model is trained on ten years of historical customer data. The team assumes the dataset is representative because it is large. Analysis reveals older records were collected under different processes and contain systematic gaps.</p>',
            '<p>Create a dataset assessment checklist covering quality, provenance, representativeness, minimisation, security and retention.</p>',
            ['Large datasets can still be biased or poor quality.','Data provenance and minimisation are responsible-development controls.'],
        )),
        ('04 - Fairness and Non-Discrimination','Build fairness into design and testing.',content('Fairness and Non-Discrimination',['Identify sources of bias.','Plan fairness evaluation.','Choose mitigation carefully.'],[
            ('Sources of bias','''<p>Bias can originate in historical decisions, sampling, labels, feature engineering, deployment context and feedback loops. It can also arise when the target variable reflects a historical inequality rather than a neutral measure.</p>'''),
            ('Testing','''<p>Define relevant groups and outcomes, select suitable measures, compare results and investigate disparities. Fairness assessment should involve appropriate domain expertise because statistical results require contextual interpretation.</p>'''),
            ('Mitigation','''<p>Mitigation may involve data improvement, feature changes, threshold adjustments, human review, narrower deployment or stopping the use case. Every mitigation should itself be evaluated for unintended effects.</p>''')],
            '<p>An AI system for candidate screening shows a disparity between groups. The team does not simply remove the sensitive attribute; it investigates proxies, historical data, labels and model behaviour and develops a mitigation plan.</p>',
            '<p>Write five questions a developer should ask before declaring an AI model "fair".</p>',
            ['Fairness is contextual.','Removing sensitive fields alone does not guarantee fairness.'],
        )),
        ('05 - Transparency and Explainability','Design understandable AI interactions.',content('Transparency and Explainability',['Explain the difference between transparency and explainability.','Design information for different audiences.','Support challenge and correction.'],[
            ('Transparency','''<p>Transparency communicates what AI is doing, why it is being used and what role it plays. Different audiences need different levels of detail.</p>'''),
            ('Explainability','''<p>Explainability is about making the system\'s contribution understandable enough for a relevant person to review or respond. A technical description may not be an effective explanation for an affected customer.</p>'''),
            ('Limitations','''<p>Responsible systems communicate important limitations. Users should understand when outputs may be unreliable and what they should do when uncertainty is high.</p>''')],
            '<p>A customer-support AI generates confident but incorrect answers. The organisation adds source references, confidence handling, human escalation and clear instructions that generated content requires review for specified topics.</p>',
            '<p>Create a user-facing explanation for an AI system and a separate operator-facing explanation. Make each appropriate to its audience.</p>',
            ['Explainability should serve a practical purpose.','Users need information about limitations as well as capabilities.'],
        )),
        ('06 - Privacy by Design','Integrate privacy into development.',content('Privacy by Design',['Identify privacy risks early.','Apply minimisation and access controls.','Understand the role of privacy assessment.'],[
            ('Design controls','''<p>Privacy-friendly design can include minimised fields, restricted access, retention limits, separation of environments, appropriate security, controlled prompts and reduced exposure of raw personal data.</p>'''),
            ('Privacy risk review','''<p>Where the processing creates significant risk, appropriate privacy professionals and formal assessments should be involved. The goal is to change the design where necessary, not simply document a decision already made.</p>''')],
            '<p>A development team wants to log every user prompt indefinitely for model improvement. Privacy review identifies that the full logs are unnecessary and increases exposure. The team introduces shorter retention, redaction and restricted access.</p>',
            '<p>Review an imaginary AI logging design and identify three privacy-by-design improvements.</p>',
            ['Privacy is a design requirement.','Logging can create a new data-protection risk.'],
        )),
        ('07 - Safety, Reliability and Robustness','Design systems that fail safely.',content('Safety, Reliability and Robustness',['Differentiate reliability from safety.','Plan testing for unexpected conditions.','Design safe failure and escalation.'],[
            ('Reliability','''<p>Reliability concerns whether the system performs consistently under expected conditions. Safety asks whether failures can cause unacceptable harm and what safeguards exist.</p>'''),
            ('Robustness testing','''<p>Test unusual inputs, missing data, adversarial conditions, distribution changes and known failure modes. Test the complete human-and-system process, not only the model in isolation.</p>'''),
            ('Safe failure','''<p>Where uncertainty is high, the system may need to defer to a human, restrict an action or stop rather than produce a confident but unsafe result.</p>''')],
            '<p>An AI customer triage system encounters a new type of complaint and produces an unreliable category. Instead of forcing a prediction, the redesigned system routes unfamiliar cases to trained staff.</p>',
            '<p>List five failure modes for an AI application and specify the safe response for each.</p>',
            ['Good systems are designed for failure as well as success.','Uncertainty should influence escalation behaviour.'],
        )),
        ('08 - AI Security and Misuse','Protect AI systems, data and interfaces.',content('AI Security and Misuse',['Identify AI-specific security concerns.','Apply defence-in-depth thinking.','Recognise misuse and prompt-related threats.'],[
            ('Threats','''<p>AI systems can face data leakage, unauthorised access, malicious inputs, prompt injection, model abuse, compromised dependencies and manipulation of outputs. Generative systems can also be persuaded to reveal information they should not expose if surrounding controls are weak.</p>'''),
            ('Controls','''<ul><li>Strong identity and access control</li><li>Data segregation</li><li>Input/output validation</li><li>Secrets management</li><li>Monitoring and logging</li><li>Security testing</li><li>Least privilege</li><li>Incident response</li></ul>''')],
            '<p>An internal AI assistant has access to sensitive documents. A prompt-injection test causes it to reveal information from a restricted source. The responsible response is to treat the finding as a security design issue, restrict retrieval permissions and retest rather than simply telling users not to ask malicious questions.</p>',
            '<p>Threat-model an AI assistant. Identify assets, attackers, entry points, likely abuse cases and controls.</p>',
            ['AI security includes the surrounding application and data architecture.','User instructions are not a substitute for technical access controls.'],
        )),
        ('09 - Human Oversight and Human-Centred Design','Design meaningful human control.',content('Human Oversight and Human-Centred Design',['Design effective review.','Reduce automation bias.','Give users authority to intervene.'],[
            ('Human-in-the-loop is not enough','''<p>Calling a process "human-in-the-loop" does not prove that oversight is meaningful. Reviewers need appropriate training, time, context, authority and escalation routes.</p>'''),
            ('Automation bias','''<p>People may over-trust machine recommendations, especially when the system appears sophisticated or when staff are under time pressure. Interface design, training and performance incentives can reduce or increase this effect.</p>'''),
            ('Feedback','''<p>Human overrides and corrections are valuable monitoring signals. Organisations should examine why people disagree with AI and whether recurring patterns indicate model or process weaknesses.</p>''')],
            '<p>An AI system recommends which customer complaints should be escalated. Staff are rewarded for speed and rarely challenge recommendations. A responsible redesign changes training, review requirements and performance metrics so quality and challenge are valued.</p>',
            '<p>Create a human oversight checklist for a high-impact AI recommendation system.</p>',
            ['Oversight requires authority and competence.','Override behaviour can be an important monitoring signal.'],
        )),
        ('10 - Responsible AI Development Lifecycle','Integrate responsible practices from idea to retirement.',content('Responsible AI Development Lifecycle',['Apply responsible AI throughout development.','Build a repeatable release process.','Know when to pause or retire a system.'],[
            ('Lifecycle gates','''<ol><li>Problem definition</li><li>Appropriateness assessment</li><li>Stakeholder and impact analysis</li><li>Data assessment</li><li>Risk assessment</li><li>Design controls</li><li>Development and testing</li><li>Independent or specialist review where appropriate</li><li>Controlled deployment</li><li>Monitoring</li><li>Change review</li><li>Retirement</li></ol>'''),
            ('Release criteria','''<p>A responsible release should have clear evidence requirements. These can include performance tests, fairness assessment, privacy review, security testing, documentation, human oversight and monitoring readiness. The required evidence should be proportionate to impact.</p>'''),
            ('Retirement','''<p>Responsible AI includes knowing when to stop. If a system becomes unsuitable, its data becomes unreliable, the risk cannot be controlled or a safer alternative becomes available, retirement may be the responsible decision.</p>''')],
            '<p>A model has been in production for three years. Its performance has declined because customer behaviour changed, while the original monitoring plan did not include drift. The responsible team does not simply retrain automatically; it reassesses purpose, data, risk and controls before deciding whether to update, redesign or retire the system.</p>',
            '<p>Create a responsible-AI release checklist with at least 15 checks covering purpose, data, fairness, privacy, security, safety, transparency, oversight and monitoring.</p>',
            ['Responsible AI is a lifecycle discipline.','Release and retirement should both be governed decisions.'],
        )),
    ]
    for i,(t,d,h) in enumerate(data,1): lesson(c,t,d,h,i,preview=i<=2)
    a=lesson(c,'Final Responsible AI Assessment','Apply responsible AI principles to a realistic development scenario.',content('Final Responsible AI Assessment',['Identify responsible-AI risks.','Recommend design controls.'],[('Scenario','''<p>A company is building an AI assistant that summarises customer cases and recommends next actions to support staff. The system will process customer text and internal knowledge. It may occasionally produce incorrect or biased recommendations.</p>'''),('Assessment task','''<p>Consider data quality, privacy, security, fairness, transparency, safety, human oversight, monitoring and retirement.</p>''')],'<p>The best solution is not simply "add a disclaimer". Consider technical, organisational and human controls together.</p>','<p>Write a responsible-AI design review containing: risks, controls, release criteria, monitoring metrics and escalation triggers.</p>',['Responsible AI turns principles into design and operational choices.','Good controls combine technology, process and human judgement.']),len(data)+1,False)
    quiz(a,'Responsible AI Professional Final Assessment','Scenario-based final assessment.',[
        {'question':'What should happen before selecting an AI technology?','options':['Define the business problem and assess whether AI is appropriate','Buy the most advanced model','Deploy immediately','Ignore alternatives'],'correct_answer':0,'explanation':'Responsible development starts with the problem and appropriateness decision.'},
        {'question':'Why can a large dataset still create bias?','options':['Large datasets are always fair','Historical or sampling biases can remain','Size removes all errors','Bias only comes from software bugs'],'correct_answer':1,'explanation':'Scale does not guarantee representativeness or fairness.'},
        {'question':'What is meaningful human oversight?','options':['A person approves everything automatically','A competent person can understand, challenge and override outputs','A person is listed as owner','No human involvement'],'correct_answer':1,'explanation':'Oversight requires real authority and capability.'},
        {'question':'Which is a privacy-by-design control?','options':['Collect everything forever','Minimise data and restrict access','Share logs widely','Add privacy after launch'],'correct_answer':1,'explanation':'Minimisation and access controls reduce unnecessary exposure.'},
        {'question':'Why test unusual inputs?','options':['To identify failure modes and robustness weaknesses','To make the interface prettier','It is only marketing','Unusual inputs never matter'],'correct_answer':0,'explanation':'Robustness testing helps identify unsafe or unreliable behaviour.'},
        {'question':'What should happen when a system cannot safely handle an input?','options':['Force a confident answer','Use a defined safe-failure or human-escalation path','Hide the error','Delete the user'],'correct_answer':1,'explanation':'Safe failure prevents uncertain systems from creating avoidable harm.'},
        {'question':'Why is AI security broader than model security?','options':['The surrounding data, interfaces and access controls also create attack paths','Security is irrelevant to AI','Only the model matters','Security is only physical'],'correct_answer':0,'explanation':'AI security includes application, data, identity, interfaces and dependencies.'},
        {'question':'What is an appropriate reason to retire an AI system?','options':['Its risk can no longer be controlled or its purpose is no longer appropriate','It has been used for one month','A new logo exists','Employees like it'],'correct_answer':0,'explanation':'Retirement can be the responsible choice when a system is no longer fit or controllable.'},
    ],70)
    return c


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

print('=' * 72)
print('PROFESSIONAL UK AI COURSE BUILDER')
print('=' * 72)

u = instructor()
gov = category('ai-governance','AI Governance','Professional AI governance and organisational risk management.')
comp = category('ai-compliance','AI Compliance','AI compliance, privacy, auditing and regulatory risk.')
eth = category('ai-ethics','AI Ethics','Responsible and ethical AI development and deployment.')

c1 = build_governance(u, gov)
c2 = build_compliance(u, comp)
c3 = build_responsible(u, eth)

for c in (c1,c2,c3):
    print(f'Created: {c.title} | lessons={c.total_lessons} | price={c.price_display}')

print('\nDONE.')
print('Run: python manage.py shell < create_uk_courses_professional.py')
