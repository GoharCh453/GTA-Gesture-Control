"""Safe keyboard mapping test; it never sends input to Windows."""

from __future__ import annotations

import time

import config
import control


def main() -> None:
    inputs = control.InputState(send_inputs=False)
    try:
        print("Keyboard test mode: no real keyboard or mouse input will be sent.")
        for gesture in ("left", "right", "backward"):
            inputs.set_movement(gesture)
            inputs.release_inputs((config.LEFT_KEY, config.RIGHT_KEY, config.BACKWARD_KEY))
        inputs.pulse(config.JUMP_KEY, time.monotonic())
        inputs.update_pulses(time.monotonic() + config.PULSE_DURATION)
        inputs.release_all()
        print("Keyboard mapping test complete: left, right, backward, jump.")
    finally:
        inputs.release_all()


if __name__ == "__main__":
    main()