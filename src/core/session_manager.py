import logging
from typing import Dict, Any, Optional
from src.core.interfaces import Exercise
from src.core.protocols import KeypointExtractor
from src.core.entities.session import Session
from src.core.entities.ui_state import UIState
from config.translation_strings import i18n

class SessionManager:
    def __init__(self, db_manager: Any, user_id: int, exercise: Exercise, 
                 keypoint_extractor: KeypointExtractor, target_sets: int, target_reps: int):
        self.db_manager: Any = db_manager
        self.user_id: int = user_id
        
        # Config
        self.target_sets: int = target_sets
        self.target_reps: int = target_reps
        
        # State
        self.current_set: int = 1
        self.workout_state: str = "EXERCISE" # EXERCISE | REST | FINISHED
        
        # Injected dependencies
        self.exercise_logic = exercise
        self.keypoint_extractor = keypoint_extractor
        
        # Session Entity
        self.session_entity = Session(
            user_id=user_id,
            target_sets=target_sets,
            target_reps=target_reps
        )
        logging.info(f"SessionManager created for {exercise.display_name_key}")

    def update(self, pose_data: Any, timestamp: float) -> UIState:
        """
        Updates the session logic based on new pose data.
        Returns the state needed for the UI to render.
        """
        
        current_reps = self.exercise_logic.reps
        feedback = ""
        stage = self.exercise_logic.stage
        keypoints = None

        # Extract keypoints using injected extractor (decoupled from YOLO format)
        has_people, keypoints = self.keypoint_extractor.extract(pose_data)

        # Update Logic only if we are in EXERCISE mode and have a person
        if self.workout_state == "EXERCISE" and has_people:
            analysis = self.exercise_logic.process_frame(keypoints, timestamp)
            current_reps = analysis.reps
            feedback = analysis.correction
            stage = analysis.stage
            
            # Check Set Completion
            if analysis.reps >= self.target_reps:
                self._complete_set()

        return UIState(
            exercise_name=i18n.get(self.exercise_logic.display_name_key),
            reps=current_reps,
            target_reps=self.target_reps,
            current_set=self.current_set if self.current_set <= self.target_sets else self.target_sets,
            target_sets=self.target_sets,
            state=stage,
            feedback_key=feedback,
            workout_state=self.workout_state,
            keypoints=keypoints
        )

    def _complete_set(self):
        logging.info(f"Set {self.current_set} completed.")
        
        # Save set data
        self.session_entity.add_exercise({
            "name": self.exercise_logic.exercise_id,  # Canonical name for DB
            "set_index": self.current_set,
            "reps": self.exercise_logic.reps,
            "config": self.exercise_logic.config
        })
        
        if self.current_set >= self.target_sets:
            self.workout_state = "FINISHED"
            self.end_session()
        else:
            self.workout_state = "REST"
        
        # Reset exercise logic for next set (but keep config)
        self.exercise_logic.reset()

    def handle_user_input(self, action: str) -> None:
        if action == 'CONTINUE' and self.workout_state == "REST":
            self.current_set += 1
            self.workout_state = "EXERCISE"
            logging.info(f"Resuming workout. Starting set {self.current_set}")

    def is_session_finished(self) -> bool:
        return self.workout_state == "FINISHED"

    def end_session(self) -> None:
        if not self.session_entity.end_time:
            self.session_entity.end_session()
            self.db_manager.save_session(self.session_entity)
    
    def save_session(self) -> None:
        # Public method to force save (e.g. on app quit)
        self.end_session()
