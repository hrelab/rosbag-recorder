#!/bin/bash

DEFAULT_TOPICS="[ '/processed/emg', '/processed/imu', '/processed/smg', '/raw_data/delsys', '/raw_data/telemed' ]"
DEFAULT_TOPIC_TYPES="[ 'stretch_sim_interfaces/msg/EmgMsg', 'stretch_sim_interfaces/msg/ImuMsg', 'stretch_sim_interfaces/msg/SmgMsg', 'stretch_sim_interfaces/msg/DelsysMsg', 'stretch_sim_interfaces/msg/SmgMsg' ]"

while true; do
  echo "Enter a tag or key to identify this rosbag:"
  read -r value1
  if [[ -n "$value1" ]]; then
    break
  fi
  echo "Tag/key cannot be empty. Please try again."
done

echo "Use default topics? [Y/n]"
read -r use_default

if [[ "$use_default" =~ ^([nN][oO]|[nN])$ ]]; then
  echo "Enter topics as a comma-separated list, e.g. /topic1,/topic2:"
  read -r topic_input
  topic_input="${topic_input// /}"

  echo "Enter matching topic types as a comma-separated list, e.g. package/msg/Type1,package/msg/Type2:"
  read -r type_input
  type_input="${type_input// /}"

  IFS=',' read -r -a topic_array <<< "$topic_input"
  IFS=',' read -r -a type_array <<< "$type_input"

  if [[ ${#topic_array[@]} -ne ${#type_array[@]} ]]; then
    echo "The number of topics and topic types must match. Using default topics instead."
    topics_param="$DEFAULT_TOPICS"
    types_param="$DEFAULT_TOPIC_TYPES"
  else
    topics_param="["
    for topic in "${topic_array[@]}"; do
      topics_param+=" '$topic',"
    done
    topics_param="${topics_param%,} ]"

    types_param="["
    for topic_type in "${type_array[@]}"; do
      types_param+=" '$topic_type',"
    done
    types_param="${types_param%,} ]"
  fi
else
  topics_param="$DEFAULT_TOPICS"
  types_param="$DEFAULT_TOPIC_TYPES"
fi

ros2 run rosbag_recorder record_rosbag --ros-args \
  -p topics:="$topics_param" \
  -p topic_types:="$types_param" \
  -p output_path:="./data/rosbag/rosbag-${value1}"

