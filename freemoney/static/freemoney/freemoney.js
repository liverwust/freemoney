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
