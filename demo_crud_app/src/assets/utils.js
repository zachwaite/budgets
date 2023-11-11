function zoom(element) {
  var newTab = window.open();
  setTimeout(function () {
    const imgEl = element.firstElementChild.cloneNode();
    imgEl.removeAttribute("style");
    newTab.document.body.append(imgEl);
  }, 500);
  return false;
}
