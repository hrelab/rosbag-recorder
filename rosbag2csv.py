#!/usr/bin/env python3
"""Convert ROS 2 bags to CSV files without hardcoded topic schemas."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_types_from_msg, get_typestore


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_SRC = SCRIPT_DIR.parent
DEFAULT_BAG_DIRS = (
    Path.cwd() / 'data' / 'rosbag',
    SCRIPT_DIR / 'data' / 'rosbag',
    SCRIPT_DIR.parents[2] / 'data' / 'rosbag',
)
DEFAULT_OUTPUT_DIR = Path.cwd() / 'data' / 'csv'


def build_typestore():
    typestore = get_typestore(Stores.ROS2_HUMBLE)

    for msg_file in WORKSPACE_SRC.glob('*/msg/*.msg'):
        package_name = msg_file.parents[1].name
        msg_name = f'{package_name}/msg/{msg_file.stem}'
        typestore.register(get_types_from_msg(msg_file.read_text(), msg_name))

    return typestore


def find_bag_path(bag: str | None) -> Path:
    if bag:
        bag_path = Path(bag).expanduser()
        if bag_path.exists():
            return bag_path

        for bag_dir in DEFAULT_BAG_DIRS:
            candidate = bag_dir / bag
            if candidate.exists():
                return candidate

        raise FileNotFoundError(f'Could not find bag: {bag}')

    candidates = []
    for bag_dir in DEFAULT_BAG_DIRS:
        if not bag_dir.exists():
            continue
        candidates.extend(path for path in bag_dir.iterdir() if (path / 'metadata.yaml').exists())

    if not candidates:
        searched = ', '.join(str(path) for path in DEFAULT_BAG_DIRS)
        raise FileNotFoundError(f'No ROS bag directories found. Searched: {searched}')

    return max(candidates, key=lambda path: (path / 'metadata.yaml').stat().st_mtime)


def sanitize_topic_name(topic: str) -> str:
    name = topic.strip('/').replace('/', '_')
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', name) or 'root'


def is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str, bytes))


def flatten_value(value: Any, prefix: str = '') -> dict[str, Any]:
    if is_scalar(value):
        return {prefix: value}

    if is_dataclass(value):
        flat = {}
        for field in fields(value):
            field_name = f'{prefix}.{field.name}' if prefix else field.name
            flat.update(flatten_value(getattr(value, field.name), field_name))
        return flat

    if isinstance(value, (list, tuple)):
        flat = {}
        for index, item in enumerate(value):
            item_name = f'{prefix}.{index}' if prefix else str(index)
            flat.update(flatten_value(item, item_name))
        return flat

    if isinstance(value, Iterable) and not isinstance(value, (dict, str, bytes)):
        return flatten_value(list(value), prefix)

    if hasattr(value, '__dict__'):
        flat = {}
        for key, item in vars(value).items():
            if key.startswith('_'):
                continue
            item_name = f'{prefix}.{key}' if prefix else key
            flat.update(flatten_value(item, item_name))
        return flat

    return {prefix: value}


def should_include_column(column_name: str) -> bool:
    if column_name == 'timestamp_ns':
        return True
    lower_name = column_name.lower()
    if '__msg' in lower_name:
        return False
    if column_name == 'header' or column_name.startswith('header.'):
        return False
    return True


def rows_for_topic(reader: AnyReader, topic: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    columns = {'timestamp_ns'}
    connections = [connection for connection in reader.connections if connection.topic == topic]

    for connection, timestamp, rawdata in reader.messages(connections=connections):
        msg = reader.deserialize(rawdata, connection.msgtype)
        row = {'timestamp_ns': timestamp}
        row.update(
            {key: value for key, value in flatten_value(msg).items() if should_include_column(key)}
        )
        rows.append(row)
        columns.update(row.keys())

    ordered_columns = ['timestamp_ns'] + sorted(column for column in columns if column != 'timestamp_ns')
    return rows, ordered_columns


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def convert_bag(bag_path: Path, output_dir: Path, topic_filter: set[str] | None = None) -> None:
    typestore = build_typestore()

    with AnyReader([bag_path], default_typestore=typestore) as reader:
        topics = sorted({connection.topic for connection in reader.connections})
        if topic_filter:
            topics = [topic for topic in topics if topic in topic_filter]

        if not topics:
            print('No matching topics found.')
            return

        bag_output_dir = output_dir / bag_path.name
        for topic in topics:
            rows, columns = rows_for_topic(reader, topic)
            csv_path = bag_output_dir / f'{sanitize_topic_name(topic)}.csv'
            write_csv(csv_path, rows, columns)
            print(f'Wrote {len(rows)} rows: {csv_path}')


def main() -> None:
    bag_name = input(
        'Enter a bag directory or bag name under data/rosbag (leave blank to use the newest bag): '
    ).strip()
    bag_path = find_bag_path(bag_name or None)
    output_dir = DEFAULT_OUTPUT_DIR.expanduser()

    print(f'Converting bag: {bag_path}')
    convert_bag(bag_path, output_dir)


if __name__ == '__main__':
    main()
