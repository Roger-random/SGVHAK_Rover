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

// Upon document load, start to query the server for wheel angle and velocity.
$(document).ready(function() {
  setTimeout(requestWheels, 1000);
})

// Begin the asyncyronous server request to obtain latest wheel updates.
// If successful, call updateWheels to process results.
var requestWheels = function() {
  $.ajax({
    type: "POST",
    url: document.getElementById("request_wheel_status").value,
    data: "all",
    success: updateWheels
  });
}

// Upon successful completion of POST started by requestWheels(), we receive
// a chunk of JSON that represents the wheel status. Iterate through each
// wheel and call updateWheelCanvas to draw the update in visual form.
// If all goes well, set a timer to repeat the process soon.
var updateWheels = function(data, textStatus, jqXHR) {
  Object.keys(data).forEach(function(key,index) {
    updateWheelCanvas(key, data[key].angle, data[key].velocity);
  })
  setTimeout(requestWheels, 200);
}

// Given a wheel name, its angle, and its velocity, find the <canvas> tag
// representing that wheel and draw a visual representation.
var updateWheelCanvas = function(name, angle, velocity) {
  var canvas = document.getElementById("canvas_"+name);
  var ctx = canvas.getContext("2d");
  var wheelW = canvas.width*0.4;
  var wheelH = canvas.height*0.8;

  ctx.clearRect(0,0,canvas.width,canvas.height);

  ctx.save();
  ctx.translate(canvas.width/2, canvas.height/2);
  ctx.rotate(angle * Math.PI/180);
  ctx.strokeRect(-wheelW/2, -wheelH/2, wheelW, wheelH);
  ctx.fillStyle = "#008000";
  if (velocity > 0) {
    var drawH = (wheelH/2)*(velocity/100);
    ctx.fillRect(-wheelW/2, -drawH, wheelW, drawH);
  } else if (velocity < 0) {
    var drawH = (wheelH/2)*(-velocity/100);
    ctx.fillRect(-wheelW/2, 0, wheelW, drawH);
  }
  ctx.restore();

}