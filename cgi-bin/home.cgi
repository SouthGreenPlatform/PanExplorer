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

my $execution_dir = "$Configuration::TEMP_EXECUTION_DIR/$session";
$base_cgi -> headHTML("pangenomexplorer");

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
        <li class="active"><a href="#" onClick="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">Home</a></li>
        <li><a href="#" onClick="window.location='./upload.cgi?project='+document.getElementById('project').value;">Import genomes</a></li>
        <li><a href="#">Project: <select id="project" name="project" onchange="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">$options</select></a></li>
        <li><a href="#" onClick="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">Overview</a></li>
        <li><a href="#" onClick="window.location='./search.cgi?project='+document.getElementById('project').value;">Search</a></li>
        <li><a href="#" onClick="window.location='./synteny.cgi?project='+document.getElementById('project').value;">Synteny</a></li>
        <li><a href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Cluster Search</a></li>
        <li><a href="#" onClick="window.location='./genes.cgi?project='+document.getElementById('project').value;">Gene Search</a></li>
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

my $paragraph = qq~
<section class="jumbotron text-center">
        <div class="container">
          <h2 class="jumbotron-heading">Pan-genome Explorer</h2>
          <p class="lead text-muted">PanExplorer performs pan-genome analysis based on the PGAP pipeline and exposes resulting information as a comprehensive and easy way, through several modules facilitating the exploration gene clusters and interpretation of data.</p>
          <p>
            <a href="./panexplorer.cgi" class="btn btn-primary my-2">Browse pan-genome projects</a>
            <a href="./upload.cgi" class="btn btn-primary my-2">Import genomes as a new project</a>
          </p>
        </div>
      </section>
<div class="text-center">
<p><img width='80%' src=\"$Configuration::WEB_DIR/images/GraphicalAbstract.png\"></p>
</div>

<section class="jumbotron text-center">
<div class="container">
<p class="text-left">
The application allows interactive data exploration at different levels :</p>
<p class="text-left">
(i) Pan-genome visualization as a presence/absence heatmap. This overview allows to easily identify and distinguish core-genes (present in all strains), cloud genes (genes from the accessory genome) and genome-specific genes.</p>
<p class="text-left">
(ii)    Physical map of core-genes and strain-specific genes can be displayed as a circular genomic representation (Circos), for each genome taken independently.
</p>
<p class="text-left">
(iii)   Synteny analysis. The conservation of gene order between genomes can be investigated using graphical representations
</p>
<p class="text-left">
(iv)    Visual inspection of a specific cluster.
</p>
For general questions, comments or problems about the site or the data, please contact us at <a href="mailto:alexis.dereeper\@ird.fr"> alexis.dereeper\@ird.fr</a>
</section>

~;
print $paragraph;

my $footer = qq~
<footer>
<hr>
<div class="container" style="text-align: center;">
                    <p>Copyright &copy; 2021, CIRAD | Designed by <a target="_blank" href="https://www.southgreen.fr/">South Green Bioinformatics platform</a>.</p>
                </div>
</footer>~;

print $footer;




