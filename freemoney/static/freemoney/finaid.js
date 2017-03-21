$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "finaid") {
    var nr_forms = Number.parseInt($('input[name="form-TOTAL_FORMS"]').val());
    for (var i = 0; i < nr_forms; i++) {
      (function (i_s) {
        /* Add a delete button for every row except the final blank row */
        var row_finaid_id = $('input[name="form-'+i_s+'-finaid_id"]');
        if (row_finaid_id.val() !== '') {
          var row_id = Number.parseInt(row_finaid_id.val());
          var row_td = $('input[type!="hidden"][name^="form-'+i_s+'"]').first();
          var new_button = $('<button type="submit" class="btn btn-primary" name="submit-type" value="delete-'+row_id+'"><span class="glyphicon glyphicon-minus" aria-hidden="true"></span></button>');
          new_button.appendTo(row_td.closest('tr').find('td:last'));
        }
      })((new Number(i)).toString());
    }

    $('button[name="submit-type"][value="save"]').prop('disabled', true);
    $('input').on('change', function () {
      $('button[name="submit-type"][value="save"]').prop('disabled', false);
    });
    register_close_warning();
  }
});
