#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Long;

my %node_lengths;
my $gfa_file = $ARGV[0];
my $reference = $ARGV[1];
my $output_basename = $ARGV[2];

my %paths;
open(GFA, $gfa_file) or die "Cannot open pangenome.gfa: $!";
while(<GFA>) {
    chomp;
    if (/^S\t(\d+)\t(\w+)/) {
        my $segment_id = $1;
        my $segment_seq = $2;
        my $length = length($segment_seq);
        $node_lengths{$segment_id} = $length;
    }
    if (/^P\t([^\s]+)\t(.*)$/){
        my $path_name = $1;
        my ($genome, $rest) = split(/#/, $path_name);
        my $path_nodes = $2;
        $paths{$genome} = $path_nodes;
    }
}   
close(GFA);

my %node_positions;
my $path_of_reference = $paths{$reference};
my @nodes_in_path = split(/,/, $path_of_reference);
my $position = 0;
my @valid_nodes;
my %node_series;
my %strand_of_node;
my %pav;
foreach my $node(@nodes_in_path) {
    my $strand = "+";
    if ($node =~ /\+$/) {
        $strand = "+";
    } elsif ($node =~ /-$/) {
        $strand = "-";
    }
    $node =~ s/[+-]//;  # Remove orientation if present
    $strand_of_node{$node} = $strand;
    if (exists $node_lengths{$node}) {
        my $length=$node_lengths{$node};
        
        if ($length > 100) {
        #if ($length > 1) {
            push(@valid_nodes, $node);
            my $start = $position + 1;  
            my $end = $position + $length;
            $node_positions{$node} = "$start,$end";
            $node_series{$reference} .= "$start,$end|";
            $pav{$node}{$reference} = $strand.$length;
        }
        $position += $length; 
        # Node exists in the GFA, length already recorded
    } 
}

my @list_colors= ("#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080", "#ffffff", "#000000");

#print scalar @valid_nodes;


foreach my $path_name (sort keys %paths) {
    
    if ($path_name eq $reference) {
        next; # Skip the reference path
    }
    my $path_nodes = $paths{$path_name};
    my @nodes_in_path = split(/,/, $path_nodes);
    my $current_position = 0;
    my @positions;
    my %has_this_node;
    foreach my $node(@nodes_in_path) {
        
        my $strand = "+";
        if ($node =~ /\+$/) {
            $strand = "+";
        } elsif ($node =~ /-$/) {
            $strand = "-";
        }  # Remove orientation if present
        $node =~ s/[+-]//;
        $strand_of_node{$node} = $strand;
        if (exists $node_lengths{$node}) {
            $has_this_node{$node} = 1;   
        } 
    }
    foreach my $node(@valid_nodes) {
        if (exists $has_this_node{$node}) {
            my $length = $node_lengths{$node};
            my $strand = $strand_of_node{$node};
            $pav{$node}{$path_name} = $strand.$length;
            my $node_position = $node_positions{$node};
            $node_series{$path_name} .= "$node_position|";
        } 
    }
}
open(VALID, ">$output_basename.node_pav.tsv");
open(VALID2, ">$output_basename.node_pav.binary.csv");
print VALID "Node";
print VALID2 "";
foreach my $path_name (sort keys %paths) {
    print VALID "\t$path_name";
    print VALID2 ",$path_name";
}
print VALID "\n";
print VALID2 "\n";
my $count = 0;
foreach my $node(@nodes_in_path) {
    if (exists $pav{$node}) {
        $count++;
        print VALID $count."_".$node;
        print VALID2 $count."_".$node;
        foreach my $path_name (sort keys %paths) {
            if (exists $pav{$node}{$path_name}) {
                print VALID "\t".$pav{$node}{$path_name};
                print VALID2 ",1";
            } else {
                print VALID "\t0";
                print VALID2 ",0";
            }
        }
        print VALID "\n";   
        print VALID2 "\n";
    }
}
close(VALID);
close(VALID2);


open(SEGX, ">$output_basename.segments_x.txt");
open(SEGY, ">$output_basename.segments_y.txt");
my $num_ind = 0;
foreach my $path_name (sort keys %node_series) {
    $num_ind++;
    #print "$path_name\n";
    print SEGX $path_name."###";
    print SEGY $path_name."###";
    if (exists $node_series{$path_name}) {

        my $previous_position = 0;
        my $concat = "";
        my @list_nodes = split(/\|/, $node_series{$path_name});
        foreach my $node(@list_nodes) {
            my ($start, $end) = split(/,/, $node);
            
            my $gap = $start - $previous_position;
            $concat .= "$node,";
            if ($gap < 1000 ) {
            #if ($gap < 50 ) {
                
                my @pos = split(/,/, $concat);
                my $first = $pos[0];
                my $last = $pos[-1];
                #print "$node small $first $last\n";
            }
            else{
                
                my @pos = split(/,/, $concat);
                my $first = $pos[0];
                print SEGX "$first,$previous_position,None,";
                print SEGY "$num_ind,$num_ind,None,";
                $concat = "$node,";
            }
            
            $previous_position = $end;
        }
        # Finalisation of the last segment
        my @pos = split(/,/, $concat);
        my $first = $pos[0];
        print SEGX "$first,$previous_position,None,";
        print SEGY "$num_ind,$num_ind,None,";
    }
    print SEGX "\n";
    print SEGY "\n";
}
close(SEGX);
close(SEGY);

