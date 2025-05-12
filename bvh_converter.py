def convert_to_bvh(joint_data, bvh_header=None):
    """Converts joint data to BVH format for game engines"""
    # BVH header (simplified skeleton)
    bvh = """HIERARCHY
ROOT Hips
  JOINT LeftUpLeg
    End Site
  JOINT RightUpLeg
    End Site
MOTION
Frames: {}\n""".format(len(joint_data))

    # Add motion smoothing (3-frame average)
    smoothed_data = joint_data.rolling(window=3).mean()

    for frame in smoothed_data.values:
        bvh_header += " ".join([f"{val:.6f}" for val in frame]) + "\n"


def convert_to_bvh(joint_data):
    """Convert joint data to BVH format"""
    bvh_template = """HIERARCHY
ROOT Hips
{JOINT_DATA}
MOTION
Frames: {FRAME_COUNT}
Frame Time: 0.033333
{FRAME_DATA}"""

    # Simplified skeleton - adjust as needed
    joint_hierarchy = """
    OFFSET 0 0 0
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT Chest
        OFFSET 0 5 0
        CHANNELS 3 Zrotation Xrotation Yrotation
        JOINT Neck
            OFFSET 0 5 0
            CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT Head
                OFFSET 0 2 0
                CHANNELS 3 Zrotation Xrotation Yrotation
                End Site
                    OFFSET 0 2 0
        JOINT LeftShoulder
            OFFSET -2 5 0
            CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT LeftElbow
                OFFSET -3 0 0
                CHANNELS 3 Zrotation Xrotation Yrotation
                End Site
                    OFFSET -3 0 0
        JOINT RightShoulder
            OFFSET 2 5 0
            CHANNELS 3 Zrotation Xrotation Yrotation
            JOINT RightElbow
                OFFSET 3 0 0
                CHANNELS 3 Zrotation Xrotation Yrotation
                End Site
                    OFFSET 3 0 0"""

    # Convert joint data to BVH frame format
    frame_data = "\n".join([" ".join(map(str, frame)) for frame in joint_data.values])

    return bvh_template.format(
        JOINT_DATA=joint_hierarchy,
        FRAME_COUNT=len(joint_data),
        FRAME_DATA=frame_data
    )