function register_close_warning() {
  $(window).on('beforeunload.freemoney', function () {
    var save_button = $('button[name="submit-type"][value="save"]');
    if (save_button.length > 0 && !save_button.prop('disabled')) {
      return 'Warning! You have unsaved changes! Really close the page?';
    }
  });
  $('form').on('submit.freemoney', function () {
    $(window).off('beforeunload.freemoney');
  });
}
$(function () {
  var b = $('button[name="submit-type"][value="restart"][id!="restart-for-real"]');
  b.on('click', function (e) {
    e.preventDefault();
    e.stopImmediatePropagation();
    $('#dialog-restart-warn').modal('show');
  });
});
