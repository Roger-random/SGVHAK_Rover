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

// Resize the pad and redraw upon initial load, and whenever window size changes.
$(document).ready(function() {
  resizePad();
  drawPad();
  padListeners();
});
$(window).resize(function() {
  resizePad();
  drawPad();
});

// Current status of control pad, initialized to default values.
padSize = 300;
knobX = padSize/2;
knobY = padSize/2;
knobtracking = false;

// Size the control pad to fit the available window.
var resizePad = function() {
  var pad = document.getElementById("controlPad");

  var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
  var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);

  var square = Math.min(w,h);

  if (square > 300)
  {
    pad.width = square;
    pad.height = square;
    padSize = square;
    knobX = padSize/2;
    knobY = padSize/2;
  }
}

// Add event listeners to control pad
var padListeners = function() {
  var pad = document.getElementById("controlPad");

  // TODO: Figure out why the jQuery equivalents didn't work.
  pad.addEventListener("mousedown", trackingOn)
  pad.addEventListener("touchstart", trackingOn)
  pad.addEventListener("mousemove", updateKnob)
  //pad.addEventListener("touchmove", updateKnob)
  pad.addEventListener("mouseup", trackingOff)
  pad.addEventListener("touchend", trackingOff)

  // Turn off touch events when target is the pad, otherwise it'll scroll the
  // page instead of doing what we want.
  document.body.addEventListener("touchstart", function(e) {
    if (e.target == pad) {
      e.preventDefault();
    }
  }, false);
  document.body.addEventListener("touchmove", function(e) {
    if (e.target == pad) {
      e.preventDefault();
    }
  }, false);
  document.body.addEventListener("touchend", function(e) {
    if (e.target == pad) {
      e.preventDefault();
    }
  }, false);
}

var trackingOn = function() {
  knobtracking = true;
  window.requestAnimationFrame(drawPad);
}

var trackingOff = function() {
  knobtracking = false;
  window.requestAnimationFrame(drawPad);
}

var updateKnob = function(e) {
  if (knobtracking)
  {
    knobX = e.clientX;
    knobY = e.clientY - padSize*.15/2;
    window.requestAnimationFrame(drawPad);
  }
}

// Draw control pad
var drawPad = function() {
  var pad = document.getElementById("controlPad");
  var ctx = pad.getContext("2d");
  var center = padSize/2;
  var radius = 0.85 * center;
  var knobradius = 0.15 * center;

  ctx.clearRect(0,0,padSize,padSize);

  ctx.beginPath();
  ctx.fillStyle = "#00FF00";
  ctx.arc(center,center,radius,0,2*Math.PI);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(knobX, knobY, knobradius, 0, 2*Math.PI);
  if (knobtracking)
  {
    ctx.fillStyle = "#0000FF";
  }
  else
  {
    ctx.fillStyle = "#FF0000";
  }
  ctx.fill()
}