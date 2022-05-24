var images_location = "https:/panexplorer.southgreen.fr/images";

function Upload2(cgi_dir,session,email,genbanks,projectnew,software)
{
        var url = cgi_dir + "/ajax.pl";
        $.ajax({
                            type: 'GET',
                            url: url,
                            data: jQuery.param({action: "upload", projectnew : projectnew, email: email, session : session, software : software, genbanks : genbanks}) ,
                            timeout: 50000000,
                            success: function(res) {
                                div.html(res);
                                }
                    });
        var thediv = $("#results_div");
        thediv.html("<div class=\"alert alert-success\" role=\"alert\">Thanks, the genomes have been submitted to the pipeline. An email will be sent when data will be available</div>");
}

function Upload(cgi_dir,session,genbanks,projectnew,software)
{
	var url = cgi_dir + "/display_ajax.cgi";
	var params = "action=upload";
	if (projectnew != "" && document.query_form.email.value != "" && genbanks != ""){
		var mailformat = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
		if(document.query_form.email.value.match(mailformat))
		{
			params = params + '&projectnew=' + projectnew;
			params = params + '&email=' + document.getElementById("email").value;
			params = params + '&genbanks=' + genbanks;
			params = params + '&session=' + session;
			params = params + '&software=' + software;
			var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_upload,onSuccess:success_search,onFailure:failure_search});
		}
		else{
			alert("You have entered an invalid email address!");
		}
	}
	else{
		alert("You must provide project name, genbank ids and email...");
	}
}
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function CheckIDs2(cgi_dir,session)
{


 //       var url = cgi_dir + "/display_ajax.cgi";
        var url = cgi_dir + "/ajax.pl";
        var ajax_div = $("#check_div_global");
        genbanks = document.query_form.genbanks.value;
        projectnew = document.query_form.projectnew.value;
        software = document.query_form.software.value;
	email = document.query_form.email.value;
        if (projectnew != "" && document.query_form.email.value != "" && genbanks != ""){
                var project_format = /(^[\w]+)$/;
                if(!projectnew.match(project_format))
                {
                        alert("Project name is not valid...");return;
                }
                var genbanks_format = /(^[\w\.\,\-]+)$/;
                if(!genbanks.match(genbanks_format))
                {
                        alert("List of genbank identifiers is not valid. Please make sure that it doesn't contain special character...");return;
                }
                var mailformat = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
                if(document.query_form.email.value.match(mailformat))
                {
                        var arrayOfStrings = genbanks.split(",");
                        var list = "";
                        if (arrayOfStrings.length > 300){
                               alert("Too many Genbank identifiers (maximum 300). Here: " + arrayOfStrings.length);return;
                        }
                        else if (arrayOfStrings.length < 3){
                                alert("You must provide at least 3 Genbank identifiers of bacterial genomes");return;
                        }
                        else{
				ajax_div.html("<i>Please wait ...</i>");
                                for(var i= 0; i < arrayOfStrings.length; i++)
                                {
                                        var genbank_id = arrayOfStrings[i];
                                        var div = $("#"+(i+1));
					div.html("<img height=20 src=\"https://panexplorer.southgreen.fr/images/waiting-icon-gif-23.jpg\">"+i + " " +genbank_id+" pending...");
                                }
				var nb_found = 0;
                                for(var i= 0; i < arrayOfStrings.length; i++)
{
                                        var genbank_id = arrayOfStrings[i];
					var div = $("#"+(i+1));
					div.html("<img height=20 src=\"https://panexplorer.southgreen.fr/images/please-wait-animated-gif-7-gif-images-download_63.gif\">Checking "+ genbank_id + "...");
					$.ajax({
                            type: 'GET',
                            url: url,
                            data: jQuery.param({action: "check_id", projectnew : projectnew, email: email, session : session, genbanks : genbank_id}) ,
                            timeout: 50000000,
                            success: function(res) {
				var error_format = "ERROR";
				if (res.match(error_format)){nb_found++;}
				div.html(res);
				},
                            error: function() {}
                    });


				await sleep(7000);
                                }
				if (nb_found == 0){
					var new_button = "<br/>Genbank identifiers have been checked successfully...<br/><br/>";
                			new_button += "<input class=\"btn btn-primary\" type=\"button\" id=\"submission\" value=\"Submit\" onclick=\"document.getElementById('submission').style.visibility = 'hidden';Upload2('"+cgi_dir+"','"+session+"','"+email+"','"+genbanks+"','"+projectnew+"','"+software+"');\">";
                			new_button += "<br/><br/><div id=results_div></div>";
					ajax_div.html(new_button);
				}
				else{
					ajax_div.html("<div class=\"alert alert-danger\" role=\"alert\">Some of the identifiers provided are not allowed</div>");
					//ajax_div.html("<div class=\"alert alert-danger\" role=\"alert\">Some of the identifiers provided are not allowed</div>"+nb_found+ " and "+arrayOfStrings.length);
				}
                        }
                }
                else{
                        alert("You have entered an invalid email address!");
                }
        }
        else{
                alert("You must provide project name, genbank ids and email...");
        }
}

async function CheckIDs(cgi_dir,session)
{


        var url = cgi_dir + "/display_ajax.cgi";
	genbanks = document.query_form.genbanks.value;
	projectnew = document.query_form.projectnew.value;
        if (projectnew != "" && document.query_form.email.value != "" && genbanks != ""){
		var project_format = /(^[\w]+)$/;
		if(!projectnew.match(project_format))
		{
			alert("Project name is not valid...");return;
		}
		var genbanks_format = /(^[\w\.\,]+)$/;
		if(!genbanks.match(genbanks_format))
                {
                        alert("List of genbank identifiers is not valid. Please make sure that it doesn't contain special character...");return;
                }
                var mailformat = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
                if(document.query_form.email.value.match(mailformat))
                {
			var arrayOfStrings = genbanks.split(",");
			var list = "";
			if (arrayOfStrings.length > 60){
                                alert("Too many Genbank identifiers (maximum 60)");
                        }
			else if (arrayOfStrings.length < 3){
                                alert("You must provide at least 3 Genbank identifiers of bacterial genomes");
                        }
			else{
				for(var i= 0; i < arrayOfStrings.length; i++)
				{
					var genbank_id = arrayOfStrings[i];
					list += "<div id='"+genbank_id+"'><img height=20 src=\"https://panexplorer.southgreen.fr/images/waiting-icon-gif-23.jpg\">"+genbank_id+" pending...</div>";
				}
			
				var thediv= $('check_div') ;
	
				thediv.innerHTML = list;
				for(var i= 0; i < arrayOfStrings.length; i++)
				{
					var genbank_id = arrayOfStrings[i];
					await sleep(7000);
					var params = "action=check_id";
					params = params + '&projectnew=' + projectnew;
					params = params + '&email=' + document.getElementById("email").value;
					params = params + '&session=' + session;
					params = params + '&genbanks=' + genbank_id;
		                	var myAjax = new Ajax.Request(url,{timeOut:900000, method:'post',postBody:params,onLoading:loading_genbank(genbank_id),onSuccess:success_genbank,onFailure:failure_genbank});
					if (i == arrayOfStrings.length){

					}	
				}
				var ajax_div = $('check_div_global');
				ajax_div.innerHTML = "Please wait...";

				await sleep(7000);
				var params = "action=check_ids";
				params = params + '&projectnew=' + projectnew;
				params = params + '&session=' + session;
				params = params + '&genbanks=' + genbanks;
				params = params + '&software=' + document.getElementById("software").value;
				var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_genbanks,onSuccess:success_genbanks});
			}
                }
                else{
                        alert("You have entered an invalid email address!");
                }
        }
        else{
                alert("You must provide project name, genbank ids and email...");
        }
}

function loading_genbank(genbank_id)
{
	var div = $(genbank_id);
	div.innerHTML = "<img height=20 src='"+images_location+"/please-wait-animated-gif-7-gif-images-download_63.gif'>Checking "+ genbank_id + "...";
}
function failure_genbank(genbank_id)
{
        var div = $(genbank_id);
        div.innerHTML = "It failed...";
}

function success_genbanks(transport)
{
	 var ajax_div = $('check_div_global');
	ajax_div.innerHTML = transport.responseText;
}
function loading_genbanks()
{
	var ajax_div = $('check_div_global');
	ajax_div.innerHTML = "Please wait...";
}
function success_genbank(transport)
{
	var response = transport.responseText;
	var arrayOfStrings = transport.responseText.split("GENBANK_ID");
	if (!arrayOfStrings[1]){
		var ajax_div = $('check_div_global');
		div.innerHTML = "<img height=20 src='"+images_location+"/error-icon-4.png'>error"+response;
	}
	var genbank_id = arrayOfStrings[1];
	var information = arrayOfStrings[2];
	var arrayOfErrors = information.split("ERROR");
        var div = $(genbank_id);
	if (arrayOfErrors.length > 1){
		div.innerHTML = "<img height=20 src='"+images_location+"/error-icon-4.png'>&nbsp;&nbsp;"+genbank_id+": "+information;
	}
	else{
		div.innerHTML = "<img height=20 src='"+images_location+"/2048px-Yes_Check_Circle.svg.png'>&nbsp;&nbsp;"+genbank_id+" validated: "+information;
	}
}
function SearchStrain(cgi_dir,session)
{
	var url = cgi_dir + "/display_ajax.cgi";
	var params = "action=search";
	var list_strains = "";
	if (document.query_form.strains.options)
        {
                var strains = document.query_form.strains.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
			if (strains[i].selected){
	                    list_strains += strains[i].value + ",";
			}
                }
        }
	var nb_max_by_strain = document.query_form.nb_max_by_strain.value;
	params = params + '&strains=' + list_strains + '&nb_max_by_strain=' + nb_max_by_strain + '&session=' + session;
	params = params + '&project=' + document.getElementById("project").value;
	var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}

function SearchCluster(cgi_dir,session)
{
        var url = cgi_dir + "/display_ajax.cgi";
        var params = "action=search_cluster";
        params = params + '&genename=' + document.getElementById("genename").value + '&session=' + session;
        params = params + '&project=' + document.getElementById("project").value;
	//alert('okkk'+params);
	//window.open(url+"?"+params);
        var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}

function openCity(evt, cityName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(cityName).style.display = "block";
  evt.currentTarget.className += " active";
}


function Circos(cgi_dir,session)
{
        var url = cgi_dir + "/display_ajax.cgi";
        var params = "action=circos";
        var list_strains = "";
        if (document.query_form.strains.options)
        {
                var strains = document.query_form.strains.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
                        if (strains[i].selected){
                            list_strains += strains[i].value + ",";
                        }
                }
        }
		var feature = "coregenes1";
		if (document.query_form.feature && document.query_form.feature.options)
		{
			var features = document.query_form.feature.options;
			for (var i = features.length - 1; i>=0; i--)
			{
				if (features[i].selected){
						feature = features[i].value;
				}
			}
		}
        //params = params + '&strains=' + list_strains + '&session=' + session + '&feature=' + feature;
        params = params + '&strains=' + list_strains + '&session=' + session + '&feature=coregenes1';
	params = params + '&project=' + document.getElementById("project").value;
        var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}

function Circos2(cgi_dir,session)
{
        var url = cgi_dir + "/display_ajax.cgi";
        var params = "action=circos";
        var list_strains = document.query_form.strains.value + ",";
        params = params + '&strains=' + list_strains + '&feature=coregenes1&session=' + session;
        params = params + '&project=' + document.getElementById("project").value;
	alert(params);
        var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}

function GeneSearch(cgi_dir,session)
{
        var url = cgi_dir + "/display_ajax.cgi";
        var params = "action=genesearch";
        var list_strains = "";
        if (document.query_form.strains.options)
        {
                var strains = document.query_form.strains.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
                        if (strains[i].selected){
                            list_strains += strains[i].value + ",";
                        }
                }
        }
        params = params + '&strains=' + list_strains + '&session=' + session;
	params = params + '&project=' + document.getElementById("project").value;
        var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}

function Synteny(cgi_dir,session)
{
        var url = cgi_dir + "/display_ajax.cgi";
        var params = "action=synteny";
        var strain1 = "";
        if (document.query_form.strains1.options)
        {
                var strains = document.query_form.strains1.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
                        if (strains[i].selected){
                            strain1 = strains[i].value;
                        }
                }
        }
	var strain2 = "";
	if (document.query_form.strains2.options)
        {
                var strains = document.query_form.strains2.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
                        if (strains[i].selected){
                            strain2 = strains[i].value;
                        }
                }
        }
	var strain3 = "";
	if (document.query_form.strains3.options)
        {
                var strains = document.query_form.strains3.options;
                for (var i = strains.length - 1; i>=0; i--)
                {
                        if (strains[i].selected){
                            strain3 = strains[i].value;
                        }
                }
        }
        params = params + '&strain1=' + strain1 + '&strain2=' + strain2 + '&strain3=' + strain3 + '&session=' + session + '&cluster=' + document.getElementById("cl").value;
	params = params + '&project=' + document.getElementById("project").value;
        var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_search,onSuccess:success_search,onFailure:failure_search});
}


function success_search(transport)
{
  var ajax_div = $('results_div');
  ajax_div.innerHTML = transport.responseText;
}
function failure_search(transport)
{
  var thediv= $('results_div') ;
 thediv.innerHTML = "Well...it failed !!" ;
}
function loading_search(transport)
{
        var thediv = $('results_div');
	thediv.innerHTML = "<i>Searching... Please wait...</i>";
        //thediv.update("&nbsp;&nbsp;&nbsp;&nbsp;<img src=" + images_location + "/loading.gif>\n");
}

function loading_upload(transport)
{
        var thediv = $('results_div');
	thediv.innerHTML = "<div class=\"alert alert-success\" role=\"alert\">The clustering analysis is ready to be launched. An email will be sent when data will be available</div>";
}

function loading_checkIDs(transport)
{
        var thediv = $('check_div');
        thediv.innerHTML = "<i>Checking Genbank IDs... Please wait...</i>";
}
function success_checkIDs(transport)
{
  var ajax_div = $('check_div');
  ajax_div.innerHTML = transport.responseText;
}
function failure_checkIDs(transport)
{
  var thediv= $('check_div') ;
 thediv.innerHTML = "Well...it failed !!" ;
}
function MSAViewer(url){
var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.send(null);
    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            var type = request.getResponseHeader('Content-Type');
        fasta = request.responseText;
        var seqs = msa.io.fasta.parse(fasta);
        var m = msa({
        el: document.getElementById("msa"),
        seqs: seqs
        });
        m.render();

        }
    }
}

