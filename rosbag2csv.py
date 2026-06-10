from pathlib import Path
from rosbags.dataframe import get_dataframe
from rosbags.highlevel import AnyReader
import pandas as pd
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--tag', default='tag1', help='Tag of rosbag to convert', required=True)
parser.add_argument('--raw_dels', action='store_true', help='Raw Delsys topic')
parser.add_argument('--raw_tele', action='store_true', help='Raw Telemed topic')
parser.add_argument('--proc_emg', action='store_true', help='Processed EMG topic')
parser.add_argument('--proc_imu', action='store_true', help='Processed IMU topic')
parser.add_argument('--proc_smg', action='store_true', help='Processed SMG topic')
args = parser.parse_args()

rosbag_tag = args.tag
bag_path = Path(f'./data/rosbag/rosbag-{rosbag_tag}/')
# bag_path = Path(f'./data/rosbag/rosbag2_2026_03_11-10_02_11/')

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

def expand_list_columns(df, cols):
    expanded_parts = []
    first_col = cols[0]
    max_len = df[first_col].apply(len).max()

    for i in range(max_len):
        for col in cols:
            expanded_parts.append(df[col].apply(lambda x: x[i]).rename(f'{col}-{i+1}'))

    return pd.concat(expanded_parts, axis=1)
def get_df(topic, cols):
    with AnyReader([bag_path], default_typestore=typestore) as reader:
        df = get_dataframe(reader, topic, cols)
        return expand_list_columns(df, cols)

if __name__ == '__main__':
    if args.raw_dels:
        delsys_df = get_df(raw_delsys_topic, delsys_cols)
        print(delsys_df.head())
        delsys_df.to_csv(f'data/csv/{rosbag_tag}_raw_delsys.csv', index=False, header=True)

    if args.raw_tele:
        telemed_df = get_df(raw_telemed_topic, smg_cols)
        print(telemed_df.head())
        telemed_df.to_csv(f'data/csv/{rosbag_tag}_raw_telemed.csv', index=False, header=True)

    if args.proc_emg:
        emg_df = get_df(proc_emg_topic, emg_cols)
        print(emg_df.head())
        emg_df.to_csv(f'data/csv/{rosbag_tag}_proc_emg.csv', index=False, header=True)
        
    if args.proc_imu:
        imu_df = get_df(proc_imu_topic, imu_cols)
        print(imu_df.head())
        imu_df.to_csv(f'data/csv/{rosbag_tag}_proc_imu.csv', index=False, header=True)

    if args.proc_smg:
        smg_df = get_df(proc_smg_topic, smg_cols)
        print(smg_df.head())
        smg_df.to_csv(f'data/csv/{rosbag_tag}_proc_smg.csv', index=False, header=True)
