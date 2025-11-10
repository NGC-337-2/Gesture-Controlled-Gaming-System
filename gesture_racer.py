import cv2
import mediapipe as mp
import numpy as np
import math
from pynput.keyboard import Controller, Key
import time
from collections import deque

# Initialize keyboard controller
keyboard = Controller()

# MediaPipe Hand Detection Setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class HillClimbGestureController:
    """Gesture controller optimized for Hill Climb Racing"""
    
    def __init__(self):
        # Hand detection configuration
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        
        # Control state
        self.current_action = "IDLE"
        self.gas_active = False
        self.brake_active = False
        
        # Smoothing buffers
        self.action_buffer = deque(maxlen=3)
        self.left_hand_buffer = deque(maxlen=3)
        self.right_hand_buffer = deque(maxlen=3)
        
        # Visual feedback colors
        self.colors = {
            'gas': (0, 255, 0),      # Green
            'brake': (0, 0, 255),    # Red
            'both': (0, 255, 255),   # Yellow
            'idle': (128, 128, 128)  # Gray
        }
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Key press tracking
        self.last_gas_state = False
        self.last_brake_state = False
        
    def get_hand_label(self, results, hand_index):
        """Determine if hand is left or right"""
        if results.multi_handedness:
            return results.multi_handedness[hand_index].classification[0].label
        return "Unknown"
    
    def is_fist_closed(self, hand_landmarks):
        """
        Detect if hand is making a fist (fingers curled)
        Compares finger tip positions to their base positions
        """
        # Get fingertip and base landmarks
        fingers = [
            (mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_MCP),
            (mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_MCP),
            (mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_MCP),
            (mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_MCP)
        ]
        
        closed_count = 0
        for tip, base in fingers:
            tip_pos = hand_landmarks.landmark[tip]
            base_pos = hand_landmarks.landmark[base]
            
            # If tip is below base (or very close), finger is curled
            if tip_pos.y >= base_pos.y - 0.03:
                closed_count += 1
        
        # Consider fist closed if 3+ fingers are curled
        return closed_count >= 3
    
    def determine_action(self, results):
        """
        Determine Hill Climb Racing action based on hand visibility
        
        Controls:
        - Right hand visible (fist) = GAS (Right Arrow / Up Arrow)
        - Left hand visible (fist) = BRAKE (Left Arrow / Down Arrow)
        - Both hands visible = BOTH (Both pedals pressed)
        - No hands = IDLE (no input)
        """
        if not results.multi_hand_landmarks:
            return "IDLE", False, False
        
        left_hand_visible = False
        right_hand_visible = False
        
        # Check each detected hand
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            hand_label = self.get_hand_label(results, idx)
            is_fist = self.is_fist_closed(hand_landmarks)
            
            if hand_label == "Right" and is_fist:
                right_hand_visible = True
            elif hand_label == "Left" and is_fist:
                left_hand_visible = True
        
        # Determine action
        if right_hand_visible and left_hand_visible:
            return "BOTH", True, True
        elif right_hand_visible:
            return "GAS", True, False
        elif left_hand_visible:
            return "BRAKE", False, True
        else:
            return "IDLE", False, False
    
    def smooth_action(self, action, gas, brake):
        """Apply smoothing to reduce jitter"""
        self.action_buffer.append(action)
        self.left_hand_buffer.append(brake)
        self.right_hand_buffer.append(gas)
        
        # Most common action
        smooth_action = max(set(self.action_buffer), 
                           key=self.action_buffer.count)
        
        # Majority vote for gas and brake
        smooth_gas = sum(self.right_hand_buffer) > len(self.right_hand_buffer) / 2
        smooth_brake = sum(self.left_hand_buffer) > len(self.left_hand_buffer) / 2
        
        return smooth_action, smooth_gas, smooth_brake
    
    def simulate_keyboard_input(self, gas_active, brake_active):
        """
        Simulate keyboard inputs for Hill Climb Racing
        Right Arrow = Gas, Left Arrow = Brake (standard PC controls)
        """
        try:
            # Handle GAS (Right Arrow)
            if gas_active and not self.last_gas_state:
                keyboard.press(Key.right)
            elif not gas_active and self.last_gas_state:
                keyboard.release(Key.right)
            
            # Handle BRAKE (Left Arrow)
            if brake_active and not self.last_brake_state:
                keyboard.press(Key.left)
            elif not brake_active and self.last_brake_state:
                keyboard.release(Key.left)
                
        except Exception as e:
            print(f"⚠️ Keyboard error: {e}")
        
        self.last_gas_state = gas_active
        self.last_brake_state = brake_active
    
    def draw_ui(self, image, action, gas_active, brake_active, results):
        """Draw Hill Climb Racing themed UI overlay"""
        h, w, _ = image.shape
        
        # Draw hand landmarks with custom colors
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_label = self.get_hand_label(results, idx)
                
                # Color based on hand type
                if hand_label == "Right":
                    landmark_color = self.colors['gas']
                    connection_color = self.colors['gas']
                else:
                    landmark_color = self.colors['brake']
                    connection_color = self.colors['brake']
                
                # Draw landmarks
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=landmark_color, thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=connection_color, thickness=2)
                )
        
        # Status panel with semi-transparent background
        panel_h = 180
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Game title
        cv2.putText(image, "HILL CLIMB RACING", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 200, 0), 3)
        
        # Current action with color
        color = self.colors.get(action.lower(), self.colors['idle'])
        action_text = f"ACTION: {action}"
        cv2.putText(image, action_text, (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        # FPS counter
        fps_text = f"FPS: {int(self.fps)}"
        cv2.putText(image, fps_text, (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Active controls indicator
        controls_text = f"GAS: {'ON' if gas_active else 'OFF'}  |  BRAKE: {'ON' if brake_active else 'OFF'}"
        cv2.putText(image, controls_text, (20, 155),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Pedal visualization (bottom center)
        pedal_y = h - 120
        pedal_spacing = 120
        center_x = w // 2
        
        # Gas pedal (right)
        gas_color = self.colors['gas'] if gas_active else (50, 50, 50)
        gas_x = center_x + pedal_spacing // 2
        cv2.rectangle(image, (gas_x - 40, pedal_y - 60), 
                     (gas_x + 40, pedal_y + 20), gas_color, -1)
        cv2.rectangle(image, (gas_x - 40, pedal_y - 60), 
                     (gas_x + 40, pedal_y + 20), (255, 255, 255), 2)
        cv2.putText(image, "GAS", (gas_x - 30, pedal_y - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(image, "→", (gas_x - 15, pedal_y + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # Brake pedal (left)
        brake_color = self.colors['brake'] if brake_active else (50, 50, 50)
        brake_x = center_x - pedal_spacing // 2
        cv2.rectangle(image, (brake_x - 40, pedal_y - 60), 
                     (brake_x + 40, pedal_y + 20), brake_color, -1)
        cv2.rectangle(image, (brake_x - 40, pedal_y - 60), 
                     (brake_x + 40, pedal_y + 20), (255, 255, 255), 2)
        cv2.putText(image, "BRAKE", (brake_x - 38, pedal_y - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, "←", (brake_x - 15, pedal_y + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # Instructions box (bottom left)
        instructions = [
            "CONTROLS:",
            "Right Fist = GAS",
            "Left Fist = BRAKE",
            "Both Fists = BOTH",
            "",
            "Press 'Q' to Quit"
        ]
        
        inst_y = h - 200
        inst_bg = image.copy()
        cv2.rectangle(inst_bg, (10, inst_y - 30), (280, inst_y + 120), (0, 0, 0), -1)
        cv2.addWeighted(inst_bg, 0.7, image, 0.3, 0, image)
        
        for i, instruction in enumerate(instructions):
            font_scale = 0.7 if i == 0 else 0.5
            thickness = 2 if i == 0 else 1
            color = (255, 200, 0) if i == 0 else (200, 200, 200)
            
            cv2.putText(image, instruction, (20, inst_y + i*22),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        
        return image
    
    def update_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self):
        """Main control loop"""
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            print("❌ ERROR: Unable to access camera. Try index 1 or 2.")
            return

        print("=" * 70)
        print("🏔️  HILL CLIMB RACING - GESTURE CONTROLLER  🏔️")
        print("=" * 70)
        print("\n📸 Camera initialized successfully!")
        print("\n🎮 CONTROLS:")
        print("  👊 Right Fist (closed hand) → GAS (Right Arrow)")
        print("  👊 Left Fist (closed hand) → BRAKE (Left Arrow)")
        print("  👊👊 Both Fists → GAS + BRAKE")
        print("\n⌨️  Simulated Keys: Right Arrow (gas), Left Arrow (brake)")
        print("\n💡 TIP: Make a clear FIST gesture (close your hand firmly)")
        print("\n❌ Press 'Q' to quit\n")
        print("=" * 70)

        try:
            empty_frame_count = 0

            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    empty_frame_count += 1
                    if empty_frame_count > 30:
                        print("❌ ERROR: Camera feed failed. Exiting...")
                        break
                    time.sleep(0.1)
                    continue
                else:
                    empty_frame_count = 0

                # Process frame
                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = self.hands.process(image_rgb)
                image_rgb.flags.writeable = True
                image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

                # Determine action and control state
                action, gas, brake = self.determine_action(results)
                action, gas, brake = self.smooth_action(action, gas, brake)
                
                # Update control state
                self.current_action = action
                self.gas_active = gas
                self.brake_active = brake
                
                # Send keyboard commands
                self.simulate_keyboard_input(gas, brake)
                
                # Draw UI
                image = self.draw_ui(image, action, gas, brake, results)
                self.update_fps()

                cv2.imshow('Hill Climb Racing - Gesture Controller', image)

                # Console output every 30 frames
                if self.frame_count % 30 == 0:
                    gas_status = "✓" if gas else "✗"
                    brake_status = "✓" if brake else "✗"
                    print(f"🎯 {action:8} | Gas:{gas_status} Brake:{brake_status} | FPS: {int(self.fps)}")

                if cv2.waitKey(5) & 0xFF == ord('q'):
                    print("\n🛑 Shutting down...")
                    break

        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")

        finally:
            # Cleanup
            self.hands.close()
            cap.release()
            cv2.destroyAllWindows()
            
            # Release all keys
            try:
                keyboard.release(Key.right)
                keyboard.release(Key.left)
            except:
                pass
            
            print("✅ Hill Climb Racing Gesture Controller terminated!")
            print("=" * 70)


def main():
    """Entry point"""
    controller = HillClimbGestureController()
    controller.run()


if __name__ == "__main__":
    main()