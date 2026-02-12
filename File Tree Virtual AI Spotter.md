```
├── 📁 .github
│   └── 📁 workflows                          # CI/CD pipeline definitions
├── 📁 assets
│   └── 📁 models
│       └── 📄 yolov8n-pose.pt                 # Pre-trained YOLOv8 pose model
├── 📁 config
│   ├── 🐍 settings.py                         # Global constants, thresholds, colors
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
├── 📁 tests                                   # Automated test suite (136 tests)
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
│   ├── 🐍 test_plank.py                       # Plank lifecycle & timer tests
│   ├── 🐍 test_pose_estimator.py              # PoseEstimator protocol tests
│   ├── 🐍 test_session_manager.py             # Workout flow & state transitions
│   ├── 🐍 test_smoothing.py                   # One Euro Filter convergence tests
│   ├── 🐍 test_visualizer.py                  # Renderer + state display mapping tests
│   ├── 🐍 verify_debouncing.py                # Manual debouncing validation
│   ├── 🐍 verify_features.py                  # Manual feature smoke tests
│   ├── 🐍 verify_i18n.py                      # Manual i18n string verification
│   └── 🐍 verify_refactor.py                  # Manual refactor validation
├── ⚙️ .gitignore
├── 📄 LICENSE                                  # AGPL v3
├── 📝 README.md
├── 🐍 main.py                                 # Application entry point
└── 📄 requirements.txt                        # Python dependencies
```