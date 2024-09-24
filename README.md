-> Python wrapper that uses several tools (porechope, qiime2, etc.) to analyse 16S nanopore data

-> Author: Massimo Bourquin, 2024

# 1. Installation & Usage

  a.  The data must have been processed using dorado with the 'sup' model. Here is the code to do this, it should yield one directory containing the fastq_pass files, you will use this directory as a starting point for the pipeline:
  ```
  # installation
  wget https://cdn.oxfordnanoportal.com/software/analysis/dorado-{LATEST VERSION}-linux-x64.tar.gz
  tar -xvzf dorado-{LATEST VERSION}-linux-x64.tar.gz
 
# check installation
tools/dorado-{LATEST VERSION}-linux-x64/bin/dorado basecaller -h
 
# output demultiplexed trimmed reads into one bam file
# use -r for searching multiple subdirectories
../tools/dorado-0.7.3-linux-x64/bin/dorado basecaller sup -r ../raw_data/gl_soil_ampl_2023/pod5/ --kit-name SQK-NBD114-96 > calls.bam
 
# output fastq file for each barcode
../tools/dorado-0.7.3-linux-x64/bin/dorado demux --output-dir . --emit-fastq --no-classify calls.bam
```
 --> also gzip the fastq files after basecalling, for this run `gzip *` inside the fastq files dir.

  b. Clone the Github repo `git clone https://github.com/Mass23/MACE_16S_nanopore`, place the data folder (reads) inside the repository
  
  c. Create the conda environment `conda env create -f MACE_16S_nanopore.yml \ conda activate MACE_16S_nanopore`
  
  c. Run example (in the example file) `python3 process_16S_nanopore.py -f alpine_soil/ -n alpine_soil -m metadata.tsv -t 24` from within the repository, -f is the data folder (reads), -n is the name for the output, metadata.tsv is the metadata file (look at the one in the repo for guidance, needs the Barcode and Well columns), -t is the numbers of threads to use.

# 2. Description

  a. Porechop: removes adapters
  
  b. Chopper: quality control (q > 12) and size (only keeps reads from 1300bp to 1800bp)
  
  c. Qiime2: dereplicates sequences, creates abundance table, and taxonokmy based on greengenes2

# 3. Results/ folder
to do...
