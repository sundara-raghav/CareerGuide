# System Architecture — CareerGuide India

## High-Level Architecture

```mermaid
graph TB
    subgraph Client["🌐 Client Layer"]
        Browser["Browser / PWA"]
        Mobile["Mobile (Responsive)"]
    end

    subgraph Nginx["🔀 Nginx Reverse Proxy"]
        NX["Nginx<br/>TLS termination<br/>Static files<br/>Load balance"]
    end

    subgraph App["⚙️ Flask Application (Gunicorn)"]
        Auth["auth blueprint"]
        Student["student blueprint"]
        Rec["recommendations blueprint"]
        Colleges["colleges blueprint"]
        Careers["careers blueprint"]
        Admin["admin blueprint"]
        Analytics["analytics blueprint"]
        Notif["notifications blueprint"]
    end

    subgraph Services["🧩 Service Layer"]
        QuizSvc["QuizService<br/>56-Q scoring"]
        RecSvc["RecommendationService<br/>ML + rules + scholarships"]
        CollegeSvc["CollegeService<br/>Haversine search"]
        NotifSvc["NotificationService<br/>Email/SMS/WhatsApp"]
        AnalyticsSvc["AnalyticsService<br/>Impact metrics"]
    end

    subgraph ML["🤖 ML Pipeline"]
        PP["Preprocessing<br/>Pipeline"]
        RF["Random Forest"]
        XGB["XGBoost"]
        LR["Logistic Regression"]
        Stack["Stacking<br/>Meta-Learner"]
        Rules["Rule-Based<br/>Layer (budget/geo)"]
        SHAP["SHAP<br/>Explainer"]
    end

    subgraph Data["💾 Data Layer"]
        PG["PostgreSQL<br/>(Supabase)"]
        Redis["Redis<br/>(Celery broker + cache)"]
        Storage["Supabase Storage<br/>(uploads)"]
        Artifacts["ML Artifacts<br/>(.pkl files)"]
    end

    subgraph Queue["⚡ Async Queue"]
        Celery["Celery Workers"]
        Beat["Celery Beat<br/>(cron scheduler)"]
    end

    subgraph External["🌍 External APIs"]
        GMaps["Google Maps JS API<br/>+ Places API"]
        SendGrid["SendGrid<br/>(Email)"]
        Twilio["Twilio<br/>(SMS + WhatsApp)"]
        Sentry["Sentry<br/>(Error tracking)"]
    end

    Browser -->|HTTPS| NX
    Mobile -->|HTTPS| NX
    NX -->|Proxy /| App
    NX -->|Direct /static| Storage

    Auth --> Services
    Student --> Services
    Rec --> Services
    Colleges --> Services
    Admin --> Services

    RecSvc --> ML
    PP --> RF & XGB & LR
    RF & XGB & LR --> Stack
    Stack --> Rules --> SHAP

    Services --> PG
    Services --> Redis
    NotifSvc --> Queue
    Queue --> SendGrid & Twilio

    App --> External
    Admin --> Analytics
    Analytics --> PG
```

---

## Request Flow — Student Getting Recommendations

```mermaid
sequenceDiagram
    participant S as Student Browser
    participant N as Nginx
    participant F as Flask App
    participant Q as QuizService
    participant R as RecommendationService
    participant ML as ML Inference
    participant DB as PostgreSQL

    S->>N: POST /student/quiz/submit
    N->>F: proxy request
    F->>Q: submit_attempt(attempt_id, responses)
    Q->>Q: score_responses() → normalize 0-100
    Q->>DB: INSERT aptitude_scores
    Q->>DB: UPDATE students.quiz_complete = true
    F->>R: generate_for_student(student)
    R->>ML: get_recommendation(student, aptitude)
    ML->>ML: pipeline.transform(features)
    ML->>ML: ensemble.predict(X)
    ML-->>R: {stream, courses, careers, explanations}
    R->>R: match_scholarships(student)
    R->>DB: INSERT recommendations
    F-->>S: redirect /recommendations/dashboard
    S->>F: GET /recommendations/dashboard
    F->>DB: SELECT latest recommendation
    F-->>S: render dashboard.html
```

---

## ML Ensemble Architecture

```mermaid
graph LR
    subgraph Input["Input Features (40+)"]
        M["Marks (9 subjects)"]
        A["Aptitude scores (6 dims)"]
        I["Interests (16 binary)"]
        C["Constraints (budget, travel, hostel)"]
        D["Demographics (board, school type)"]
    end

    subgraph Preprocessing["Preprocessing Pipeline"]
        ME["MarkFeatureEngineer<br/>(aggregate, tier)"]
        AE["AptitudeEngineer<br/>(composite, STEM/Humanities)"]
        CE["CategoricalEncoder<br/>(LabelEncoder)"]
        IN["IncomeNormalizer<br/>(log1p)"]
        CS["ColumnSelector + StandardScaler"]
    end

    subgraph Ensemble["Stacking Ensemble (per task)"]
        RF["RandomForest<br/>n=200, depth=12"]
        XGB["XGBoost<br/>n=150, lr=0.1"]
        LR["LogisticRegression<br/>(calibrated)"]
        META["Meta-Learner<br/>LogisticRegression<br/>(5-fold CV)"]
        CAL["Platt Calibration<br/>(confidence scores)"]
    end

    subgraph Output["Top-K Output"]
        S["Stream Rank (Top 4)"]
        CO["Course Rank (Top 5)"]
        CA["Career Rank (Top 5)"]
        EX["SHAP Explanations"]
    end

    Input --> Preprocessing
    Preprocessing --> RF & XGB & LR
    RF & XGB & LR --> META
    META --> CAL
    CAL --> Output
```

---

## Database Entity Relationship

```mermaid
erDiagram
    users ||--o| students : "has profile"
    users ||--o| parents : "has profile"
    students ||--o{ quiz_attempts : "takes"
    students ||--o| aptitude_scores : "has"
    students ||--o{ recommendations : "receives"
    students ||--o{ admission_events : "tracks"
    recommendations ||--o{ model_feedback : "gets feedback"
    recommendations ||--o{ counselor_feedback : "gets reviewed"
    colleges ||--o{ admission_events : "hosts"
    users ||--o{ notifications : "receives"
    parents }o--o| students : "linked to"

    users {
        bigint id PK
        uuid supabase_uid
        text email
        user_role role
        text preferred_language
    }
    students {
        bigint id PK
        int student_class
        text board
        jsonb marks
        text district
        numeric travel_radius_km
        boolean quiz_complete
    }
    recommendations {
        bigint id PK
        text recommended_stream
        numeric stream_confidence
        jsonb top_courses
        jsonb career_clusters
        jsonb explanations
    }
```

---

## Notification Event Flow

```mermaid
stateDiagram-v2
    [*] --> Trigger
    Trigger --> QueuedTask : Celery .delay()
    QueuedTask --> Email : channel=email
    QueuedTask --> SMS : channel=sms
    QueuedTask --> WhatsApp : channel=whatsapp
    QueuedTask --> InApp : channel=inapp

    Email --> Sent : SendGrid 202
    Email --> Failed : API error
    SMS --> Sent : Twilio 201
    SMS --> Failed : API error
    WhatsApp --> Sent : Twilio WA
    InApp --> Stored : DB insert

    Sent --> Logged
    Failed --> Retry : max_retries=3
    Retry --> Sent
    Retry --> DeadLetter : exhausted
```
