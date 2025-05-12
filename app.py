import streamlit as st
from pose_extractor import process_video, add_jiggle_physics
from bvh_converter import convert_to_bvh
from datetime import datetime
import os
import time

# ======== CONSTANTS ========
GAME_JOINTS = ["LEFT_SHOULDER", "RIGHT_SHOULDER",
               "LEFT_ELBOW", "RIGHT_ELBOW",
               "LEFT_HIP", "RIGHT_HIP",
               "LEFT_KNEE", "RIGHT_KNEE"]

# ======== 1. Modern Page Config ========
st.set_page_config(
    page_title="MOTION2CODE | AI Movement Converter",
    page_icon="static/images/icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://example.com/help',
        'Report a bug': "https://example.com/bug",
        'About': "# MOTION2CODE\nTurn human movements into executable code"
    }
)

# Visitor counter
if 'visitors' not in st.session_state:
    st.session_state.visitors = 0
st.session_state.visitors += 1

# Save to file (creates visitor_log.txt)
with open("visitor_log.txt", "a") as f:
    f.write(f"{datetime.now()}: Visitor {st.session_state.visitors}\n")

# ===== FIXED CHAT BOT IMPLEMENTATION =====
st.markdown("""
<style>
    /* Floating button - fixed positioning */
    .chatbot-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00b4d8, #0077b6);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 180, 216, 0.3);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        transition: all 0.3s ease;
    }

    .chatbot-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0, 180, 216, 0.4);
    }

    /* Chat container - fixed positioning */
    .chatbot-container {
        position: fixed;
        right: 30px;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 5px 25px rgba(0,0,0,0.2);
        z-index: 9998;
        display: none;
        flex-direction: column;
        border: 1px solid #e0e0e0;
        overflow: hidden;
    }

    .chatbot-container.visible {
        display: flex;
        bottom: 100px;
        top: auto;
    }

    .chatbot-header {
        background: linear-gradient(135deg, #00b4d8, #0077b6);
        color: white;
        padding: 15px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chatbot-close {
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
    }

    .chatbot-messages {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        background: #f9f9f9;
    }

    .message {
        margin-bottom: 15px;
        max-width: 80%;
    }

    .user-message {
        margin-left: auto;
        background: #e3f2fd;
        padding: 10px 15px;
        border-radius: 18px 18px 0 18px;
        text-align: right;
    }

    .bot-message {
        margin-right: auto;
        background: #00b4d8;
        color: white;
        padding: 10px 15px;
        border-radius: 18px 18px 18px 0;
    }

    .chatbot-input-container {
        display: flex;
        padding: 15px;
        background: white;
        border-top: 1px solid #eee;
    }

    .chatbot-input {
        flex: 1;
        padding: 10px 15px;
        border: 1px solid #ddd;
        border-radius: 20px;
        outline: none;
    }

    .chatbot-send {
        margin-left: 10px;
        background: #00b4d8;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0 20px;
        cursor: pointer;
    }
</style>

<div id="chatbotButton" class="chatbot-btn">🤖</div>

<div id="chatbotWindow" class="chatbot-container">
    <div class="chatbot-header">
        Motion2Code Assistant
        <button class="chatbot-close" id="chatbotClose">×</button>
    </div>
    <div class="chatbot-messages" id="chatbotMessages">
        <div class="message bot-message">
            Hello! I can help with Motion2Code questions. Ask me about features or how to use the tool.
        </div>
    </div>
    <div class="chatbot-input-container">
        <input type="text" class="chatbot-input" id="chatbotInput" placeholder="Type your question...">
        <button class="chatbot-send" id="chatbotSend">Send</button>
    </div>
</div>

<script>
// Wait for elements to be available
function whenAvailable() {
    return new Promise(resolve => {
        const check = () => {
            const btn = document.getElementById('chatbotButton');
            const window = document.getElementById('chatbotWindow');
            if (btn && window) resolve({btn, window});
            else setTimeout(check, 100);
        };
        check();
    });
}

whenAvailable().then(({btn, window}) => {
    let isOpen = false;

    // Toggle chat window
    btn.addEventListener('click', () => {
        isOpen = !isOpen;
        if (isOpen) {
            window.classList.add('visible');
            // Position above the button
            const btnRect = btn.getBoundingClientRect();
            window.style.bottom = (window.innerHeight - btnRect.top + 30) + 'px';
        } else {
            window.classList.remove('visible');
        }
    });

    // Close button
    document.getElementById('chatbotClose').addEventListener('click', () => {
        isOpen = false;
        window.classList.remove('visible');
    });

    // Handle sending messages
    function sendMessage() {
        const input = document.getElementById('chatbotInput');
        const messages = document.getElementById('chatbotMessages');

        if (input.value.trim() === '') return;

        // Add user message
        messages.innerHTML += `
            <div class="message user-message">
                ${input.value}
            </div>
        `;

        // Bot responses
        const responses = {
            "what is this": "Motion2Code converts human movements into executable code for robots and games.",
            "how to use": "3 simple steps:<br>1. Upload your movement video<br>2. Select output format (CSV for robots, BVH for games)<br>3. Download the generated code",
            "features": "Main features:<br>- Real-time pose detection<br>- Multiple output formats<br>- No special hardware needed<br>- Works with webcam or uploaded videos",
            "robotics": "For robotics, we generate:<br>- Joint angle CSV files<br>- ROS-compatible trajectories<br>- Arduino servo control code",
            "game": "For game development:<br>- BVH animation files<br>- Unity/Unreal compatible<br>- Full body motion capture",
            "help": "I can help with:<br>- Using the tool<br>- Output formats<br>- Troubleshooting<br>- Example movements"
        };

        let response = "I can answer questions about features, robotics, or game animation. Try asking 'how to use' or 'what formats are supported'.";
        const question = input.value.toLowerCase();

        for (const [keyword, reply] of Object.entries(responses)) {
            if (question.includes(keyword)) {
                response = reply;
                break;
            }
        }

        // Add bot response after delay
        setTimeout(() => {
            messages.innerHTML += `
                <div class="message bot-message">
                    ${response}
                </div>
            `;
            messages.scrollTop = messages.scrollHeight;
        }, 500);

        input.value = '';
        messages.scrollTop = messages.scrollHeight;
    }

    // Send on button click or Enter key
    document.getElementById('chatbotSend').addEventListener('click', sendMessage);
    document.getElementById('chatbotInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Make chat follow scroll
    let lastScroll = window.pageYOffset;
    window.addEventListener('scroll', () => {
        if (isOpen) {
            const currentScroll = window.pageYOffset;
            const scrollDiff = lastScroll - currentScroll;

            const currentBottom = parseInt(window.style.bottom) || 100;
            const newBottom = currentBottom + scrollDiff;

            // Keep within reasonable bounds
            window.style.bottom = Math.max(50, Math.min(newBottom, window.innerHeight - 50)) + 'px';

            lastScroll = currentScroll;
        }
    });
});
</script>
""", unsafe_allow_html=True)

# ======== 2. Professional CSS Injection ========
st.markdown(f"""
<style>
    /* Main colors - professional teal/indigo scheme */
    :root {{
        --primary: #2b5876;
        --secondary: #4e4376;
        --accent: #00b4d8;
        --text: #e2e2e2;
        --dark: #121212;
    }}

    /* Modern gradient background */
    .stApp {{
        background: linear-gradient(135deg, var(--dark) 0%, var(--primary) 100%);
        color: var(--text);
        min-height: 100vh;
    }}

    /* Card-style containers */
    .block-container {{
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
    }}

    /* Professional buttons */
    .stButton>button {{
        background: linear-gradient(90deg, var(--accent) 0%, #0077b6 100%);
        color: white;
        border: none;
        padding: 12px 28px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 180, 216, 0.3);
        transition: all 0.3s ease;
        font-size: 1rem;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 180, 216, 0.4);
    }}

    /* Download buttons */
    .stDownloadButton>button {{
        background: linear-gradient(90deg, #48cae4 0%, #0096c7 100%);
        border-radius: 8px;
    }}

    /* Radio buttons */
    .stRadio > div {{
        flex-direction: row;
        gap: 1rem;
    }}
    .stRadio > div > label {{
        background: rgba(30, 30, 30, 0.7);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }}
    .stRadio > div > label:hover {{
        border-color: var(--accent);
    }}
    .stRadio > div > label[data-baseweb="radio"] {{
        background: rgba(0, 180, 216, 0.2);
        border-color: var(--accent);
    }}

    /* Progress bar */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, var(--accent) 0%, #0077b6 100%);
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: rgba(30, 30, 30, 0.7);
        border-radius: 8px 8px 0 0 !important;
        padding: 1rem 2rem !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        transition: all 0.3s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background: rgba(0, 180, 216, 0.2) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }}

    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(30, 30, 30, 0.5);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--accent);
        border-radius: 4px;
    }}
   /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(30, 30, 30, 0.5);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--accent);
        border-radius: 4px;
    }}

    /* WHITE TEXT FIX (add this last) */
    .stRadio div[role="radiogroup"] label div {{
        color: white !important;
    }}
    .stFileUploader label p {{
        color: white !important;
    }}
    .stCameraInput label p {{
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# ======== 3. Hero Section ========
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("""
    <div style='margin-top: -20px;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem; font-weight: 700;'>MOTION<span style='color: #00b4d8'>2</span>CODE</h1>
        <p style='font-size: 1.5rem; opacity: 0.9; margin-bottom: 2rem;'>Transform <span style='color: #00b4d8'>human movement</span> into <span style='color: #48cae4'>executable data</span></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background: rgba(0, 180, 216, 0.1); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #00b4d8; margin-bottom: 2rem;'>
        <p style='margin-bottom: 0; font-size: 1.1rem;'>✨ <strong>Next-gen motion capture</strong> without expensive hardware. Convert movements directly to robotics code or game animations.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display: flex; gap: 1rem; margin-bottom: 2rem;'>
        <div style='flex: 1; background: rgba(30, 30, 30, 0.7); padding: 1rem; border-radius: 8px; border-bottom: 3px solid #2b5876;'>
            <p style='margin-bottom: 0.5rem;'><span style='color: #00b4d8; font-size: 1.2rem;'>🤖</span></p>
            <p style='margin-bottom: 0; font-size: 0.9rem;'>Robotic motion programming</p>
        </div>
        <div style='flex: 1; background: rgba(30, 30, 30, 0.7); padding: 1rem; border-radius: 8px; border-bottom: 3px solid #4e4376;'>
            <p style='margin-bottom: 0.5rem;'><span style='color: #00b4d8; font-size: 1.2rem;'>🎮</span></p>
            <p style='margin-bottom: 0; font-size: 0.9rem;'>Game character animation</p>
        </div>
        <div style='flex: 1; background: rgba(30, 30, 30, 0.7); padding: 1rem; border-radius: 8px; border-bottom: 3px solid #0077b6;'>
            <p style='margin-bottom: 0.5rem;'><span style='color: #00b4d8; font-size: 1.2rem;'>📱</span></p>
            <p style='margin-bottom: 0; font-size: 0.9rem;'>No special hardware needed</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(30, 30, 30, 0.5); border-radius: 16px; padding: 2rem; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; border: 1px dashed rgba(0, 180, 216, 0.3);'>
        <div style='display: flex; justify-content: center; margin-bottom: 1.5rem;'>
            <div style='position: relative; width: 200px; height: 200px;'>
                <div style='position: absolute; top: 0; left: 50%; transform: translateX(-50%); font-size: 3rem;'>👤</div>
                <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(0deg); font-size: 2rem; color: #00b4d8;'>→</div>
                <div style='position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); display: flex; gap: 1rem;'>
                    <div style='font-size: 2.5rem;'>🤖</div>
                    <div style='font-size: 2.5rem;'>🕹️</div>
                </div>
            </div>
        </div>
        <p style='color: #a1a1a1; font-size: 0.9rem;'>Human movement → Data extraction → Code generation</p>
    </div>
    """, unsafe_allow_html=True)

# ======== 4. Main Conversion Interface ========
st.markdown("---")
st.markdown("""
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;'>
    <h2 style='margin-bottom: 0;'>Movement Conversion</h2>
    <div style='background: rgba(0, 180, 216, 0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; border: 1px solid rgba(0, 180, 216, 0.3);'>
        <span style='color: #00b4d8;'>🔄</span> Real-time processing
    </div>
</div>
""", unsafe_allow_html=True)

# Step 1: User selects mode
user_type = st.radio("What do you want to create?",
                     ("🤖 Robotics Code (CSV)", "🎮 Game Animation (BVH)"),
                     horizontal=True)

# New tracking mode selection
analysis_mode = st.radio(
    "What do you want to track?",
    ("🧍 Human Movement", "🚗 Object Physics"),
    horizontal=True
)

# Input method selection
input_method = st.radio("How to provide movement data?",
                        ("📁 Upload a video", "🎥 Use webcam"),
                        horizontal=True)

video_path = None

if input_method == "📁 Upload a video":
    uploaded_file = st.file_uploader("Drag & drop your video (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])
    if uploaded_file:
        with st.expander("🎬 Video Preview", expanded=True):
            st.video(uploaded_file)
        video_path = "temp_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
else:
    st.write("Position yourself in frame and click the button below")
    cam_feed = st.camera_input("Take a movement video (5-10 seconds recommended)")
    if cam_feed:
        video_path = "temp_video.mp4"
        with open(video_path, "wb") as f:
            f.write(cam_feed.getbuffer())
        st.success("🎥 Video captured! Click 'Process Movement' below")

# Process video if available
if video_path and st.button("🚀 Process Movement", type="primary"):
    with st.spinner('🔍 Analyzing movements with pose estimation...'):
        progress_bar = st.progress(0)

        try:
            for i in range(100):
                time.sleep(0.02)  # Simulate processing
                progress_bar.progress(i + 1)

            if user_type == "🤖 Robotics Code (CSV)":
                joint_data = process_video(
                    video_path,
                    mode="object" if analysis_mode == "🚗 Object Physics" else "human",
                    joints_to_track=None
                )
                st.success('✅ Movement analysis complete!')

                # Show data preview
                with st.expander("📊 Joint Data Preview", expanded=True):
                    st.write("First 3 frames of joint coordinates (X,Y,Z):")
                    st.dataframe(joint_data.head(3))

                    st.markdown("""
                    <style>
                        .stDataFrame {
                            background-color: rgba(30, 30, 30, 0.7);
                            color: white;
                        }
                        .stDataFrame td {
                            border: 1px solid rgba(255, 255, 255, 0.1);
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    # Download button
                    csv = joint_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Robot Joint Data (CSV)",
                        data=csv,
                        file_name="robot_movements.csv",
                        mime="text/csv",
                        help="Contains timestamped joint coordinates for robotic programming"
                    )

                    # Robot simulation
                    st.markdown("---")
                    st.subheader("🤖 Robot Arm Visualization")
                    if st.checkbox("Show joint movement simulation", value=True):
                        st.write("First frame joint positions (normalized coordinates):")
                    cols = st.columns(3)
                    for i, (x, y, z) in enumerate(zip(joint_data.iloc[0][::3],
                                                      joint_data.iloc[0][1::3],
                                                      joint_data.iloc[0][2::3])):
                        with cols[i % 3]:
                            st.metric(
                                label=f"Joint {i + 1}",
                                value=f"X:{x:.2f} Y:{y:.2f}",
                                delta=f"Z:{z:.2f}"
                            )

            else:  # Game Dev Mode
                joint_data = process_video(
                    video_path,
                    mode="object" if analysis_mode == "🚗 Object Physics" else "human",
                    joints_to_track=GAME_JOINTS
                )
                joint_data = add_jiggle_physics(joint_data)
                bvh_data = convert_to_bvh(joint_data)

                st.success('✅ Animation conversion complete!')

                # BVH preview
                with st.expander("📜 BVH File Preview", expanded=False):
                    st.code(bvh_data[:500] + "\n...", language="text")

                st.download_button(
                    label="📥 Download Character Animation (BVH)",
                    data=bvh_data,
                    file_name="character_animation.bvh",
                    mime="text/plain",
                    help="BVH file compatible with Blender, Maya, Unity, and Unreal Engine"
                )

                # Animation info
                st.markdown("""
                <div style='background: rgba(0, 180, 216, 0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 3px solid #00b4d8;'>
                    <p style='margin-bottom: 0.5rem; font-weight: 600;'>🕹️ Game Engine Compatibility</p>
                    <p style='margin-bottom: 0; font-size: 0.9rem;'>This BVH file works with most game engines including Unity, Unreal Engine, Godot, and 3D software like Blender and Maya.</p>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error processing video: {str(e)}")
            st.markdown("""
            <div style='background: rgba(255, 77, 77, 0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 3px solid #ff4d4d;'>
                <p style='margin-bottom: 0;'>Try these fixes:</p>
                <ul style='margin-bottom: 0;'>
                    <li>Ensure good lighting and clear visibility of your body</li>
                    <li>Use videos shorter than 30 seconds</li>
                    <li>Make movements distinct and deliberate</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # Clean up
    if os.path.exists(video_path):
        os.remove(video_path)

# ======== 5. Tutorial Section ========
st.markdown("---")
st.subheader("📚 Tutorials & Guides")

tab1, tab2 = st.tabs(["For Game Developers", "For Robotics Engineers"])
with tab1:
    st.markdown("""
    <div style='display: flex; gap: 2rem; margin-bottom: 2rem;'>
        <div style='flex: 1;'>
            <h4 style='color: #00b4d8; margin-bottom: 1rem;'>🎮 Unity Integration</h4>
            <ol style='padding-left: 1.5rem;'>
                <li>Record your movement (5-10 sec ideal)</li>
                <li>Download the BVH file</li>
                <li>In Unity: Assets → Import New Asset</li>
                <li>Drag onto your character's Animator</li>
            </ol>
        </div>
        <div style='flex: 1;'>
            <h4 style='color: #00b4d8; margin-bottom: 1rem;'>🖥️ Blender Workflow</h4>
            <ol style='padding-left: 1.5rem;'>
                <li>File → Import → Motion Capture (BVH)</li>
                <li>Select your downloaded file</li>
                <li>Apply to any humanoid rig</li>
                <li>Use Graph Editor to refine</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background: rgba(30, 30, 30, 0.7); padding: 1rem; border-radius: 8px;'>
        <p style='margin-bottom: 0.5rem; font-weight: 600;'>💡 Pro Tip</p>
        <p style='margin-bottom: 0;'>For best results in games:</p>
        <ul style='margin-bottom: 0;'>
            <li>Face the camera directly</li>
            <li>Exaggerate movements slightly</li>
            <li>Record in 30+ FPS if possible</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <div style='display: flex; gap: 2rem; margin-bottom: 2rem;'>
        <div style='flex: 1;'>
            <h4 style='color: #00b4d8; margin-bottom: 1rem;'>🤖 Arduino Implementation</h4>
            <ol style='padding-left: 1.5rem;'>
                <li>Download the joint data CSV</li>
                <li>Map columns to your servo motors</li>
                <li>Use interpolation for smooth motion</li>
                <li>Adjust timing with delay() functions</li>
            </ol>
        </div>
        <div style='flex: 1;'>
            <h4 style='color: #00b4d8; margin-bottom: 1rem;'>📈 ROS Integration</h4>
            <ol style='padding-left: 1.5rem;'>
                <li>Import CSV as trajectory points</li>
                <li>Use MoveIt! for motion planning</li>
                <li>Adjust for your robot's kinematics</li>
                <li>Test in simulation first</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background: rgba(30, 30, 30, 0.7); padding: 1rem; border-radius: 8px;'>
        <p style='margin-bottom: 0.5rem; font-weight: 600;'>🔧 Best Practices</p>
        <p style='margin-bottom: 0;'>For robotic applications:</p>
        <ul style='margin-bottom: 0;'>
            <li>Start with simple, slow movements</li>
            <li>Record in consistent lighting</li>
            <li>Scale data to your robot's range of motion</li>
            <li>Add safety limits in your code</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ======== 6. Footer ========
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
with footer_col1:
    st.markdown("""
    <div style='color: #a1a1a1; font-size: 0.9rem;'>
        <p>© 2025 MOTION2CODE | AI Movement Conversion System</p>
        <p style='margin-bottom: 0;'>For research and development purposes. Not for medical or safety-critical applications.</p>
    </div>
    """, unsafe_allow_html=True)
with footer_col2:
    st.markdown("""
    <div style='font-size: 0.9rem;'>
        <p><strong>Resources</strong></p>
        <p style='margin-bottom: 0.5rem;'><a href='#' style='color: #00b4d8; text-decoration: none;'>Documentation</a></p>
        <p style='margin-bottom: 0.5rem;'><a href='#' style='color: #00b4d8; text-decoration: none;'>API Reference</a></p>
        <p style='margin-bottom: 0;'><a href='#' style='color: #00b4d8; text-decoration: none;'>GitHub</a></p>
    </div>
    """, unsafe_allow_html=True)
with footer_col3:
    st.markdown("""
    <div style='font-size: 0.9rem; margin-top: 2rem;'>
        <p><strong>Support</strong></p>
        <p style='margin-bottom: 0.5rem;'>
            ✉️ <a href='mailto:kkidda494@gmail.com' style='color: #00b4d8; text-decoration: none;'>Contact Us</a> (For general questions)
        </p>
        <p style='margin-bottom: 0.5rem;'>
            ⚠️ <a href='mailto:kkidda494@gmail.com?subject=Bug Report' style='color: #00b4d8; text-decoration: none;'>Report Issue</a> (When something breaks)
        </p>
        <p style='margin-bottom: 0;'>
            💡 <a href='mailto:kkidda494@gmail.com?subject=Feedback' style='color: #00b4d8; text-decoration: none;'>Feedback</a> (Suggest improvements)
        </p>
    </div>
    """, unsafe_allow_html=True)


# ===== 3. CHATBOT LOGIC =====
def handle_ai_question(question):
    qa = {
        "what is this": "Motion2Code converts movements to robot/game code.",
        "how to use": "1. Upload video\n2. Select output\n3. Download",
        # Add more Q&A as needed
    }
    question = question.lower()
    return next((v for k,v in qa.items() if k in question),
               "Ask about: features, robotics, or game animation")

if __name__ == "__main__":
    pass
# TODO: Fix chat bot