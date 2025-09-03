#!/usr/bin/perl

use strict;

my $gff_dir = $ARGV[0];
my $coregene_file = $ARGV[1];
my $output = $ARGV[2];
my $minimal_size_blocks_to_be_displayed = $ARGV[3];

my %order_by_strain;
my %info_cluster;

open(CG,$coregene_file);
my $first_line = <CG>;
$first_line =~s/\n//g;
$first_line =~s/\r//g;
my %cluster_of_genes;
my @samples = split(/\t/,$first_line);
while(<CG>){
    my $line = $_;
    $line =~s/\n//g;
    $line =~s/\r//g;
    # do not consider core-genes with paralog (multiple copies in the same sample)
    if ($line =~/,/){next;}

    my @infos = split(/\t/,$line);
    my $cluster = $infos[0];
    for (my $i = 1; $i <= $#infos; $i++){
        my $sample = $samples[$i];
        if ($sample =~/(.*)_x/){
                $sample = $1;
                #if ($sample !~/CFB/){
                #        next;
                #}
                my ($gene) = split(/,/,$infos[$i]);

                $cluster_of_genes{$gene}{$sample} = $cluster;
        }
        
    }
}
close(CG);

my %cluster_is_found;
open(LS,"ls $gff_dir/*ptt |");
while(<LS>){
    my $file = $_;
    if ($file =~/([^\/]*).ptt/){
        my $sample = $1;
        open(F,$file);
        while(<F>){
            my @infos = split(/\t/,$_);
            my $gene = $infos[3];
            my $chrom = $infos[4];
            my $chrom_num = 1;
            if ($chrom =~/(\d+)/){
                $chrom_num = $1;
            }
            my $positions = $infos[0];
            my ($position,$position2) = split(/\.\./,$positions);
            
            if ($chrom_num != 1){
                next;
            }
            if ($position > 2000000){
                #next;
            }

            
            if (!$gene or $_=~/Location/){next;}
            my $cluster = $cluster_of_genes{$gene}{$sample};
            $cluster_is_found{$cluster}++;
            # not a core-gene
            if (!$cluster){
                next;
            }
            $order_by_strain{$sample}{$position} = $cluster;
            $info_cluster{$cluster}{$sample}{"start"} = $position;
            $info_cluster{$cluster}{$sample}{"end"} = $position2;
        }
        close(F);
    }
}
close(LS);


my %suite_of_clusters;
open(ORDER_CLUSTERS,">$output.order_clusters1.txt");
foreach my $strain(keys(%order_by_strain)){
                        print ORDER_CLUSTERS "$strain\n";
                        my $ref_hash1 = $order_by_strain{$strain};
                        my %subhash1 = %$ref_hash1;
                        foreach my $position(sort {$a<=>$b} keys(%subhash1)){
                                my $cluster = $order_by_strain{$strain}{$position};
                                if ($cluster_is_found{$cluster} == scalar keys(%order_by_strain)){
                                        $suite_of_clusters{$strain}.= "$cluster-";
                                        print ORDER_CLUSTERS "$cluster-";
                                }
                        }
                        print ORDER_CLUSTERS "\n";

                        foreach my $position(sort {$b<=>$a} keys(%subhash1)){
                                my $cluster = $order_by_strain{$strain}{$position};
                                if ($cluster_is_found{$cluster} == scalar keys(%order_by_strain)){
                                        $suite_of_clusters{$strain}.= "$cluster-";
                                        print ORDER_CLUSTERS "$cluster-";
                                }
                        }
                        print ORDER_CLUSTERS "\n";
}
close(ORDER_CLUSTERS);

my %groups_of_clusters;
open(ORDER_CLUSTERS2,">$output.order_clusters2.txt");
foreach my $strain(keys(%order_by_strain)){
                        my $ref_hash1 = $order_by_strain{$strain};
                        my %subhash1 = %$ref_hash1;
                        my $to_be_tested = "";
                        my $previous;
                        foreach my $position(sort {$a<=>$b} keys(%subhash1)){
                                my $cluster = $order_by_strain{$strain}{$position};
                                $to_be_tested .= "$cluster-";
                                my $size = scalar(split(/\-/,$to_be_tested));
                                if ($size > 1){
                                        my $test_presence = 0;
                                        foreach my $strain2(keys(%order_by_strain)){
                                                if ($suite_of_clusters{$strain2} =~/$to_be_tested/){$test_presence++;}
                                        }
                                        $test_presence =~s/\n//g;$test_presence =~s/\r//g;
                                        print ORDER_CLUSTERS2 "$position $to_be_tested $test_presence\n";


                                        if ($test_presence < scalar keys(%order_by_strain)){
                                                $to_be_tested = "$cluster-";
                                        }
                                        else{
                                                $groups_of_clusters{$to_be_tested}=1;
                                                delete($groups_of_clusters{$previous});
                                                print ORDER_CLUSTERS2 "Good!!!!!\n";
                                        }
                                }
                                $previous = $to_be_tested;
                        }
                        print ORDER_CLUSTERS2 "finished\n";
                        last;
}
close(ORDER_CLUSTERS2);

my %final_blocks;
my %strand_of_blocks;
my $concat = "";
open(ORDER_CLUSTERS3,">$output.order_clusters3.txt");
foreach my $group(keys(%groups_of_clusters)){
                        my @clusters_in_block = split(/-/,$group);
                        my $first_cluster = $clusters_in_block[0];
                        my $last_cluster = $clusters_in_block[$#clusters_in_block];
                        $concat .= "[";
                        my $num_track = 0;
                        foreach my $strain(keys(%order_by_strain)){
                                my @list_positions_clusters;
                                push(@list_positions_clusters,$info_cluster{$first_cluster}{$strain}{"start"});
                                push(@list_positions_clusters,$info_cluster{$first_cluster}{$strain}{"end"});
                                push(@list_positions_clusters,$info_cluster{$last_cluster}{$strain}{"start"});
                                push(@list_positions_clusters,$info_cluster{$last_cluster}{$strain}{"end"});
                                my @sorted_list_positions_clusters = sort {$a<=>$b} @list_positions_clusters;
                                my $start_first = $sorted_list_positions_clusters[0];
                                my $end_last = $sorted_list_positions_clusters[$#sorted_list_positions_clusters];

                                my $strand = "-";
                                #print "$first_cluster $last_cluster\n";
                                if ($start_first == $info_cluster{$first_cluster}{$strain}{"start"} && $end_last == $info_cluster{$last_cluster}{$strain}{"end"}){
                                        $strand = "+";
                                }
                                $strand_of_blocks{$start_first}{$strain} = $strand;
                                #my $num_track = $info_cluster{$last_cluster}{$strain}{"num_track"};
                                $num_track++;
                                my $taxid = $info_cluster{$last_cluster}{$strain}{"taxid"};
                                $concat .= "{\"name\": \"$taxid.fasta\",\"start\": $start_first,\"end\": $end_last,\"strand\": \"$strand\",\"lcb_idx\": $num_track},";
                        }
                        chop($concat);
                        $concat .= "],\n";
                        $final_blocks{$group} = 1;
                        print ORDER_CLUSTERS3 "$group\n";
}
close(ORDER_CLUSTERS3);
#print "$concat\n";

my $num_block = 0;
my %limits_of_blocks;
open(B,"$output.order_clusters3.txt");
open(OUT,">$output");
print OUT ",".join(",",keys(%order_by_strain)).",num_block\n";
while(<B>){
        $num_block++;
        my $line = $_;
        $line =~s/\n//g;
        $line =~s/\r//g;
        $line =~s/-$//g;
        my @clusters = split(/-/,$line);
        foreach my $cluster(@clusters){
                print OUT "$cluster";
                foreach my $strain(keys(%order_by_strain)){
                        my $position = $info_cluster{$cluster}{$strain}{"start"};
                        print OUT ",$position";
                        $limits_of_blocks{$strain}{$num_block} .= "$position,";
                }
                print OUT ",$num_block\n";
        }
}
close(B);
close(OUT);
my $max_num_block = $num_block;

########################################################
# construct JSON file for visualization with Clinker
########################################################
my %colinear_block_infos;
my $json = "{\n";
$json .= "\"clusters\":[\n";
foreach my $strain(keys(%order_by_strain)){
        $json .= "\t{\n";
        $json .= "\t\"uid\":\"$strain\",\n";
        $json .= "\t\"name\":\"$strain\",\n";
        $json .= "\t\"loci\":[\n";
        $json .= "\t{\n";

        $json .= "\t\t\"uid\":\"$strain\",\n";
        $json .= "\t\t\"name\":\"$strain\",\n";
        $json .= "\t\t\"start\":0,\n";
        $json .= "\t\t\"end\":100000,\n";
        $json .= "\t\t\"genes\":[\n";
        for (my $num_block = 1; $num_block <= $max_num_block; $num_block++){
                my $positions = $limits_of_blocks{$strain}{$num_block};
                my @pos = split(/,/,$positions);
                my $start = $pos[0];
                my $end = $pos[$#pos];
                my $strand;
                if ($strand_of_blocks{$start}{$strain}){
                        $strand = $strand_of_blocks{$start}{$strain};
                }
                elsif ($strand_of_blocks{$end}{$strain}){
                        $strand = $strand_of_blocks{$end}{$strain};
                }
                
                my $strand_value = "1";
                if ($strand eq "-"){
                        $strand_value = "-1";
                }
                #print "$strain $start $end $strand\n";
                my $number_of_genes_in_block = scalar @pos;
                $colinear_block_infos{$num_block} = $number_of_genes_in_block;

                if ($number_of_genes_in_block > $minimal_size_blocks_to_be_displayed){
                        my $bloc_name = $strain."_block".$num_block;
                        $start = $start / 50;
                        $end = $end / 50;

                        $json .= "\t\t{\n";
                        $json .= "\t\t\t\"uid\":\"$bloc_name\",\n";
                        $json .= "\t\t\t\"label\":\"$bloc_name\",\n";
                        if ($start < $end){
                                $json .= "\t\t\t\"start\":$start,\n";
                                $json .= "\t\t\t\"end\":$end,\n";
                        }
                        else{
                                $json .= "\t\t\t\"start\":$end,\n";
                                $json .= "\t\t\t\"end\":$start,\n";
                        }
                        $json .= "\t\t\t\"strand\":$strand_value\n";

                        $json .= "\t\t},\n";
                }
                
        }
        chop($json);chop($json);

        $json .= "\n\t\t]\n";
        $json .= "\t}\n";
        $json .= "\t]\n";
        $json .= "\t},\n";
}
chop($json);chop($json);

$json .= "],\n";
$json .= "\"links\":[\n";
my $uid_link = 0;
my %links_done;
for (my $num_block = 1; $num_block <= $max_num_block; $num_block++){

        my $number_of_genes_in_block = $colinear_block_infos{$num_block};
        if ($number_of_genes_in_block <= $minimal_size_blocks_to_be_displayed){
                next;
        }
        foreach my $strain1(keys(%order_by_strain)){
                foreach my $strain2(keys(%order_by_strain)){
                        if ($strain1 eq $strain2){next;}
                        my $query = $strain1."_block".$num_block;
                        my $target = $strain2."_block".$num_block;
                        
                        if (!$links_done{$target}{$query}){
                                $uid_link++;
                                $json .= "\t{\n";
                                $json .= "\t\t\"uid\":\"$uid_link\",\n";

                                $json .= "\t\t\"query\":{\n";
                                $json .= "\t\t\t\"uid\":\"$query\",\n";
                                $json .= "\t\t\t\"label\":\"$query\"\n";
                                $json .= "\t\t},\n";

                                $json .= "\t\t\"target\":{\n";
                                $json .= "\t\t\t\"uid\":\"$target\",\n";
                                $json .= "\t\t\t\"label\":\"$target\"\n";
                                $json .= "\t\t},\n";

                                $json .= "\t\t\"identity\":0.5,\n";
                                $json .= "\t\t\"similarity\":0.5\n";

                                $json .= "\t},\n";

                                $links_done{$query}{$target} = 1;
                                $links_done{$target}{$query} = 1;
                        }
                        
                }
        }
}
chop($json);chop($json);
$json .= "\n],\n";

$json .= "\"groups\":[\n";
for (my $num_block = 1; $num_block <= $max_num_block; $num_block++){
        my $number_of_genes_in_block = $colinear_block_infos{$num_block};
        if ($number_of_genes_in_block <= $minimal_size_blocks_to_be_displayed){
                next;
        }

        $json .= "\t{\n";
        my $number_of_genes_in_block = $colinear_block_infos{$num_block};
        $json .= "\t\t\"uid\":\"$num_block\",\n";
        $json .= "\t\t\"label\":\"Colinear block $num_block: $number_of_genes_in_block genes\",\n";
        $json .= "\t\t\"genes\":[\n";
        foreach my $strain(keys(%order_by_strain)){
                my $bloc_name = $strain."_block".$num_block;
                $json .= "\t\t\t\"$bloc_name\",\n";
        }
        chop($json);chop($json);
        $json .= "\n";
        $json .= "\t\t]\n";
        $json .= "\t},\n";
}
chop($json);chop($json);
$json .= "\n";
$json .= "]\n";
$json .= "}\n";

open(JSON,">$output.clinker.json");
print JSON $json;
close(JSON);
