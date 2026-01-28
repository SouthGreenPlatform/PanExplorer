#!/usr/bin/perl

my $dir = $ARGV[0];
my $outdir = $ARGV[1];

open(LS,"ls $dir/* |");
my $n = 0;
my %duplicate_definitions;
mkdir("$outdir");
mkdir("$outdir/forzip");
my $nb_files_ok = 0;

my $nb_uploaded = `ls -alrt $dir/* | wc -l`;

while(<LS>){
			$n++;
			my $file = $_;
			$file =~s/\n//g;$file =~s/\r//g;
			my $evidences_LOCUS = 0;
			my $evidences_ACCESSION = 0;
			my $evidences_gene = 0;
			my $evidences_seq = 0;
			my $concat = "";
			
			my @infos_file_path = split(/\//,$file);
			my $filename = $infos_file_path[$#infos_file_path];
			$filename =~s/_//g;
			$filename =~s/\.//g;
			$filename =~s/-//g;
		
			my $already_observed = 0;

			my $nb_locus_tag = 0;	
			my $nb_protein_id = 0;
			my $current_locus;
			my $locus_num = 0;
			open(F,$file);
			while(<F>){
				if (/product=/){
					$evidences_gene++;
				}
				if (/locus_tag=/){
					$nb_locus_tag++;
				}
				if (/protein_id=/){
                                        $nb_protein_id++;
                                }
				if (/^LOCUS\s+([^\s]+)\s+/){
					$locus_num++;
					$current_locus = $1;
					my $name_provisoire = $current_locus;
					my $new_locus_name = $filename.$locus_num;
					$_ =~s/$name_provisoire/$new_locus_name/g;
					$evidences_LOCUS++;
				}
				if (/^ACCESSION/){
					$evidences_ACCESSION++;
					my $new_locus_name = $filename.$locus_num;
					#my $accession = $1;
					#if (!$accession){
					$_ = "ACCESSION   $new_locus_name\n";
					#}
					#if (/^ACCESSION\s+$/){
					#	$_ = "ACCESSION   $current_locus\n";
					#}
				}
				if (/^DEFINITION  (.*)$/){
					my ($strain) = split(/,/,$1);
					$strain =~s/[^\w\_ ]//g;
					my @informations_strain = split(/ /,$strain);
					# annotation bakta
					if ($strain eq "chromosome"){
						$strain = "Genus species";
						$_ = "DEFINITION  $filename\n";
					}
					# annotation bakta
					elsif ($strain =~/contig/ or $strain =~/scaffold/ or $strain =~/NODE_\d+/){
                                                $strain = "Genus species";
                                                $_ = "DEFINITION  $filename\n";
                                        }
					# annotation dfast
					elsif ($strain =~/Genus sp unspecified DNA/){
						$strain = "Genus species";
						$_ = "DEFINITION  $filename\n";
					}
					# annotation prokka
					elsif (/Genus species strain/){
						$_ = "DEFINITION  $filename\n";
					}
					# definition is not explicite enough
					elsif (scalar @informations_strain < 10){
						$duplicate_definitions{$strain}++;
                                                $_ = "DEFINITION  $filename\n";
                                        }
					elsif ($duplicate_definitions{$strain} > 1){
						$already_observed=1;
						$_ = "DEFINITION  $filename\n";
					}
					else{
						$duplicate_definitions{$strain}++;
						#if ($duplicate_definitions{$strain} > 1){
						#	$already_observed=1;
						#}	
					}
                                }
				if (/^ORIGIN/){
					$evidences_seq++;
				}
				$concat .= $_;
			}
			close(F);

			

			#if ($evidences_gene > 300 && $evidences_LOCUS == 1 && $evidences_seq == 1){
			if ($evidences_gene > 45 && $evidences_seq > 0 && ($nb_locus_tag > 0 or $nb_protein_id > 0) && $evidences_ACCESSION > 0){
				#system("cp $file $Configuration::DATA_DIR/$pangenome_data/$session.$projectnew/genomes/genomes/$filename.gbff");
				open(F,">$outdir/forzip/$filename.gb");
				print F $concat;
				close(F);

				#system("gzip $Configuration::DATA_DIR/$pangenome_data/$session.$projectnew/genomes/genomes/$filename.gbff");
				$nb_files_ok++;
			}
			else{
				#if ($evidences_LOCUS > 1){
				#	print O "<img height=20 src='https://panexplorer.southgreen.fr/images/error-icon-4.png'>&nbsp;&nbsp; $filename: ERROR: It seems that genbank contains several LOCUS tags.<br/>\n";
				#}
				if ($evidences_gene <= 45){
                                        $error = "$filename: ERROR: Too few genes detected (less than 45)";
                                }
				elsif ($evidences_seq == 0){
                                        $error = "$filename: ERROR: Genbank file does not contain genomic sequence for locus<br/>\n";
                                }
				elsif ($evidences_ACCESSION == 0){
                                        $error = "$filename: ERROR: Genbank file does not contain ACCESSION tag<br/>\n";
				}
				elsif ($nb_protein_id == 0 && $nb_locus_tag == 0){
                                        $error = "$filename: ERROR: Genbank file can not be processed since it does not contain locus_tag or protein_id for genes<br/>\n";
                                }
				else{
					$error = "$filename: ERROR<br/>\n";
				}
			}
}
close(LS);

if (-d "$outdir"){
    chdir("$outdir/forzip");
    system("zip genomes.zip  ./*.gb >>zip.log 2>&1");
	
}