$(function () {
  $('.feedbackbutton').each(function (index, elem) {
    /* Button for choosing a particular peer to provide feedback for */
    var button = $(elem);
    /* Textarea where the feedback actually goes (initially hidden) */
    var textarea = button.closest('.row').find('textarea').first();
    /* Collapsible div containing the textarea */
    var collapse = textarea.closest('.collapse');

    button.on('click.freemoney', function () {
      if (button.attr('data-toggle') == 'button') {
        /* Bootstrap controls button state, but we control textarea collapse */
        collapse.collapse('toggle');
      }
      else {
        /* Do not allow the user to dismiss feedback without confirmation */
        /* TODO: actual prompt */
        alert('hello world');
        textarea.val('');
        textarea.change();
        button.click();
      }
    });

    textarea.on('change.freemoney', function () {
      if (textarea.val().length == 0) {
        /* No text remains, so return full control to Bootstrap */
        button.attr('data-toggle', 'button');
      }
      else {
        /* Lock the button when text is entered, to prevent data loss */
        button.removeAttr('data-toggle');
      }
    });

    /* Initialize the handlers, plus the collapsible div */
    textarea.change();
    if (textarea.val().length == 0) {
      collapse.collapse({toggle: false});
    }
    else {
      collapse.collapse({toggle: true});
    }
  });
});
