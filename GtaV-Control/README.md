# GTA V Hand Gesture Control

This project is maintained by **Gohar Fatima**. It is an external keyboard and mouse controller for the classic PC versions of **GTA Vice City** and **GTA San Andreas**. It does not modify game files, install a mod, inject into the game, or change the game's controls.

The project is distributed under the MIT License. See the root [LICENSE](../LICENSE) for the complete legal notice.

The controller uses MediaPipe hand landmarks directly. It does not require `dataset.csv`, `model.pkl`, or `trainer.py`.

## Setup

Requirements: Windows, Python 3.8, an OpenCV-compatible webcam, and GTA running windowed or borderless.

From this directory:

```powershell
py -3.8 -m venv .venv
.\.venv\Scripts\Activate.ps1
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
python control.py
```

## Gesture mappings

Edit the constants at the top of `config.py` if the game's Controls/Options menu uses a custom layout.

| Gesture | Action | Default |
| --- | --- | --- |
| Index only | Move forward | W |
| Three fingers (middle, ring, pinky) | Move backward | S |
| Pinky only | Turn left | A |
| Middle only | Turn right | D |
| Open palm | Neutral; push holds handbrake | W/S/A/D released; `HANDBRAKE_INPUT` while pushed |
| Two fingers (index and middle) | Jump | Space pulse |
| Thumb only | Enter or exit vehicle | F pulse |
| Index and thumb | Aim mode | No movement |
| Index and thumb plus forward push | Shoot | `SHOOT_INPUT` |
| Closed fist plus forward push | Punch/attack | `ATTACK_INPUT` |
| Index and ring | Crouch | C held |
| Index, middle, and ring | Sprint forward | W + Shift held |
| Thumb and middle | Next weapon | E pulse |
| Thumb and ring | Previous weapon | Z pulse |
| Thumb, index, middle, and ring | Pause | P pulse |

`SHOOT_INPUT` and `ATTACK_INPUT` accept `mouse_left`, `mouse_right`, `space`, or a single keyboard key. Handbrake uses Space by default and can be disabled or remapped.

Vehicle mode is toggled by the thumb-only gesture and shown in the camera overlay. W, S, A, and D are sent individually for acceleration, reverse/brake, left steering, and right steering. No automatic W-plus-steering combination is added. Unclear or missing gestures release all held controls.

The controller sends configured keyboard/mouse input by default. Run `keyboard_test.py` for a safe mapping test; it uses an isolated `InputState` and never sends input. `CAMERA_CONTROL_ENABLED` is off by default and, when enabled, moves the mouse with a deadzone and bounded step.

## Shared and game-specific controls

Both classic games commonly use W/S/A/D for movement, Space for jumping, F for entering or exiting vehicles, and A/D for steering when driving. Defaults can differ by release, platform, language, or a user's custom configuration. Vehicle handbrake, aim, fire, and attack inputs can also differ between keyboard/mouse and controller-oriented layouts.

Verify every mapping in the game's own **Options/Controls** menu, then update `config.py` to match it. This program never changes those settings automatically.

## Window and focus setup

Use windowed or borderless mode and leave the game's resolution unchanged. Start `control.py`, position the separate camera window away from important game UI, then click the game window so it owns keyboard focus. Do not click the camera window while playing. The controller does not use Alt+Tab, Alt+Enter, fullscreen changes, or continuous cursor movement by default. Q is an emergency stop, P pauses the game by default, and ESC exits the controller; emergency stop and exit release every held input.

If the camera or MediaPipe loses the hand, movement keys are released. The same cleanup runs on camera failure, exit, and exceptions.

This project is not affiliated with or endorsed by Rockstar Games.