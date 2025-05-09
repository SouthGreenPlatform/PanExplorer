#!/usr/bin/perl

use strict;

my $gff_dir = $ARGV[0];
my $coregene_file = $ARGV[1];
my $output = $ARGV[2];

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
                                if ($start_first == $info_cluster{$first_cluster}{$strain}{"start"} && $end_last == $info_cluster{$last_cluster}{$strain}{"end"}){
                                        $strand = "+";
                                }
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

my $num_block = 0;
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
                }
                print OUT ",$num_block\n";
        }
}
close(B);
close(OUT);