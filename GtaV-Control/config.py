"""User-editable mappings and recognition settings for classic GTA controls."""

FORWARD_KEY = "w"
BACKWARD_KEY = "s"
LEFT_KEY = "a"
RIGHT_KEY = "d"
JUMP_KEY = "space"
SQUAT_KEY = "c"
SPRINT_KEY = "shift"
ENTER_EXIT_KEY = "f"
EMERGENCY_STOP_KEY = "q"
PAUSE_KEY = "p"
NEXT_WEAPON_KEY = "e"
PREVIOUS_WEAPON_KEY = "z"

# Use mouse_left, mouse_right, space, or one keyboard character.
SHOOT_INPUT = "mouse_left"
ATTACK_INPUT = "mouse_left"
AIM_INPUT = "mouse_right"
HANDBRAKE_INPUT = "space"
HANDBRAKE_ENABLED = True
DEBUG_ACTIONS = True

# Hold gestures: crouch is index + ring; sprint is index + middle + ring.
# Pulses: thumb + middle is next weapon, thumb + ring is previous weapon,
# and thumb + index + middle + ring is pause.
CROUCH_MODE = "hold"
SPRINT_ENABLED = True
PAUSE_ENABLED = True

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_WARMUP_READS = 8
CAMERA_WARMUP_DELAY = 0.08
CAMERA_WINDOW_TITLE = "Classic GTA Hand Controller"
SMOOTHING_FRAMES = 5
MIN_STABLE_FRAMES = 3
FINGER_MARGIN = 0.015
MIN_DETECTION_CONFIDENCE = 0.65
MIN_TRACKING_CONFIDENCE = 0.65
STABILITY_CONFIDENCE = 0.60
PULSE_DURATION = 0.08
PULSE_COOLDOWN = 0.45
ACTION_COOLDOWN = 0.70
PUSH_SCALE_DELTA = 0.08
PUSH_Z_DELTA = 0.025
PUSH_MIN_INTERVAL = 0.20

CAMERA_CONTROL_ENABLED = False
CAMERA_SENSITIVITY = 3.0
CAMERA_DEADZONE = 0.035
CAMERA_MAX_STEP = 18

# Safety: an unknown or missing gesture always releases every held action.
RELEASE_ON_UNKNOWN = True