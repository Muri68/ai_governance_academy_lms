from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.dashboard.models import SiteSetting, FAQ  # Update with your actual app name


class Command(BaseCommand):
    help = 'Populate default Privacy Policy, Terms & Conditions, and FAQs'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating default content...')
        
        # ==========================================
        # PRIVACY POLICY
        # ==========================================
        privacy_content = """
<h2 id="information-we-collect">1. Information We Collect</h2>

<h3>Personal Information</h3>
<p>We may collect personal information that you voluntarily provide when you:</p>
<ul>
    <li>Create an account on our platform</li>
    <li>Enroll in a course</li>
    <li>Subscribe to our newsletter</li>
    <li>Contact us through our contact form</li>
    <li>Participate in surveys or assessments</li>
</ul>
<p>This information may include your name, email address, phone number, billing information, and professional details.</p>

<h3>Automatically Collected Information</h3>
<p>When you access our website, we automatically collect certain information including:</p>
<ul>
    <li>IP address and browser type</li>
    <li>Device information and operating system</li>
    <li>Pages visited and time spent on pages</li>
    <li>Referring website addresses</li>
    <li>Course progress and completion data</li>
</ul>

<h2 id="how-we-use">2. How We Use Your Information</h2>
<p>We use the collected information for the following purposes:</p>
<ul>
    <li>To provide and maintain our educational services</li>
    <li>To process course enrollments and payments</li>
    <li>To track your learning progress and issue certificates</li>
    <li>To send administrative information and updates</li>
    <li>To respond to your inquiries and provide support</li>
    <li>To improve our platform and user experience</li>
    <li>To comply with legal obligations</li>
</ul>

<h2 id="data-sharing">3. Data Sharing and Disclosure</h2>
<p>We do not sell, trade, or rent your personal information to third parties. We may share your information in the following circumstances:</p>
<ul>
    <li><strong>With instructors:</strong> Course instructors can see enrolled students' names and progress</li>
    <li><strong>Service providers:</strong> Trusted third parties who assist in operating our platform</li>
    <li><strong>Legal requirements:</strong> When required by law or to protect our rights</li>
    <li><strong>Business transfers:</strong> In connection with a merger, sale, or acquisition</li>
</ul>

<h2 id="data-security">4. Data Security</h2>
<p>We implement appropriate technical and organizational security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. These measures include:</p>
<ul>
    <li>SSL/TLS encryption for data transmission</li>
    <li>Secure server infrastructure</li>
    <li>Regular security assessments and updates</li>
    <li>Access controls and authentication mechanisms</li>
</ul>

<h2 id="cookies">5. Cookies and Tracking Technologies</h2>
<p>We use cookies and similar tracking technologies to enhance your browsing experience. Cookies are small text files stored on your device that help us:</p>
<ul>
    <li>Remember your login status and preferences</li>
    <li>Analyze website traffic and usage patterns</li>
    <li>Provide personalized content and recommendations</li>
</ul>
<p>You can control cookie preferences through your browser settings. Disabling cookies may affect certain features of our platform.</p>

<h2 id="your-rights">6. Your Rights</h2>
<p>Depending on your location, you may have the following rights regarding your personal data:</p>
<ul>
    <li><strong>Access:</strong> Request a copy of your personal data</li>
    <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
    <li><strong>Erasure:</strong> Request deletion of your personal data</li>
    <li><strong>Portability:</strong> Receive your data in a structured format</li>
    <li><strong>Objection:</strong> Object to processing of your personal data</li>
    <li><strong>Withdraw consent:</strong> Withdraw previously given consent</li>
</ul>

<h2 id="third-party">7. Third-Party Services</h2>
<p>Our platform may contain links to third-party websites and services. We are not responsible for the privacy practices of these external sites. We encourage you to review their privacy policies before providing any personal information.</p>

<h2 id="children">8. Children's Privacy</h2>
<p>Our services are not directed to individuals under the age of 13. We do not knowingly collect personal information from children. If we become aware that a child has provided us with personal information, we will take steps to delete such information.</p>

<h2 id="changes">9. Changes to This Privacy Policy</h2>
<p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the "Last updated" date. We encourage you to review this policy periodically.</p>

<h2 id="contact">10. Contact Us</h2>
<p>If you have any questions about this Privacy Policy or our data practices, please contact us:</p>
<ul>
    <li><strong>Email:</strong> privacy@aiga.com</li>
    <li><strong>Address:</strong> AI Governance Academy, 123 Innovation Drive, San Jose, CA 95113</li>
    <li><strong>Phone:</strong> +1 (223) 456-6000</li>
</ul>
"""
        SiteSetting.objects.update_or_create(
            key='privacy_policy',
            defaults={
                'value': privacy_content,
                'setting_type': 'content',
                'description': 'Privacy Policy page content'
            }
        )
        self.stdout.write(self.style.SUCCESS('✅ Privacy Policy populated'))

        # ==========================================
        # TERMS & CONDITIONS
        # ==========================================
        terms_content = """
<h2>1. Acceptance of Terms</h2>
<p>By creating an account, enrolling in a course, or otherwise using our services, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions, our Privacy Policy, and any additional guidelines or rules applicable to specific services.</p>

<h2>2. Definitions</h2>
<p>For the purposes of these Terms and Conditions:</p>
<ul>
    <li><strong>"Platform"</strong> refers to the AI Governance Academy website and all related services</li>
    <li><strong>"User," "You,"</strong> refers to any individual who accesses or uses our platform</li>
    <li><strong>"Instructor"</strong> refers to users who create and publish courses on our platform</li>
    <li><strong>"Student"</strong> refers to users who enroll in and take courses</li>
    <li><strong>"Content"</strong> includes all materials, courses, videos, text, and resources</li>
</ul>

<h2>3. Account Registration</h2>
<p>To access certain features of our platform, you must register for an account. You agree to:</p>
<ul>
    <li>Provide accurate, current, and complete registration information</li>
    <li>Maintain and promptly update your account information</li>
    <li>Keep your password confidential and secure</li>
    <li>Accept responsibility for all activities under your account</li>
    <li>Notify us immediately of any unauthorized use of your account</li>
</ul>

<h2>4. Course Enrollment and Access</h2>
<h3>4.1 Enrollment</h3>
<p>When you enroll in a course, you receive a limited, non-exclusive, non-transferable license to access the course content for personal educational purposes. This license is valid for the lifetime of the course on our platform.</p>
<h3>4.2 Payment and Refunds</h3>
<p>Course fees are displayed at the time of enrollment. All payments are processed securely through our payment partners. Our refund policy allows for refunds within 14 days of purchase, provided you have not completed more than 25% of the course content.</p>
<h3>4.3 Free Courses</h3>
<p>Free courses are provided at no cost but are still subject to these Terms and Conditions. We reserve the right to modify or discontinue free courses at any time.</p>

<h2>5. User Conduct</h2>
<p>You agree not to:</p>
<ul>
    <li>Use the platform for any unlawful purpose or in violation of any regulations</li>
    <li>Share, distribute, or resell course content without authorization</li>
    <li>Harass, abuse, or harm other users or instructors</li>
    <li>Impersonate any person or entity</li>
    <li>Interfere with or disrupt the platform or its servers</li>
    <li>Upload malicious code, viruses, or harmful content</li>
    <li>Attempt to gain unauthorized access to any part of the platform</li>
</ul>

<h2>6. Intellectual Property</h2>
<h3>6.1 Platform Content</h3>
<p>All content on our platform, including but not limited to text, graphics, logos, images, videos, software, and course materials, is protected by copyright, trademark, and other intellectual property laws.</p>
<h3>6.2 Instructor Content</h3>
<p>Instructors retain ownership of their course content. By publishing content on our platform, instructors grant us a license to host, distribute, and promote their courses.</p>
<h3>6.3 User-Generated Content</h3>
<p>By submitting reviews, comments, or other content, you grant us the right to use, display, and distribute such content in connection with our services.</p>

<h2>7. Certificate of Completion</h2>
<p>Upon successful completion of a course, you may receive a certificate of completion. Certificates are provided for personal achievement purposes and do not constitute formal academic accreditation unless explicitly stated.</p>

<h2>8. Limitation of Liability</h2>
<p>To the fullest extent permitted by law, AI Governance Academy shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the platform. Our total liability shall not exceed the amount you paid for the specific course giving rise to the claim.</p>

<h2>9. Disclaimer of Warranties</h2>
<p>The platform and all content are provided on an "as is" and "as available" basis. We make no warranties, express or implied, regarding the accuracy, completeness, or reliability of any content or the uninterrupted operation of our services.</p>

<h2>10. Termination</h2>
<p>We reserve the right to suspend or terminate your account and access to our services at any time, with or without cause, including but not limited to violation of these Terms and Conditions.</p>

<h2>11. Modifications to Terms</h2>
<p>We may modify these Terms and Conditions at any time. We will notify users of material changes via email or through the platform. Continued use of the platform after changes constitutes acceptance of the modified terms.</p>

<h2>12. Governing Law</h2>
<p>These Terms and Conditions shall be governed by and construed in accordance with the laws of the State of California, United States, without regard to its conflict of law provisions.</p>

<h2>13. Contact Information</h2>
<p>For questions about these Terms and Conditions, please contact us:</p>
<ul>
    <li><strong>Email:</strong> legal@aiga.com</li>
    <li><strong>Address:</strong> AI Governance Academy, 123 Innovation Drive, San Jose, CA 95113</li>
    <li><strong>Phone:</strong> +1 (223) 456-6000</li>
</ul>
"""
        SiteSetting.objects.update_or_create(
            key='terms_conditions',
            defaults={
                'value': terms_content,
                'setting_type': 'content',
                'description': 'Terms & Conditions page content'
            }
        )
        self.stdout.write(self.style.SUCCESS('✅ Terms & Conditions populated'))

        # ==========================================
        # FAQs
        # ==========================================
        faqs_data = [
            # General
            ('general', 'What is AI Governance Academy?', 'AI Governance Academy is an online learning platform dedicated to providing high-quality education in artificial intelligence, cybersecurity, data privacy, and governance. We partner with industry experts to deliver practical, career-focused courses that help professionals stay ahead in the rapidly evolving tech landscape.', 1),
            ('general', 'How do I create an account?', 'Creating an account is easy! Click the "Sign Up" button in the top right corner, enter your email address, create a password, and fill in your basic information. You can also sign up using your Google or LinkedIn account for faster registration.', 2),
            ('general', 'Is the platform free to use?', 'Creating an account and browsing courses is completely free. We offer both free and paid courses. Free courses provide full access to learning materials at no cost. Paid courses offer more comprehensive content, certificates, and instructor support.', 3),
            
            # Courses
            ('courses', 'How do I enroll in a course?', 'To enroll in a course, browse our course catalog and click on any course that interests you. On the course detail page, click the "Enroll Now" button. For free courses, you\'ll be enrolled immediately. For paid courses, you\'ll be directed to our secure payment page.', 1),
            ('courses', 'How long do I have access to a course?', 'Once you enroll in a course, you have lifetime access to the course materials. You can learn at your own pace and revisit the content as many times as you want. There are no deadlines or expiration dates for course access.', 2),
            ('courses', 'Can I preview a course before enrolling?', 'Yes! Many courses offer free preview lessons. On the course detail page, look for lessons marked with "Preview" in the curriculum section. This allows you to sample the course content and teaching style before making a commitment.', 3),
            ('courses', 'What skill levels do your courses cover?', 'We offer courses for all skill levels:<br><br><strong>Beginner:</strong> No prior experience required<br><strong>Intermediate:</strong> Basic knowledge recommended<br><strong>Advanced:</strong> For experienced professionals<br><strong>All Levels:</strong> Suitable for everyone', 4),
            
            # Payment
            ('payment', 'What payment methods do you accept?', 'We accept all major credit and debit cards including Visa, MasterCard, American Express, and Discover. All payments are processed securely through Stripe, our trusted payment partner.', 1),
            ('payment', 'What is your refund policy?', 'We offer a 14-day money-back guarantee on all paid courses. If you\'re not satisfied with a course, you can request a refund within 14 days of purchase, provided you haven\'t completed more than 25% of the course content. Refunds are processed within 5-10 business days.', 2),
            ('payment', 'Do you offer discounts or promotions?', 'Yes! We regularly offer promotional discounts and seasonal sales. Subscribe to our newsletter to stay informed about upcoming promotions. Some instructors also offer discount coupons for their courses.', 3),
            
            # Technical
            ('technical', 'What are the system requirements?', 'Our platform works on any modern web browser including Chrome, Firefox, Safari, and Edge. You\'ll need a stable internet connection for video streaming. For the best experience, we recommend:<br><br>• Updated web browser (latest 2 versions)<br>• Internet speed of at least 2 Mbps for video<br>• JavaScript enabled<br>• Screen resolution of 1024x768 or higher', 1),
            ('technical', 'Can I access courses on mobile devices?', 'Yes! Our platform is fully responsive and works on smartphones and tablets. You can learn on the go using any mobile browser. The video player, quizzes, and all course materials are optimized for mobile viewing.', 2),
            ('technical', 'What if I encounter technical issues?', 'If you experience any technical issues, try the following:<br><br>• Clear your browser cache and cookies<br>• Try a different browser<br>• Check your internet connection<br>• Contact our support team at support@aiga.com', 3),
            
            # Certificates
            ('certificates', 'Do I get a certificate upon completion?', 'Yes! Upon completing all lessons in a course, you\'ll receive a Certificate of Completion. The certificate includes your name, course title, completion date, and a unique verification code that can be shared with employers or on your LinkedIn profile.', 1),
            ('certificates', 'Are the certificates accredited?', 'Our certificates are proof of completion and demonstrate your commitment to professional development. While they are not formal academic credentials, they are valued by employers as evidence of practical skills and continuous learning.', 2),
            ('certificates', 'How can I share my certificate?', 'You can download your certificate as a PDF and share it directly on LinkedIn, add it to your resume, or include the verification link in your portfolio. Each certificate has a unique verification URL that allows employers to confirm its authenticity.', 3),
        ]
        
        for category, question, answer, order in faqs_data:
            FAQ.objects.update_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'category': category,
                    'order': order,
                    'is_active': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(faqs_data)} FAQs populated'))
        self.stdout.write(self.style.SUCCESS('\n🎉 All default content populated successfully!'))
        self.stdout.write('\nYou can now manage this content from:')
        self.stdout.write('  Admin Dashboard > Settings > Content Pages (Privacy & Terms)')
        self.stdout.write('  Admin Dashboard > Settings > FAQ Management')