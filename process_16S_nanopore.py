import os
import argparse
import subprocess
import pandas as pd # type: ignore
import datetime
import glob

################################################################################
#################           FUNCTIONS           ################################
################################################################################

# Preprocessing part

def create_result_folder(results_folder_name):
    if not os.path.exists(results_folder_name):
        os.makedirs(results_folder_name)
    
    with open(f'{results_folder_name}/log.txt', 'w') as log:
        log.write(f"Log file for the run {results_folder_name}, time and date: {datetime.datetime.now().strftime('%I:%M%p on %B %d, %Y')}" + '\n\n')

def print_env_summary(results_folder_name):
    subprocess.call(f'conda list > {results_folder_name}/list_conda.txt', shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
        log.write('Creating the list_conda.txt file that summarises the conda env.' + '\n\n')


def load_metadata(metadata_path):
    metadata = pd.read_csv(metadata_path, sep='\t', header=0)
    return(metadata)

def list_subfolders(folder_path):
    """
    Lists all folders in the given folder (= samples fastq files).
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

def check_metadata_samples(metadata, samples, results_folder_name):
    """
    Check that the metadata agrees with the sample names listed.
    """
    metadata_samples = set(metadata['Barcode']) # samples in the metadata
    files_samples = set(samples) # samples in the reads' files
    print(files_samples)

    print('There are %d samples in the metadata file'%(len(metadata_samples)))
    print("There are %d samples in the reads' files"%(len(files_samples)))
    print("Barcode in the metadata but not in the reads' files:")
    print(metadata_samples.difference(files_samples))

    with open(f'{results_folder_name}/log.txt', 'a') as log:
        log.write('There are %d samples in the metadata file'%(len(metadata_samples)) + '\n\n')
        log.write("There are %d samples in the reads' files"%(len(files_samples)) + '\n\n')
        log.write("Barcode in the metadata but not in the reads' files:" + '\n\n')
        log.write(str(metadata_samples.difference(files_samples)) + '\n\n')

    out_list = [sample for sample in list(metadata_samples) if sample in files_samples]
    return metadata.loc[metadata['Barcode'].isin(out_list)], out_list

def concatenate_files(folder_path, metadata, samples, results_folder_name):
    """
    Takes folder paths, metadata files and samples list and concatenate the data
    for each sample in the list, + renames it to the sample name using metadata.
    """
    os.makedirs('%s/raw_data' % (results_folder_name))
    new_samples = []
    for sample in samples:
        new_sample = metadata.loc[metadata['Barcode'] == sample, '#SampleID'].values[0]
        new_path = f'{results_folder_name}/raw_data/{new_sample}.fastq.gz'
        args = ['cat', folder_path + sample + '/*.fastq.gz', '>', new_path]
        subprocess.call(' '.join(args), shell = True)
        new_samples.append(new_sample)
    return(new_samples)


# Reads preprocessing part

def run_porechop(samples, threads, results_folder_name):
    with open(f'{results_folder_name}/log.txt', 'a') as log:
        log.write(f'Running porechop...' + '\n\n')

    for sample in samples:
        reads_in = f'{results_folder_name}/raw_data/{sample}.fastq.gz'
        reads_out = f'{results_folder_name}/raw_data/{sample}_porechopped.fastq.gz'
        args = ['porechop', '--threads', str(threads), '-i', reads_in, '-o',
                reads_out]
        subprocess.call(' '.join(args), shell = True)

        with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args) + '\n\n')

def run_chopper(samples, threads, results_folder_name):
    with open(f'{results_folder_name}/log.txt', 'a') as log:
        log.write(f'Running chopper...' + '\n\n')

    for sample in samples:
        reads_in = f'{results_folder_name}/raw_data/{sample}_porechopped.fastq.gz'
        reads_out = f'{results_folder_name}/raw_data/{sample}_chopped.fastq.gz'
        args = ['gunzip', '-c', reads_in, '|',
                'chopper', '-q', str(10), '--maxlength', str(1800),
                           '--minlength', str(1300), '--threads', str(threads),
                '|', 'gzip', '>', reads_out]
        subprocess.call(' '.join(args), shell = True)

        with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args) + '\n\n')



# Qiime 2 part

def create_manifest(results_folder_name):
    os.makedirs(f'{results_folder_name}/qiime2')
    full_path = os.getcwd()
    manifest = pd.DataFrame(columns=['sample-id', 'absolute-filepath'])
    
    sample_files = glob.glob(f'{results_folder_name}/raw_data/*_chopped.fastq.gz')
    samples = [sample.split('/')[2].replace('_chopped.fastq.gz','') for sample in sample_files]
    print(samples)
    for sample in samples:
        manifest.loc[len(manifest.index)] = [sample, f'{full_path}/{results_folder_name}/raw_data/{sample}_chopped.fastq.gz'] 
    manifest.to_csv(f'{results_folder_name}/qiime2/qiime2_manifest.tsv', sep='\t', index=False) 

    with open(f'{results_folder_name}/log.txt', 'a') as log:
        log.write('Qiime2 manifest created...' + '\n\n')

def import_qiime2(results_folder_name):
    args = ['qiime', 'tools', 'import', '--type', "'SampleData[SequencesWithQuality]'",
            '--input-path', f'{results_folder_name}/qiime2/qiime2_manifest.tsv', 
            '--output-path' , f'{results_folder_name}/qiime2/preprocessed_reads.qza',
            '--input-format', 'SingleEndFastqManifestPhred33V2']
    subprocess.call(' '.join(args), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args) + '\n\n')

def dereplicate_qiime2(results_folder_name):
    args = ['qiime', 'vsearch', 'dereplicate-sequences',
            '--i-sequences', f'{results_folder_name}/qiime2/preprocessed_reads.qza',
            '--o-dereplicated-table', f'{results_folder_name}/qiime2/table-dereplicated.qza', 
            '--o-dereplicated-sequences', f'{results_folder_name}/qiime2/rep-seqs-dereplicated.qza']
    subprocess.call(' '.join(args), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args) + '\n\n')

def taxonomy_qiime2(results_folder_name):
    args_1 = ['wget', '-P', f'{results_folder_name}/qiime2/',
    'http://ftp.microbio.me/greengenes_release/2022.10/2022.10.backbone.full-length.fna.qza']
    subprocess.call(' '.join(args_1), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_1) + '\n\n')

    args_2 = ['qiime', 'greengenes2', 'non-v4-16s', 
              '--i-table', f'{results_folder_name}/qiime2/table-dereplicated.qza',
              '--i-sequences', f'{results_folder_name}/qiime2/rep-seqs-dereplicated.qza', 
              '--i-backbone', f'{results_folder_name}/qiime2/2022.10.backbone.full-length.fna.qza',
              '--o-mapped-table', f'{results_folder_name}/qiime2/taxonomy-mapped-table.qza', 
              '--o-representatives', f'{results_folder_name}/qiime2/rep-seqs-taxonomy.qza']
    subprocess.call(' '.join(args_2), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_2) + '\n\n')

    args_3 = ['wget', '-P', f'{results_folder_name}/qiime2/',
    'http://ftp.microbio.me/greengenes_release/2022.10/2022.10.taxonomy.asv.nwk.qza']
    subprocess.call(' '.join(args_3), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_3) + '\n\n')

    args_4 = ['qiime', 'greengenes2', 'taxonomy-from-table',
              '--i-reference-taxonomy', f'{results_folder_name}/qiime2/2022.10.taxonomy.asv.nwk.qza'
              '--i-table', f'{results_folder_name}/qiime2/taxonomy-mapped-table.qza', 
              '--o-classification', f'{results_folder_name}/qiime2/taxonomy-classification.qza']
    subprocess.call(' '.join(args_4), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_4) + '\n\n')

def export_qiime2(results_folder_name):
    args_1 = ['qiime', 'tools', 'export', 
              '--input-path', f'{results_folder_name}/qiime2/rep-seqs-dereplicated.qza', 
              '--output-path', f'{results_folder_name}/exported_sequences']
    subprocess.call(' '.join(args_2), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_2) + '\n\n')

    args_2 = ['qiime', 'tools', 'export', 
              '--input-path', f'{results_folder_name}/qiime2/table-dereplicated.qza', 
              '--output-path', f'{results_folder_name}/exported_table']
    subprocess.call(' '.join(args_2), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_2) + '\n\n')

    args_3 = ['qiime', 'tools', 'export', 
              '--input-path', f'{results_folder_name}/qiime2/taxonomy-classification.qza', 
              '--output-path', f'{results_folder_name}/exported_taxonomy']
    subprocess.call(' '.join(args_3), shell = True)
    with open(f'{results_folder_name}/log.txt', 'a') as log:
            log.write(' '.join(args_3) + '\n\n')

################################################################################
#################             MAIN             #################################
################################################################################

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="List files in a folder")

    # Add the folder path argument
    parser.add_argument("-f", "--folder", type=str,
                        help="Path to the folder as a string", required=True)
    parser.add_argument("-n", "--name", type=str,
                        help="Name of the results folder (_results will be added at the end)", required=True)
    parser.add_argument("-m", "--metadata_file", type=str,
                        help="Path to the metadata tsv file", required=True)
    parser.add_argument("-t", "--threads", type=str,
                        help="Number of threads to use for multiprocessing-compatible tasks", required=True)
    parser.add_argument("--skippreprocessing", action='store_true',
                        help="To add if you want to skip preprocessing")


    # Parse arguments
    args = parser.parse_args()

    if args.skippreprocessing is True:
        # Create results folder, print the environment summary, load the metadata
        # and list the samples to process
        out_folder = f'{args.name}_results'
        create_result_folder(out_folder)
        print_env_summary(out_folder)
        metadata = load_metadata(args.metadata_file)
        samples = list_subfolders(args.folder)
        metadata, samples_to_process = check_metadata_samples(metadata, samples, out_folder)

        # Concatenate files belonging to the same sample in the new directory,
        # run porechop and chopper
        samples_names = concatenate_files(args.folder, metadata, samples_to_process, out_folder)
        run_porechop(samples_names, args.threads, out_folder)
        run_chopper(samples_names, args.threads, out_folder)

    # Create the Qiime manifest, run qiime analysis
    create_manifest(out_folder)
    import_qiime2(out_folder)
    dereplicate_qiime2(out_folder)
    taxonomy_qiime2(out_folder)
    export_qiime2(out_folder)

if __name__ == "__main__":
    main()
