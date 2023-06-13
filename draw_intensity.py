import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-f", type=str, nargs="+", help="Path to the csv file with OpenFace results")
parser.add_argument("--folder", action="store_true", help="If the path is a folder, run on all files from that folder")
parser.add_argument("--output_folder", type=str, default=None, help="Path to the output folder, by default outputs to the same folder")
parser.add_argument("--aus", type=int, nargs="*", help="Which Aus to plot, if none provided, will plot all")
parser.add_argument("--width", default=8, type=float,
                    help="Width of the pictures")
parser.add_argument("--height", default=4, type=float,
                    help="Height of the pictures")

AU_PRESENCE_COLUMNS = [
    'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c',
    'AU17_c', 'AU20_c', 'AU23_c', 'AU25_c', 'AU26_c', 'AU28_c', 'AU45_c'
]

AU_INTENSITY_COLUMNS = [
    'AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r',
    'AU17_r', 'AU20_r', 'AU23_r', 'AU25_r', 'AU26_r', 'AU45_r'
]


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


def plot(df, melted_df, aus, width, height):
    # Choose aus to plot
    if not aus:
        aus = [u[:4] for u in AU_INTENSITY_COLUMNS]
    else:
        aus = [f'AU{str(u).zfill(2)}' for u in aus]
    cmap = plt.get_cmap('tab10')
    fig, ax = plt.subplots(1, 1, figsize=(width, height))
    df.plot(ax=ax, x='timestamp', y=[f'{u}_r' for u in aus])

    # plot also presence as a span (need final_df for this)
    for i, (tier, start, end, _) in melted_df.iterrows():
        if tier[:4] in aus:
            c = cmap(aus.index(tier[:4]))
            ax.axvspan(start, end, color=c, label=tier, alpha=0.1)
    return fig


def process_file(fp, aus, width, height, output_folder):
    file_name = os.path.basename(fp)
    video_name = os.path.splitext(file_name)[0]
    df = read_df(fp)
    melted_df = melt_df(df)
    fig = plot(df, melted_df, aus, width, height)
    # Save the new table
    if output_folder is not None:
        os.makedirs(output_folder, exist_ok=True)
        output_fp = os.path.join(output_folder, f'{video_name}.png')
    else:
        output_fp = fp.replace('.csv', '.png')
    fig.savefig(output_fp)


def main(args):
    if args.folder:
        for folder_path in args.f:
            for fp in os.listdir(folder_path):
                if not fp.endswith('.csv'):
                    continue
                process_file(os.path.join(folder_path, fp), args.aus, args.width, args.height, args.output_folder)
    else:
        for fp in args.f:
            process_file(fp, args.aus, args.width, args.height, args.output_folder)


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    main(args)
