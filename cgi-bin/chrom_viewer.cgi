#!/usr/bin/perl

use strict;
use warnings;
use Carp qw (cluck confess croak);

use lib ".";

use CGI;

use Config::Configuration;

#use lib '/apps/www/coffee-genome/prod/cgi-bin';


my $cgi = CGI->new();


my $chromosome = $cgi -> param('chrom');
my $display = $cgi -> param('display');
my $session = $cgi -> param('session');
my $level = $cgi -> param('level');
my $extension="";
if ($level=~/\d+/){$extension = ".$level";}
my $config;
if ($session)
{
	$config = $Configuration::TEMP_EXECUTION_DIR."/$session/chrom_viewer.conf$extension";
}
else
{
	$config = '/apps/www/coffee-genome/prod/cgi-bin/chrom_viewer.conf';
}
my %CONFIG;
eval '%CONFIG = ( ' . `cat $config` . ')';
die "Error while loading configuration file: $@n" if $@;



sub log10 {
my $n = shift;
return log($n)/log(10);
}


my $chrom_to_display;
if ($chromosome)
{
	$chrom_to_display = $chromosome;
}

print $cgi->header();

print $cgi->start_html(
	-title  => "Chromosome viewer",
	-script => {
		'-language' => 'javascript', 
		'-src'		=> "$Configuration::JAVASCRIPT_DIR/jquery-1.5.1.min.js"
    },

);
if (!$chrom_to_display){$chrom_to_display = "All";}

print "Display: <select name='display' id='display' onchange='reload();'>";
foreach my $key(sort keys(%CONFIG))
{
	if (!$display){$display=$key;}
	my $select_title = $CONFIG{$key}{"select_title"};
	if ($display eq $key)
	{
		print "<option value='$key' selected=\"selected\">$select_title</option>\n";
	}
	else
	{
		print "<option value='$key'>$select_title</option>\n";
	}
}
print "</select>\n";
print "<input type=\"hidden\" id=\"session\" value=\"$session\"> \n";
print "<input type=\"hidden\" id=\"level\" value=\"$level\"> \n";

my $split_per_chrom = $CONFIG{$display}{"per_chrom"};

my %phenotype;
my %xData;

my $file = $CONFIG{$display}{"file"};
my $type_display = $CONFIG{$display}{"type"};
my %chroms;
my %headers;
my %data;
my @inds;
my @xaxis;
my $max = 0;
open(my $F,$file) or print "<br><b>Not able to open file $file</b><br/>";
my $numline = 0;
my $n = 0;
my $k_start = 2;
if ($type_display eq 'heatmap'){$k_start = 1;}
if ($type_display eq 'column'){$k_start = 1;}
if ($type_display eq 'boxplot'){
	if ($CONFIG{$display}{"header"} eq "false"){$k_start = 0;}
	if ($CONFIG{$display}{"header"} eq "true"){$k_start = 1;}
}
if ($type_display eq 'scatter'){$k_start = 3;}

my $cat_pie;
my $data_pie = "";
my %chrom_numbers;
my %lengths;
if ($type_display eq 'pie')
{	
	my @categories_pie;
	my $nsection = 0;
	while(<$F>)
	{
		my $line = $_;
		chomp($line);
		$line =~s/\n//g;
		$line =~s/\r//g;
		my @values = split(/\t/,$line);
		my $indice = $values[0];
		push(@categories_pie,$indice);
		my $val = $values[1];
		my @nbs;
		my @cat_interne;
		for (my $i = 2; $i <= $#values; $i++)
		{
			my ($type,$n) = split(":",$values[$i]);
			push(@nbs,$n);
			push(@cat_interne,$type);
		}
		my $cat_pie_interne = "'" . join("','",@cat_interne) . "'";
		my $nb_pie_interne = join(",",@nbs);
		$data_pie .= "{y: $val,color: colors[$nsection],drilldown: {name: '$indice',categories: [$cat_pie_interne],data: [$nb_pie_interne],color: colors[$nsection]}},";
		$nsection++;
	}
	$cat_pie = "'" . join("','",@categories_pie) . "'";
}
else
{
	my $max_val = 0;
	my $decalage = 0;
	my $track_num = 0;
	open(my $H,">$Configuration::HOME_DIR/biocircos/histogram.$session.js");
	print $H qq~
var LINE01 = [ "LINE01" , {
maxRadius: 240,
minRadius: 165,
LineColor: "#9932CC",
LineWidth: 2
} , [~;
	my $previous_x = 1;
	while(<$F>)
	{
		$numline++;
		my $line = $_;
		chomp($line);
		$line =~s/\n//g;
		$line =~s/\r//g;
		my @values = split(/\t/,$line);
		if ($numline == 1)
		{
			for (my $k = $k_start; $k <= $#values; $k++)
			{
				$headers{$k} = $values[$k];
				push(@inds,$headers{$k});
			}
		}
		else
		{
			my $chr = $values[0];
			if (!$chrom_numbers{$chr}){
				$chrom_numbers{$chr} = 1;
			}
			if (!$chrom_to_display or $CONFIG{$display}{"per_chrom"} eq "off")
			{
				$chrom_to_display=$chr;
				push(@xaxis,$chr);
			}
			my $x = $values[1];
			
			$chroms{$chr} = 1;
			if ($chr eq $chrom_to_display or $chrom_to_display eq 'All')
			{
				for (my $k = $k_start; $k <= $#values; $k++)
				{
					my $y = $values[$k];	
					if ($y > $max){$max = $y;}
					if ($type_display eq 'heatmap')
					{
						my $num = $k - 1;
						my $header = "";
						if ($headers{$k}){$header = $headers{$k};}
						$data{$header}.= "[$n,$num,$y],";
					}
					elsif ($type_display eq 'column')
					{
						$data{$headers{$k}}.= "$y,";
					}
					elsif ($type_display eq 'scatter')
					{
						#$data{$headers{$k}}.= "{name: '$chr',x: $x,y: $y},";
						my $name = $values[1];
						if ($values[4]){
							#$data{$values[0]}.= "{name: '$name',x: $values[2],y: $values[3],z: $values[4]},";
							$data{$values[0]}.= "{\"name\": \"$name\",\"x\": $values[2],\"y\": $values[3],\"z\": $values[4]},";
						}
						else{
							#$data{$values[0]}.= "{name: '$name',x: $values[2],y: $values[3]},";
							$data{$values[0]} .= "{\"name\": \"$name\",\"x\":$values[2],\"y\":$values[3]},";
						}
					}
					elsif ($type_display eq 'boxplot')
					{
						my $ind = $values[0];
						$phenotype{$headers{$k}}{$ind}=$y;
						if ($y ne "-999" && $y ne ""){$data{$headers{$k}}.= "$y,";}
					}
					else
					{
						if ($chrom_to_display eq 'All'){
							my $ystart = $decalage;
                                        		$y = $ystart + $values[$k];
							if (!$decalage && $values[$k] > $max_val){$max_val=$values[$k];}
							#$data{$headers{$k}}{$chr}.= "[$x,$ystart,$y],";
							$data{$headers{$k}}{$chr}.= $values[$k].",";
							$xData{$x} = 1;
						
							$lengths{$chr} = $x;
							my $valeur = $values[$k];
							if ($valeur < 0){$valeur = 0;}
							#if ($x > $lengths{$chr}){$lengths{$chr} = $x;}
							#print $H "{chr: \"$chr\", start: \"$previous_x\" , end: \"$x\", name: \"p\", value: \"$valeur\"},\n";
							print $H "{chr: \"$chr\", pos: \"$x\", value: \"$valeur\"},\n";
							$previous_x = $x;
						}
						else{
							$data{$headers{$k}}.= "[$x,$y],";
						}
					}
				}
				$n++;
			}
		}
	}
	print $H "]];\n";
	close($H);
}
close($F);

#if ($chrom_to_display eq 'All' && scalar keys %chrom_numbers > 30 && $type_display ne 'heatmap' && $type_display ne 'scatter')
#{
#        print "<br/><br/><b>Error </b>: Too many reference sequences to be displayed!!!<br/>\n<br/>\n";exit;
#}
	 
if ($split_per_chrom eq "on")
{
	print "Chromosome: <select name='chrom' id='chrom' onchange='reload();'>";
	#print "<option value='All' selected=\"selected\">All</option>\n";
	foreach my $chr(sort keys(%chroms))
	{
		if ($chromosome && $chromosome =~/$chr$/)
		{
			print "<option value='$chr' selected=\"selected\">$chr</option>\n";
		}
		else
		{
			print "<option value='$chr'>$chr</option>\n";
		}
	}
	print "</select>\n";
}
else
{
	print "<input type=hidden id='chrom' value=''>";
}

print "<br/><br/>";


my $colors = "[0, '#3060cf'],[0.5, '#fffbbc'],[0.9, '#c4463a'],[1, '#c4463a']";
if ($CONFIG{$display}{"colors"})
{
	$colors = $CONFIG{$display}{"colors"};
}

my $colorAxis = qq~
colorAxis: {
            stops: [
                $colors
            ],
            min: 0,
            max: $max,
            startOnTick: false,
            endOnTick: false,
            labels: {
                format: '{value}.'
            }
        },
~;
my $zoomType = "zoomType: 'xy',";
my $y_categories = "";
my $x_categories = "";
if ($type_display ne 'heatmap')
{
	$colorAxis = "";
	$zoomType = "zoomType: 'x',";
}

if ($type_display eq 'heatmap')
{
	$y_categories = "categories: ['" . join("','",@inds) . "'],";
	if (scalar @xaxis)
	{
		$x_categories = "categories: ['" . join("','",@xaxis) . "'],labels: {enabled:true, rotation: 90, align: 'left'},";
	}
}
if ($type_display eq 'column')
{
	if (scalar @xaxis)
	{
		$x_categories = "categories: ['" . join("','",@xaxis) . "'],labels: {enabled:true, rotation: 90, align: 'left'},";
	}
}


my $point_size = 2;
if ($CONFIG{$display}{"point_size"})
{
	$point_size = $CONFIG{$display}{"point_size"};
}


my $javascript = qq~
	
	<script type="text/javascript">
	
	function reload()
	{
		var chrom = document.getElementById('chrom').value;	
		var display = document.getElementById('display').value;	
		var session = document.getElementById('session').value;
		var level = document.getElementById('level').value;	
		var url = window.location.href; 
		var base_url = url.split('?');
		url = base_url[0];
		url += '?chrom='+chrom;
		url += '&display='+display;
		url += '&session='+session;
		url += '&level='+level;
		window.location.href = url;
	}
	
	</script>
~;

print $javascript;

my $window_height = "400px";
if ($chrom_to_display eq 'All' && $type_display ne 'pie'){
	$window_height = (200 + (scalar keys %chrom_numbers) * 80) ."px";
	#$window_height = "900px";
}
if ($type_display eq 'heatmap'){
	$window_height = "800px";
}
if ($chrom_to_display eq "All" && $type_display ne 'pie'){
	my $genome_text = "";
	foreach my $chr(sort {$a<=>$b} keys(%lengths)){
                my $length = $lengths{$chr};
                $genome_text .= "[\"$chr\" , $length],";
	}
	#open(O,">$Configuration::HOME_DIR/biocircos/output.$session.html");
	#open(I,"$Configuration::HOME_DIR/biocircos/test.html");
	#while(<I>){
	#	if (/histogram.js/){
	#		$_ =~s/histogram.js/histogram.$session.js/g;
	#	}
	#	if (/To be replaced/){
	#		$_ = $genome_text;
	#	}
	#	print O $_;
	#}
	#close(I);
	#close(O);
	#print "<iframe src='$Configuration::HOMEPAGE/biocircos/output.$session.html' width='1300' height='900' style=\"border:solid 0px black;\"></iframe>";exit;
	
}

my $html = qq~

<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="https://code.highcharts.com/highcharts-more.js"></script>
<script src="https://code.highcharts.com/modules/data.js"></script>
<script src="https://code.highcharts.com/modules/exporting.js"></script>
<script src="https://code.highcharts.com/modules/heatmap.js"></script>
<script src="https://code.highcharts.com/highcharts-3d.js"></script>



<!-- Additional files for the Highslide popup effect -->
<script type="text/javascript" src="https://highslide.com/highslide/highslide-full.min.js"></script>
<script type="text/javascript" src="https://sniplay.southgreen.fr/javascript/highslide.config.js" charset="utf-8"></script>
<link rel="stylesheet" type="text/css" href="https://www.highcharts.com/media/com_demo/highslide.css" />
<link rel="stylesheet" type="text/css" href="$Configuration::STYLE_DIR/multiple_chr.css" />

	<div id='plot' style='min-width:120px;height:$window_height'></div>
	~;
print $html;

my $stacking = "";
if ($CONFIG{$display}{"stacking"} eq "normal")
{
	$stacking = "stacking: 'normal',";
}
if ($CONFIG{$display}{"stacking"} eq "percent")
{
        $stacking = "stacking: 'percent',";
}

my $tooltip = "";
my $plotline = "";
if ($type_display eq 'scatter')
{
	$tooltip = "tooltip: {headerFormat: '<b></b>',pointFormat: '<b>{point.name}'},";
	$plotline = "plotLines: [{value: 0,color: 'black',width: 2,}]";
}
my $options3D = "";
my $depth = "";
my $xAxis = "xAxis: {$x_categories title: {text: '$CONFIG{$display}{\"xAxis\"}'},$plotline},";

if ($type_display eq 'boxplot'){
	$xAxis = "xAxis: {categories: ['".join("','",@inds)."']},";
}

my $maxYaxis = "";
if ($CONFIG{$display}{"maxyAxis"}){
	$maxYaxis = ",max: ".$CONFIG{$display}{"maxyAxis"};
}
my $minYaxis = "";
if ($CONFIG{$display}{"minyAxis"} =~/\d+/){
	$minYaxis = ",min: ".$CONFIG{$display}{"minyAxis"};
}
my $yAxis = "yAxis: {$y_categories title: {text: '$CONFIG{$display}{\"yAxis\"}'} $minYaxis $maxYaxis,$plotline},";


if ($chrom_to_display eq 'All'){
	$yAxis = "yAxis: {title:{text:'gfg',style:{'color':'white'}}, lineWidth: 0,minorGridLineWidth: 0,lineColor: 'transparent',labels: {enabled: false},minorTickLength: 0,tickLength: 0, gridLineColor:'white',},";
}

my $zAxis = "";
my $rotation_3d = "";
if ($CONFIG{$display}{"zAxis"})
{
	$options3D = "options3d: {enabled: true,alpha: 10,beta: 30,depth: 250,viewDistance: 5,}";
	$depth = "depth: 10,";
	$zoomType = "";
	$xAxis = "xAxis: {$x_categories title: {text: '$CONFIG{$display}{\"xAxis\"}'},},";
	$yAxis = "yAxis: {$y_categories title: {text: '$CONFIG{$display}{\"yAxis\"}'},},";
	$zAxis = "zAxis: {title: {text: '$CONFIG{$display}{\"zAxis\"}'},},";
	$rotation_3d = qq~
    \$(chart.container).bind('mousedown.hc touchstart.hc', function (e) {
        e = chart.pointer.normalize(e);

        var posX = e.pageX,
            posY = e.pageY,
            alpha = chart.options.chart.options3d.alpha,
            beta = chart.options.chart.options3d.beta,
            newAlpha,
            newBeta,
            sensitivity = 5; // lower is more sensitive

        \$(document).bind({
            'mousemove.hc touchdrag.hc': function (e) {
                // Run beta
                newBeta = beta + (posX - e.pageX) / sensitivity;
                chart.options.chart.options3d.beta = newBeta;

                // Run alpha
                newAlpha = alpha + (e.pageY - posY) / sensitivity;
                chart.options.chart.options3d.alpha = newAlpha;

                chart.redraw(false);
            },
            'mouseup touchend': function () {
                \$(document).unbind('.hc');
            }
        });
    });
	~;
}
my $pointer = "";
if ($CONFIG{$display}{"link"})
{
        my $jbrowse_link = $CONFIG{$display}{"link"};
        $pointer = qq~
	cursor:'pointer',
        point:
        {
                                                events: {
                                                        click: function (e) {
									pos = this.x;
                                                                        x = this.x - 20000;
                                                                        y = this.x + 20000;
								hs.graphicsDir = 'https://highslide.com/highslide/graphics/';
                                                                hs.outlineType = 'rounded-white';
                                                                hs.wrapperClassName = 'draggable-header';
                                                                hs.htmlExpand(null, {
                                                                        pageOrigin: {
                                                                                x: e.pageX,
                                                                                y: e.pageY
                                                                        },
                                                                        headingText: 'Links',
                                                                        maincontentText: '<a href=$jbrowse_link&loc=$chrom_to_display:'+x+'..'+y+'&highlight=$chrom_to_display:'+x+'..'+y+' target=_blank>View in JBrowse</a>',


                                    width: 200,
                                height:70
                                });
                            }
                        }
                    },
        ~;
	#$pointer = "";
}
my $title = $CONFIG{$display}{"title"};
if ($split_per_chrom eq "on")
{
	$title .= " ($chrom_to_display)";
}
	
#type: '$CONFIG{$display}{"type"}',

if ($type_display eq 'pie')
{
	my $javascript = qq~
	<script type='text/javascript'>
	\$(function () {

	
    var colors = Highcharts.getOptions().colors,
        categories = [$cat_pie],
        data = [$data_pie],
        browserData = [],
        versionsData = [],
        i,
        j,
        dataLen = data.length,
        drillDataLen,
        brightness;


    // Build the data arrays
    for (i = 0; i < dataLen; i += 1) {

        // add browser data
        browserData.push({
            name: categories[i],
            y: data[i].y,
            color: data[i].color
        });

        // add version data
        drillDataLen = data[i].drilldown.data.length;
        for (j = 0; j < drillDataLen; j += 1) {
            brightness = 0.2 - (j / drillDataLen) / 5;
            versionsData.push({
                name: data[i].drilldown.categories[j],
                y: data[i].drilldown.data[j],
                color: Highcharts.Color(data[i].color).brighten(brightness).get()
            });
        }
    }

	var chart;
		
							
	\$(document).ready(function() 
	{
		chart = new Highcharts.Chart({
				
			chart: {
					renderTo: 'plot',
					type: '$CONFIG{$display}{"type"}',
					$zoomType
				},
	
    
        title: 
		{
			text: '$title'
		},
		subtitle: 
		{
			text: '$CONFIG{$display}{"subtitle"}'
		},
        
        plotOptions: {
            pie: {
                shadow: false,
                center: ['50%', '50%']
            }
        },
        series: [{
            name: 'nb',
            data: browserData,
            size: '100%',
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                connectorColor: 'silver'
            },
        }, {
            name: 'nb',
            data: versionsData,
            size: '100%',
            innerSize: '100%',
            dataLabels: {
                formatter: function () {
                    // display only if larger than 1
                    return this.y > 1 ? '<b>' + this.point.name + ':</b> ' + this.y + ''  : null;
                }
            }
        }]
    });
});
});
</script>
~;
	print $javascript;
}
else
{
	my $type_display = $CONFIG{$display}{"type"};
	#$yAxis = "";
	#$xAxis = "";


	my $plotoptions = qq~ plotOptions: {
                                        series:{
                                           turboThreshold:20000//larger threshold or set to 0 to disable
                                        },
                                        $CONFIG{$display}{"type"}: {
                                                $stacking
                                                $tooltip
                                                marker: {
                                                        radius:$point_size,
                                                }
                                        }
                                },~;
	if ($type_display eq 'boxplot'){$plotoptions = "";}


	my $javascript = qq~
<script type='text/javascript'>
		\$(function () {

		\$.getJSON('$Configuration::WEB_DIR/json/data.$session.json', function (data) {
		var chart;
		
							
		\$(document).ready(function() {
			chart = new Highcharts.Chart({
				chart: {
					renderTo: 'plot',
					type: '$type_display',
					$zoomType
					$options3D
				},
				title: 
				{
					text: '$title'
				},
				subtitle: 
				{
					text: '$CONFIG{$display}{"subtitle"}'
				},
				legend:
				{
					enabled: true
				},
				$yAxis
				$xAxis
				$zAxis
				$colorAxis
				$plotoptions
				series: ~;
	
	
if ($chrom_to_display eq "All"){
	##################################################################################
	# create json formatted file
	##################################################################################
	open(my $JSON,">$Configuration::HOME_DIR/json/data.$session.json");
	my $xData_string = join(",",sort {$a<=>$b} keys(%xData));
	my $nb_x = scalar keys(%xData);
	my $json_string = qq ~
{
    "xData": [$xData_string],
    "datasets": [
~;
	foreach my $header(sort {$a<=>$b} keys(%data)){
		my $ref_hash = $data{$header};
		my %hash2 = %$ref_hash;
		foreach my $key(sort {$a<=>$b} keys(%hash2)){
			my $chr_data = $data{$header}{$key};
			my $nb_data = scalar split(",",$chr_data);
			if ($nb_data < $nb_x){
				my $diff = $nb_x - $nb_data;
				$chr_data .= "0," x $diff;
			}			
			chop($chr_data);
			$json_string.= qq~
{
"name": "$key",
"data": [$chr_data],
"unit": "Mb",
"type": "area"
},~;
#"name": "$key",
#"data": [$chr_data],
#"unit": "Mb",
#"type": "area"
		}
	}
	chop($json_string);
	$json_string .= "]\n}";
	print $JSON $json_string;
	close($JSON);


	$javascript = qq~
<script type='text/javascript'>
\$(function () {
    \$.getJSON('$Configuration::WEB_DIR/json/data.$session.json', function (activity) {
        \$.each(activity.datasets, function (i, dataset) {

            // Add X values
            dataset.data = Highcharts.map(dataset.data, function (val, i) {
                return [activity.xData[i], val];
            });

            \$('<div class="chart_multi_chr">')
                .appendTo('#plot')
                .highcharts({
                    chart: {
                        marginLeft: 100, // Keep all charts left aligned
                        spacingTop: 0,
                        spacingBottom: 0,
                        zoomType: 'x',
                        // pinchType: null // Disable zoom on touch devices
                    },
                    title: {
                        text: dataset.name,
                        align: 'left',
                        margin: 0,
                        ymargin: 10,
                        y: 80,
			x: 5
                    },
                    legend: {
                        enabled: false
                    },	
                    yAxis: {
                        title: {
                            text: null
                        }
                    },
                    series: [{
                        data: dataset.data,
                        name: dataset.name,
                        type: dataset.type,
                        color: Highcharts.getOptions().colors[3],
                        fillOpacity: 0.3,
                    }]
                });
 });
});
});
</script>
~;
	print $javascript;
	exit;
}
else{
	print $javascript;
	if ($type_display eq 'boxplot'){
		my %medians;
		print "[{data: [";
		my $n = 0;
		#foreach my $header(keys(%data)){
		foreach my $header(@inds){
			$n++;
			my @values = split(",",$data{$header});
			open(my $F,">$file.calc.in.$header");print $F join("\n",@values);close($F);
			my $res = `$Configuration::CALC_EXE < $file.calc.in.$header`;
			my ($min,$max,$min,$lower_quartile,$median,$upper_quartile) = split(";",$res);	
			print "[$min,$lower_quartile,$median,$upper_quartile,$max],";
			#$medians{$header} = $median;
			$medians{$header} = $lower_quartile;
		}
		print "]}]";
		
		foreach my $trait(keys(%phenotype)){
			my $refhash = $phenotype{$trait};
			my %hash2 = %$refhash;
			my $median = $medians{$trait};
			open(my $TEST,">$file.calc.in.$trait.under_quartile.xls");
			foreach my $ind(keys(%hash2)){
				my $val = $phenotype{$trait}{$ind};
				if ($val < $median && $val ne "-999"){
					print $TEST "$ind\n";
				}

			}
			close($TEST);
		}
		
	}
	else{
		print "data\n";
	}
	open(my $JSON,">$Configuration::HOME_DIR/json/data.$session.json");
	print $JSON "[\n";
	my $n = 0;
	foreach my $header(sort {$a<=>$b} keys(%data)){
		
		#print "{\n";
		#print "name: '$header',\n";
		#print "data: [" . $data{$header} . "],\n";
		#print "data: data,\n";
		#if ($CONFIG{$display}{"group_padding"} eq "0")
		#{
			#print "pointPadding: 0,\n";
			#print "groupPadding: 0,\n";
		#}
		#print "marker: {radius:$point_size},\n";
		#print "$pointer\n";
		#print "},\n";

		my $data_value = $data{$header};
		chop($data_value);
		if ($n>0){print $JSON ",";}
		print $JSON "{\n";
		print $JSON "\"name\": \"$header\",\n";
		print $JSON "\"data\": [$data_value]\n";
		if ($CONFIG{$display}{"group_padding"} eq "0"){
			print $JSON ",\"pointPadding\": 0,\n";
			print $JSON "\"groupPadding\": 0\n";
		}
		print $JSON "}\n";
		$n++;
	}
	print $JSON "]\n";
	close($JSON);
}
my $javascript_end = qq~			
			});

		$rotation_3d
		});

	});

	});
		
		</script>
~;
print $javascript_end;
}
			






