const videoImg = document.getElementById('video-stream');
const canvas = document.getElementById('skeleton-canvas');
const ctx = canvas.getContext('2d');

const exerciseNameEl = document.getElementById('exercise-name');
const setCounterEl = document.getElementById('set-counter');
const repCounterEl = document.getElementById('rep-counter');
const repLabelEl = document.getElementById('rep-label');
const feedbackTextEl = document.getElementById('feedback-text');
const stateIndicatorEl = document.getElementById('state-indicator');

const overlay = document.getElementById('workout-overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlaySubtitle = document.getElementById('overlay-subtitle');

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

ws.onmessage = async (event) => {
    if (event.data instanceof Blob) {
        latestImageBlob = event.data;
    } else {
        // It's text (JSON state)
        if (latestImageBlob) {
            const objectURL = URL.createObjectURL(latestImageBlob);
            videoImg.onload = () => {
                URL.revokeObjectURL(objectURL);
                resizeCanvas();
                const state = JSON.parse(event.data);
                updateDashboard(state);
                drawSkeleton(state.keypoints);
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
    setCounterEl.textContent = `${state.current_set} / ${state.target_sets}`;
    repLabelEl.textContent = state.is_time_based ? "Seconds" : "Reps";
    
    // Rep micro-animation
    if (state.reps > previousRepCount) {
        repCounterEl.classList.add('rep-glow');
        setTimeout(() => repCounterEl.classList.remove('rep-glow'), 300);
    }
    previousRepCount = state.reps;
    
    repCounterEl.textContent = `${state.reps} / ${state.target_reps}`;
    feedbackTextEl.textContent = state.feedback_key; // Assuming already localized or needs translation
    
    // State indicator
    if (state.state_display) {
        stateIndicatorEl.textContent = state.state_display.category.toUpperCase();
        const [b, g, r] = state.state_display.color;
        stateIndicatorEl.style.backgroundColor = `rgba(${r},${g},${b},0.3)`;
        stateIndicatorEl.style.color = `rgb(${r},${g},${b})`;
    }

    // Workout State overlays
    if (state.workout_state === "REST" || state.workout_state === "FINISHED") {
        overlay.classList.remove('hidden');
        overlayTitle.textContent = state.workout_state === "REST" ? "Rest" : "Finished!";
        overlaySubtitle.textContent = state.workout_state === "REST" ? "Take a breather." : "Great job!";
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

function drawSkeleton(keypoints) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!keypoints) return;

    // Draw lines
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#00FF00'; // Green
    for (let [i, j] of POSE_CONNECTIONS) {
        const p1 = keypoints[i];
        const p2 = keypoints[j];
        if (p1 && p2 && p1[2] > 0.5 && p2[2] > 0.5) {
            ctx.beginPath();
            
            // Map coordinates from frame to canvas
            const scaleX = canvas.width;
            const scaleY = canvas.height;
            // Wait, YOLO keypoints might be already in pixel coordinates.
            // If they are absolute pixel coords, we scale them down to canvas size.
            // Actually, naturalWidth and naturalHeight of image will match frame size.
            // So if canvas is sized to naturalWidth, pixel coords just work.
            // Wait, CSS scales the canvas to object-fit: contain.
            // We should use the natural coords!
            
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
            ctx.fillStyle = '#0000FF'; // Blue centers
            ctx.fill();
            ctx.strokeStyle = '#FFFFFF'; // White border
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    }
}

// Commands
document.getElementById('quit-btn').addEventListener('click', () => {
    fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: 'quit'})
    }).then(() => window.location.href = 'index.html');
});

document.getElementById('continue-btn').addEventListener('click', () => {
    fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: 'continue'})
    });
});
