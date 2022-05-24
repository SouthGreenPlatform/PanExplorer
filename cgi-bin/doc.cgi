#!/usr/bin/perl

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

	  	   
my $base_cgi = CGI::BaseCGI2 -> new();
$base_cgi -> setTitle("Pan-genome Explorer: Search");
$base_cgi -> setHeading("Pan-genome Explorer");
	
# params	 
my $submit = $base_cgi -> param('submit');
my $result = $base_cgi -> param('result');
my $project = $base_cgi -> param('project');

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
        <li class="active"><a href="#" onClick="window.location='./doc.cgi?project='+document.getElementById('project').value;">Doc</a></li>
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

print "<br><h1>How to import new genomes?</h1>";

print "<img src=\"$Configuration::IMAGES_DIR/import_figure.png\" width=90%>";

print "<h3>(1) Give a name to your dataset</h3>";
print qq~<h4>For example, you may write the name of the bacteria species that will be analyzed. This project name must be alphanumeric and must not contain space. Once the analysis done, the project will appear in the drop-down list of the main menu.</h4>
~;
print "<h3>(2) Enter a list of Genbank identifiers</h3>";
print qq~<h4>It must be a comma separated list of identifiers. It can be either GenBank accession number of genomes (ex: CP001079, CP000235) or GenBank assembly identifiers (ex: GCA_000011945, GCA_000024505). You may refer to the section below to retrieve GenBank assembly ids of your favorite organism. <br>Note that genomes must be completely assembled with status "complete" or "chromosome" (not draft) and completely annotated.</h4>
~;

print "<h3>(3) Enter your email</h3>";
print qq~<h4>You will be notified by email when the analysis is done, and will receive the URL to access to your results and data</h4>~;

print "<h3>(4) Choose the software for pan-genome analysis</h3>";
print qq~<h4>Three softwares have been implemented in the workflow:<br/>
<ul>
<li>PGAP (<a href="https://doi.org/10.1093/bioinformatics/btr655" target="_blank">Zhao et al., 2012</a>)</li>
<li>Roary (<a href="https://doi.org/10.1093/bioinformatics/btv421" target="_blank">Page et al., 2015</a>)</li>
<li>PanACoTA (<a href="https://pubmed.ncbi.nlm.nih.gov/33575648/" target="_blank">Perrin et al., 2021</a>)</li>
</ul></h4>~;

print "<h3>(5) Click the button for checking ids</h3>";
print qq~<h4>Each of the GenBank identifiers will be checked for compatibility (assembly and annotation status)</h4>~;

print "<h3>(6) Click the Submit button</h3>";
print qq~<h4>If everything is OK, a Submit button appears. Click on it to finally send your list to the workflow.</h4>~;

print "<br><h1>How to get the list of available genomes from GenBank?</h1>";

print qq~<h4>In order to define the list of genbank identifiers, you can refer to this page which allows to extract the genomes available at NCBI: <br/><a href='https://www.ncbi.nlm.nih.gov/datasets/genomes'>https://www.ncbi.nlm.nih.gov/datasets/genomes</a><br/>
</h4>~;

print "<img src=\"$Configuration::IMAGES_DIR/genbank_genomes_figure.png\" width=100%>";

print "<h3>(1) Enter the name of organism</h3>";
print "<h3>(2) Restrict the assembly level to chromosome and complete only</h3>";
print "<h3>(3) Restrict to genomes that are annotated</h3>";
print "<h3>(4) Check all genomes and export as a table</h3>";
print "<h3>(5) Open the Excel file and sort by \"Assembly Accession\". Get all GCA accessions</h3>";

print "<br><h1>How to browse pangenome results?</h1>";

print "<img src=\"$Configuration::IMAGES_DIR/overview_figure.png\" width=100%>";

print "<h3>(1) Distribution of core-genome and accessory genome</h3>";

print qq~<h4>A pie-chart shows the distribution of respective percentage of genes that compose core-genome, dispensable genome or strain-specific genes.<br/>By clicking on Display "Distribution of strain-specific genes", a focus allows to display as a bar chart the number of strain-specific genes for each genome</h4>~;

print "<h3>(2) Interactive presence/absence matrix</h3>";

print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a) Zoom panel for zooming horizontally on gene clusters or vertically on strains</h4>~;
print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;b) Metadata about strains. It includes by default, the genus, the organism name, the country and continent (extracted from GenBank file). </h4>~;
print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;c) Metadata about strains and gene clusters when the mouse passes over cells of the matrix. </h4>~;
print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;d) Clicking on a specific cell of the matrix conducts to the Cluster search in order to get more information about this cluster. </h4>~;
print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;e) Cluster details: list of genes included in the cluster, their sequences and alignment.<br/></h4>~;
print qq~<h4>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; A distance-based phylogeny is performed if the number of genes is below 160</h4>~; 

print "<h3>(3) Dispensable genome as an Upset diagram</h3>";
print qq~<h4>This section allows to represent the size of the different intersections within the accessory genome, from most abundant to least abundant. <br/>Each column corresponds to an intersection between strains, and bar charts on top show the size of this intersection. Each row corresponds to a possible intersection: the filled-in cells show which strain is part of an intersection.<br/>Only the first 20 most abundant intersections are shown.<br/>The SVG is zoomable by double-click or mouse scroll.</h4>~;

print "<br><h1>How to evaluate synteny between genomes?</h1>";


print "<img src=\"$Configuration::IMAGES_DIR/synteny_figure.png\" width=100%>";

print "<h3>(1) Choose three genomes to be compared among the list of genomes available in the project</h3>";
print qq~<h4>Each genome has a specific color (blue,red,green) that will be used in the HivePlot.</h4>~;
print "<h3>(2) Click on Submit</h3>";
print "<h3>(3) A Hive plot shows the links between core-genes projected on each genome</h3>";
print qq~<h4>The HivePlot representation is a way to visualize the conservation of gene order between 3 pre-selected genomes of a dataset. Genes are connected by links between these 3 genomes, if they are composing the core-genome. Links are thus materialized only by core-genes because they can be connected between genomes, using their respective physical order in each genome. Each axis corresponds to a genome and is colorized with the corresponding color of the drop-down list of genomes.<br/>
This section allows to visually identify translocation (right blue arrow) or inversion (left blue arrow) events.</h4>~;
print "<h3>(4) Mauve viewer</h3>";
print qq~<h4>In the same way, the Mauve viewer allows to display horizontally gene order conservation between the three selected genomes.</h4>~;
print "<h3>(5) Focus on a specific region by zooming</h3>";
print qq~<h4>The Mauve viewer allows to zoom in on a specific region of interest. It gives access to the annotation of the strain (gene names, etc).</h4>~;


print "</div>";

print "</div>";


my $footer = qq~
<footer>
<hr>
<div class="container" style="text-align: center;">
                    <p>Copyright &copy; 2021, CIRAD | Designed by <a target="_blank" href="https://www.southgreen.fr/">South Green Bioinformatics platform</a>.</p>
                </div>
</footer>~;

print $footer;




