import os
import pandas as pd
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-f", type=str, nargs="+", help="Path to the csv file with OpenFace results")
parser.add_argument("--folder", action="store_true", help="If the path is a folder, run on all files from that folder")
parser.add_argument("--au_names", action="store_true", help="Rename AUs from index to human readable names")
parser.add_argument("--output_folder", default=None, type=str,
                    help="Path to the output folder, by default outputs to the same folder")

AU_PRESENCE_COLUMNS = [
    'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c',
    'AU17_c', 'AU20_c', 'AU23_c', 'AU25_c', 'AU26_c', 'AU28_c', 'AU45_c'
]

AU_INTENSITY_COLUMNS = [
    'AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r',
    'AU17_r', 'AU20_r', 'AU23_r', 'AU25_r', 'AU26_r', 'AU45_r'
]

INDEX_TO_NAME = {
    'AU01_c': 'Inner Brow Raiser',
    'AU02_c': 'Outer Brow Raiser',
    'AU04_c': 'Brow Lowerer',
    'AU05_c': 'Upper Lid Raiser',
    'AU06_c': 'Cheek Raiser',
    'AU07_c': 'Lid Tightener',
    'AU09_c': 'Nose Wrinkler',
    'AU10_c': 'Upper Lip Raiser',
    'AU12_c': 'Lip Corner Puller',
    'AU14_c': 'Dimpler',
    'AU15_c': 'Lip Corner Depressor',
    'AU17_c': 'Chin Raiser',
    'AU20_c': 'Lip Stretcher',
    'AU23_c': 'Lip Tightener',
    'AU25_c': 'Lip Part',
    'AU26_c': 'Jaw Drop',
    'AU28_c': 'Lip Suck',
    'AU45_c': 'Blink',
}


def read_df(fp):
    df = pd.read_csv(fp)
    # Remove empty spaces in column names.
    df.columns = [col.replace(" ", "") for col in df.columns]
    return df


def melt_df(df):
    melted_df = df.melt(id_vars=['frame', 'timestamp'], value_vars=AU_PRESENCE_COLUMNS, var_name='tier',
                        value_name='presence')

    # Filter out the rows where 'presence' is 0
    melted_df = melted_df[melted_df['presence'] == 1]

    # Find consecutive spans of frames for each action unit
    melted_df['consecutive_group'] = (melted_df['frame'].diff() != 1).cumsum()

    # Calculate the start and end time for each action unit
    start_end_df = melted_df.groupby(['tier', 'consecutive_group']).agg(start=('timestamp', 'min'),
                                                                        end=('timestamp', 'max')).reset_index()

    # Merge start and end times back into the dataframe
    final_df = melted_df.merge(start_end_df, on=['tier', 'consecutive_group'])

    # # Remove duplicates and unnecessary columns
    final_df = final_df.drop_duplicates(subset=['tier', 'start', 'end'])
    final_df = final_df[['tier', 'start', 'end']]
    final_df['annotation'] = ""
    return final_df


def process_file(fp, au_names=False, output_folder=None):
    file_name = os.path.basename(fp)
    video_name = os.path.splitext(file_name)[0]
    df = read_df(fp)
    df = melt_df(df)
    if au_names:
        df['tier'] = df['tier'].replace(INDEX_TO_NAME)

    # Save the new table
    if output_folder is not None:
        os.makedirs(output_folder, exist_ok=True)
        output_fp = os.path.join(output_folder, f'{video_name}_aus.csv')
    else:
        output_fp = fp.replace('.csv', '_aus.csv')
    df.to_csv(output_fp)


def main(args):
    if args.folder:
        for folder_path in args.f:
            for fp in os.listdir(folder_path):
                if not fp.endswith('.csv'):
                    continue
                process_file(os.path.join(folder_path, fp), args.au_names, args.output_folder)
    else:
        for fp in args.f:
            process_file(fp, args.au_names, args.output_folder)


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    main(args)
