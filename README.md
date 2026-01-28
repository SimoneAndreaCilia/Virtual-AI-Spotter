# Virtual AI Spotter

![Status](https://img.shields.io/badge/Status-Work_in_Progress-yellow)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)

> 🚧 **Work in Progress**: This project is currently under active development. Core features like **YOLOv8** integration, **Bicep Curl** analysis, and the **visual HUD** are fully functional. AWS cloud synchronization and additional exercises are being implemented incrementally.

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
- **Automatic Rep Counting**: Precision counting based on biomechanical state transitions.
- **Form Correction**: Instant feedback on posture (e.g., "Lower your hips", "Straighten back") using geometric rules.
- **Multi-language Support**: Fully localized interface (Italian/English) with dynamic switching.
- **Advanced HUD Visualization**: Pro-style transparent overlay with real-time feedback, colored indicators, and smooth skeletal rendering.

## MVP Scope (Minimum Viable Product)
The initial release focuses on 4 fundamental exercises that test different aspects of the tracking engine:

1.  **Squat (Lower Body)**
    *   *Focus*: Knee and hip angles.
    *   *Challenge*: Defining "UP" (standing) vs "DOWN" (valid squat depth) states.
    *   *Feedback*: Squat depth and back alignment.

2.  **Push-up (Upper Body)**
    *   *Focus*: Body alignment and elbow extension.
    *   *Challenge*: Robustness against occlusion (body close to floor).

3.  **Bicep Curl (Isolation)**
    *   *Focus*: Elbow flexion/extension.
    *   *Challenge*: Calibrating the counting algorithm on a simple cyclical movement.

4.  **Plank (Static Core)**
    *   *Focus*: Maintaining a straight line (Shoulder-Hip-Knee alignment).
    *   *Challenge*: Static analysis (Time Under Tension) rather than repetition counting.

## System Architecture

### 1. Object-Oriented Design (Abstraction & Polymorphism)
To ensure scalability, the project follows strict OOP principles:
*   **Abstract Base Class (`Exercise`)**: Defines the contract for all exercises (methods like `calculate_angle`, `check_form`, `count_reps`).
*   **Polymorphic Subclasses**: Each exercise (e.g., `Squat`, `PushUp`) inherits from the base class and implements its own specific biomechanical logic.

### 2. Data Structures & Algorithms
We go beyond basic lists to optimize performance and data integrity:
*   **Circular Buffer**: Using `collections.deque` to maintain a sliding window of the last 30 frames. This allows for temporal analysis, preventing false positives from single noisy frames.
*   **Signal Smoothing**: Implementation of algorithms like **One Euro Filter** or **Exponential Moving Average (EMA)** on raw YOLO keypoints to reduce "jittering" and ensure stable angle readings.

### 3. Clean Architecture & Localization
*   **Centralized Settings**: All configuration parameters (Thresholds, Colors, Paths) are managed in `config/settings.py` for easy tuning.
*   **Localization Layer**: A dedicated `LanguageManager` (`config/translation_strings.py`) handles dynamic string translation, separating logic from presentation.
*   **Visualizer Engine**: A specialized `Visualizer` class handles all rendering duties, using ROI optimization for high-performance transparent overlays.

### 4. Hybrid Cloud Architecture (Edge + AWS)
The system employs a hybrid approach to balance latency and data persistence:
*   **Edge (Local PC/GPU)**: The AI inference (YOLOv8) and logic run locally to ensure real-time performance without network lag.
*   **Cloud (AWS)**: Asynchronous synchronization at the end of each set.
    *   **AWS Lambda**: Serverless functions to ingest workout data (e.g., `{"exercise": "Squat", "reps": 12, "mistakes": 2}`).
    *   **Amazon DynamoDB (NoSQL)**: A flexible, high-speed database for storing workout analytics.
    *   **Amazon S3**: Object storage for screenshots captured when form errors are detected, allowing users to review their mistakes later.

### 5. Database Strategy
*   **Local (SQLite)**: Used for storing user preferences and caching workout data if the device is offline.
*   **Cloud (DynamoDB)**: The central repository for long-term history and analytics.

### 6. DevOps & Quality Assurance
*   **CI/CD**: Automated pipelines using **GitHub Actions** for build and deployment checks.
*   **Testing**: Comprehensive **Unit Testing** suite to validate geometric calculations and state machine logic.

---

## 🗺️ Roadmap

- [x] **Project Initialization**
    - [x] Define Architecture & Technology Stack
    - [x] Set up Repository Structure & Security (`.gitignore`)
- [x] **Core Engineering**
    - [x] Implement `Exercise` Abstract Base Class (OOP)
    - [x] Integrate YOLOv8-pose for real-time keypoints
    - [x] Develop Geometry Engine for angle calculation
    - [x] **New**: Implement Visualizer & HUD Engine
    - [x] **New**: Implement Multi-language Support (IT/EN)
- [ ] **Exercise Logic (MVP)**
    - [ ] Squat Analysis (Depth & Form)
    - [ ] Push-up Analysis (Occlusion handling)
    - [x] Bicep Curl (Rep counting logic)
    - [ ] Plank (Static stability check)
- [ ] **Cloud & DevOps**
    - [ ] AWS Lambda & DynamoDB integration
    - [ ] Unit Testing Suite
    - [ ] CI/CD Pipeline (GitHub Actions)
