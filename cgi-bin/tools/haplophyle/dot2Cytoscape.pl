#!/usr/bin/perl

use strict;

use Getopt::Long;

my $usage = qq~Usage:$0 <args> [<opts>]

where <args> are:

    -i, --input         <dot file obtained by haplophyle>
    -h, --html          <Cytoscape HTML output>
~;
$usage .= "\n";

my ($input,$htmlfile);


GetOptions(
	"input=s"      => \$input,
	"html=s"       => \$htmlfile,
);

die $usage
  if ( !$input || !$htmlfile );

my @colors = ("#ed292a","#ed292a","#82ABA0","#2255a6","#6ebe43","#e76599","#662e91","#c180ff","#ea8b2f","#fff100","#666666","#01ffff","#bfbfbf","#2ac966","#666666");

my %hash;
my $pie_block = "";
my $nb_groups = 0;
for (my $i = 1; $i <= $nb_groups; $i++){
	$pie_block .= "'pie-$i-background-color': '$colors[$i]',\n";
	$pie_block .= "'pie-$i-background-size': 'mapData(group$i, 0, 10, 0, 100)',\n";
}

open(HTML_CYTOSCAPE,">$htmlfile");
my $html = qq~<!DOCTYPE html>
<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<link href="Pie_style/style.css" rel="stylesheet">
<meta charset="utf-8">
<meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
<title>Pie style</title>
<script src="Pie_style/jquery.js"></script>
<script src="Pie_style/cytoscape.js"></script>
<script type="text/javascript">
\$(function(){ // on dom ready

\$('#cy').cytoscape({

  style: cytoscape.stylesheet()
    .selector(':selected')
      .css({
        'background-color': 'black',
        'line-color': 'black',
        'opacity': 1
      })
    .selector('.faded')
      .css({
        'opacity': 0.25,
        'text-opacity': 0
      })
    .selector('edge')
      .css({
                'width': 1,
		'height': 1,
                'line-color': 'black',
      })
    .selector('node')
      .css({
        'width': 'mapData(width, 0, 10, 0, 100)',
        'height': 'mapData(width, 0, 10, 0, 100)',
        'content': 'data(id)',
        'pie-size': '98%',
		'background-color': 'data(color)',
        $pie_block
      }),
elements: {
    nodes: [
~;
my $done = 0;
open(IN,"$input");
open(OUT,">$htmlfile.json");
open(OUT2,">$htmlfile.d3.json");
print OUT "{\n";
print OUT "  \"nodes\": [\n";
my $ok = 0;
my $json = "{\n  \"nodes\": [\n";
while(<IN>){
	if (/(^[\w\.\-]+)\s\[.*width=([\d\.]+),/){
		my $node = $1;
		my $size = $2 * 8;
		#my $size = $2 * 15;
		$html.= "{ data: { id: '$node', width: $size, color:'grey'} },\n";
		print OUT "{\"id\": \"$node\"},\n";
		my $pie = "";
		#if (/fillcolor=\"([^;]+);/){
		if (/fillcolor/){
			my @colors = split(";",$1);
			$pie = "\"pieChart\" : [";
			my $n = 0;
			foreach my $color(@colors){
				$n++;
				$pie .= "{ \"color\": $n, \"percent\": 25 },";
			}
			$pie .= "],";
		}
		$json .= "{\"id\": \"$node\", $pie \"size\": $size, \"color\": \"grey\"},\n";
	}
	if (/([\w\.\-]+) -- ([\w\.\-]+)/){
		if ($done == 0){
			$done = 1;
			$html .= "],\n";
			$html .= "edges: [\n";
		}
		$done = 1;
		$html.= "{ data: { id: '$1$2', weight: 10, source: '$1', target: '$2'} },\n";
		if ($ok == 0){
			chop($json);chop($json);
			$json .= "],\n";
			$json .= "\"links\": [\n";
		}
		print OUT "{\"source\": \"$1\", \"target\": \"$2\", \"value\": 1},\n";
		$json .= "{\"source\": \"$1\", \"target\": \"$2\", \"value\": 5},\n";
		$ok=1;
	}
}
close(IN);
print OUT "]\n";
print OUT "}";
chop($json);chop($json);
$json .= "]\n}";
print OUT2 $json;
close(OUT);
close(OUT2);

$html.= qq~
]
  },
layout: {
        name: 'cose',
    padding: 10
  },

  ready: function(){
    window.cy = this;
  }
});

});

</script>
</head>
<body>
<div id="cy">
</div>
~;
print HTML_CYTOSCAPE $html;
close(HTML_CYTOSCAPE);
