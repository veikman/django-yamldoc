# `django-yamldoc`: Quoins for static sites

This is a Django application for maintaining documents in YAML format and
refining them to a traditional ORM’d database to serve them to users. It’s for
people who prefer VCS over SQL.

## Status

`yamldoc` is technically reusable, and used in multiple personal projects over
the years, with some individual YAML documents over a hundred thousand lines
long. However, `yamldoc` is probably of no interest to you. Its architecture
is less elegant than the average Django app, mixing various concerns united
only by the theme of refining YAML to HTML via quearyable SQL.

## History

`yamldoc` was originally called `vedm` for “Viktor Eikman’s Django miscellania”.

`yamlwrap`, available [here](https://github.com/veikman/yamlwrap), was once a
central component of `yamldoc`.

## Legal

Copyright 2016–2021 Viktor Eikman

`django-yamldoc` is licensed as detailed in the accompanying file LICENSE.
