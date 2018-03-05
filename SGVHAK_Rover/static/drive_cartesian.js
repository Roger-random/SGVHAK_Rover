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

// Default control pad size.
var padSize = 300;

// Center coordinate to use pad calculations
var centerX = padSize/2;
var centerY = padSize/2;

// Knob class encapsulates the functionality associated with the control knob
class Knob {
  constructor(knobRadius, maxRadius) {
    // (knobX,knobY is relative to pad center at (0,0)
    this.knobX = 0;
    this.knobY = 0;

    // Percentage of max (knobX,knobY). Angle is controlled by knobX and
    // magnitude is controlled by knobY
    this.angle = 0;
    this.magnitude = 0;

    // Radius for drawing visual representation of control knob.
    this.knobRadius = knobRadius;

    // Maximum permitted distance from center (0,0) to (knobX,knobY)
    this.maxRadius = maxRadius;

    // Whether the knob is current tracking input events.
    this.knobTracking = false;

    // Whenthe knob is tracking a multitouch event, ID for the touch point
    // currently being tracked.
    this.knobTrackingTouchPoint = null;
  }

  // We're only hit-testing the rectangle that encloses the knob, since this
  // math is simpler and faster. Revisit if this shortcut causes UI issues.
  contains(x,y) {
    return (x > (this.knobX-this.knobRadius) &&
            x < (this.knobX+this.knobRadius) &&
            y > (this.knobY-this.knobRadius) &&
            y < (this.knobY+this.knobRadius));
  }

  // True if we the knob is currently tracking an input pointer.
  get isTracking() {
    return this.knobTracking;
  }

  // Pass in true if we've started tracking an input pointer.
  tracking(status) {
    this.knobTracking = status;
  }

  // When tracking a touch pointer, we also remember the pointer identifier.
  get getTouch() {
    return this.knobTrackingTouchPoint;
  }

  // Touch pointer identifier, null if not currently tracking a touch pointer.
  setTouch(newTouchPoint) {
    this.knobTrackingTouchPoint = newTouchPoint;
  }

  // Updates knob position to the given x,y coordinates
  moveTo(x,y) {
    // Constrain x within -maxRadius <= x <= maxRadius
    this.knobX = Math.min(Math.max(x, -this.maxRadius), this.maxRadius);
    this.knobY = Math.min(Math.max(y, -this.maxRadius), this.maxRadius);

    this.angle = Math.round(100*this.knobX/this.maxRadius);
    this.magnitude = Math.round(-100*this.knobY/this.maxRadius);
  }

  // Draws knob on the given context. Caller is expected to have transformed
  //  the canvas so knob is centered on 0,0.
  draw(ctx) {
    ctx.save();
    ctx.beginPath();

    ctx.arc(this.knobX, this.knobY, this.knobRadius , 0, 2*Math.PI);
    if (this.knobTracking)
    {
      ctx.fillStyle = "#00FF00";
    }
    else
    {
      ctx.fillStyle = "#FF0000";
    }
    ctx.fill();
    ctx.restore();
  }
}

var knob = null;

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
    centerX = padSize/2;
    centerY = padSize/2;

    knob = new Knob(padSize*.1, padSize*.4);
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

// When Mouse or Touch event occurs, their respective handlers will pull out
// the x/y coordinates and pass into these common handlers.
var pointerStart = function(x,y) {
  if (knob.contains(x,y)) {
    knob.moveTo(x,y);
    knob.tracking(true);
    window.requestAnimationFrame(drawPad);
    sendDriveCommand();
  }
}

var pointerMove = function(x,y) {
  if (knob.isTracking) {
    knob.moveTo(x,y);
    window.requestAnimationFrame(drawPad);
    sendDriveCommand();
  }
}

var pointerEnd = function() {
  if (knob.isTracking) {
    knob.moveTo(knob.knobX,0);
    knob.tracking(false);
    window.requestAnimationFrame(drawPad);
    sendDriveCommand();
  }
}

// Send control knob location to server
// Because input events may occur faster than the underlying mechanical bits
// can respond, we constrain the frequency of updates we send to the server.
var sendDriveTimer = null;

var sendDriveCommand = function() {
  if (knob.magnitude == 0) {
    // Magnitude zero is a stop command, which we execute immediately.
    postCommand()
  }
  if ( sendDriveTimer == null) {
    // No timer, so let's start one to respond to this burst of events.
    sendDriveTimer = window.setTimeout(postCommand, 200 /* milliseconds */);
  }

  // If magnitude is not zero and there is already a timer, do nothing.
}

// Method to actually send data to server, rate of calling this function
// is contrained by sendDriveCommand() use of sendDriveTimer.
var postCommand = function() {
  $.ajax({
    type: "POST",
    url: document.getElementById("command").value,
    data: {pct_angle:knob.angle, magnitude:knob.magnitude},
    error: pointerEnd
  })

  // Command has bee POST-ed to server, clear the timer for the next batch.
  if (sendDriveTimer) {
    window.clearTimeout(sendDriveTimer);
    sendDriveTimer = null;
  }
}

// For mouse control, we only want to start the knob tracking if the user
// deliberately started on the control knob. Clicking elsewhere on the pad
// should be ignored.
var padMouseDown = function(e) {
  pointerStart(e.offsetX-centerX,e.offsetY-centerY);
}

var padMouseMove = function(e) {
  pointerMove(e.offsetX-centerX,e.offsetY-centerY);
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
  if (knob.isTracking) {
    // Already tracking a touch point, ignore newly started ones.
    return;
  }
  var newTouches = e.changedTouches;

  for (var i = 0; i < newTouches.length; i++) {
    var touch = newTouches[i];

    // Correct for X/Y client offset and pad center X/Y
    var touchX = touch.clientX - touch.target.getBoundingClientRect().left - centerX;
    var touchY = touch.clientY - touch.target.getBoundingClientRect().top - centerY;

    if (knob.contains(touchX, touchY)) {
      // A newly touched-down point is within knob space. This will be our
      // joystick control pointer.
      knob.setTouch(touch.identifier);
      pointerStart(touchX, touchY);
      break;
    }
  }
}

var padTouchMove = function(e) {
  if (knob.isTracking) {
    var newTouches = e.changedTouches;

    for (var i = 0; i < newTouches.length; i++) {
      var touch = newTouches[i];
      if (touch.identifier == knob.getTouch) {
        // Correct for X/Y client offset
        var touchX = touch.clientX - touch.target.getBoundingClientRect().left - centerX;
        var touchY = touch.clientY - touch.target.getBoundingClientRect().top - centerY;

        pointerMove(touchX, touchY);
        break;
      }
    }
  }
}

var padTouchEnd = function(e) {
  if (knob.isTracking) {
    var newTouches = e.changedTouches;

    for (var i = 0; i < newTouches.length; i++) {
      var touch = newTouches[i];
      if (touch.identifier == knob.getTouch) {
        pointerEnd();
        knob.trackTouch(null);
        break;
      }
    }
  }
}

// Draw control pad
var drawPad = function() {
  var pad = document.getElementById("controlPad");
  var ctx = pad.getContext("2d");

  ctx.clearRect(0,0,padSize,padSize);

  ctx.fillStyle = "#0000FF";
  ctx.fillRect(padSize*0.1,padSize*0.1,padSize*0.8,padSize*0.8);

  ctx.save();
  ctx.translate(centerX, centerY);
  knob.draw(ctx);
  ctx.restore();
}
