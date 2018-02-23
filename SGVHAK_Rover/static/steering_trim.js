/*
MIT License

Copyright (c) 2018 Roger Cheng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// Hook up event handlers in this file to elements in corresponding HTML.
$(document).ready(function() {
  $("input[type=radio]").on("click", radioSelect);
  $(".adjust").on("click", trimAdjust);
  $("#trimCancel").on("click", trimCancel);
  $("#trimZero").on("click", trimZero);

  postTrimUrl = document.getElementById("steering_trim").value;
})

var angle = 0; // The angle value shown on screen
var selectedWheel = null; // Name of wheel selected via radio button
var postTrimUrl = null; // The URL to use for POST trim data.

// When a radio button is clicked to select a wheel, enable to angle adjustment
// controls and disable the wheel select to keep it focused on one wheel.
var radioSelect = function(e) {
  selectedWheel = e.target.id;
  $("input[type=radio]").attr("disabled","disabled");
  $(".adjust").removeAttr("disabled");
  $("#trimCancel").removeAttr("disabled");
  $("#trimZero").removeAttr("disabled");
}

// User has clicked on a movement button to move the selected wheel a little
// bit, looking for the center.
var trimAdjust = function(e) {
  var trimAction = e.target.id;

  // Make adjustment commanded by user click.
  if (trimAction.startsWith("plus")) {
    var addAmount = parseInt(trimAction.substr(4));
    angle += addAmount;
  } else if (trimAction.startsWith("minus")) {
    var subtractAmount = parseInt(trimAction.substr(5));
    angle -= subtractAmount;
  } else {
    console.log("Invalid action for trim button");
  }

  // Now that wheel steering angle has been updated, POST to controller.
  $.ajax({
    type: "POST",
    url: postTrimUrl,
    data: {wheel: selectedWheel, move_to:angle},
    complete: postComplete
  })

  // Update on onscreen indicator accordingly.
  $("#angleOut").text(angle);
}

// When user either commits angle as new zero, or cancel out and leave things
// unchanged, we want to reset the UI by disabling all the adjustment controls
// and turn the wheel selection back on.
var resetTrimUI = function() {
  angle = 0;
  $("#angleOut").text(angle);
  $("input[type=radio]").removeAttr("disabled");
  $(".adjust").attr("disabled","disabled");
  $("#trimCancel").attr("disabled","disabled");
  $("#trimZero").attr("disabled","disabled");
}

// User has chosen to cancel trim action. POST to controller to ask it to steer
// wheel back to its zero position, and reset the UI to allow selecting another
// wheel.
var trimCancel = function(e) {
  $.ajax({
    type: "POST",
    url: postTrimUrl,
    data: {wheel: selectedWheel, move_to:0},
    complete: postComplete
  })

  resetTrimUI();
}

// User has chosen to commit trim action. POST to controller to ask it to use
// the current position as the new zero, and reset UI to allow selecting
// another wheel.
var trimZero = function(e) {

  $.ajax({
    type: "POST",
    url: postTrimUrl,
    data: {wheel: selectedWheel, set_zero:angle},
    complete: postComplete
  })

  resetTrimUI();
}

// Called when POST action is complete.
var postComplete = function(jqXHR, textStatus) {
  console.log(textStatus); // TODO: remove this debug output once running
}