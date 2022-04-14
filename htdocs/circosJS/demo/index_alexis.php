<!DOCTYPE html> 
<html>
<head>
  <title id="titleMeh"></title>
  <script src="https://code.jquery.com/jquery-3.2.1.js" integrity="sha256-DZAnKJ/6XZ9si04Hgrsxu/8s717jcIzLy3oi35EouyE=" crossorigin="anonymous"></script>
  <link href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.7/yeti/bootstrap.min.css" rel="stylesheet" integrity="sha384-HzUaiJdCTIY/RL2vDPRGdEQHHahjzwoJJzGUkYjHVzTwXFQ2QN/nVgX7tzoMW3Ov" crossorigin="anonymous">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&amp;lang=en">
  <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
  <link rel="stylesheet" href="//code.getmdl.io/1.3.0/material.deep_purple-pink.min.css">
  <script src='../dist/circos.js'></script>
  <script src='../dist/svg-pan-zoom.js'></script>
  <script src='https://cdnjs.cloudflare.com/ajax/libs/d3/4.5.0/d3.js'></script>
  <script src='https://cdnjs.cloudflare.com/ajax/libs/d3-queue/3.0.3/d3-queue.js'></script>
  <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
  <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
  <script>
   /* $( function() {
      $( "#cat" ).dialog({
        height: 430,
        width: 725,
        autoOpen: true,
        show: {
          effect: "blind",
          duration: 1000
        },
        hide: {
          effect: "explode",
          duration: 1000
        }
      });
    } );*/
  </script>
</head>
<body>
  <div style="display: none;" id="cat">
    <img src="../dist/cat.gif" />
  </div>
  <div class="row">
    <div class="col-md-8">
      <!--Div qui se charge de l'affichage du circos-->
      <div class="circoscontainer" >
        <div id='lineChart'></div>
      </div>
    </div>
    <div class="form-horizontal col-md-4">
      <fieldset>
        <legend>Data</legend>
        <br>
        <div class="form-group">

          <div class="form-group">
          <label for="userUrl" class="col-lg-4 control-label">Url(optional) :</label>
           <div class="col-lg-7">
             <input id="userUrl" wrap="off" rows=4 class="form-control" placeholder="Insert URL"></input>
           </div>
            <div id="modalContent"></div>
            <div id="urlFinal"></div>
         </div>

         <br>
         <div class="form-group">
           <label for="dataFieldAreaC" class="col-lg-4 control-label">Chromosome data*</label>
           <div class="col-lg-7">
            <textarea id="dataFieldAreaC" wrap="off" rows="5" class="form-control" placeholder="Insert values here"></textarea>
            <span class="help-block">Each entry must be separated by carriage return :<br>
              <b>chr0 length #color</b>
              <br>
              <b>chr1 length #color</b></span>
            </div>
          </div>

          <button class="btn btn-primary col-lg-6 col-lg-offset-4" onclick="load_file(this.value)" id="newLoadDataC" value="C">Load Data</button>
          <br>
          <input class="btn btn-warning col-lg-6 col-lg-offset-4" type="file" style="display:none;" id="fileInputC">
          <h5 id="parC" class=" col-lg-offset-5"></h5>
        </div>
        <h5>Tracks</h5>
        <br>
        <div class="form-group">
          <div id="tracks_content">
            <!--ici vient le choix de l'user-->
          </div>
          <div id="button">
            <!--Boutton pour l'ajout d'une track-->
            <button class="btn btn-primary" id="newTrackButton">Add new track</button>
            <button class="btn btn-warning" onclick="load_test()" id="load_test">Test data</button>
            <button class="btn btn-danger" onclick="load_circos()" style="display:none;" id="loadCircos">Load Circos</button>
            <a id="download" class="btn btn-warning" onclick="generateSVG()">Download</a>
          </div>
        </div>
      </div>
    </fieldset>
  </div>
  <script src='./holdtheline_alexis2.js'></script>
  <?php
  
   #print_r($_POST["chromosome"]);
   #echo "OK<br>";
   #echo file_get_contents($_POST["chromosome"]);
#echo "Select<br><br>";
    #print_r($_POST["select"]);
#echo "dereeper<br><br>";
    #print_r($_POST["data"]);
#echo "dereeper<br><br>";
    if(isset($_FILES["data"]) && isset($_FILES["chromosome"])){
      $i = 0;
      $chromosomeData = json_encode(file_get_contents($_FILES["chromosome"]["tmp_name"]));
      echo "
      <script>
        var data  = {$chromosomeData};
        $('#dataFieldAreaC').text(data);
      </script>";
      foreach($_FILES["data"]["tmp_name"] as $key => $text_field){
        $capture_field_vals = json_encode(file_get_contents($text_field));
        $select = $_POST["select"][$i];
        echo "
        <script>
          var data  = {$capture_field_vals};
          var select = \"$select\";
          var i = $i;
          $('#newTrackButton').click();
          $('#selectType'+i).val(select).change();
          $('#dataFieldArea'+i).text(data);
        </script>";
        $i++;
      }
      echo "
      <script>
        load_circos();
      </script>";
    }
   elseif(isset($_POST["data"]) && isset($_POST["chromosome"])){
      $i = 0;
      $chromosomeData = json_encode(file_get_contents($_POST["chromosome"]));
      echo "
      <script>
        var data  = {$chromosomeData};
        $('#dataFieldAreaC').text(data);
      </script>";
      foreach($_POST["data"] as $key => $text_field){
        $capture_field_vals = json_encode(file_get_contents($text_field));
        $select = $_POST["select"][$i];
        echo "
        <script>
          var data  = {$capture_field_vals};
          var select = \"$select\";
          var i = $i;
          $('#newTrackButton').click();
          $('#selectType'+i).val(select).change();
          $('#dataFieldArea'+i).text(data);
        </script>";
        $i++;
      }
      echo "
      <script>
        load_circos();
      </script>";
    }
  ?>
</body>
</html>
