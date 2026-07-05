# File Tree: Virtual-AI-Spotter
```
├── 📁 .github
│   └── 📁 workflows
├── 📁 assets
│   └── 📁 models
│       └── 📄 yolov8n-pose.pt
├── 📁 aws
│   ├── 📁 lambda
│   │   ├── 🐍 lambda_function.py
│   │   └── 📄 requirements.txt
│   ├── 📝 README.md
│   └── ⚙️ iam-policy.json
├── 📁 config
│   ├── 🐍 settings.py
│   └── 🐍 translation_strings.py
├── 📁 scripts
│   ├── 🐍 check_cam.py
│   └── 🐍 verify_refactor.py
├── 📁 src
│   ├── 📁 api
│   │   ├── 🐍 routes.py
│   │   └── 🐍 server.py
│   ├── 📁 core
│   │   ├── 📁 entities
│   │   │   ├── 🐍 session.py
│   │   │   ├── 🐍 ui_state.py
│   │   │   ├── 🐍 user.py
│   │   │   └── 🐍 workout_state.py
│   │   ├── 🐍 app.py
│   │   ├── 🐍 config_types.py
│   │   ├── 🐍 exceptions.py
│   │   ├── 🐍 factory.py
│   │   ├── 🐍 feedback.py
│   │   ├── 🐍 fsm.py
│   │   ├── 🐍 gesture_detector.py
│   │   ├── 🐍 gesture_handler.py
│   │   ├── 🐍 interfaces.py
│   │   ├── 🐍 mixins.py
│   │   ├── 🐍 protocols.py
│   │   ├── 🐍 registry.py
│   │   └── 🐍 session_manager.py
│   ├── 📁 data
│   │   ├── 🐍 api_client.py
│   │   ├── 🐍 db_manager.py
│   │   └── 📄 schema.sql
│   ├── 📁 exercises
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 curl.py
│   │   ├── 🐍 plank.py
│   │   ├── 🐍 pushup.py
│   │   └── 🐍 squat.py
│   ├── 📁 infrastructure
│   │   ├── 🐍 ai_inference.py
│   │   ├── 🐍 keypoint_extractor.py
│   │   ├── 🐍 sinks.py
│   │   └── 🐍 webcam.py
│   ├── 📁 ui
│   └── 📁 utils
│       ├── 🐍 geometry.py
│       ├── 🐍 performance.py
│       └── 🐍 smoothing.py
├── 📁 tests
│   ├── 📁 api
│   │   └── 🐍 test_routes.py
│   ├── 📁 infrastructure
│   │   └── 🐍 test_sinks.py
│   ├── 📁 mocks
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 mock_pose.py
│   │   └── 🐍 mock_video.py
│   ├── 🐍 __init__.py
│   ├── 🐍 conftest.py
│   ├── 🐍 helpers.py
│   ├── 🐍 test_api_client.py
│   ├── 🐍 test_app_di.py
│   ├── 🐍 test_app_integration.py
│   ├── 🐍 test_db_manual.py
│   ├── 🐍 test_db_negative.py
│   ├── 🐍 test_entities_manual.py
│   ├── 🐍 test_exercise_integration.py
│   ├── 🐍 test_exercises.py
│   ├── 🐍 test_fsm.py
│   ├── 🐍 test_geometry.py
│   ├── 🐍 test_gesture.py
│   ├── 🐍 test_lambda.py
│   ├── 🐍 test_plank.py
│   ├── 🐍 test_pose_estimator.py
│   ├── 🐍 test_session_manager.py
│   ├── 🐍 test_session_rest.py
│   ├── 🐍 test_smoothing.py
│   ├── 🐍 test_visualizer.py
│   ├── 🐍 verify_debouncing.py
│   ├── 🐍 verify_features.py
│   ├── 🐍 verify_i18n.py
│   └── 🐍 verify_refactor.py
├── 📁 web
│   ├── 📁 css
│   │   └── 🎨 style.css
│   ├── 📁 js
│   │   └── 📄 app.js
│   ├── 🖼️ favicon.svg
│   ├── 🌐 index.html
│   └── 🌐 workout.html
├── ⚙️ .env.example
├── ⚙️ .gitignore
├── 📝 File Tree Virtual AI Spotter.md
├── 📄 LICENSE
├── 📝 README.md
├── 🐍 main.py
└── 📄 requirements.txt
```