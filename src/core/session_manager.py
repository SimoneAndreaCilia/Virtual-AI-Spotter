import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.core.factory import ExerciseFactory
from src.core.entities.session import Session
from config.translation_strings import i18n
# Note: Assuming config.translation_strings is where i18n is located based on main.py analysis.

@dataclass
class UIState:
    exercise_name: str
    reps: int
    target_reps: int
    current_set: int
    target_sets: int
    state: str  # "start", "up", "down"
    feedback_key: str
    workout_state: str # "EXERCISE", "REST", "FINISHED"
    keypoints: Any = None

class SessionManager:
    def __init__(self, db_manager, user_id, exercise_name, exercise_config, target_sets, target_reps):
        self.db_manager = db_manager
        self.user_id = user_id
        
        # Config
        self.exercise_name = exercise_name
        self.exercise_config = exercise_config
        self.target_sets = target_sets
        self.target_reps = target_reps
        
        # State
        self.current_set = 1
        self.workout_state = "EXERCISE" # EXERCISE | REST | FINISHED
        
        # Exercise Logic
        self.exercise_logic = ExerciseFactory.create_exercise(exercise_name, exercise_config)
        
        # Session Entity
        self.session_entity = Session(
            user_id=user_id,
            target_sets=target_sets,
            target_reps=target_reps
        )
        logging.info(f"SessionManager created for {exercise_name}")

    def update(self, pose_data, timestamp: float) -> UIState:
        """
        Updates the session logic based on new pose data.
        Returns the state needed for the UI to render.
        """
        
        current_reps = self.exercise_logic.reps
        feedback = ""
        stage = self.exercise_logic.stage
        keypoints = None

        # Extract keypoints availability
        has_people = False
        if pose_data and hasattr(pose_data[0], 'keypoints') and pose_data[0].keypoints is not None:
             if pose_data[0].keypoints.data.shape[0] > 0:
                 has_people = True
                 keypoints = pose_data[0].keypoints.data[0].cpu().numpy()

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
            "name": self.exercise_name,
            "set_index": self.current_set,
            "reps": self.exercise_logic.reps,
            "config": self.exercise_config
        })
        
        if self.current_set >= self.target_sets:
            self.workout_state = "FINISHED"
            self.end_session()
        else:
            self.workout_state = "REST"
        
        # Reset exercise logic for next set (but keep config)
        self.exercise_logic.reset()

    def handle_user_input(self, action: str):
        if action == 'CONTINUE' and self.workout_state == "REST":
            self.current_set += 1
            self.workout_state = "EXERCISE"
            logging.info(f"Resuming workout. Starting set {self.current_set}")

    def is_session_finished(self):
        return self.workout_state == "FINISHED"

    def end_session(self):
        if not self.session_entity.end_time:
            self.session_entity.end_session()
            self.db_manager.save_session(self.session_entity)
    
    def save_session(self):
        # Public method to force save (e.g. on app quit)
        self.end_session()
