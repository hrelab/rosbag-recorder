# HRELab ROS 2 Rosbag-Recorder

This folder can be pulled for all custom ROS 2 topic recordings. You will need to change the bash script(s) named `run-recorder.bash` and `rosbag2csv.py` for each set, but the package is completely built and robust.

## Making a New Recording

Use `run-recorder.bash` to choose the rosbag tag/key and optionally enter custom topics and topic types at runtime.

If your project uses different topic names or message types, update the following:

- In `run-recorder.bash`, change `DEFAULT_TOPICS` and `DEFAULT_TOPIC_TYPES` to match your new ROS topic names and message types.
- In `rosbag2csv.py`, update the topic strings (`raw_delsys_topic`, `raw_telemed_topic`, `proc_emg_topic`, `proc_imu_topic`, `proc_smg_topic`) to match your recording.
- Also update the corresponding column lists (`delsys_cols`, `emg_cols`, `imu_cols`, `smg_cols`) so they match the selected message payload fields.

Make sure the number of topics and topic types always stays in sync if you enter custom values interactively. This ensures the conversion logic can read the correct message types and export the right CSV files for your current project.
