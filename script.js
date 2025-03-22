document.addEventListener('DOMContentLoaded', function() {
    const startCameraBtn = document.getElementById('start-camera');
    const beginAnalysisBtn = document.querySelector('.controls .btn:nth-child(2)');
    const webcamFeed = document.querySelector('.webcam-feed');
    const poseCanvas = document.querySelector('.pose-detection');
    const feedbackContent = document.querySelector('.feedback-content');
    
    let video;
    let poseNet;
    let pose;
    let ctx;
    let isAnalyzing = false;
    
    // Start camera
    startCameraBtn.addEventListener('click', async function() {
        webcamFeed.innerHTML = '';
        
        // Create video element
        video = document.createElement('video');
        video.style.width = '100%';
        video.style.height = '100%';
        webcamFeed.appendChild(video);
        
        // Set up canvas for drawing keypoints
        poseCanvas.width = webcamFeed.offsetWidth;
        poseCanvas.height = webcamFeed.offsetHeight;
        ctx = poseCanvas.getContext('2d');
        
        try {
            // Access webcam
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                feedbackContent.textContent = 'Camera is active. Click "Begin Pose Analysis" to start.';
            };
            
            // Load PoseNet model
            poseNet = await posenet.load({
                architecture: 'MobileNetV1',
                outputStride: 16,
                inputResolution: { width: 640, height: 480 },
                multiplier: 0.75
            });
            
        } catch (error) {
            console.error('Error accessing webcam or loading model:', error);
            feedbackContent.textContent = 'Error: Could not access camera or load pose detection model.';
        }
    });
    
    // Begin pose analysis
    beginAnalysisBtn.addEventListener('click', function() {
        if (!video || !poseNet) {
            feedbackContent.textContent = 'Please activate the camera first.';
            return;
        }
        
        if (!isAnalyzing) {
            isAnalyzing = true;
            feedbackContent.textContent = 'Analyzing your pose... Hold position...';
            detectPose();
        } else {
            isAnalyzing = false;
            feedbackContent.textContent = 'Pose analysis stopped.';
        }
    });
    
    async function detectPose() {
        if (!isAnalyzing) return;
        
        try {
            // Detect poses
            const poses = await poseNet.estimateMultiplePoses(video, {
                flipHorizontal: false,
                maxDetections: 1,
                scoreThreshold: 0.6,
                nmsRadius: 20
            });
            
            if (poses.length > 0) {
                pose = poses[0];
                
                // Clear canvas and draw new pose
                ctx.clearRect(0, 0, poseCanvas.width, poseCanvas.height);
                drawKeypoints(pose.keypoints);
                drawSkeleton(pose.keypoints);
                
                // Analyze pose (this is where the real analysis would happen)
                analyzePose(pose);
            }
            
            // Continue detection loop
            requestAnimationFrame(detectPose);
            
        } catch (error) {
            console.error('Error detecting pose:', error);
            feedbackContent.textContent = 'Error analyzing pose. Please try again.';
            isAnalyzing = false;
        }
    }
    
    function drawKeypoints(keypoints) {
        for (let i = 0; i < keypoints.length; i++) {
            const keypoint = keypoints[i];
            
            if (keypoint.score > 0.5) {
                ctx.beginPath();
                ctx.arc(keypoint.position.x, keypoint.position.y, 5, 0, 2 * Math.PI);
                ctx.fillStyle = 'aqua';
                ctx.fill();
            }
        }
    }
    
    function drawSkeleton(keypoints) {
        // Define connected keypoints for skeleton
        const skeleton = [
            ['nose', 'leftEye'], ['leftEye', 'leftEar'], ['nose', 'rightEye'],
            ['rightEye', 'rightEar'], ['nose', 'leftShoulder'], ['leftShoulder', 'leftElbow'],
            ['leftElbow', 'leftWrist'], ['leftShoulder', 'leftHip'], ['leftHip', 'leftKnee'],
            ['leftKnee', 'leftAnkle'], ['nose', 'rightShoulder'], ['rightShoulder', 'rightElbow'],
            ['rightElbow', 'rightWrist'], ['rightShoulder', 'rightHip'], ['rightHip', 'rightKnee'],
            ['rightKnee', 'rightAnkle']
        ];
        
        // Draw skeleton lines
        ctx.strokeStyle = 'aqua';
        ctx.lineWidth = 2;
        
        skeleton.forEach(([startPoint, endPoint]) => {
            const start = keypoints.find(kp => kp.part === startPoint);
            const end = keypoints.find(kp => kp.part === endPoint);
            
            if (start.score > 0.5 && end.score > 0.5) {
                ctx.beginPath();
                ctx.moveTo(start.position.x, start.position.y);
                ctx.lineTo(end.position.x, end.position.y);
                ctx.stroke();
            }
        });
    }
    
    function analyzePose(pose) {
        // This is where you'd implement actual pose analysis based on the detected keypoints
        // For this example, we'll simulate analysis for a child's pose
        
        // Get relevant keypoints
        const keypoints = {};
        pose.keypoints.forEach(kp => {
            keypoints[kp.part] = {
                position: kp.position,
                score: kp.score
            };
        });
        
        // Simplified analysis (in reality this would be much more complex)
        let feedbackItems = [];
        
        // Check if we have enough data points to analyze
        const requiredParts = ['leftShoulder', 'rightShoulder', 'leftHip', 'rightHip', 'leftKnee', 'rightKnee'];
        const hasAllParts = requiredParts.every(part => 
            keypoints[part] && keypoints[part].score > 0.5
        );
        
        if (!hasAllParts) {
            feedbackContent.innerHTML = '<p>Please ensure your full body is visible in the frame.</p>';
            return;
        }
        
        // Detect if in Child's Pose (very simplified example)
        const isLowPosition = 
            keypoints.leftShoulder.position.y > keypoints.leftHip.position.y &&
            keypoints.rightShoulder.position.y > keypoints.rightHip.position.y;
            
        const kneesAreWide = 
            Math.abs(keypoints.leftKnee.position.x - keypoints.rightKnee.position.x) > 
            Math.abs(keypoints.leftHip.position.x - keypoints.rightHip.position.x);
            
        // Generate feedback
        if (isLowPosition && kneesAreWide) {
            feedbackItems.push('<p><strong>Analyzing "Child\'s Pose":</strong></p>');
            feedbackItems.push('<p>✓ Basic pose detected</p>');
            
            // Check shoulder relaxation
            const shoulderDistance = Math.abs(keypoints.leftShoulder.position.y - keypoints.rightShoulder.position.y);
            if (shoulderDistance > 20) {
                feedbackItems.push('<p>⚠️ Try to keep shoulders level and relaxed</p>');
            } else {
                feedbackItems.push('<p>✓ Shoulders are well positioned</p>');
            }
            
            // Check knee position
            if (kneesAreWide) {
                feedbackItems.push('<p>✓ Knees are properly positioned</p>');
            } else {
                feedbackItems.push('<p>⚠️ Try to widen your knees more</p>');
            }
            
            feedbackItems.push('<p>Overall: Good form. This pose helps reduce menstrual cramps.</p>');
        } else {
            feedbackItems.push('<p>I don\'t recognize this as Child\'s Pose.</p>');
            feedbackItems.push('<p>For Child\'s Pose: kneel on the floor, touch your big toes together, sit on your heels, then lay your torso down between your thighs.</p>');
        }
        
        feedbackContent.innerHTML = feedbackItems.join('');
    }
});