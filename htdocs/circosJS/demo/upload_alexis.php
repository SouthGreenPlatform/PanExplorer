<!DOCTYPE html> 
<html>
<head>
  <title>Meh</title>
  <meta charset="utf-8">
  <script src="https://code.jquery.com/jquery-3.2.1.js"></script>
  <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
  <link href="//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" rel="stylesheet">
</head>
<body>
  <script type="text/javascript">
    $(document).ready(function() {
    var max_fields      = 6; //maximum input boxes allowed
    var wrapper         = $(".input_fields_wrap"); //Fields wrapper
    var add_button      = $(".add_field_button"); //Add button ID
    
    var x = 1; //initlal text box count
    $(add_button).click(function(e){ //on add input button click
      e.preventDefault();
        if(x < max_fields){ //max input box allowed
            x++; //text box increment
            $(wrapper).append('<div class="form-group"><div class="form-group"><label for="inputPassword" class="col-lg-2 control-label">Load File :</label><div class="col-lg-10"><input type="file" name="data[]"></div></div><div class="form-group"><label for="select" class="col-lg-2 control-label">Type</label><div class="col-lg-10"><select class="form-control" name="select[]"><option value="Chords">Chords</option><option value="HighLight">HighLight</option><option value="Line">Line</option><option value="HeatMap">HeatMap</option><option value="Scatter">Scatter</option><option value="Histogram" disabled="">Histogram</option><option value="Stack" disabled="">Stack</option><option value="Text" disabled="">Text</option></select></div></div><div class="form-group"></div><button href="#" class="remove_field btn-danger col-lg-6 col-lg-offset-4">Remove</button></div>'); //add input box
          }else{
            alert("To many values ;)");
          }
        });
    
    $(wrapper).on("click",".remove_field", function(e){ //user click on remove text
      e.preventDefault(); $(this).parent('div').remove(); x--;
    })
  });
</script>


<form class="form-horizontal col-md-5" action="http://dev.visusnp.southgreen.fr/circosJS/demo/index_alexis.php" method="post" enctype="multipart/form-data" >
  <fieldset class="input_fields_wrap">
    <legend>Upload files</legend>
    <div class="form-group">
      <label class="col-lg-2 control-label">Upload Chromosome file :</label>
      <div class="col-lg-10">
        <input type="file" name="chromosome"></div>
      </div>
    <div class="form-group">
      <div class="col-lg-10 col-lg-offset-2">
        <button type="reset" class="btn btn-default">Cancel</button>
        <button type="submit" class="btn btn-primary">Submit</button>
        <button class="add_field_button">Ajouter champ</button>
      </div>
    </div>
  </fieldset>
</form>
</body>
</html>
