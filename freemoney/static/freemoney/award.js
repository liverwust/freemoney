$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "award") {
    var nr_forms = Number.parseInt($('input[name="form-TOTAL_FORMS"]').val());
    for (var i = 0; i < nr_forms; i++) {
      (function (i_s) {
        /* Turn the award name into a collapser button */
        /* TODO: val() into what should be HTML */
        var award_name = $('input[name="form-'+i_s+'-name"]').first();
        var collapser = $('<button type="button" data-toggle="collapse" data-target="#collapse-form-'+i_s+'" class="btn btn-primary">'+award_name.val()+'</button>');
        award_name.siblings('label').remove();
        award_name.attr('type', 'hidden');
        collapser.insertAfter(award_name);

        /* Turn the description into a (maybe-collapsed) static div */
        var award_desc = $('textarea[name="form-'+i_s+'-description"]').first();
        award_desc.siblings('label').remove();
        award_desc.css('display', 'none');
        var static_div = $('<div id="collapse-form-' +
                           i_s +
                           '" class="well collapse"><p>' +
                           award_desc.val() +
                           /* TODO: val() into what should be HTML */
/*                           (award_desc[0]).innerHTML +*/
                           '</p></div>');
        static_div.insertAfter(award_desc);

        /* Turn the checkbox into a button */
        var checkbox = $('input[name="form-'+i_s+'-selected"]').first();
        checkbox.closest('div.checkbox').replaceWith(checkbox);
        checkbox.attr('autocomplete', 'off'); /* Bootstrap recommendation */
        checkbox.wrap('<label class="btn btn-selector"></label>')
                .after('Apply for the ' + award_name.val());
        checkbox.parent()
                .wrap('<div class="btn-group" data-toggle="buttons"></div>');
        checkbox.parent().parent()
                .appendTo(static_div);
        if (checkbox.prop('checked')) {
          checkbox.closest('label').addClass('active');
          /* this is a Bootstrap collapse-related class */
          checkbox.closest('div.collapse').addClass('in');
        }
      })((new Number(i)).toString());
    }
  }
});
