#!/usr/bin/python3

import os

import yaml
import bioblend
import bioblend.galaxy
from bioblend.galaxy import GalaxyInstance
from bioblend import galaxy

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CONFIG_YAML = "panexplorer_config.yaml"

with open(CONFIG_YAML, "r") as f:
    conf = yaml.safe_load(f)

galaxy_instance = conf.get("galaxy_instance")
galaxy_apikey = conf.get("galaxy_apikey")

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--i",help = "List of Genbank ids of bacteria full genomes")
parser.add_argument("--o",help = "Output path")
parser.add_argument("--p",help = "Minimum percentage identity for BlastP")
parser.add_argument("--a",help = "Alignment of coregenes must be activated")
parser.add_argument("--z",help = "Zip of genbank files")
parser.add_argument("--f",help = "Zip of genome FASTA files")
parser.add_argument("--s",help = "Software to use for pan-genome construction")
parser.add_argument("--n",help = "Name of analysis")
args = parser.parse_args()


gi = galaxy.GalaxyInstance(url=galaxy_instance, key=galaxy_apikey,verify=True)

workflows = gi.workflows.get_workflows()
histories = gi.histories.get_histories()
history = gi.histories.create_history(str(args.n))
inputsTool = dict()


if (str(args.z) != "None"):
    zip_genbanks = gi.tools.upload_file(str(args.z), history['id'])

    if (str(args.f) != "None"):
        zip_fasta = gi.tools.upload_file(str(args.f), history['id'])
        inputsTool={
                'mode|mode' : "fasta",
                'mode|private_genomes': {
                    'id':zip_genbanks['outputs'][0]['id'],
                    'src':'hda'
                    },
                'mode|private_genomes_fasta': {
                    'id':zip_fasta['outputs'][0]['id'],
                    'src':'hda'
                    },
                'mode|input' : str(args.i),
                'min_identity' : str(args.p),
                'generate_core_genes_alignment': args.a,
                'mode|software': str(args.s)
                }

    else:
        inputsTool={
                'mode|mode' : "genbanks",
                'mode|private_genomes': {
                    'id':zip_genbanks['outputs'][0]['id'],
                    'src':'hda'
                    },
                'mode|input' : str(args.i),
                'min_identity' : str(args.p),
                'generate_core_genes_alignment': args.a,
                'mode|software': str(args.s)
    }



else:
    print("ok")
    print(args.a)
    inputsTool={
        'mode|mode' : "accessions",
        'mode|input' : str(args.i),
        'min_identity' : str(args.p),
        'generate_core_genes_alignment': args.a,
        'mode|software': str(args.s)
    }
print(history['id'])


run_pgap = gi.tools.run_tool(history['id'], "pangenome_explorer" , inputsTool)
pgap_output = run_pgap['outputs'][0]['id']
pgap_outtree = run_pgap['outputs'][1]['id']
pgap_outcog = run_pgap['outputs'][3]['id']
pgap_outgenes = run_pgap['outputs'][2]['id']
pgap_outgc = run_pgap['outputs'][4]['id']
pgap_outpdf = run_pgap['outputs'][5]['id']
pgap_outheatmap = run_pgap['outputs'][6]['id']
pgap_outheatmap_html = run_pgap['outputs'][7]['id']
pgap_outcogstat = run_pgap['outputs'][8]['id']
pgap_outcogstat2 = run_pgap['outputs'][9]['id']
pgap_outcogofclusters = run_pgap['outputs'][10]['id']
pgap_outani = run_pgap['outputs'][11]['id']
pgap_outanipdf = run_pgap['outputs'][12]['id']
pgap_outrarefaction = run_pgap['outputs'][13]['id']
pgap_outrarefactionsvg = run_pgap['outputs'][14]['id']
pgap_outalpha = run_pgap['outputs'][15]['id']
pgap_outdist = run_pgap['outputs'][16]['id']
pgap_outvcf = run_pgap['outputs'][17]['id']
pgap_outgfa = run_pgap['outputs'][18]['id']
pgap_outalign = run_pgap['outputs'][19]['id']
pgap_outlog = run_pgap['outputs'][20]['id']
gi.max_get_attempts = 20

print("Downloading results...")


#quit()
out_pgap = gi.datasets.download_dataset(pgap_output, file_path = args.o+"/1.Orthologs_Cluster.txt",maxwait=820000,require_ok_state=False,use_default_filename=False)
outtree_pgap = gi.datasets.download_dataset(pgap_outtree, file_path = args.o+"/heatmap.svg.complete.pdf.distance_matrix.hclust.newick",maxwait=820000,require_ok_state=False,use_default_filename=False)
# outcog_pgap = gi.datasets.download_dataset(pgap_outcog, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outgenes_pgap = gi.datasets.download_dataset(pgap_outgenes, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outgc_pgap = gi.datasets.download_dataset(pgap_outgc, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outupset_pgap = gi.datasets.download_dataset(pgap_outpdf, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outheatmap_pgap = gi.datasets.download_dataset(pgap_outheatmap, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
outheatmaphtml_pgap = gi.datasets.download_dataset(pgap_outheatmap_html, file_path = args.o+"/vntr_matrix.tsv",maxwait=820000,require_ok_state=False,use_default_filename=False)
outcogstat_pgap = gi.datasets.download_dataset(pgap_outcogstat, file_path = args.o+"/cog_category_counts.txt",maxwait=820000,require_ok_state=False,use_default_filename=False)
outcogstat2_pgap = gi.datasets.download_dataset(pgap_outcogstat2, file_path = args.o+"/cog_category_2_counts.txt",maxwait=820000,require_ok_state=False,use_default_filename=False)
outcogofclusters_pgap = gi.datasets.download_dataset(pgap_outcogofclusters, file_path = args.o+"/cog_of_clusters.txt",maxwait=820000,require_ok_state=False,use_default_filename=False)
outani_pgap = gi.datasets.download_dataset(pgap_outani, file_path = args.o+"/fastani.out.matrix.complete.xls",maxwait=820000,require_ok_state=False,use_default_filename=False)
# outanipdf_pgap = gi.datasets.download_dataset(pgap_outanipdf, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outrarefaction_pgap = gi.datasets.download_dataset(pgap_outrarefaction, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outrarefactionsvg_pgap = gi.datasets.download_dataset(pgap_outrarefactionsvg, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outalpha_pgap = gi.datasets.download_dataset(pgap_outalpha, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
# outdist_pgap = gi.datasets.download_dataset(pgap_outdist, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
outvcf_pgap = gi.datasets.download_dataset(pgap_outvcf, file_path = args.o+"/variants.vcf",maxwait=820000,require_ok_state=False,use_default_filename=False)
#outlog_pgap = gi.datasets.download_dataset(pgap_outlog, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
outgfa_pgap = gi.datasets.download_dataset(pgap_outgfa, file_path = args.o+"/pangenome.gfa",maxwait=820000,require_ok_state=False,use_default_filename=False)
#outalign_pgap = gi.datasets.download_dataset(pgap_outalign, file_path = args.o,maxwait=820000,require_ok_state=False,use_default_filename=False)
history_id = history['id']

print("Done.")
#gi.histories.delete_history(history_id, purge=True)

