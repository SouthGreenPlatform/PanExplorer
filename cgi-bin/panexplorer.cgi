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

my %alphabet = ("A"=>"1","B"=>"2","C"=>"3","D"=>"4","E"=>"5","F"=>"6","G"=>"7","H"=>"8","I"=>"9","J"=>"10","K"=>"11","L"=>"12","M"=>"13","N"=>"14","O"=>"15","P"=>"16","Q"=>"17","R"=>"18","S"=>"19","T"=>"20","U"=>"21","V"=>"22","W"=>"23","X"=>"24","Y"=>"25","Z"=>"26");

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
$base_cgi -> setTitle("Pan-genome Explorer");
$base_cgi -> setHeading("Pan-genome Explorer");
	
# params	 
my $submit = $base_cgi -> param('submit');
my $result = $base_cgi -> param('result');
my $project = $base_cgi -> param('project');
my $output   = "plink.out";
my $uploadid = $base_cgi -> param('uploadid');
my $session;
if ($base_cgi -> param('session') =~/(\d+)/)
{
	$session = $1;
}

$base_cgi -> headHTML("pangenomexplorer");


my $param_url = "";
my $options = "";
my @projects;
if ($project =~/^(\d+)\.(\w+)/){
	my $visible = $2;
        push(@projects,$project);
        $options .= "<option value='$project' selected>$visible</option>";
}
elsif ($uploadid && $uploadid =~/^(\d+)\.(\w+)/){
	my $visible = $2;
	push(@projects,$uploadid);
	$project = $uploadid;
	$options .= "<option value='$uploadid' selected>$visible</option>";
	$param_url = "&uploadid=$uploadid";
}
else{
	opendir(DIR,"$Configuration::DATA_DIR/pangenome_data");
	while(my $filename = readdir(DIR)) {
	#open(DIR,"ls $Configuration::DATA_DIR/pangenome_data |");
	#while(<DIR>){
		#my $filename = $_;
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

if (!$session){
        if ($project){
                my @letters = split(//,uc($project));
                foreach my $letter(@letters){
			if ($letter =~/\d/){
				$session.=$letter;
			}
			elsif ($letter =~/[A-Z]/){
	                        $session .= $alphabet{$letter};
			}
                }
        }
}

if ($session && $session !~/^\d+$/)
{
        $base_cgi -> headHTML("2");
        print "<b><font color=red>Error: Session parameter must be an integer</font></b><br/><br/>\n";
        $base_cgi -> endHTML();
        exit;
}
my $execution_dir = "$Configuration::TEMP_EXECUTION_DIR/$session";

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
        <li><a href="#" onClick="window.location='./doc.cgi?project='+document.getElementById('project').value;">Doc</a></li>
        <li><a href="#">Project: <select id="project" name="project" onchange="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">$options</select></a></li>	
        <li class="active"><a href="#" onClick="window.location='./panexplorer.cgi?project='+document.getElementById('project').value;">Overview</a></li>
	<li><a href="#" onClick="window.location='./search.cgi?project='+document.getElementById('project').value;">Search</a></li>
	<li><a href="#" onClick="window.location='./synteny.cgi?project='+document.getElementById('project').value;">Synteny</a></li>

<!--
	<li class="nav-item dropdown">
<a class="nav-link dropdown-toggle" href="#" id="navbarDropdownMenuLink" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
          Search
        </a>
        <div class="dropdown-menu" aria-labelledby="navbarDropdownMenuLink">
          <a class="dropdown-item" href="#" onClick="window.location='./genes.cgi?project='+document.getElementById('project').value;">Search genes</a><br/>
          <a class="dropdown-item" href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Search cluster</a><br/>
          <a class="dropdown-item" href="#" onClick="window.location='./search.cgi?project='+document.getElementById('project').value;">Search intersection</a><br/>
        </div>
</li>-->

	<li><a href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Cluster Search</a></li>
        <li><a href="#" onClick="window.location='./genes.cgi?project='+document.getElementById('project').value;">Gene Search</a></li>
	<li><a href="#" onClick="window.location='./circos.cgi?project='+document.getElementById('project').value;">Circos</a></li>
</div>
</nav>
~;
print "<div class=\"container\">";
print $menu;
#if (!-d $execution_dir){
	mkdir($execution_dir);
#}
my $execution_dir3 = $execution_dir."3";
mkdir($execution_dir3);
my $session3 = $session."3";
my $execution_dir4 = $execution_dir."4";
mkdir($execution_dir4);
my $session4 = $session."4";

###########################################
# table of results
###########################################
my $config_table = "";
$config_table .= qq~
                'results'=>
                {
                        "select_title" => "Field Samples",
                        "file" => "$execution_dir/dataset.txt",
                },
                'results2'=>
                {
                        "select_title" => "Diagnostics",
                        "file" => "$execution_dir/diagnostics.txt",
                },
        ~;


my $tabs = qq~
<ul class="nav nav-tabs">
  <li class="active"><a data-toggle="tab" href="#pangenome">Pan-genome</a></li>
<!--  <li><a data-toggle="tab" href="#matrix">Presence/Absence Matrix</a></li>-->
  <li><a data-toggle="tab" href="#clusters">Core-Genes</a></li>
  <li><a data-toggle="tab" href="#dispensable">Dispensable Genes</a></li>
  <li><a data-toggle="tab" href="#specific">Strain-Specific Genes</a></li>
  <li><a data-toggle="tab" href="#cog">COGs</a></li>
  <li><a data-toggle="tab" href="#phylogeny">Phylogeny</a></li>
  <!--<li><a data-toggle="tab" href="#distribution">Distribution of core-genes</a></li>-->
</ul>
~;

print $tabs;

open(TEST,">$execution_dir/test");
my $t = gmtime();
print TEST "1 $t\n";
###########################################
# parsing and filtering 
############################################
my %gene_positions;
my %gene_positions2;
my %gene_positions3;
open(LS,"ls $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/*.ptt |");
while(<LS>){
	my $file = $_;
	$file =~s/\n//g;$file =~s/\r//g;
	if ($file =~/\/([^\/]+)\.ptt/){
		open(F,$file);
		my $strain = $1;
		<F>;<F>;<F>;
		while(<F>){
			my $line = $_;
			$line =~s/\n//g;$line =~s/\r//g;
			my @infos = split("\t",$line);
			my ($start,$end) = split(/\.\./,$infos[0]);	
			my $gene = $infos[3];
			$gene_positions{$strain}{$start} = $gene;
			$gene_positions2{$strain}{$gene} = $start;
			$gene_positions3{$strain}{$gene} = $end;
		}
		close(F);
	}
}
close(LS);

my $t = gmtime();
print TEST "2 $t\n";


my %continents;
open(F,"$Configuration::DATA_DIR/countries.txt");
<F>;
while(<F>){
	my $line = $_;
	$line =~s/\n//g;$line =~s/\r//g;
	my ($continent,$country) = split(/,/,$line);
	$continents{$country} = $continent;
}
close(F);


my %organisms;
my %countries;
my $nb_genomes = 0;
open(LS,"ls $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/*.gb |");
while(<LS>){
	my $file = $_;
	$file =~s/\n//g;$file =~s/\r//g;
	if ($file =~/\/([^\/]+)\.gb/){
		open(F,$file);
		my $strain = $1;
		$nb_genomes++;
		my $organism = `grep ORGANISM $file`;
		if ($organism =~/ORGANISM  (.*)/){$organism = $1;}
		$organisms{$strain}= $organism;
		my $country = `grep country $file`;
		$country =~s/^\s+//g;
		$country =~s/\/country=//g;
		$country =~s/\"//g;
		$country =~s/\n//g;$country =~s/\r//g;
		if ($country =~/:/){
			my $city;
			($country,$city) = split(/:/,$country);
		}
		$countries{$strain}= $country;
	}
}
close(LS);

my $t = gmtime();
print TEST "3 $t\n";


my %functions;
open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt");
while(<F>){
        my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
        if (/^(\w+\.1) (.*) \[(.*)\]$/){
                my $gene = $1;
                my $function = $2;
                my $species = $3;
                my $species_init = $species;
                $species_init =~s/ /_/g;
                $function =~s/'//g;
                $function =~s/"//g;
                $function =~s/\)//g;
                $function =~s/\(//g;
                $function =~s/,//g;
		if (!$function){$function = "unknown";}
		$functions{$gene} = $function;
        }
}
close(F);

my $t = gmtime();
print TEST "4 $t\n";


my %sites;
open(L,"$Configuration::DATA_DIR/pangenome_data/$project/heatmap.circos");
open(L2,">$execution_dir/heatmap.txt");
my $firstline = <L>;
while(<L>){
        my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
        my @infos = split("\t",$line);
	print L2 $infos[1];
	for (my $j = 3; $j <= $#infos; $j++){
		print L2 "\t".$infos[$j];
	} 
	print L2 "\n";
}
close(L);
close(L2);

my $t = gmtime();
print TEST "5 $t\n";


my %cogs;
my %cog_categories;
open(C,"$Configuration::DATA_DIR/pangenome_data/$project/COG_assignation.txt");
while(<C>){
	if ($nb_genomes > 40){last;}
	my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
	my ($gene,$cog,$cogcat) = split("\t",$line);
	$cogs{$gene} = $cog;
	$cog_categories{$gene} = $cogcat;
}
close(C);

my %cogs_of_clusters;
my %cogcats_of_clusters;
open(C,"$Configuration::DATA_DIR/pangenome_data/$project/cog_of_clusters.txt");
while(<C>){
        my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
        my ($cluster,$cog,$cogcat) = split("\t",$line);
	#print "$cluster $cog<br>";
        $cogs_of_clusters{$cluster}{$cog} = 1;
	$cogcats_of_clusters{$cluster}{$cogcat} = 1;
}
close(C);

my $t = gmtime();
print TEST "6 $t\n";

##############################################################################
# Prepare files for graphics
##############################################################################


print "<div class=\"tab-content\">";


################################################################################
# Pan genome overview
#################################################################################
my %cluster_of_gene;
my %genes_of_cluster;
my %core_genes;
my %core_genes_simple;
my %core_genecluster;
my %hash_concatenate_samples;
system("cp -rf $Configuration::HOME_DIR/hotmap/mysession $Configuration::HOME_DIR/hotmap/$session");
open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
open(O,">$execution_dir/heatmap.txt");
open(H,">$Configuration::HOME_DIR/hotmap/$session/data/med.json");
open(U,">$execution_dir/upsetr_matrix.txt");
print H "{\n\"rows\":[\n";
open(C,">$execution_dir/coregenes.txt");
open(D,">$execution_dir/dispensablegenes.txt");
open(P,">$Configuration::HOME_DIR/circosjs/$session.circos_heatmap.txt");
my $first_line = <F>;
$first_line =~s/\n//g;$first_line =~s/\r//g;
my $first_line_upset = $first_line;
$first_line_upset =~s/\t/,/g;
print U "$first_line_upset\n";
my @samples = split("\t",$first_line);
my @samples2;
my %samples_displayed;
my $sample_line = "";
foreach my $sample(@samples){
	if ($sample =~/ClutserID/){next;}
	
	my @words = split(/_/,$sample);
        my $genus = $words[0];
        my $species = $words[1];
        my $shortname = substr($genus,0,3) . "_". substr($species,0,2);
        for (my $j = 2; $j <= $#words; $j++){
                $shortname.="_".$words[$j];
        }
        $shortname = substr($shortname,0,25);

	#my $first_letters = substr($sample,0,20);
	my $organism = $organisms{$sample};
	my $country = $countries{$sample};
	my $continent = "unresolved";
	if ($continents{$country}){
		$continent = $continents{$country};
	}
	$continent =~s/Africa/africa/g;
	
	$sample_line .= "{\"meta\":[\"$genus\",\"$organism\",\"$country\",\"$continent\"],\"name\":\"$shortname\", \"project\":\"$project\"},\n";
	my $substr = substr($sample,0,40);
	push(@samples2,$substr);
	$samples_displayed{$substr}=1;
}
my $t = gmtime();
print TEST "7 $t\n";


chop($sample_line);chop($sample_line);
print H "$sample_line],\n";
print H "\"cols\":[\n";
my %hash_matrix;
print O "Cluster\t".join("\t",@samples2)."\n";
print C "Cluster\tFunction\tCOG\tCOG categories\n";
print D "Cluster\tFound in N strains\tFunction\tCOG\tCOG categories\n";
my $genes_line = "";
my $nb_core_genes = 0;
my $nb_dispensable_genes = 0;
my $nb_specific_genes = 0;
my %specific;
my $nb_genomes = scalar @samples2;
while(<F>){
	my @i = split("\t",$_);
	my $cluster_num = $i[0];
	my $clnb = $i[0];
	my $pos = $clnb;
	my $pos_before = $pos - 1;
	print P "clusters $clnb";
	if (length($clnb) == 1){$clnb = "000".$clnb;}
	elsif (length($clnb) == 2){$clnb = "00".$clnb;}
	elsif (length($clnb) == 3){$clnb = "0".$clnb;}
	my $name = "CLUSTER".$clnb;
	print O $name;
	print U $name;
	my $nb_found = 0;
	my $concatenate_samples = "";
	my $strain_found = 0;
	my %functions_of_genes;
	for (my $j = 1; $j <= $#i; $j++){
		my $val = $i[$j];
		if ($val =~/\w+/){
			print U ",1";
			print P " 1";
			#print P "cl $pos_before $pos red sample$j\n"; 
			my @genes = split(",",$val);
			foreach my $gene(@genes){
				my $function = $functions{$gene};
				if ($function =~/\w+/){$functions_of_genes{$function}++;}
				$cluster_of_gene{$gene} = $name;
				$genes_of_cluster{$name}.=",$gene";
			}
			$nb_found++;
			$strain_found = $j;
			print O "\t10";
			$hash_matrix{$j} .= "1,";
			$concatenate_samples .=",".$samples[$j];
		}
		else{
			print O "\t5";
			print U ",0";
			print P " 0";
			#print P "cl $pos_before $pos white sample$j\n";
			$hash_matrix{$j} .= "0,";
		}
	}
	my $functions_concat = "#";
	my %reverse_functions = reverse(%functions_of_genes);
	foreach my $nb(sort {$b<=>$a} keys(%reverse_functions)){
		$functions_concat = $reverse_functions{$nb};last;
	}
	my $cogs_concat = "#";
        if ($cogs_of_clusters{$cluster_num}){
                my $ref_cogs_of_clusters = $cogs_of_clusters{$cluster_num};
                $cogs_concat = join(",",keys(%$ref_cogs_of_clusters));
        }
        my $cogcats_concat = "#";
        if ($cogcats_of_clusters{$cluster_num}){
                my $ref_cogcats_of_clusters = $cogcats_of_clusters{$cluster_num};
                $cogcats_concat  = join(",",keys(%$ref_cogcats_of_clusters));
        }

	$genes_line .= "{\"meta\":[\"$cogs_concat\",\"$cogcats_concat\",\"$functions_concat\"],\"name\":\"$name\"},\n";
	print O "\n";
	print U "\n";
	print P "\n";
	$hash_concatenate_samples{$concatenate_samples}.=",$name";

	my @genes = split(",",$genes_of_cluster{$name});
	##############################
	# core-genes
	##############################
	if ($nb_found == $#i){
		$nb_core_genes++;
		#core-genes with only one representant by strain
		my $is_coregene_simple = 0;
		if (scalar @genes == ($nb_found+1)){
			$is_coregene_simple = 1;
		}
		my %cogs_of_cluster;
		my %cogcats_of_cluster;
		
		foreach my $gene(@genes){
			$core_genes{$gene} = 1;
			#my $function = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt`;
			if ($is_coregene_simple){$core_genes_simple{$gene} = 1;}
			my $cog = $cogs{$gene};
			my $cogcat1 = $cog_categories{$gene};
			if ($cog =~/COG/){
				$cogs_of_cluster{$cog}++;
				$cogcats_of_cluster{$cogcat1}++;
			}
		}
		$core_genecluster{$name} = 1;
		my $cogs_concat = "#";
		if (join(",",keys(%cogs_of_cluster))){
			$cogs_concat = join(",",keys(%cogs_of_cluster));
		}
		if ($cogs_of_clusters{$cluster_num}){
			my $ref_cogs_of_clusters = $cogs_of_clusters{$cluster_num};
			$cogs_concat = join(",",keys(%$ref_cogs_of_clusters));
		}
		my $cogcats_concat = "#";
		if (join(",",keys(%cogcats_of_cluster))){
			$cogcats_concat  = join(",",keys(%cogcats_of_cluster));
		}
		if ($cogcats_of_clusters{$cluster_num}){
			my $ref_cogcats_of_clusters = $cogcats_of_clusters{$cluster_num};	
			$cogcats_concat  = join(",",keys(%$ref_cogcats_of_clusters));
		}
		my $functions_concat = "#";
		my %reverse_functions = reverse(%functions_of_genes);
		foreach my $nb(sort {$b<=>$a} keys(%reverse_functions)){
			$functions_concat = $reverse_functions{$nb};last;
		}
		my $cogs_concat_truncated = substr($cogs_concat,0,24);
		print C "<a href='./clusters.cgi?genename=$name&project=$project' target=_blank>$name</a>\t$functions_concat\t$cogs_concat_truncated\t$cogcats_concat\n";
	}
	elsif ($nb_found == 1){
		$nb_specific_genes++;
		my $sample_found = $samples[$strain_found];
		my %cogs_of_cluster;
                my %cogcats_of_cluster;
                foreach my $gene(@genes){
                        my $cog = $cogs{$gene};
                        my $cogcat1 = $cog_categories{$gene};
                        if ($cog =~/COG/){
                                $cogs_of_cluster{$cog}++;
                                $cogcats_of_cluster{$cogcat1}++;
                        }
                }
		my $cogs_concat = "#";
                if (join(",",keys(%cogs_of_cluster))){
                        $cogs_concat = join(",",keys(%cogs_of_cluster));
                }
		if ($cogs_of_clusters{$cluster_num}){
                        my $ref_cogs_of_clusters = $cogs_of_clusters{$cluster_num};
                        $cogs_concat = join(",",keys(%$ref_cogs_of_clusters));
                }
                my $cogcats_concat = "#";
                if (join(",",keys(%cogcats_of_cluster))){
                        $cogcats_concat  = join(",",keys(%cogcats_of_cluster));
                }
		if ($cogcats_of_clusters{$cluster_num}){
                        my $ref_cogcats_of_clusters = $cogcats_of_clusters{$cluster_num};
                        $cogcats_concat  = join(",",keys(%$ref_cogcats_of_clusters));
                }
		my $functions_concat = "#";
                my %reverse_functions = reverse(%functions_of_genes);
                foreach my $nb(sort {$b<=>$a} keys(%reverse_functions)){
                        $functions_concat = $reverse_functions{$nb};last;
                }
		my $cogs_concat_truncated = substr($cogs_concat,0,24);
		$specific{$sample_found}.= "<a href='./clusters.cgi?genename=$name&project=$project' target=_blank>$name</a>\t$functions_concat\t<span title=''>$cogs_concat_truncated</span>\t$cogcats_concat\n";
	}
	else{
		$nb_dispensable_genes++;
		my %cogs_of_cluster;
		my %cogcats_of_cluster;
		foreach my $gene(@genes){
			my $cog = $cogs{$gene};
			my $cogcat1 = $cog_categories{$gene};
			if ($cog =~/COG/){
				$cogs_of_cluster{$cog}++;
				$cogcats_of_cluster{$cogcat1}++;
			}
		}
		my $cogs_concat = "#";
		if (join(",",keys(%cogs_of_cluster))){
			$cogs_concat = join(",",keys(%cogs_of_cluster));
		}
		if ($cogs_of_clusters{$cluster_num}){
                        my $ref_cogs_of_clusters = $cogs_of_clusters{$cluster_num};
                        $cogs_concat = join(",",keys(%$ref_cogs_of_clusters));
                }
		my $cogcats_concat = "#";
		if (join(",",keys(%cogcats_of_cluster))){
                        $cogcats_concat  = join(",",keys(%cogcats_of_cluster));
                }
		if ($cogcats_of_clusters{$cluster_num}){
                        my $ref_cogcats_of_clusters = $cogcats_of_clusters{$cluster_num};
                        $cogcats_concat  = join(",",keys(%$ref_cogcats_of_clusters));
                }
		my $functions_concat = "#";
                my %reverse_functions = reverse(%functions_of_genes);
                foreach my $nb(sort {$b<=>$a} keys(%reverse_functions)){
                        $functions_concat = $reverse_functions{$nb};last;
                }
		if ($functions_concat !~/\w/){$functions_concat="unknown";}
		my $cogs_concat_truncated = substr($cogs_concat,0,24);
		print D "<a href='./clusters.cgi?genename=$name&project=$project' target=_blank>$name</a>\t$nb_found\t$functions_concat\t$cogs_concat_truncated\t$cogcats_concat\n";
	}
}
close(F);
close(O);
close(C);
close(D);
close(U);
close(P);
open(CHROM_LENGTH,">$Configuration::HOME_DIR/circosjs/$session.chr_length.txt");
print CHROM_LENGTH "clusters 7000\n";
close(CHROM_LENGTH);

chop($genes_line);
chop($genes_line);
print H "$genes_line],\n\"matrix\":[\n";
my $matrix = "";
foreach my $j(sort {$a<=>$b} keys(%hash_matrix)){
	my $values = $hash_matrix{$j};
	chop($values);
	$matrix .= "[$values],";
}
chop($matrix);
print H "$matrix\n]}";
close(H);

my $t = gmtime();
print TEST "8 $t\n";
close(TEST);


#open(H,">$Configuration::HOME_DIR/treemap/$session.treemap.html");
open(S,">$execution_dir/pie.txt");
print S "Core-genes	$nb_core_genes\n";
print S "Dispensable genes	$nb_dispensable_genes\n";
print S "Strain-specific genes	$nb_specific_genes\n";
close(S);
#close(H);
my $config_specific = "";
open(S,">$execution_dir/pie_specific.txt");
#print S "Strain\tNumber of specific genes\n";
foreach my $sample(sort keys(%specific)){
	open(L,">$execution_dir3/$sample.specific.txt");
	print L "Cluster\tFunction\tCOG\tCOG categories\n";
	my $lines_specific = $specific{$sample};
	my $nb_specific = scalar split("\n",$lines_specific);
	print S "$sample	$nb_specific\n";
	print L $lines_specific;
	close(L);
	$config_specific .= qq~
		'$sample'=>
                {
                        "select_title" => "$sample",
                        "file" => "$execution_dir3/$sample.specific.txt",
                },
	~;
}
close(S);

system("echo 'Strain\tNumber' >$execution_dir/pie_specific.2.txt");
system("sort -k 2nr $execution_dir/pie_specific.txt >>$execution_dir/pie_specific.2.txt");

open(T,">$execution_dir3/tables.conf");
print T $config_specific;
close(T);

my $nb = 0;
#print scalar keys(%hash_concatenate_samples);
foreach my $concatenate_samples(keys(%hash_concatenate_samples)){
	my @clusters = split(",",$hash_concatenate_samples{$concatenate_samples});
	if (scalar @clusters > 0){
		#print scalar @clusters ."\n";
		$nb++;
	}
}


my $config = qq~
'1-pie'=>
	{
	        "select_title" => "Distribution of core-genome and accessory genome",
                "per_chrom" => "off",
                "title" => "Distribution of core-genome and accessory genome",
                "type" => "pie",
                "stacking" => "off",	
		"file" => "$execution_dir/pie.txt"
},
#'pie_specific'=>
#        {
#                "select_title" => "Distribution of strain-specific genes",
#                "per_chrom" => "off",
#                "title" => "Distribution of strain-specific genes",
#                "type" => "pie",
#                "stacking" => "off",
#                "file" => "$execution_dir/pie_specific.txt"
#},
'2-barplot'=>
        {
                "select_title" => "Distribution of strain-specific genes",
                "per_chrom" => "off",
                "title" => "Distribution of strain-specific genes",
                "type" => "column",
                "stacking" => "off",
                "file" => "$execution_dir/pie_specific.2.txt"
},
~;
open(F,">$execution_dir/chrom_viewer.conf");
print F $config;
close(F);

my $software = `cat $Configuration::DATA_DIR/pangenome_data/$project/software.txt`;
$software =~s/\n//g;$software =~s/\r//g;

my $graph_part = qq~
  <div id="pangenome" class="tab-pane active">
<br/><b>Number of genomes (processed by $software): $nb_genomes</b></br>
  <br/><iframe src='$Configuration::CGI_WEB_DIR/chrom_viewer.cgi?session=$session' width='950' height='500' style='border:solid 0px black;'></iframe>~;

print $graph_part;

if (-e "$Configuration::DATA_DIR/pangenome_data/$project/Accessory_heatmap.clusterized.html"){
	print "<br/><b>Accessory genes: Presence/absence matrix</b> (<i>Clusters and strains have been preliminarily clusterized (Hierarchical clustering)</i>)<br/><br/>";
	system("cp -rf $Configuration::DATA_DIR/pangenome_data/$project/Accessory_heatmap.clusterized.html $Configuration::HOME_DIR/upsetr_pdf/$session.Accessory_heatmap.html");
	#print "<embed width='100%' height='1000px' src=\"$Configuration::WEB_DIR/upsetr_pdf/$session.Accessory_heatmap.html\"/><br/>";
}
#else{
	print "<br><b>Presence/Absence matrix</b></br> <iframe src='$Configuration::WEB_DIR/hotmap/$session/' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>";
#}
if (-e "$Configuration::DATA_DIR/pangenome_data/$project/UpsetDiagram.svg"){
	print "<br/><br/><b>Accessory genes: Upset diagram</b> (<i>This SVG image is zoomable by mouse scroll or double-click</i>)<br/>";

	my $svg_content = `grep -v '<svg' $Configuration::DATA_DIR/pangenome_data/$project/UpsetDiagram.svg | grep -v '<?xml'`;
	open(HTML,">$Configuration::HOME_DIR/svg-pan-zoom/demo/$session.html");
	open(H,"$Configuration::HOME_DIR/svg-pan-zoom/demo/template.html");
	while(<H>){
		if (/SVG_CONTENT/){print HTML $svg_content;}
		else{print HTML $_;}
	}
	close(HTML);
	print "<embed width='100%' height='1000px' src=\"$Configuration::WEB_DIR/svg-pan-zoom/demo/$session.html\"/>";
}

print "</div>";

#print "<form id=\"loginForm\" target=\"myIframe3\" action=\"$Configuration::WEB_DIR/circosJS/demo/index.php\" method=\"POST\">\n";
#print "<input type=\"hidden\" name=\"chromosome\" value=\"$Configuration::WEB_DIR/circosjs/$session.chr_length.txt\" />\n";
#print "<input type=\"hidden\" name=\"select[]\" id=\"annot\" value=\"HeatMap\" />\n";
#print "<input type=\"hidden\" name=\"name[]\" id=\"annot\" value=\"density\" />\n";
#print "<input type=\"hidden\" name=\"data[]\" id=\"annot\" value=\"$Configuration::WEB_DIR/circosjs/$session.circos_heatmap.txt\" />\n";

#print "<input onload=\"document.getElementById('display').form.submit();\" value=\"Display Circos\" id=\"display\" type=\"submit\">\n";
#print "</form>\n";
#print "<iframe scrolling=\"no\" src=\"\" id=\"myIframe3\" name=\"myIframe3\" frameborder=\"0\" style=\"height:1100px; overflow:hidden; width: 1100px\" src=\"#\"></iframe>\n";
#print "<script type=\"text/javascript\">jQuery(document).ready(function(){var loginform= document.getElementById(\"loginForm\");loginform.style.display = \"none\";loginform.submit();});</script>";

################################################################################
## genes and clusters
##################################################################################

my %cogcategories;
my %cog_by_species;
my %cogbigcategory_by_species;
open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt");
open(G,">$execution_dir/genes.txt");
print G "Gene\tStart\tEnd\tFunctional annotation\tCOG\tSpecies/Strain\tCluster\n";
while(<F>){
	my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
	if (/^(\w+\.1) (.*) \[(.*)\]$/){
		my $gene = $1;
		my $cluster = "#";
		if ($cluster_of_gene{$gene}){
			$cluster = $cluster_of_gene{$gene};
		}
		my $function = $2;
		my $species = $3;
		my $species_init = $species;
		$species_init =~s/ /_/g;
		my $start = $gene_positions2{$species_init}{$gene};
		my $end = $gene_positions3{$species_init}{$gene};	
		$species =~s/\]//g;
		$function =~s/'//g;
		$function =~s/"//g;
		$function =~s/\)//g;
		$function =~s/\(//g;
		$function =~s/,//g;
		my $cog = "#";
		if ($cogs{$gene} && $species =~/\w+/){
			$cog = $cogs{$gene};
			my $cogcat = $cog_categories{$gene};
			my $cog_bigcategory = $cogs_categories{$cogcat};
			$cogcategories{$cogcat}=1;
			$cog_by_species{$species}{$cogcat}++;
			$cogbigcategory_by_species{$species}{$cog_bigcategory}++;
		}
		print G "$gene\t$start\t$end\t$function\t$cog\t$species\t$cluster\n";
	}	
}
close(F);
close(G);

my $config_table = "";
$config_table .= qq~
				'core-genes'=>
                {
                        "select_title" => "Core-Genes",
                        "file" => "$execution_dir/coregenes.txt",
                },
        ~;
open(T,">$execution_dir/tables.conf");
print T $config_table;
close(T);


my $config_table4 = "";
$config_table4 .= qq~
                                'dispensable-genes'=>
                {
                        "select_title" => "Dispensable-Genes",
                        "file" => "$execution_dir/dispensablegenes.txt",
                },
        ~;
open(T,">$execution_dir4/tables.conf");
print T $config_table4;
close(T);

my $table_part = qq~
  <div id="clusters" class="tab-pane fade"><br/><b>$nb_core_genes Core-Genes</b>
<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>
  </div>~;
print $table_part;

#print "<div id=\"dispensable\" class=\"tab-pane fade\">";
#print "<form name=\"query_form\" id=\"query_form\">\n";
#print "<br/><table><tr><td>";
#print "Select the genomes in order to retrieve<br/>dispensable genes:&nbsp;&nbsp;</td>";
#print "<td><select name=\"strains\" id=\"strains\" multiple size=10>\n";

#foreach my $sample(sort @samples){
#        if ($sample =~/ClutserID/){next;}
#        print "<option value=\"$sample\">$sample</option>";
#}
#print "</select></br><br/>\n";

#print "<select name=\"nb_max_by_strain\" id=\"nb_max_by_strain\">\n";
#print "<option value=\"several\">Accept several representative genes by strain</option>";
#print "<option value=\"one\">Only one representative gene by strain</option>";
#print "</select></td>";
#print "<td>&nbsp;&nbsp;<input class=\"btn btn-primary\" type=\"button\" value=\"Submit\" onclick=\"SearchStrain('$Configuration::CGI_WEB_DIR','$session');\"></td>";
#print "</tr></table>";
#print "<br/><br/><br/>";
#print "</form>\n";
#print "<div id=results_div></div>";
#print "</div>";

my $table_part = qq~
  <div id="dispensable" class="tab-pane fade"><br/><b>$nb_dispensable_genes Dispensable Genes</b>
<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session4' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>
  </div>~;
print $table_part;

my $table_part = qq~
  <div id="specific" class="tab-pane fade"><br/><b>$nb_specific_genes Strain-Specific Genes</b><br/>
<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session3' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>
  </div>~;
print $table_part;


################################################################################
## COG
##################################################################################
my $execution_dir2 = $execution_dir."2";
mkdir($execution_dir2);
if (-e "$Configuration::DATA_DIR/pangenome_data/$project/cog_category_counts.txt"){

	open(COG,">$execution_dir/cog.txt");
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/cog_category_counts.txt");
	my $first = <F>;
	print COG $first;
	while(<F>){
		my @infos = split(/\t/,$_);
		my $sample = $infos[0];
		my @words = split(/_/,$sample);
		my $genus = $words[0];
		my $species = $words[1];
		my $shortname = substr($genus,0,3) . "_". substr($species,0,2);
		for (my $j = 2; $j <= $#words; $j++){
			$shortname.="_".$words[$j];
		}
		$shortname = substr($shortname,0,15);
		$_=~s/$sample/$shortname/g;
		print COG $_;
	}
	close(F);
	close(COG);

	open(BIGCOG,">$execution_dir/bigcog.txt");
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/cog_category_2_counts.txt");
	my $first = <F>;
        print BIGCOG $first;
	while(<F>){
                my @infos = split(/\t/,$_);
                my $sample = $infos[0];
                my @words = split(/_/,$sample);
                my $genus = $words[0];
                my $species = $words[1];
                my $shortname = substr($genus,0,3) . "_". substr($species,0,2);
                for (my $j = 2; $j <= $#words; $j++){
                        $shortname.="_".$words[$j];
                }
                $shortname = substr($shortname,0,15);
                $_=~s/$sample/$shortname/g;
                print BIGCOG $_;
        }
        close(F);
	close(BIGCOG);
}
else{
open(COG,">$execution_dir/cog.txt");
open(BIGCOG,">$execution_dir/bigcog.txt");
print COG "Sample	".join("\t",keys(%cogcategories))."\n";
print BIGCOG "Sample	".join("\t",keys(%cogs_categories_reverse))."\n";
foreach my $sample(sort keys(%cog_by_species)){

	my @words = split(/_/,$sample);
        my $genus = $words[0];
        my $species = $words[1];
        my $shortname = substr($genus,0,3) . "_". substr($species,0,2);
        for (my $j = 2; $j <= $#words; $j++){
                $shortname.="_".$words[$j];
        }
        $shortname = substr($shortname,0,10);


	#my $sample_short = substr($sample,0,20);
	#$sample_short =~s/ /_/g;
	#print "a"."$sample\n";
	#if (!$samples_displayed{substr($sample,0,40)}){next;}
	#print "$sample\n";
	print COG $shortname;
	foreach my $cogcat(keys(%cogcategories)){
		my $nb = 0;
		if ($cog_by_species{$sample}{$cogcat}){
			$nb = $cog_by_species{$sample}{$cogcat};
		}
		print COG "	$nb";
	}
	print COG "\n";

	print BIGCOG $shortname;
	foreach my $cogcat(keys(%cogs_categories_reverse)){
		my $nb = 0;
		if ($cogbigcategory_by_species{$sample}{$cogcat}){
			$nb = $cogbigcategory_by_species{$sample}{$cogcat};
		}
		print BIGCOG "	$nb";
	}
	print BIGCOG "\n";
}
close(COG);
close(BIGCOG);
}

my $config = qq~
'cogall1'=>
        {
                "select_title" => "Distribution of COG functional categories (percent)",
                "per_chrom" => "off",
                "title" => "Distribution of COG functional categories",
                "type" => "column",
                "group_padding" => "0",
                "stacking" => "percent",
                "yAxis" => "Relative abundance",
                "xAxis" => "Genomes",
                "file" => "$execution_dir/cog.txt"
        },
'cogall2'=>
        {
                "select_title" => "Distribution of COG functional categories (counts)",
                "per_chrom" => "off",
                "title" => "Distribution of COG functional categories",
                "type" => "column",
                "group_padding" => "0",
                "stacking" => "normal",
                "yAxis" => "Number of genes assigned",
                "xAxis" => "Genomes",
                "file" => "$execution_dir/cog.txt"
        },
'cogall3'=>
        {
                "select_title" => "Distribution of COG categories (percent)",
                "per_chrom" => "off",
                "title" => "Distribution of COG categories",
                "type" => "column",
                "group_padding" => "0",
                "stacking" => "percent",
                "yAxis" => "Relative abundance",
                "xAxis" => "Genomes",
                "file" => "$execution_dir/bigcog.txt"
        },

~;
open(F,">$execution_dir2/chrom_viewer.conf");
print F $config;
close(F);
my $session2 = $session."2";

my $graph_part = qq~
  <div id="cog" class="tab-pane fade">
<br/><iframe src='$Configuration::CGI_WEB_DIR/chrom_viewer.cgi?session=$session2' width='950' height='500' style='border:solid 0px black;'></iframe><br/><br/>
<pre>
INFORMATION STORAGE AND PROCESSING
0        [J] Translation, ribosomal structure and biogenesis
0        [A] RNA processing and modification
0        [K] Transcription
0        [L] Replication, recombination and repair
0        [B] Chromatin structure and dynamics

CELLULAR PROCESSES AND SIGNALING 
0        [D] Cell cycle control, cell division, chromosome partitioning
0        [Y] Nuclear structure
0        [V] Defense mechanisms
0        [T] Signal transduction mechanisms
0        [M] Cell wall/membrane/envelope biogenesis
0        [N] Cell motility
0        [Z] Cytoskeleton
0        [W] Extracellular structures
0        [U] Intracellular trafficking, secretion, and vesicular transport
0        [O] Posttranslational modification, protein turnover, chaperones

METABOLISM
0        [C] Energy production and conversion
0        [G] Carbohydrate transport and metabolism
0        [E] Amino acid transport and metabolism
0        [F] Nucleotide transport and metabolism
0        [H] Coenzyme transport and metabolism
0        [I] Lipid transport and metabolism
0        [P] Inorganic ion transport and metabolism
0        [Q] Secondary metabolites biosynthesis, transport and catabolism

POORLY CHARACTERIZED
0        [R] General function prediction only
0        [S] Function unknown
</pre>
</div>~;
print $graph_part;

################################################################################
# Phylogeny
################################################################################
my $newick = "";
open(my $NEWICK,"$Configuration::DATA_DIR/pangenome_data/$project/4.PanBased.Neighbor-joining.tree");
while(<$NEWICK>)
{
	my $line = $_;
	chomp($line);
	$newick .= $line;
}
close($NEWICK);

open(H,"$Configuration::HOME_DIR/phylotree/template.html");
open(H2,">$Configuration::HOME_DIR/phylotree/$session.html");
while(<H>){
	if (/MY_NEWICK_TREE/){
		chomp($newick);
		print H2 "var test_string = \"$newick\";\n";
	}
	else{
		print H2 $_;
	}
}
close(H);
close(H2);

#my $iframe = qq~
#<div id="matrix" class="tab-pane fade">
 #       <iframe width='100%' height='1000px' src=\"$Configuration::WEB_DIR/upsetr_pdf/$session.Accessory_heatmap.html\"/><br/>";
#</div>
#                ~;
#print $iframe;

my $iframe = qq~
<div id="phylogeny" class="tab-pane fade">
	<iframe src=\"$Configuration::WEB_DIR/phylotree/$session.html\" width=\"1000\" height=\"900\" style='border:solid 0px black;'></iframe>
</div>
                ~;
print $iframe;

################################################################################
# Circos
#################################################################################
print "<div id=\"distribution\" class=\"tab-pane fade\">";
print "<br/><br/><form id=\"loginForm\" target=\"myIframe3\" action=\"https://genomeharvest.southgreen.fr/visu/circosJS/demo/index.php\" method=\"POST\">\n";
print "<input type=\"hidden\" name=\"chromosome\" value=\"$Configuration::WEB_DIR/circosjs/$session.chrom_length.txt\" />\n";

print "<input type=\"hidden\" name=\"select[]\" id=\"annot\" value=\"Stack\" />\n";
print "<input type=\"hidden\" name=\"name[]\" id=\"annot\" value=\"density\" />\n";
print "<input type=\"hidden\" name=\"data[]\" id=\"annot\" value=\"$Configuration::WEB_DIR/circosjs/$session.circos_stack.txt\" />\n";


print "<input type=\"submit\">\n";
print "</form>\n";
print "<iframe src=\"\" id=\"myIframe3\" name=\"myIframe3\" width=\"1300px\" height=\"1600\" style='border:solid 0px black;zoom:0.8;-moz-transform: scale(0.8);-moz-transform-origin: 0 0;-o-transform: scale(0.8);-o-transform-origin: 0 0;-webkit-transform: scale(0.8);-webkit-transform-origin: 0 0;' src=\"#\"></iframe>\n";
print "<script>jQuery(document).ready(function(){var loginform= document.getElementById(\"loginForm\");loginform.style.display = \"none\";loginform.submit();});</script>";
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

