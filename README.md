# `django-yamldoc` – quoins for static sites

This is a Django application for maintaining documents in YAML format and
refining them to a traditional ORM’d database to serve them to users. It’s for
people who prefer VCS and powerful text editors over SQL and plutonian
web-based administrative interfaces.

## Status

`yamldoc` is technically reusable, and used in multiple personal projects over
the years, with some individual YAML documents over a hundred thousand lines
long. However, `yamldoc` is probably of no interest to you. Its architecture
is less elegant than the average Django app, mixing various concerns united
only by the theme of refining YAML to HTML via quearyable SQL.

`yamldoc.util.file` is more likely than the rest to be of any interest, if you
to want to pick and choose code under the license. That module handles wrapping
and unwrapping of lines (of Markdown) in version-controlled YAML documents.

## History

`yamldoc` was originally called `vedm` for “Viktor Eikman’s Django miscellania”.

Per Django recommendation, `yamldoc` ships with its migrations. Because the
application is designed for static sites where the entire database is routinely
rebuilt and therefore disposable, these migrations have been overwritten a few
times. Under `semver`, things should be more stable nowadays, but do tell me if
you rely on that.

## Legal

Copyright 2016–2021 Viktor Eikman

`django-yamldoc` is licensed as detailed in the accompanying file LICENSE.
