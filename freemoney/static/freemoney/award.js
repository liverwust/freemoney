$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "award") {
    var nr_forms = Number.parseInt($('input[name="form-TOTAL_FORMS"]').val());
    for (var i = 0; i < nr_forms; i++) {
      (function (i_s) {
        var checkbox = $('input[name="form-'+i_s+'-selected"]').first();
        var award_name = $('input[name="form-'+i_s+'-name"]').first();
        var award_desc = $('textarea[name="form-'+i_s+'-description"]').first();

        checkbox.closest('div.checkbox').replaceWith(checkbox);
        checkbox.attr('autocomplete', 'off'); /* Bootstrap recommendation */
        checkbox.wrap('<label class="btn btn-selector"></label>')
                .after('Apply for the ' + award_name.val());
        checkbox.parent()
                .wrap('<div class="btn-group" data-toggle="buttons"></div>');
        if (checkbox.prop('checked')) {
          checkbox.closest('label').addClass('active');
        }

        award_name.attr('type', 'hidden');
        award_name.closest('div.form-group').replaceWith(award_name);

        award_desc.siblings('label').remove();
        award_desc.css('display', 'none');
        award_desc.after('<div class="well">' +
                        (award_desc[0]).innerHTML +
                        '</div>');
      })((new Number(i)).toString());
    }
  }
});
