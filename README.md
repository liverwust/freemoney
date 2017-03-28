freemoney
=========

This is a custom web application for collecting information about Penn
State Chapter of Triangle scholarship candidates.  It is intended to
facilitate improvements in the collection process by making it easier
for candidates to provide structured information, and for reviewers to
access that information.


Motivation
----------

Similar solutions have preceded this one, including (but probably not
limited to) a custom PHP application on psutriangle.org and several
incarnations of Google Forms.  These solutions addressed many of the
requirements imposed by our fraternity's scholarship process, but they
stopped short of providing several useful enhancements which I suspect
will quickly prove their utility and *become* requirements for any
future solution.

The central enhancement provided by this web application is added
structure in responses.  Particularly, insufficient financial aid
information has stymied the Scholarship Committee's attempts to award
scholarships to otherwise-deserving brothers.  By laying out *exactly*
what sort of information is required, and by validating that information
before allowing the form to be submitted, this problem will be
mitigated.

Other important enhancements include:

* Support for advanced *conditionals*: this application currently checks
  an applicant's awards when determining which essays to show, and also
  verifies that only certain majors apply for certain awards
* Authentication: administrators can create applicant accounts without
  depending on a third-party service (e.g., Google) which not all
  applicants might use
* Full control over collected data: instead of relying on a third-party
  service to protect our applicants' data (including from the service
  providers themselves), all such data is now stored on a server that
  the brotherhood can control
* Full control over styling: although primarily aesthetic, there are
  also cases where third-party applications have actually been
  *confusing* to use (e.g., unusual textarea behavior in Google Forms)


User Guide
----------

TBD.  For now, follow the instructions in the web interface.


Technical Information
---------------------

TBD. Uses Django. Should have an INSTALL.md file at some point...


Future Directions
-----------------

The addition of several further enhancements would bring this
application closer to meeting all of our needs (and wants) for the
scholarship application process:

* Deep-linking: if a candidates information were directly accessible
  through an (authenticated) URI, then that URI could be embedded
  directly in an outside document; the intent is to include
  authoritative candidate information in-line in, say, a Google Doc
  being used for scholarship review
* Transcript upload: rather than copy-pasting it into a field as in
  previous solutions, why not have it directly inside of the
  application? Bonus points if the transcript is automatically *parsed*
  to obtain major, minor, GPA, and semester standing information.
* Full authentication support: or at least the ability to change
  passwords would be very nice.
* Interactive word counts: would just be fancy!
