## Python wrapper that uses several tools (porechope, qiime2, etc.) to analyse 16S nanopore data

# 1. Installation

  a. Clone the Github repo `git clone https://github.com/Mass23/MACE_16S_nanopore`
  
  b. Create the conda environment `conda env create -f MACE_16S_nanopore.yml.yml \ conda activate MACE_16S_nanopore.yml`
  
  c. Run example (in the example file) `python3 process_16S_nanopore.py -f alpine_soil/ -n alpine_soil -m metadata.tsv -t 24`

# 2. Description

  a. Porechop: removes adapters
  
  b. Chopper: quality control (q > 9) and size (only keeps reads from 1300bp to 1800bp)
  
  c. Qiime2: dereplicates sequences, creates abundance table, and taxonokmy based on greengenes2

# 3. Results/ folder
to do...
