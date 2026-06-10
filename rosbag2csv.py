from pathlib import Path
from rosbags.dataframe import get_dataframe
from rosbags.highlevel import AnyReader
import pandas as pd
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

bag_path_template = './data/rosbag/rosbag-{}'
msg_path = Path('../../delsys-listener/stretch_sim_interfaces/msg')

typestore = get_typestore(Stores.ROS2_HUMBLE)

raw_delsys_topic = '/raw_data/delsys'
raw_telemed_topic = '/raw_data/telemed'
proc_emg_topic = '/processed/emg'
proc_imu_topic = '/processed/imu'
proc_smg_topic = '/processed/smg'

delsys_cols = ['emg1', 'emg2', 'emg3', 'emg4', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']
emg_cols = ['emg1', 'emg2', 'emg3', 'emg4']
imu_cols = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']
smg_cols = ['smg']

for msg_file in msg_path.glob('*.msg'):
    msg_text = msg_file.read_text()
    msg_name = f'stretch_sim_interfaces/msg/{msg_file.stem}'
    typestore.register(get_types_from_msg(msg_text, msg_name))


def ask_yes_no(prompt, default=True):
    default_str = 'Y/n' if default else 'y/N'
    answer = input(f'{prompt} [{default_str}] ').strip()
    if not answer:
        return default
    return answer.lower() in ('y', 'yes')


def ask_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print('Value cannot be empty. Please try again.')


def expand_list_columns(df, cols):
    expanded_parts = []
    first_col = cols[0]
    max_len = df[first_col].apply(len).max()

    for i in range(max_len):
        for col in cols:
            expanded_parts.append(df[col].apply(lambda x: x[i]).rename(f'{col}-{i+1}'))

    return pd.concat(expanded_parts, axis=1)


def get_df(topic, cols, bag_path):
    with AnyReader([bag_path], default_typestore=typestore) as reader:
        df = get_dataframe(reader, topic, cols)
        return expand_list_columns(df, cols)


def save_csv(df, filename):
    print(df.head())
    df.to_csv(filename, index=False, header=True)


if __name__ == '__main__':
    rosbag_tag = ask_non_empty('Enter the rosbag tag/key to convert: ')
    bag_path = Path(bag_path_template.format(rosbag_tag))

    if not bag_path.exists():
        print(f'Bag path does not exist: {bag_path}')
        raise SystemExit(1)

    use_default = ask_yes_no('Convert all default topics?', default=True)

    convert_raw_dels = convert_raw_tele = convert_proc_emg = convert_proc_imu = convert_proc_smg = False

    if use_default:
        convert_raw_dels = True
        convert_raw_tele = True
        convert_proc_emg = True
        convert_proc_imu = True
        convert_proc_smg = True
    else:
        convert_raw_dels = ask_yes_no('Convert raw Delsys topic?', default=True)
        convert_raw_tele = ask_yes_no('Convert raw Telemed topic?', default=True)
        convert_proc_emg = ask_yes_no('Convert processed EMG topic?', default=True)
        convert_proc_imu = ask_yes_no('Convert processed IMU topic?', default=True)
        convert_proc_smg = ask_yes_no('Convert processed SMG topic?', default=True)

    if not any((convert_raw_dels, convert_raw_tele, convert_proc_emg, convert_proc_imu, convert_proc_smg)):
        print('No conversions selected. Exiting.')
        raise SystemExit(0)

    if convert_raw_dels:
        delsys_df = get_df(raw_delsys_topic, delsys_cols, bag_path)
        save_csv(delsys_df, f'data/csv/{rosbag_tag}_raw_delsys.csv')

    if convert_raw_tele:
        telemed_df = get_df(raw_telemed_topic, smg_cols, bag_path)
        save_csv(telemed_df, f'data/csv/{rosbag_tag}_raw_telemed.csv')

    if convert_proc_emg:
        emg_df = get_df(proc_emg_topic, emg_cols, bag_path)
        save_csv(emg_df, f'data/csv/{rosbag_tag}_proc_emg.csv')

    if convert_proc_imu:
        imu_df = get_df(proc_imu_topic, imu_cols, bag_path)
        save_csv(imu_df, f'data/csv/{rosbag_tag}_proc_imu.csv')

    if convert_proc_smg:
        smg_df = get_df(proc_smg_topic, smg_cols, bag_path)
        save_csv(smg_df, f'data/csv/{rosbag_tag}_proc_smg.csv')
