#!/bin/bash

while true; do
  echo "To record a rosbag: enter the one identifying key values"
  read -r value1
  if [[ -n "$value1" ]]; then
    break
  fi
done

ros2 run rosbag_recorder record_rosbag --ros-args -p topics:="[ '/processed/emg', '/processed/imu', '/processed/smg', '/raw_data/delsys', '/raw_data/telemed' ]" \
  -p topic_types:="[ 'stretch_sim_interfaces/msg/EmgMsg', 'stretch_sim_interfaces/msg/ImuMsg', 'stretch_sim_interfaces/msg/SmgMsg', 'stretch_sim_interfaces/msg/DelsysMsg', 'stretch_sim_interfaces/msg/SmgMsg'  ]" \
  -p output_path:="./data/rosbag/rosbag-${value1}"

