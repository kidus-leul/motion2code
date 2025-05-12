import cv2
import numpy as np




class ObjectTracker:
    def __init__(self):
        """Optimized for Ethiopian hardware"""
        self.prev_points = None
        self.prev_frame = None
        self.last_position = None
        self.fallback_mode = False  # For low-end PCs

    def track(self, frame):
        try:
            # Adaptive resolution for Ethiopian internet
            if frame.shape[1] > 1280:  # If HD
                frame = cv2.resize(frame, (640, 360))

            gray = self._preprocess_frame(frame)

            if self.fallback_mode or cv2.ocl.haveOpenCL() == False:
                return self._cpu_track(gray)

            return self._gpu_track(gray)

        except Exception as e:
            print(f"Tracking error: {str(e)}")
            return {'x': 0, 'y': 0, 'rotation': 0, 'speed': 0}

    def _preprocess_frame(self, frame):
        """Handle low-light Ethiopian videos"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Contrast enhancement for Ethiopian power fluctuations
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _gpu_track(self, gray):
        """GPU-accelerated tracking"""
        features = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=50,  # Reduced for Ethiopian GPUs
            qualityLevel=0.2,
            minDistance=5
        )

class ObjectTracker:
    def __init__(self):
        self.prev_points = None
        self.rotation_history = []

    def track(self, frame):
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect features to track (good for cars/objects)
        features = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.3, minDistance=7)

        if features is not None:
            # Calculate optical flow (movement between frames)
            new_features, status, _ = cv2.calcOpticalFlowPyrLK(
                self.prev_frame if self.prev_points is not None else gray,
                gray,
                self.prev_points,
                None
            )

            # Calculate center point and rotation
            center_x = np.mean(new_features[:, 0])
            center_y = np.mean(new_features[:, 1])
            rotation = self._calculate_rotation(new_features)

            # Store for next frame
            self.prev_points = new_features
            self.prev_frame = gray

            return {
                'x': float(center_x),
                'y': float(center_y),
                'rotation': float(rotation),
                'speed': self._calculate_speed(center_x, center_y)
            }
        return {'x': 0, 'y': 0, 'rotation': 0, 'speed': 0}

    def _calculate_rotation(self, points):
        # Simplified rotation calculation
        return np.std(points[:, 0])  # Higher value = more rotation

    def _calculate_speed(self, x, y):
        if not hasattr(self, 'last_position'):
            self.last_position = (x, y)
            return 0
        dx = x - self.last_position[0]
        dy = y - self.last_position[1]
        self.last_position = (x, y)
        return np.sqrt(dx ** 2 + dy ** 2)

    def _cpu_track(self, gray):
        """Fallback for low-end Ethiopian PCs"""
        # Simplified tracking algorithm
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            (x, y), _ = cv2.minEnclosingCircle(largest)
            return {'x': x, 'y': y, 'rotation': 0, 'speed': 0}
        return {'x': 0, 'y': 0, 'rotation': 0, 'speed': 0}
