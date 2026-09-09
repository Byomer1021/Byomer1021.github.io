"""The CV, in one place.

Both the two-page and the one-page PDF are rendered from this, so a fact fixed
here is fixed in both. `short` is the compressed line used on the one-pager;
where it is absent the full text is reused.

Every number here is measured and appears in the repository it belongs to.
"""

CONTACT = {
    "name": "Ömer Can Atlı",
    "title": "Computer Engineer  |  Software Developer  |  AI & Backend",
    "site": "omercanatli.com",
    "email": "atli.omercan_2001@hotmail.com",
    "phone": "+90 536 426 1897",
    "location": "Maltepe, İstanbul, Türkiye",
    "github": "github.com/Byomer1021",
    "linkedin": "linkedin.com/in/ömer-can-atlı",
    "linkedin_url": "https://www.linkedin.com/in/%C3%B6mer-can-atli-8a9b491b5/",
}

SUMMARY = (
    "Final-year Computer Engineering student at Gebze Technical University with a deep "
    "interest in backend systems and artificial intelligence. I build across the stack — "
    ".NET and Node.js backends, React Native and Flutter clients, and applied "
    "computer-vision and graph pipelines in Python. Creator and lead developer of two "
    "shipped products, and four open-source projects published with the measurements "
    "that say where each one breaks."
)

SUMMARY_SHORT = (
    "Final-year Computer Engineering student at Gebze Technical University. Backend and "
    "AI focused, building across the stack: .NET and Node.js backends, React Native and "
    "Flutter clients, computer-vision and graph pipelines in Python. Creator and lead "
    "developer of two shipped products."
)

EXPERIENCE = [{
    "role": "Intern — Network Management Directorate",
    "org": "Türk Telekom, İstanbul",
    "dates": "July 2025 – August 2025",
    "bullets": [
        "Rotational internship across the Transmission, MPLS-IP, DSL, Mobile Core, "
        "Central Office and TTVPN units.",
        "Hands-on with xDSL/FTTH access technologies, MPLS, BNG, traffic monitoring "
        "and fault analysis on a national backbone network.",
    ],
    "short": [
        "Rotational internship across Transmission, MPLS-IP, DSL, Mobile Core, Central "
        "Office and TTVPN; hands-on with xDSL/FTTH, MPLS, BNG, traffic monitoring and "
        "fault analysis.",
    ],
}]

PRODUCTS = [
    {
        "name": "Shorties",
        "role": "Creator & Lead Developer",
        "link": "shorties.tr",
        "url": "https://shorties.tr",
        "bullets": [
            "An exam-preparation ecosystem that turns a question bank into short vertical "
            "videos with AI: one shared architecture across three separate apps.",
            "Designed and built the .NET backend on a Clean Architecture split "
            "(API / Business / Core / DataAccess), the React Native (Expo) client and the "
            "Python video-generation engine, over MSSQL.",
            "YKS Shorties is live on the App Store and Google Play at version 2, with "
            "subscriptions through RevenueCat; KPSS and ALES are in development on the "
            "same stack.",
        ],
        "stack": "C# · .NET · Clean Architecture · REST API · MSSQL · React Native (Expo) · Python · RevenueCat",
        "short": [
            "Exam-prep ecosystem turning a question bank into AI-generated short videos; "
            "one .NET Clean Architecture backend, React Native client and Python video "
            "engine across three apps. YKS live on both stores at v2 with RevenueCat "
            "subscriptions; KPSS and ALES in development.",
        ],
    },
    {
        "name": "respos",
        "role": "Creator & Lead Developer",
        "link": "resposapp.com",
        "url": "https://resposapp.com",
        "bullets": [
            "A multi-tenant SaaS point-of-sale system for restaurants: one Node.js/Express "
            "backend serves many tenants, each with isolated data and self-service sign-up.",
            "Layered backend (routes → services → repositories) with tenant scoping in the "
            "service layer, JWT authentication and per-restaurant module access.",
            "Live table plan, kitchen display system, recipe-based stock tracking, shift "
            "and cash management, and discount authorisation with an audit log.",
        ],
        "stack": "Node.js · Express · React · React Native (Expo) · JWT · Multi-tenancy",
        "short": [
            "Multi-tenant SaaS POS for restaurants: one Node.js/Express backend serving "
            "many tenants with isolated data, React and Expo clients, JWT auth, live table "
            "plan, kitchen display and recipe-based stock.",
        ],
    },
    {
        "name": "Mobile Fitness Tracker",
        "role": "Team project",
        "link": None,
        "url": None,
        "bullets": [
            "Cross-platform fitness app building personalised meal and workout "
            "recommendations with AI; secure authentication, workout logging and data "
            "analytics.",
        ],
        "stack": "Flutter · .NET · MSSQL",
        "short": [
            "Cross-platform fitness app with AI meal and workout recommendations; Flutter "
            "client, .NET backend, MSSQL.",
        ],
    },
]

OPEN_SOURCE = [
    {
        "name": "otonomarac",
        "url": "https://github.com/Byomer1021/otonomarac",
        "tagline": "Monocular driving perception and bird's-eye-view mapping",
        "bullets": [
            "Detection (YOLO), multi-object tracking (ByteTrack), monocular depth "
            "(Depth Anything V2), drivable-area segmentation, ground-plane homography and "
            "time-to-collision, built end to end over eight weeks.",
            "Deployed as a public Gradio demo on Hugging Face Spaces, running CPU-only on "
            "the free tier.",
        ],
        "stack": "Python · PyTorch · OpenCV · Gradio",
        "demo": "https://huggingface.co/spaces/byomer1021/otonomarac",
        "short": "Single-camera driving perception: detection, tracking, monocular depth, "
                 "segmentation, ground-plane projection and time-to-collision over eight "
                 "weeks. Live public demo on Hugging Face Spaces.",
    },
    {
        "name": "trafikisaret",
        "url": "https://github.com/Byomer1021/trafikisaret",
        "tagline": "Turkish traffic-sign dataset and two-stage recogniser",
        "bullets": [
            "717 bounding boxes labelled by hand over 787 frames of own dashcam footage in "
            "daylight, rain and night.",
            "Class-agnostic detector plus a 14-class crop classifier: 0.953 recall on a "
            "held-out test set; detector mAP50 0.515 overall — 0.608 in daylight, 0.361 in "
            "rain and at night.",
        ],
        "stack": "Python · YOLO · Dataset construction",
        "short": "Turkish traffic-sign dataset labelled from scratch — 717 boxes over 787 "
                 "frames of day, rain and night — with a two-stage detector and classifier: "
                 "0.953 test recall, mAP50 0.515.",
    },
    {
        "name": "smart-city-traffic-analysis",
        "url": "https://github.com/Byomer1021/smart-city-traffic-analysis",
        "tagline": "38.3 million New York taxi trips modelled as a graph",
        "bullets": [
            "PageRank, Louvain communities and a node-removal simulation over 258 zones and "
            "9,990 edges; full pipeline runs in 40.7 s.",
            "Removing the five most critical zones costs 34.1% of network flow; removing "
            "JFK Airport splits the graph from one connected component into sixteen.",
        ],
        "stack": "PySpark · GraphFrames · NetworkX · Pandas",
        "short": "38.3M NYC taxi trips as one graph: PageRank, Louvain communities and a "
                 "node-removal simulation over 258 zones. Removing JFK splits the network "
                 "into sixteen components.",
    },
    {
        "name": "plakatanima",
        "url": "https://github.com/Byomer1021/plakatanima",
        "tagline": "Turkish licence plate recognition — in progress",
        "bullets": [
            "Synthetic data generator calibrated against 690 hand-labelled real plates: the "
            "plan assumed ±35° of plate angle, measurement showed about 7°, so the generator "
            "changed rather than the measurement.",
            "CTC sequence recogniser written; training not yet run, and the project reports "
            "that rather than an estimate.",
        ],
        "stack": "Python · PyTorch · CTC · Synthetic data",
        "short": "Turkish plate recognition: synthetic data generator calibrated against 690 "
                 "hand-labelled plates, CTC recogniser written. Data phase complete, "
                 "training not yet run.",
    },
]

EDUCATION = [
    {"school": "Gebze Technical University", "detail": "B.Sc. Computer Engineering",
     "dates": "Expected 2027", "where": "Kocaeli"},
    {"school": "Şehit Mustafa Serin Science High School", "detail": "Science track",
     "dates": "Graduated 2019", "where": "Balıkesir"},
]

SKILLS = [
    ("Languages", "Java, C++, C, C#, Python, JavaScript, SQL, HTML/CSS"),
    ("Frameworks & Libraries", ".NET, Spring Boot, Django, Flutter, React Native, "
                               "Scikit-learn, TensorFlow (basic), NumPy, Pandas"),
    ("Tools & Platforms", "Git, Docker, Jira, Maven, Firebase, MSSQL, MySQL, SQL Server"),
    ("Core Concepts", "Object-Oriented Programming, Data Structures, Machine Learning, "
                      "Deep Learning"),
]

LANGUAGES = "Turkish — native  ·  English — Advanced (C1)"

VOLUNTEER = [
    'C developer, "Besleme Kahramanları"',
    "Member, GTÜ Bilgisayar Topluluğu",
    "AFAD disaster response volunteer",
    "Member, GTU Search and Rescue Club (GETAK)",
]

# One line on the one-pager; the full version keeps the formal wording.
VOLUNTEER_SHORT = [
    'C developer, "Besleme Kahramanları"',
    "GTÜ Bilgisayar Topluluğu",
    "AFAD disaster response volunteer",
    "GETAK Search and Rescue Club",
]
