#!/usr/bin/perl -w

=pod

=head1 NAME

display_ajax.cgi - displays an html page for ajax.

=head1 SYNOPSIS

=head1 REQUIRES

=head1 DESCRIPTION

Displays an an html page for ajax.

=cut

use lib ".";

use strict;
use warnings;
use Carp qw (cluck confess);

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
my $strains2;
if ($cgi -> param('strains2') =~/([\w\,\-\.]+)/){
        $strains2 = $1;
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
my $genename;
if ($cgi -> param('genename') =~/([\w\.,]+)/){
	$genename = $cgi -> param('genename');
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
                                my $get_genbank = `$Configuration::TOOLS_DIR/edirect/efetch -id $genbank -db nuccore -mode text >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
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
	my $cmd = "perl $Configuration::CGI_DIR/GetSequences.pl -i $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes";
	system($cmd);
	if ($software eq 'roary'){
		my $cmd = "perl $Configuration::CGI_DIR/Run_Roary_bioblend.pl -i $options -p $projectnew -e $email -o $execution_dir ";
		system($cmd);
	}
	else{
		my $cmd = "perl $Configuration::CGI_DIR/Run_PGAP_bioblend.pl -i $options -p $projectnew -e $email -o $execution_dir ";
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
                                my $get_genbank = `$Configuration::TOOLS_DIR/edirect/efetch -id $genbank -db nuccore -format gb >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gb`;
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
        my $selection_size = scalar @strains2;

	# in case of a second group to be compared
	my @strains_to_be_compared = split(",",$strains2);
        my $concatenate_strains_to_be_compared = join(",",sort @strains_to_be_compared);
        my @all_strains_to_be_analyzed = @strains_to_be_compared;
        push(@all_strains_to_be_analyzed, @strains2);
        my $concat_all_strains_to_be_analyzed = join(",",sort @all_strains_to_be_analyzed);

        my %cluster_of_gene;
        my %genes_of_cluster;
        open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
        open(R,">$execution_dir/roary_matrix.txt");
        open(A,">$Configuration::HOME_DIR/tables/$session.absent.txt");
        open(C,">$Configuration::HOME_DIR/tables/$session.dispensablegenes.txt");
        print C "Cluster\tGenes\tFunction\n";
        print A "Cluster\tGenes\tFunction\n";
        my $first_line = <F>;
        $first_line =~s/\n//g;$first_line =~s/\r//g;
        my @samples = split("\t",$first_line);
        my $found = 0;
        my $nb_found_absent = 0;
        my $nb_total_strains = 0;
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
                my $cluster_is_found = 0;
                $nb_total_strains = $#i;
		if ($strains2 =~/\w+/){$nb_total_strains = scalar @all_strains_to_be_analyzed - 1;}
                for (my $j = 1; $j <= $#i; $j++){
                        my $val = $i[$j];
                        my $samp = $samples[$j];

			# exclude strains that must not be considered
			if ($strains2 =~/\w+/ && $concat_all_strains_to_be_analyzed !~/$samp/){next;}

                        if ($val =~/\w+/){
                                my @genes = split(",",$val);
                                foreach my $gene(@genes){
                                        $cluster_of_gene{$gene} = $name;
                                        $genes_of_cluster{$name}.=",$gene";
                                }
                                $nb_found++;
                                $concatenate_samples .=",".$samples[$j];

                                if ($concatenate_strains =~/$samp/){$cluster_is_found = 1;}
                                push(@samples_specific,$samples[$j]);
                        }
                }

                # specifically absent
                if ($cluster_is_found == 0 && $nb_found ==($nb_total_strains-$selection_size)){
                        my @gene_list = split(",",$genes_of_cluster{$name});
                        my $function;
                        foreach my $gene(@gene_list){
                                if ($functions{$gene} =~/\w+/){
                                        $function = $functions{$gene};
                                }
                        }
                        my $list_to_displayed = substr($genes_of_cluster{$name},0,50);
                        # exclude if several reprensentant by strain (if restriction is checked)
                        my $nb_genes = scalar split(",",$genes_of_cluster{$name})-1;
                        if ($nb_max_by_strain eq "one" && scalar @strains2 != $nb_genes){next;}

                        print A "<a href='./clusters.cgi?genename=$name&project=$project' target=_blank>$name</a>\t$list_to_displayed\t$function\n";
                        $nb_found_absent++;
                }

                # specifically present
                my $concatenate_samples = join(",",sort @samples_specific);
                if (scalar @strains2 == scalar @samples_specific && $concatenate_strains eq $concatenate_samples){
                        my @gene_list = split(",",$genes_of_cluster{$name});
                        my $function;
                        foreach my $gene(@gene_list){
                                if ($functions{$gene} =~/\w+/){
                                        $function = $functions{$gene};
                                }
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
        close(R);
        close(A);


        print "<b>Number of gene clusters specifically present in this subset: $found</b></br>";
        print "<b>Number of gene clusters specifically absent in this subset: $nb_found_absent</b></br>";
        my $config_table = "";
        $config_table .= qq~
                                        '0dispensable-genes'=>
                                        {
                                                        "select_title" => "Specifically present genes",
                                                        "file" => "$Configuration::HOME_DIR/tables/$session.dispensablegenes.txt",
                                        },
                                        'absent'=>
                                        {
                                                        "select_title" => "Specifically absent genes",
                                                        "file" => "$Configuration::HOME_DIR/tables/$session.absent.txt",
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
	open(CIRCOS,">$Configuration::HOME_DIR/circosjs/$session.circos_stack.txt");

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
	open(CHROM_LENGTH,">$Configuration::HOME_DIR/circosjs/$session.chrom_length.txt");
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
                <h3>Hive plot</h3>
                It represents the physical location of core-genes on the three genomes, and allows to evaluate the conservation of gene order between genomes.<br>
                Each node corresponds to a cluster defined as core-gene between the three genomes.<br/>
                Links are colored with a color gradient in order to better estimate genomic rearrangements.<br/>
                Passing the mouse cursor over nodes displays the name of the cluster and the corresponding gene of the strain genome.
		
		
		<iframe src='$Configuration::WEB_DIR/hiveplot_json/hiveplot.$session.html' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>~;
		print $macrosynteny_part;
		
		print "<br/><iframe src='$Configuration::WEB_DIR/mauve_viewer/mauve-viewer/demo/$session.html' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>";
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
		
			open(CIRCOS,">$Configuration::HOME_DIR/circosjs/$session.circos_line.txt");
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
elsif ($action eq "search_cluster"){
	search_cluster();
}
	
sub rgbToHex {
    my $red=$_[0];
    my $green=$_[1];
    my $blue=$_[2];
    my $string=sprintf (" #%2.2X%2.2X%2.2X\n",$red,$green,$blue);
    return ($string);
}

sub search_cluster{

	my $tabs = qq~
<style>
body {font-family: Arial;}

/* Style the tab */
.tab {
  overflow: hidden;
  border: 1px solid #ccc;
  background-color: #f1f1f1;
}

/* Style the buttons inside the tab */
.tab button {
  background-color: inherit;
  float: left;
  border: none;
  outline: none;
  cursor: pointer;
  padding: 10px 10px;
  transition: 0.3s;
  font-size: 14px;
}

/* Change background color of buttons on hover */
.tab button:hover {
  background-color: #ddd;
}

/* Create an active/current tablink class */
.tab button.active {
  background-color: #ccc;
}

/* Style the tab content */
.tabcontent {
  display: none;
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-top: none;
}
</style>
<script>
// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>
</head>
<body>


<div class="tab">
  <button class="tablinks" onclick="openCity(event, 'Genes')" id="defaultOpen">Genes</button>
  <button class="tablinks" onclick="openCity(event, 'Sequences')">Sequences</button>
  <button class="tablinks" onclick="openCity(event, 'Phylogeny')">Phylogeny</button>
  <button class="tablinks" onclick="openCity(event, 'Haplotypes')">SNPs/haplotypes</button>
  <button class="tablinks" onclick="openCity(event, 'Cytoscape')">Cytoscape network</button>
</div>

~;

	my $nb_found = 0;
	my %strains;
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/1.Orthologs_Cluster.txt");
	my $first_line = <F>;
	$first_line =~s/\n//g;$first_line =~s/\r//g;
	my @speciesinfo = split("\t",$first_line);
	my $sequences = "";
	my $dnasequences = "";
	my $haplotype_sequences = "";
	my $cluster;
	my $ngenes = 0;
	my $nb_haplo = 0;
	my $is_core = 0;
	my %list_of_genes;
	my @list_of_species;
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
					push(@list_of_species,$species);
					my @genes = split(",",$gene);
					foreach my $gene(@genes){
						if ($gene eq ""){next;}
						$ngenes++;
						#my $grep = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt`;
						my $grep;
						$list_of_genes{$gene} = $species;
						my $function = "#";
						if ($grep =~/$gene (.*) \[/){
							$function = $1;
						}
						my $grep2;	
						#my $grep2 = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/COG_assignation.txt`;
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
							#my $grep4 = `grep $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.ptt`;
							my $grep4;
							my @infos = split("\t",$grep4);
							my $positions = $infos[0];
							my $synonym = $infos[4];
							
							#my $grep3 = `grep -A 40 $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.faa`;
							my $grep3;
							#print C "$clustername\t$gene\t$positions\t$synonym\t$function\t$cog\t$species\n";
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
								#$grep4 = `grep -A 40 $locustag $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.fna`;
							}
							else{
								#$grep4 = `grep -A 40 $gene $Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.fna`;
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


	my %results;
	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/COG_assignation.txt");
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		my @infos = split(/\t/,$line);
		my $gene = $infos[0];
		my $cog = $infos[1];
		if ($list_of_genes{$gene}){
			$results{$gene}{"cog"} = $cog;
		}	
	}
	close(F);

	open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genes.txt");
	while(<F>){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		my @infos = split(/ /,$line);
		my $gene = $infos[0];
		my $function = "#";
		if ($list_of_genes{$gene}){
			if ($line =~/$gene (.*) \[/){
				$function = $1;
			}
			$results{$gene}{"function"} = $function;
		}
	}
	close(F);
	


	foreach my $species(@list_of_species){
		my $go = 0;
	
		open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.ptt");
		while(<F>){
			my $line = $_;
			$line =~s/\n//g;$line =~s/\r//g;
			my @infos = split(/\t/,$line);
			my $gene = $infos[3];
			if ($list_of_genes{$gene}){
				$results{$gene}{"location"} = $infos[0];
				$results{$gene}{"synonym"} = $infos[4];
			}
		}
		close(F);

		my %locus_tags;
		open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.faa");
		while(<F>){
			if (/^>/){
				if ($go ==1){$go = 0;}
				if (/protein_id=([\w\.]+)\]/){
					my $id = $1;
					my $locus_tag;
					if (/locus_tag=([\w\.]+)\]/){
						$locus_tag = $1;
					}	
					if ($list_of_genes{$id}){
						$locus_tags{$locus_tag} = $id;
						$go = 1;
						$sequences .= ">$species"."_"."$id\n";
					}
				}
				else{$go = 0;}	
			}
			else{
				
				if ($go == 1){
					$sequences .= $_;
				}
			}
		}
		close(F);

		$go = 0;
		open(F,"$Configuration::DATA_DIR/pangenome_data/$project/genomes/genomes/$species.fna");
		while(<F>){
			if (/^>/){
				if ($go ==1){$go = 0;}
				if (/locus_tag=([\w\.]+)\]/){
					my $locus_tag = $1;
					if ($locus_tags{$locus_tag}){
						$go = 1;
						my $protein_id = $locus_tags{$locus_tag};
						
						$dnasequences .= ">$species"."_"."$protein_id\n";
					}
				}
				else{$go = 0;}
			}
			else{
				if ($go == 1){
					$dnasequences .= $_;
				}
			}
		}
		close(F);
	}

	foreach my $gene(keys(%results)){
                my $positions = $results{$gene}{"location"};
                my $synonym = $results{$gene}{"synonym"};
                my $function = $results{$gene}{"function"};
                my $cog = $results{$gene}{"cog"};
                my $species = $list_of_genes{$gene};
                print C "$genename\t$gene\t$positions\t$synonym\t$function\t$cog\t$species\n";
        }
        close(C);
	
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
        <br/> <a href='$Configuration::WEB_DIR/tables/$session.genes.txt'>Download table</a>
        <br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>~;


	
	my $t = gmtime();
	print TEST "1 $t\n";

	open(FASTA,">$execution_dir/genes.fa");
	print FASTA $sequences;
	close(FASTA);

	open(FASTA,">$execution_dir/genes_dna.fa");
	print FASTA $dnasequences;
	close(FASTA);

	print "<b>$cluster ($ngenes genes) (".scalar @list_of_species." strains)";
	if ($is_core == 1){print " (Core)";}
	elsif ($nb_found == 1){print " (Strain-specific)";}
	else{print " (Dispensable)";}

	print "<br/><br/></b>";	
	
	my $alignment = "";
	my %hash;
	my %hash2;
	print $tabs;

	###############################
	# MUSCLE
	###############################

	if ($ngenes < $Configuration::MAX_NUMBER_FOR_PHYLO){
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

	my %different_sequences;
	open(F,"$execution_dir/snp.align.fa");
	while(<F>){
		if (/>/){

		}
		else{
			my $different_seq = $_;
			$different_sequences{$different_seq}++;
		}
	}
	close(F);

	open(O,">$execution_dir/haplotypes.fna");
	my $num_seq = 0;
	foreach my $seq(keys(%different_sequences)){
		$num_seq++;
		my $size = $different_sequences{$seq};
		$haplotype_sequences .= ">haplo$num_seq|$size\n";
                $haplotype_sequences .= "$seq";
	}
	print O $haplotype_sequences;
	close(O);

	
	#print "Number of different sequences: " . scalar keys(%different_sequences)."<br>";

	$nb_haplo = $num_seq;
	if ($num_seq < $Configuration::MAX_NUMBER_FOR_NETWORK){
		system("$Configuration::HAPLOPHYLE_EXE -in $execution_dir/haplotypes.fna -out $execution_dir/snp.network.dot >> $execution_dir/haplophyle.log 2>&1");
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
					if ($1 > 1){$size = $1;}
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
	 <div id="Genes" class="tabcontent">

	<br/><iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='950' height='900' style='border:solid 0px black;'></iframe><br/><br/>
	</div>
	~;
	

	print $table_part;

	print "<div id=\"Sequences\" class=\"tabcontent\">";	
	print "<br/><b>DNA sequences</b><br/>";
	print "<pre>$dnasequences</pre>";
	print "<br/><b>Protein sequences</b><br/>";
	print "<pre>$sequences</pre>";
	print "<br/>";
	print "</div>";
	
	print "<div id=\"Haplotypes\" class=\"tabcontent\">";
        print "<br/><b>$nb_haplo distinct haplotype sequences (only SNPs residues)</b><br/>";
        print "<pre>$haplotype_sequences</pre>";
        print "<br/>";
        print "</div>";

	#print "<br/><b>Alignment of genes</b><br/>";	
	#print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.genes.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	#print "<br/><br/><b>Alignment of SNPs</b><br/>";
	
	#print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.snps.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	#print "<br/><br/><b>Alignment of proteins</b><br/>";
	
	#print "<iframe src='$Configuration::WEB_DIR/MSAViewer/$session.proteins.html' width='950' height='200' style='border:solid 1px black;'></iframe>";

	#print "</div>";	
	
	print "<div id=\"Phylogeny\" class=\"tabcontent\">";	
	if (-e "$Configuration::HOME_DIR/phylotree/$session.html"){
		print "<br/><b>Distance tree (Muscle+DnaDist+FastME)</b> of the different genes of the cluster (across the different strains).";
		print "<iframe src=\"$Configuration::WEB_DIR/phylotree/$session.html\" width=\"1000\" height=\"900\" style='border:solid 0px black;'></iframe>";	
	}
	else{
                print "<br/>Couldn't compute because too many sequences";
        }
	print "</div>";	


	print "<div id=\"Cytoscape\" class=\"tabcontent\">";
	if (-e "$execution_dir/snp.network.dot"){
		print "<br/><b>Median-Joining Network (MJN)</b> of the distinct haplotype sequences (only SNP positions) across the whole genes of the cluster.<br/>Each node corresponds to a specific haplotype sequence. If the sequence is the same for multiple strains, the node is represented only once.<br/>The size of the circle is proportional to the number of strains carrying this sequence.";
		print "<br/><iframe src='$Configuration::WEB_DIR/d3/$session.snp.d3.network.html' width='950' height='900' style='border:solid 1px black;'></iframe>";
	}
	else{
		print "<br/>Couldn't compute because too many sequences";
	}
	print "</div>";
	print qq~
<script>
// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>	
~;	
	
}








