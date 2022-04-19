# PanExplorer

Web application to explore bacterial pangenomes

Official instance of PanExplorer: [https://panexplorer.southgreen.fr](https://panexplorer.southgreen.fr)

## Table of contents

- [Introduction](#introduction)
- [Running the workflow](#running)
- [Web application deployment](#deployment)

## Introduction

PanExplorer performs pan-genome analysis (using PGAP or Roary) and exposes resulting information as a comprehensive and easy way, through several modules facilitating the exploration gene clusters and interpretation of data.

The application allows interactive data exploration at different levels :

(i) Pan-genome visualization as a presence/absence heatmap. This overview allows to easily identify and distinguish core-genes (present in all strains), cloud genes (genes from the accessory genome) and genome-specific genes.

(ii) Physical map of core-genes and strain-specific genes can be displayed as a circular genomic representation (Circos), for each genome taken independently.

(iii) Synteny analysis. The conservation of gene order between genomes can be investigated using graphical representations

(iv) Visual inspection of a specific cluster.

## Running the workflow

1- Git clone

```
git clone https://github.com/SouthGreenPlatform/PanExplorer.git
cd PanExplorer
```

## Web application deployment

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


