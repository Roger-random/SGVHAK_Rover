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
var padSize = 300;
var knobX = padSize/2;
var knobY = padSize/2;
var knobRadius = padSize * .15/2 // knob diameter is 15% of pad size.
var knobTracking = false;
var knobTrackingTouchPoint = null;

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
    knobRadius = padSize * .15/2
  }
}

// Add event listeners to control pad
var padListeners = function() {
  var pad = document.getElementById("controlPad");

  // TODO: Gracefully handle interspersed mouse and touch events. 

  // For unknown reason, jQuery equivalent failed to fire, so do it here.
  pad.addEventListener("mousedown", padMouseDown)
  pad.addEventListener("mousemove", padMouseMove)
  pad.addEventListener("mouseup", padMouseUp)

  // No jQuery equivalents for touch events.
  pad.addEventListener("touchstart", padTouchStart)
  pad.addEventListener("touchmove", padTouchMove)
  pad.addEventListener("touchcancel", padTouchEnd)
  pad.addEventListener("touchend", padTouchEnd)

  // Turn off touch events when user touches the pad, otherwise user movements
  // for moving the control knob will scroll the page instead.
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

// We're only hit-testing the rectangle that encloses the knob, since this
// math is simpler and faster. Revisit if this shortcut causes UI issues.
var onKnob = function(x,y) {
  return (x > (knobX-knobRadius) &&
          x < (knobX+knobRadius) &&
          y > (knobY-knobRadius) &&
          y < (knobY+knobRadius));
}

// When Mouse or Touch event occurs, their respective handlers will pull out
// the x/y coordinates and pass into these common handlers.
var pointerStart = function(x,y) {
  if (onKnob(x,y)) {
    knobX = x;
    knobY = y;
    knobTracking = true;
    window.requestAnimationFrame(drawPad);
  }
}

var pointerMove = function(x,y) {
  if (knobTracking) {
    knobX = x;
    knobY = y;
    window.requestAnimationFrame(drawPad);
  }
}

var pointerEnd = function() {
  if (knobTracking) {
    knobX = padSize/2;
    knobY = padSize/2;
    knobTracking = false;
    window.requestAnimationFrame(drawPad);
  }
}

// For mouse control, we only want to start the knob tracking if the user
// deliberately started on the control knob. Clicking elsewhere on the pad
// should be ignored.
var padMouseDown = function(e) {
  pointerStart(e.offsetX,e.offsetY);
}

var padMouseMove = function(e) {
  pointerMove(e.offsetX,e.offsetY);
}

var padMouseUp = function(e) {
  pointerEnd();
}

// TODO: Robust client X/Y transform for touch events.
// While mouse events have offsetX/offsetY for coordinates in target space,
// touch events don't seem to have the same thing. We need to transform the
// clientX/clientY coordinates (which is relative to all HTML content) into
// target space. A robust solution will account for zoom/scaling and rotation.
// The code below only corrects for X/Y offset transform and is not robust 
// against other transforms.

// When a touch event starts and we're not currently tracking, we look through 
// all the touch pointers to see if any of them are on the control knob. If
// found, we track that pointer (and ignore all others) until it is lifted.
var padTouchStart = function(e) {
  if (knobTracking) {
    // Already tracking a touch point, ignore newly started ones.
    return;
  }
  var newTouches = e.changedTouches;

  for (var i = 0; i < newTouches.length; i++) {
    touch = newTouches[i];

    // Correct for X/Y client offset
    touchX = touch.clientX - touch.target.getBoundingClientRect().left;
    touchY = touch.clientY - touch.target.getBoundingClientRect().top;

    if (onKnob(touchX, touchY)) {
      knobTrackingTouchPoint = touch.identifier;
      pointerStart(touchX, touchY);
    }
  }
}

var padTouchMove = function(e) {
  if (knobTracking) {
    var newTouches = e.changedTouches;

    for (var i = 0; i < newTouches.length; i++) {
      touch = newTouches[i];
      if (touch.identifier == knobTrackingTouchPoint) {
        // Correct for X/Y client offset
        touchX = touch.clientX - touch.target.getBoundingClientRect().left;
        touchY = touch.clientY - touch.target.getBoundingClientRect().top;

        pointerMove(touchX, touchY);
      }
    }
  }
}

var padTouchEnd = function(e) {
  if (knobTracking) {
    var newTouches = e.changedTouches;

    for (var i = 0; i < newTouches.length; i++) {
      touch = newTouches[i];
      if (touch.identifier == knobTrackingTouchPoint) {
        pointerEnd();
        knobTrackingTouchPoint = null;
      }
    }
  }
}

// Draw control pad
var drawPad = function() {
  var pad = document.getElementById("controlPad");
  var ctx = pad.getContext("2d");
  var center = padSize/2;
  var radius = 0.85 * center;

  ctx.clearRect(0,0,padSize,padSize);

  ctx.beginPath();
  ctx.fillStyle = "#00FF00";
  ctx.arc(center,center,radius,0,2*Math.PI);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(knobX, knobY, knobRadius, 0, 2*Math.PI);
  if (knobTracking)
  {
    ctx.fillStyle = "#0000FF";
  }
  else
  {
    ctx.fillStyle = "#FF0000";
  }
  ctx.fill()
}