# Virtual AI Spotter

![Status](https://img.shields.io/badge/Status-Optimized_Beta-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)
![Coverage](https://img.shields.io/badge/Tests-Passing-brightgreen)

> � **Major Update (v2.0)**: The core engine has been refactored for **Production Readiness**. Key improvements include a new FSM-based counting logic, a modular Feedback System, and significant performance optimizations (30+ FPS on CPU).

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
    *   *Focus*: Maintaining a straight line (Shoulder-Hip-Knee alignment).
    *   *Status*: In Development.

## System Architecture

### 1. Object-Oriented Design & Core Modules
To ensure scalability, the project follows strict OOP and SOLID principles:
*   **Abstract Base Class (`Exercise`)**: Defines the contract for all exercises.
*   **FSM Core (`src/core/fsm.py`)**: A reusable `RepetitionCounter` class handles state transitions, debouncing, and hysteresis. It supports both standard (Squat) and inverted (Curl) logic.
*   **Feedback Core (`src/core/feedback.py`)**: A `FeedbackSystem` class aggregates form check rules and prioritizes critical messages.

### 2. High-Performance Optimization
*   **Geometry Engine**: NumPy overhead removed in favor of standard `math` for critical vector calculations (`src/utils/geometry.py`).
*   **Visualizer**: Implemented Region-of-Interest (ROI) alpha blending to minimize pixel operations during HUD rendering.

### 3. Data Structures & Algorithms
*   **Circular Buffer**: Using `collections.deque` to maintain a sliding window of the last 30 frames for temporal smoothing.
*   **One Euro Filter**: Advanced jitter reduction for keypoint data.

### 4. Hybrid Cloud Architecture (Edge + AWS)
*   **Edge (Local PC/GPU)**: AI inference runs locally for zero-latency feedback.
*   **Cloud (AWS)**: Asynchronous synchronization to DynamoDB and S3 via Lambda functions.

### 5. Quality Assurance
*   **Unit Testing**: Comprehensive tests in `tests/` covering:
    *   FSM Logic (Standard, Inverted, Debouncing).
    *   Geometric Calculations.
    *   Database Integrations.

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
    - [ ] Plank (Static stability check)
- [ ] **Cloud & DevOps**
    - [ ] AWS Lambda & DynamoDB implementation details
    - [x] Unit Testing Suite (`tests/`)
    - [ ] CI/CD Pipeline (GitHub Actions)
