-> Python wrapper that uses several tools (porechope, qiime2, etc.) to analyse 16S nanopore data

-> Author: Massimo Bourquin, 2024

# 1. Installation & Usage

  a. Clone the Github repo `git clone https://github.com/Mass23/MACE_16S_nanopore`

  b. Install both the "basecalling.yml" and "MACE_16S_nanopore.yml" conda environments:
```
conda env create --name basecalling --file=basecalling.yml
conda env create --name MACE_16S_nanopore --file=MACE_16S_nanopore.yml
```
  Then activate the "basecalling" environment: `conda activate basecalling`

  b. Run the basecalling on the pod5 files, if needed use the `pod5 merge *.pod5 -o merged.pod5` function of the basecalling environment to merge all failed and pass pod5 files. (to install pod5 run `/home/USER/anaconda3/envs/basecalling/bin/pip install pod5`)

  c. Run the basecalling using dorado with the "sup" model, subsequently demultiplex the bam file and output fastq files: 
  ```
  /data/databases/dorado/dorado-0.8.1-linux-x64/bin/dorado basecaller sup -r merged.pod5 --kit-name SQK-NBD114-96 > calls.bam
  /data/databases/dorado/dorado-0.8.1-linux-x64/bin/dorado demux --output-dir WHERE_YOU_WANT_IT --emit-fastq --no-classify calls.bam
  ```

  d. You will then need to remove the kit name suffix, and gzip these files (from within the fastq files directory)
```
rename s/SUFFIX_// S*.fastq
gzip *.fastq
```
  
  e. Activate the "MACE_16S_nanopore" conda environment `conda activate MACE_16S_nanopore`
  
  f. Run the pipeline by updating the "example.sh" file, and running it as a bash script: `bash example.sh` (don't forget to create a screen because it may run for a while)
  
  example run: `python3 process_16S_nanopore.py -f /data/alpine_soil/ -n alpine_soil -m metadata.tsv -t 24` from within the repository, -f is the data folder (reads), -n is the name for the output, metadata.tsv is the metadata file (look at the one in the repo for guidance, needs the Barcode and #SampleID columns), -t is the numbers of threads to use.

# 2. Description

  a. Porechop: removes adapters
  
  b. Chopper: quality control (q > 12) and size (only keeps reads from 1300bp to 1800bp)
  
  c. Qiime2: dereplicates sequences, creates abundance table, and taxonokmy based on greengenes2

# 3. Results/ folder
to do...
