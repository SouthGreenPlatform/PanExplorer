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
use 5.010;
use Error qw(:try);
use POSIX ":sys_wait_h";
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
$base_cgi -> setTitle("Pan-genome Explorer: Upload");
$base_cgi -> setHeading("Pan-genome Explorer");
	
# params	 
my $submit = $base_cgi -> param('submit');
my $result = $base_cgi -> param('result');
my $project = $base_cgi -> param('project');
my $genbanks;
if ($base_cgi -> param('genbanks') =~/([\w\.,]+)/){
        $genbanks = $base_cgi -> param('genbanks');
}
my $email;
if ($base_cgi -> param('email') =~/([\w\.\@]+)/){
        $email = $base_cgi -> param('email');
}
my $projectnew;
if ($base_cgi -> param('projectnew') =~/(^[\w]+)$/){
        $projectnew = $base_cgi -> param('projectnew');
}
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
        <li class="active"><a href="#" onClick="window.location='./upload.cgi?project='+document.getElementById('project').value;">Import genomes</a></li>
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
#exit;

print "<form name=\"query_form\" id=\"query_form\" action=\"./upload.cgi\" method=\"post\">\n";
print "<input type=\"hidden\" name=\"project\" id=\"project\" value=\"$project\"><br/><br/>";
print "<table border=0><tr><td>Enter a project name:</td><td>";
print "<input type=\"text\" name=\"projectnew\" id=\"projectnew\" value=\"$projectnew\" size=50></td><td><i> Alphanumeric, no space</i></td></tr>";
print "<tr><td>&nbsp;</td><td></td></tr>";
print "<tr><td>Enter a list of Genbank accessions:<br/>(up to 200 genomes) </td><td valign=top><input type=\"text\" name=\"genbanks\" id=\"genbanks\" value=\"$genbanks\" size=50><br/></td><td><i> Coma separated list (ex: CP000235.1,CP001079.1,CP001759.1,CP015994.2)</i></td></tr>";
print "<tr><td>&nbsp;</td><td></td></tr>";
print "<tr><td>Enter a valid email address: </td><td><input type=\"text\" name=\"email\" id=\"email\" value=\"$email\" size=50></td><td><i> To be informed of data availability</i></td></tr>";
print "<tr><td>&nbsp;</td><td></td></tr>";
print "<tr><td>Choose the pan-genome software &nbsp;&nbsp; </td><td><select name='software' id='software'><option value='panacota'>PanACoTA (New)(faster)</option><option value='roary'>Roary (more stringent: comparison of strains in the same genus)</option><option value='pgap'>PGAP (more relaxed: comparison of strains in different species or genus)</option></select></td></tr>";
#print "<p>Upload zip of Genbank files: <input type=\"file\" name=\"genbanks\" /></p> ";
print "</table><br/>";


#print "<input class=\"btn btn-primary\" type=\"button\" value=\"Submit\" onclick=\"Upload('$Configuration::CGI_WEB_DIR','$session');\"></td>";
print "<input class=\"btn btn-primary\" type=\"button\" value=\"Check Genbank IDs\" onclick=\"CheckIDs2('$Configuration::CGI_WEB_DIR','$session','$genbanks','$projectnew');\">";
#print "<br/><br/><div id=\"check_div\"></div><br/><br/><div id=\"check_div_global\">\n";
print "<br/><br/>";
for (my $j = 1; $j <= 200; $j++){
	print "<div id=\"$j\"></div>";
}
print "<br/><br/><div id=\"check_div_global\"></div>\n";
if (!$genbanks){
	#print "<input class=\"btn btn-primary\" type=\"submit\" value=\"Check IDs\" ></td>";
}
print "<br/>";
#print "</form><br/>\n";

#print "<br/><div id=results_div>";
#exit;
if ($genbanks){
	my $projectnew;
	if ($base_cgi -> param('projectnew') =~/(^[\w]+)$/){
		$projectnew = $base_cgi -> param('projectnew');
	}
	else{
		print "<div class=\"alert alert-danger\" role=\"alert\">Project name is not valid</div>";exit;
	}

	my @genbank_ids = split(",",$genbanks);
        if (scalar @genbank_ids < 3){
                print "<div class=\"alert alert-danger\" role=\"alert\">You must provide at least 3 Genbank identifiers of bacterial genomes</div>";exit;
        }
	elsif (scalar @genbank_ids > 60){
                print "<div class=\"alert alert-danger\" role=\"alert\">Too many Genbank identifiers (maximum 60)</div>";exit;
        }
        else{
                my $nbok = 0;
                my $not_found = 0;
		my $not_annotated = 0;
		my $duplicated_strain = 0;
		mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew");
		mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes");
		mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes");
		mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/GCpercent");
		my %strains;
		my %strain_names;
		print "<div class=\"alert alert-success\" role=\"alert\">";
		print "Check Genbank...<br>";
                foreach my $genbank(@genbank_ids){
                        if ($genbank =~/([\w\.]+)/){
                                $genbank = $1;
				my $get_genbank = `$Configuration::TOOLS_DIR/edirect/efetch -id $genbank -db nuccore -mode text >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #my $strain = `grep 'DEFINITION' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb`;
                                my $genus = `grep 'genus' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
				if ($genus =~/genus \"([^\"]*)\"/){$genus = $1;}
				my $species = `grep 'species' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
				if ($species =~/species \"([^\"]*)\"/){$species = $1;}
				my $subname = `grep 'subname' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
				if ($subname =~/subname \"([^\"]*)\"/){$subname = $1;}
				$subname =~s/ /-/g;
				my $strain = $genus."_".$species."_".$subname;
				my $contain_genes = `grep -c cdregion $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
				chomp($contain_genes);
				if ($contain_genes == 0){
					$not_annotated = $genbank;last;
				}
                                #if ($strain =~/DEFINITION  (.*)$/){
                                #if ($strain =~/taxname \"([^\"]*)\"/){
                                if ($strain){
					#$strain = $1;
					my ($info1,$info2 ) = split(",",$strain);
					$strain = $info1;
					$strain =~s/ /_/g;
					$strain_names{$strain}++;
					my $indice = $strain_names{$strain};
					if ($indice > 1){$duplicated_strain = $strain;}
					$strains{$genbank} = $strain;
					#rename("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb","$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.gb");
					rename("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json","$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.json");
					$nbok++;
					print "$genbank : ok => $strain ($contain_genes genes)<br>";
				}
                                else{
                                        $not_found = $genbank;last;
                                }
                        }
                }
		print "</div>";
		if ($not_found && $nbok < scalar @genbank_ids){
                        print "<div class=\"alert alert-danger\" role=\"alert\">One of the identifiers provided is not found in Genbank: $not_found</div>";exit;
                }
		if ($not_annotated && $nbok < scalar @genbank_ids){
                        print "<div class=\"alert alert-danger\" role=\"alert\">One of the identifiers provided is not annotated : $not_annotated</div>";exit;
                }
		if ($duplicated_strain){
                        print "<div class=\"alert alert-danger\" role=\"alert\">The same strain name has been found several times : $duplicated_strain</div>";exit;
                }
                print "<div class=\"alert alert-success\" role=\"alert\">";
                print "Genbank identifiers have been checked successfully...<br>";
                #print "An email will be sent to <b>$email</b> when data will be available under project entitled <b>$projectnew</b>.<br>";
                print "</div>";
		print "<input class=\"btn btn-primary\" type=\"button\" id=\"submission\" value=\"Submit\" onclick=\"document.getElementById('submission').style.visibility = 'hidden';Upload('$Configuration::CGI_WEB_DIR','$session','$genbanks','$projectnew');\">";
		print "<br/><br/><div id=results_div></div>";
		exit;
		}
	}


my $footer = qq~
<footer>
<hr>
<div class="container" style="text-align: center;">
                    <p>Copyright &copy; 2021, CIRAD | Designed by <a target="_blank" href="https://www.southgreen.fr/">South Green Bioinformatics platform</a>.</p>
                </div>
</footer>~;

print $footer;
