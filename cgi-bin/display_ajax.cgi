#!/usr/bin/perl -w

=pod

=head1 NAME

display_ajax.cgi - displays an html page for ajax.

=head1 SYNOPSIS

=head1 REQUIRES

=head1 DESCRIPTION

Displays an an html page for ajax.

=cut

use strict;
use warnings;
use Carp qw (cluck confess);

use DBI;
use CGI;
#use CGI::Session;
use Config::Configuration;
use CGI::BaseCGI2;

use POSIX ":sys_wait_h";


my %cogs_categories_reverse = (
	"INFORMATION STORAGE AND PROCESSING"=>"JAKLB",
	"CELLULAR PROCESSES AND SIGNALING"=>"DYVTMNZWUO",
	"METABOLISM"=>"CGEFHIPQ",
	"POORLY CHARACTERIZED"=>"RS"
);

my %colors1 = (
	"INFORMATION STORAGE AND PROCESSING"=>"green",
	"CELLULAR PROCESSES AND SIGNALING"=>"turquoise",
	"METABOLISM"=>"red",
	"POORLY CHARACTERIZED"=>"blue"
);

my %colors = (
	"3" => "#70B860",
	"1" => "blue",
	"2" => "red"
);

#############
# CODE START
#############





#my $cgi = CGI->new();
my $cgi = CGI::BaseCGI2 -> new();
$cgi -> headHTML("pangenomexplorer");
my $session;
if ($cgi -> param('session') =~/(\d+)/)
{
	$session = $1;
}
my $strains;
if ($cgi -> param('strains') =~/([\w\,\-\.]+)/){
	$strains = $1;
}
my $strain1;
if ($cgi -> param('strain1') =~/([\w\,\-\.]+)/){
	$strain1 = $1;
}
my $strain2;
if ($cgi -> param('strain2') =~/([\w\,\-\.]+)/){
	$strain2 = $1;
}
my $strain3;
if ($cgi -> param('strain3') =~/([\w\,\-\.]+)/){
	$strain3 = $1;
}
my $action;
if ($cgi -> param('action') =~/([\w\,]+)/){
	$action = $1;
}
my $feature;
if ($cgi -> param('feature') =~/([\w\,]+)/){
	$feature = $1;
}
my $nb_max_by_strain;
if ($cgi -> param('nb_max_by_strain') =~/([\w\,]+)/){
        $nb_max_by_strain = $1;
}
my $project;
if ($cgi -> param('project') =~/([\w\,\.]+)/){
        $project = $1;
}
my $cl;
if ($cgi -> param('cluster') =~/([\w]+)/){
	$cl = $cgi -> param('cluster');
}
my $genbanks;
if ($cgi -> param('genbanks') =~/([\w\.,]+)/){
        $genbanks = $cgi -> param('genbanks');
}
my $software = $cgi -> param('software');
my $projectnew;
if ($action eq "test"){
print "ok";	
}

if ($action eq "check_id"){
	if ($cgi -> param('projectnew') =~/(^[\w]+)$/){
	        $projectnew = $cgi -> param('projectnew');
	}
	else{
		print "<div class=\"alert alert-danger\" role=\"alert\">Project name is not valid </div>";exit;
	}
	my @genbank_ids = split(",",$genbanks);
        if (scalar @genbank_ids > 60){
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
		foreach my $genbank(@genbank_ids){
                        if ($genbank =~/([\w\.]+)/){
                                $genbank = $1;
                                my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -mode text >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #my $wget = `wget -O $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.uid https://www.ncbi.nlm.nih.gov/nuccore/$genbank?report=gilist&format=text`;
				#my $ok = 0;
				#open(F,"$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.uid");
				#while(<F>){
				#	if (/pre\>\d+/){$ok = 1;}
				#}
				#close(F);	
				
				#my $curl = `curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=$genbank&rettype=gb&retmode=txt" >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb`;	
				#sleep(30);
				#system("/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -mode text >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json");
				#system("/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format ft >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.ft");
				#if ($ok == 1){
					
                                 #       print "GENBANK_ID".$genbanks."GENBANK_ID";
				#	my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -mode text | head -200 >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
				#	exit;
					
                                #}
                                #else{
                                 #       print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Identifier is not found in Genbank $ok";exit;
                                #}
				#print "GENBANK_ID".$genbanks."GENBANK_IDERROR..";exit;
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
				if ($genus !~/\w+/){
					#print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Identifier is not found in Genbank";
					$not_found = $genbank;last;
				}
                                if ($contain_genes == 0){
					#print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Identifier is not found in Genbank";
                                        $not_annotated = $genbank;last;
                                }
                                if ($strain && $genus =~/\w+/){
                                        my ($info1,$info2 ) = split(",",$strain);
                                        $strain = $info1;
                                        $strain =~s/ /_/g;
                                        $strain_names{$strain}++;
                                        my $indice = $strain_names{$strain};
                                        if ($indice > 1){$duplicated_strain = $strain;}
                                        $strains{$genbank} = $strain;
					print "GENBANK_ID".$genbanks."GENBANK_ID"."$strain ($contain_genes genes)<br>";
                                        rename("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json","$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.json");
                                        $nbok++;exit;
                                }
                        }
                }
		if ($not_found && $nbok < scalar @genbank_ids){
			print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Identifier is not found in Genbank";
                }
                elsif ($not_annotated && $nbok < scalar @genbank_ids){
			print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Genome is not annotated";
                }
		else{
			#print "GENBANK_ID".$genbanks."GENBANK_IDERROR: Identifier is not found in Genbank";exit;
		}
	}
}
if ($action eq "check_ids"){

	if ($cgi -> param('projectnew') =~/(^[\w]+)$/){
                $projectnew = $cgi -> param('projectnew');
        }
        else{
                print "<div class=\"alert alert-danger\" role=\"alert\">Project name is not valid </div>";exit;
        }	
	my @genbank_ids = split(",",$genbanks);
	my $grep = `grep -c 'species' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/*.json | grep -v ':0'`;
	my @lines = split(/\n/,$grep);
	if (scalar @genbank_ids == scalar @lines){
		print "<br/><br/>Genbank identifiers have been checked successfully...<br>";
		print "<input class=\"btn btn-primary\" type=\"button\" id=\"submission\" value=\"Submit\" onclick=\"document.getElementById('submission').style.visibility = 'hidden';Upload('$Configuration::CGI_WEB_DIR','$session','$genbanks','$projectnew','$software');\">";
                print "<br/><br/><div id=results_div></div>";
	}
	else{
		print "<div class=\"alert alert-danger\" role=\"alert\">Some of the identifiers provided are not allowed</div>";exit;
	}
	
}
my $email;
if ($cgi -> param('email') =~/([\w\.\@]+)/){
        $email = $cgi -> param('email');
}
my $execution_dir = "$Configuration::TEMP_EXECUTION_DIR/$session";
if (!-d $execution_dir){
	mkdir($execution_dir);
}
$feature = "gcpercent";
my $SCRIPT_NAME = "display_ajax.cgi";

	    
#print $cgi->header();




###########################################
# parsing and filtering 
############################################
my %gene_positions;
my %gene_positions2;
my %gene_positions3;
my %gene_strands;
my %functions;
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
			my $strand = $infos[1];
			my $gene = $infos[3];
			my $function = $infos[8];
			$functions{$gene} = $function;
			$gene_positions{$strain}{$start} = $gene;
			$gene_positions2{$strain}{$gene} = $start;
			$gene_positions3{$strain}{$gene} = $end;
			$gene_strands{$strain}{$gene} = $strand;
		}
		close(F);
	}
}
close(LS);


my %cogs;
my %cog_categories;
open(C,"$Configuration::DATA_DIR/pangenome_data/$project/COG_assignation.txt");
while(<C>){
	my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
	my ($gene,$cog,$cogcat) = split("\t",$line);
	$cogs{$gene} = $cog;
	$cog_categories{$gene} = $cogcat;
}
close(C);

my %taxonomy;
open(C,"$Configuration::DATA_DIR/taxonomy/mytaxonomy.txt");
while(<C>){
	my $line = $_;$line =~s/\n//g;$line =~s/\r//g;
	my ($strain,$taxid) = split(" ",$line);
	$taxonomy{$strain} = $taxid;
}
close(C);

my %cluster_of_gene;
my %genes_of_cluster;
my %core_genes;
my %core_genes_simple;
my %strain_specific_genes;
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
while(<F>){
	my $line = $_;
	$line =~s/\n//g;$line =~s/\r//g;
	my @i = split("\t",$line);
	my $clnb = $i[0];
	if (length($clnb) == 1){$clnb = "000".$clnb;}
	elsif (length($clnb) == 2){$clnb = "00".$clnb;}
	elsif (length($clnb) == 3){$clnb = "0".$clnb;}
	my $name = "CLUSTER".$clnb;
	my $nb_found = 0;
	my $concatenate_samples = "";
	for (my $j = 1; $j <= $#i; $j++){
		my $val = $i[$j];
		if ($val =~/\w+/){
			my @genes = split(",",$val);
			foreach my $gene(@genes){
				$cluster_of_gene{$gene} = $name;
				$genes_of_cluster{$name}.=",$gene";
			}
			$nb_found++;
			$concatenate_samples .=",".$samples[$j];
		}
	}
	$hash_concatenate_samples{$concatenate_samples}.=",$name";

	##############################
	# core-genes
	##############################
	if ($nb_found == $#i){
		my @genes = split(",",$genes_of_cluster{$name});

		#core-genes with only one representant by strain
		my $is_coregene_simple = 0;
		if (scalar @genes == ($nb_found+1)){
			$is_coregene_simple = 1;
		}
		my %cogs_of_cluster;
		my %cogcats_of_cluster;
		foreach my $gene(@genes){
			$core_genes{$gene} = 1;
			if ($is_coregene_simple){$core_genes_simple{$gene} = 1;}
			my $cog = $cogs{$gene};
			my $cogcat1 = $cog_categories{$gene};
			$cogs_of_cluster{$cog} = 1;
			$cogcats_of_cluster{$cogcat1}=1;
		}
		$core_genecluster{$name} = 1;
		my $cogs_concat = "#";
		if (join(",",keys(%cogs_of_cluster))){
			$cogs_concat = join(",",keys(%cogs_of_cluster));
		}
		my $cogcats_concat = "#";
		if (join(",",keys(%cogcats_of_cluster))){
			$cogcats_concat  = join(",",keys(%cogcats_of_cluster));
		}
	}
	elsif ($nb_found == 1){
		my @genes = split(",",$genes_of_cluster{$name});
		foreach my $gene(@genes){
			$strain_specific_genes{$gene} = 1;
		}
	}
}
close(F);

#########################################################################
## upload
#########################################################################

if ($action eq "upload"){
	my %strains;
	if ($cgi -> param('projectnew') =~/(^[\w]+)$/){
                $projectnew = $cgi -> param('projectnew');
        }
	open(LS,"ls $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/*gbff.gz |");
        while(<LS>){
                if (/\/([^\/]*)\.gbff.gz/){
                        my $strain = $1;

                        my $grep_id = `zgrep 'LOCUS' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.gbff.gz | head -1`;
                        if ($grep_id =~/LOCUS\s+(\w+)\s+/){
                                my $genbank = $1;
                                $genbank =~s/\n//g;$genbank =~s/\r//g;
                                $strains{$genbank} = $strain;
                        }
                }
        }
        close(LS);

	my $options = join(",",keys(%strains));
	my $cmd = "perl /www/panexplorer.southgreen.fr/prod/cgi-bin/GetSequences.pl -i $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes";
	system($cmd);
	if ($software eq 'roary'){
		my $cmd = "perl /www/panexplorer.southgreen.fr/prod/cgi-bin/Run_Roary_bioblend.pl -i $options -p $projectnew -e $email -o $execution_dir ";
		system($cmd);
	}
	else{
		my $cmd = "perl /www/panexplorer.southgreen.fr/prod/cgi-bin/Run_PGAP_bioblend.pl -i $options -p $projectnew -e $email -o $execution_dir ";
		system($cmd);
	}
	#system("cp -rf $execution_dir/Galaxy1-\[Orthologs_Clusters\].txt $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/1.Orthologs_Cluster.txt");

}
#############################################################
# Check genebank identifiers
#############################################################
if ($action eq "check_idsii"){
	if ($projectnew =~/(^[\w]+)$/){
        }
        else{
                print "<div class=\"alert alert-danger\" role=\"alert\">Project name is not valid</div>";exit;
        }

        my @genbank_ids = split(",",$genbanks);
        if (scalar @genbank_ids < 3){
                print "<div class=\"alert alert-danger\" role=\"alert\">You must provide at least 3 Genbank identifiers of bacterial genomes</div>";exit;
        }
        elsif (scalar @genbank_ids > 20){
                print "<div class=\"alert alert-danger\" role=\"alert\">Too many Genbank identifiers (maximum 20)</div>";exit;
        }
        else{
                my $nbok = 0;
                my $not_found = 0;
		mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew");
                mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes");
                mkdir("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes");
                my %strains;
                print "<div class=\"alert alert-success\" role=\"alert\">";
                print "Check Genbank...<br>";
                foreach my $genbank(@genbank_ids){
                        if ($genbank =~/([\w\.]+)/){
                                $genbank = $1;
				my $grep = `grep 'gi ' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json | head -1`;
				if ($grep =~/gi (\d+)$/){$genbank = $1;}
                                my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format gb >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb`;
                                my $strain = `grep 'DEFINITION' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb`;
                                if ($strain =~/DEFINITION  (.*)$/){
                                        $strain = $1;
                                        my ($info1,$info2 ) = split(",",$strain);
                                        $strain = $info1;
                                        $strain =~s/ /_/g;
                                        $strains{$genbank} = $strain;
                                        rename("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb","$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.gb");
                                        $nbok++;
                                        print "$genbank : ok => $strain<br>";
                                }
                                else{
                                        $not_found = $genbank;last;
                                }
                        }
                }
                print "</div>";
                if ($nbok < scalar @genbank_ids){
                        print "<div class=\"alert alert-danger\" role=\"alert\">One of the identifiers provided is not found in Genbank: $not_found</div>";exit;
                }
                print "<div class=\"alert alert-success\" role=\"alert\">";
                print "Genbank identifiers have been checked successfully...<br>";
		print "</div>";
                print "<br/><br/><div id=results_div>";
		print "<input class=\"btn btn-primary\" type=\"button\" id=\"submission\" value=\"Submit\" onclick=\"document.getElementById('submission').style.visibility = 'hidden';//Upload('$Configuration::CGI_WEB_DIR','$session','$genbanks','$projectnew');\">";
		print "</div>";
                exit;
	}
}
#############################################################
# Search strain-specific strains
#############################################################
if ($action eq "search"){
	my @strains2 = split(",",$strains);
	my $concatenate_strains = join(",",sort @strains2);
	my %cluster_of_gene;
	my %genes_of_cluster;
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
	open(C,">$Configuration::HOME_DIR/tables/$session.dispensablegenes.txt");
	print C "Cluster\tGenes\tFunction\n";
	my $first_line = <F>;
	$first_line =~s/\n//g;$first_line =~s/\r//g;
	my @samples = split("\t",$first_line);
	my $found = 0;
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		my @i = split("\t",$line);
		my $clnb = $i[0];
		if (length($clnb) == 1){$clnb = "000".$clnb;}
		elsif (length($clnb) == 2){$clnb = "00".$clnb;}
		elsif (length($clnb) == 3){$clnb = "0".$clnb;}
		my $name = "CLUSTER".$clnb;
		my $nb_found = 0;
		my $concatenate_samples = "";
		my @samples_specific;
		for (my $j = 1; $j <= $#i; $j++){
			my $val = $i[$j];
			if ($val =~/\w+/){
				my @genes = split(",",$val);
				foreach my $gene(@genes){
					$cluster_of_gene{$gene} = $name;
					$genes_of_cluster{$name}.=",$gene";
				}
				$nb_found++;
				$concatenate_samples .=",".$samples[$j];
				push(@samples_specific,$samples[$j]);
			}
		}
		my $concatenate_samples = join(",",sort @samples_specific);
		if (scalar @strains2 == scalar @samples_specific && $concatenate_strains eq $concatenate_samples){
			my @gene_list = split(",",$genes_of_cluster{$name});
			my $function;
			foreach my $gene(@gene_list){
				$function = $functions{$gene};
			}
			
			my $list_to_displayed = substr($genes_of_cluster{$name},0,50);

			# exclude if several reprensentant by strain (if restriction is checked)
			my $nb_genes = scalar split(",",$genes_of_cluster{$name})-1;
			if ($nb_max_by_strain eq "one" && scalar @strains2 != $nb_genes){next;}


			print C "<a href='./clusters.cgi?genename=$name&project=$project' target=_blank>$name</a>\t$list_to_displayed\t$function\n";
			$found++;
		}
	}
	close(F);
	close(C);


	print "<b>$found gene cluster(s) found</b></br>";

	my $config_table = "";
	$config_table .= qq~
					'dispensable-genes'=>
					{
							"select_title" => "Dispensable-Genes",
							"file" => "$Configuration::HOME_DIR/tables/$session.dispensablegenes.txt",
					},
			~;
	open(T,">$execution_dir/tables.conf");
	print T $config_table;
	close(T);

	my $table_part = qq~
	<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='950' height='550' style='border:solid 0px black;'></iframe><br/><br/>
	<a href='$Configuration::WEB_DIR/tables/$session.dispensablegenes.txt'>Download table</a><br/>
	~;
	print $table_part;
}

###############################################################################
# Hive plot and Circos
###############################################################################
elsif (($action eq "synteny" && $strain1 && $strain2 && $strain3) or ($action eq "circos" && $strains)){
	
	my %strains_for_hiveplot = ("$strain1"=>1,"$strain2"=>1,"$strain3"=>1);

	if (!$strain1){
		
		my @strains_to_be_displayed = split(",",$strains);
		foreach my $strain(@strains_to_be_displayed){
			$strains_for_hiveplot{$strain} = 1;
		}
	}
	
	system("sed \"s/444444444444444/$session/g\" $Configuration::HOME_DIR/hiveplot_json/test.html >$Configuration::HOME_DIR/hiveplot_json/hiveplot.$session.html");
	open(JSON,">$Configuration::HOME_DIR/hiveplot_json/data.$session.json") or print "Can not write file $Configuration::HOME_DIR/hiveplot_json/data.$session.json";
	#open(CIRCOS,">$Configuration::HOME_DIR/circosjs/$session.circos_stack.txt");
	open(CIRCOS,">/www/panexplorer.southgreen.fr/prod/htdocs/circosjs/$session.circos_stack.txt");

	#print "$session.circos_stack.txt";
	print JSON "[\n";
	my $group = 0;
	my $jsondata = "";
	my $json_mauve = "";
	# define order and node number in each axis for each selected genes
	my %ordering;
	my %ordering2;
	my %hash_mauve;
	foreach my $strain(keys(%gene_positions)){
		if (!$strains_for_hiveplot{$strain}){next;}
		my $refhash = $gene_positions{$strain};
		my %hash2=%$refhash;
		my $node = 0;
		foreach my $start(sort {$a<=>$b} keys(%hash2)){
			my $gene = $gene_positions{$strain}{$start};
			if ($core_genes_simple{$gene}){
				$node++;
				$ordering{$gene} = $node;
				$ordering2{$strain}{$node} = $gene;
			}
		}
	}
	my $previous_strain;
	my $max_size_chrom = 0;
	my $legend_circos = "Tracks (from outside in)\n";
	# associate targets and write json data
	my $num_track = 0;
	my %heatmap;
	my %heatmap_extreme;
	$heatmap_extreme{"min"} = 1;
	my $node_number = 0;
	my %links;
	my @strains_to_compared = ($strain1,$strain2,$strain3);
	if (!$strain1){
		@strains_to_compared = split(",",$strains);
	}
	if (-e "$Configuration::DATA_DIR/pangenome_data/$project/GCpercent/GCpercent"){
		my %h;
		open(F,"$Configuration::DATA_DIR/pangenome_data/$project/GCpercent/GCpercent");
		while(<F>){
			if (/^#/){next;}
			my ($chr_strain) = split("\t",$_);
			$h{$chr_strain}.=$_;
		}
		foreach my $st(keys(%h)){
			open(GC,">$Configuration::DATA_DIR/pangenome_data/$project/GCpercent/$st.genome.GC_content");
			my $file_content = $h{$st};
			$file_content =~s/$st\t//g;
			print GC $file_content;
			close(GC);
		}
		system("mv $Configuration::DATA_DIR/pangenome_data/$project/GCpercent/GCpercent $Configuration::DATA_DIR/pangenome_data/$project/GCpercent/GCpercent.converted");
	}

	$legend_circos .= "1) Genes (<font color='red'>forward</font> and reverse)\n";
	$legend_circos .= "2) Core-Genes\n";
	$legend_circos .= "3) Strain-specific Genes\n";
	$legend_circos .= "4) GC content: deviation of GC percent from the average\n";
	foreach my $strain(@strains_to_compared){
		if ($strain !~/\w/){next;}
		$num_track++;
		#$legend_circos .= "$num_track) $strain (genes: forward in red and reverse in black)\n";
		# search taxnomy id corresponding to the strain
		my ($genus,$spec,$additional) = split("_",$strain);
		my $genus_species = $genus."_".$spec;
		my $taxid = `grep $genus $Configuration::DATA_DIR/taxonomy/mytaxonomy.txt | grep $spec | grep $additional`;
		if ($taxid =~/\| (\d+\.\d+)/){$taxid = $1;}
		#print "$strain => $taxid<br>";
		if (!$taxid){$taxid = "1335053";}	
		if ($action eq "circos" && $feature eq "gcpercent"){	
			open(GC,"$Configuration::DATA_DIR/pangenome_data/$project/GCpercent/$strain.genome.GC_content");
			<GC>;
			my $sum = 0;
			my $count = 0;
			while(<GC>){
				my $line = $_;
				$line =~s/\n//g;$line =~s/\r//g;
				my ($c,$start,$end,$gcpercent) = split(" ",$line);
				$sum+=$gcpercent;
				$count++;
				$heatmap{$start}{$strain} = $gcpercent;
				if ($gcpercent < $heatmap_extreme{"min"}){
					$heatmap_extreme{"min"} = $gcpercent;
				}
				if ($gcpercent > $heatmap_extreme{"max"}){
					$heatmap_extreme{"max"} = $gcpercent;
				}
			}
			close(GC);
			$heatmap_extreme{$strain}{"average"} = $sum / $count;
		}
		
		$group++;
		my $circos_genes = "";
		my $circos_specific = "";
		my $previous = 0;
		open(GENES,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$strain.ptt");
		while(<GENES>){
			my $line = $_;
			$line =~s/\n//g;$line =~s/\r//g;
			my @infos = split("\t",$line);	
			if ($infos[0] =~/\.\./){
				my ($start,$end) = split(/\.\./,$infos[0]);
				my $strand = $infos[1];
				my $name = $infos[3];
				if ($start <= $previous){
					$start = $previous+1;
				}
				if ($strand eq "+"){
					$circos_genes .= "Chr $start $end red black $name\n";
					$circos_genes .= "Chr $start $end red black $name\n";
				}
				else{
					$circos_genes .= "Chr $start $end black black $name\n";
					$circos_genes .= "Chr $start $end black black $name\n";
				}
				if ($strain_specific_genes{$name}){
					my $cog_cat = $cog_categories{$name};
					my $col = "purple";
                                	foreach my $cat(keys(%cogs_categories_reverse)){
                                        	my $val = $cogs_categories_reverse{$cat};
                                        	if ($cat =~/$cog_cat/){
                                                	$col = $colors1{$cat};
                                        	}
                                	}
					$circos_specific .= "Chr $start $end $col specific $name\n";
					$circos_specific .= "Chr $start $end $col specific $name\n";
				}
				$previous = $end;
			}
		}
		close(GENES);
		my $refhash = $ordering2{$strain};
		my %hash2=%$refhash;
		my $previous_point = 1;
		my $circos_blue = "";
		foreach my $node(sort {$a<=>$b} keys(%hash2)){
			my $gene = $ordering2{$strain}{$node};
			my $start = $gene_positions2{$strain}{$gene};
			my $end = $gene_positions3{$strain}{$gene};
			my $cluster = $cluster_of_gene{$gene};
			my $strand = $gene_strands{$strain}{$gene};
			#$node_number++;
			$hash_mauve{$cluster} .= "{\"name\": \"$taxid.fasta\",\"start\": $start,\"end\": $end,\"strand\": \"$strand\",\"lcb_idx\": $num_track},";
			
			my @genes = split(",",$genes_of_cluster{$cluster});

			my $node_target;
			foreach my $gene_target(@genes){

				# target only genes belonging to previous strain

				if ($ordering{$gene_target} && $gene_positions2{$previous_strain}{$gene_target}){
					$node_target = $ordering{$gene_target};
				}
			}
			my $point_name = $strain."_".$gene;
			my $end = $start + 1000;
			if ($end > $max_size_chrom){$max_size_chrom=$end;}
			my $start2 = $start+1;
			if ($start2 < $previous_point){
				$start2 = $previous_point+1;
			}
			
			my $color = "purple";
			if ($feature){
				$color = "purple";
				my $cog = $cog_categories{$gene};
				foreach my $cat(keys(%cogs_categories_reverse)){
					my $val = $cogs_categories_reverse{$cat};
					if ($cat =~/$cog/){
						$color = $colors1{$cat};
					}
				}
			}
			#if ($feature && $feature eq "coregenes2"){
			#	$color = "purple";
			#	my ($genus) = split("_",$strain);
			#	$color = $Configuration::COLORS{$genus};
			#}
			$links{$cluster}.= "$node_number,";
			$circos_blue .= "Chr $start2 $end $color blue $gene\n";
			$circos_blue .= "Chr $start2 $end $color blue $gene\n";
			my $color_to_applied = $colors{$group};
			if ($cluster eq $cl){$color_to_applied = "yellow";}
			if (!$node_target){
				$jsondata .= "{\"name\":\"$cluster:$gene:$strain\",\"group\":$group, \"y\": $start , \"color\" :\"".$color_to_applied."\" },\n";
			}
			else{
				my @infos_links = split(",",$links{$cluster});	
				$jsondata .= "{\"name\":\"$cluster:$gene:$strain\",\"group\":$group, \"y\": $start, \"color\" :\"".$color_to_applied."\", \"targets\": [";
				foreach my $node_to_be_linked(@infos_links){
					if ($node_to_be_linked == $node_number){next;}
					$jsondata .= "{\"node\": $node_to_be_linked, \"value\": 2},";
				}
				chop($jsondata);
				$jsondata .= "]},\n";
			}
			$previous_point = $end+1;
			$node_number++;
		}
		$previous_strain = $strain;
		print CIRCOS $circos_genes;
		print CIRCOS "Chr 1 10 white blank1 genename\n";
		print CIRCOS "Chr 1 10 white blank1 genename\n";
		print CIRCOS $circos_blue;
		print CIRCOS "Chr 1 10 white blank2 genename\n";
                print CIRCOS "Chr 1 10 white blank2 genename\n";
		print CIRCOS $circos_specific;
	}
	chop($jsondata);chop($jsondata);
	print JSON "$jsondata\n";
	print JSON "]\n";
	close(JSON);
	close(CIRCOS);

	#open(CHROM_LENGTH,">$Configuration::HOME_DIR/circosjs/$session.chrom_length.txt");
	open(CHROM_LENGTH,">/www/panexplorer.southgreen.fr/prod/htdocs/circosjs/$session.chrom_length.txt");
	print CHROM_LENGTH "Chr $max_size_chrom\n";
	close(CHROM_LENGTH);


	if ($action eq "synteny"){
		
		my $concat = "";
		foreach my $cluster(keys(%hash_mauve)){
			my $info = $hash_mauve{$cluster};
			chop($info);
			$concat .= "[$info],\n";
		}
		chop($concat);
		chop($concat);
		# write JSON for Mauve
		open(J,">$Configuration::HOME_DIR/mauve_viewer/mauve-viewer/demo/data/$session.json");
		print J "[\n";
		print J $concat."\n";
		print J "]\n";
		close(J);
		# write HTML for Mauve
		system("sed \"s/5-brucella.json/$session.json/g\" $Configuration::HOME_DIR/mauve_viewer/mauve-viewer/demo/index.html >$Configuration::HOME_DIR/mauve_viewer/mauve-viewer/demo/$session.html");
		
		
		
		my $tabs = qq~
<ul class="nav nav-tabs">
  <li class="active"><a data-toggle="tab" href="#hiveplot">Hive plot</a></li>
  <li><a data-toggle="tab" href="#mauve">Mauve viewer</a></li>

</ul>
~;
		my $macrosynteny_part = qq~
		Each node is a cluster of the core-genome.<br/>
		
		<iframe src='https://panexplorer.southgreen.fr/hiveplot_json/hiveplot.$session.html' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>~;
		print $macrosynteny_part;
		
		print "<br/><iframe src='https://panexplorer.southgreen.fr/mauve_viewer/mauve-viewer/demo/$session.html' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>";
	}
	
	
	
	if ($action eq "circos"){
		$legend_circos .= "\n\nCore-Genes and strain-specific genes are colored according to COG category:\n";
		foreach my $cogtype(keys(%colors1)){
			my $color = $colors1{$cogtype};
			$legend_circos .= "<font color='$color'>$cogtype</font>\n";
		}
		$legend_circos .= "<font color='purple'>NO COG ASSIGNED</font>\n";
		print "<form id=\"loginForm\" target=\"myIframe3\" action=\"$Configuration::WEB_DIR/circosJS/demo/index.php\" method=\"POST\">\n";
		#print "<input type=\"hidden\" name=\"userUrl\" id=\"userUrl\" value=\"www.google.fr\" />\n";
		print "<input type=\"hidden\" name=\"chromosome\" value=\"$Configuration::WEB_DIR/circosjs/$session.chrom_length.txt\" />\n";
		if ($feature eq "gcpercent"){
		
			open(CIRCOS,">/www/panexplorer.southgreen.fr/prod/htdocs/circosjs/$session.circos_line.txt");
			#print "Minimum: " . $heatmap_extreme{"min"}."<br>";
			#print "Maximum: " . $heatmap_extreme{"max"}."<br>";
			#print "Mediane: $mediane /www/panexplorer.southgreen.fr/prod/htdocs/circosjs/$session.circos_line.txt<br>";
			foreach my $pos(sort {$a<=>$b}keys(%heatmap)){
				my $start = $pos;
				my $end = $start + 1000;
				foreach my $strain(sort keys(%ordering2)){
					my $average = $heatmap_extreme{$strain}{"average"};
					if ($heatmap{$pos}{$strain}){
						my $gcpercent = $heatmap{$pos}{$strain};
						my $gamme = $heatmap_extreme{"max"} - $heatmap_extreme{"min"};
						my $multiplicateur = 1 / $gamme;
						my $diff_to_average = ($gcpercent - $average) * 100;
						my $level = ($gcpercent-$heatmap_extreme{"min"}) * $multiplicateur;

						my $color_hex = rgbToHex(255,255-($level*255),255);
						#print "$level<br>";
						$color_hex =~s/\n//g;$color_hex =~s/\r//g;$color_hex =~s/ //g;
						#print CIRCOS " $gcpercent";
						#print CIRCOS "Chr $start $end $color_hex $strain\n";
						#print CIRCOS "Chr $start $end $color_hex $strain\n";
						
						#print CIRCOS "Chr $start $gcpercent $mediane\n";
						print CIRCOS "Chr $start $end $diff_to_average\n";
					}
					else{
						#print CIRCOS "Chr $start $pos black $strain\n";
						#print CIRCOS "Chr $start $pos black $strain\n";
						
						#print CIRCOS "Chr $start 0\n";
						print CIRCOS "Chr $start $end 0\n";
						
						#print CIRCOS " 0";
					}
				}
			}
			#print CIRCOS "Chr 1000 2000 0.60\n";
			#print CIRCOS "Chr 2000 3000 0.10\n";
			#print CIRCOS "Chr 3000 4000 -0.20\n";
			#print CIRCOS "Chr 4000 5000 0.20\n";
			#print CIRCOS "Chr 5000 6000 -0.10\n";
			#print CIRCOS "Chr 6000 7000 0.10\n";
			close(CIRCOS);
	
			print "<input type=\"hidden\" name=\"select[]\" id=\"annot\" value=\"Stack\" />\n";
			print "<input type=\"hidden\" name=\"name[]\" id=\"annot\" value=\"density\" />\n";
			print "<input type=\"hidden\" name=\"data[]\" id=\"annot\" value=\"$Configuration::WEB_DIR/circosjs/$session.circos_stack.txt\" />\n";

			#print "<input type=\"hidden\" name=\"select[]\" id=\"annot\" value=\"Stack\" />\n";
                        #print "<input type=\"hidden\" name=\"name[]\" id=\"annot\" value=\"density2\" />\n";
                        #print "<input type=\"hidden\" name=\"data[]\" id=\"annot\" value=\"$Configuration::WEB_DIR/circosjs/$session.circos_stack.txt\" />\n";
			
			print "<input type=\"hidden\" name=\"select[]\" id=\"annot\" value=\"Histogram\" />\n";
			print "<input type=\"hidden\" name=\"name[]\" id=\"annot\" value=\"heatmap\" />\n";
			print "<input type=\"hidden\" name=\"data[]\" id=\"annot\" value=\"$Configuration::WEB_DIR/circosjs/$session.circos_line.txt\" />\n";
			
		}
		print "<script type=\"text/javascript\">alert('ok');</script>";
		print "<input onload=\"document.getElementById('display').form.submit();\" value=\"Display Circos\" id=\"display\" type=\"submit\">\n";

		print "</form>\n";
		#print "<iframe onload=\"document.getElementById('display').form.submit();\"></iframe>";
		#print "<iframe src=\"\" id=\"myIframe3\" name=\"myIframe3\" width=\"1200px\" height=\"1600\" style='border:solid 0px black;zoom:0.8;-moz-transform: scale(0.8);-moz-transform-origin: 0 0;-o-transform: scale(0.8);-o-transform-origin: 0 0;-webkit-transform: scale(0.8);-webkit-transform-origin: 0 0;' src=\"#\"></iframe>\n";
		print "<iframe scrolling=\"no\" src=\"\" id=\"myIframe3\" name=\"myIframe3\" frameborder=\"0\" style=\"height:1100px; overflow:hidden; width: 1100px\" src=\"#\"></iframe>\n";
		print "<script type=\"text/javascript\">jQuery(document).ready(function(){var loginform= document.getElementById(\"loginForm\");alert(loginform);loginform.style.display = \"none\";loginform.submit();});</script>";
		print "<script type=\"text/javascript\">alert('ok');</script>";
		print "<br/><b>Legend:</b><br/><pre>$legend_circos</pre>";
	}
}
	
sub rgbToHex {
    my $red=$_[0];
    my $green=$_[1];
    my $blue=$_[2];
    my $string=sprintf (" #%2.2X%2.2X%2.2X\n",$red,$green,$blue);
    return ($string);
}


