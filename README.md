# icinga2checks
Aiming to make standard checks more useful

These are a variety of python based icinga2 checks that either did not exist yet or that add some functionality to existing checks.

The biggest design goal for these checks is that they have to be actually useful in a real world scenario. This means that the check output does not contain useless information - things that should only be performance data are performance data, and things that should only be in the check output (like serial numbers), are only in the check output. The plugins also take advantage over the revolutionary new technology called newline, making output more readable.

Some plugins also perform differently in OK, WARNING or CRITICAL conditions. check_mem.py for example returns the most memory consuming processes in WARNING or CRITICAL.

We aim to also have a consistent coding style and good documentation within the code. This is of course work in progress.
