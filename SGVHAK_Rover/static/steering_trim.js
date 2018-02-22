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
})

var radioSelect = function(e) {
  console.log("Radio button selected");
}

var trimAdjust = function(e) {
  console.log("Adjustment button clicked");
}

var trimCancel = function(e) {
  console.log("Trim action cancelled");
}

var trimZero = function(e) {
  console.log("Set position to be zero")
}