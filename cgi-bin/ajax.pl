#!/usr/bin/perl

use lib ".";

use strict;

use Config::Configuration;
use CGI;
my $cgi = CGI->new;
print $cgi->header;
my $action = $cgi-> param("action");
my $projectnew = $cgi -> param('projectnew');
my $email = $cgi -> param('email');
my $session= $cgi -> param('session');
my $genbanks = $cgi -> param('genbanks');
my $software = $cgi -> param('software');

my $execution_dir = "$Configuration::TEMP_EXECUTION_DIR/$session";
if (!-d $execution_dir){
        mkdir($execution_dir);
}

if ($action eq "check_id"){

	# wget https://ftp.ncbi.nlm.nih.gov/genomes/GENOME_REPORTS/prokaryotes.txt
        if ($cgi -> param('projectnew') =~/(^[\w]+)$/){
                $projectnew = $cgi -> param('projectnew');
        }
        else{
                print "<div class=\"alert alert-danger\" role=\"alert\">Project name is not valid </div>";exit;
        }
        my @genbank_ids = split(",",$genbanks);
        if (scalar @genbank_ids > 80){
                print "<div class=\"alert alert-danger\" role=\"alert\">Too many Genbank identifiers (maximum 80)</div>";exit;
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
				if ($genbank =~/^(ASM\d+v)\d+$/){
					$genbank = $1;
				}
				my $grep = `grep $genbank $Configuration::DATA_DIR/prokaryotes.txt`;
				my @infos = split(/\t/,$grep);
				my $status = $infos[15];
				if ($status !~/Complete Genome/ && $status !~/Chromosome/){
					print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: This identifier is not a genome available in Genbank (status: $status)";exit;
				}
				my $ftp_path = $infos[$#infos -2];
				$ftp_path =~s/ftp:/http:/g;
				my @table = split(/\//,$ftp_path);
				my $name = $table[$#table];
				my $prot_file = "$ftp_path/$name"."_protein.faa.gz";
				my $gbff_file = "$ftp_path/$name"."_genomic.gbff.gz";
				`wget -O $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.faa.gz $prot_file`;
				if (!-e "$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.faa.gz"){
					print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: Genome is not annotated";exit;
				}
				my $contain_genes = `zcat $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.faa.gz | grep -c '>' `;
				chomp($contain_genes);
					

                                #my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -mode text >$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                my $get_genbank = `wget -O $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gbff.gz $gbff_file`;
				my $get_organism_line = `zcat $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gbff.gz | head -10 | grep DEFINITION `;	
				my $strain;
				if ($get_organism_line =~/DEFINITION  (.*)$/){
                                        $strain = $1;
                                }
				else{
                                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: Organism name not found";exit;
                                }
				$strain =~s/strain //g;
				$strain =~s/ chromosome//g;
				$strain =~s/ genome//g;
				$strain =~s/str\. //g;
				$strain =~s/\=//g;
				$strain =~s/\///g;
				$strain =~s/ /_/g;
				$strain =~s/\(//g;
				$strain =~s/\)//g;
				$strain =~s/\-/_/g;
				my ($info1,$info2 ) = split(",",$strain);
				$strain = $info1;
				$strain =~s/\.//g;
				my $original_strain_name = $strain;
				my @words = split(/_/,$strain);
				my $genus = $words[0];
				#my $species = $words[1];
				#$strain = substr($genus,0,3) . "_". substr($species,0,2);
				#for (my $j = 2; $j <= $#words; $j++){
				#	$strain.="_".$words[$j];
				#}


				#my $genus = `grep 'genus' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #if ($genus =~/genus \"([^\"]*)\"/){$genus = $1;}
                                #my $species = `grep 'species' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #if ($species =~/species \"([^\"]*)\"/){$species = $1;}
                                #my $subname = `grep 'subname' $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #if ($subname =~/subname \"([^\"]*)\"/){$subname = $1;}
                                #$subname =~s/ /-/g;
                                #my $strain = $genus."_".$species."_".$subname;
                                #my $contain_genes = `grep -c cdregion $Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.json`;
                                #chomp($contain_genes);
				#if ($genus !~/\w+/){
				#	print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: This identifier is not a genome available in Genbank (no genus found)";exit;
				#}
				if ($contain_genes < 10){
					print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: Genome is not annotated";exit;
				}
				if ($contain_genes >8000){
                                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbank: ERROR: Genome contains too many genes to be supported by the analysis (max:8000) ";exit;
                                }
			if ($strain && $genus =~/\w+/){
                                        $strain_names{$strain}++;
                                        my $indice = $strain_names{$strain};
                                        if ($indice > 1){$duplicated_strain = $strain;}
                                        $strains{$genbank} = $strain;

                                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/2048px-Yes_Check_Circle.svg.png'>&nbsp;&nbsp;$genbank: $original_strain_name ($contain_genes genes)";
                                        rename("$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$genbank.gbff.gz","$Configuration::DATA_DIR/pangenome_data/$session.$projectnew/genomes/genomes/$strain.gbff.gz");
                                        $nbok++;exit;
                                }
                        }
                }
                if ($not_found && $nbok < scalar @genbank_ids){
                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbanks: ERROR: Identifier is not found in Genbank";
                }
                elsif ($not_annotated && $nbok < scalar @genbank_ids){
                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbanks: ERROR: Genome is not annotated";
                }
                else{
                        print "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $genbanks: ERROR: Identifier is not found in Genbank";exit;
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
        #system($cmd);
	my $cmd = "perl $Configuration::CGI_DIR/Run_Panexplorer_workflow.pl -i $options -p $projectnew -e $email -o $execution_dir -s $software";
	system($cmd);
        
} 
