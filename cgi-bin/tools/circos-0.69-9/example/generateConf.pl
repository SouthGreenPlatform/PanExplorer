#!/usr/bin/perl

use strict;

for (my $i = 1; $i <= 20; $i++){
	my $r0 = 50+$i*2;
	my $r1 = 52+$i*2;
	my $r0val = $r0."r";
	my $r1val = $r1."r";
	my $block = qq~<plot>
type    = heatmap
file    = /www/panexplorer.southgreen.fr/data/pangenome_data/2298288513879.Xantho_oryzae/$i.heatmpa.txt
r1      = 0.$r1val
r0      = 0.$r0val
</plot>
~;
	print $block;

}
