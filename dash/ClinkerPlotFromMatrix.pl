#!/usr/bin/perl

use strict;

my $matrix = $ARGV[0];
my $gene = $ARGV[1];
my $genbank_files = $ARGV[2];
my $list_strains = $ARGV[3];
my $outhtml = $ARGV[4];

if ($gene =~/CLUSTER/){
	$gene =~s/CLUSTER000//g;
	$gene =~s/CLUSTER00//g;
	$gene =~s/CLUSTER0//g;
	$gene =~s/CLUSTER//g;
}

##############################################
# Get cluster of the gene
##############################################
my %genes_first_round;
my %cluster_of_genes;
open(M,$matrix);
my $first_line = <M>;;
$first_line =~s/\n//g;$first_line =~s/\r//g;
my @samples = split(/\t/,$first_line);
my $sample;
my %indices;
while(<M>){
	if (/^$gene\t/){
		my $line = $_;
		$line =~s/\n//g;$line =~s/\r//g;
		$line =~s/\|/_/g;
		$line =~s/:/_/g;
		my @infos = split(/\t/,$line);
		#foreach my $genelist(@infos){
		for (my $j = 0; $j <= $#infos; $j++){
			my $genelist = $infos[$j];
			my @genes = split(/,/,$genelist);
			my $samp = $samples[$j];
			
			# discard this sample if not in the list provided by user
			if ($list_strains !~/$samp,/){next;}
			
			$indices{$j} = 1;
			if ($genelist =~/,/){next;}
			print "Processing sample: $samp\n";
			foreach my $info(@genes){
				print "Gene info: $info\n";
				if ($info !~/^\d+$/ && $info ne "-"){
					$sample = $samp;
					$gene = $info;
					#$genes_first_round{$info} = 1;
				}
			}
		}
	}
}
close(M);

print "Sample: $sample $gene\n";

######################################################################
# get all gene positions from genbank files
######################################################################
my %genes;
my %ordering;
my %features;
my @gbk_files = split(/,/,$genbank_files);
open(POS,">$outhtml.gene_positions.txt");

if (scalar keys(%ordering) == 0){
	open(LS,"ls $genbank_files/*ptt |");
	while(my $gbk = <LS>){
		chomp($gbk);
			my @particules = split(/\//,$gbk);
		my $f = $particules[$#particules];
		$f =~s/\.ptt//g;
		open(GBK,$gbk);
		my $start;
		my $end;
		my $locus;
		my $strand;
		while(<GBK>){
			if (/^(\d+)\.\.(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)/){
				$start = $1;
				$end = $2;
				$locus = 1;
				$strand = $3;
				
				if ($strand eq "-"){$strand = "-1";}
				else{$strand = "1";}
				my $protein_id = $5;
				$protein_id =~s/:/_/g;
				$genes{$protein_id}{$f} = "$locus:$start,$end";
				$ordering{$f}{$locus}{$start} = $protein_id;
				$features{$f}{$locus}{"$start,$end"}{"name"}= $protein_id;
				print POS "$f $locus $start,$end $protein_id $strand\n";
				$features{$f}{$locus}{"$start,$end"}{"strand"}= $strand;
			}
		}
		close(GBK);
	}
	close(LS);
}


if (scalar keys(%ordering) == 0){
	open(LS,"ls $genbank_files/*gff |");
	while(my $gff = <LS>){
		chomp($gff);
        	my @particules = split(/\//,$gff);
		my $f = $particules[$#particules];
		$f =~s/\.gff//g;
		open(GFF,$gff);
		while(my $line = <GFF>){
			chomp($line);
			my ($locus,$source,$feature,$start,$end,$score,$strand,$frame,$attributes) = split(/\t/,$line);
			if ($feature eq "mRNA" && $attributes=~/ID=([^;]*);/){
				my $protein_id = $1;
				$protein_id =~s/\|/_/g;
				$protein_id =~s/:/_/g;
				if ($strand eq "-"){$strand = "-1";}
				else{$strand = "1";}
				$genes{$protein_id}{$f} = "$locus:$start,$end";
				$ordering{$f}{$locus}{$start} = $protein_id;
				$features{$f}{$locus}{"$start,$end"}{"name"}= $protein_id;
				print POS "$f $locus $start,$end $protein_id $strand\n";
				$features{$f}{$locus}{"$start,$end"}{"strand"}= $strand;
			}
		}
		close(GFF);
	}
	close(LS);
}
close(POS);

########################################################################
# get neighbors of the gene and their cluster
########################################################################
my $ref_hash = $ordering{$sample};
print "sample: $sample\n";
my %subhash = %$ref_hash;
open(O,">$outhtml.ordered_genes.txt");
foreach my $chrom(sort {$a<=>$b} keys(%subhash)){
	my $ref_hash2 = $ordering{$sample}{$chrom};
	my %subhash2 = %$ref_hash2;
	foreach my $start(sort {$a<=>$b} keys(%subhash2)){
		my $protein_id = $ordering{$sample}{$chrom}{$start};
		print O "$start => $protein_id => $chrom\n";
	}
}
close(O);

print "\n\n=============\n\n";

my %functions_of_cluster;
my %uid_genes;
my %loci;
my %neighbors_of_gene;


print "Focus on gene: $gene\n";
#########################################################
# first, we get the genes and chrom corresponding to the cluster
#########################################################
my $copy_without_special_character = `sed "s/[\|\:]/_/g" $matrix >$outhtml.matrix.txt`;
my $grep = `grep $gene $outhtml.matrix.txt`;
$grep =~s/\n//g;$grep =~s/\r//g;
my @infos = split(/\t/,$grep);
my $cluster = $infos[0];
for (my $i =1; $i <= $#infos; $i++){
	if (!$indices{$i}){next;}
	my $species = @samples[$i];
	my $gene_list = $infos[$i];
	my @genes = split(/,/,$gene_list);
	foreach my $g(@genes){
		if ($g eq "-"){next;}
		my ($chr) = split(/:/,$genes{$g}{$species});
		$loci{$species} = $chr;
		$genes_first_round{$species}{$g} = 1;
		my $random = int(rand(100000));
		print "$species-$g $random\n";
		$uid_genes{"$species-$g"} = $random;
	}
}

#########################################################
# then, we get the genes and chrom of neighbored genes
#########################################################
my $neighbor = `grep -B 4 -A 4 '$gene' $outhtml.ordered_genes.txt`;
my @neighbors = split(/\n/,$neighbor);
foreach my $n(@neighbors){
	my ($start,$genename,$chrom) = split(/ => /,$n);
	$neighbors_of_gene{$genename} = 1;
	my $grep = `grep '$genename' $outhtml.matrix.txt`;
	$grep =~s/\n//g;$grep =~s/\r//g;
	
	my @infos = split(/\t/,$grep);

	#print "$grep $genename $matrix\n";
	my $cluster = $infos[0];
	print "\nSelection: $start $genename $chrom $cluster\n";
	my $to_be_stopped = 0;
	for (my $i =1; $i <= $#infos; $i++){
		if (!$indices{$i}){next;}
		my $species = @samples[$i];
		my $gene_list = $infos[$i];


		print "genelist: $gene_list $species\n";
		my @genes = split(/,/,$gene_list);

		# do not display genes if multiple copies
		if (scalar @genes > 1){
			next;
		}

		foreach my $g(@genes){
			if ($g eq "-"){next;}
			print "gene ----> $g\n";
			my ($chr) = split(/:/,$genes{$g}{$species});
			if (!$loci{$species}){
				$loci{$species} = $chr;
			}
			$genes_first_round{$species}{$g} = 1;
			my $random = int(rand(100000));
			print "Species-gene => $species-$g $random\n";

			$uid_genes{"$species-$g"} = $random;
		}
	}
}

#print $uid_genes{"Xanthomonas_vesicatoria_LM159-WP_074052270.1"};
#exit;

my %genes_of_clusters;
my $species_num = 0;
open(JSON,">$outhtml.data.json");
print JSON "{\n";
print JSON "   \"clusters\":[\n";
my $json_cluster = "";
my %readjusted_positions;	
foreach my $species(keys(%genes_first_round)){
	#if ($species eq ""){next;}
	$species_num++;
	if ($species eq ""){next;}
	print "=============\nStrain: $species\n=============\n";
	my @inf = split(/\//,$species);
	my $organism = $inf[$#inf];
	my $chromosome = $loci{$species};
	$organism =~s/\.gb//g;
	$json_cluster .= "           {\n";
	$json_cluster .= "           \"uid\":\"$organism\",\n";
	$json_cluster .= "           \"name\":\"$organism\",\n";
	$json_cluster .= "           \"loci\":[\n";
	$json_cluster .= "           {\n";
	$json_cluster .= "                \"uid\":\"$chromosome\",\n";
	$json_cluster .= "                \"name\":\"$chromosome\",\n";
	$json_cluster .= "                \"start\":0,\n";
	$json_cluster .= "                \"end\":30000,\n";
	$json_cluster .= "                \"genes\":[\n";
	my $json_genes = "";
	my $refhash = $genes_first_round{$species};
	my %subhash = %$refhash;
	my %regions;
	foreach my $gene(keys(%subhash)){
		my ($chrom,$location )= split(/:/,$genes{$gene}{$species});
		my ($start,$end) = split(/,/,$location);
		my $int = int($start / 100000);
		$regions{$int}.= "$gene,";
		print "$gene => $location => $int\n";
	}
	my %occurences;
	foreach my $int(keys(%regions)){
		my $n = scalar(split(/,/,$regions{$int}));
		$occurences{$n} = $int;
	}
	# get the most frequent
	foreach my $n(sort {$b<=>$a} keys(%occurences)){
		my $int = $occurences{$n};
		print "$int ===> $n\n";
		my @final_gene_list = split(/,/,$regions{$int});
		my $limit_start = 100000000;
		my $limit_end = 0;
		foreach my $gene(@final_gene_list){
			my ($chrom,$location )= split(/:/,$genes{$gene}{$species});
			print "Location $gene $location\n";
			my ($start,$end) = split(/,/,$location);
			if ($start > $limit_end){$limit_end = $start;}
			if ($end > $limit_end){$limit_end = $end;}
			if ($start < $limit_start){$limit_start = $start;}
                        if ($end < $limit_start){$limit_start = $end;}
		}
		print $regions{$int}."\n";
		print "Limit: $chromosome | $limit_start to $limit_end\n";
		my $go = 0;
		my %genes_of_region;
		my $locus;

		my $ref_hash_positions_of_chrom = $features{$species}{$chromosome};
		my %hash_positions_of_chrom = %$ref_hash_positions_of_chrom;
		foreach my $positions_genes(keys(%hash_positions_of_chrom)){
			my ($start,$end) = split(/,/,$positions_genes);
			my $name = $features{$species}{$chromosome}{$positions_genes}{"name"};
			my $strand = $features{$species}{$chromosome}{$positions_genes}{"strand"};
			if ($start >= $limit_start && $start <= $limit_end){
				$genes_of_region{"$start-$end"}{"strand"} = $strand;
				$genes_of_region{"$start-$end"}{"name"} = $name;
			}
		}
		foreach my $gene(keys(%genes_of_region)){
	
			my ($start,$end) = split(/-/,$gene);
			my $name = $genes_of_region{"$start-$end"}{"name"};
			if (!$name){next;}
			$json_genes .= "                  {\n";
			my $uid_gene = $uid_genes{"$species-$name"};
			#if (!$name){print "pb $species $start-$end\n";exit;}
			my $strand = $genes_of_region{"$start-$end"}{"strand"};
			my $readjusted_start = $start - $limit_start;
			my $readjusted_end = $end - $limit_start;
			$readjusted_positions{$name}{"start"} = $readjusted_start;
			$readjusted_positions{$name}{"end"} = $readjusted_end;
			$readjusted_positions{$name}{"strand"} = $strand;
			my $grep = `grep '$name' $outhtml.matrix.txt`;
			my ($cluster) = split(/\t/,$grep);
			if (!$functions_of_cluster{$cluster}){
				my $function = `grep '$name' $genbank_files/../genes.txt`;
				my ($func) = split(/ \[/,$function);
				
				if ($func =~/^[\w\.]+ (.*)/){$func = $1;}
				$functions_of_cluster{$cluster} = $func;
			}
			if (!$uid_gene){
				my $random = int(rand(100000));
				$uid_gene = $random;
				$uid_genes{"$species-$name"} = $random;
			}
			$genes_of_clusters{$cluster}.="$uid_gene,";
			#$json_genes .= "CLLL: $cluster $uid_gene $species-$name $functions_of_cluster{$cluster}\n";
			$name=~s/\.\d+//g;
			$json_genes .= "                         \"uid\":\"$uid_gene\",\n";
			$json_genes .= "                         \"label\":\"$name\",\n";

			$json_genes .= "                         \"start\":$readjusted_start,\n";
			$json_genes .= "                         \"end\":$readjusted_end,\n";
			$json_genes .= "                         \"strand\":$strand,\n";
			$json_genes .= "                  },\n";
		}
		last;
	}
	chop($json_genes);
	chop($json_genes);
	$json_cluster .= $json_genes;
	$json_cluster .= "                ]\n";
	$json_cluster .= "                }\n";
	$json_cluster .= "           ]\n";
	$json_cluster .= "           },\n";
}
chop($json_cluster);
chop($json_cluster);
$json_cluster .= "],\n";
print JSON $json_cluster;


###########################################################
# create links between genes of clusters
###########################################################

my $num_pair = 0;
my $json_links = "\"links\":[\n";
foreach my $cl(keys(%genes_of_clusters)){
	if ($cl eq "ClutserID"){next;}
	print "=====\n$cl\n=====\n";
	my @genes = split(/,/,$genes_of_clusters{$cl});
	my %pairs;
	foreach my $gene(@genes){
		print "$gene\n";
		foreach my $gene2(@genes){
			if ($gene ne $gene2 && !$pairs{"$gene-$gene2"} && !$pairs{"$gene2-$gene"}){
				$pairs{"$gene-$gene2"} = 1;
				#$pairs{"$gene2-$gene"} = 1;
			}
		}
	}
	foreach my $pair(keys(%pairs)){
		my ($gene1,$gene2) = split(/-/,$pair);
		$num_pair++;
		my $start_gene1 = $readjusted_positions{$gene1}{"start"};
		my $end_gene1 = $readjusted_positions{$gene1}{"end"};
		my $start_gene2 = $readjusted_positions{$gene2}{"start"};
		my $end_gene2 = $readjusted_positions{$gene2}{"end"};
		$gene1=~s/\.\d+//g;
		$gene2=~s/\.\d+//g;
		$json_links .= qq~
		
{
         "uid":"$num_pair",
         "query":{
            "uid":"$gene1",
            "label":"$gene1",
         },
         "target":{
            "uid":"$gene2",
            "label":"$gene2",
         },
         "identity":0.5,
         "similarity":0.5
      },
~;
		#$json_links .= "{\"uid\":\"$num_pair\"},";
		print "$pair\n";
	}
	
}

chop($json_links);
#chop($json_links);
$json_links .= "],\n";
print JSON $json_links;


###########################################################
# create groups/clusters
###########################################################

my $json_groups = "\"groups\":[\n";
foreach my $clnb(keys(%genes_of_clusters)){
	if (!$clnb){next;}
	my $name_cluster = "CLUSTER".$clnb;
	if (length($clnb) == 1){$name_cluster = "CLUSTER000".$clnb;}
        elsif (length($clnb) == 2){$name_cluster = "CLUSTER00".$clnb;print "yes";}
        elsif (length($clnb) == 3){$name_cluster = "CLUSTER0".$clnb;}
	$name_cluster = $clnb;

	my $func = $functions_of_cluster{$clnb};
	$json_groups .= "    {\n";
	$json_groups .= "         \"uid\":\"$clnb\",\n";
	$json_groups .= "         \"label\":\"$name_cluster ($func)\",\n";
	#$json_groups .= "         \"label\":\"$name_cluster\",\n";
	$json_groups .= "         \"genes\":[\n";
	my @genes = split(/,/,$genes_of_clusters{$clnb});
	foreach my $gene(@genes){
		$json_groups .= "              \"$gene\",\n";
	}
	$json_groups .= "             ],\n";
	$json_groups .= "    },\n";
}
$json_groups .= "]\n";
print JSON $json_groups;

print JSON "}\n";
close(JSON);

my $json = `cat $outhtml.data.json`;




open(O,">$outhtml");
open(T,"template_clinker.html");
while(<T>){
	if (/JSONDATA/){print O $json;}
	else{print O $_;}
}
close(O);
close(T);
