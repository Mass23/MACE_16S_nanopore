import os
import argparse
import subprocess
import glob
import pandas as pd

################################################################################
#################           FUNCTIONS           ################################
################################################################################

def create_result_folder():
    newpath = 'results'
    if not os.path.exists(newpath):
        os.makedirs(newpath)

def print_env_summary():
    subprocess.call('conda list > results/list_conda.txt', shell = True)

def load_metadata(metadata_path):
    metadata = pd.read_csv(metadata_path, sep='\t', header=0)
    return(metadata)

def list_subfolders(folder_path):
    """
    Lists all folders in the given folder.
    """
    try:
        # Check if the path is a directory
        if not os.path.isdir(folder_path):
            print(f"The path '{folder_path}' is not a directory.")
            return

        # List all entries in the directory
        entries = os.listdir(folder_path)

        # Filter out files, keep only directories
        subfolders = [entry for entry in entries if os.path.isdir(os.path.join(folder_path, entry))]
        filtered_subfolders = [subfolder for subfolder in subfolders if subfolder != 'unclassified']
        return(filtered_subfolders)

    except Exception as e:
        print(f"An error occurred: {e}")

def check_metadata_samples(metadata, samples):
    """
    Check that the metadata agrees with the sample names listed.
    """
    metadata_samples = set(metadata['Barcode']) # samples in the metadata
    files_samples = set(samples) # samples in the reads' files

    print('There are %d samples in the metadata file'%(len(metadata_samples)))
    print("There are %d samples in the reads' files"%(len(files_samples)))

    print("Barcode in the metadata but not in the reads' files:")
    print(metadata_samples.difference(files_samples))
    out_list = [sample for sample in list(metadata_samples) if sample in files_samples]
    return metadata.loc[metadata['Barcode'].isin(out_list)], out_list

def concatenate_files(folder_path, metadata, samples):
    """
    Takes folder paths, metadata files and samples list and concatenate the data
    for each sample in the list, + renames it to the sample name using metadata.
    """
    os.makedirs('results/raw_data')
    new_samples = []
    for sample in samples:
        new_sample = metadata.loc[metadata['Barcode'] == sample, '#SampleID'].values[0]
        new_path = 'results/raw_data/' + str(new_sample) + '.fastq.gz'
        args = ['cat', folder_path + sample + '/*.fastq.gz', '>', new_path]
        subprocess.call(' '.join(args), shell = True)
        new_samples.append(new_sample)
    return(new_samples)

def run_porechop(samples, threads):
    for sample in samples:
        reads_in = 'results/raw_data/%s.fastq.gz'(sample)
        reads_out = 'results/raw_data/%s_porechopped.fastq.gz'(sample)
        args = ['porechop', '--threads', str(threads), '-i', reads_in, '-o',
                reads_out]
        subprocess.call(' '.join(args), shell = True)

def run_chopper(samples, threads):
    for sample in samples:
        reads_in = 'results/raw_data/%s_porechopped.fastq.gz'(sample)
        reads_out = 'results/raw_data/%s_chopped.fastq.gz'(sample)
        args = ['gunzip', '-c', reads_in, '|',
                'chopper', '-q', str(11), '--maxlength', str(1800),
                           '--minlength', str(1300), '--threads', str(threads),
                '|', 'gzip', '>', reads_out]
        subprocess.call(' '.join(args), shell = True)

################################################################################
#################             MAIN             #################################
################################################################################

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="List files in a folder")

    # Add the folder path argument
    parser.add_argument("-f", "--folder", type=str,
                        help="Path to the folder as a string", required=True)
    parser.add_argument("-m", "--metadata_file", type=str,
                        help="Path to the metadata tsv file", required=True)
    parser.add_argument("-t", "--threads", type=str,
                        help="Path to the metadata tsv file", required=True)

    # Parse arguments
    args = parser.parse_args()

    # Create results folder, print the environment summary, load the metadata
    # and list the samples to process
    create_result_folder()
    print_env_summary()
    metadata = load_metadata(args.metadata_file)
    samples = list_subfolders(args.folder)
    metadata, samples_to_process = check_metadata_samples(metadata, samples)

    # Concatenate files belonging to the same sample in the new directory,
    # run porechop and chopper
    samples_names = concatenate_files(args.folder, metadata, samples_to_process)
    run_porechop(samples_names, args.threads)
    run_chopper(samples_names, args.threads)

    # Create the Qiime manifest, run qiime analysis
    #manifest_name = create_manifest(new_samples)


if __name__ == "__main__":
    main()
