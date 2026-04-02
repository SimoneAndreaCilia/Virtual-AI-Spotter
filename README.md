# Virtual AI Spotter

![Status](https://img.shields.io/badge/Status-Optimized_Beta-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)
![Coverage](https://img.shields.io/badge/Tests-Passing-brightgreen)
![AWS](https://img.shields.io/badge/Cloud-AWS_Integrated-orange)

> 🚀 **Major Update**: The core engine has been refactored for **Production Readiness**.
> Full rewrite around **FSM-based counting** (debouncing + hysteresis), a **modular Feedback System**, **One Euro Filter** signal smoothing, and a **pure-math Geometry Engine** (zero NumPy overhead).
> Architecture highlights: Factory + Registry extensibility, Protocol-based DI, Session Manager with set/rest orchestration, hands-free **Gesture Control**, **i18n** (IT/EN), **SQLite** persistence, and an optimized **HUD** with ROI alpha blending — all validated by a **150+ test suite** running at **30+ FPS on CPU**.

> ☁️ **NEW — AWS Cloud Integration**: Workout sessions are now persisted to the cloud via **API Gateway → Lambda → DynamoDB** pipeline. Data Batching pattern sends a single JSON payload per session. Configurable via `.env`, fully optional (app works offline with SQLite only).

## Project Overview
**Virtual AI Spotter** is a real-time Computer Vision assistant designed to act as an intelligent personal trainer. It utilizes state-of-the-art Deep Learning and geometric analysis to provide automatic repetition counting, exercise suggestions, and instant feedback on execution form.

## Technology Stack
- **Core AI**: ![YOLOv8](https://img.shields.io/badge/YOLOv8-Deep_Learning-blue) YOLOv8 (Pose Estimation)
- **Framework**: ![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?logo=PyTorch&logoColor=white) PyTorch
- **Computer Vision**: ![OpenCV](https://img.shields.io/badge/OpenCV-white.svg?logo=opencv&logoColor=black) OpenCV
- **Logic**: 📐 Geometric Vector Analysis & ⚙️ Finite State Machines (FSM)
- **Cloud**: ![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?logo=amazon-aws&logoColor=white) AWS (Lambda, DynamoDB, S3)
- **Database**: ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?logo=sqlite&logoColor=white) ![DynamoDB](https://img.shields.io/badge/Amazon%20DynamoDB-4053D6?logo=amazon-dynamodb&logoColor=white) SQLite (Local), DynamoDB (Cloud)

## Key Features
- **Real-time Pose Estimation**: High-speed, accurate body tracking using YOLOv8-pose.
- **Action Classification**: Distinguishes between different exercises and movement phases.
- **Automatic Rep Counting**: Precision counting based on **Finite State Machines (FSM)** with debouncing and hysteresis.
- **Form Correction**: Instant feedback on posture (e.g., "Lower your hips", "Straighten back") using a modular **Feedback System**.
- **Multi-language Support**: Fully localized interface (Italian/English) with dynamic switching.
- **High-Performance HUD**: Optimized Visualizer engine using ROI-based Alpha Blending for smooth, transparent overlays.
- **Gesture Control**: Hands-free interaction using pose-based gestures (e.g., raised arm to skip rest periods).
- **Extensible Architecture**: Factory + Registry Pattern enables adding new exercises without modifying core code. Dependency Injection via Python Protocols for testability.

## MVP Scope (Minimum Viable Product)
The initial release focuses on 4 fundamental exercises that test different aspects of the tracking engine:

1.  **Squat (Lower Body)**
    *   *Focus*: Knee and hip angles.
    *   *Logic*: Standard FSM (Down < Threshold, Up > Threshold).
    *   *Feedback*: Squat depth and back alignment.

2.  **Push-up (Upper Body)**
    *   *Focus*: Body alignment and elbow extension.
    *   *Challenges*: Robustness against occlusion (body close to floor).
    *   *Feedback*: "Keep back straight" via body angle analysis.

3.  **Bicep Curl (Isolation)**
    *   *Focus*: Elbow flexion/extension.
    *   *Logic*: Inverted FSM Logic (Up/Flexion < Threshold, Down/Extension > Threshold).
    *   *Feedback*: Full extension check.

4.  **Plank (Static Core)**
    *   *Focus*: Maintaining a straight line (Shoulder-Hip-Ankle alignment).
    *   *Logic*: `StaticDurationCounter` FSM with countdown, active timer, and form break detection.

## System Architecture

The project follows a **Layered Architecture** with clear separation of concerns, enabling testability, extensibility (Open/Closed Principle), and adherence to Domain-Driven Design (DDD) principles.

### Data Flow Diagram

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph INFRA["🔌 Infrastructure Layer"]
        direction TB
        A["📷 Webcam"] --> B["🤖 YOLOv8 Pose"]
        B --> C["🔑 Keypoint Extractor"]
    end

    subgraph CORE["⚡ Core Domain"]
        direction TB
        D["📐 Geometry Engine"] --> E["⚙️ FSM"]
        E --> F["💬 Feedback"]
    end

    subgraph UI["🎨 Presentation Layer"]
        direction TB
        G["🖥️ Visualizer"] --> H["📊 Renderers"]
    end

    C ==> D
    F ==> G

    %% Layer styling - pastel fills, semantic strokes
    style INFRA fill:#f3f4f6,stroke:#6b7280,stroke-width:2px,color:#374151
    style CORE fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,color:#1e40af
    style UI fill:#f5f3ff,stroke:#8b5cf6,stroke-width:2px,color:#5b21b6

    %% Node styling - light backgrounds, dark text
    style A fill:#ffffff,stroke:#9ca3af,stroke-width:1px,color:#1f2937
    style B fill:#ffffff,stroke:#9ca3af,stroke-width:1px,color:#1f2937
    style C fill:#ffffff,stroke:#9ca3af,stroke-width:1px,color:#1f2937
    style D fill:#ffffff,stroke:#60a5fa,stroke-width:1px,color:#1e3a8a
    style E fill:#ffffff,stroke:#60a5fa,stroke-width:1px,color:#1e3a8a
    style F fill:#ffffff,stroke:#60a5fa,stroke-width:1px,color:#1e3a8a
    style G fill:#ffffff,stroke:#a78bfa,stroke-width:1px,color:#4c1d95
    style H fill:#ffffff,stroke:#a78bfa,stroke-width:1px,color:#4c1d95

    linkStyle default stroke:#64748b,stroke-width:1px
    linkStyle 3 stroke:#059669,stroke-width:2px
    linkStyle 4 stroke:#059669,stroke-width:2px
```

### 1. Core Domain (`src/core`)

Business logic is fully isolated from external dependencies:

*   **Entities** (`src/core/entities/`): Domain objects following DDD — `Session`, `User`, `WorkoutState`, `UIState`.
*   **FSM Core** (`fsm.py`): Reusable `RepetitionCounter` with debouncing, hysteresis, and support for standard/inverted logic.
*   **Feedback System** (`feedback.py`): Aggregates form-check rules and prioritizes messages.
*   **Factory + Registry** (`factory.py`, `registry.py`): Exercises self-register via `@register_exercise` decorator — no if/elif chains.
*   **Session Manager** (`session_manager.py`): Orchestrates workout flow, rest periods, and set progression.
*   **Dependency Injection**: Abstractions defined in `protocols.py` (PoseDetector, KeypointExtractor, DatabaseManagerProtocol) enable mock injection for CI/CD testing.

### 2. Infrastructure Layer (`src/infrastructure`)

Handles external integrations, decoupled from business logic:

*   **AI Inference** (`ai_inference.py`): YOLO model wrapper implementing `PoseDetector` protocol.
*   **Keypoint Extractor** (`keypoint_extractor.py`): Transforms raw YOLO output to standardized 17×3 arrays.
*   **Webcam** (`webcam.py`): Frame capture abstraction for easy replacement with video files or streams.

### 3. UI & Visualization (`src/ui`)

Presentation layer with separated rendering responsibilities:

*   **Visualizer** (`visualizer.py`): Facade coordinating all renderers.
*   **Dashboard Renderer**: Draws HUD panels (reps, sets, feedback text).
*   **Overlay Renderer**: Transparent overlays using ROI-based alpha blending.
*   **Skeleton Renderer**: Draws pose skeleton connections.

### 4. Signal Processing (`src/utils`)

*   **Geometry Engine** (`geometry.py`): Pure `math`-based vector calculations (no NumPy overhead).
*   **Smoothing** (`smoothing.py`): One Euro Filter for jitter reduction.
*   **Circular Buffer**: `collections.deque` for temporal smoothing (30-frame window).

### 5. Hybrid Cloud Architecture (AWS)

The project implements a **Hybrid Edge–Cloud** model: real-time inference runs locally for zero-latency feedback, while session data is persisted to the cloud asynchronously after each workout.

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph EDGE["💻 Edge (Local)"]
        direction TB
        A["📷 Webcam"] --> B["🤖 YOLOv8 Pose"]
        B --> C["⚙️ FSM + Feedback"]
        C --> D["💾 SQLite"]
    end

    subgraph CLOUD["☁️ AWS Cloud"]
        direction TB
        E["🌐 API Gateway"] --> F["⚡ Lambda"]
        F --> G["🗄️ DynamoDB"]
    end

    D ==>|"POST /sessions\(Data Batching)"| E

    style EDGE fill:#f3f4f6,stroke:#6b7280,stroke-width:2px,color:#374151
    style CLOUD fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#9a3412
    style A fill:#ffffff,stroke:#9ca3af,stroke-width:1px,color:#1f2937
    style B fill:#ffffff,stroke:#9ca3af,stroke-width:1px,color:#1f2937
    style C fill:#ffffff,stroke:#60a5fa,stroke-width:1px,color:#1e3a8a
    style D fill:#ffffff,stroke:#60a5fa,stroke-width:1px,color:#1e3a8a
    style E fill:#ffffff,stroke:#fb923c,stroke-width:1px,color:#9a3412
    style F fill:#ffffff,stroke:#fb923c,stroke-width:1px,color:#9a3412
    style G fill:#ffffff,stroke:#fb923c,stroke-width:1px,color:#9a3412
    linkStyle default stroke:#64748b,stroke-width:1px
    linkStyle 3 stroke:#f97316,stroke-width:2px
```

*   **Edge (Local)**: Real-time inference on local PC/GPU for zero-latency feedback. Sessions are saved to **SQLite**.
*   **Cloud (AWS)**: After each workout, a single JSON payload (Data Batching) is sent to **API Gateway** (`POST /sessions`), which triggers a **Lambda** function that validates the data and writes it to **DynamoDB**.
*   **Security**: API Key authentication via `x-api-key` header. IAM policy follows Least Privilege (only `dynamodb:PutItem` + CloudWatch logs).
*   **Configuration**: All AWS settings are loaded from `.env` via `config/settings.py`. Cloud upload is fully optional — without a `.env` file, the app works entirely offline.

### 6. Quality Assurance

*   **Test Suite** (`tests/`): 150+ automated tests across 14 test files — FSM, Geometry, SessionManager, Gesture Detection, DI mocks, exercise integration, state display, and **AWS Lambda** coverage.
*   **Verification Scripts**: Manual validation tools for debouncing, i18n, refactoring.

---

<details>
<summary>📂 <strong>View Project Structure (File Tree)</strong></summary>

```
├── 📁 .github
│   └── 📁 workflows                          # CI/CD pipeline definitions
├── 📁 assets
│   └── 📁 models
│       └── 📄 yolov8n-pose.pt                 # Pre-trained YOLOv8 pose model
├── 📁 aws                                     # ☁️ AWS backend infrastructure
│   ├── 📁 lambda                              # Lambda function package
│   │   ├── 🐍 lambda_function.py              # Session Logger (validate → DynamoDB)
│   │   └── 📄 requirements.txt               # Lambda dependencies (boto3)
│   ├── 📄 iam-policy.json                     # Least-privilege IAM policy
│   └── 📝 README.md                           # AWS deploy instructions & API docs
├── 📁 config
│   ├── 🐍 settings.py                         # Global constants, thresholds, AWS config
│   └── 🐍 translation_strings.py              # i18n strings (IT/EN)
├── 📁 scripts
│   ├── 🐍 check_cam.py                        # Camera connectivity check
│   └── 🐍 verify_refactor.py                  # Post-refactor sanity checks
├── 📁 src
│   ├── 📁 core                                # Business logic (framework-agnostic)
│   │   ├── 📁 entities                        # Domain objects (DDD)
│   │   │   ├── 🐍 session.py                  # Workout session dataclass
│   │   │   ├── 🐍 ui_state.py                 # Rendering state container
│   │   │   ├── 🐍 user.py                     # User profile dataclass
│   │   │   └── 🐍 workout_state.py            # Workout FSM states (ACTIVE/REST/FINISHED)
│   │   ├── 🐍 app.py                          # Composition root & main loop
│   │   ├── 🐍 config_types.py                 # TypedDict definitions for configs
│   │   ├── 🐍 exceptions.py                   # Custom exception hierarchy (SpotterError)
│   │   ├── 🐍 factory.py                      # Exercise factory (creates instances)
│   │   ├── 🐍 feedback.py                     # Rule-based form correction engine
│   │   ├── 🐍 fsm.py                          # RepetitionCounter & StaticDurationCounter
│   │   ├── 🐍 gesture_detector.py             # Pose-based gesture recognition
│   │   ├── 🐍 interfaces.py                   # ABCs: Exercise, VideoSource, StateDisplayInfo
│   │   ├── 🐍 protocols.py                    # DI protocols: PoseDetector, DBManager
│   │   ├── 🐍 registry.py                     # @register_exercise decorator & registry
│   │   └── 🐍 session_manager.py              # Set/rest/rep orchestration
│   ├── 📁 data                                # Persistence layer
│   │   ├── 🐍 db_manager.py                   # SQLite CRUD operations
│   │   └── 📄 schema.sql                      # Database schema definition
│   ├── 📁 exercises                           # Concrete exercise implementations
│   │   ├── 🐍 __init__.py                     # Auto-imports for registration
│   │   ├── 🐍 curl.py                         # Bicep Curl (inverted FSM)
│   │   ├── 🐍 plank.py                        # Plank (static hold timer)
│   │   ├── 🐍 pushup.py                       # Push-Up (bilateral + form check)
│   │   └── 🐍 squat.py                        # Squat (standard FSM)
│   ├── 📁 infrastructure                      # External system adapters
│   │   ├── 🐍 ai_inference.py                 # YOLO model wrapper (PoseDetector)
│   │   ├── 🐍 keypoint_extractor.py           # Raw YOLO output → 17×3 arrays
│   │   └── 🐍 webcam.py                       # OpenCV camera capture (VideoSource)
│   ├── 📁 ui                                  # Presentation layer
│   │   ├── 🐍 cli.py                          # Interactive workout setup prompts
│   │   ├── 🐍 dashboard_renderer.py           # HUD panel (reps, sets, state)
│   │   ├── 🐍 overlay_renderer.py             # Full-screen REST/FINISHED overlays
│   │   ├── 🐍 skeleton_renderer.py            # Pose skeleton & angle arcs
│   │   └── 🐍 visualizer.py                   # Renderer facade (delegates to above)
│   └── 📁 utils                               # Signal processing utilities
│       ├── 🐍 geometry.py                     # Pure-math angle calculations
│       ├── 🐍 performance.py                  # FPS counter & timing helpers
│       └── 🐍 smoothing.py                    # One Euro Filter for jitter reduction
├── 📁 tests                                   # Automated test suite (150+ tests)
│   ├── 📁 mocks                               # Test doubles
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 mock_pose.py                    # Fake PoseDetector for DI tests
│   │   └── 🐍 mock_video.py                   # Fake VideoSource for DI tests
│   ├── 🐍 __init__.py
│   ├── 🐍 helpers.py                          # Shared fixtures (UIState, dummy frames)
│   ├── 🐍 test_app_di.py                      # Dependency injection wiring tests
│   ├── 🐍 test_db_manual.py                   # SQLite persistence tests
│   ├── 🐍 test_entities_manual.py             # Domain entity tests
│   ├── 🐍 test_exercise_integration.py        # End-to-end rep counting & form feedback
│   ├── 🐍 test_exercises.py                   # Exercise process_frame unit tests
│   ├── 🐍 test_fsm.py                         # FSM state transitions & debouncing
│   ├── 🐍 test_geometry.py                    # Angle calculation edge cases
│   ├── 🐍 test_gesture.py                     # Gesture recognition tests
│   ├── 🐍 test_lambda.py                      # ☁️ AWS Lambda handler & validation tests
│   ├── 🐍 test_plank.py                       # Plank lifecycle & timer tests
│   ├── 🐍 test_pose_estimator.py              # PoseEstimator protocol tests
│   ├── 🐍 test_session_manager.py             # Workout flow & state transitions
│   ├── 🐍 test_smoothing.py                   # One Euro Filter convergence tests
│   ├── 🐍 test_visualizer.py                  # Renderer + state display mapping tests
│   ├── 🐍 verify_debouncing.py                # Manual debouncing validation
│   ├── 🐍 verify_features.py                  # Manual feature smoke tests
│   ├── 🐍 verify_i18n.py                      # Manual i18n string verification
│   └── 🐍 verify_refactor.py                  # Manual refactor validation
├── ⚙️ .env                                     # AWS credentials & cloud config
├── ⚙️ .gitignore
├── 📄 LICENSE                                  # AGPL v3
├── 📝 README.md
├── 🐍 main.py                                 # Application entry point
└── 📄 requirements.txt                        # Python dependencies
```

</details>

---

## 🗺️ Roadmap

- [x] **Project Initialization**
    - [x] Architecture & Tech Stack Definition
    - [x] Repository Structure & `.gitignore`
- [x] **Core Engineering**
    - [x] Abstract `Exercise` Class
    - [x] YOLOv8 Integration
    - [x] **FSM & Feedback Architecture Refactoring**
    - [x] **Performance Optimization (Math + ROI Visualizer)**
- [x] **Exercise Logic (MVP)**
    - [x] Squat (Depth & Form)
    - [x] Push-up (Occlusion handling)
    - [x] Bicep Curl (Inverted Logic)
    - [x] Plank (Static stability check)
- [x] **Cloud & DevOps**
    - [x] AWS Lambda Session Logger (`aws/lambda/lambda_function.py`)
    - [x] DynamoDB Table
    - [x] API Gateway HTTP API (`POST /sessions` + API Key auth)
    - [x] IAM Least-Privilege Policy (`aws/iam-policy.json`)
    - [x] Cloud config in `settings.py` + `.env` support
    - [x] Lambda unit tests (`tests/test_lambda.py` — 25 tests)
    - [x] Unit Testing Suite (`tests/`)
    - [ ] CI/CD Pipeline (GitHub Actions)
