$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "essay") {
    $('button[name="submit-type"][value="save"]').prop('disabled', true);
    $('textarea').on('change', function () {
      $('button[name="submit-type"][value="save"]').prop('disabled', false);
    });
    register_close_warning();
  }
});
