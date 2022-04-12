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
        <li class="active"><a href="#" onClick="window.location='./clusters.cgi?project='+document.getElementById('project').value;">Cluster Search</a></li>
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
#my $execution_dir2 = $execution_dir."2";
#if (!-d $execution_dir2){
#        mkdir($execution_dir2);
#}
#my $execution_dir3 = $execution_dir."3";
#if (!-d $execution_dir3){
#        mkdir($execution_dir3);
#}
#my $execution_dir4 = $execution_dir."4";
#if (!-d $execution_dir4){
#        mkdir($execution_dir4);
#}





open(TEST,">$execution_dir/test");
my $t = gmtime();
print TEST "$t\n";


print "<form name=\"query_form\" id=\"query_form\" action=\"./clusters.cgi\" method=\"get\">\n";
print "<table><tr><td><b>Enter a gene or cluster name </b><i>(ex: CLUSTER1736, AGJ99558.1)</i>: &nbsp;&nbsp;&nbsp;";
print "<input type=\"text\" name=\"genename\" id=\"genename\" value=\"$genename\"><br/><br/>";
print "<input type=\"hidden\" name=\"project\" id=\"project\" value=\"$project\"><br/><br/>";
print "<input class=\"btn btn-primary\" type=\"submit\" value=\"Submit\" onclick=\"GeneSearch('$Configuration::CGI_WEB_DIR','$session');\"></td>";
print "</tr></table>";
print "<br/>";
print "</form>\n";


my $nb_found = 0;
if ($genename){

	my %strains;
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
	my $first_line = <F>;
	$first_line =~s/\n//g;$first_line =~s/\r//g;
	my @speciesinfo = split("\t",$first_line);
	my $sequences = "";
	my $dnasequences = "";
	my $cluster;
	my $ngenes = 0;
	my $is_core = 0;
	open(C,">$Configuration::HOME_DIR/tables/$session.genes.txt");
	print C "Cluster\tGenes\tPositions\tSynonym\tFunction\tCOG\tSpecies\n";
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		my @i = split("\t",$line);
		my $clnb = $i[0];
		if (length($clnb) == 1){$clnb = "000".$clnb;}
		elsif (length($clnb) == 2){$clnb = "00".$clnb;}
		elsif (length($clnb) == 3){$clnb = "0".$clnb;}
		my $clustername = "CLUSTER".$clnb;
		
		if ($clustername eq $genename or $line =~/$genename/){
			
			for (my $j = 1; $j <= $#i; $j++){
				if ($i[$j] =~/\w+/){
					$nb_found++;
					my $gene = $i[$j];
					my $species = $speciesinfo[$j];
					my @genes = split(",",$gene);
					foreach my $gene(@genes){
						if ($gene eq ""){next;}
						$ngenes++;
						my $grep = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt`;
						my $function = "#";
						if ($grep =~/$gene (.*) \[/){
							$function = $1;
						}
						
						my $grep2 = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/COG_assignation.txt`;
						my $cog = "#";
						if ($grep2 =~/\w+/){
							my %cogs;
							my @cogids = split("COG",$grep2);
							foreach my $cogid(@cogids){
								if ($cogid =~/(\d+)\s(\w+)/){
									$cogs{"COG$1"}=1;
								}
							}
							$cog = join(", ",keys(%cogs));
						}
						
						if ($clustername =~/\w+/ && $gene=~/\w+/){
							$cluster = $clustername;
							my $grep4 = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.ptt`;
							my @infos = split("\t",$grep4);
							my $positions = $infos[0];
							my $synonym = $infos[4];
							
							my $grep3 = `grep -A 40 $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.faa`;
							print C "$clustername\t$gene\t$positions\t$synonym\t$function\t$cog\t$species\n";
							$strains{$gene} = $species;
							my @lines = split("\n",$grep3);
							my $locustag;
							foreach my $line(@lines){
								if ($line =~/>(.*) /){
									my $g = $1;
									if ($g =~/locus_tag=([^\]]+)/){
										$locustag = $1;
									}
									if ($g !~/$gene/){last;}
								}
								$sequences .= $line."\n";
							}
							my $grep4;
							if ($locustag){
								$grep4 = `grep -A 40 $locustag $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.fna`;
							}
							else{
								$grep4 = `grep -A 40 $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.fna`;
							}
							#if (!$grep4){print "error: $species.fna $gene<br/>";}
							my @lines = split("\n",$grep4);
							foreach my $line(@lines){
								if ($line =~/>(.*) /){
									my $g = $1;
									if ($g !~/$gene/ && $g !~$locustag){last;}
									my $strain = $strains{$gene};
									$line = ">$species"."_".$gene;
								}
								$dnasequences .= $line."\n";
							}

						}
					}
				}
			}
			if ($nb_found == $#i){
				$is_core = 1;
			}
		}
	}
	close(F);
	close(C);
	
	my $t = gmtime();
	print TEST "1 $t\n";

	open(FASTA,">$execution_dir/genes.fa");
	print FASTA $sequences;
	close(FASTA);

	open(FASTA,">$execution_dir/genes_dna.fa");
	print FASTA $dnasequences;
	close(FASTA);

	print "<b>$cluster ($ngenes genes)";
	if ($is_core == 1){print " (Core)";}
	elsif ($nb_found == 1){print " (Strain-specific)";}
	else{print " (Dispensable)";}
	print "<br/><br/></b>";	

	my $alignment = "";
	my %hash;
	my %hash2;
	
	###############################
	# MUSCLE
	###############################
	if ($ngenes < 20){
	system("$Configuration::MUSCLE_EXE -in $execution_dir/genes_dna.fa -out $execution_dir/genes_dna.align.fa");
	my $t = gmtime();
        print TEST "2 $t\n";
	system("$Configuration::MUSCLE_EXE -in $execution_dir/genes.fa -out $execution_dir/proteins.align.fa");
	
	my $t = gmtime();
        print TEST "2 $t\n";

	###############################
	# Discover SNPs
	###############################
	my %SNPs;
	my $strain;
	my %alignments;
	open(A,"$execution_dir/genes_dna.align.fa");
	while(<A>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		if ($line=~/>(.*)/){
			$strain = $1;
		}
		else{
			my @nt = split("",$line);
			$alignments{$strain} .= $line;
		}
	}
	close(A);
	
	foreach my $strain(keys(%alignments)){
		my $seq = $alignments{$strain};
		my @nt = split("",$seq);
		for (my $i = 0; $i <=$#nt; $i++){
			$hash{$strain}{$i}= $nt[$i];
			$SNPs{$i}{$nt[$i]}++;
			if ($nt[$i] eq "-"){
				delete($hash2{$i});next;
			}
			if ($hash2{$i} && $hash2{$i} ne $nt[$i]){
				$hash2{$i} .= $nt[$i];
			}
			elsif (!$hash2{$i}){
				$hash2{$i} = $nt[$i];
			}
		}
	}

	my @snps;
	foreach my $position(sort {$a<=>$b} keys(%hash2)){
		my $alleles = $hash2{$position};
		if (length($alleles) > 1){
			push(@snps,$position);
		}
	}

	my $snp_alignment = "";	
	foreach my $strain(keys(%hash)){
		
		my $strainname = $strains{$strain};
		my $strain2 = $strainname."_"."$strain";
		$snp_alignment .= ">$strain2\n";
		my $n=0;
		foreach my $position(sort {$a<=>$b} @snps){
						
			# do not print tri-allelic SNP because it will block network
			my $refsnp = $SNPs{$position};
			my %hashsnp = %$refsnp;
			if (scalar keys %hashsnp > 2){next;}
			
			my $allele = $hash{$strain}{$position};
			$snp_alignment .= $allele;
		}
		$snp_alignment .= "\n";
	}
	open(A,">$execution_dir/snp.align.fa");
	print A $snp_alignment;
	close(A);
	
	
	system("cp -rf $execution_dir/genes_dna.align.fa $Configuration::HOME_DIR/alignments/$session.genes.align.fa");
	system("cp -rf $execution_dir/proteins.align.fa $Configuration::HOME_DIR/alignments/$session.proteins.align.fa");
	
	
	
	###########################################
	# readseq
	###########################################
	my $input = "$execution_dir/genes_dna.align.fa";

	# replace by number to avoid truncation of long names
	my %correspondance;
	my $numseq = 0;
	open(F,"$input");
	open(O,">$input.with_number");
	while(<F>){
		if (/>(.*)$/){
			$numseq++;
			my $new_name = "seq".$numseq."end";
			print O ">$new_name\n";
			$correspondance{$numseq} = $1;
		}
		else{
			print O $_;
		}
	}
	close(F);
	close(O);
	my $phylip_file = "$execution_dir/genes_dna.align.fa.with_number.phylip";
	my $readseq_command = $Configuration::READSEQ_EXE . " $input.with_number -f 12 >>$execution_dir/readseq.log 2>&1";
	system($readseq_command);

	###########################################
	# DnaDist
	###########################################
	open(F,">$execution_dir/dnadist_script");
	print F "$phylip_file\n";
	print F "Y\n";
	close(F);

	my $matrix_file = "$execution_dir/gene.matrix";
	chdir($execution_dir);
	my $dnadist_command = $Configuration::DNADIST_EXE . " < $execution_dir/dnadist_script >>$execution_dir/dnadist.log 2>&1";
	system($dnadist_command);

	my $t = gmtime();
        print TEST "3 $t\n";

	rename("$execution_dir/outfile",$matrix_file);

	# replace -1.000000 par 9.999999
	open(M,$matrix_file);
	open(M2,">$matrix_file.2");
	while(<M>)
	{
		my $line = $_;
		$line =~s/\-1\.000000/9\.999999/g;
		print M2 $line;
		}
	close(M);
	close(M2);

	###########################################
	# FastMe
	###########################################
	my $treefile = "$execution_dir/gene.align_for_tree.ph";
	my $fastme_command = $Configuration::FASTME_EXE . " -i $matrix_file.2 -o $treefile >>$execution_dir/fastme.log 2>&1";
	system($fastme_command);
	
	# replace negative values by 0
	open(T,$treefile);
	open(T2,">$treefile.2");
	while(<T>){
		my $line = $_;
		$line =~s/\-\d+\.*\d*\,/0,/g;
		$line =~s/\-\d+\.*\d*\)/0\)/g;
		print T2 $line;
	}
	close(T);
	close(T2);

	my $t = gmtime();
        print TEST "4 $t\n";

	###########################################
	# ROOTING TREE
	###########################################
	my $rooting_command = $Configuration::ROOTING_EXE . " -input $treefile.2 -output $treefile.all -midpoint $treefile.midpoint >>$execution_dir/rooting.log 2>&1";
	system($rooting_command);
	
	
	my $newick = "";
	open(N,"$treefile.midpoint");
	while(<N>){
		foreach my $seqnumber(keys(%correspondance)){
			my $name = $correspondance{$seqnumber};
			my $to_be_replaced = "seq".$seqnumber."end";
			$_ =~s/$to_be_replaced/$name/g;
		}
		$newick .= $_;
	}
	close(N);
	
	my $prot_alignment = "";
	open(A,"$execution_dir/genes.align.fa");
	while(<A>){
		$prot_alignment .= $_;
	}
	close(A);
	
	
	#####################################################
	# Generate HTML pages (MSAViewer and phylotree)
	#####################################################
	system("sed \"s/session/$session/g\" $Configuration::HOME_DIR/MSAViewer/template.html >$Configuration::HOME_DIR/MSAViewer/$session.genes.html");
	system("sed \"s/genes/proteins/g\" $Configuration::HOME_DIR/MSAViewer/$session.genes.html >$Configuration::HOME_DIR/MSAViewer/$session.proteins.html");
	system("sed \"s/genes/snps/g\" $Configuration::HOME_DIR/MSAViewer/$session.genes.html >$Configuration::HOME_DIR/MSAViewer/$session.snps.html");
	system("sed \"s/MYSESSION/$session/g\" $Configuration::HOME_DIR/d3/template2.html >$Configuration::HOME_DIR/d3/$session.snp.d3.network.html");
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

	
	system("cp -rf $execution_dir/snp.align.fa $Configuration::HOME_DIR/alignments/$session.snps.align.fa");

	system("/opt/java/bin/java -jar $Configuration::TOOLS_DIR/haplophyle/NetworkCreator_fat.jar -in $execution_dir/snp.align.fa -out $execution_dir/snp.network.dot >> $execution_dir/haplophyle.log 2>&1");
	system("perl $Configuration::TOOLS_DIR/haplophyle/dot2Cytoscape.pl -i $execution_dir/snp.network.dot -h $Configuration::HOME_DIR/cytoscape/$session.snp.network.html >> $execution_dir/dot2cytoscape.log 2>&1");
	system("cp -rf $Configuration::HOME_DIR/cytoscape/$session.snp.network.html.d3.json $Configuration::HOME_DIR/d3/$session.snp.network.json");

	# add colors and increase node size in HTML cytoscape
	open(H,"$Configuration::HOME_DIR/d3/$session.snp.network.json");
	open(H2,">$Configuration::HOME_DIR/d3/$session.snp.network.json.2");
	while(<H>){
		my $line = $_;
		if (/color/ && /id\": \"([^"]+)\"/){
			my $id = $1;
			my ($null,$species) = split("_",$id);
			my $color = $Configuration::COLORS{$species};
			if ($color =~/\w+/){
				$_ =~s/grey/$color/;
			}
			my $size = 1;
			if (/size\": (\d+)/){
				if ($1 > 1){$size = 10;}
			}
			my $coma = ",";
			if ($line =~/]/){
				$coma = "],";
			}
			$line = "{\"id\": \"$id\", \"group\": 4, \"size\":$size, \"color\":\"$color\"}$coma\n";
		}
		print H2 $line;
	}
	close(H);
	close(H2);
	rename("$Configuration::HOME_DIR/d3/$session.snp.network.json.2","$Configuration::HOME_DIR/d3/$session.snp.network.json");
	}

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

	
	
	if ($ngenes < 20){
		my $tabs = qq~
<ul class="nav nav-tabs">
  <li class="active"><a data-toggle="tab" href="#cytoscape">Cytoscape network</a></li>
  <li><a data-toggle="tab" href="#genes">Genes</a></li>
  <li><a data-toggle="tab" href="#sequences">Sequences</a></li>
  <!--<li><a data-toggle="tab" href="#alignment">Alignments</a></li>-->
  <li><a data-toggle="tab" href="#phylogeny">Phylogeny</a></li>
  
</ul>
~;
	print $tabs;
	}
	else{
		my $tabs = qq~
<ul class="nav nav-tabs">
  <li class="active"><a data-toggle="tab" href="#genes">Genes</a></li>
  <li><a data-toggle="tab" href="#sequences">Sequences</a></li>

</ul>
~;
        print $tabs;
	}
	print "<div class=\"tab-content\">";
	print "<div id=\"genes\" class=\"tab-pane active\">";
	print $table_part;
	print "</div>";

	print "<div id=\"sequences\" class=\"tab-pane fade\">";	
	print "<br/><b>DNA sequences</b><br/>";
	print "<pre>$dnasequences</pre>";
	print "<br/><b>Protein sequences</b><br/>";
	print "<pre>$sequences</pre>";
	print "<br/>";
	print "</div>";

	print "<div id=\"alignment\" class=\"tab-pane fade\">";
	print "<br/><b>Alignment of genes</b><br/>";	
	print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.genes.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	print "<br/><br/><b>Alignment of SNPs</b><br/>";
	
	print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.snps.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	print "<br/><br/><b>Alignment of proteins</b><br/>";
	
	print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.proteins.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	print "</div>";	
	
	print "<div id=\"phylogeny\" class=\"tab-pane fade\">";	
	print "<iframe src=\"$Configuration::WEB_DIR/phylotree/$session.html\" width=\"1000\" height=\"900\" style='border:solid 0px black;'></iframe>";			
	print "</div>";	

	if ($ngenes < 20){	
	print "<div id=\"cytoscape\" class=\"tab-pane active\">";	
	print "<br/>";
	print "</div>";
	}

	if ($ngenes < 20){	
		print "<br/><iframe src='$Configuration::WEB_DIR/d3/$session.snp.d3.network.html' width='950' height='900' style='border:solid 1px black;'></iframe>";
	}
	print "</div>";
	
	
	
}
print "</div>";
my $footer = qq~
<footer>
<hr>
<div class="container" style="text-align: center;">
                    <p>Copyright &copy; 2021, CIRAD | Designed by <a target="_blank" href="https://www.southgreen.fr/">South Green Bioinformatics platform</a>.</p>
                </div>
</footer>~;

print $footer;
#print "<div id=results_div>";








