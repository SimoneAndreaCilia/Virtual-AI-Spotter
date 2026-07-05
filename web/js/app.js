const videoImg = document.getElementById('video-stream');
const bgBlurImg = document.getElementById('bg-video-blur');
const canvas = document.getElementById('skeleton-canvas');
const ctx = canvas.getContext('2d');

const exerciseNameEl = document.getElementById('exercise-name');
const repCounterEl = document.getElementById('rep-counter');
const repLabelEl = document.getElementById('rep-label');
const setDotsContainer = document.getElementById('set-dots-container');

const feedbackBoxEl = document.getElementById('feedback-box');
const feedbackIconEl = document.getElementById('feedback-icon');
const feedbackTextEl = document.getElementById('feedback-text');
const stateIndicatorEl = document.getElementById('state-indicator');

const repRing = document.getElementById('rep-ring');

const overlay = document.getElementById('workout-overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlaySubtitle = document.getElementById('overlay-subtitle');

// Progress ring setup
const ringRadius = repRing.r.baseVal.value;
const ringCircumference = ringRadius * 2 * Math.PI;
repRing.style.strokeDasharray = `${ringCircumference} ${ringCircumference}`;
repRing.style.strokeDashoffset = ringCircumference;

function setProgress(current, total) {
    if (total === 0) return;
    // Don't exceed 100%
    const ratio = Math.min(current / total, 1.0);
    const offset = ringCircumference - ratio * ringCircumference;
    repRing.style.strokeDashoffset = offset;
}

// Resize canvas to match video aspect ratio properly
function resizeCanvas() {
    if (videoImg.naturalWidth && videoImg.naturalHeight) {
        canvas.width = videoImg.naturalWidth;
        canvas.height = videoImg.naturalHeight;
    } else {
        canvas.width = videoImg.clientWidth || 640;
        canvas.height = videoImg.clientHeight || 480;
    }
}
window.addEventListener('resize', resizeCanvas);

const ws = new WebSocket(`ws://${location.host}/ws/stream`);
ws.binaryType = 'blob';

let latestImageBlob = null;
let previousRepCount = 0;
let frameCount = 0;

ws.onmessage = async (event) => {
    if (event.data instanceof Blob) {
        latestImageBlob = event.data;
    } else {
        // It's text (JSON state)
        if (latestImageBlob) {
            const objectURL = URL.createObjectURL(latestImageBlob);
            videoImg.onload = () => {
                // Update blur background every 3 frames for performance
                if (frameCount % 3 === 0) {
                    bgBlurImg.src = objectURL;
                }
                URL.revokeObjectURL(objectURL);
                resizeCanvas();
                const state = JSON.parse(event.data);
                updateDashboard(state);
                drawSkeleton(state.keypoints, state.is_valid);
                frameCount++;
            };
            videoImg.src = objectURL;
            latestImageBlob = null;
        }
    }
};

ws.onclose = () => {
    console.log("WebSocket Closed");
};

function updateDashboard(state) {
    exerciseNameEl.textContent = state.exercise_name;
    repLabelEl.textContent = state.is_time_based ? "Seconds" : "Reps";
    repCounterEl.textContent = `${state.reps}/${state.target_reps}`;
    
    // Update SVG Progress
    setProgress(state.reps, state.target_reps);
    
    // Update Sets Dots
    let dotsHtml = '';
    for (let i = 1; i <= state.target_sets; i++) {
        // if i < current_set, it's complete. 
        // if current_set == target_sets and workout_state == FINISHED, it's all complete.
        let isActive = (i < state.current_set) || (i === state.target_sets && state.workout_state === "FINISHED");
        dotsHtml += `<div class="dot ${isActive ? 'active' : ''}"></div>`;
    }
    setDotsContainer.innerHTML = dotsHtml;

    // Rep micro-animation on change
    if (state.reps > previousRepCount) {
        repCounterEl.classList.add('rep-glow');
        setTimeout(() => repCounterEl.classList.remove('rep-glow'), 300);
    }
    previousRepCount = state.reps;
    
    // Feedback text and color mapping
    feedbackTextEl.textContent = state.feedback_key; 
    
    feedbackBoxEl.className = 'feedback-box'; // reset
    if (state.is_valid) {
        feedbackIconEl.textContent = "✓";
        feedbackBoxEl.classList.add('feedback-green');
    } else {
        feedbackIconEl.textContent = "!";
        feedbackBoxEl.classList.add('feedback-red');
    }
    
    // State pill (Badge)
    if (state.state_display) {
        stateIndicatorEl.textContent = state.state_display.label_key || state.state_display.category;
        
        // Map category to semantic colors
        // categories are usually: start (blue), down (amber), up (green) 
        // This mapping overrides original BGR colors for a unified premium aesthetic
        const category = state.state_display.category.toLowerCase();
        if (category === 'start' || category === 'neutral') {
            stateIndicatorEl.style.backgroundColor = 'var(--accent-blue)';
        } else if (category === 'down' || category === 'transition') {
            stateIndicatorEl.style.backgroundColor = 'var(--accent-amber)';
        } else {
            stateIndicatorEl.style.backgroundColor = 'var(--accent-green)';
        }
    }

    // Workout State overlays
    if (state.workout_state === "REST" || state.workout_state === "FINISHED") {
        overlay.classList.remove('hidden');
        overlayTitle.textContent = state.workout_state === "REST" ? "Rest" : "Finished!";
        overlaySubtitle.textContent = state.workout_state === "REST" ? "Take a breather." : "Great job!";
        
        const btn = document.getElementById('continue-btn');
        btn.textContent = state.workout_state === "REST" ? "Continue" : "Torna alla Home";
        btn.dataset.action = state.workout_state === "REST" ? "continue" : "quit";
    } else {
        overlay.classList.add('hidden');
    }
}

// Draw skeleton matching original OpenCV logic
const POSE_CONNECTIONS = [
    [15, 13], [13, 11], [16, 14], [14, 12], [11, 12], 
    [5, 11], [6, 12], [5, 6], [5, 7], [6, 8], 
    [7, 9], [8, 10], [1, 2], [0, 1], [0, 2], 
    [1, 3], [2, 4], [3, 5], [4, 6]
];

function drawSkeleton(keypoints, isValid) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!keypoints) return;

    // Use semantic colors based on global validity
    const lineColor = isValid ? '#10B981' : '#EF4444'; // Green or Red
    const pointColor = '#3B82F6'; // Blue centers for neutrality
    
    ctx.lineWidth = 4;
    ctx.strokeStyle = lineColor;
    
    // Draw lines
    for (let [i, j] of POSE_CONNECTIONS) {
        const p1 = keypoints[i];
        const p2 = keypoints[j];
        if (p1 && p2 && p1[2] > 0.5 && p2[2] > 0.5) {
            ctx.beginPath();
            ctx.moveTo(p1[0], p1[1]);
            ctx.lineTo(p2[0], p2[1]);
            ctx.stroke();
        }
    }

    // Draw points
    for (let i = 0; i < keypoints.length; i++) {
        const p = keypoints[i];
        if (p && p[2] > 0.5) {
            ctx.beginPath();
            ctx.arc(p[0], p[1], 5, 0, 2 * Math.PI);
            ctx.fillStyle = pointColor; 
            ctx.fill();
            ctx.strokeStyle = '#FFFFFF'; 
            ctx.lineWidth = 2;
            ctx.stroke();
        }
    }
}

// Commands
document.getElementById('quit-btn').addEventListener('click', () => {
    if (confirm("Sei sicuro di voler terminare l'allenamento?")) {
        fetch('/api/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: 'quit'})
        }).then(() => window.location.href = 'index.html');
    }
});

document.getElementById('continue-btn').addEventListener('click', (e) => {
    const action = e.target.dataset.action || 'continue';
    if (action === 'quit') {
        fetch('/api/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: 'quit'})
        }).then(() => window.location.href = 'index.html');
    } else {
        fetch('/api/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: 'continue'})
        });
    }
});
