var id = 0;
var options = ["Chords","HighLight","Line","HeatMap","Scatter","Histogram","Stack","Text"];
//Init de la var width pour afin de déterminer la largeur du graphe s'adapte a la largeur de la page au premier chargement 4 
var width = document.getElementsByClassName('circoscontainer')[0].offsetWidth
//Creation du circos et def de la div dans laquelle il va aller 
var circos = new Circos({
  container: '#lineChart', 
  width: width,
  height: width
})
var chromosomeData = [];
var heatmapcontainer  = [];
//Couleurs des cytobands
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
var inversions = [];

var button = document.getElementById("newTrackButton");
button.setAttribute("onclick","addNewTrack()");
document.getElementById("titleMeh").innerHTML = randomName();
//DONE
//Parse les chromosomes et les stocke dans une variable globale
function chromosomeParser(data){
  chromosomeData = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    var color;
    if(localsplit[2] == undefined){
      color = "#272727";
    }else{
      color = localsplit[2];
    }
    localchr = {
      id : localsplit[0],
      label : localsplit[0],
      len : parseInt(localsplit[1]),
      color : color
    }
    chromosomeData.push(localchr);
  }
  return chromosomeData;
}
//Pends des fichiers au format Chr debut fin valeur
//Utile pour HeatMap, Linen, scatter
function scatterParser(data){
  var array = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    localchr = {
      chromosome : localsplit[0],
      start : parseInt(localsplit[1]),
      value : localsplit[2] 
    }
    //
    array.push(localchr);
  }
  return array;
}
function getChromosomeLength(chromosome){
  for(var i = 0;i<chromosomeData.length;i++){
    if(chromosomeData[i].id == chromosome){
      return chromosomeData[i].len;
    }
  }
}
function heatmapParser(data){
  var array = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  var xlength = split[0].split(" ");
  for(var xl = 0;xl<xlength.length-2;xl++){
    array[xl]=new Array();
  }
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    for(var n = 2; n<localsplit.length; n++){
      var next;
      if(split[i+1] !== undefined){
        next = split[i+1].split(" ")[1];
        if(next == 0){
          next = getChromosomeLength(localsplit[0]);
        }
      }
      else{
        next = getChromosomeLength(localsplit[0]);
      }
      localchr = {
        chromosome : localsplit[0],
        start : parseInt(localsplit[1]),
        end : parseInt(next),
        value : localsplit[n] 
      }
      array[n-2].push(localchr);
    }
  }
  return array;
}
function lineParser(data){
  var array = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  var xlength = split[0].split(" ");
  for(var xl = 0;xl<xlength.length-2;xl++){
    array[xl]=new Array();
  }
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    for(var n = 2; n<localsplit.length; n++){
      localchr = {
        chromosome : localsplit[0],
        start : parseInt(localsplit[1]),
        value : localsplit[n] 
      }
      array[n-2].push(localchr);
    }
  }
  return array;
}
//Parser pour les cytobands
function cytobandsParser(data){
  var array = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    localchr = {
      chromosome : localsplit[0],
      start : parseInt(localsplit[1]),
      end : parseInt(localsplit[2]),
      name : localsplit[3],
      gieStain : localsplit[4] 
    }
    //
    array.push(localchr);
  }
  return array;
}
//Parser for Chords
function chordsParser(data){
  var chords = [];
  var split = data.split("\n");
  var localsplit  = "";
  var localchr="";
  for (var i = 0; i < split.length; i++) {
    localsplit = split[i].split(" ");
    if(((localsplit[1]>localsplit[2]) && (localsplit[4]<localsplit[5])) || ((localsplit[1]<localsplit[2]) && (localsplit[4]>localsplit[5]))){
      localchr = {
        source : localsplit[0],
        source_start : parseInt(localsplit[1]),
        source_end : parseInt(localsplit[2]),
        target : localsplit[3],
        target_start : parseInt(localsplit[4]),
        target_end : parseInt(localsplit[5]),
        source_label : localsplit[0],
        target_label : localsplit[3]
      }
      inversions.push(localchr);
    }else{
      localchr = {
        source : localsplit[0],
        source_start : parseInt(localsplit[1]),
        source_end : parseInt(localsplit[2]),
        target : localsplit[3],
        target_start : localsplit[4],
        target_end : parseInt(localsplit[5]),
        source_label : parseInt(localsplit[0]),
        target_label : localsplit[3]
      }
      chords.push(localchr);
    }
  }
  return chords;
}



//Config generation part
function layoutConfig(spacing,suffix){
  var layout = {
    innerRadius: 295,
  outerRadius: 300,
  cornerRadius: 10,
  gap: 0.04, // in radian
  labels: {
    display: true,
    position: 'center',
    size: 16,
    color: '#000000',
    radialOffset: 20,
  },
  ticks: {
    display: true,
    color: 'grey',
    spacing: 10000000,
    labels: true,
    labelSpacing: 10,
    labelSuffix: 'Mb',
    labelDenominator: 1000000,
    labelDisplay0: true,
    labelSize: 8,
    labelColor: '#000000',
    labelFont: 'default',
    majorSpacing: 5,
    size: {
      minor: 2,
      major: 5,
    }
  },
  clickCallback: null
/*
    innerRadius: width - 100,
    outerRadius: width - 80,
    labels: {
      display: true,
      size: '44px',
      radialOffset : 60
    },
    ticks: {
      //def 6000000
      spacing: spacing,
      //def Mbi
      labelSize: '20px',
      labelSuffix: suffix,
      labelDenominator: 1000000,
      display: true
    }
*/
  }

  return layout;
}
function heatmapConfig(position,color,orientation){
  if(orientation == "out"){
    var radius = 1.2 + (position * 0.22)
    var innerRad = radius;
    var outerRadius = radius + 0.2
  }else{
    var radius = 1 - (position * 0.12);
    var outerRadius = radius;
    var innerRad = radius - 0.1
  }
  //onsole.log("inner : " + innerRad + " outer : " + outerRadius)
  var heatmap = {
    innerRadius: innerRad,
    outerRadius: outerRadius,
    logScale: false,
    color: color
  }
  return heatmap;
}
function chordConfig(option){
  if(option == "1"){
    var chord = {
      logScale: false,
      opacity: 0.7,
      color: '#ff5722',
      tooltipContent: function (d) {
        return '<h3>' + d.source.id + ' > ' + d.target.id + ': ' + d.value + '</h3><i>(CTRL+C to copy to clipboard)</i>';
      }
    }
  }
  else{
    var chord = {
      logScale: false,
      opacity: 0.7,
      color: '#1f52a5',
      tooltipContent: function (d) {
        return '<h3>' + d.source.id + ' > ' + d.target.id + ': ' + d.value + '</h3><i>(CTRL+C to copy to clipboard)</i>';
      }
    }
  }
  return chord;
}
function lineConfig(position,orientation){
  var orientation_line = "out";
  if(orientation == "out"){
    orientation_line = "in";
    var radius = 1.2 + (position * 0.22) //écart
    var innerRad = radius + 0.2//Largeur
    //var innerBad = 1.1 + (position * 0.22)
    //var radius = radius + 0.2
  }else{
    orientation_line = "out";
    var radius = 1 - (position * 0.12);
    var innerRad = radius - 0.1
  }
  
  var line = {
    innerRadius: innerRad,
    outerRadius: radius,
    maxGap: 1000000,
    //direction :orientation,
    direction: orientation_line,
    fill: "true",
    strokeColor: '#272727', 
    color: randomColor(), 
    axes: [
    {
      spacing: 100000000000000000000000000000000000,
      //spacing: 0.001,
      thickness: 1,
      color: '#666666'
    }]
  }
  return line
}
function lineScatterConfig(position,orientation){
  if(orientation == "out"){
    var radius = 1.20 + (position * 0.3) //écart
    var innerRad = radius + 0.2//Largeur
  }else{
    var radius = 1 - (position * 0.12);
    var innerRad = radius - 0.1
  }
  var line = {
    innerRadius: innerRad,
    outerRadius: radius,
    maxGap: 1000000,
    direction :orientation,
    fill: false,
    strokeWidth: 0,
    tooltipContent: function (d, i) {
      return `${d.block_id}:${Math.round(d.position)} > ${d.value}`
    }
  }
  return line
}
function highlightConfig(){
  var highlight = {
    innerRadius: width - 100,
    outerRadius: width - 95,
    opacity: 0.3,
    color: function (d) {
      return gieStainColor[d.gieStain]
    },
    tooltipContent: function (d) {
      return d.name
    }
  }
  return highlight;
}
function scatterConfig(position,orientation){
  if(orientation == "out"){
    var radius = 1.25 + (position * 0.4)
    var innerRad = radius + 0.2
  }else{
    var radius = 1 - (position * 0.9);
    var innerRad = radius - 0.1
  }
  var scatter = {
    innerRadius: innerRad,
    outerRadius: radius,
    color: function (d) {
      if (d.value > 0.006) { return '#4caf50' }
        if (d.value < 0.002) { return '#f44336' }
          return '#d3d3d3'
      },
      strokeColor: 'grey',
      strokeWidth: 1,
      shape: 'circle',
      size: 14,
      axes: [
      {
        spacing: 100000000000000000000000000000000000,
        thickness: 1,
        color: '#000000',
        opacity: 0.7
      }],
      tooltipContent: function (d, i) {
        return `${d.block_id}:${Math.round(d.position)} > ${d.value}`
      }
    }
    return scatter;
  // 
}
//


//Var mapping part
function chordVarMapper(fileName){
  mappedVar = fileName.map(function (d) {
    return {
      source: {
        id: d.source,
        start: parseInt(d.source_start) - 2000000,
        end: parseInt(d.source_end) + 2000000},
        target: {
          id: d.target,
          start: parseInt(d.target_start) - 2000000,
          end: parseInt(d.target_end) + 2000000
        }
      }
    }
    );
  return mappedVar;
}
function heatmapVarMapper(fileName){
  var mappedVar =fileName.map(function(d) {
    return {
      block_id: d.chromosome,
      start: parseInt(d.start),
      end: parseInt(d.end),
      value: parseFloat(d.value)
    };
  });
  return mappedVar;
}
function lineVarMapper(fileName){
  var mappedVar = fileName.map(function (d) {
    return {
      block_id: d.chromosome,
      position: parseInt(d.start),
      value: d.value
    }
  });
  return mappedVar;
}
function cytobandsVarMapper(fileName){
  cytobands = fileName
  .map(function (d) {
    return {
      block_id: d.chromosome,
      start: parseInt(d.start),
      end: parseInt(d.end),
      gieStain: d.gieStain,
      name: d.name
    }
  })
  return cytobands;
}
function scatterVarMapper(fileName){
  var mappedVar = fileName.map(function (d) {
    return {
      block_id: d.chromosome,
      position: parseInt(d.start),
      value: d.value
    }
  });
  return mappedVar;
}
//

//Miscellaneous
function randomId(){
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  for( var i=0; i < 7; i++ )
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}
function randomColor(){
  var color = "#";
  var possible = "0123456789ABCDEF";
  for( var i=0; i < 6; i++ )
    color += possible.charAt(Math.floor(Math.random() * possible.length));
  return color;
}
function randomName(){
  var name = "";
  var possible = ["Aai","Adzuki","Adzumi","Adzusa","Ae","Aeri","Ageha","Ai","Aiha","Aiho","Aika","Aiki","Aiko","Aimi","Aina","Aine","Aino","Aira","Airi","Airu","Aisa","Aise","Aisha","Aito","Aiya","Aiyu","Aka","Akae","Akaho","Akaki","Akana","Akane","Akari","Akatsuki","Akeha","Akeki","Akemi","Akeno","Akeo","Akeyo","Aki","Akie","Akiha","Akiho","Akii","Akika","Akiko","Akime","Akimi","Akina","Akine","Akino","Akira","Akisa","Akiyo","Ako","Akuro","Amarante","Amaya","Ameri","Ami","Amika","Amu","Anan","Anbi","Anda","Aneko","Anji","Anju","Anka","Anmi","Anna","Anne","Anon","Anri","Anru","Ansha","Anzu","Ao","Aoba","Aoha","Aoi","Aoka","Aoki","Aomi","Aona","Aono","Aori","Aose","Aoto","Aozora","Arei","Ari","Arie","Ariha","Ariho","Arika","Arimi","Arin","Arina","Arisa","Arise","Arisu","Arufa","Aruha","Aruna","Asa","Asae","Asagi","Asahi","Asaho","Asai","Asaka","Asaki","Asako","Asami","Asana","Asao","Asara","Asari","Asayo","Asuhi","Asuka","Asumi","Atsue","Atsuka","Atsuki","Atsuko","Atsumi","Atsuna","Atsune","Atsuno","Atsusa","Atsuyo","Awana","Awano","Aya","Ayae","Ayaha","Ayahi","Ayaho","Ayai","Ayaka","Ayaki","Ayako","Ayame","Ayami","Ayamu","Ayana","Ayane","Ayano","Ayao","Ayara","Ayari","Ayasa","Ayase","Ayato","Ayayo","Ayu","Ayuka","Ayuki","Ayume","Ayumi","Ayumu","Ayuna","Ayuno","Ayuri","Ayusa","Ayuto","Azuki","Azumi","Azuna","Azusa","Benten","Biei","Chia","Chiaki","Chiaya","Chidzuki","Chidzuko","Chidzumi","Chidzuru","Chie","Chieko","Chiemi","Chieri","Chigusa","Chiharu","Chihaya","Chihiro","Chiho","Chika","Chikae","Chikage","Chikako","Chikano","Chikara","Chikaru","Chikasa","Chikashi","Chiki","Chiko","Chikoto","Chikuma","China","Chinae","Chinami","Chinari","Chinaru","Chinatsu","Chino","Chinon","Chio","Chiori","Chisa","Chisaki","Chisako","Chisane","Chisato","Chise","Chisei","Chisumi","Chitose","Chiya","Chiyeko","Chiyo","Chiyoko","Chiyomi","Chiyu","Chiyuki","Chiyumi","Chizuru","Cho","Chou","Chura","Dai","Echiko","Ehana","Eho","Ei","Eiha","Eiichi","Eika","Eiko","Eimi","Eina","Eiri","Eko","Ema","Emi","Emiho","Emika","Emiko","Emina","Emio","Emiri","Emu","En","Ena","Eo","Epo","Eran","Ere","Erei","Eren","Erena","Eri","Erika","Eriko","Erin","Erina","Eriya","Eru","Eruna","Eruru","Etsuho","Etsuki","Etsuko","Etsumi","Etsuyo","Euiko","Fua","Fubuki","Fujika","Fujiko","Fujina","Fujino","Fujisa","Fuki","Fumi","Fumie","Fumika","Fumiki","Fumiko","Fumina","Fumino","Fumiyo","Fusa","Fusae","Fusako","Fusana","Fusano","Futaba","Fuu","Fuua","Fuuga","Fuuha","Fuui","Fuuka","Fuuki","Fuuna","Fuune","Fuuno","Fuusa","Fuyu","Fuyue","Fuyuhi","Fuyuka","Fuyuko","Fuyume","Fuyumi","Fuyune","Fuyuno","Fyei","Gemmei","Gen","Gin","Ginko","Gou","Hadzuki","Haine","Haju","Hako","Hama","Hami","Hana","Hanae","Hanaha","Hanaka","Hanako","Hanami","Hanano","Hanari","Hanatsu","Haniko","Hanna","Hano","Hanon","Hanri","Hare","Haru","Harue","Haruha","Haruhi","Haruho","Harui","Haruka","Haruki","Harukichi","Haruko","Haruku","Haruma","Harume","Harumi","Harumo","Harumu","Haruna","Harune","Haruno","Haruo","Haruse","Haruyo","Hase","Hasumi","Hatsue","Hatsuho","Hatsuka","Hatsuki","Hatsuku","Hatsumi","Hatsuna","Hatsune","Hatsuno","Hatsuyo","Haya","Hayaka","Hayami","Hayane","Hayasa","Hayase","Hazumi","Hazuna","Hibiki","Hide","Hideko","Hidemi","Hideri","Hidzuki","Hiho","Hiina","Hiira","Hiiragi","Hiiro","Hiizu","Hikana","Hikari","Hikaru","Himari","Himawari","Hina","Hinagi","Hinaki","Hinako","Hinami","Hinano","Hinari","Hinata","Hinatsu","Hinayo","Hinon","Hiori","Hirari","Hiroa","Hiroe","Hiroha","Hiroka","Hiroko","Hiromi","Hiromu","Hirona","Hirone","Hirono","Hiroo","Hiroshi","Hiroyo","Hisa","Hisae","Hisaho","Hisaka","Hisaki","Hisako","Hisami","Hisana","Hisano","Hisashi","Hisato","Hisayo","Hisui","Hitoe","Hitoha","Hitoka","Hitomi","Hitomo","Hitona","Hitone","Hitono","Hitose","Hitoshi","Hitsuji","Hiyo","Hiyori","Hiyu","Hiyumi","Hodaka","Hodzumi","Hoharu","Hoki","Hona","Honami","Honatsu","Honoka","Honomi","Honon","Honone","Honori","Hoshi","Hoshie","Hoshiha","Hoshiko","Hoshimi","Hoshina","Hoshine","Hoshino","Hoshiyo","Hotaru","Hotona","Hotsumi","Houka","Hozue","Hozumi","Hozumu","Hyuu","Ibuki","Ichi","Ichie","Ichiha","Ichika","Ichimi","Ichina","Ichine","Ichino","Idzumi","Ika","Iku","Ikue","Ikuho","Ikuka","Ikuko","Ikumi","Ikuna","Ikuno","Ikuyo","Imari","Imi","Ina","Inami","Inari","Inatsu","Inori","Inoru","Inoue","Io","Ion","Iori","Ira","Irei","Iri","Irii","Iroha","Iru","Iruka","Isa","Isae","Isaki","Isako","Ise","Isuzu","Ito","Itono","Itsue","Itsuho","Itsuka","Itsuki","Itsuko","Itsumi","Itsuna","Iyo","Iyori","Izuho","Izumi","Jin","Jio","Joruri","Juai","Juan","Juchika","Jue","Juho","Juka","Juki","Jukia","Jun","Juna","June","Junka","Junko","Junmi","Junna","Juno","Junrei","Junri","Jura","Juri","Jurin","Juru","Kaai","Kadzuho","Kadzuki","Kadzumi","Kadzusa","Kae","Kaede","Kagami","Kahana","Kahane","Kaho","Kahori","Kai","Kaida","Kairi","Kaiya","Kaiyo","Kajitsu","Kaju","Kaki","Kako","Kameko","Kami","Kammi","Kammie","Kana","Kanade","Kanae","Kanaha","Kanaho","Kanako","Kaname","Kanami","Kanan","Kanana","Kanari","Kanatsu","Kanawa","Kanayo","Kane","Kaneko","Kanna","Kano","Kanoha","Kanoho","Kanoka","Kanon","Kanori","Kao","Kaon","Kaori","Kaoru","Karan","Karei","Karen","Kari","Karibu","Karin","Karina","Kasaki","Kasane","Kashi","Kasuga","Kasui","Kasumi","Kasune","Kata","Katsue","Katsuki","Katsuko","Katsumi","Kaya","Kayasa","Kayo","Kayoko","Kayou","Kayu","Kayume","Kazu","Kazuchi","Kazue","Kazuha","Kazuhi","Kazuho","Kazuka","Kazuko","Kazumi","Kazuna","Kazune","Kazuno","Kazura","Kazuri","Kazusa","Kazuwo","Kazuyo","Kei","Keiga","Keika","Keiki","Keiko","Keimi","Keina","Keino","Keiri","Keiru","Keisa","Keito","Kia","Kichi","Kichino","Kie","Kifumi","Kiharu","Kihiro","Kiho","Kii","Kiiko","Kiiro","Kika","Kiki","Kiko","Kiku","Kikue","Kikuko","Kikuno","Kikyou","Kimi","Kimie","Kimihi","Kimii","Kimika","Kimiko","Kimina","Kimino","Kimiyo","Kimiyu","Kimu","Kin","Kina","Kinami","Kinatsu","Kino","Kinoka","Kinori","Kinue","Kinuka","Kinuko","Kinumi","Kinuye","Kinuyo","Kioko","Kira","Kiran","Kirara","Kirari","Kiri","Kirika","Kiriko","Kirin","Kirina","Kirine","Kisa","Kisaki","Kisaya","Kisei","Kisha","Kishi","Kishuu","Kita","Kitsuki","Kiwa","Kiya","Kiyo","Kiyoe","Kiyoha","Kiyohi","Kiyoho","Kiyoi","Kiyoka","Kiyoko","Kiyomi","Kiyona","Kiyono","Kiyora","Kiyoshi","Kiyu","Kiyui","Kiyuki","Kiyuu","Kobato","Kochiyo","Kohaku","Kohana","Kohane","Koharu","Kohina","Koi","Koimi","Koiso","Koken","Koko","Kokoa","Kokoe","Kokoha","Kokomi","Kokona","Kokone","Kokori","Kokoro","Kokoru","Komachi","Komaki","Komiki","Komina","Komoe","Komomo","Komugi","Kona","Konami","Konan","Konana","Konatsu","Konoe","Konoha","Konoka","Konoma","Konomi","Korin","Kosato","Kosui","Kosumi","Kosumo","Kosuzu","Koto","Kotoa","Kotoe","Kotoha","Kotoho","Kotoka","Kotoki","Kotoko","Kotome","Kotomi","Kotona","Kotone","Kotono","Kotora","Kotori","Kotose","Kotowa","Kotoyo","Kou","Koue","Kouhi","Kouki","Koumi","Kouna","Koura","Kouran","Kouri","Kousei","Kouyou","Koyori","Koyuki","Koyume","Koyumi","Koyuri","Kozato","Kozue","Kozumi","Kumi","Kumiko","Kuni","Kunie","Kuniko","Kuniyo","Kuno","Kura","Kuran","Kurea","Kureha","Kurei","Kurena","Kureno","Kuri","Kuria","Kuruchi","Kurue","Kurumi","Kyara","Kyoko","Kyou","Kyouka","Kyouki","Kyouko","Kyoumi","Kyouna","Kyoune","Kyouno","Maai","Maasa","Maaya","Mabuki","Machi","Machiko","Madoha","Madoka","Mae","Maeko","Maemi","Mafumi","Mafuyu","Maha","Mahime","Mahiro","Mahiru","Maho","Mahona","Mai","Maia","Maiha","Maiho","Maika","Maiki","Maiko","Maina","Maine","Maino","Maira","Mairi","Maiya","Maka","Makana","Maki","Makie","Makiha","Makiho","Makika","Makiko","Makina","Makino","Makinu","Mako","Makoto","Mami","Mamiko","Mamori","Mana","Manae","Manaha","Manaka","Manako","Manama","Manami","Manan","Manano","Manao","Manare","Manari","Manase","Manato","Manatsu","Manaya","Mane","Mano","Manon","Mao","Maon","Maou","Mara","Mare","Marei","Mareka","Maremu","Maren","Marena","Mari","Maria","Marie","Marika","Mariko","Marin","Marina","Mario","Marisa","Marise","Mariya","Maru","Masae","Masai","Masaki","Masako","Masami","Masana","Masano","Masayo","Mashiho","Masumi","Matsu","Matsuki","Matsuko","Matsumi","Matsuri","Matsuyo","Mau","Maya","Mayaka","Mayako","Mayo","Mayoko","Mayu","Mayue","Mayui","Mayuka","Mayuki","Mayuko","Mayume","Mayumi","Mayumu","Mayuna","Mayura","Mayuri","Mayuu","Mayuzumi","Mebae","Mebuki","Megu","Meguho","Meguka","Megumi","Meguri","Mei","Meika","Meiko","Meina","Meira","Meiran","Meiri","Meiya","Memi","Memori","Mena","Meo","Meya","Meyu","Mia","Miaka","Miaki","Miako","Miasa","Miaya","Mibuki","Michi","Michie","Michiho","Michika","Michiko","Michina","Michio","Michiru","Michiyo","Midori","Midzue","Midzuho","Midzuka","Midzuki","Mie","Miei","Mieko","Mifuki","Mifuu","Mifuyu","Miha","Mihae","Mihana","Mihane","Miharu","Mihato","Mihaya","Mihayu","Mihime","Mihiro","Miho","Mihoka","Mihoko","Mihona","Mii","Miiha","Miiko","Miina","Miine","Miiru","Miju","Mika","Mikae","Mikako","Mikan","Mikana","Mikari","Mikawa","Mikayo","Miki","Mikie","Mikiho","Mikiko","Mikina","Mikino","Mikiyo","Miko","Mikoto","Miku","Mikuho","Mikuka","Miliko","Mima","Mimari","Mimi","Mimori","Mimu","Mina","Minae","Minagi","Minaha","Minaho","Minai","Minaka","Minaki","Minako","Minami","Minamo","Minao","Minari","Minase","Minato","Minatsu","Mine","Mineka","Mineki","Mineko","Mineri","Mino","Minoka","Minoki","Minon","Minori","Minoru","Mio","Mioha","Mioka","Miomi","Mion","Miora","Miori","Mioto","Miou","Mirai","Miran","Mire","Mirei","Miri","Miru","Miruka","Misa","Misaho","Misaki","Misako","Misao","Misato","Misawo","Mishuri","Misono","Misora","Misumi","Misuzu","Mito","Mitsu","Mitsue","Mitsugi","Mitsuha","Mitsuho","Mitsuka","Mitsuki","Mitsuko","Mitsumi","Mitsuna","Mitsune","Mitsuno","Mitsuyo","Miu","Miwa","Miwako","Miwo","Miya","Miyabi","Miyako","Miyano","Miyo","Miyoka","Miyoko","Miyoshi","Miyou","Miyu","Miyuho","Miyuka","Miyuki","Miyumi","Miyusa","Miyuu","Mizue","Mizuha","Mizuho","Mizuka","Mizuki","Mizumi","Mizuna","Mizune","Mizuno","Mizuo","Mizuse","Moa","Moe","Moeka","Moeko","Moemi","Moeno","Moeri","Moi","Moka","Moko","Momi","Momie","Momika","Momo","Momoa","Momoe","Momoha","Momohi","Momoka","Momoki","Momoko","Momoku","Momomi","Momona","Momone","Momono","Momoo","Momose","Momoyo","Mona","Monaka","Monami","Monan","Mone","Mono","Moori","More","Moto","Motoe","Motoi","Motoka","Motoko","Motomi","Mowa","Moyu","Moyumi","Mume","Mura","Muteki","Mutsue","Mutsuka","Mutsuki","Mutsuko","Mutsumi","Mutsuyo","Nachi","Nachie","Nachika","Nadzuki","Nae","Naemi","Naeri","Nagino","Nagisa","Naho","Nahoko","Naina","Naka","Nami","Namie","Namiha","Namiho","Namika","Namiki","Namiko","Namina","Namisa","Namiyo","Nana","Nanae","Nanaha","Nanaho","Nanaka","Nanaki","Nanako","Nanami","Nanan","Nanana","Nanane","Nanao","Nanari","Nanasa","Nanase","Nanashi","Nanato","Nanatsu","Nanaya","Nanka","Nanoha","Nanoka","Nanoko","Nanon","Nanri","Nao","Naoe","Naoha","Naoka","Naoki","Naoko","Naomi","Naon","Naora","Naori","Naren","Nari","Narika","Nariko","Narisa","Naru","Narue","Naruho","Naruka","Narumi","Nasa","Natsu","Natsue","Natsuha","Natsuho","Natsui","Natsuka","Natsuki","Natsuko","Natsume","Natsumi","Natsuna","Natsune","Natsusa","Natsuyo","Nattsu","Nau","Nawa","Naya","Nayo","Nayoko","Nayu","Nayuki","Nayume","Nayumi","Nayura","Nazumi","Nazuna","Neiro","Nemu","Nene","Nera","Neu","Nichika","Nie","Niima","Niina","Niino","Niji","Nijiha","Nijiho","Nijika","Nijina","Niki","Niko","Nina","Nire","Nirei","Nishi","Noa","Nobu","Nobue","Nobuko","Nodoka","Noeru","Noma","Nomi","Nona","Nonka","Nonno","Nono","Nonoka","Nori","Noria","Norie","Noriha","Norika","Noriko","Norina","Norino","Norisa","Norito","Noriyo","Nozomi","Nyoko","Ochiyo","Oharu","Oki","Okichi","Okiku","Omitsu","Omoi","Omoka","Ooaya","Orie","Orika","Orina","Orino","Orisa","Oto","Otoe","Otoha","Otoka","Otona","Otose","Otowa","Otsu","Otsune","Ouka","Oumi","Ouna","Ouri","Pinku","Raichi","Raicho","Raika","Raiki","Raimi","Raina","Raira","Rairi","Raisa","Raito","Raku","Rama","Rami","Ramu","Ran","Rana","Ranan","Ranna","Rara","Rasa","Rea","Reeko","Reemi","Reen","Reena","Reho","Rei","Reia","Reiha","Reiho","Reika","Reiki","Reiko","Reimi","Reina","Reini","Reino","Reira","Reiri","Reisa","Reishi","Reiya","Rema","Remi","Remon","Ren","Rena","Reno","Renon","Reo","Reon","Rera","Reri","Ria","Rian","Ridzu","Ridzuki","Rie","Rieko","Riemi","Riha","Riharu","Riho","Rii","Riju","Rika","Rikako","Rikana","Rikei","Riki","Rikka","Riko","Riku","Rikuka","Rima","Rimi","Rin","Rina","Rinako","Rine","Ringo","Rini","Rinka","Rinna","Rinne","Rino","Rinon","Rio","Rion","Riona","Riori","Rira","Riran","Rirei","Riri","Riria","Ririka","Ririna","Riru","Risa","Risaki","Risako","Risana","Risato","Rise","Risuzu","Rito","Ritsu","Ritsue","Ritsuho","Ritsuki","Ritsuko","Ritsuna","Ritsuno","Riu","Riya","Riyo","Riyu","Riyuu","Riza","Rizu","Rizumu","Romi","Rua","Rubi","Rui","Ruina","Ruiri","Ruka","Ruki","Rumi","Rumiko","Rumoi","Runa","Runmi","Runo","Ruo","Rura","Ruri","Rurika","Ruriko","Ruru","Ruuna","Ruuru","Ryoko","Ryou","Ryoubi","Ryouga","Ryouha","Ryouka","Ryouko","Ryoumi","Ryouna","Ryuubi","Ryuuka","Ryuumi","Ryuuri","Saa","Saaki","Saara","Saari","Saaya","Sachi","Sachie","Sachiho","Sachika","Sachiko","Sachimi","Sachina","Sachino","Sachio","Sachiwo","Sachiyo","Sada","Sadako","Sae","Saeka","Saeko","Saemi","Saera","Saeri","Saharu","Sahi","Saho","Sahoko","Sahori","Sai","Saiha","Saiju","Saika","Saimi","Saira","Sairi","Saisha","Saito","Saka","Sakae","Sakaki","Sakamae","Saki","Sakie","Sakiha","Sakiho","Sakika","Sakiko","Sakimi","Sakimo","Sakina","Sakino","Sakira","Sakisa","Sakiyo","Saku","Sakue","Sakuko","Sakumi","Sakuna","Sakuno","Sakura","Sakurako","Sakuri","Sakuro","Sama","Samasa","Sami","San","Sana","Sanae","Sanako","Sanami","Sanatsu","Sane","Sango","Sano","Sao","Saori","Sara","Sarana","Sarasa","Sari","Sarii","Sarina","Sasa","Sasara","Sasha","Sata","Sato","Satoe","Satoha","Satoho","Satoka","Satoko","Satoma","Satomi","Satona","Satone","Satono","Satori","Satsuka","Satsuki","Satu","Sau","Sawa","Sawae","Sawaka","Sawaki","Sawako","Sawami","Sawayo","Saya","Sayaka","Sayaki","Sayako","Sayami","Sayano","Sayo","Sayoko","Sayomi","Sayori","Sayu","Sayui","Sayuka","Sayuki","Sayumi","Sayuri","Sea","Sei","Seiga","Seiha","Seiho","Seiju","Seika","Seikai","Seiki","Seiko","Seima","Seina","Seine","Seino","Seira","Seiri","Seisa","Seiya","Seka","Seki","Sen","Sena","Senna","Senri","Seo","Sera","Serena","Seri","Seria","Serie","Serika","Serina","Serisa","Seshiru","Setsuka","Setsuko","Seu","Seya","Shidzu","Shidzue","Shidzuka","Shidzuki","Shidzuku","Shidzuru","Shie","Shiemi","Shien","Shieri","Shieru","Shige","Shigeno","Shiho","Shii","Shiimi","Shiina","Shiine","Shiino","Shika","Shiki","Shima","Shimizu","Shina","Shinju","Shinko","Shino","Shinobu","Shinon","Shio","Shioe","Shioi","Shioka","Shiokaze","Shioko","Shiomi","Shion","Shiona","Shiono","Shiora","Shiori","Shiose","Shiou","Shiraho","Shisa","Shisei","Shisumi","Shiun","Shiyono","Shiyori","Shiyou","Shiyu","Shizu","Shizue","Shizuha","Shizuho","Shizuka","Shizuki","Shizuko","Shizuku","Shizuma","Shizumi","Shizuna","Shizuno","Shizuo","Shizura","Shizuri","Shizuru","Shizusa","Shizuse","Shizuto","Shizuyo","Shoka","Shoken","Shoko","Shoon","Shouka","Shouko","Shouna","Shue","Shuho","Shuka","Shuki","Shuma","Shun","Shuna","Shunri","Shunyou","Shura","Shuri","Shusa","Shuu","Shuuha","Shuuho","Shuuka","Shuuki","Shuuko","Shuumi","Shuuna","Soeru","Sona","Sono","Sonoe","Sonoka","Sonoko","Sonomi","Sora","Souka","Soyo","Soyoka","Soyono","Suguri","Sui","Suika","Suki","Suko","Suma","Sumi","Sumie","Sumiha","Sumiho","Sumika","Sumiko","Sumina","Sumino","Sumio","Sumire","Sumiyo","Sumomo","Sunaho","Suzu","Suzue","Suzuha","Suzuho","Suzuka","Suzuki","Suzuko","Suzuma","Suzume","Suzumi","Suzuna","Suzune","Suzuno","Suzuto","Suzuyo","Tadako","Tae","Taeko","Taena","Tai","Taji","Taka","Takae","Takaha","Takako","Takami","Takana","Takane","Takara","Takase","Takayo","Tama","Tamae","Tamafune","Tamaha","Tamahi","Tamaho","Tamai","Tamaka","Tamaki","Tamami","Tamamo","Tamao","Tamara","Tamari","Tamawo","Tamayo","Tami","Tamie","Tamika","Tamiko","Tamiyo","Tanak","Taniko","Tansho","Tao","Tara","Taree","Tatsumi","Taura","Taya","Tenna","Tenri","Tenru","Terue","Teruha","Terumi","Teruna","Teruno","Teruyo","Toa","Tochika","Toka","Toki","Tokie","Tokiha","Tokiko","Tokino","Tokiri","Tokiyo","Toko","Toku","Tokuko","Tomi","Tomie","Tomiko","Tomo","Tomoa","Tomoe","Tomoha","Tomoka","Tomoki","Tomoko","Tomomi","Tomona","Tomone","Tomono","Tomoo","Tomose","Tomoyo","Tona","Tonami","Tono","Toomi","Toon","Tooru","Toshi","Toshie","Toshika","Toshiko","Toshimi","Toshino","Toshiyo","Touka","Toumi","Touna","Towa","Toya","Toyoko","Tsubame","Tsubasa","Tsue","Tsugumi","Tsuguri","Tsukasa","Tsuki","Tsukiyama","Tsukumi","Tsuneko","Tsutae","Tsutako","Tsuya","Ubuka","Ui","Uika","Ume","Umeka","Umeko","Umi","Umie","Umina","Una","Uno","Urako","Uran","Urara","Urei","Uru","Urue","Uruha","Urume","Urumi","Ururu","Usa","Usagi","Ushio","Uta","Utae","Utaha","Utaka","Utako","Utami","Utano","Utayo","Utsuki","Uyo","Waka","Wakaba","Wakae","Wakaha","Wakaho","Wakako","Wakami","Wakana","Wakano","Wakao","Wattan","Waya","Wayu","Wazuka","Yachi","Yae","Yaeko","Yaemi","Yama","Yasu","Yasue","Yasuha","Yasuho","Yasuka","Yasuki","Yasuko","Yasumi","Yasuna","Yasuno","Yasuo","Yasura","Yasuyo","Yayoi","Yayori","Yazuya","Yodo","Yoko","Yomishi","Yomogi","Yori","Yorie","Yorika","Yoriko","Yorimi","Yorina","Yoshe","Yoshi","Yoshie","Yoshiho","Yoshika","Yoshike","Yoshiki","Yoshiko","Yoshimi","Yoshina","Yoshine","Yoshino","Yoshiri","You","Youju","Youka","Youko","Youna","Yousei","Yu","Yua","Yuami","Yuan","Yuara","Yuari","Yuasa","Yuchika","Yudzuha","Yudzuki","Yudzuru","Yue","Yuei","Yufu","Yuhana","Yuhaya","Yuhiro","Yuho","Yui","Yuiga","Yuiha","Yuiho","Yuika","Yuiki","Yuiko","Yuina","Yuine","Yuiri","Yuisa","Yuka","Yukako","Yukana","Yukari","Yukayo","Yuki","Yukia","Yukie","Yukiha","Yukiho","Yukika","Yukiko","Yukimi","Yukina","Yukine","Yukino","Yukio","Yukisa","Yukise","Yukiyo","Yuko","Yuma","Yumako","Yume","Yumeha","Yumeho","Yumeka","Yumemi","Yumena","Yumeri","Yumeto","Yumi","Yumie","Yumika","Yumiko","Yumina","Yumine","Yumino","Yumio","Yumiyo","Yuna","Yune","Yuni","Yuno","Yunoka","Yunon","Yuo","Yuori","Yura","Yuri","Yuriha","Yurika","Yuriko","Yurima","Yusa","Yusana","Yusato","Yusuke","Yuto","Yutsuki","Yutsuru","Yuu","Yuua","Yuuga","Yuuha","Yuuhi","Yuuho","Yuui","Yuuka","Yuuki","Yuuko","Yuumi","Yuuna","Yuuno","Yuuri","Yuusa","Yuuwa","Yuuyu","Yuya","Yuyu","Yuzu","Yuzuha","Yuzuho","Yuzuka","Yuzuki","Yuzumi","Yuzuru","Yuzusa"];
  name += possible[(Math.floor(Math.random() * possible.length))];
  return name;
}
function addNewTrack(){
  if(id>7){
    alert("Too many items ;)")
    return null;
  }
  var trackdiv = document.getElementById("tracks_content");

  var formdiv = document.createElement('div');
  formdiv.setAttribute("class","form-horizontal");
  formdiv.setAttribute("id",getN());

  var fieldset = document.createElement("fieldset");

  var legend = document.createElement("legend");
  legend.setAttribute("id","legend"+getN());
  fieldset.appendChild(legend);

  var formgroup = document.createElement('div');
  formgroup.setAttribute("class","form-group");

  var label = document.createElement('label');
  label.setAttribute("for","name"+getN())
  label.setAttribute("class","col-lg-4 control-label");
  label.appendChild(document.createTextNode("Name"));
  var divcontent = document.createElement("div");
  divcontent.setAttribute("class","col-lg-7");

  var input = document.createElement("input");
  input.setAttribute("type","text")
  input.setAttribute("onchange","document.getElementById(\"legend"+getN()+"\").innerHTML = this.value")
  input.setAttribute("class","form-control")
  input.setAttribute("id","name"+getN())
  input.setAttribute("placeholder","Track Name");

  divcontent.appendChild(input);
  formgroup.appendChild(label);
  formgroup.appendChild(divcontent);
  fieldset.appendChild(formgroup);

  //Select creator
  formgroup = document.createElement('div');
  formgroup.setAttribute("class","form-group");
  label = document.createElement('label');
  label.setAttribute("for","select")
  label.setAttribute("class","col-lg-4 control-label");
  label.appendChild(document.createTextNode("Type"));
  divcontent = document.createElement("div");
  divcontent.setAttribute("class","col-lg-7");
  input = document.createElement("select");
  //input.setAttribute("multiple", "")
  input.setAttribute("id","selectType"+getN());
  input.setAttribute("class", "form-control");
  input.setAttribute("onchange","updateFields(this.value,\""+getN()+"\")");

  for(var i=0; i<options.length;i++){
    var option = document.createElement('option');
    option.value = options[i];
    option.text= options[i];
    if(i>4){
      var att = document.createAttribute("disabled");
      option.setAttributeNode(att);
    }
    input.appendChild(option)
  }
  divcontent.appendChild(input);
  formgroup.appendChild(label);
  formgroup.appendChild(divcontent);
  fieldset.appendChild(formgroup);

  //Data Field 
  formgroup = document.createElement('div');
  formgroup.setAttribute("class","form-group");
  label = document.createElement('label');
  label.setAttribute("for","textArea")
  label.setAttribute("class","col-lg-4 control-label");
  label.appendChild(document.createTextNode("Data"));
  divcontent = document.createElement("div");
  divcontent.setAttribute("class","col-lg-7");
  input = document.createElement("textarea");
  input.setAttribute("rows", "3");
  input.setAttribute("wrap","off");
  input.setAttribute("class", "form-control");
  input.setAttribute("id", "dataFieldArea"+getN());
  var span = document.createElement("span");
  span.setAttribute("class","help-block");
  span.setAttribute("id","help-block"+getN());
  divcontent.appendChild(input);
  divcontent.appendChild(span);
  formgroup.appendChild(label);
  formgroup.appendChild(divcontent);
  fieldset.appendChild(formgroup);

  formgroup = document.createElement('div');
  formgroup.setAttribute("class","form-group");
  formgroup.setAttribute("id","attributefield"+getN());
  fieldset.appendChild(formgroup);

  //Button Field 
  formgroup = document.createElement('div');
  formgroup.setAttribute("class","form-group");
  divcontent = document.createElement("div");
  divcontent.setAttribute("class","col-lg-7 col-lg-offset-6");
  input = document.createElement("button");
  input.setAttribute("class", "btn btn-primary ");
  input.setAttribute("onclick", "load_file(this.value)");
  input.setAttribute("id", "newLoadData"+getN());
  input.setAttribute("value",getN());
  input.appendChild(document.createTextNode("Load Data"));
  divcontent.appendChild(input);
  input = document.createElement("button");
  input.setAttribute("class", "remove_field btn btn-danger ");
  input.setAttribute("onclick",'$("#'+getN()+'").remove(); decreaseN();');
  input.appendChild(document.createTextNode("Remove Track"));
  divcontent.appendChild(input);
  // <button href="#" class="remove_field btn-danger col-lg-6 col-lg-offset-4">Remove</button>
  input = document.createElement("input");
  input.setAttribute("class", "btn btn-warning col-lg-6 col-lg-offset-4");
  input.setAttribute("type", "file");
  input.setAttribute("style", "display:none;");
  input.setAttribute("id", "fileInput"+getN());
  var par = document.createElement("h5");
  par.setAttribute("id","par"+getN());
  par.setAttribute("class"," col-lg-offset-5");

  formgroup.appendChild(divcontent);
  formgroup.appendChild(input);
  formgroup.appendChild(par);
  fieldset.appendChild(formgroup);

  formdiv.appendChild(fieldset);
  trackdiv.appendChild(formdiv);
  updateN();
  if(!$("#loadCircos").is(":visible")){
    $("#loadCircos").fadeIn('slow');
  }
}
function updateN(){
  id++;
}
function decreaseN(){
  id--;
}
function getN(){

  return id;
}
//

//IN PROGRESS 
function load_file(value){
  $("#fileInput"+value).show();
  var fileInput = document.getElementById('fileInput'+value);
  fileInput.addEventListener('change', function(e) {
    var file = fileInput.files[0];
    var reader = new FileReader();
    reader.onload = function(e) {
     $('#newLoadData'+value).fadeOut('slow');
     $('#fileInput'+value).fadeOut('slow');
     $("#dataFieldArea"+value).text(reader.result);
     $('#par'+value).text("Loaded File : "+file.name);
   };
   reader.readAsText(file);  
 });   
}
function load_circos(){
  document.getElementById("lineChart").innerHTML = ""
  circos = new Circos({
    container: '#lineChart', 
    width: width,
    height: width
  })
  circos.layout(chromosomeParser($("#dataFieldAreaC").val()),layoutConfig(10000000,'Mb'));
  var scattercpt=1;
  var representationcpt = 0;
  var circosOrientation = "in";
  for(var i = 0; i < id; i++){
    var selected = $('#selectType'+i).val();
    if(selected =="Chords"){
      circosOrientation = "out";
    }
  }
  for(var i = 0; i < id; i++){
    var selected = $('#selectType'+i).val();
    var content  = $('#dataFieldArea'+i).val();
    switch(selected){
      case "HeatMap":
      var data = heatmapParser(content)
      if(data.length>1){
        for(var r = 0; r<data.length;r++){
          circos.heatmap(randomId(),heatmapVarMapper(data[r]),heatmapConfig((representationcpt+r),"YlOrRd",circosOrientation));
        }
        representationcpt++;
      }else{
        circos.heatmap(randomId(),heatmapVarMapper(data[0]),heatmapConfig(representationcpt,"YlOrRd",circosOrientation));
        representationcpt++;
      }
      break;
      case "Line":
      var data = lineParser(content);
      if(data.length>1){
        for(var r = 0; r<data.length;r++){
          circos.line(randomId(), lineVarMapper(data[r]),lineConfig(representationcpt,circosOrientation));
          circos.scatter(randomId(), lineVarMapper(data[r]),lineScatterConfig(representationcpt,circosOrientation));
          lineScatterConfig
        }
        representationcpt++;
      }
      else{
        circos.line(randomId(), lineVarMapper(data[0]),lineConfig(representationcpt,circosOrientation));
        circos.scatter(randomId(), lineVarMapper(data[0]),lineScatterConfig(representationcpt,circosOrientation));
        representationcpt++;
      }
      break;
      case "Chords":
      circos.chords(randomId(),chordVarMapper(chordsParser(content)),chordConfig("1"));
      if(inversions.length>0){
        circos.chords(randomId(),chordVarMapper(inversions),chordConfig("2"));
        inversions = [];
      }
      break;
      case "HighLight":
      circos.highlight(randomId(), cytobandsVarMapper(cytobandsParser(content)),highlightConfig())
      break;
      case "Histogram":
      break;
      case "Scatter":
      if(circosOrientation == "out"){
        circos.scatter(randomId(), scatterVarMapper(scatterParser(content)),scatterConfig(representationcpt,circosOrientation));
        representationcpt++;
      }
      else{
        circos.scatter(randomId(), scatterVarMapper(scatterParser(content)),scatterConfig(scattercpt,circosOrientation));
      }
      scattercpt++;
      break;
      case "Stack":
      break;
      case "Text":
      break;
    } 
  }
  circos.render();

  $(function() {
    panZoomInstance = svgPanZoom('#svgdemo', {
      zoomEnabled: true,
      controlIconsEnabled: true,
      fit: true,
      center: true,
      minZoom: 0.1
    });

  // zoom out
  panZoomInstance.zoom(1)
})
}
function load_test(){
  $('#newTrackButton').click();
  $('#newTrackButton').click();

  $('#selectType0').val("Line").change();
  $('#selectType3').val("Chords").change();

  $("#dataFieldAreaC").text("chr1 38193400\nchr2 54522928\nchr3 32030951\nchr4 28191985\nchr5 29137935\nchr6 37293965\nchr7 29833120\nchr8 31585744\nchr9 22352177\nchr10 27624748\nchr11 33540656");
   $("#dataFieldArea0").text("chr1 200000 472\nchr1 400000 351\nchr1 600000 138\nchr1 800000 322\nchr1 1000000 173\nchr1 1200000 114\nchr1 1400000 249\nchr1 1600000 379\nchr1 1800000 323\nchr1 2000000 221\nchr1 2200000 470\nchr1 2400000 207\nchr1 2600000 248\nchr1 2800000 153\nchr1 3000000 195\nchr1 3200000 463\nchr1 3400000 226\nchr1 3600000 61\nchr1 3800000 275\nchr1 4000000 168\nchr1 4200000 187\nchr1 4400000 249\nchr1 4600000 281\nchr1 4800000 172\nchr1 5000000 142\nchr1 5200000 102\nchr1 5400000 81\nchr1 5600000 395\nchr1 5800000 70\nchr1 6000000 24\nchr1 6200000 415\nchr1 6400000 4\nchr1 6600000 65\nchr1 6800000 66\nchr1 7000000 145\nchr1 7200000 113\nchr1 7400000 153\nchr1 7600000 64\nchr1 7800000 9\nchr1 8000000 273\nchr1 8200000 4\nchr1 8400000 128\nchr1 8600000 38\nchr1 8800000 30\nchr1 9000000 21\nchr1 9200000 47\nchr1 9400000 10\nchr1 9600000 33\nchr1 9800000 144\nchr1 10000000 179\nchr1 10200000 13\nchr1 10400000 43\nchr1 10600000 47\nchr1 10800000 56\nchr1 11000000 20\nchr1 11200000 53\nchr1 11400000 48\nchr1 11600000 208\nchr1 11800000 2\nchr1 12000000 0\nchr1 12200000 0\nchr1 12400000 0\nchr1 12600000 16\nchr1 12800000 14\nchr1 13000000 0\nchr1 13200000 49\nchr1 13400000 69\nchr1 13600000 10\nchr1 13800000 10\nchr1 14000000 12\nchr1 14200000 38\nchr1 14400000 35\nchr1 14600000 24\nchr1 14800000 10\nchr1 15000000 0\nchr1 15200000 10\nchr1 15400000 0\nchr1 15600000 52\nchr1 15800000 49\nchr1 16000000 0\nchr1 16200000 29\nchr1 16400000 18\nchr1 16600000 15\nchr1 16800000 26\nchr1 17000000 42\nchr1 17200000 15\nchr1 17400000 11\nchr1 17600000 15\nchr1 17800000 42\nchr1 18000000 125\nchr1 18200000 27\nchr1 18400000 15\nchr1 18600000 26\nchr1 18800000 50\nchr1 19000000 5\nchr1 19200000 0\nchr1 19400000 0\nchr1 19600000 27\nchr1 19800000 206\nchr1 20000000 330\nchr1 20200000 156\nchr1 20400000 53\nchr1 20600000 15\nchr1 20800000 83\nchr1 21000000 28\nchr1 21200000 35\nchr1 21400000 13\nchr1 21600000 54\nchr1 21800000 136\nchr1 22000000 81\nchr1 22200000 105\nchr1 22400000 98\nchr1 22600000 154\nchr1 22800000 113\nchr1 23000000 153\nchr1 23200000 83\nchr1 23400000 85\nchr1 23600000 184\nchr1 23800000 308\nchr1 24000000 115\nchr1 24200000 242\nchr1 24400000 98\nchr1 24600000 7\nchr1 24800000 83\nchr1 25000000 53\nchr1 25200000 488\nchr1 25400000 164\nchr1 25600000 361\nchr1 25800000 112\nchr1 26000000 174\nchr1 26200000 348\nchr1 26400000 1099\nchr1 26600000 940\nchr1 26800000 217\nchr1 27000000 302\nchr1 27200000 270\nchr1 27400000 173\nchr1 27600000 232\nchr1 27800000 188\nchr1 28000000 162\nchr1 28200000 130\nchr1 28400000 335\nchr1 28600000 329\nchr1 28800000 239\nchr1 29000000 278\nchr1 29200000 299\nchr1 29400000 252\nchr1 29600000 321\nchr1 29800000 193\nchr1 30000000 231\nchr1 30200000 212\nchr1 30400000 402\nchr1 30600000 222\nchr1 30800000 233\nchr1 31000000 339\nchr1 31200000 244\nchr1 31400000 255\nchr1 31600000 384\nchr1 31800000 338\nchr1 32000000 325\nchr1 32200000 435\nchr1 32400000 353\nchr1 32600000 477\nchr1 32800000 298\nchr1 33000000 381\nchr1 33200000 338\nchr1 33400000 233\nchr1 33600000 311\nchr1 33800000 554\nchr1 34000000 330\nchr1 34200000 340\nchr1 34400000 413\nchr1 34600000 385\nchr1 34800000 277\nchr1 35000000 344\nchr1 35200000 586\nchr1 35400000 324\nchr1 35600000 284\nchr1 35800000 334\nchr1 36000000 223\nchr1 36200000 375\nchr1 36400000 467\nchr1 36600000 402\nchr1 36800000 343\nchr1 37000000 329\nchr1 37200000 435\nchr1 37400000 371\nchr1 37600000 373\nchr1 37800000 373\nchr1 38000000 465\nchr1 38200000 370\nchr10 200000 384\nchr10 400000 500\nchr10 600000 319\nchr10 800000 348\nchr10 1000000 375\nchr10 1200000 438\nchr10 1400000 330\nchr10 1600000 414\nchr10 1800000 332\nchr10 2000000 325\nchr10 2200000 338\nchr10 2400000 486\nchr10 2600000 356\nchr10 2800000 378\nchr10 3000000 317\nchr10 3200000 287\nchr10 3400000 267\nchr10 3600000 274\nchr10 3800000 387\nchr10 4000000 232\nchr10 4200000 264\nchr10 4400000 359\nchr10 4600000 224\nchr10 4800000 197\nchr10 5000000 257\nchr10 5200000 357\nchr10 5400000 183\nchr10 5600000 236\nchr10 5800000 123\nchr10 6000000 275\nchr10 6200000 306\nchr10 6400000 279\nchr10 6600000 138\nchr10 6800000 210\nchr10 7000000 239\nchr10 7200000 189\nchr10 7400000 125\nchr10 7600000 123\nchr10 7800000 414\nchr10 8000000 171\nchr10 8200000 143\nchr10 8400000 374\nchr10 8600000 291\nchr10 8800000 390\nchr10 9000000 117\nchr10 9200000 53\nchr10 9400000 74\nchr10 9600000 132\nchr10 9800000 163\nchr10 10000000 147\nchr10 10200000 164\nchr10 10400000 36\nchr10 10600000 343\nchr10 10800000 574\nchr10 11000000 14\nchr10 11200000 78\nchr10 11400000 108\nchr10 11600000 32\nchr10 11800000 156\nchr10 12000000 0\nchr10 12200000 0\nchr10 12400000 41\nchr10 12600000 89\nchr10 12800000 16\nchr10 13000000 15\nchr10 13200000 41\nchr10 13400000 26\nchr10 13600000 0\nchr10 13800000 43\nchr10 14000000 0\nchr10 14200000 138\nchr10 14400000 56\nchr10 14600000 66\nchr10 14800000 47\nchr10 15000000 0\nchr10 15200000 7\nchr10 15400000 18\nchr10 15600000 44\nchr10 15800000 17\nchr10 16000000 52\nchr10 16200000 15\nchr10 16400000 124\nchr10 16600000 56\nchr10 16800000 0\nchr10 17000000 4\nchr10 17200000 17\nchr10 17400000 147\nchr10 17600000 0\nchr10 17800000 84\nchr10 18000000 85\nchr10 18200000 87\nchr10 18400000 34\nchr10 18600000 28\nchr10 18800000 2\nchr10 19000000 19\nchr10 19200000 149\nchr10 19400000 106\nchr10 19600000 104\nchr10 19800000 68\nchr10 20000000 0\nchr10 20200000 16\nchr10 20400000 230\nchr10 20600000 22\nchr10 20800000 124\nchr10 21000000 120\nchr10 21200000 76\nchr10 21400000 32\nchr10 21600000 166\nchr10 21800000 100\nchr10 22000000 117\nchr10 22200000 354\nchr10 22400000 357\nchr10 22600000 227\nchr10 22800000 438\nchr10 23000000 97\nchr10 23200000 299\nchr10 23400000 75\nchr10 23600000 141\nchr10 23800000 0\nchr10 24000000 62\nchr10 24200000 193\nchr10 24400000 381\nchr10 24600000 518\nchr10 24800000 165\nchr10 25000000 192\nchr10 25200000 191\nchr10 25400000 128\nchr10 25600000 208\nchr10 25800000 49\nchr10 26000000 427\nchr10 26200000 247\nchr10 26400000 406\nchr10 26600000 167\nchr10 26800000 272\nchr10 27000000 308\nchr10 27200000 290\nchr10 27400000 315\nchr10 27600000 123\nchr10 27800000 15\nchr11 200000 102\nchr11 400000 85\nchr11 600000 188\nchr11 800000 195\nchr11 1000000 195\nchr11 1200000 65\nchr11 1400000 28\nchr11 1600000 56\nchr11 1800000 165\nchr11 2000000 17\nchr11 2200000 72\nchr11 2400000 78\nchr11 2600000 37\nchr11 2800000 53\nchr11 3000000 427\nchr11 3200000 29\nchr11 3400000 0\nchr11 3600000 2\nchr11 3800000 149\nchr11 4000000 96\nchr11 4200000 44\nchr11 4400000 2\nchr11 4600000 144\nchr11 4800000 81\nchr11 5000000 127\nchr11 5200000 225\nchr11 5400000 311\nchr11 5600000 84\nchr11 5800000 173\nchr11 6000000 290\nchr11 6200000 313\nchr11 6400000 710\nchr11 6600000 182\nchr11 6800000 98\nchr11 7000000 84\nchr11 7200000 87\nchr11 7400000 22\nchr11 7600000 78\nchr11 7800000 5\nchr11 8000000 133\nchr11 8200000 5\nchr11 8400000 0\nchr11 8600000 6\nchr11 8800000 212\nchr11 9000000 152\nchr11 9200000 1\nchr11 9400000 12\nchr11 9600000 0\nchr11 9800000 147\nchr11 10000000 141\nchr11 10200000 103\nchr11 10400000 4\nchr11 10600000 13\nchr11 10800000 113\nchr11 11000000 127\nchr11 11200000 283\nchr11 11400000 105\nchr11 11600000 111\nchr11 11800000 147\nchr11 12000000 225\nchr11 12200000 59\nchr11 12400000 170\nchr11 12600000 181\nchr11 12800000 0\nchr11 13000000 31\nchr11 13200000 1\nchr11 13400000 8\nchr11 13600000 0\nchr11 13800000 0\nchr11 14000000 0\nchr11 14200000 8\nchr11 14400000 84\nchr11 14600000 14\nchr11 14800000 1\nchr11 15000000 23\nchr11 15200000 17\nchr11 15400000 2\nchr11 15600000 32\nchr11 15800000 205\nchr11 16000000 188\nchr11 16200000 81\nchr11 16400000 405\nchr11 16600000 60\nchr11 16800000 193\nchr11 17000000 64\nchr11 17200000 69\nchr11 17400000 3\nchr11 17600000 151\nchr11 17800000 162\nchr11 18000000 3\nchr11 18200000 65\nchr11 18400000 118\nchr11 18600000 98\nchr11 18800000 48\nchr11 19000000 8\nchr11 19200000 71\nchr11 19400000 153\nchr11 19600000 15\nchr11 19800000 108\nchr11 20000000 376\nchr11 20200000 297\nchr11 20400000 268\nchr11 20600000 83\nchr11 20800000 282\nchr11 21000000 464\nchr11 21200000 501\nchr11 21400000 257\nchr11 21600000 129\nchr11 21800000 119\nchr11 22000000 184\nchr11 22200000 28\nchr11 22400000 377\nchr11 22600000 186\nchr11 22800000 202\nchr11 23000000 191\nchr11 23200000 514\nchr11 23400000 838\nchr11 23600000 694\nchr11 23800000 240\nchr11 24000000 649\nchr11 24200000 759\nchr11 24400000 319\nchr11 24600000 152\nchr11 24800000 327\nchr11 25000000 96\nchr11 25200000 334\nchr11 25400000 159\nchr11 25600000 174\nchr11 25800000 106\nchr11 26000000 321\nchr11 26200000 233\nchr11 26400000 428\nchr11 26600000 228\nchr11 26800000 247\nchr11 27000000 551\nchr11 27200000 438\nchr11 27400000 426\nchr11 27600000 167\nchr11 27800000 245\nchr11 28000000 256\nchr11 28200000 314\nchr11 28400000 263\nchr11 28600000 388\nchr11 28800000 476\nchr11 29000000 448\nchr11 29200000 412\nchr11 29400000 378\nchr11 29600000 349\nchr11 29800000 223\nchr11 30000000 230\nchr11 30200000 407\nchr11 30400000 263\nchr11 30600000 279\nchr11 30800000 424\nchr11 31000000 320\nchr11 31200000 317\nchr11 31400000 304\nchr11 31600000 284\nchr11 31800000 329\nchr11 32000000 255\nchr11 32200000 315\nchr11 32400000 381\nchr11 32600000 485\nchr11 32800000 423\nchr11 33000000 194\nchr11 33200000 133\nchr11 33400000 222\nchr11 33600000 81\nchr2 200000 313\nchr2 400000 431\nchr2 600000 308\nchr2 800000 233\nchr2 1000000 339\nchr2 1200000 379\nchr2 1400000 494\nchr2 1600000 293\nchr2 1800000 314\nchr2 2000000 355\nchr2 2200000 415\nchr2 2400000 326\nchr2 2600000 447\nchr2 2800000 362\nchr2 3000000 403\nchr2 3200000 531\nchr2 3400000 379\nchr2 3600000 388\nchr2 3800000 405\nchr2 4000000 222\nchr2 4200000 399\nchr2 4400000 388\nchr2 4600000 388\nchr2 4800000 342\nchr2 5000000 308\nchr2 5200000 408\nchr2 5400000 318\nchr2 5600000 316\nchr2 5800000 266\nchr2 6000000 219\nchr2 6200000 359\nchr2 6400000 430\nchr2 6600000 642\nchr2 6800000 369\nchr2 7000000 316\nchr2 7200000 457\nchr2 7400000 468\nchr2 7600000 380\nchr2 7800000 256\nchr2 8000000 378\nchr2 8200000 473\nchr2 8400000 1131\nchr2 8600000 275\nchr2 8800000 320\nchr2 9000000 320\nchr2 9200000 494\nchr2 9400000 250\nchr2 9600000 334\nchr2 9800000 121\nchr2 10000000 310\nchr2 10200000 267\nchr2 10400000 140\nchr2 10600000 178\nchr2 10800000 255\nchr2 11000000 185\nchr2 11200000 160\nchr2 11400000 474\nchr2 11600000 254\nchr2 11800000 225\nchr2 12000000 197\nchr2 12200000 337\nchr2 12400000 162\nchr2 12600000 313\nchr2 12800000 163\nchr2 13000000 617\nchr2 13200000 430\nchr2 13400000 247\nchr2 13600000 213\nchr2 13800000 236\nchr2 14000000 232\nchr2 14200000 114\nchr2 14400000 148\nchr2 14600000 173\nchr2 14800000 142\nchr2 15000000 210\nchr2 15200000 293\nchr2 15400000 413\nchr2 15600000 279\nchr2 15800000 238\nchr2 16000000 201\nchr2 16200000 363\nchr2 16400000 332\nchr2 16600000 362\nchr2 16800000 404\nchr2 17000000 312\nchr2 17200000 257\nchr2 17400000 401\nchr2 17600000 321\nchr2 17800000 343\nchr2 18000000 259\nchr2 18200000 359\nchr2 18400000 380\nchr2 18600000 244\nchr2 18800000 285\nchr2 19000000 403\nchr2 19200000 296\nchr2 19400000 367\nchr2 19600000 224\nchr2 19800000 402\nchr2 20000000 389\nchr2 20200000 332\nchr2 20400000 328\nchr2 20600000 357\nchr2 20800000 346\nchr2 21000000 340\nchr2 21200000 410\nchr2 21400000 288\nchr2 21600000 249\nchr2 21800000 120\nchr2 22000000 156\nchr2 22200000 139\nchr2 22400000 205\nchr2 22600000 156\nchr2 22800000 350\nchr2 23000000 273\nchr2 23200000 268\nchr2 23400000 149\nchr2 23600000 112\nchr2 23800000 87\nchr2 24000000 246\nchr2 24200000 740\nchr2 24400000 270\nchr2 24600000 259\nchr2 24800000 266\nchr2 25000000 68\nchr2 25200000 8\nchr2 25400000 367\nchr2 25600000 285\nchr2 25800000 116\nchr2 26000000 67\nchr2 26200000 28\nchr2 26400000 222\nchr2 26600000 189\nchr2 26800000 196\nchr2 27000000 57\nchr2 27200000 239\nchr2 27400000 193\nchr2 27600000 92\nchr2 27800000 216\nchr2 28000000 0\nchr2 28200000 7\nchr2 28400000 102\nchr2 28600000 73\nchr2 28800000 56\nchr2 29000000 46\nchr2 29200000 132\nchr2 29400000 52\nchr2 29600000 137\nchr2 29800000 2\nchr2 30000000 0\nchr2 30200000 19\nchr2 30400000 62\nchr2 30600000 153\nchr2 30800000 86\nchr2 31000000 147\nchr2 31200000 45\nchr2 31400000 18\nchr2 31600000 5\nchr2 31800000 4\nchr2 32000000 0\nchr2 32200000 13\nchr2 32400000 20\nchr2 32600000 1\nchr2 32800000 148\nchr2 33000000 125\nchr2 33200000 0\nchr2 33400000 204\nchr2 33600000 153\nchr2 33800000 467\nchr2 34000000 81\nchr2 34200000 141\nchr2 34400000 2\nchr2 34600000 32\nchr2 34800000 33\nchr2 35000000 112\nchr2 35200000 0\nchr2 35400000 0\nchr2 35600000 122\nchr2 35800000 12\nchr2 36000000 118\nchr2 36200000 0\nchr2 36400000 18\nchr2 36600000 22\nchr2 36800000 10\nchr2 37000000 26\nchr2 37200000 36\nchr2 37400000 51\nchr2 37600000 11\nchr2 37800000 5\nchr2 38000000 107\nchr2 38200000 59\nchr2 38400000 168\nchr2 38600000 80\nchr2 38800000 21\nchr2 39000000 19\nchr2 39200000 46\nchr2 39400000 114\nchr2 39600000 73\nchr2 39800000 170\nchr2 40000000 47\nchr2 40200000 30\nchr2 40400000 19\nchr2 40600000 73\nchr2 40800000 206\nchr2 41000000 38\nchr2 41200000 8\nchr2 41400000 73\nchr2 41600000 99\nchr2 41800000 42\nchr2 42000000 96\nchr2 42200000 42\nchr2 42400000 45\nchr2 42600000 8\nchr2 42800000 102\nchr2 43000000 0\nchr2 43200000 112\nchr2 43400000 117\nchr2 43600000 170\nchr2 43800000 117\nchr2 44000000 232\nchr2 44200000 3\nchr2 44400000 235\nchr2 44600000 91\nchr2 44800000 29\nchr2 45000000 162\nchr2 45200000 88\nchr2 45400000 240\nchr2 45600000 36\nchr2 45800000 343\nchr2 46000000 233\nchr2 46200000 172\nchr2 46400000 104\nchr2 46600000 132\nchr2 46800000 120\nchr2 47000000 99\nchr2 47200000 85\nchr2 47400000 179\nchr2 47600000 148\nchr2 47800000 137\nchr2 48000000 415\nchr2 48200000 139\nchr2 48400000 225\nchr2 48600000 254\nchr2 48800000 183\nchr2 49000000 166\nchr2 49200000 147\nchr2 49400000 103\nchr2 49600000 86\nchr2 49800000 149\nchr2 50000000 244\nchr2 50200000 174\nchr2 50400000 136\nchr2 50600000 143\nchr2 50800000 42\nchr2 51000000 19\nchr2 51200000 146\nchr2 51400000 339\nchr2 51600000 365\nchr2 51800000 318\nchr2 52000000 363\nchr2 52200000 163\nchr2 52400000 139\nchr2 52600000 330\nchr2 52800000 278\nchr2 53000000 300\nchr2 53200000 298\nchr2 53400000 274\nchr2 53600000 329\nchr2 53800000 330\nchr2 54000000 457\nchr2 54200000 379\nchr2 54400000 201\nchr2 54600000 119\nchr3 200000 566\nchr3 400000 397\nchr3 600000 287\nchr3 800000 295\nchr3 1000000 356\nchr3 1200000 437\nchr3 1400000 420\nchr3 1600000 227\nchr3 1800000 393\nchr3 2000000 363\nchr3 2200000 402\nchr3 2400000 306\nchr3 2600000 225\nchr3 2800000 268\nchr3 3000000 478\nchr3 3200000 339\nchr3 3400000 255\nchr3 3600000 448\nchr3 3800000 605\nchr3 4000000 410\nchr3 4200000 188\nchr3 4400000 277\nchr3 4600000 230\nchr3 4800000 297\nchr3 5000000 291\nchr3 5200000 354\nchr3 5400000 620\nchr3 5600000 293\nchr3 5800000 546\nchr3 6000000 221\nchr3 6200000 288\nchr3 6400000 240\nchr3 6600000 368\nchr3 6800000 50\nchr3 7000000 330\nchr3 7200000 194\nchr3 7400000 353\nchr3 7600000 157\nchr3 7800000 319\nchr3 8000000 731\nchr3 8200000 375\nchr3 8400000 113\nchr3 8600000 202\nchr3 8800000 637\nchr3 9000000 141\nchr3 9200000 11\nchr3 9400000 42\nchr3 9600000 87\nchr3 9800000 5\nchr3 10000000 74\nchr3 10200000 0\nchr3 10400000 8\nchr3 10600000 414\nchr3 10800000 261\nchr3 11000000 316\nchr3 11200000 0\nchr3 11400000 5\nchr3 11600000 17\nchr3 11800000 82\nchr3 12000000 508\nchr3 12200000 143\nchr3 12400000 559\nchr3 12600000 24\nchr3 12800000 199\nchr3 13000000 115\nchr3 13200000 258\nchr3 13400000 276\nchr3 13600000 231\nchr3 13800000 110\nchr3 14000000 319\nchr3 14200000 205\nchr3 14400000 305\nchr3 14600000 79\nchr3 14800000 7\nchr3 15000000 3\nchr3 15200000 143\nchr3 15400000 63\nchr3 15600000 206\nchr3 15800000 128\nchr3 16000000 107\nchr3 16200000 14\nchr3 16400000 61\nchr3 16600000 37\nchr3 16800000 14\nchr3 17000000 220\nchr3 17200000 557\nchr3 17400000 460\nchr3 17600000 239\nchr3 17800000 2\nchr3 18000000 67\nchr3 18200000 0\nchr3 18400000 15\nchr3 18600000 146\nchr3 18800000 32\nchr3 19000000 24\nchr3 19200000 16\nchr3 19400000 16\nchr3 19600000 17\nchr3 19800000 25\nchr3 20000000 23\nchr3 20200000 12\nchr3 20400000 8\nchr3 20600000 0\nchr3 20800000 0\nchr3 21000000 39\nchr3 21200000 123\nchr3 21400000 111\nchr3 21600000 102\nchr3 21800000 240\nchr3 22000000 247\nchr3 22200000 383\nchr3 22400000 264\nchr3 22600000 25\nchr3 22800000 370\nchr3 23000000 625\nchr3 23200000 73\nchr3 23400000 147\nchr3 23600000 35\nchr3 23800000 15\nchr3 24000000 15\nchr3 24200000 66\nchr3 24400000 11\nchr3 24600000 50\nchr3 24800000 0\nchr3 25000000 0\nchr3 25200000 0\nchr3 25400000 31\nchr3 25600000 248\nchr3 25800000 196\nchr3 26000000 96\nchr3 26200000 27\nchr3 26400000 149\nchr3 26600000 71\nchr3 26800000 46\nchr3 27000000 386\nchr3 27200000 452\nchr3 27400000 43\nchr3 27600000 245\nchr3 27800000 471\nchr3 28000000 69\nchr3 28200000 53\nchr3 28400000 198\nchr3 28600000 22\nchr3 28800000 139\nchr3 29000000 1011\nchr3 29200000 996\nchr3 29400000 851\nchr3 29600000 909\nchr3 29800000 395\nchr3 30000000 225\nchr3 30200000 40\nchr3 30400000 154\nchr3 30600000 234\nchr3 30800000 237\nchr3 31000000 537\nchr3 31200000 177\nchr3 31400000 177\nchr3 31600000 253\nchr3 31800000 427\nchr3 32000000 628\nchr3 32200000 90\nchr4 200000 359\nchr4 400000 408\nchr4 600000 470\nchr4 800000 385\nchr4 1000000 292\nchr4 1200000 273\nchr4 1400000 526\nchr4 1600000 377\nchr4 1800000 285\nchr4 2000000 325\nchr4 2200000 333\nchr4 2400000 355\nchr4 2600000 408\nchr4 2800000 298\nchr4 3000000 322\nchr4 3200000 382\nchr4 3400000 316\nchr4 3600000 357\nchr4 3800000 284\nchr4 4000000 316\nchr4 4200000 425\nchr4 4400000 287\nchr4 4600000 183\nchr4 4800000 443\nchr4 5000000 372\nchr4 5200000 367\nchr4 5400000 539\nchr4 5600000 167\nchr4 5800000 396\nchr4 6000000 202\nchr4 6200000 433\nchr4 6400000 104\nchr4 6600000 516\nchr4 6800000 282\nchr4 7000000 275\nchr4 7200000 348\nchr4 7400000 420\nchr4 7600000 214\nchr4 7800000 242\nchr4 8000000 167\nchr4 8200000 202\nchr4 8400000 79\nchr4 8600000 0\nchr4 8800000 14\nchr4 9000000 185\nchr4 9200000 189\nchr4 9400000 271\nchr4 9600000 149\nchr4 9800000 459\nchr4 10000000 100\nchr4 10200000 212\nchr4 10400000 242\nchr4 10600000 3\nchr4 10800000 20\nchr4 11000000 0\nchr4 11200000 290\nchr4 11400000 55\nchr4 11600000 220\nchr4 11800000 0\nchr4 12000000 16\nchr4 12200000 324\nchr4 12400000 356\nchr4 12600000 220\nchr4 12800000 668\nchr4 13000000 279\nchr4 13200000 215\nchr4 13400000 219\nchr4 13600000 298\nchr4 13800000 213\nchr4 14000000 367\nchr4 14200000 87\nchr4 14400000 52\nchr4 14600000 92\nchr4 14800000 174\nchr4 15000000 43\nchr4 15200000 58\nchr4 15400000 107\nchr4 15600000 35\nchr4 15800000 82\nchr4 16000000 16\nchr4 16200000 12\nchr4 16400000 56\nchr4 16600000 0\nchr4 16800000 19\nchr4 17000000 32\nchr4 17200000 141\nchr4 17400000 65\nchr4 17600000 296\nchr4 17800000 40\nchr4 18000000 131\nchr4 18200000 68\nchr4 18400000 14\nchr4 18600000 16\nchr4 18800000 7\nchr4 19000000 57\nchr4 19200000 63\nchr4 19400000 287\nchr4 19600000 24\nchr4 19800000 223\nchr4 20000000 170\nchr4 20200000 229\nchr4 20400000 159\nchr4 20600000 113\nchr4 20800000 29\nchr4 21000000 13\nchr4 21200000 16\nchr4 21400000 220\nchr4 21600000 173\nchr4 21800000 89\nchr4 22000000 70\nchr4 22200000 60\nchr4 22400000 185\nchr4 22600000 211\nchr4 22800000 140\nchr4 23000000 13\nchr4 23200000 78\nchr4 23400000 11\nchr4 23600000 0\nchr4 23800000 284\nchr4 24000000 12\nchr4 24200000 38\nchr4 24400000 23\nchr4 24600000 194\nchr4 24800000 196\nchr4 25000000 75\nchr4 25200000 184\nchr4 25400000 122\nchr4 25600000 132\nchr4 25800000 238\nchr4 26000000 331\nchr4 26200000 364\nchr4 26400000 31\nchr4 26600000 47\nchr4 26800000 84\nchr4 27000000 112\nchr4 27200000 72\nchr4 27400000 262\nchr4 27600000 189\nchr4 27800000 166\nchr4 28000000 10\nchr4 28200000 245\nchr5 200000 216\nchr5 400000 231\nchr5 600000 268\nchr5 800000 48\nchr5 1000000 181\nchr5 1200000 100\nchr5 1400000 35\nchr5 1600000 190\nchr5 1800000 446\nchr5 2000000 170\nchr5 2200000 200\nchr5 2400000 98\nchr5 2600000 100\nchr5 2800000 265\nchr5 3000000 129\nchr5 3200000 90\nchr5 3400000 131\nchr5 3600000 0\nchr5 3800000 52\nchr5 4000000 34\nchr5 4200000 4\nchr5 4400000 29\nchr5 4600000 0\nchr5 4800000 23\nchr5 5000000 0\nchr5 5200000 88\nchr5 5400000 66\nchr5 5600000 79\nchr5 5800000 13\nchr5 6000000 3\nchr5 6200000 18\nchr5 6400000 71\nchr5 6600000 30\nchr5 6800000 0\nchr5 7000000 21\nchr5 7200000 18\nchr5 7400000 11\nchr5 7600000 276\nchr5 7800000 152\nchr5 8000000 2\nchr5 8200000 6\nchr5 8400000 3\nchr5 8600000 17\nchr5 8800000 20\nchr5 9000000 14\nchr5 9200000 0\nchr5 9400000 0\nchr5 9600000 33\nchr5 9800000 45\nchr5 10000000 0\nchr5 10200000 294\nchr5 10400000 6\nchr5 10600000 0\nchr5 10800000 23\nchr5 11000000 89\nchr5 11200000 8\nchr5 11400000 4\nchr5 11600000 19\nchr5 11800000 38\nchr5 12000000 0\nchr5 12200000 61\nchr5 12400000 51\nchr5 12600000 16\nchr5 12800000 17\nchr5 13000000 61\nchr5 13200000 85\nchr5 13400000 17\nchr5 13600000 87\nchr5 13800000 64\nchr5 14000000 132\nchr5 14200000 114\nchr5 14400000 0\nchr5 14600000 132\nchr5 14800000 207\nchr5 15000000 85\nchr5 15200000 110\nchr5 15400000 82\nchr5 15600000 119\nchr5 15800000 0\nchr5 16000000 114\nchr5 16200000 57\nchr5 16400000 161\nchr5 16600000 0\nchr5 16800000 0\nchr5 17000000 66\nchr5 17200000 107\nchr5 17400000 0\nchr5 17600000 53\nchr5 17800000 38\nchr5 18000000 65\nchr5 18200000 182\nchr5 18400000 194\nchr5 18600000 270\nchr5 18800000 337\nchr5 19000000 137\nchr5 19200000 208\nchr5 19400000 133\nchr5 19600000 191\nchr5 19800000 818\nchr5 20000000 229\nchr5 20200000 299\nchr5 20400000 129\nchr5 20600000 139\nchr5 20800000 518\nchr5 21000000 191\nchr5 21200000 301\nchr5 21400000 1009\nchr5 21600000 271\nchr5 21800000 658\nchr5 22000000 188\nchr5 22200000 393\nchr5 22400000 582\nchr5 22600000 300\nchr5 22800000 461\nchr5 23000000 679\nchr5 23200000 382\nchr5 23400000 404\nchr5 23600000 173\nchr5 23800000 735\nchr5 24000000 265\nchr5 24200000 389\nchr5 24400000 307\nchr5 24600000 423\nchr5 24800000 324\nchr5 25000000 268\nchr5 25200000 561\nchr5 25400000 360\nchr5 25600000 416\nchr5 25800000 474\nchr5 26000000 270\nchr5 26200000 299\nchr5 26400000 290\nchr5 26600000 374\nchr5 26800000 245\nchr5 27000000 521\nchr5 27200000 395\nchr5 27400000 363\nchr5 27600000 456\nchr5 27800000 479\nchr5 28000000 495\nchr5 28200000 591\nchr5 28400000 494\nchr5 28600000 390\nchr5 28800000 317\nchr5 29000000 298\nchr5 29200000 376\nchr6 200000 305\nchr6 400000 394\nchr6 600000 341\nchr6 800000 336\nchr6 1000000 344\nchr6 1200000 309\nchr6 1400000 271\nchr6 1600000 380\nchr6 1800000 256\nchr6 2000000 272\nchr6 2200000 334\nchr6 2400000 303\nchr6 2600000 457\nchr6 2800000 465\nchr6 3000000 278\nchr6 3200000 172\nchr6 3400000 270\nchr6 3600000 226\nchr6 3800000 421\nchr6 4000000 355\nchr6 4200000 311\nchr6 4400000 224\nchr6 4600000 294\nchr6 4800000 453\nchr6 5000000 201\nchr6 5200000 252\nchr6 5400000 278\nchr6 5600000 304\nchr6 5800000 393\nchr6 6000000 422\nchr6 6200000 349\nchr6 6400000 214\nchr6 6600000 224\nchr6 6800000 352\nchr6 7000000 296\nchr6 7200000 289\nchr6 7400000 281\nchr6 7600000 243\nchr6 7800000 337\nchr6 8000000 414\nchr6 8200000 279\nchr6 8400000 281\nchr6 8600000 303\nchr6 8800000 315\nchr6 9000000 403\nchr6 9200000 363\nchr6 9400000 345\nchr6 9600000 293\nchr6 9800000 345\nchr6 10000000 302\nchr6 10200000 240\nchr6 10400000 274\nchr6 10600000 223\nchr6 10800000 180\nchr6 11000000 225\nchr6 11200000 253\nchr6 11400000 282\nchr6 11600000 319\nchr6 11800000 97\nchr6 12000000 86\nchr6 12200000 171\nchr6 12400000 351\nchr6 12600000 210\nchr6 12800000 234\nchr6 13000000 256\nchr6 13200000 264\nchr6 13400000 201\nchr6 13600000 213\nchr6 13800000 262\nchr6 14000000 313\nchr6 14200000 163\nchr6 14400000 519\nchr6 14600000 119\nchr6 14800000 131\nchr6 15000000 241\nchr6 15200000 318\nchr6 15400000 129\nchr6 15600000 448\nchr6 15800000 125\nchr6 16000000 102\nchr6 16200000 53\nchr6 16400000 61\nchr6 16600000 39\nchr6 16800000 0\nchr6 17000000 30\nchr6 17200000 26\nchr6 17400000 2\nchr6 17600000 135\nchr6 17800000 469\nchr6 18000000 316\nchr6 18200000 138\nchr6 18400000 445\nchr6 18600000 295\nchr6 18800000 462\nchr6 19000000 213\nchr6 19200000 113\nchr6 19400000 61\nchr6 19600000 386\nchr6 19800000 325\nchr6 20000000 64\nchr6 20200000 0\nchr6 20400000 196\nchr6 20600000 84\nchr6 20800000 74\nchr6 21000000 106\nchr6 21200000 413\nchr6 21400000 135\nchr6 21600000 161\nchr6 21800000 330\nchr6 22000000 308\nchr6 22200000 40\nchr6 22400000 90\nchr6 22600000 171\nchr6 22800000 47\nchr6 23000000 89\nchr6 23200000 96\nchr6 23400000 120\nchr6 23600000 0\nchr6 23800000 104\nchr6 24000000 24\nchr6 24200000 238\nchr6 24400000 166\nchr6 24600000 67\nchr6 24800000 36\nchr6 25000000 31\nchr6 25200000 104\nchr6 25400000 1\nchr6 25600000 43\nchr6 25800000 19\nchr6 26000000 26\nchr6 26200000 53\nchr6 26400000 115\nchr6 26600000 22\nchr6 26800000 0\nchr6 27000000 0\nchr6 27200000 0\nchr6 27400000 0\nchr6 27600000 18\nchr6 27800000 0\nchr6 28000000 44\nchr6 28200000 29\nchr6 28400000 0\nchr6 28600000 34\nchr6 28800000 46\nchr6 29000000 36\nchr6 29200000 34\nchr6 29400000 7\nchr6 29600000 0\nchr6 29800000 5\nchr6 30000000 24\nchr6 30200000 19\nchr6 30400000 43\nchr6 30600000 31\nchr6 30800000 40\nchr6 31000000 18\nchr6 31200000 57\nchr6 31400000 122\nchr6 31600000 0\nchr6 31800000 0\nchr6 32000000 25\nchr6 32200000 40\nchr6 32400000 5\nchr6 32600000 107\nchr6 32800000 170\nchr6 33000000 169\nchr6 33200000 610\nchr6 33400000 81\nchr6 33600000 2\nchr6 33800000 70\nchr6 34000000 68\nchr6 34200000 109\nchr6 34400000 116\nchr6 34600000 132\nchr6 34800000 3\nchr6 35000000 4\nchr6 35200000 0\nchr6 35400000 0\nchr6 35600000 34\nchr6 35800000 232\nchr6 36000000 330\nchr6 36200000 323\nchr6 36400000 226\nchr6 36600000 80\nchr6 36800000 298\nchr6 37000000 232\nchr6 37200000 195\nchr6 37400000 124\nchr7 200000 454\nchr7 400000 398\nchr7 600000 310\nchr7 800000 263\nchr7 1000000 299\nchr7 1200000 658\nchr7 1400000 433\nchr7 1600000 322\nchr7 1800000 453\nchr7 2000000 447\nchr7 2200000 265\nchr7 2400000 358\nchr7 2600000 339\nchr7 2800000 588\nchr7 3000000 500\nchr7 3200000 214\nchr7 3400000 393\nchr7 3600000 455\nchr7 3800000 223\nchr7 4000000 347\nchr7 4200000 314\nchr7 4400000 224\nchr7 4600000 337\nchr7 4800000 387\nchr7 5000000 257\nchr7 5200000 298\nchr7 5400000 330\nchr7 5600000 384\nchr7 5800000 287\nchr7 6000000 403\nchr7 6200000 341\nchr7 6400000 779\nchr7 6600000 252\nchr7 6800000 332\nchr7 7000000 261\nchr7 7200000 495\nchr7 7400000 385\nchr7 7600000 290\nchr7 7800000 217\nchr7 8000000 287\nchr7 8200000 380\nchr7 8400000 341\nchr7 8600000 208\nchr7 8800000 329\nchr7 9000000 437\nchr7 9200000 324\nchr7 9400000 353\nchr7 9600000 314\nchr7 9800000 196\nchr7 10000000 302\nchr7 10200000 284\nchr7 10400000 237\nchr7 10600000 267\nchr7 10800000 329\nchr7 11000000 301\nchr7 11200000 286\nchr7 11400000 158\nchr7 11600000 275\nchr7 11800000 257\nchr7 12000000 233\nchr7 12200000 173\nchr7 12400000 295\nchr7 12600000 162\nchr7 12800000 170\nchr7 13000000 202\nchr7 13200000 206\nchr7 13400000 300\nchr7 13600000 239\nchr7 13800000 130\nchr7 14000000 401\nchr7 14200000 109\nchr7 14400000 1521\nchr7 14600000 281\nchr7 14800000 648\nchr7 15000000 203\nchr7 15200000 819\nchr7 15400000 343\nchr7 15600000 161\nchr7 15800000 238\nchr7 16000000 240\nchr7 16200000 180\nchr7 16400000 240\nchr7 16600000 113\nchr7 16800000 119\nchr7 17000000 466\nchr7 17200000 470\nchr7 17400000 467\nchr7 17600000 101\nchr7 17800000 175\nchr7 18000000 72\nchr7 18200000 31\nchr7 18400000 175\nchr7 18600000 44\nchr7 18800000 101\nchr7 19000000 75\nchr7 19200000 318\nchr7 19400000 47\nchr7 19600000 147\nchr7 19800000 188\nchr7 20000000 118\nchr7 20200000 50\nchr7 20400000 36\nchr7 20600000 28\nchr7 20800000 6\nchr7 21000000 54\nchr7 21200000 50\nchr7 21400000 70\nchr7 21600000 30\nchr7 21800000 30\nchr7 22000000 59\nchr7 22200000 77\nchr7 22400000 22\nchr7 22600000 35\nchr7 22800000 34\nchr7 23000000 171\nchr7 23200000 305\nchr7 23400000 25\nchr7 23600000 101\nchr7 23800000 226\nchr7 24000000 16\nchr7 24200000 37\nchr7 24400000 47\nchr7 24600000 185\nchr7 24800000 24\nchr7 25000000 310\nchr7 25200000 306\nchr7 25400000 137\nchr7 25600000 17\nchr7 25800000 38\nchr7 26000000 18\nchr7 26200000 0\nchr7 26400000 19\nchr7 26600000 109\nchr7 26800000 26\nchr7 27000000 181\nchr7 27200000 2\nchr7 27400000 74\nchr7 27600000 9\nchr7 27800000 0\nchr7 28000000 32\nchr7 28200000 60\nchr7 28400000 0\nchr7 28600000 49\nchr7 28800000 0\nchr7 29000000 1\nchr7 29200000 0\nchr7 29400000 0\nchr7 29600000 0\nchr7 29800000 0\nchr7 30000000 179\nchr8 200000 352\nchr8 400000 365\nchr8 600000 273\nchr8 800000 352\nchr8 1000000 191\nchr8 1200000 344\nchr8 1400000 562\nchr8 1600000 229\nchr8 1800000 883\nchr8 2000000 273\nchr8 2200000 76\nchr8 2400000 371\nchr8 2600000 299\nchr8 2800000 901\nchr8 3000000 319\nchr8 3200000 141\nchr8 3400000 290\nchr8 3600000 236\nchr8 3800000 202\nchr8 4000000 279\nchr8 4200000 99\nchr8 4400000 76\nchr8 4600000 64\nchr8 4800000 322\nchr8 5000000 264\nchr8 5200000 124\nchr8 5400000 252\nchr8 5600000 147\nchr8 5800000 46\nchr8 6000000 1117\nchr8 6200000 434\nchr8 6400000 103\nchr8 6600000 151\nchr8 6800000 35\nchr8 7000000 6\nchr8 7200000 0\nchr8 7400000 352\nchr8 7600000 213\nchr8 7800000 24\nchr8 8000000 96\nchr8 8200000 284\nchr8 8400000 95\nchr8 8600000 212\nchr8 8800000 88\nchr8 9000000 15\nchr8 9200000 482\nchr8 9400000 415\nchr8 9600000 208\nchr8 9800000 161\nchr8 10000000 92\nchr8 10200000 263\nchr8 10400000 43\nchr8 10600000 438\nchr8 10800000 122\nchr8 11000000 23\nchr8 11200000 62\nchr8 11400000 24\nchr8 11600000 0\nchr8 11800000 17\nchr8 12000000 0\nchr8 12200000 9\nchr8 12400000 17\nchr8 12600000 27\nchr8 12800000 1\nchr8 13000000 2\nchr8 13200000 0\nchr8 13400000 5\nchr8 13600000 1\nchr8 13800000 121\nchr8 14000000 195\nchr8 14200000 57\nchr8 14400000 4\nchr8 14600000 192\nchr8 14800000 6\nchr8 15000000 74\nchr8 15200000 2\nchr8 15400000 115\nchr8 15600000 52\nchr8 15800000 33\nchr8 16000000 19\nchr8 16200000 0\nchr8 16400000 0\nchr8 16600000 16\nchr8 16800000 33\nchr8 17000000 0\nchr8 17200000 28\nchr8 17400000 103\nchr8 17600000 53\nchr8 17800000 18\nchr8 18000000 169\nchr8 18200000 97\nchr8 18400000 0\nchr8 18600000 85\nchr8 18800000 41\nchr8 19000000 72\nchr8 19200000 237\nchr8 19400000 78\nchr8 19600000 226\nchr8 19800000 84\nchr8 20000000 25\nchr8 20200000 25\nchr8 20400000 69\nchr8 20600000 26\nchr8 20800000 67\nchr8 21000000 54\nchr8 21200000 131\nchr8 21400000 221\nchr8 21600000 78\nchr8 21800000 52\nchr8 22000000 50\nchr8 22200000 244\nchr8 22400000 324\nchr8 22600000 23\nchr8 22800000 315\nchr8 23000000 746\nchr8 23200000 37\nchr8 23400000 97\nchr8 23600000 145\nchr8 23800000 279\nchr8 24000000 194\nchr8 24200000 199\nchr8 24400000 101\nchr8 24600000 380\nchr8 24800000 372\nchr8 25000000 198\nchr8 25200000 507\nchr8 25400000 306\nchr8 25600000 355\nchr8 25800000 274\nchr8 26000000 563\nchr8 26200000 238\nchr8 26400000 361\nchr8 26600000 112\nchr8 26800000 15\nchr8 27000000 27\nchr8 27200000 143\nchr8 27400000 284\nchr8 27600000 275\nchr8 27800000 320\nchr8 28000000 271\nchr8 28200000 185\nchr8 28400000 319\nchr8 28600000 272\nchr8 28800000 288\nchr8 29000000 261\nchr8 29200000 325\nchr8 29400000 445\nchr8 29600000 319\nchr8 29800000 352\nchr8 30000000 332\nchr8 30200000 406\nchr8 30400000 473\nchr8 30600000 523\nchr8 30800000 305\nchr8 31000000 375\nchr8 31200000 340\nchr8 31400000 272\nchr8 31600000 195\nchr9 200000 377\nchr9 400000 329\nchr9 600000 279\nchr9 800000 235\nchr9 1000000 222\nchr9 1200000 264\nchr9 1400000 362\nchr9 1600000 313\nchr9 1800000 399\nchr9 2000000 150\nchr9 2200000 409\nchr9 2400000 622\nchr9 2600000 335\nchr9 2800000 323\nchr9 3000000 297\nchr9 3200000 274\nchr9 3400000 305\nchr9 3600000 249\nchr9 3800000 332\nchr9 4000000 342\nchr9 4200000 220\nchr9 4400000 181\nchr9 4600000 433\nchr9 4800000 357\nchr9 5000000 136\nchr9 5200000 0\nchr9 5400000 0\nchr9 5600000 0\nchr9 5800000 39\nchr9 6000000 339\nchr9 6200000 211\nchr9 6400000 218\nchr9 6600000 363\nchr9 6800000 476\nchr9 7000000 78\nchr9 7200000 311\nchr9 7400000 118\nchr9 7600000 182\nchr9 7800000 251\nchr9 8000000 137\nchr9 8200000 241\nchr9 8400000 164\nchr9 8600000 155\nchr9 8800000 208\nchr9 9000000 93\nchr9 9200000 27\nchr9 9400000 218\nchr9 9600000 139\nchr9 9800000 130\nchr9 10000000 169\nchr9 10200000 226\nchr9 10400000 160\nchr9 10600000 51\nchr9 10800000 31\nchr9 11000000 17\nchr9 11200000 56\nchr9 11400000 84\nchr9 11600000 2\nchr9 11800000 27\nchr9 12000000 91\nchr9 12200000 131\nchr9 12400000 52\nchr9 12600000 52\nchr9 12800000 159\nchr9 13000000 60\nchr9 13200000 56\nchr9 13400000 7\nchr9 13600000 38\nchr9 13800000 45\nchr9 14000000 0\nchr9 14200000 0\nchr9 14400000 5\nchr9 14600000 0\nchr9 14800000 55\nchr9 15000000 28\nchr9 15200000 0\nchr9 15400000 32\nchr9 15600000 5\nchr9 15800000 14\nchr9 16000000 0\nchr9 16200000 146\nchr9 16400000 100\nchr9 16600000 80\nchr9 16800000 9\nchr9 17000000 8\nchr9 17200000 44\nchr9 17400000 94\nchr9 17600000 55\nchr9 17800000 36\nchr9 18000000 0\nchr9 18200000 16\nchr9 18400000 37\nchr9 18600000 1\nchr9 18800000 23\nchr9 19000000 0\nchr9 19200000 6\nchr9 19400000 0\nchr9 19600000 4\nchr9 19800000 88\nchr9 20000000 87\nchr9 20200000 26\nchr9 20400000 0\nchr9 20600000 89\nchr9 20800000 238\nchr9 21000000 15\nchr9 21200000 58\nchr9 21400000 188\nchr9 21600000 140\nchr9 21800000 236\nchr9 22000000 237\nchr9 22200000 322\nchr9 22400000 128");

  $("#dataFieldArea1").text("chr3 76806987 76807187 chr1 91852578 91852878\nchr1 91862783 91852783 chr2 133037705 133036705\nchr1 91852783 91852783 chr2 88124673 88124673\nchr3 33478116 33478116 chr1 237766312 237766312\nchr1 33478116 33478116 chr3 91853039 91853039");
  load_circos();
}
function updateFields(type, parent){
  switch(type){ 
    case "HeatMap":
    document.getElementById("help-block"+parent).innerHTML = "Data format : chr pos value value2...";
    break;
    case "HighLight":
    document.getElementById("help-block"+parent).innerHTML = "Data format : chr start end text text";
    break;
    case "Histogram":
    document.getElementById("help-block"+parent).innerHTML = "Data format : 65464";
    break;
    case "Chords":
    document.getElementById("help-block"+parent).innerHTML = "Data format : chr_source start end chr_dest start end";
    break;
    case "Line":
    document.getElementById("help-block"+parent).innerHTML = "Data format : chr pos value, value2...";
    break;
    case "Scatter":
    document.getElementById("help-block"+parent).innerHTML = "Data format : chr start end value";
    break;
    case "Stack":
    document.getElementById("help-block"+parent).innerHTML = "Data format : 65464";
    break;
    case "Text":
    document.getElementById("help-block"+parent).innerHTML = "Data format : 65464";
    break;
  } 
}

//Function TEST
function generateSVG(){
  //get svg element.
  var svg = document.getElementById("svgdemo");

  //get svg source.
  var serializer = new XMLSerializer();
  var source = serializer.serializeToString(svg);

  //add name spaces.
  if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
    source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
  }
  if(!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)){
    source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
  }

  //add xml declaration
  source = '<?xml version="1.0" standalone="no"?>\r\n' + source;

  //convert svg source to URI data scheme.
  var url = "data:image/svg+xml;charset=utf-8,"+encodeURIComponent(source);

  //set url value to a element's href attribute.
  document.getElementById("download").href = url
  document.getElementById("download").download = "result.svg";
  document.getElementById("download").click();
}

