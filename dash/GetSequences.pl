#!/usr/bin/perl

use strict;
use Getopt::Long;

my $usage = qq~Usage:$0 <args> [<opts>]

where <args> are:

    -i, --input         <input directory>
     
~;
$usage .= "\n";

my ($inputdir);


GetOptions(
	"input=s"      => \$inputdir
);


die $usage
  if ( !$inputdir );


	my %strains;
	open(LS,"ls $inputdir/*gbff.gz |");
        while(<LS>){
                if (/\/([^\/]*)\.gbff.gz/){
                        my $strain = $1;

                        my $grep_id = `zgrep 'LOCUS' $inputdir/$strain.gbff.gz | head -1`;
                        if ($grep_id =~/LOCUS\s+(\w+)\s+/){
                                my $genbank = $1;
                                $genbank =~s/\n//g;$genbank =~s/\r//g;
                                $strains{$genbank} = $strain;
                        }
                }
        }
        close(LS);


	open(LS,"ls $inputdir/*gbff |");
        while(<LS>){
                if (/\/([^\/]*)\.gbff/){
                        my $strain = $1;
			my $old_name_strain = $strain;
			#my $grep_id = `grep 'DEFINITION' $inputdir/$strain.gbff | head -1`;

			my $get_organism_line = `head -10 $inputdir/$strain.gbff | grep -A 1 DEFINITION `;
			# if several lines for DEFINITION, concatenate the lines
			my @lines_organism = split(/\n/,$get_organism_line);
			my $first_line = $lines_organism[0];
			my $second_line = $lines_organism[1];
			if ($second_line =~/^            (.*)/){
				$get_organism_line = $first_line. " ".$1;
			}
			else{
				$get_organism_line = $first_line;
			}
			$get_organism_line =~s/\n//g;$get_organism_line =~s/\r//g;

			#print $grep_id;
                        #if ($grep_id =~/LOCUS\s+(\w+)\s+/){
			if ($get_organism_line =~/DEFINITION  (.*)$/){
				$strain = $1;

                                        $strain =~s/\.//g;
                                        my ($info1,$info2 ) = split(",",$strain);
                                        $strain = $info1;
                                        $strain =~s/ /_/g;
                                        $strain =~s/strain_//g;
                                        $strain =~s/_chromosome//g;
                                        $strain =~s/_genome//g;
                                        $strain =~s/_str_/_/g;
                                        $strain =~s/[^\w\-\_]//g;
                                        $strain =~s/\-/_/g;

                                $strains{$old_name_strain} = $strain;
				system("mv $inputdir/$old_name_strain.gbff $inputdir/$strain.gbff");
				system("gzip $inputdir/$strain.gbff");
                        }
                }
        }
        close(LS);
	open(LS,"ls $inputdir/*gff |");
	while(<LS>){
		if (/\/([^\/]*)\.gff/){
                        my $strain = $1;
			system("$Configuration::TOOLS_DIR/gffread/gffread -y $inputdir/$strain.faa -x $inputdir/$strain.fna -g $inputdir/$strain.fasta $inputdir/$strain.gff");
			open(PTT,">$inputdir/$strain.ptt");

			print PTT "Location\tStrand\tLength\tPID\tGene\tSynonym Code\tCOG\tProduct\tblock_id\n";
			open(GFF,"$inputdir/$strain.gff");
			while(my $line = <GFF>){
				chomp($line);
				my @infos = split(/\t/,$line);
				my $chr = $infos[0];
				my $feature = $infos[2];
				my $start = $infos[3];
				my $end = $infos[4];
				my $strand = $infos[6];
				if ($feature eq "mRNA" && $line =~/ID=([^;]*);.*product=([^;]*);/){
					my $gene = $1;
					my $product = $2;
					$gene =~s/\|/_/g;
					$gene =~s/:/_/g;
					print PTT "$start..$end\t$strand\t\t$gene\t$gene\t\t\t$product\t$chr\n";
				}
				elsif ($feature eq "mRNA" && $line =~/ID=([^;]*);.*Note=([^;]*);/){
					my $gene = $1;
					my $product = $2;
					$gene =~s/\|/_/g;
					$gene =~s/:/_/g;
					print PTT "$start..$end\t$strand\t\t$gene\t$gene\t\t\t$product\t$chr\n";
				}
				elsif ($feature eq "mRNA" && $line =~/ID=([^;]*);/){
					my $gene = $1;
					$gene =~s/\|/_/g;
					$gene =~s/:/_/g;
					print PTT "$start..$end\t$strand\t\t$gene\t$gene\t\t\t\t$chr\n";
				}
			}
			close(GFF);
			close(PTT);
		}
	}
	close(LS);

        foreach my $genbank(keys(%strains)){
            my $strain = $strains{$genbank};
			open(F,">$inputdir/$strain.gi");print F "$genbank\n";close(F);
			system("cp -rf $inputdir/$strain.gbff.gz $inputdir/$strain.gb.gz");
			system("gunzip $inputdir/$strain.gb.gz");
            #my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format gb >$inputdir/$strain.gb`;
            system("perl GetSequencesFromGenbank.pl $inputdir/$strain.gb");
			rename("$inputdir/$strain.gb.pep","$inputdir/$strain.faa");
			rename("$inputdir/$strain.gb.nuc","$inputdir/$strain.fna");
            #my $get_prot = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format fasta_cds_aa >$inputdir/$strain.faa`;
            #my $get_gene = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format gene_fasta >$inputdir/$strain.fna`;
            my $convert_ptt = `gb2ptt/bin/gb2ptt.pl --infile $inputdir/$strain.gb`;
            rename("$inputdir/$strain.gb.ptt","$inputdir/$strain.ptt");
        }

