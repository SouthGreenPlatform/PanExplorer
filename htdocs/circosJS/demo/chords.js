var gieStainColor = {
  gpos100: 'rgb(0,0,0)',
  gpos: 'rgb(0,0,0)',
  gpos75: 'rgb(130,130,130)',
  gpos66: 'rgb(160,160,160)',
  gpos50: 'rgb(200,200,200)',
  gpos33: 'rgb(210,210,210)',
  gpos25: 'rgb(200,200,200)',
  gvar: 'rgb(220,220,220)',
  gneg: 'rgb(255,255,255)',
  acen: 'rgb(217,47,39)',
  stalk: 'rgb(100,127,164)',
  select: 'rgb(135,177,255)'
}

var drawCircos = function (error, GRCh37, cytobands, data) {
  //Taille du container qui va contenir le circos
  var width = document.getElementsByClassName('mdl-card__supporting-text')[0].offsetWidth
  //Crée le circos
  var circos = new Circos({
    container: '#chordsChart',
    width: width,
    height: width
  })

  cytobands = cytobands.map(function (d) {
    return {
      block_id: d.chrom,
      start: parseInt(d.chromStart),
      end: parseInt(d.chromEnd),
      gieStain: d.gieStain,
      name: d.name
    }
  })

  data = data.map(function (d) {
    return {
      source: {
        id: d.source_id,
        start: parseInt(d.source_breakpoint) - 2000000,
        end: parseInt(d.source_breakpoint) + 2000000
      },
      target: {
        id: d.target_id,
        start: parseInt(d.target_breakpoint) - 2000000,
		end: parseInt(d.target_breakpoint) + 2000000
	      }
	    }
	  })
	  var conf = { 
	    innerRadius: width/2 - 80,
	    outerRadius: width/2 - 40,
	    labels: {
	      radialOffset: 70
	    },
	    ticks: {
	      display: true,
	      labelDenominator: 1000000
	    }
	  }
	  //console.log(GRCh37);
	  circos.layout(GRCh37,conf);

	  

	  circos.highlight('cytobands', cytobands, {
	    innerRadius: width/2 - 80,
	    outerRadius: width/2 - 40,
	    opacity: 0.3,
	    color: function (d) {
	      return gieStainColor[d.gieStain]
	    },
	    tooltipContent: function (d) {
      return d.name
    }
  })

  circos.chords(
    'l1',
    data,
    {
      logScale: false,
      opacity: 0.7,
      color: '#ff5722',
      tooltipContent: function (d) {
        return 'hfgv<h3><a href="http://google.fr">test</a>' + d.source.id + ' ➤ ' + d.target.id + ': ' + d.value + '</h3><i>(CTRL+C to copy to clipboard)</i>'
      }
    }
    );
    circos.render();

  }

  d3.queue()
  .defer(d3.json, './data/GRCh37.json') // Fichier qui définit tout les chromosomes 
  .defer(d3.csv, './data/cytobands.csv') // Les bandes autout du cercle 
  .defer(d3.csv, './data/fusion-genes.csv') // Lines between les chromosomes 
  .await(drawCircos)
