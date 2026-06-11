#!/bin/bash
set -euo pipefail

DEFAULT_YAML_FILE="topics.yaml"

prompt_non_empty() {
  local prompt="$1"
  local value

  while true; do
    echo "$prompt"
    read -r value
    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return
    fi
    echo "Value cannot be empty. Please try again."
  done
}

is_yes() {
  local answer="$1"
  [[ "$answer" =~ ^([yY][eE][sS]|[yY]|"")$ ]]
}

build_ros_param() {
  local -n items=$1
  local param="["

  for item in "${items[@]}"; do
    param+=" '$item',"
  done
  param="${param%,} ]"
  printf '%s' "$param"
}

parse_yaml_list() {
  local file="$1"
  local key="$2"
  local line

  line=$(grep -E "^\s*${key}\s*:\s*\[" "$file" | head -n 1 || true)
  if [[ -z "$line" ]]; then
    return 1
  fi

  line=${line#*:}
  line=${line#*[}
  line=${line%]*}

  IFS=',' read -r -a raw_items <<< "$line"
  local cleaned
  local items=()

  for raw_item in "${raw_items[@]}"; do
    cleaned="${raw_item##+([[:space:]])}"
    cleaned="${cleaned%%+([[:space:]])}"
    cleaned="${cleaned#\'}"
    cleaned="${cleaned%\'}"
    if [[ -n "$cleaned" ]]; then
      items+=("$cleaned")
    fi
  done

  printf '%s\n' "${items[@]}"
}

collect_ros_topics() {
  local topic
  local ros_topics

  ros_topics=$(ros2 topic list 2>/dev/null || true)
  if [[ -z "$ros_topics" ]]; then
    return 1
  fi

  local topics=()
  local types=()

  while IFS= read -r topic; do
    if [[ -z "$topic" ]]; then
      continue
    fi
    local topic_type
    topic_type=$(ros2 topic type "$topic" 2>/dev/null || true)
    if [[ -n "$topic_type" ]]; then
      topics+=("$topic")
      types+=("$topic_type")
    fi
  done <<< "$ros_topics"

  if [[ ${#topics[@]} -eq 0 ]]; then
    return 1
  fi

  ROS_TOPICS=(${topics[@]})
  ROS_TYPES=(${types[@]})
  return 0
}

parse_yaml_file() {
  local file="$1"
  local tmp_topics
  local tmp_types

  if [[ ! -f "$file" ]]; then
    return 1
  fi

  mapfile -t tmp_topics < <(parse_yaml_list "$file" topics)
  mapfile -t tmp_types < <(parse_yaml_list "$file" topic_types)

  if [[ ${#tmp_topics[@]} -eq 0 ]] || [[ ${#tmp_types[@]} -eq 0 ]] || [[ ${#tmp_topics[@]} -ne ${#tmp_types[@]} ]]; then
    return 1
  fi

  YAML_TOPICS=(${tmp_topics[@]})
  YAML_TYPES=(${tmp_types[@]})
  return 0
}

main() {
  local tag
  local use_default
  local use_yaml
  local yaml_file
  local topics_param
  local types_param

  tag=$(prompt_non_empty "Enter a tag or key to identify this rosbag:")

  echo "Record all currently published topics from ROS? [Y/n]"
  read -r use_default

  if is_yes "$use_default"; then
    if ! collect_ros_topics; then
      echo "Failed to detect ROS topics. Make sure ROS is running and topics are available." >&2
      exit 1
    fi
    topics_param=$(build_ros_param ROS_TOPICS)
    types_param=$(build_ros_param ROS_TYPES)
  else
    echo "Use a YAML file for topics and types? [Y/n]"
    read -r use_yaml

    if is_yes "$use_yaml"; then
      yaml_file="$DEFAULT_YAML_FILE"

      if [[ ! -f "$yaml_file" ]]; then
        echo "YAML file '$yaml_file' not found. Create or update $DEFAULT_YAML_FILE so the script does not need changing." >&2
        exit 1
      fi

      if ! parse_yaml_file "$yaml_file"; then
        echo "Failed to parse YAML file '$yaml_file'. Ensure it contains 'topics: [ ... ]' and 'topic_types: [ ... ]' with matching lengths." >&2
        exit 1
      fi

      topics_param=$(build_ros_param YAML_TOPICS)
      types_param=$(build_ros_param YAML_TYPES)
    else
      local topic_input
      local type_input
      local topic_array
      local type_array

      echo "Enter topics as a comma-separated list, e.g. /topic1,/topic2:"
      read -r topic_input
      topic_input="${topic_input// /}"

      echo "Enter matching topic types as a comma-separated list, e.g. package/msg/Type1,package/msg/Type2:"
      read -r type_input
      type_input="${type_input// /}"

      IFS=',' read -r -a topic_array <<< "$topic_input"
      IFS=',' read -r -a type_array <<< "$type_input"

      if [[ ${#topic_array[@]} -ne ${#type_array[@]} ]]; then
        echo "The number of topics and topic types must match." >&2
        exit 1
      fi

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
  fi

  ros2 run rosbag_recorder record_rosbag --ros-args \
    -p topics:="$topics_param" \
    -p topic_types:="$types_param" \
    -p output_path:"./data/rosbag/rosbag-${tag}"
}

main "$@"

