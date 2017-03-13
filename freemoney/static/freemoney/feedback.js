$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "feedback") {
    var nr_forms = Number.parseInt($('input[name="form-TOTAL_FORMS"]').val());
    for (var i = 0; i < nr_forms; i++) {
      (function (i_s) {
        var peer_name_field = $('input[name="form-'+i_s+'-peer_name"]').first();
        var feedback_field = $('textarea[name="form-'+i_s+'-feedback"]').first();
        var new_button = $('<button type="button" data-toggle="button" class="btn btn-selector feedbackbutton">Provide feedback for '+peer_name_field.val()+'</button>');

        peer_name_field.attr('type', 'hidden');
        peer_name_field.siblings('label').replaceWith(new_button);
        feedback_field.siblings('label').remove();
        feedback_field.closest('div.form-group').addClass('collapse');

        if (feedback_field.val().length === 0) {
          feedback_field.closest('div.collapse').collapse('hide');
          new_button.attr('aria-pressed', 'false');
        }
        else {
          feedback_field.closest('div.collapse').collapse('show');
          new_button.attr('aria-pressed', 'true');
          new_button.addClass('active');
        }

        new_button.on('click', function (outer_e) {
          if (feedback_field.val().length !== 0) {
            $('#dialog-peer-name-display').html(peer_name_field.val());
            $('.dialog-peer-name-button').on('click.freemoney', function (e) {
              $('#dialog-peer-name-warn').modal('hide');
              $('.dialog-peer-name-button').off('click.freemoney');
              if (e.target.id === 'dialog-peer-name-confirm') {
                feedback_field.val('');
                new_button.click();
              }
            });
            $('#dialog-peer-name-warn').modal('show');
            outer_e.stopImmediatePropagation();
          }
          else {
            feedback_field.closest('div.collapse').collapse('toggle');
          }
        });
      })((new Number(i)).toString());
    }
  }
});
