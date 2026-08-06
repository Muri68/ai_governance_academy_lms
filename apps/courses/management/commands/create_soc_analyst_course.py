
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import CourseCategory, Course, Lesson, LessonContent
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = "Create the complete Security Operations Center (SOC) Analyst course"

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating SOC Analyst course...")

        category, _ = CourseCategory.objects.get_or_create(
            slug="cybersecurity",
            defaults={
                "name": "Cybersecurity",
                "description": "Cybersecurity, security operations, threat detection and incident response.",
                "icon": "fas fa-shield-alt",
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
                email="soc.instructor@aiga.ac",
                password="Instructor@123",
                first_name="Alex",
                last_name="Morgan",
                user_type="INSTRUCTOR",
                is_active=True,
                email_verified=True,
            )

        course, _ = Course.objects.update_or_create(
            slug="security-operations-center-soc-analyst",
            defaults={
                "title": "Security Operations Center (SOC) Analyst: Professional Training",
                "instructor": instructor,
                "category": category,
                "description": (
                    "A practical professional SOC Analyst program covering security "
                    "monitoring, networking, logs, SIEM, threat detection, incident "
                    "response, threat intelligence, EDR, detection engineering, "
                    "vulnerability management and SOC investigations."
                ),
                "short_description": (
                    "Learn how to monitor, investigate, triage and respond to "
                    "cybersecurity alerts as a professional SOC Analyst."
                ),
                "level": "intermediate",
                "duration": "14 Weeks",
                "language": "English",
                "price": 79.99,
                "is_free": False,
                "status": "published",
                "has_certificate": True,
                "requirements": (
                    "Basic computer literacy. Familiarity with networking, Windows, "
                    "Linux and command-line tools is helpful but not mandatory."
                ),
                "what_you_learn": (
                    "SOC operations, networking, threats, MITRE ATT&CK, Windows and "
                    "Linux logs, SIEM, alert triage, threat intelligence, EDR, incident "
                    "response, detection engineering, vulnerability management and SOC investigations."
                ),
                "published_at": timezone.now(),
            },
        )

        self.create_lessons(course)

        self.stdout.write(
            self.style.SUCCESS("SOC Analyst course created successfully!")
        )

    def quiz(self, questions):
        return {"questions": questions}

    def q(self, question, options, correct):
        return {
            "question": question,
            "options": options,
            "correct": correct,
        }

    def text(self, title, order, html, minutes=30, preview=False):
        return {
            "content_type": "text",
            "title": title,
            "order": order,
            "duration_minutes": minutes,
            "is_preview": preview,
            "text_content": html,
        }

    def code(self, title, order, source, minutes=30):
        return {
            "content_type": "code",
            "title": title,
            "order": order,
            "duration_minutes": minutes,
            "text_content": source,
        }

    def assignment(self, title, order, instructions, score=100, minutes=45):
        return {
            "content_type": "assignment",
            "title": title,
            "order": order,
            "duration_minutes": minutes,
            "assignment_instructions": instructions,
            "max_score": score,
        }

    def make_lesson(self, title, order, description, contents, preview=False):
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
                "Introduction to Security Operations and the SOC",
                1,
                "Understand SOC missions, roles, analyst responsibilities and the security monitoring lifecycle.",
                [
                    self.text(
                        "What Is a Security Operations Center?",
                        1,
                        """<h1>What Is a SOC?</h1>
<p>A <strong>Security Operations Center (SOC)</strong> is a team or function responsible
for monitoring an organization's technology environment, detecting suspicious activity,
investigating alerts, responding to incidents and improving defensive capability.</p>
<h2>SOC Mission</h2>
<ul>
<li>Collect security telemetry.</li>
<li>Detect suspicious behavior.</li>
<li>Investigate and validate alerts.</li>
<li>Contain and escalate incidents.</li>
<li>Document evidence and decisions.</li>
<li>Improve detections after investigations.</li>
</ul>
<h2>Typical SOC Workflow</h2>
<ol>
<li>Collect telemetry.</li><li>Detect activity.</li><li>Triage the alert.</li>
<li>Investigate evidence.</li><li>Respond according to procedure.</li><li>Learn and improve.</li>
</ol>
<div style="background:#dbeafe;padding:15px;border-radius:8px;">
<strong>Professional principle:</strong> An alert is a starting point for investigation,
not automatically proof of compromise.
</div>""",
                        30,
                        True,
                    ),
                    self.text(
                        "SOC Roles and Analyst Responsibilities",
                        2,
                        """<h1>SOC Roles</h1>
<h2>Common Functions</h2>
<ul>
<li><strong>Tier 1:</strong> Monitoring, enrichment, initial triage and escalation.</li>
<li><strong>Tier 2:</strong> Deeper investigation and incident analysis.</li>
<li><strong>Tier 3:</strong> Threat hunting, advanced investigation and detection engineering.</li>
<li><strong>Incident Response:</strong> Containment, eradication and recovery.</li>
<li><strong>Threat Intelligence:</strong> Adversary and indicator context.</li>
</ul>
<h2>Questions Every Analyst Should Ask</h2>
<ul><li>What happened?</li><li>When did it happen?</li>
<li>Which user, host or application was involved?</li><li>Is it expected?</li>
<li>What evidence supports the conclusion?</li><li>What should happen next?</li></ul>""",
                        30,
                    ),
                    self.code(
                        "Practice: SOC Alert Triage Checklist",
                        3,
                        """alert = {
    "id": "SOC-2026-001",
    "severity": "high",
    "source": "EDR",
    "hostname": "WS-FINANCE-01",
    "username": "analyst@example.local",
}

questions = [
    "Is the alert expected?",
    "What process triggered it?",
    "Who initiated the activity?",
    "What happened before and after?",
    "Are other systems affected?",
    "What evidence supports escalation?",
]

print("Investigating:", alert["id"])
for number, question in enumerate(questions, 1):
    print(f"{number}. {question}")

# Exercise: Add fields for timestamp, source IP, destination IP,
# evidence collected, analyst assessment and next action.
""",
                        25,
                    ),
                    self._quiz(
                        "Lesson 1 Quiz",
                        [
                            ("What is the primary purpose of a SOC?", ["Monitor, detect and respond to security events", "Develop websites", "Manage payroll", "Design graphics"], 0),
                            ("What normally happens first after an alert?", ["Triage", "Delete it", "Format the server", "Disable the firewall"], 0),
                            ("Which SOC tier commonly performs initial triage?", ["Tier 1", "Tier 4", "Finance", "Database"], 0),
                            ("What is telemetry?", ["Security-relevant data collected from systems", "A password", "A firewall only", "A backup"], 0),
                            ("A professional conclusion should be based on:", ["Evidence", "Guesswork", "Rumors", "Random selection"], 0),
                            ("What improves future SOC performance?", ["Lessons learned and detection improvement", "Ignoring incidents", "Deleting logs", "Disabling monitoring"], 0),
                            ("What is alert triage?", ["Initial assessment of an alert", "Installing Windows", "Writing malware", "Replacing hardware"], 0),
                            ("Which skill is important for a SOC Analyst?", ["Analytical thinking", "Only typing speed", "Graphic design only", "Accounting only"], 0),
                            ("Why is documentation important?", ["It supports investigation and communication", "It replaces evidence", "It is never needed", "It deletes alerts"], 0),
                            ("Good analyst decisions use:", ["Evidence and context", "Fear", "Assumptions", "Random choice"], 0),
                        ],
                        70,
                    ),
                ],
                preview=True,
            ),

            self.make_lesson(
                "Networking Fundamentals for SOC Analysts",
                2,
                "Understand IP addressing, TCP/IP, ports, DNS, HTTP, HTTPS and network investigation.",
                [
                    self.text(
                        "TCP/IP, IP Addresses and Ports",
                        1,
                        """<h1>Networking Fundamentals</h1>
<p>SOC Analysts investigate network activity constantly. Networking knowledge helps
you understand what an alert actually represents.</p>
<h2>Important Concepts</h2>
<ul><li>IP address: identifies a network interface.</li>
<li>MAC address: identifies a network interface at the data-link layer.</li>
<li>Port: identifies a service endpoint.</li>
<li>Protocol: defines how communication occurs.</li></ul>
<h2>Common Ports</h2>
<ul><li>22 - SSH</li><li>25 - SMTP</li><li>53 - DNS</li>
<li>80 - HTTP</li><li>443 - HTTPS</li><li>3389 - RDP</li></ul>
<p>A port alone does not prove which application is running. Always correlate
ports with processes, hosts, DNS and other telemetry.</p>""",
                        35,
                    ),
                    self.text(
                        "DNS, HTTP and Network Investigation",
                        2,
                        """<h1>Network Investigation</h1>
<h2>DNS</h2>
<p>DNS converts names into addresses and can provide useful evidence about unusual
domains, query volume and connections to suspicious infrastructure.</p>
<h2>HTTP and HTTPS</h2>
<p>HTTPS protects application traffic with TLS. Analysts can still investigate
metadata and endpoint/network telemetry even when content is encrypted.</p>
<h2>Questions to Ask</h2>
<ul><li>Who initiated the connection?</li><li>Where did it connect?</li>
<li>Which port and protocol were used?</li><li>Was it successful?</li>
<li>Is this normal for the host?</li><li>Did other hosts do the same thing?</li></ul>""",
                        35,
                    ),
                    self.code(
                        "Practice: Network Investigation Commands",
                        3,
                        """# Windows
ipconfig /all
nslookup example.com
ping 192.0.2.10
netstat -ano

# Linux
ip addr
ip route
ss -tulpn
dig example.com
ping -c 4 192.0.2.10

# Only investigate systems and networks you are authorized to monitor.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 2 Quiz",
                        [
                            ("What does DNS provide?", ["Name resolution", "Disk encryption", "Compression", "Passwords"], 0),
                            ("Common HTTPS port?", ["21", "53", "443", "8080"], 2),
                            ("Windows network configuration command?", ["ipconfig", "ls", "grep", "chmod"], 0),
                            ("Linux command for listening sockets?", ["ss", "mkdir", "cat", "whoami"], 0),
                            ("What is a port?", ["A service endpoint", "A password", "A user account", "A disk"], 0),
                            ("Does a port alone prove the application?", ["Yes", "No", "Only Linux", "Only Windows"], 1),
                            ("HTTPS uses:", ["TLS protection", "DHCP", "ARP", "FTP"], 0),
                            ("Useful network evidence includes:", ["Source, destination, port and context", "Only source IP", "Only username", "Nothing"], 0),
                            ("DNS investigations should consider:", ["Domain context and history", "Only domain length", "Capitalization", "Nothing"], 0),
                            ("Network investigation should be performed:", ["Only on authorized systems", "Against random systems", "Without permission", "Only on public Wi-Fi"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Cybersecurity Threats, Attacks and MITRE ATT&CK",
                3,
                "Recognize common attack patterns and map observed behavior to MITRE ATT&CK.",
                [
                    self.text(
                        "Threats and Attack Progression",
                        1,
                        """<h1>Common Cybersecurity Threats</h1>
<ul><li>Phishing and social engineering</li><li>Credential theft</li>
<li>Malware and ransomware</li><li>Unauthorized remote access</li>
<li>Web application attacks</li><li>Data exfiltration</li><li>Insider misuse</li>
<li>Command and control activity</li></ul>
<h2>Investigation Thinking</h2>
<p>Ask how access occurred, what executed, whether persistence was established,
whether privilege or credentials changed, what systems were accessed and whether
data was collected or transferred.</p>
<p>One event rarely tells the complete story. Correlation across time, hosts,
users and network activity is essential.</p>""",
                        35,
                    ),
                    self.text(
                        "MITRE ATT&CK for SOC Analysts",
                        2,
                        """<h1>MITRE ATT&CK</h1>
<p>MITRE ATT&CK is a knowledge base describing adversary tactics and techniques.
SOC teams use it to organize investigations and detection coverage.</p>
<h2>Common Tactics</h2>
<ul><li>Initial Access</li><li>Execution</li><li>Persistence</li>
<li>Privilege Escalation</li><li>Defense Evasion</li><li>Credential Access</li>
<li>Discovery</li><li>Lateral Movement</li><li>Collection</li>
<li>Command and Control</li><li>Exfiltration</li><li>Impact</li></ul>
<p>Mapping behavior helps analysts communicate consistently and identify defensive gaps.</p>""",
                        35,
                    ),
                    self.code(
                        "Practice: ATT&CK Observation Mapping",
                        3,
                        """observations = [
    "Suspicious email attachment received",
    "Unusual PowerShell execution",
    "Privileged account authenticates to another workstation",
    "Archive files created before an external connection",
]

for item in observations:
    print("[OBSERVATION]", item)

# Exercise:
# Map each observation to an ATT&CK tactic/technique.
# Then list the evidence needed before escalation.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 3 Quiz",
                        [
                            ("What is MITRE ATT&CK?", ["A knowledge base of adversary tactics and techniques", "An antivirus", "A firewall", "A programming language"], 0),
                            ("Which is an ATT&CK tactic?", ["Credential Access", "Word Processing", "Accounting", "Printing"], 0),
                            ("Why use ATT&CK?", ["To organize adversary behavior and detection coverage", "Replace firewalls", "Create passwords", "Compress logs"], 0),
                            ("Phishing is commonly associated with:", ["Initial Access", "Disk formatting", "Backup", "Printing"], 0),
                            ("PowerShell activity should be judged using:", ["Context and evidence", "The word PowerShell alone", "Random choice", "Hostname length"], 0),
                            ("Lateral movement means:", ["Moving between systems after access", "Changing wallpaper", "Updating a browser", "Backing up files"], 0),
                            ("Why correlate events?", ["To understand the broader attack story", "Delete evidence", "Reduce all alerts", "Avoid investigation"], 0),
                            ("Credential Access concerns:", ["Obtaining or attempting to obtain credentials", "Installing printers", "Changing resolution", "Creating documents"], 0),
                            ("Collection means:", ["Gathering data of interest", "Installing a monitor", "Changing DNS only", "Writing a manual"], 0),
                            ("ATT&CK mapping should use:", ["Observed behavior and evidence", "Guesswork", "Job title", "IP address alone"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Windows Security Monitoring and Event Logs",
                4,
                "Analyze Windows authentication, process and PowerShell telemetry.",
                [
                    self.text(
                        "Windows Event Logs",
                        1,
                        """<h1>Windows Event Logs</h1>
<p>Windows generates security and operational events that can be collected by
SIEM and EDR platforms.</p>
<ul><li>Security: authentication and audit activity.</li>
<li>System: OS and service events.</li><li>Application: application events.</li>
<li>PowerShell: PowerShell-related telemetry when enabled.</li></ul>
<h2>Authentication Investigation</h2>
<p>Review account, source host, destination, timestamp, authentication result,
authentication type and surrounding events.</p>
<p>A failed login followed by a successful login may be important, but context
is required before deciding whether it is malicious.</p>""",
                        40,
                    ),
                    self.text(
                        "PowerShell and Endpoint Investigation",
                        2,
                        """<h1>PowerShell Investigation</h1>
<p>PowerShell is legitimate administration technology and is also frequently
observed during attacks. Its presence alone is not proof of malicious activity.</p>
<h2>Investigate</h2>
<ul><li>Parent process</li><li>User</li><li>Command/script details</li>
<li>Host role</li><li>Network connections</li><li>File activity</li>
<li>Persistence indicators</li></ul>
<p>Compare the activity with normal administrative behavior.</p>""",
                        35,
                    ),
                    self.code(
                        "Practice: Windows Triage Commands",
                        3,
                        """whoami
hostname
ipconfig /all
tasklist
netstat -ano

# PowerShell
Get-Process
Get-Service
Get-WinEvent -LogName Security -MaxEvents 20

# Use commands only on systems you are authorized to investigate.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 4 Quiz",
                        [
                            ("Important Windows authentication log?", ["Security", "Paint", "Clipboard", "Recycle Bin"], 0),
                            ("Does PowerShell automatically mean malware?", ["Yes", "No", "Only servers", "Only laptops"], 1),
                            ("What should surround a suspicious login?", ["Related events and context", "Only username", "Only time", "Nothing"], 0),
                            ("Current Windows user command?", ["whoami", "pwd", "ls", "touch"], 0),
                            ("tasklist identifies:", ["Running processes", "DNS records", "Firewall policies", "Passwords"], 0),
                            ("Why inspect a parent process?", ["It can show how the process was launched", "It changes IP", "It encrypts logs", "It deletes files"], 0),
                            ("netstat can show:", ["Network connections", "User groups only", "File permissions", "CPU temperature"], 0),
                            ("Failed login followed by success is:", ["Worth investigating in context", "Always harmless", "Always malware", "Never useful"], 0),
                            ("Endpoint telemetry is:", ["Security-relevant data from endpoints", "A password", "A cable", "A backup disk"], 0),
                            ("SOC commands should be run:", ["With authorization", "On random systems", "Without permission", "Only against public servers"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Linux Security Monitoring and Log Analysis",
                5,
                "Analyze Linux authentication, processes, services, sockets, permissions and logs.",
                [
                    self.text(
                        "Linux Logs and Authentication",
                        1,
                        """<h1>Linux Security Monitoring</h1>
<p>Linux servers are important sources of security telemetry.</p>
<h2>Investigation Sources</h2>
<ul><li>Authentication and SSH logs</li><li>System logs</li><li>Service logs</li>
<li>Web server logs</li><li>Application logs</li><li>systemd journal</li></ul>
<h2>SSH Investigation</h2>
<p>Identify source address, account, authentication result and timestamp.
Then examine successful access and post-authentication activity.</p>
<p>Multiple failures followed by successful authentication and suspicious
activity provide stronger evidence than one failed attempt.</p>""",
                        35,
                    ),
                    self.text(
                        "Processes, Services and Permissions",
                        2,
                        """<h1>Linux Endpoint Triage</h1>
<ul><li>Processes and process relationships</li><li>Listening sockets</li>
<li>Running services</li><li>Users and groups</li><li>File permissions</li>
<li>Scheduled tasks and persistence</li></ul>
<h2>Analyst Questions</h2>
<ul><li>What is the process?</li><li>Who started it?</li>
<li>What executable is used?</li><li>What files are accessed?</li>
<li>What network destinations are contacted?</li><li>Is the service expected?</li></ul>""",
                        35,
                    ),
                    self.code(
                        "Practice: Linux Triage Commands",
                        3,
                        """whoami
hostname
ip addr
ip route
ss -tulpn
ps aux
systemctl --type=service --state=running
journalctl -n 50
ls -la
stat /path/to/file

# Exercise: Explain what evidence each command can provide.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 5 Quiz",
                        [
                            ("Common Linux remote access service?", ["SSH", "Paint", "Excel", "Bluetooth only"], 0),
                            ("Command for running processes?", ["ps aux", "mkdir", "echo", "date"], 0),
                            ("ss helps investigate:", ["Network sockets", "Passwords", "Documents", "Screen resolution"], 0),
                            ("journalctl accesses:", ["systemd journal logs", "DNS only", "Browser history only", "BIOS"], 0),
                            ("Failed SSH logins may indicate:", ["Password guessing or unauthorized attempts", "Guaranteed compromise", "Nothing", "Deleted accounts"], 0),
                            ("After suspicious successful login, examine:", ["Post-authentication activity", "Wallpaper", "Keyboard layout", "Nothing"], 0),
                            ("Why examine permissions?", ["To identify unusual access/configuration", "Change IP", "Encrypt traffic", "Update DNS"], 0),
                            ("Listening sockets can identify:", ["Services accepting network connections", "User salaries", "Disk capacity", "Printer ink"], 0),
                            ("Linux investigation should be:", ["Authorized", "Random", "Without permission", "Only public IPs"], 0),
                            ("Stronger evidence comes from:", ["Corroborating events and context", "A scary IP", "Username alone", "Assumptions"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "SIEM Fundamentals and Security Event Correlation",
                6,
                "Understand SIEM architecture, log collection, normalization, enrichment, correlation and alerting.",
                [
                    self.text(
                        "What Is a SIEM?",
                        1,
                        """<h1>Security Information and Event Management</h1>
<p>A SIEM centralizes security telemetry and provides searching, correlation,
dashboards, alerting and investigation capabilities.</p>
<h2>Common Sources</h2>
<ul><li>Firewalls and routers</li><li>Windows and Linux</li>
<li>Identity systems</li><li>EDR</li><li>DNS and proxy systems</li>
<li>Applications</li><li>Cloud platforms</li></ul>
<h2>Pipeline</h2>
<ol><li>Collection</li><li>Parsing/normalization</li><li>Enrichment</li>
<li>Storage/indexing</li><li>Search/correlation</li><li>Alerting</li></ol>""",
                        40,
                    ),
                    self.text(
                        "Correlation and Detection Rules",
                        2,
                        """<h1>Event Correlation</h1>
<p>Correlation connects individual events into a pattern more meaningful than
one event alone.</p>
<h2>Example</h2>
<ol><li>Many authentication failures.</li><li>Successful login from same source.</li>
<li>Privileged action.</li><li>Remote connection to another server.</li></ol>
<p>The sequence deserves investigation.</p>
<h2>Good Detection Rules</h2>
<ul><li>Clear security objective</li><li>Useful thresholds</li><li>Relevant context</li>
<li>Controlled false positives</li><li>Testing and documentation</li></ul>""",
                        40,
                    ),
                    self.code(
                        "Practice: Simple Correlation Logic",
                        3,
                        """events = [
    {"type": "login_failed", "user": "alice", "source": "203.0.113.50"},
    {"type": "login_failed", "user": "alice", "source": "203.0.113.50"},
    {"type": "login_failed", "user": "alice", "source": "203.0.113.50"},
    {"type": "login_success", "user": "alice", "source": "203.0.113.50"},
]

failures = [e for e in events if e["type"] == "login_failed"]
successes = [e for e in events if e["type"] == "login_success"]

if len(failures) >= 3 and successes:
    print("Potential credential attack pattern - investigate.")
else:
    print("No matching pattern in this sample.")

# Exercise: Add timestamps and a time-window condition.
""",
                        35,
                    ),
                    self._quiz(
                        "Lesson 6 Quiz",
                        [
                            ("SIEM is primarily used for:", ["Centralized security telemetry and analysis", "Email only", "Backups only", "Graphic design"], 0),
                            ("Why normalize logs?", ["Consistent analysis", "Delete evidence", "Encrypt disks", "Change passwords"], 0),
                            ("Correlation does what?", ["Connects related events", "Deletes alerts", "Blocks all traffic", "Creates users"], 0),
                            ("A SIEM alert is:", ["A signal requiring investigation", "Always proof of compromise", "Always false", "A firewall policy"], 0),
                            ("Common SIEM source?", ["Firewall logs", "Wallpaper", "Keyboard", "Mouse pad"], 0),
                            ("False positive means:", ["An alert that is not actually malicious", "Confirmed breach", "Deleted log", "Blocked port"], 0),
                            ("Good detection rules have:", ["A clear security objective", "Alerts on everything", "No context", "No testing"], 0),
                            ("Why enrich SIEM data?", ["Add useful context", "Remove evidence", "Disable monitoring", "Hide alerts"], 0),
                            ("After an alert, analyst should:", ["Investigate evidence and context", "Declare breach immediately", "Delete it", "Ignore it"], 0),
                            ("Correlation is valuable because:", ["Sequences reveal broader patterns", "It removes logs", "Prevents every attack", "Replaces analysts"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Incident Detection, Triage and Alert Investigation",
                7,
                "Develop a repeatable method for investigating alerts and deciding when to escalate.",
                [
                    self.text(
                        "The Alert Triage Process",
                        1,
                        """<h1>Alert Triage</h1>
<ol><li>Validate the alert.</li><li>Identify user, host, IP and application.</li>
<li>Contextualize asset and user behavior.</li><li>Enrich with approved sources.</li>
<li>Correlate related events.</li><li>Classify benign, suspicious or malicious.</li>
<li>Escalate according to procedure.</li></ol>
<h2>Think in Questions</h2>
<p>What happened? When? Who? Which host? Is it normal? What evidence supports
the assessment? What systems may be affected? What is the next action?</p>""",
                        40,
                    ),
                    self.text(
                        "Severity, Priority and Evidence",
                        2,
                        """<h1>Severity and Priority</h1>
<p>Severity describes potential security impact. Priority also considers business
context, asset criticality and urgency.</p>
<p>A suspicious login against a test workstation may be less urgent than the same
behavior against a privileged account or critical server.</p>
<h2>Document</h2>
<ul><li>Timestamps</li><li>Hosts</li><li>Usernames</li><li>Source/destination</li>
<li>Processes</li><li>Relevant logs</li><li>Indicators</li><li>Analyst reasoning</li></ul>
<p>Write facts first, interpretations second, and clearly state uncertainty.</p>""",
                        35,
                    ),
                    self.assignment(
                        "Practical Alert Triage Exercise",
                        3,
                        """<h3>Scenario</h3>
<p>An employee account generates 18 failed authentication attempts from an unfamiliar
workstation within 10 minutes. A successful authentication occurs two minutes later.
The account then accesses a server it normally does not use.</p>
<h3>Your Tasks</h3>
<ol><li>Set an initial severity and explain why.</li>
<li>List at least 10 pieces of evidence to collect.</li>
<li>Identify systems and accounts to investigate.</li>
<li>Explain how you would determine whether the behavior is legitimate.</li>
<li>State escalation conditions.</li><li>Write a concise SOC case note.</li></ol>
<h3>Scoring</h3><ul><li>Triage: 20</li><li>Evidence: 25</li>
<li>Correlation: 20</li><li>Escalation: 20</li><li>Documentation: 15</li></ul>""",
                        100,
                        45,
                    ),
                    self._quiz(
                        "Lesson 7 Quiz",
                        [
                            ("Purpose of triage?", ["Determine relevance, severity and next action", "Delete alerts", "Replace SIEM", "Disable logs"], 0),
                            ("Identify early:", ["Affected users, hosts and systems", "Only alert color", "Only IP", "Nothing"], 0),
                            ("Why asset criticality?", ["It affects impact and priority", "Changes passwords", "Removes logs", "Replaces evidence"], 0),
                            ("Enrichment means:", ["Adding useful investigation context", "Deleting events", "Blocking all traffic", "Formatting disk"], 0),
                            ("Analyst notes should distinguish:", ["Facts from hypotheses", "Blue from green", "Servers from laptops", "Nothing"], 0),
                            ("Escalate:", ["Based on evidence and procedures", "Randomly", "Never", "Only after a week"], 0),
                            ("Correlate to:", ["Establish a broader timeline", "Hide activity", "Reduce evidence", "Remove alerts"], 0),
                            ("Useful evidence includes:", ["Timestamp and affected host", "Guess", "Rumor", "Unrelated screenshot"], 0),
                            ("Priority considers:", ["Evidence and business context", "Only color", "Only username", "Only IP"], 0),
                            ("Professional case notes are:", ["Clear, factual and reproducible", "Emotional", "Vague", "Unsupported"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Threat Intelligence and IOC Analysis",
                8,
                "Understand threat intelligence, indicators of compromise and responsible enrichment.",
                [
                    self.text(
                        "Threat Intelligence Fundamentals",
                        1,
                        """<h1>Threat Intelligence</h1>
<p>Threat intelligence provides context that helps defenders make better decisions.</p>
<h2>Types</h2><ul><li><strong>Strategic:</strong> Business-level trends.</li>
<li><strong>Operational:</strong> Campaign and adversary activity.</li>
<li><strong>Tactical:</strong> Techniques and behaviors.</li>
<li><strong>Technical:</strong> Domains, IPs, URLs and hashes.</li></ul>""",
                        35,
                    ),
                    self.text(
                        "Indicators of Compromise and Enrichment",
                        2,
                        """<h1>IOCs</h1>
<p>Indicators of compromise are observable pieces of information that may be associated
with malicious activity.</p>
<ul><li>File hashes</li><li>IP addresses</li><li>Domains</li><li>URLs</li>
<li>Email addresses</li><li>File paths and names</li></ul>
<p>An IOC is not automatically malicious. Validate it using internal telemetry,
context and trustworthy intelligence.</p>
<h2>IOC Workflow</h2>
<ol><li>Observe</li><li>Validate</li><li>Enrich</li><li>Search internally</li>
<li>Assess confidence</li><li>Respond when appropriate</li></ol>""",
                        35,
                    ),
                    self.code(
                        "Practice: IOC Enrichment Workflow",
                        3,
                        """iocs = {
    "ip": "203.0.113.10",
    "domain": "example.invalid",
    "sha256": "placeholder-hash",
}

for indicator_type, value in iocs.items():
    print(indicator_type, value)
    print("Validate -> Enrich -> Search internal telemetry -> Assess -> Document")
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 8 Quiz",
                        [
                            ("What is an IOC?", ["An observable indicator potentially associated with compromise", "A firewall", "A password", "A backup"], 0),
                            ("Technical IOC?", ["File hash", "Business strategy", "Office layout", "Job title"], 0),
                            ("Does an IOC prove malicious activity?", ["Yes", "No", "Only IPs", "Only hashes"], 1),
                            ("Strategic intelligence is:", ["High-level threat/business information", "Only hashes", "Only URLs", "Only malware"], 0),
                            ("Why enrich an IOC?", ["Understand relevance", "Delete it", "Make it malicious", "Hide it"], 0),
                            ("Indicator found internally should be:", ["Searched against related telemetry", "Immediately ignored", "Deleted", "Made public"], 0),
                            ("A file hash identifies:", ["A specific file object", "User salary", "Cable", "VLAN"], 0),
                            ("Threat intelligence should be:", ["Evaluated for relevance and confidence", "Accepted blindly", "Ignored", "Always proof"], 0),
                            ("Intelligence about adversary techniques is:", ["Tactical", "Financial", "Graphic", "Administrative"], 0),
                            ("Why document confidence?", ["Communicate reliability of assessment", "Delete evidence", "Hide uncertainty", "No purpose"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Endpoint Detection and Response (EDR)",
                9,
                "Learn endpoint telemetry, process trees, persistence and EDR investigation workflows.",
                [
                    self.text(
                        "EDR Fundamentals",
                        1,
                        """<h1>Endpoint Detection and Response</h1>
<p>EDR platforms collect endpoint telemetry and provide detection, investigation
and response capabilities.</p>
<ul><li>Process creation</li><li>Parent-child relationships</li>
<li>Command-line data</li><li>File activity</li><li>Network connections</li>
<li>Configuration changes</li><li>User activity</li></ul>
<h2>Process Trees</h2>
<p>Process trees help analysts understand how activity started and what it spawned.
An unusual relationship is a clue, not automatically proof of malicious activity.</p>""",
                        35,
                    ),
                    self.text(
                        "Endpoint Investigation Workflow",
                        2,
                        """<h1>Investigating an Endpoint Alert</h1>
<ol><li>Identify endpoint and user.</li><li>Review triggering process.</li>
<li>Inspect parent and child processes.</li><li>Review command line and files.</li>
<li>Review network connections.</li><li>Search for persistence.</li>
<li>Search for similar activity elsewhere.</li><li>Determine containment needs.</li></ol>
<p>Containment can protect the organization but may disrupt business operations.
Follow documented procedures and consider system criticality.</p>""",
                        35,
                    ),
                    self.code(
                        "Practice: Endpoint Timeline",
                        3,
                        """events = [
    ("09:10:02", "user login"),
    ("09:12:15", "browser started"),
    ("09:13:01", "script interpreter launched"),
    ("09:13:04", "new outbound connection"),
    ("09:13:12", "file created"),
]

for timestamp, event in events:
    print(timestamp, "|", event)

# Exercise: Identify the event requiring the most investigation
# and list endpoint telemetry you would request.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 9 Quiz",
                        [
                            ("EDR provides:", ["Endpoint telemetry, detection and response", "Email hosting", "Payroll", "Database only"], 0),
                            ("Process trees show:", ["Process relationships", "Disk encryption", "IP changes", "User salaries"], 0),
                            ("After suspicious process, examine:", ["Parent, child, command line and related activity", "Only name", "Nothing", "Wallpaper"], 0),
                            ("Endpoint containment means:", ["Limiting endpoint communication/activity", "Deleting endpoint", "Formatting every server", "Changing every password"], 0),
                            ("Why consider business impact before isolation?", ["Isolation can disrupt services", "Isolation never works", "It deletes logs", "It changes DNS"], 0),
                            ("Endpoint network telemetry can reveal:", ["Connections made by a process or host", "Salary", "Keyboard brand", "Monitor size"], 0),
                            ("Unusual process automatically means malware?", ["No, validate context", "Yes", "Always", "Only servers"], 0),
                            ("Persistence means:", ["Maintaining access across restarts/sessions", "A backup", "A firewall", "Password reset"], 0),
                            ("Search other endpoints to:", ["Determine whether activity is widespread", "Delete evidence", "Slow investigation", "Avoid investigation"], 0),
                            ("EDR investigation should be:", ["Evidence-driven and procedure-based", "Random", "Name-based only", "Undocumented"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Incident Response and Digital Investigation",
                10,
                "Learn preparation, detection, containment, eradication, recovery and lessons learned.",
                [
                    self.text(
                        "Incident Response Lifecycle",
                        1,
                        """<h1>Incident Response</h1>
<ol><li><strong>Preparation:</strong> Policies, tools, contacts and procedures.</li>
<li><strong>Detection and Analysis:</strong> Identify and understand the incident.</li>
<li><strong>Containment:</strong> Limit spread and impact.</li>
<li><strong>Eradication:</strong> Remove root cause and malicious artifacts.</li>
<li><strong>Recovery:</strong> Restore trusted operation.</li>
<li><strong>Lessons Learned:</strong> Improve controls and procedures.</li></ol>
<p>Good response is controlled, documented and evidence-driven.</p>""",
                        40,
                    ),
                    self.text(
                        "Evidence, Timelines and Incident Reports",
                        2,
                        """<h1>Digital Investigation Basics</h1>
<p>Investigations reconstruct a timeline using multiple sources.</p>
<h2>Report Structure</h2>
<ol><li>Executive summary</li><li>Detection source</li><li>Timeline</li>
<li>Affected assets</li><li>Indicators and evidence</li><li>Impact assessment</li>
<li>Containment/remediation</li><li>Lessons learned</li><li>Recommendations</li></ol>
<p>Clearly separate confirmed facts from hypotheses and unknown information.</p>""",
                        40,
                    ),
                    self.assignment(
                        "Incident Response Report",
                        3,
                        """<h3>Scenario</h3>
<p>A workstation triggers an EDR alert after a suspicious document is opened.
The endpoint contacts an unfamiliar external address and creates a new executable.
The same user's account later authenticates to another workstation.</p>
<h3>Write a Professional Report</h3>
<ol><li>Executive summary</li><li>Initial assessment</li><li>Timeline</li>
<li>Affected users/systems</li><li>Supporting evidence</li><li>Containment</li>
<li>Eradication and recovery</li><li>Additional evidence required</li>
<li>Lessons learned and detection improvements</li></ol>
<h3>Scoring</h3><ul><li>Technical analysis: 30</li><li>Timeline: 20</li>
<li>Response plan: 25</li><li>Evidence: 15</li><li>Professional writing: 10</li></ul>""",
                        100,
                        60,
                    ),
                    self._quiz(
                        "Lesson 10 Quiz",
                        [
                            ("Containment means:", ["Limiting incident spread or impact", "Deleting logs", "Writing policy only", "Replacing every computer"], 0),
                            ("After eradication comes:", ["Recovery", "Initial detection", "Preparation", "Email delivery"], 0),
                            ("Why build a timeline?", ["Understand sequence of events", "Hide evidence", "Delete alerts", "Replace logs"], 0),
                            ("Eradication means:", ["Removing root cause and malicious artifacts", "Creating alert", "Writing email", "Changing wallpaper"], 0),
                            ("Why preserve evidence?", ["It supports investigation and accountability", "It is never useful", "It replaces containment", "It deletes incidents"], 0),
                            ("Recovery means:", ["Returning systems to trusted operation", "Deleting backups", "Ignoring users", "Closing SOC"], 0),
                            ("Incident report should include:", ["Timeline and evidence", "Only title", "Only IP", "Only screenshot"], 0),
                            ("Lessons learned should:", ["Improve controls and processes", "Blame users", "Delete alerts", "Be ignored"], 0),
                            ("Containment decisions consider:", ["Impact, evidence and business context", "Only alert color", "Nothing", "User preference only"], 0),
                            ("Incident response should be:", ["Structured and documented", "Random", "Undocumented", "Assumption-based"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Security Monitoring, Detection Engineering and Threat Hunting",
                11,
                "Design useful detections, manage false positives and perform hypothesis-driven hunts.",
                [
                    self.text(
                        "Detection Engineering",
                        1,
                        """<h1>Detection Engineering</h1>
<p>Detection engineering turns security requirements and threat knowledge into
repeatable analytic rules.</p>
<ol><li>Define the threat behavior.</li><li>Identify telemetry.</li>
<li>Define analytic logic.</li><li>Test benign and suspicious examples.</li>
<li>Measure false positives.</li><li>Document assumptions.</li><li>Deploy and monitor.</li></ol>
<p>Good detections have a clear security objective and useful context.</p>""",
                        40,
                    ),
                    self.text(
                        "Threat Hunting",
                        2,
                        """<h1>Threat Hunting</h1>
<p>Threat hunting proactively searches for suspicious activity that may not have
generated an existing alert.</p>
<h2>Method</h2>
<ol><li>Create a hypothesis.</li><li>Identify required telemetry.</li>
<li>Search relevant patterns.</li><li>Investigate anomalies.</li>
<li>Validate findings.</li><li>Improve detections where appropriate.</li></ol>
<p>Example hypothesis: a compromised account may be used from a new workstation
before lateral movement.</p>""",
                        40,
                    ),
                    self.code(
                        "Practice: Detection Logic",
                        3,
                        """events = [
    {"user": "alice", "host": "WS-01", "success": True},
    {"user": "alice", "host": "WS-01", "success": True},
    {"user": "alice", "host": "WS-99", "success": True},
]

known_hosts = {"alice": {"WS-01"}}

for event in events:
    if event["success"] and event["host"] not in known_hosts.get(event["user"], set()):
        print("Potential unusual authentication:", event)

# Exercise: Add timestamps, asset criticality and a time window.
""",
                        35,
                    ),
                    self._quiz(
                        "Lesson 11 Quiz",
                        [
                            ("Detection engineering is:", ["Designing and maintaining security detections", "Replacing computers", "Writing websites", "Payroll"], 0),
                            ("A detection should begin with:", ["A clear security objective", "Random fields", "A color", "Username only"], 0),
                            ("Why test detections?", ["Measure accuracy and false positives", "Delete logs", "Disable monitoring", "Avoid documentation"], 0),
                            ("Threat hunting is:", ["Proactive searching for suspicious activity", "Installing antivirus", "Backup", "Changing passwords"], 0),
                            ("A hunting hypothesis is:", ["A testable idea about possible behavior", "Confirmed incident", "Password", "Firewall rule"], 0),
                            ("Why measure false positives?", ["Improve detection quality", "Hide attacks", "Remove telemetry", "Disable alerts"], 0),
                            ("A hunt can discover:", ["Activity missed by existing detections", "Only failed logins", "Only malware", "Nothing"], 0),
                            ("After a successful hunt:", ["Validate findings and improve detections", "Delete evidence", "Ignore it", "Stop logging"], 0),
                            ("Good detections use:", ["Relevant telemetry and context", "Only usernames", "Only IPs", "No testing"], 0),
                            ("Threat hunting is:", ["Hypothesis-driven investigation", "Random searching", "Password cracking", "Administration only"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Vulnerability Management and Risk in Security Operations",
                12,
                "Understand vulnerabilities, CVEs, prioritization, remediation and SOC risk context.",
                [
                    self.text(
                        "Vulnerability Management Fundamentals",
                        1,
                        """<h1>Vulnerability Management</h1>
<p>Vulnerability management identifies weaknesses and helps organizations prioritize
remediation.</p>
<h2>Lifecycle</h2><ol><li>Asset discovery</li><li>Vulnerability identification</li>
<li>Validation</li><li>Risk prioritization</li><li>Remediation</li><li>Verification</li>
<li>Continuous monitoring</li></ol>
<ul><li><strong>CVE:</strong> Identifier for a publicly known vulnerability.</li>
<li><strong>CVSS:</strong> Framework for communicating vulnerability severity.</li>
<li><strong>Exploitability:</strong> How feasible exploitation may be.</li>
<li><strong>Asset criticality:</strong> Importance of the affected asset.</li></ul>""",
                        35,
                    ),
                    self.text(
                        "Risk-Based Prioritization",
                        2,
                        """<h1>Prioritizing Vulnerabilities</h1>
<p>Organizations must prioritize because remediation resources are limited.</p>
<ul><li>Severity</li><li>Exploit availability/active exploitation</li>
<li>Internet exposure</li><li>Asset criticality</li><li>Business impact</li>
<li>Compensating controls</li><li>Patch availability</li></ul>
<p>A medium vulnerability on a highly exposed critical system can deserve attention
before a higher-scoring vulnerability on an isolated test system.</p>
<p>SOC teams can correlate vulnerability information with observed attack activity
to improve investigation priority.</p>""",
                        35,
                    ),
                    self.assignment(
                        "Vulnerability Prioritization Exercise",
                        3,
                        """<h3>Rank These Assets</h3>
<ol><li>Internet-facing web server: high-severity vulnerability, public exploit available.</li>
<li>Internal test laptop: critical vulnerability, isolated from production.</li>
<li>Domain controller: medium-severity vulnerability, no known exploit, critical asset.</li>
<li>Public VPN gateway: high-severity vulnerability with reports of active exploitation.</li></ol>
<p>Rank them from highest to lowest priority. Explain your reasoning using severity,
exposure, exploitability, asset criticality and business impact.</p>
<p>Deliver a one-page professional vulnerability prioritization report.</p>""",
                        100,
                        40,
                    ),
                    self._quiz(
                        "Lesson 12 Quiz",
                        [
                            ("CVE is:", ["An identifier for a publicly known vulnerability", "An antivirus", "A firewall", "A password"], 0),
                            ("CVSS communicates:", ["Vulnerability severity", "User identity", "Network speed", "Disk size"], 0),
                            ("Why prioritize vulnerabilities?", ["Resources and time are limited", "All are harmless", "Patching is unnecessary", "SOC never patches"], 0),
                            ("What can increase priority?", ["Internet exposure and active exploitation", "Pretty hostname", "Unused hardware", "Screen size"], 0),
                            ("Why asset criticality?", ["Impact differs between systems", "Changes CVE", "Removes risk", "Replaces patching"], 0),
                            ("Remediation means:", ["Fixing or reducing the vulnerability", "Creating a vulnerability", "Deleting logs", "Writing report only"], 0),
                            ("After remediation:", ["Verify the fix", "Ignore asset", "Delete scanner", "Stop monitoring"], 0),
                            ("Why correlate vulnerability and SOC data?", ["Understand whether vulnerable systems are targeted", "Hide vulnerabilities", "Replace SIEM", "Avoid evidence"], 0),
                            ("Risk-based prioritization considers:", ["Severity, exposure, exploitability and business impact", "Severity only", "Hostname", "Username"], 0),
                            ("An actively exploited public VPN vulnerability may outrank an isolated critical test-laptop vulnerability.", ["True", "False", "Only weekends", "Cannot assess"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Professional SOC Tools and Investigation Workflows",
                13,
                "Combine SIEM, EDR, firewall, ticketing, threat intelligence and network telemetry in investigations.",
                [
                    self.text(
                        "The SOC Toolset",
                        1,
                        """<h1>SOC Tool Categories</h1>
<ul><li><strong>SIEM:</strong> Centralized log search and correlation.</li>
<li><strong>EDR:</strong> Endpoint telemetry and response.</li>
<li><strong>Firewall:</strong> Network traffic control and logging.</li>
<li><strong>IDS/IPS:</strong> Network detection/prevention.</li>
<li><strong>Threat Intelligence:</strong> Indicator and adversary context.</li>
<li><strong>Case Management:</strong> Investigation workflow and documentation.</li>
<li><strong>Vulnerability Scanner:</strong> Weakness discovery.</li>
<li><strong>Network Analysis:</strong> Traffic investigation.</li></ul>""",
                        35,
                    ),
                    self.text(
                        "End-to-End Investigation Workflow",
                        2,
                        """<h1>Example: Phishing Investigation</h1>
<ol><li><strong>Email:</strong> Sender, recipient, attachment and URL.</li>
<li><strong>Identity:</strong> Authentication behavior after interaction.</li>
<li><strong>Endpoint:</strong> Process and file activity.</li>
<li><strong>Network:</strong> DNS and outbound connections.</li>
<li><strong>SIEM:</strong> Search for related indicators across the environment.</li>
<li><strong>Response:</strong> Follow containment/escalation procedures.</li>
<li><strong>Documentation:</strong> Record facts, evidence, uncertainty and actions.</li></ol>""",
                        40,
                    ),
                    self.code(
                        "Practice: SOC Case Timeline",
                        3,
                        """case_events = [
    {"time": "08:45", "source": "Email", "event": "Suspicious email delivered"},
    {"time": "08:52", "source": "Endpoint", "event": "Attachment opened"},
    {"time": "08:53", "source": "EDR", "event": "Unusual child process"},
    {"time": "08:54", "source": "DNS", "event": "New domain queried"},
    {"time": "08:55", "source": "Firewall", "event": "Outbound connection"},
    {"time": "09:00", "source": "SIEM", "event": "Correlation alert"},
]

for event in case_events:
    print(event["time"], "|", event["source"], "|", event["event"])

# Exercise: Add Evidence, Assessment and Next Action fields.
""",
                        30,
                    ),
                    self._quiz(
                        "Lesson 13 Quiz",
                        [
                            ("Which tool centralizes logs?", ["SIEM", "Calculator", "Printer", "Text editor"], 0),
                            ("Which focuses on endpoint telemetry?", ["EDR", "DNS", "Spreadsheet", "Switch"], 0),
                            ("Why correlate multiple tools?", ["Build a fuller investigation picture", "Delete alerts", "Replace analysts", "Disable logs"], 0),
                            ("A SOC case should contain:", ["Evidence, analysis and actions", "Only title", "Only IP", "Only emoji"], 0),
                            ("Why review email and endpoint data together?", ["Connect user action with endpoint behavior", "They are unrelated", "Delete email", "Replace EDR"], 0),
                            ("Firewall logs provide:", ["Network connection evidence", "Passwords", "File contents always", "CPU temperature"], 0),
                            ("Case management is for:", ["Tracking investigation workflow", "Encrypting disks", "Creating malware", "Replacing SIEM"], 0),
                            ("A timeline should be:", ["Chronological and evidence-based", "Random", "Emotional", "Unsupported"], 0),
                            ("Why record uncertainty?", ["Distinguish facts from hypotheses", "Weaken reports", "Hide evidence", "No reason"], 0),
                            ("Professional investigations combine:", ["Tools, evidence, context and reasoning", "One alert only", "IP addresses only", "Guesswork"], 0),
                        ],
                        70,
                    ),
                ],
            ),

            self.make_lesson(
                "Capstone Project: Complete SOC Incident Investigation",
                14,
                "Apply the complete SOC workflow to investigate a realistic multi-stage security incident.",
                [
                    self.text(
                        "Capstone Scenario",
                        1,
                        """<h1>Capstone: Multi-Stage SOC Investigation</h1>
<p>You are a SOC Analyst. A SIEM alert involves a finance employee account.</p>
<h2>Available Evidence</h2>
<ul><li>Suspicious email delivered.</li><li>User opened attachment.</li>
<li>EDR reported unusual process activity.</li><li>Workstation queried a new domain.</li>
<li>Firewall recorded an outbound connection.</li>
<li>User later authenticated to an internal server.</li>
<li>A new archive file was created.</li></ul>
<h2>Mission</h2>
<p>Determine whether the events represent a coordinated incident. Do not assume
every event is malicious; build the conclusion from evidence.</p>
<h2>Questions</h2>
<ol><li>What happened first?</li><li>Which user and endpoint were involved?</li>
<li>What evidence connects the events?</li><li>What logs are still needed?</li>
<li>Which assets may be affected?</li><li>What containment is recommended?</li>
<li>What evidence should be preserved?</li><li>Which detections should improve?</li></ol>""",
                        45,
                    ),
                    self.assignment(
                        "Final SOC Analyst Assessment",
                        2,
                        """<h1>Final SOC Analyst Assessment</h1>
<h2>Required Report</h2>
<ol><li><strong>Executive Summary</strong></li>
<li><strong>Detection</strong></li><li><strong>Timeline</strong></li>
<li><strong>Affected Assets</strong></li><li><strong>Evidence</strong></li>
<li><strong>Threat Assessment</strong></li><li><strong>MITRE ATT&CK Mapping</strong></li>
<li><strong>Containment</strong></li><li><strong>Eradication</strong></li>
<li><strong>Recovery</strong></li><li><strong>Detection Improvements</strong></li>
<li><strong>Lessons Learned</strong></li></ol>
<h2>Rubric - 100 Points</h2>
<ul><li>Triage: 15</li><li>Timeline: 15</li><li>Evidence: 20</li>
<li>Threat/ATT&CK analysis: 15</li><li>Response recommendations: 15</li>
<li>Detection improvements: 10</li><li>Professional documentation: 10</li></ul>
<p><strong>Professional standard:</strong> Clearly distinguish confirmed facts,
reasonable conclusions and unknown information. Never claim evidence that was not provided.</p>""",
                        100,
                        90,
                    ),
                    self._quiz(
                        "Final SOC Analyst Knowledge Assessment",
                        [
                            ("First priority after receiving an alert?", ["Understand and triage it", "Delete it", "Ignore it", "Format host"], 0),
                            ("Tool that centralizes logs?", ["SIEM", "Word processor", "Printer", "Spreadsheet"], 0),
                            ("Tool for endpoint telemetry?", ["EDR", "DHCP", "DNS only", "Switch"], 0),
                            ("Incident conclusion should be supported by:", ["Evidence", "Guesswork", "Rumors", "Severity alone"], 0),
                            ("Containment is intended to:", ["Limit spread or impact", "Delete evidence", "Close case", "Disable every system"], 0),
                            ("Threat intelligence provides:", ["Relevant threat context", "Proof every IOC is malicious", "Replacement for logs", "Replacement for analysts"], 0),
                            ("Why use MITRE ATT&CK?", ["Describe adversary behavior consistently", "Create passwords", "Patch automatically", "Replace SIEM"], 0),
                            ("Threat hunting is:", ["Proactive hypothesis-driven searching", "Random Internet scanning", "Password guessing", "Deleting alerts"], 0),
                            ("Vulnerability prioritization considers:", ["Severity, exposure, exploitability and business impact", "Severity only", "Hostname", "Username"], 0),
                            ("A professional report distinguishes:", ["Facts, conclusions and unknowns", "Passwords and facts", "Screenshots only", "Nothing"], 0),
                            ("After an incident, teams should perform:", ["Lessons learned and security improvement", "Delete evidence", "Stop monitoring", "Ignore root cause"], 0),
                            ("Investigation findings can improve:", ["Security detections", "Only wallpapers", "Payroll", "Printer settings"], 0),
                        ],
                        80,
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

            # Make the command repeatable: replace old content for an existing lesson.
            if not created:
                LessonContent.objects.filter(lesson=lesson).delete()

            for content in contents:
                content = content.copy()
                quiz_data = content.pop("quiz_data", None)

                LessonContent.objects.create(
                    lesson=lesson,
                    quiz_data=quiz_data,
                    **content,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Lesson {lesson.order}: {lesson.title}"
                )
            )

    def _quiz(self, title, questions, passing_score=70):
        return {
            "content_type": "quiz",
            "title": title,
            "order": 99,
            "duration_minutes": 20,
            "quiz_data": self.quiz([
                self.q(question, options, correct)
                for question, options, correct in questions
            ]),
            "passing_score": passing_score,
        }
