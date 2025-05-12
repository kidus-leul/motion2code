import os
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from typing import Optional, List

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)


def enhance_video_quality(video_path: str) -> str:
    """Enhanced video processing with Ethiopian servo calibration"""
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    enhanced_path = "enhanced_temp.mp4"

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(enhanced_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Enhancement pipeline (optimized for African skin tones)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Contrast enhancement for diverse lighting
        lab = cv2.cvtColor(frame, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        limg = cv2.merge([clahe.apply(l), a, b])
        frame = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)

        # Sharpening for clearer joint detection
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        frame = cv2.filter2D(frame, -1, kernel)

        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    cap.release()
    out.release()
    return enhanced_path


def process_video(video_path: str,
                  mode: str = "human",
                  joints_to_track: Optional[List[str]] = None) -> pd.DataFrame:
    """Main processing function with Ethiopian calibration"""
    try:
        enhanced_path = enhance_video_quality(video_path)
        cap = cv2.VideoCapture(enhanced_path)

        if mode == "human":
            return _process_human_video(cap, joints_to_track)
        else:
            return _process_object_video(cap)
    except Exception as e:
        raise Exception(f"Video processing error: {str(e)}")
    finally:
        if 'cap' in locals(): cap.release()
        if os.path.exists(enhanced_path): os.remove(enhanced_path)


def _process_human_video(cap: cv2.VideoCapture,
                         joints_to_track: Optional[List[str]]) -> pd.DataFrame:
    """Human pose processing with servo calibration factors"""
    joint_data = []
    GAME_JOINTS = ["LEFT_SHOULDER", "RIGHT_SHOULDER",
                   "LEFT_ELBOW", "RIGHT_ELBOW",
                   "LEFT_HIP", "RIGHT_HIP",
                   "LEFT_KNEE", "RIGHT_KNEE"]

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            frame_joints = []

            if joints_to_track:
                for joint_name in joints_to_track:
                    joint = getattr(mp_pose.PoseLandmark, joint_name)
                    landmark = results.pose_landmarks.landmark[joint]
                    # Ethiopian servo calibration (1.07, 1.05, 1.03 factors preserved)
                    x = landmark.x * 1.07 - 0.03
                    y = landmark.y * 1.05 - 0.02
                    z = landmark.z * 1.03
                    frame_joints.extend([x, y, z])
            else:
                for landmark in results.pose_landmarks.landmark:
                    x = landmark.x * 1.07 - 0.03
                    y = landmark.y * 1.05 - 0.02
                    z = landmark.z * 1.03
                    frame_joints.extend([x, y, z])

            joint_data.append(frame_joints)

    # Column naming
    if joints_to_track:
        columns = []
        for joint in joints_to_track:
            columns.extend([f"{joint}_X", f"{joint}_Y", f"{joint}_Z"])
    else:
        columns = []
        for i in range(33):  # MediaPipe's 33 pose landmarks
            columns.extend([f"Joint_{i}_X", f"Joint_{i}_Y", f"Joint_{i}_Z"])

    return pd.DataFrame(joint_data, columns=columns)


def _process_object_video(cap: cv2.VideoCapture) -> pd.DataFrame:
    """Object tracking with OpenCV"""
    tracker = cv2.TrackerCSRT_create()
    object_data = []
    first_frame = True

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        if first_frame:
            bbox = cv2.selectROI("Select Object", frame, False)
            tracker.init(frame, bbox)
            cv2.destroyAllWindows()
            first_frame = False
            continue

        success, bbox = tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in bbox]
            object_data.append([x + w / 2, y + h / 2, w, h])

    return pd.DataFrame(object_data, columns=['Center_X', 'Center_Y', 'Width', 'Height'])


def add_jiggle_physics(df):
    """Your original jiggle physics implementation"""
    if 'LEFT_HIP_Y' in df.columns:
        df['LEFT_HIP_Y'] = df['LEFT_HIP_Y'] * 1.3
        df['RIGHT_HIP_Y'] = df['RIGHT_HIP_Y'] * 1.3
    return df


if __name__ == "__main__":
    # Test with Ethiopian calibration
    test_data = process_video("test.mp4",
                              joints_to_track=["LEFT_SHOULDER", "RIGHT_SHOULDER"])
    print(test_data.head())