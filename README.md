# PanExplorer

Web application to explore bacterial pangenomes

Official instance of PanExplorer: [https://panexplorer.southgreen.fr](https://panexplorer.southgreen.fr)

## Introduction

PanExplorer performs pan-genome analysis (using PGAP or Roary) and exposes resulting information as a comprehensive and easy way, through several modules facilitating the exploration gene clusters and interpretation of data.

The application allows interactive data exploration at different levels :

(i) Pan-genome visualization as a presence/absence heatmap. This overview allows to easily identify and distinguish core-genes (present in all strains), cloud genes (genes from the accessory genome) and genome-specific genes.

(ii) Physical map of core-genes and strain-specific genes can be displayed as a circular genomic representation (Circos), for each genome taken independently.

(iii) Synteny analysis. The conservation of gene order between genomes can be investigated using graphical representations

(iv) Visual inspection of a specific cluster.


## Install

1- Git clone

```
git clone https://github.com/SouthGreenPlatform/PanExplorer.git
cd PanExplorer
```

2- Build the singularity container

This step assumes you have singularity installed.

If singularity is not installed, have a look first to this: https://singularity-tutorial.github.io/01-installation/

```
cd singularity
sudo singularity build panexplorer.sif panexplorer.def
```

## Run the workflow as command line

1- Define the PANEX_PATH environnement variable

```
export PANEX_PATH=/usr/local/bin/PanExplorer_workflow
```

2- Prepare your input dataset (list of genomes to be analyzed)

Edit a new file names "genbank_ids" listing the Genbank identifiers of complete assembled and annotated genomes. 

The file should look like this

```
cat genbank_ids
CP000235.1
CP001079.1
CP001759.1
CP015994.2
```

3- Run the workflow

Creating a pangenome using Roary

```
singularity exec PanExplorer/singularity/panexplorer.sif snakemake --cores 1 -s $PANEX_PATH/Snakemake_files/Snakefile_wget_roary_heatmap_upset_COG
```

Creating a pangenome using PGAP

```
singularity exec PanExplorer/singularity/panexplorer.sif snakemake --cores 1 -s $PANEX_PATH/Snakemake_files/Snakefile_wget_PGAP_heatmap_upset_COG
```

In both cases, you should a new directory named "outputs" containing all output files.

This includes:

UpsetR Diagram

 <img src="upsetr.svg" align="center" width="70%" style="display: block; margin: auto;"/>
 
 Presence/absence heatmap of accessory genes:
 
 <img src="heatmap.svg" align="center" width="70%" style="display: block; margin: auto;"/>

## Deploy the Web application

1- Git clone

```
git clone https://github.com/SouthGreenPlatform/PanExplorer.git
cd PanExplorer
```

2- Copy directories into dedicated HTML and CGI directories

```
mkdir <PANEXPLORER_HTML_DIR>
cd <PANEXPLORER_PATH>/html
cp * <PANEXPLORER_HTML_DIR>
```

```
mkdir <PANEXPLORER_CGI_BIN_DIR>
cd <PANEXPLORER_PATH>/cgi-bin
cp * <PANEXPLORER_CGI_BIN_DIR>
```

3- Edit the Configuration file and javascript

```
cd <PANEXPLORER_CGI_BIN_DIR>/Config
vi Configuration.pm
```


