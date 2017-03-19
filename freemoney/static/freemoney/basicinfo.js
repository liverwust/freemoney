$(function () {
  if ($('input[name="currentstep"][type="hidden"]').val() === "basicinfo") {
    var psu_email = $('input[name="psu_email"]');
    psu_email.wrap('<div class="input-group"></div>');
    psu_email.after('<span class="input-group-addon">@psu.edu</span>');

    var year_initiated = $('input[name="year_initiated"]');
    var semester_initiated = $('select[name="semestertype_initiated"]');
    semester_initiated.wrap('<div class="row"></div>');
    year_initiated.clone().insertAfter(semester_initiated)
                          .wrap('<div class="col-md-2"></div>');
    semester_initiated.wrap('<div class="col-md-2"></div>');
    year_initiated.closest('div.form-group').remove();

    var year_graduating = $('input[name="year_graduating"]');
    var semester_graduating = $('select[name="semestertype_graduating"]');
    semester_graduating.wrap('<div class="row"></div>');
    year_graduating.clone().insertAfter(semester_graduating)
                           .wrap('<div class="col-md-2"></div>');
    semester_graduating.wrap('<div class="col-md-2"></div>');
    year_graduating.closest('div.form-group').remove();

    var modified_at = $('input[name="transcript_modified_at"]').val();
    if (modified_at !== '') {
      var transcript = $('input[type="file"][name="transcript"]');
      transcript.closest('div.bootstrap3-multi-input')
                .before('<a href="/freemoney/transcript.pdf">Transcript uploaded at '+modified_at+'</a>');
    }
  }
});
