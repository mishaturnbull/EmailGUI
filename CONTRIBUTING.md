# Contributions

All contributions to this program are welcomed!  I'm glad you chose to help!

Due to the nature of this program's capabilities, and the fact that it's easy to use to harass people, I do enforce a few rules for contributors (including myself) for liability reasons.  The rundown is that all commits must be [signed off][signoff] to certify that the person committing actually wrote the commit in question.  This is enforced using GitHub's DCO extension that checks for signoffs on all commits before merging to master.

Also, because a bug in this program could have severe consequences (imagine if the program accidently fills in the `to` address with the `from` address -- I accidently blasted my own inbox in testing multiple times) all commits must meet style guides before being merged to master (kinda -- right now, TravisCI just ensures that no new style violations are being added).  Master is a protected branch and should never be commited on directly.

# Contributing Method

If you'd like to contribute to this program, the preferred manner of doing so is the fork-and-pull workflow.  That is:

1. You fork the repo at present time.
2. You make desired changes on your fork.
3. Open a pull request back to this copy.
4. We work out any potential issues with the merge and commit changes.

A more in-depth guide can be found [here][forkandpull]

# Notice 9/27/2018

As of adding this file, version 2 is underway on the `2.x` branch [(see PR #21)][ver2PR].  Because of this, I'm focusing all my efforts on the upcoming version 2 and not much at all on the older code currently located on master; and until 2 is properly released onto the `develop` branch I would prefer that you do the same!  This is because version 2 is an entire rewrite, which all at once exterminates most bugs with the old version and incorporates a lot of new features.  Working on the old code is just a waste of time as it will all soon be overwritten.


[signoff]: https://stackoverflow.com/questions/1962094/what-is-the-sign-off-feature-in-git-for
[forkandpull]: https://github.com/susam/gitpr
[ver2PR]: https://github.com/mishaturnbull/EmailGUI/pull/21
