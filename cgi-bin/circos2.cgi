#!/usr/bin/perl

use lib ".";

use CGI;
use CGI::Carp qw(carpout fatalsToBrowser);
use CGI::Session;
use CGI::BaseCGI2;
use strict;
use File::Copy "cp";
use File::Basename;

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

        <li><a href="#">Project: <select id="project" name="project" onchange="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">$options</select></a></li>
        <li><a href="#" onClick="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">Overview</a></li>
        <li><a href="#" onClick="window.location='./search.cgi?project='+document.getElementById('project').value;">Search</a></li>
        <li><a href="#" onClick="window.location='./synteny.cgi?project='+document.getElementById('project').value;">Synteny</a></li>
        <li><a href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Cluster Search</a></li>
        <li><a href="#" onClick="window.location='./genes.cgi?project='+document.getElementById('project').value;">Gene Search</a></li>
        <li class="active"><a href="#" onClick="window.location='./circos.cgi?project='+document.getElementById('project').value;">Circos</a></li>
        <li><a href="#" onClick="window.location='./upload.cgi?project='+document.getElementById('project').value;">Upload genomes</a></li>

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





################################################################################
# Pan genome overview
#################################################################################
#system("cp -rf /www/panexplorer.southgreen.fr/pangenome_data/1.Orthologs_Cluster.txt $execution_dir/1.Orthologs_Cluster.txt");
my %cluster_of_gene;
my %genes_of_cluster;
my %core_genes;
my %core_genes_simple;
my %core_genecluster;
my %hash_concatenate_samples;
open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
my $first_line = <F>;
$first_line =~s/\n//g;$first_line =~s/\r//g;
my @samples = split("\t",$first_line);
my @samples2;
my %samples_displayed;
foreach my $sample(@samples){
	if ($sample =~/ClutserID/){next;}
	my $substr = substr($sample,0,40);
	push(@samples2,$substr);
	$samples_displayed{$substr}=1;
}



print "<form name=\"query_form\" id=\"query_form\">\n";
print "Select the genome(s) to be displayed &nbsp;&nbsp;";
print "<select name=\"strains\" id=\"strains\">\n";

foreach my $sample(@samples){
	if ($sample =~/ClutserID/){next;}
	print "<option value=\"$sample\">$sample</option>";
	
}
print "</select><br/><br/>\n";
print "&nbsp;&nbsp;<input class=\"btn btn-primary\" type=\"button\" value=\"Submit\" onclick=\"Circos('$Configuration::CGI_WEB_DIR','$session');\">";


#print "<tr>";
#print "<td>Select the type of feature to be displayed &nbsp;</td>";
#print "<td><select name=\"feature\" id=\"feature\">";
#print "<option value=\"coregenes1\">Core-genes (colorized by COG category)</option>";
#print "<option value=\"coregenes2\">Core-genes (colorized by strain)</option>";
#print "<option value=\"gcpercent\">GC%</option>";
#print "</select>\n";
#print "</td>";
#print "</tr>";
#print "</table>";
print "<br/><br/><br/>";
print "</form>\n";


print "<div id=results_div>";
print "</div>";






