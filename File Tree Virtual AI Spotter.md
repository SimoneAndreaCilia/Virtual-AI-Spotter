# File Tree: Virtual-AI-Spotter
```
├── 📁 .github
│   └── 📁 workflows
├── 📁 assets
│   └── 📁 models
│       └── 📄 yolov8n-pose.pt
├── 📁 config
│   ├── 🐍 settings.py
│   └── 🐍 translation_strings.py
├── 📁 scripts
│   ├── 🐍 check_cam.py
│   └── 🐍 verify_refactor.py
├── 📁 src
│   ├── 📁 core
│   │   ├── 📁 entities
│   │   │   ├── 🐍 session.py
│   │   │   ├── 🐍 ui_state.py
│   │   │   ├── 🐍 user.py
│   │   │   └── 🐍 workout_state.py
│   │   ├── 🐍 app.py
│   │   ├── 🐍 factory.py
│   │   ├── 🐍 feedback.py
│   │   ├── 🐍 fsm.py
│   │   ├── 🐍 gesture_detector.py
│   │   ├── 🐍 interfaces.py
│   │   ├── 🐍 protocols.py
│   │   ├── 🐍 registry.py
│   │   └── 🐍 session_manager.py
│   ├── 📁 data
│   │   ├── 🐍 db_manager.py
│   │   └── 📄 schema.sql
│   ├── 📁 exercises
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 curl.py
│   │   ├── 🐍 pushup.py
│   │   └── 🐍 squat.py
│   ├── 📁 infrastructure
│   │   ├── 🐍 ai_inference.py
│   │   ├── 🐍 keypoint_extractor.py
│   │   └── 🐍 webcam.py
│   ├── 📁 ui
│   │   ├── 🐍 cli.py
│   │   ├── 🐍 dashboard_renderer.py
│   │   ├── 🐍 overlay_renderer.py
│   │   ├── 🐍 skeleton_renderer.py
│   │   └── 🐍 visualizer.py
│   └── 📁 utils
│       ├── 🐍 geometry.py
│       ├── 🐍 performance.py
│       └── 🐍 smoothing.py
├── 📁 tests
│   ├── 📁 mocks
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 mock_pose.py
│   │   └── 🐍 mock_video.py
│   ├── 🐍 __init__.py
│   ├── 🐍 helpers.py
│   ├── 🐍 test_app_di.py
│   ├── 🐍 test_db_manual.py
│   ├── 🐍 test_entities_manual.py
│   ├── 🐍 test_fsm.py
│   ├── 🐍 test_geometry.py
│   ├── 🐍 test_gesture.py
│   ├── 🐍 test_pose_estimator.py
│   ├── 🐍 test_session_manager.py
│   ├── 🐍 test_smoothing.py
│   ├── 🐍 test_visualizer.py
│   ├── 🐍 verify_debouncing.py
│   ├── 🐍 verify_features.py
│   ├── 🐍 verify_i18n.py
│   └── 🐍 verify_refactor.py
├── ⚙️ .gitignore
├── 📝 File Tree Virtual AI Spotter.md
├── 📄 LICENSE
├── 📝 README.md
├── 🐍 main.py
└── 📄 requirements.txt
```