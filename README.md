Back2You

AI-Powered Campus Lost & Found Intelligence Platform

Helping lost belongings find their way Back2You.

Back2You is a campus-focused Lost & Found platform that combines Computer Vision, Natural Language Processing, similarity matching, location/time signals, and claim verification to help students reconnect lost belongings with their owners.

Instead of relying only on manual searching, Back2You analyzes lost and found reports and ranks potential matches using multiple signals.

---

Features

🔎 AI-Powered Lost & Found Matching

- Report lost or found belongings
- Analyze item descriptions using NLP embeddings
- Analyze item images using Computer Vision features
- Compare category, brand, and color
- Consider campus location and event time
- Generate ranked potential matches
- Provide an explainable match breakdown and confidence level

🖼️ Image Processing

Uploaded item images can be processed using a pretrained MobileNetV3 vision model.

The system extracts visual feature embeddings and compares them using cosine similarity.

A lightweight perceptual feature fallback is also available when the pretrained model cannot be loaded.

📝 NLP Matching

Back2You uses Sentence Transformers to convert item descriptions into semantic embeddings.

The system compares descriptions using cosine similarity rather than relying only on exact keyword matches.

Default model:

all-MiniLM-L6-v2

A deterministic fallback representation is available if the NLP model cannot be loaded.

📍 Multi-Factor Matching

Potential matches are calculated using multiple signals:

Signal| Default Weight
Image similarity| 40%
Text similarity| 30%
Location similarity| 15%
Time similarity| 10%
Category / Brand / Color attributes| 5%

If images are unavailable, the system dynamically rebalances the remaining signals.

Category mismatches also receive a strong penalty to reduce obviously incorrect matches.

«These weights are configurable prototype settings, not claimed to be universally optimal.»

🛡️ Claim Verification

Students can submit ownership claims using verification information such as:

- Brand
- Color
- Lost location
- Approximate time
- Distinguishing features
- Additional proof

Administrators can review claims and mark them as:

PENDING
UNDER_REVIEW
VERIFIED
REJECTED
RETURNED

The verification service provides an alignment assessment to assist administrators; it does not automatically decide ownership.

🤝 Community Helper

Back2You encourages students to report found belongings through:

- Points
- Helper streaks
- Badges
- Leaderboard
- Successful-return rewards

A successful recovery can reward the finder with additional Community Helper points and continue their streak.

🔔 Notifications

The platform provides in-app notifications for:

- New ownership claims
- Claim verification
- Claim rejection
- Successful item recovery
- Community Helper rewards
- System events

👤 Authentication & Profiles

The backend provides:

- User registration
- Login
- JWT authentication
- User profiles
- Password changes
- Role-based access

Supported roles include:

USER
ADMIN
MODERATOR

🛠️ Admin Portal

Administrators can:

- View platform statistics
- Review reports
- Review claims
- Verify claims
- Reject claims
- Mark items as returned
- View AI evaluation metrics
- Seed benchmark/test data

---

How Back2You Works

Student Reports Lost Item
          │
          ▼
   Item Information
  + Image + Description
          │
          ▼
   AI Feature Extraction
     ┌──────────────┐
     │ NLP          │
     │ Computer     │
     │ Vision       │
     └──────────────┘
          │
          ▼
 Multi-Factor Similarity
 ┌──────────────────────┐
 │ Image                │
 │ Description          │
 │ Category             │
 │ Brand / Color        │
 │ Location             │
 │ Time                 │
 └──────────────────────┘
          │
          ▼
   Ranked Candidates
          │
          ▼
   Potential Match
          │
          ▼
   Ownership Claim
          │
          ▼
 Administrator Review
          │
     ┌────┴─────┐
     ▼          ▼
  Verified    Rejected
     │
     ▼
    Returned
     │
     ▼
 Finder Reward

---

Technology Stack

Frontend

- HTML5
- CSS3
- JavaScript
- Responsive design
- Fetch API
- Local storage for authentication session handling

The frontend is intentionally built without a frontend framework such as React.

Backend

- Python
- FastAPI
- Pydantic
- Uvicorn
- JWT authentication
- bcrypt password hashing

AI / Machine Learning

- PyTorch
- Torchvision
- MobileNetV3
- Sentence Transformers
- scikit-learn
- NumPy
- Pandas
- Cosine similarity

Database & Storage

Current local development database

SQLite
└── back2you.db

The backend initializes and operates against the local SQLite database during the current prototype implementation.

Cloud / Supabase support

The project also contains:

- Supabase configuration
- Supabase Storage integration for item images
- PostgreSQL/Supabase database schema

When configured, uploaded images can be stored in Supabase Storage; otherwise the application can fall back to local "uploads/" storage.

---

Project Structure

BACK2YOU/
│
├── backend/
│   ├── api/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── claims.py
│   │   ├── community.py
│   │   ├── items.py
│   │   ├── matching.py
│   │   ├── notifications.py
│   │   └── profile.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── supabase_client.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   ├── gamification.py
│   │   ├── location.py
│   │   ├── matching.py
│   │   ├── nlp.py
│   │   ├── notifications.py
│   │   ├── verification.py
│   │   └── vision.py
│   │
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
│
├── database/
│   └── schema.sql
│
├── frontend/
│   ├── css/
│   │   ├── components.css
│   │   ├── dashboard.css
│   │   ├── responsive.css
│   │   └── style.css
│   │
│   ├── js/
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── icons.js
│   │
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── report-lost.html
│   ├── report-found.html
│   ├── matches.html
│   ├── item-details.html
│   ├── claims.html
│   ├── community.html
│   ├── profile.html
│   ├── notifications.html
│   └── admin.html
│
├── ml/
│   ├── dataset/
│   │   └── test_dataset.json
│   └── evaluation.py
│
├── uploads/
│
├── .env.example
├── back2you.db
└── README.md

---

Backend API

The FastAPI backend is organized into separate routers.

Authentication

POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me

Items

POST   /api/items/lost
POST   /api/items/found
POST   /api/items/upload-image
POST   /api/items/check-duplicate
GET    /api/items/lost
GET    /api/items/found
GET    /api/items/{item_id}
PATCH  /api/items/{item_id}
DELETE /api/items/{item_id}

Matching

GET  /api/matching
POST /api/matching/find
GET  /api/matching/{item_id}
GET  /api/matching/weights/current
POST /api/matching/weights/update

Claims

POST  /api/claims
GET   /api/claims
GET   /api/claims/{claim_id}
PATCH /api/claims/{claim_id}

Community

GET /api/community/gamification
GET /api/community/leaderboard
GET /api/community/badges

Profile

GET   /api/profile
GET   /api/profile/stats
PATCH /api/profile
POST  /api/profile/change-password

Notifications

GET   /api/notifications
PATCH /api/notifications/{notification_id}/read
POST  /api/notifications/read-all

Admin

GET  /api/admin/statistics
GET  /api/admin/reports
GET  /api/admin/claims

POST /api/admin/claims/{claim_id}/verify
POST /api/admin/claims/{claim_id}/reject
POST /api/admin/items/{item_id}/return

GET  /api/admin/evaluation
POST /api/admin/seed-test-data

---

AI Matching Architecture

Back2You uses a multi-modal matching approach.

Text

Title
  +
Description
  +
Brand
  +
Color
  +
Distinguishing Features
        │
        ▼
Sentence Transformer
        │
        ▼
Text Embedding
        │
        ▼
Cosine Similarity

Image

Item Image
    │
    ▼
Pretrained MobileNetV3
    │
    ▼
Visual Feature Embedding
    │
    ▼
Cosine Similarity

Final Matching

Image Similarity
       +
Text Similarity
       +
Attribute Similarity
       +
Location Similarity
       +
Time Similarity
       │
       ▼
Weighted Confidence Score
       │
       ▼
Ranked Potential Matches

The matching engine also generates human-readable explanations such as matching category, brand, color, visual resemblance, semantic description overlap, campus proximity, and temporal correlation.

---

Evaluation

The repository includes a prototype evaluation module designed to measure the matching engine on a benchmark dataset.

The evaluation module supports:

- Matching Accuracy
- Precision@1
- Precision@3
- Precision@5
- False Match Rate
- Text-only evaluation
- Visual/attribute-only evaluation
- Combined multi-modal evaluation

It also includes an ablation experiment comparing:

Text-Only
      vs
Vision + Attributes
      vs
Combined Back2You

Evaluation results should be generated from the included benchmark dataset rather than being treated as fixed claims about real-world performance.

---

Running Locally

1. Clone the repository

git clone https://github.com/venkateshmamidi-dev/BACK2YOU.git
cd BACK2YOU

2. Install backend dependencies

pip install -r backend/requirements.txt

3. Configure environment variables

Create a ".env" file in the project root.

Use ".env.example" as the reference.

Do not commit:

.env

or any API keys, passwords, service-role keys, or other secrets.

4. Start the FastAPI backend

From the project root:

uvicorn backend.main:app --reload

The backend will run at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc

5. Start the frontend

In another terminal:

cd frontend
python -m http.server 5500

Open:

http://localhost:5500

The frontend API client automatically connects the static frontend on port "5500" to the FastAPI backend on port "8000".

---

Database

The project currently supports a local SQLite prototype database:

back2you.db

The repository also contains a PostgreSQL/Supabase schema:

database/schema.sql

The schema covers:

- Users
- Items
- Item embeddings
- Matches
- Claims
- Gamification
- Badges
- User badges
- Notifications

---

Security Considerations

Back2You includes several application-level protections:

- JWT-based authentication
- Password hashing with bcrypt
- Role-based admin/moderator access
- Protected user-specific operations
- Item ownership checks
- Claim access restrictions
- Upload extension validation
- Maximum upload size validation
- Duplicate-report detection
- Environment-variable configuration for secrets

For production deployment, additional hardening should be performed, including secure secret management, restrictive CORS configuration, production database configuration, stronger upload validation, HTTPS, and appropriate authorization policies.

---

Project Status

Current status: Working prototype

The repository contains an integrated frontend, FastAPI backend, local database implementation, AI matching services, claims workflow, community gamification, notifications, admin portal, and prototype evaluation module.

Cloud deployment and production-grade infrastructure can be added as the project evolves.

---

Vision

Back2You aims to make campus Lost & Found more intelligent, organized, and community-driven by combining AI-assisted matching with human verification.

«Helping lost belongings find their way Back2You.»

---

License

Add an appropriate open-source license before distributing the project publicly.