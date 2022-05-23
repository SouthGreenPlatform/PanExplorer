#!/usr/bin/perl

use lib ".";

use strict;
use Getopt::Long;
use Config::Configuration;

my $usage = qq~Usage:$0 <args> [<opts>]

where <args> are:

    -i, --input         <Genbanks identifiers>
    -p, --project       <Project name>
    -e, --email         <email address>
    -o, --outdir        <output directory>
    -s, --software      <software for Pangenome analysis: roary,panacota,pgap>     
~;
$usage .= "\n";

my ($input,$project,$email,$outdir);


GetOptions(
	"input=s"      => \$input,
	"project=s"    => \$project,
	"email=s"      => \$email,
	"outdir=s"     => \$outdir
);


die $usage
  if ( !$input || !$project || !$email ||!$outdir);

$|++;
my $pid2 = fork;
if (!defined $pid2) {
	die "Cannot fork: $!";
}
elsif ($pid2 == 0 ){
	chdir($outdir);
	my @ids = split(",",$input);
	open(G,">genbank_ids");
	print G join("\n",@ids);
	close(G);
	if ($software eq "roary"){
		system("export PANEX_PATH=/usr/local/bin/PanExplorer_workflow;singularity exec $Configuration::CGI_DIR/panexplorer.sif snakemake --cores 1 -s \$PANEX_PATH/Snakemake_files/Snakefile_wget_roary_heatmap_upset_COG >>log.txt 2>&1");
	}
	elsif ($software eq "pgap"){
                system("export PANEX_PATH=/usr/local/bin/PanExplorer_workflow;singularity exec $Configuration::CGI_DIR/panexplorer.sif snakemake --cores 1 -s \$PANEX_PATH/Snakemake_files/Snakefile_wget_PGAP_heatmap_upset_COG >>log.txt 2>&1");
        }
	else{
		system("export PANEX_PATH=/usr/local/bin/PanExplorer_workflow;singularity exec $Configuration::CGI_DIR/panexplorer.sif snakemake --cores 1 -s \$PANEX_PATH/Snakemake_files/Snakefile_wget_panacota_heatmap_upset_COG >>log.txt 2>&1");
	}
	my @tab = split(/\//,$outdir);
	my $session = $tab[$#tab];
	use MIME::Lite;

	system("cp -rf outputs/pav_matrix.tsv $Configuration::DATA_DIR/pangenome_data/$session.$project/1.Orthologs_Cluster.txt >>$outdir/copy.log 2>&1");
	system("cp -rf outputs/accessory_binary_genes.fa.newick $Configuration::DATA_DIR/pangenome_data/$session.$project/4.PanBased.Neighbor-joining.tree");
        system("cp -rf outputs/cog_output.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/COG_assignation.txt");
        system("cp -rf outputs/genes.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/genomes/genes.txt");
        system("cp -rf outputs/GCskew.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/GCpercent/GCpercent");
	system("cp -rf outputs/upsetr.svg $Configuration::DATA_DIR/pangenome_data/$session.$project/UpsetDiagram.svg");
	system("cp -rf outputs/heatmap.svg $Configuration::DATA_DIR/pangenome_data/$session.$project/Accessory_heatmap.clusterized.svg");

	system("cp -rf outputs/cog_stats.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/cog_category_counts.txt");
	system("cp -rf outputs/cog_stats2.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/cog_category_2_counts.txt");
	system("cp -rf outputs/cog_of_clusters.txt $Configuration::DATA_DIR/pangenome_data/$session.$project/cog_of_clusters.txt");
	system("echo PPanGGOLiN >$Configuration::DATA_DIR/pangenome_data/$session.$project/software.txt");
	my $subject = 'Panexplorer results';
	my $message = qq~
Hi,

Your job $session.$project is done. You can click the link below to see your results:
$Configuration::CGI_WEB_DIR/panexplorer.cgi?uploadid=$session.$project

See you soon on PanExplorer,

The PanExplorer team~;
	my $msg = MIME::Lite->new(
                 From     => "panexplorer\@southgreen.fr",
                 To       => $email,
                 Subject  => $subject,
                 Data     => $message
                 );

	$msg->send;
	
	print "Email Sent Successfully\n";
}
