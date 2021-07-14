/********************************************************************************
 * Name: main.js
 * Author: ntaylor
 * Created On: October 20, 2015
 * Copyright: (c) Aquaveo 2015
 * License:
 ********************************************************************************/

//Global setTimeout variables so that it can be cleared
var timeoutRefresh = null;
var timeoutInitial = null;
var ctrlIsPressed = false;

$(document).keydown(function(event){
    if (event.which == "17")
        ctrlIsPressed = true;
});

$(document).keyup(function(){
    ctrlIsPressed = false;
});

function addProcessingDiv() {
    var divShow = document.createElement("showBackground");
    var imageShow = document.createElement("showImage");
    var elem = document.createElement("img");

    if ($('#showBackground').length === 0) {
        divShow.id = 'showBackground';
        divShow.className="center-parent hidden";
        document.body.appendChild(divShow);
        imageShow.id = 'showImage';
        document.getElementById("showBackground").appendChild(imageShow);
        elem.setAttribute("src", "/static/modflow/images/loading3.gif");
        elem.setAttribute("height", "50");
        elem.setAttribute("width", "400");
        elem.setAttribute("alt", "Upload");
        document.getElementById("showImage").appendChild(elem);
    }
}


// Generate a GIF that covers page while loading
function showProcessing() {
    $('#showBackground').removeClass('hidden');
}

function hideProcessing() {
    $('#showBackground').addClass('hidden');
}


$(function(){
   $(document).on('click', '[onclick*="window.document.location="]', function () {
      showProcessing();
  });

  $(document).on('click', 'a', function () {
      var $thisLink = $(this);
      var href = $thisLink.attr('href');
      var target = $thisLink.attr('target');
      if (href) {
          if (href.indexOf('#') !== 0 && href.indexOf('javascript') === -1 && !ctrlIsPressed && target !== '_blank') {
              showProcessing();
          }
      }
  });

  $(document).on('click', 'input[type="submit"]', function () {
      if ($(this).closest('form').attr('target') !== '_blank') {
          showProcessing();
      }
  });

    window.onbeforeunload = function(e) {
      showProcessing();
    }

  addProcessingDiv();
});