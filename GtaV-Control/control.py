"""External hand controller for classic PC versions of GTA Vice City and San Andreas."""

from __future__ import annotations

import math
import threading
import time
from collections import Counter, deque
from typing import Any

import cv2
import mediapipe as mp
from pynput.keyboard import Key, Controller as KeyboardController, Listener
from pynput.mouse import Button, Controller as MouseController

import config

keyboard = KeyboardController()
mouse = MouseController()
stop_requested = threading.Event()


def on_key_press(key: Any) -> None:
    if getattr(key, "char", None) == config.EMERGENCY_STOP_KEY or key == Key.esc:
        stop_requested.set()


def distance(first: Any, second: Any) -> float:
    return math.sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)


def finger_states(landmarks: Any) -> tuple[bool, bool, bool, bool, bool]:
    wrist = landmarks[0]
    palm_size = max(distance(landmarks[0], landmarks[9]), 0.001)
    thumb_extended = distance(landmarks[4], wrist) > distance(landmarks[3], wrist) * 1.10
    other_fingers = tuple(
        (landmarks[tip].y < landmarks[pip].y - config.FINGER_MARGIN
         and distance(landmarks[tip], wrist) > palm_size * 1.35)
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18))
    )
    return (thumb_extended, *other_fingers)


def classify_gesture(landmarks: Any) -> str:
    extended = finger_states(landmarks)
    # These poses are deliberately sparse so uncertain poses become unknown.
    if extended == (True, True, True, True, False):
        return "pause"
    if extended == (True, True, False, False, False):
        return "aim"
    if extended == (True, False, True, False, False):
        return "next_weapon"
    if extended == (True, False, False, True, False):
        return "previous_weapon"
    if extended == (False, True, False, False, False):
        return "forward"
    if extended == (False, False, True, False, False):
        return "right"
    if extended == (False, False, False, False, True):
        return "left"
    if extended == (False, False, True, True, True):
        return "backward"
    if extended == (False, True, True, False, False):
        return "jump"
    if extended == (False, True, False, True, False):
        return "crouch"
    if extended == (False, True, True, True, False):
        return "sprint"
    if extended == (True, False, False, False, False):
        return "enter_exit"
    if all(extended):
        return "open_palm"
    if not any(extended):
        return "fist"
    return "unknown"


def input_button(input_name: str) -> tuple[str, Any]:
    if input_name == "mouse_left":
        return ("mouse", Button.left)
    if input_name == "mouse_right":
        return ("mouse", Button.right)
    if input_name == "space":
        return ("keyboard", Key.space)
    special_keys = {
        "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
        "esc": Key.esc, "enter": Key.enter, "tab": Key.tab,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    }
    if input_name in special_keys:
        return ("keyboard", special_keys[input_name])
    if len(input_name) == 1:
        return ("keyboard", input_name.lower())
    raise ValueError(f"Unsupported input mapping: {input_name}")


class InputState:
    def __init__(self, send_inputs: bool = True) -> None:
        self.send_inputs = send_inputs
        self.held_inputs: set[tuple[str, Any]] = set()
        self.pulses: dict[tuple[str, Any], float] = {}
        self.last_pulse: dict[tuple[str, Any], float] = {}
        self.last_action = "none"

    def press(self, input_name: str) -> tuple[str, Any]:
        device, key = input_button(input_name)
        input_key = (device, key)
        if input_key not in self.held_inputs:
            if self.send_inputs:
                (mouse if device == "mouse" else keyboard).press(key)
            self.held_inputs.add(input_key)
            if config.DEBUG_ACTIONS:
                print(f"[KEY PRESSED] {input_name} -> {device}:{key}")
        return input_key

    def release(self, input_key: tuple[str, Any]) -> None:
        if input_key not in self.held_inputs:
            return
        device, key = input_key
        if self.send_inputs:
            (mouse if device == "mouse" else keyboard).release(key)
        self.held_inputs.discard(input_key)
        if config.DEBUG_ACTIONS:
            print(f"[KEY RELEASED] {device}:{key}")

    def release_inputs(self, input_names: tuple[str, ...]) -> None:
        for input_name in input_names:
            try:
                self.release(input_button(input_name))
            except ValueError:
                pass

    def set_movement(self, gesture: str) -> None:
        desired = {
            "forward": {config.FORWARD_KEY},
            "backward": {config.BACKWARD_KEY},
            "left": {config.LEFT_KEY},
            "right": {config.RIGHT_KEY},
        }.get(gesture, ())
        movement_keys = (config.FORWARD_KEY, config.BACKWARD_KEY,
                         config.LEFT_KEY, config.RIGHT_KEY)
        held_movement = {name for device, name in self.held_inputs
                         if device == "keyboard" and name in movement_keys}
        if held_movement == set(desired):
            return
        self.release_inputs(movement_keys)
        if desired and config.DEBUG_ACTIONS:
            print(f"[ACTION CALLED] {gesture} -> {', '.join(sorted(desired))}")
        for key in desired:
            self.press(key)

    def pulse(self, input_name: str, now: float) -> bool:
        input_key = input_button(input_name)
        if now - self.last_pulse.get(input_key, 0.0) < config.PULSE_COOLDOWN:
            return False
        self.release(input_key)
        if config.DEBUG_ACTIONS:
            print(f"[ACTION CALLED] pulse {input_name}")
        self.press(input_name)
        self.pulses[input_key] = now + config.PULSE_DURATION
        self.last_pulse[input_key] = now
        return True

    def update_pulses(self, now: float) -> None:
        for input_key, deadline in tuple(self.pulses.items()):
            if now >= deadline:
                self.release(input_key)
                del self.pulses[input_key]

    def release_all(self) -> None:
        for input_key in tuple(self.held_inputs):
            self.release(input_key)
        self.pulses.clear()
        self.last_action = "all inputs released"

    def hold(self, input_name: str, enabled: bool) -> None:
        if enabled:
            self.press(input_name)
        else:
            self.release(input_button(input_name))

    def action(self, message: str) -> None:
        self.last_action = message
        print(self.last_action)


def draw_status(frame: Any, detected: str, stable: str, stable_count: int,
                     vehicle_mode: bool, push: bool, inputs: InputState) -> None:
    lines = (f"Detected: {detected} | Stable: {stable}",
                 f"Stability: {stable_count}/{config.MIN_STABLE_FRAMES}",
             f"Hand: {'YES' if detected != 'no hand' else 'NO'} | Vehicle: {'ON' if vehicle_mode else 'OFF'}",
             f"Push: {'YES' if push else 'NO'} | Sprint: {'ON' if stable == 'sprint' else 'OFF'} | Crouch: {'ON' if stable == 'crouch' else 'OFF'}",
             f"Aim: {'ON' if stable == 'aim' else 'OFF'} | Last: {inputs.last_action}",
             "Q: emergency stop | ESC: exit")
    for index, text in enumerate(lines):
        cv2.putText(frame, text, (10, 28 + index * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                    (0, 220, 0) if index < 2 else (0, 220, 220), 2)


def move_camera(previous: tuple[float, float] | None, wrist: Any,
                gesture: str) -> tuple[float, float]:
    current = (wrist.x, wrist.y)
    if (previous is None or not config.CAMERA_CONTROL_ENABLED or gesture == "aim"):
        return current
    delta_x = current[0] - previous[0]
    delta_y = current[1] - previous[1]
    if max(abs(delta_x), abs(delta_y)) < config.CAMERA_DEADZONE:
        return current
    step_x = max(-config.CAMERA_MAX_STEP, min(config.CAMERA_MAX_STEP,
                                             round(delta_x * config.CAMERA_SENSITIVITY * 100)))
    step_y = max(-config.CAMERA_MAX_STEP, min(config.CAMERA_MAX_STEP,
                                               round(delta_y * config.CAMERA_SENSITIVITY * 100)))
    mouse.move(step_x, step_y)
    return current


def _probe_camera(index: int, backend: int, width: int, height: int) -> tuple[Any, Any] | None:
    camera = cv2.VideoCapture(index, backend)
    if not camera.isOpened():
        camera.release()
        return None

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    for _ in range(config.CAMERA_WARMUP_READS):
        success, frame = camera.read()
        if success and frame is not None and getattr(frame, "size", 0) > 0:
            return camera, frame
        time.sleep(config.CAMERA_WARMUP_DELAY)
    camera.release()
    return None


def open_camera() -> tuple[Any, int, str, Any]:
    """Return the first camera/backend/resolution that produces a real frame."""
    indexes = list(dict.fromkeys((config.CAMERA_INDEX, 0, 1, 2, 3, 4)))
    resolutions = ((640, 480), (1280, 720))
    backends = (("DirectShow", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF),
                ("default", cv2.CAP_ANY))
    previous_log_level = cv2.getLogLevel() if hasattr(cv2, "getLogLevel") else None
    if hasattr(cv2, "setLogLevel"):
        cv2.setLogLevel(0)
    try:
        for backend_name, backend in backends:
            for index in indexes:
                for width, height in resolutions:
                    result = _probe_camera(index, backend, width, height)
                    if result is not None:
                        camera, frame = result
                        print(f"Using {backend_name} camera index {index} at {width}x{height}.")
                        return camera, index, backend_name, frame
    finally:
        if previous_log_level is not None:
            cv2.setLogLevel(previous_log_level)

    raise RuntimeError(
        "No usable camera found. Tested DirectShow, MSMF, and the default backend "
        "at indexes 0-4 with 640x480 and 1280x720. Check Windows camera privacy "
        "settings, close applications using the webcam, and verify the camera driver."
    )


def run() -> None:
    stop_requested.clear()
    inputs = InputState()
    vehicle_mode = False
    gesture_history: deque[str] = deque(maxlen=config.SMOOTHING_FRAMES)
    current_gesture = "unknown"
    previous_scale = 0.0
    previous_z = 0.0
    push_latched = False
    last_push_time = 0.0
    previous_wrist: tuple[float, float] | None = None
    crouch_latched = False
    last_detected_gesture = "no hand"
    camera, selected_camera_index, selected_backend, first_frame = open_camera()
    print(f"Camera ready at index {selected_camera_index} using {selected_backend}.")
    hand_tracker = mp.solutions.hands.Hands(max_num_hands=1, model_complexity=0,
        min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE)
    drawer = mp.solutions.drawing_utils
    listener = Listener(on_press=on_key_press)
    listener.start()

    try:
        while not stop_requested.is_set():
            if first_frame is not None:
                frame = first_frame
                first_frame = None
                success = True
            else:
                success, frame = camera.read()
            now = time.monotonic()
            inputs.update_pulses(now)
            if not success:
                inputs.release_all()
                previous_scale = 0.0
                previous_wrist = None
                gesture_history.clear()
                current_gesture = "unknown"
                crouch_latched = False
                stop_requested.set()
                print("Camera frame read failed; stopping safely.")
                break

            frame = cv2.flip(frame, 1)
            results = hand_tracker.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            detected_gesture = "no hand"
            push = False
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                landmarks = hand.landmark
                detected_gesture = classify_gesture(landmarks)
                if config.DEBUG_ACTIONS and detected_gesture != last_detected_gesture:
                    print(f"[GESTURE DETECTED] {detected_gesture}")
                    last_detected_gesture = detected_gesture
                previous_wrist = move_camera(previous_wrist, landmarks[0], current_gesture)
                scale = distance(landmarks[0], landmarks[9])
                push = previous_scale > 0 and (scale > previous_scale * (1 + config.PUSH_SCALE_DELTA)
                                                or landmarks[0].z < previous_z - config.PUSH_Z_DELTA)
                previous_scale, previous_z = scale, landmarks[0].z
                drawer.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            else:
                previous_scale = 0.0
                previous_wrist = None
                gesture_history.clear()
                current_gesture = "unknown"
                crouch_latched = False
                inputs.release_all()

            if detected_gesture != "no hand":
                gesture_history.append(detected_gesture)
            stable_gesture, stable_count = (Counter(gesture_history).most_common(1)[0]
                                            if gesture_history else ("unknown", 0))
            if stable_count >= config.MIN_STABLE_FRAMES:
                if stable_gesture != current_gesture:
                    current_gesture = stable_gesture
                    if config.DEBUG_ACTIONS:
                        print(f"[GESTURE STABLE] {current_gesture} ({stable_count} frames)")
                    push_latched = False
                    if current_gesture == "crouch" and config.CROUCH_MODE == "toggle":
                        crouch_latched = not crouch_latched
                    elif current_gesture == "unknown":
                        crouch_latched = False
                    if current_gesture in ("enter_exit", "jump", "next_weapon", "previous_weapon", "pause"):
                        inputs.set_movement("unknown")
                    if current_gesture == "enter_exit":
                        if inputs.pulse(config.ENTER_EXIT_KEY, now):
                            vehicle_mode = not vehicle_mode
                            inputs.action("enter/exit")
                    elif current_gesture == "jump":
                        inputs.pulse(config.JUMP_KEY, now)
                        inputs.action("jump")
                    elif current_gesture == "next_weapon":
                        inputs.pulse(config.NEXT_WEAPON_KEY, now)
                        inputs.action("next weapon")
                    elif current_gesture == "previous_weapon":
                        inputs.pulse(config.PREVIOUS_WEAPON_KEY, now)
                        inputs.action("previous weapon")
                    elif current_gesture == "pause" and config.PAUSE_ENABLED:
                        inputs.pulse(config.PAUSE_KEY, now)
                        inputs.action("pause")

                if current_gesture in ("forward", "backward", "left", "right", "sprint"):
                    inputs.set_movement(current_gesture)
                else:
                    inputs.set_movement("unknown")
                inputs.hold(config.AIM_INPUT, current_gesture == "aim")
                crouch_active = (current_gesture == "crouch" if config.CROUCH_MODE == "hold"
                                 else crouch_latched)
                inputs.hold(config.SQUAT_KEY, crouch_active)
                inputs.hold(config.SPRINT_KEY, current_gesture == "sprint" and config.SPRINT_ENABLED)
                inputs.hold(config.HANDBRAKE_INPUT, current_gesture == "open_palm" and push and config.HANDBRAKE_ENABLED)

                if push and not push_latched and now - last_push_time >= config.PUSH_MIN_INTERVAL:
                    if current_gesture == "aim":
                        inputs.pulse(config.SHOOT_INPUT, now)
                        inputs.action("shoot")
                    elif current_gesture == "fist":
                        inputs.pulse(config.ATTACK_INPUT, now)
                        inputs.action("punch/attack")
                    last_push_time = now
                push_latched = push

            draw_status(frame, detected_gesture, current_gesture, stable_count,
                        vehicle_mode, push, inputs)
            cv2.imshow(config.CAMERA_WINDOW_TITLE, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                stop_requested.set()
    finally:
        inputs.release_all()
        listener.stop()
        camera.release()
        hand_tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()