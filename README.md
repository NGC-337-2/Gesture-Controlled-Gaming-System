# Hill Climb Racing Gesture Controller

A Python-based gesture recognition application that allows you to control the Hill Climb Racing game using hand gestures via your webcam.

## 🎮 Overview

This project uses computer vision and hand tracking to translate hand gestures into keyboard controls for Hill Climb Racing. Make a fist with your right hand to accelerate, left hand to brake, or both hands to use both pedals simultaneously.

## ✨ Features

- **Hand Gesture Recognition**: Uses MediaPipe for robust hand tracking
- **Real-time Control**: Simulates keyboard inputs (Arrow Keys) instantly
- **Visual Feedback**: Custom UI showing current action, FPS, and control status
- **Smoothing Algorithm**: Reduces jitter with action buffering for stable controls
- **Multi-hand Detection**: Supports detecting both left and right hands simultaneously
- **Game-themed UI**: Hill Climb Racing styled interface with pedal visualization

## 🎯 Controls

| Gesture | Action | Keyboard Key |
|---------|--------|--------------|
| 👊 Right Fist | GAS (Accelerate) | Right Arrow → |
| 👊 Left Fist | BRAKE | Left Arrow ← |
| 👊👊 Both Fists | GAS + BRAKE | Both Arrows |
| ✋ Open Hand | IDLE | No Input |

## 📋 Requirements

### Hardware
- Webcam (built-in or external)
- Computer with keyboard input capability

### Software
- Python 3.8 or higher
- Windows OS (for pynput keyboard control)

### Python Dependencies
```
opencv-python
mediapipe
numpy
pynput
```

## 🚀 Installation

1. **Clone or download the project**

2. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to add Python to PATH

3. **Install dependencies**
   ```bash
   pip install opencv-python mediapipe numpy pynput
   ```

4. **Run the application**
   ```bash
   python hill_climb_controller.py
   ```

## 📖 Usage

1. Connect your webcam
2. Run the script: `python hill_climb_controller.py`
3. Wait for camera initialization
4. Open Hill Climb Racing on your PC
5. Make hand gestures to control the game:
   - **Right fist** = Gas
   - **Left fist** = Brake
   - **Both fists** = Both
6. Press **'Q'** to quit the controller

## 🔧 Configuration

### Hand Detection Sensitivity

Modify the `__init__` method in the `HillClimbGestureController` class:

```python
self.hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,  # Lower = more sensitive
    min_tracking_confidence=0.6     # Lower = more responsive
)
```

### Fist Detection Threshold

Adjust the fist detection in `is_fist_closed()` method:

```python
# Change the threshold (default: 3 fingers)
return closed_count >= 3  # Increase to 4 for stricter detection
```

### Camera Settings

Modify the camera initialization in `run()` method:

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Frame width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # Frame height
cap.set(cv2.CAP_PROP_FPS, 30)             # FPS
```

## 🏗️ Project Structure

```
hill_climb_controller.py    # Main application file
├── HillClimbGestureController class
│   ├── Hand detection setup
│   ├── Gesture recognition
│   ├── Keyboard simulation
│   └── UI rendering
└── main() function
```

## 🔨 Technical Details

### Hand Detection
- Uses MediaPipe Hands solution for 21-landmark hand tracking
- Real-time processing at 30 FPS
- Supports 2 hands simultaneously

### Gesture Recognition
- Detects fist gesture by comparing fingertip positions to finger base positions
- Requires 3+ curled fingers to register as a fist
- Smooths action using a deque buffer to reduce jitter

### Keyboard Simulation
- Uses pynput library to simulate key presses
- Right Arrow = Gas
- Left Arrow = Brake
- Proper key release on gesture end

## ⚠️ Troubleshooting

### Camera Issues
- **"Unable to access camera"**: Try changing camera index in `cv2.VideoCapture(0)` to 1 or 2
- **Poor tracking**: Ensure good lighting and clear view of hands

### Detection Issues
- **Fist not detected**: Make a clear fist, keep fingers close together
- **Wrong hand detected**: Ensure your right/left orientation matches the game
- **Jittery controls**: Increase smoothing buffer size in `__init__`

### Keyboard Not Working
- Run as Administrator (some systems require this for keyboard simulation)
- Check if antivirus is blocking pynput

## 📝 License

This project is for educational and personal use.

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) - Google's hand tracking solution
- [OpenCV](https://opencv.org/) - Computer vision library
- [pynput](https://pynput.readthedocs.io/) - Keyboard/Mouse control

---

**Note**: This controller simulates keyboard input and should work with the PC version of Hill Climb Racing. For best results, run the game in windowed mode and ensure the controller window remains focused.

