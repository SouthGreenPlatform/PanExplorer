#!/usr/bin/perl

use strict;

my $genbank_file = $ARGV[0];

my %genome_sequences;
my $go = 0;
my $current_chrom;
open(G,$genbank_file);
while(<G>){
	if ($go == 1 && /(\d+) (.*)\s*$/){
		my $line = $2;
		$line =~s/ //g;
		$line =~s/\n//g;$line =~s/\r//g;
		$genome_sequences{$current_chrom}.=$line;
	}
	if (/LOCUS       ([^\s]+)/){
		$current_chrom = $1;
	}
	if (/ORIGIN/){$go = 1;}
	if (/^\/\//){$go = 0;}
}
close(G);


open(N,">$genbank_file.nuc");
open(P,">$genbank_file.pep");
open(FUNC,">$genbank_file.func");
my $go = 0;
my $start;
my $end;
my $product;
my $complement = 0;
my $end_gene = "no";
my $protein = "";
my $has_translation = `grep -c 'translation=' $genbank_file`;
$has_translation =~s/\n//g;$has_translation =~s/\r//g;
open(G,$genbank_file);
my $current_gene;
my $current_protein_id = "";
my $contain_protein_id = `grep -c 'protein_id' $genbank_file`;
$contain_protein_id =~s/\n//g;$contain_protein_id =~s/\r//g;
while(<G>){
                if (/^\s+ORGANISM\s+(.*)$/){
                }
                if (/protein_id=\"(.*)\"/){
                        $current_protein_id = $1;
                }
		if (/LOCUS       ([^\s]+)/){
			$current_chrom = $1;
		}
                if (/locus_tag=\"(.*)\"/){
                        $current_gene = $1;
                }
		if (/gene=\"(.*)\"/){
                        $current_gene = $1;
                }
                if ($go == 1){
                        my $line = $_;
                        $line =~s/ //g;
                        $line =~s/\n//g;$line =~s/\r//g;
                        $protein .= $line;
                        if (/\"$/){
                                $protein =~s/\"//g;
                                $end_gene = "yes";

                        }
                }
		if (/\/translation=\"(.*)/ or ($has_translation == 0 && /protein_id=/)){
                        $go = 1;
                        $protein .= $1;
			if ($contain_protein_id < 2){$current_protein_id = $current_gene;}
                        print P ">$current_gene [locus_tag=$current_gene] [protein_id=$current_protein_id]\n";
                        print N ">$current_gene [locus_tag=$current_gene]\n";

                        if ($protein =~/\"$/){
                                $end_gene = "yes";
                        }
			if ($has_translation == 0){$end_gene = "yes";}
                }
                if ($end_gene eq "yes"){
                        $protein =~s/\"//g;
                        print P "$protein\n";
                        $protein = "";
                                my $length = $end - $start + 1;
				my $geneseq = substr($genome_sequences{$current_chrom},$start-1,$length);

                                if ($complement){
                                        my $revcomp = reverse $geneseq;
                                        $revcomp =~ tr/ATGCatgc/TACGtacg/;
                                        $geneseq = $revcomp;
                                }
				my $geneseq_uppercase = uc($geneseq);
                                print N "$geneseq_uppercase\n";
                                print FUNC "$current_gene  -       $product\n";
                                $go = 0;
                        $end_gene = "no";
                }
                if (/\/product=\"(.*)\"/){
                        $product = $1;
                }
                if (/^\s+CDS\s+(\d+)\.\.(\d+)\s*$/){
                        $start = $1;
                        $end = $2;
                        $complement = 0;
                }
                if (/^\s+CDS\s+complement\((\d+)\.\.(\d+)\)\s*$/){
                        $start = $1;
                        $end = $2;
                        $complement = 1;
                }
}
close(G);
close(P);
close(N);
close(FUNC);
if ($has_translation == 0){
	system("perl /www/panexplorer.southgreen.fr/PanExplorer/cgi-bin/translate.pl $genbank_file.nuc $genbank_file.pep");

}
