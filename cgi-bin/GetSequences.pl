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

$|++;
my $pid2 = fork;
if (!defined $pid2) {
	die "Cannot fork: $!";
}
elsif ($pid2 == 0 ){
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
        foreach my $genbank(keys(%strains)){
                my $strain = $strains{$genbank};
		open(F,">$inputdir/$strain.gi");print F "$genbank\n";close(F);
                my $get_genbank = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format gb >$inputdir/$strain.gb`;
                my $get_prot = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format fasta_cds_aa >$inputdir/$strain.faa`;
                my $get_gene = `/www/panexplorer.southgreen.fr/tools/edirect/efetch -id $genbank -db nuccore -format gene_fasta >$inputdir/$strain.fna`;
                my $convert_ptt = `/www/panexplorer.southgreen.fr/tools/gb2ptt/bin/gb2ptt.pl --infile $inputdir/$strain.gb`;
                rename("$inputdir/$strain.gb.ptt","$inputdir/$strain.ptt");
        }

}
