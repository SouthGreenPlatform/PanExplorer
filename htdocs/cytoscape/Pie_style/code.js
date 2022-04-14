$(function(){ // on dom ready

$('#cy').cytoscape({
	
  style: cytoscape.stylesheet()
    .selector('node')
      .css({
        'width': 'mapData(width, 0, 10, 0, 100)',
        'height': 'mapData(width, 0, 10, 0, 100)',
        'content': 'data(id)',
        'pie-size': '98%',
        'pie-1-background-color': '#E8747C',
        'pie-1-background-size': 'mapData(foo, 0, 10, 0, 100)',
        'pie-2-background-color': '#74CBE8',
        'pie-2-background-size': 'mapData(bar, 0, 10, 0, 100)',
        'pie-3-background-color': '#74E883',
        'pie-3-background-size': 'mapData(baz, 0, 10, 0, 100)'
      })
    .selector('edge')
      .css({
		'width': 2,
		'line-color': 'black',
		'label': 'alexis'
      })
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
      }),
  
  elements: {
    nodes: [
      { data: { id: 'a', foo: 3, bar: 5, baz: 2,width: 8 } },
      { data: { id: 'b', foo: 6, bar: 1, baz: 3,width: 6 } },
      { data: { id: 'c', foo: 2, bar: 3, baz: 5,width: 3 } },
      { data: { id: 'd', foo: 7, bar: 1, baz: 2,width: 1 } },
      { data: { id: 'e', foo: 2, bar: 3, baz: 5,width: 10 } },
	  { data: { id: 'f', foo: 2, bar: 3, baz: 5,width: 10 } },
    ], 

    edges: [
      { data: { id: 'ae', weight: 1, source: 'a', target: 'e'} },
	  { data: { id: 'ag', weight: 30, source: 'a', target: 'g'} },
	  { data: { id: 'gh', weight: 30, source: 'g', target: 'h'} },
	  { data: { id: 'ab', weight: 30, source: 'a', target: 'b'} },
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

}); // on dom ready