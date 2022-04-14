var width = document.getElementsByClassName('mdl-card__supporting-text')[0].offsetWidth
var circosLine = new Circos({
  container: '#lineChart',
  width: width,
  height: width
})
 
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

var drawCircos = function (error, GRCh37, cytobands, snp250, snp, snp1m,daysOff, daysOff2, fusion_genes) {
  cytobands = cytobands
  .map(function (d) {
    return {
      block_id: d.chrom,
      start: parseInt(d.chromStart),
      end: parseInt(d.chromEnd),
      gieStain: d.gieStain,
      name: d.name
    }
  })

  fusion_genes = fusion_genes.map(function (d) {
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


  snp250 = snp250.map(function (d) {
    return {
      block_id: d.chromosome,
      position: (parseInt(d.start) + parseInt(d.end)) / 2,
      value: d.value
    }
  })

  snp = snp.map(function (d) {
    return {
      block_id: d.chromosome,
      position: (parseInt(d.start) + parseInt(d.end)) / 2,
      value: d.value
    }
  })
  daysOff = daysOff.map(function(d) {
    return {
      block_id: d.chromosome,
      start: parseInt(d.start),
      end: parseInt(d.end),
      value: parseFloat(d.value)
    };
  })

  daysOff2 = daysOff2.map(function(d) {
    return {
      block_id: d.chromosome,
      start: parseInt(d.start),
      end: parseInt(d.end),
      value: parseFloat(d.value)
    };
  })

  snp1m = snp1m.map(function (d) {
    return {
      block_id: d.chromosome,
      position: (parseInt(d.start) + parseInt(d.end)) / 2,
      value: d.value
    }
  })

  circosLine
  .layout(
    GRCh37,
    {
      innerRadius: width/3 - 100,
      outerRadius: width/3 - 80,
      labels: {display: true},
      ticks: {
        spacing: 6000000,
        labelSuffix: 'Mb',
        labelDenominator: 1000000,
        display: true}
      }
      )
  .line('snp-250', snp250, {
    innerRadius: 1.17,
    outerRadius: 1.5,
    maxGap: 1000000,
    min: 0,
    max: 0.015,
    color: '#222222',
    axes: [
    {
      showAxesTooltip : true,
      spacing: 1000000000,
      thickness: 1,
      color: '#666666'
    }
    ],
    tooltipContent: "meh"
  })
  .line('snp-250', snp250, {
    innerRadius: 1.1,
    outerRadius: 1.2,
    maxGap: 1000000,
    min: 0,
    max: 0.015,
    color: '#222222',
    axes: [
    {
      showAxesTooltip : true,
      spacing: 1000000000,
      thickness: 1,
      color: '#666666'
    }
    ],
    tooltipContent: "meh"
  })

  .line('snp-in', snp, {
    innerRadius: 1.55,
    outerRadius: 1.65,
    maxGap: 1000000,
    direction: 'in',
    min: 0,
    max: 0.015,
    color: '#222222',
    tooltipContent: null
  })
  .line('snp1m-in', snp1m, {
    innerRadius: 1.55,
    outerRadius: 1.65,
    maxGap: 1000000,
    direction: 'in',
    min: 0,
    max: 0.015,
    color: '#f44336',
    tooltipContent: null
  }).heatmap('days-off', daysOff, {
    innerRadius: 1.7,
    outerRadius: 1.75,
    logScale: false,
    color: 'Blues'
  }).heatmap('days-off2', daysOff2, {
    innerRadius: 1.75,
    outerRadius: 1.80,
    logScale: false,
    color: 'Blues'
  })
  .chords(
    'l1',fusion_genes,
    {
      logScale: false,
      opacity: 0.7,
      color: '#ff5722',
      tooltipContent: function (d) {
        return '<h3>' + d.source.id + ' ➤ ' + d.target.id + ': ' + d.value + '</h3><i>(CTRL+C to copy to clipboard)</i>'
      }
    }
    )
  .render()
}

d3.queue()
.defer(d3.json, './data/GRCh37.json')
.defer(d3.csv, './data/cytobands.csv')
.defer(d3.csv, './data/snp.density.250kb.txt')
.defer(d3.csv, './data/snp.density.txt')
.defer(d3.csv, './data/snp.density.1mb.txt')
.defer(d3.csv, './data/snp.density.250kb.txt')
.defer(d3.csv, './data/snp.density.1mb.txt')
  .defer(d3.csv, './data/fusion-genes.csv') // Lines between les chromosomes 
  .await(drawCircos)
