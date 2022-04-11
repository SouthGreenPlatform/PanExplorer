#!/usr/bin/perl

use CGI;
use CGI::Carp qw(carpout fatalsToBrowser);
use CGI::Session;
use CGI::BaseCGI2;
use strict;
use File::Copy "cp";
use File::Basename;
use LWP::Simple;
use Template;

use Time::localtime;
use Time::Local;

use Error qw(:try);

use Config::Configuration;

my %cogs_categories = (
	"J"=>"INFORMATION STORAGE AND PROCESSING",
	"A"=>"INFORMATION STORAGE AND PROCESSING",
	"K"=>"INFORMATION STORAGE AND PROCESSING",
	"L"=>"INFORMATION STORAGE AND PROCESSING",
	"B"=>"INFORMATION STORAGE AND PROCESSING",
	"D"=>"CELLULAR PROCESSES AND SIGNALING",
	"Y"=>"CELLULAR PROCESSES AND SIGNALING",
	"V"=>"CELLULAR PROCESSES AND SIGNALING",
	"T"=>"CELLULAR PROCESSES AND SIGNALING",
	"M"=>"CELLULAR PROCESSES AND SIGNALING",
	"N"=>"CELLULAR PROCESSES AND SIGNALING",
	"Z"=>"CELLULAR PROCESSES AND SIGNALING",
	"W"=>"CELLULAR PROCESSES AND SIGNALING",
	"U"=>"CELLULAR PROCESSES AND SIGNALING",
	"O"=>"CELLULAR PROCESSES AND SIGNALING",
	"C"=>"METABOLISM",
	"G"=>"METABOLISM",
	"E"=>"METABOLISM",
	"F"=>"METABOLISM",
	"H"=>"METABOLISM",
	"I"=>"METABOLISM",
	"P"=>"METABOLISM",
	"Q"=>"METABOLISM",
	"R"=>"POORLY CHARACTERIZED",
	"S"=>"POORLY CHARACTERIZED"
);
my %cogs_categories_reverse = (
	"INFORMATION STORAGE AND PROCESSING"=>"JAKLB",
	"CELLULAR PROCESSES AND SIGNALING"=>"DYVTMNZWUO",
	"METABOLISM"=>"CGEFHIPQ",
	"POORLY CHARACTERIZED"=>"RS"
);

my %colors1 = (
	"INFORMATION STORAGE AND PROCESSING"=>"green",
	"CELLULAR PROCESSES AND SIGNALING"=>"black",
	"METABOLISM"=>"red",
	"POORLY CHARACTERIZED"=>"blue"
);
	  	   
my $base_cgi = CGI::BaseCGI2 -> new();
$base_cgi -> setTitle("Pan-genome Explorer: Search");
$base_cgi -> setHeading("Pan-genome Explorer");
	
# params	 
my $submit = $base_cgi -> param('submit');
my $result = $base_cgi -> param('result');
my $genename = $base_cgi -> param('genename');
my $project = $base_cgi -> param('project');

my $session;
if ($base_cgi -> param('session') =~/(\d+)/)
{
	$session = $1;
}
if (!$session){
	$session = int(rand(10000000000000));
}

if ($session && $session !~/^\d+$/)
{
	$base_cgi -> headHTML("2");
	print "<b><font color=red>Error: Session parameter must be an integer</font></b><br/><br/>\n";
	$base_cgi -> endHTML();
	exit;
}

my $execution_dir = "$Configuration::TEMP_EXECUTION_DIR/$session";
$base_cgi -> headHTML("pangenomexplorer");

my $options = "";
my @projects;
if ($project =~/^(\d+)\.(\w+)/){
        my $visible = $2;
        push(@projects,$project);
        $options .= "<option value='$project' selected>$visible</option>";
}
else{
opendir(DIR,"$Configuration::DATA_DIR/pangenome_data");
while(my $filename = readdir(DIR)) {
        if ($filename =~/\./){next;}
        push(@projects,$filename);
        if (!$project){$project = $filename;}
        if ($project eq $filename){
                $options .= "<option selected>$filename</option>";
        }
        else{
                $options .= "<option>$filename</option>";
        }
}
closedir(DIR);
}

my $menu = qq~
<nav class="navbar navbar-default">
  <div class="container-fluid">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="navbar-brand" href="#">Pan-genome Explorer</a>
    </div>
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
      <ul class="nav navbar-nav">
        <li><a href="#" onClick="window.location='./home.cgi?project='+document.getElementById('project').value;">Home</a></li>
        <li><a href="#" onClick="window.location='./upload.cgi?project='+document.getElementById('project').value;">Import genomes</a></li>
        <li><a href="#">Project: <select id="project" name="project" onchange="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">$options</select></a></li>
        <li><a href="#" onClick="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">Overview</a></li>
        <li><a href="#" onClick="window.location='./search.cgi?project='+document.getElementById('project').value;">Search</a></li>
        <li><a href="#" onClick="window.location='./synteny.cgi?project='+document.getElementById('project').value;">Synteny</a></li>
        <li><a href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Cluster Search</a></li>
        <li class="active"><a href="#" onClick="window.location='./genes.cgi?project='+document.getElementById('project').value;">Gene Search</a></li>
        <li><a href="#" onClick="window.location='./circos.cgi?project='+document.getElementById('project').value;">Circos</a></li>
</div>
</nav>
~;
print "<div class=\"container\">";
print $menu;


if (!-d $execution_dir){
	mkdir($execution_dir);
}
my $execution_dir2 = $execution_dir."2";
if (!-d $execution_dir2){
        mkdir($execution_dir2);
}
my $execution_dir3 = $execution_dir."3";
if (!-d $execution_dir3){
        mkdir($execution_dir3);
}
my $execution_dir4 = $execution_dir."4";
if (!-d $execution_dir4){
        mkdir($execution_dir4);
}




print "<form name=\"query_form\" id=\"query_form\" action=\"./genes.cgi\" method=\"get\">\n";
print "<table><tr><td><b>Enter a gene name, locus tag or keyword </b><i>(ex: AGJ99556.1, ERGA_CDS_06010, secretion type IV ehrlichia)</i>: &nbsp;&nbsp;&nbsp;";
print "<input type=\"text\" name=\"genename\" id=\"genename\" value=\"$genename\"><br/><br/>";
print "<input type=\"hidden\" name=\"project\" id=\"project\" value=\"$project\"><br/><br/>";
print "<input class=\"btn btn-primary\" type=\"submit\" value=\"Submit\" onclick=\"GeneSearch('$Configuration::CGI_WEB_DIR','$session');\"></td>";
print "</tr></table>";
print "<br/>";
print "</form>\n";

open(O,">$Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt");
open(LS,"ls $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/*.ptt |");
while(<LS>){
	my $file = $_;
	$file =~s/\n//g;$file =~s/\r//g;
	my @table = split(/\//,$file);
	my $strain = $table[$#table];
	$strain =~s/\.ptt//g;
	$strain =~s/_/ /g;
	#$strain =~s/\.//g;
	open(F,$file);
	<F>;<F>;<F>;
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		my @infos = split(/\t/,$line);
		my $gene = $infos[3];
		my $function = $infos[8];
		print O "$gene $function [$strain]\n";
	}
	close(F);
}
close(LS);
close(O);


if ($genename){

	my %strains;

	# search in locus tag in genbank files
	if ($genename =~/^(\w+)/){
		my $tag = $1;
		my $grep = `grep -A 7 -P 'locus_tag="$tag"' $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/*.gb | grep protein_id`;
		if ($grep =~/protein_id=\"(.*)\"/){
			$genename = $1;
		}
	}

	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt");
	my $sequences = "";
	my $dnasequences = "";
	my $ngenes = 0;
	my @tags = split(" ",$genename);
	my $head_genomes = `head -1 $Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt`;
	my @genomes = split("\t",$head_genomes);
	my %genomes_in_clusters;
	my %clusters;
	foreach my $genome(@genomes){
		$genomes_in_clusters{$genome} = 1;
	}
	open(C,">$Configuration::HOME_DIR/tables/$session.genes.txt");
	print C "Genes\tFunction\tSpecies\tCluster\tType\n";
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		if ($line =~/$tags[0]/i && $line =~/$tags[1]/i && $line =~/$tags[2]/i && $line =~/$tags[3]/i){
			my @infos = split(/\[/,$line);
			my $species = $infos[1];
			$species =~s/]//g;
			my $genome = $species;
			$genome=~s/ /_/g;
			my $genome2 = $genome;
			$genome2=~s/\.//g;	
			if (!$genomes_in_clusters{$genome} && !$genomes_in_clusters{$genome2}){next;}
			
			my @tab = split(" ",$infos[0]);
			my $gene = $tab[0];
			my $function = "";
			for (my $j=1; $j <= $#tab; $j++){
				$function .= $tab[$j]." ";
			}
			
			my $grep = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt`;
			my ($clnb) = split("\t",$grep);
			if (length($clnb) == 1){$clnb = "000".$clnb;}
			elsif (length($clnb) == 2){$clnb = "00".$clnb;}
			elsif (length($clnb) == 3){$clnb = "0".$clnb;}
			my $clustername = "CLUSTER".$clnb;
			my @i = split(/\t/,$grep);
			my $nb_found = 0;
			for (my $j = 1; $j <= $#i; $j++){
				my $val = $i[$j];
				if ($val =~/\w+/){
					$nb_found++;
				}
			}
			$clusters{$clustername}=1;
			my $type = "Dispensable";
			if ($nb_found == $#i){
				$type = "Core";
			}
			elsif ($nb_found == 1){
                                $type = "Strain-Specific";
                        }	
			print C "$gene	$function	$species	<a href='./clusters.cgi?genename=$clustername&project=$project' target=_blank>$clustername</a>\t$type\n";
			$ngenes++;
		}
	}
	close(F);
	close(C);

	print "<b>$ngenes genes found, ".scalar keys(%clusters). " clusters<br></b>";
	
	open(FASTA,">$execution_dir/genes.fa");
	print FASTA $sequences;
	close(FASTA);

	open(FASTA,">$execution_dir/genes_dna.fa");
	print FASTA $dnasequences;
	close(FASTA);

	my $config_table = "";
	$config_table .= qq~
					'dispensable-genes'=>
					{
							"select_title" => "Genes",
							"file" => "$Configuration::HOME_DIR/tables/$session.genes.txt",
					},
			~;
	open(T,">$execution_dir/tables.conf");
	print T $config_table;
	close(T);

	my $table_part = qq~
	<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>
	<a href='$Configuration::WEB_DIR/tables/$session.genes.txt'>Download table</a>~;

	print $table_part;	

	
	print "</div>";
	
	
	
}

#print "<div id=results_div>";



print "</div>";
my $footer = qq~
<footer>
<hr>
<div class="container" style="text-align: center;">
                    <p>Copyright &copy; 2021, CIRAD | Designed by <a target="_blank" href="https://www.southgreen.fr/">South Green Bioinformatics platform</a>.</p>
                </div>
</footer>~;

print $footer;




