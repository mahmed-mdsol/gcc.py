import git

class GitManager:
  '''GitManager will help manage your repo with helpful utility methods'''

  PULL_REQUEST_FILTER = lambda self, commit: commit.summary.find("Merge pull request #") == 0

  def __init__(self, repo):
    '''Initialize the GitManager with the given local repo''' # TODO add ability to clone repos.
    self.repo = git.repo.Repo(repo)
    self.git = self.repo.git    #For direct access to actual the actual git executable.
    self.ref = self.repo.head

  def commits_for(self, *refs):
    '''Returns a generator that will yield Commit objects for the given refs in order.'''
    for ref in refs:
      yield self.repo.commit(ref)

  def commits_in_range(self, from_ref, to_ref, inclusive=True):
    '''Returns commits in the range (inclusive or exclusive depending on the inclusive arg) between from_ref and to_ref in order.'''
    if from_ref and to_ref:
      start_commit = self.repo.commit(from_ref)
      yield start_commit # This is necessary since from_ref...to_ref excludes from_ref for some reason.
      end_commit = self.repo.commit(to_ref)
      for commit in self.repo.iter_commits("{0}...{1}".format(str(start_commit), str(end_commit))):
        yield commit

  def get_commits(self, refs=[], from_ref=None, to_ref=None, filter_function=(lambda *args: True), **kwargs):
    '''
    Returns a generator that will return commits for the given refs that satisfy the given filter (if provided).

    refs should be a collection of references (branch/tag/HEAD/SHA1, etc) to retrieve a commit for. 
    
    from_ref and to_ref provide an inclusive range of commits to retrieve.

    The filter function must accept a Commit object and should return a Truthy value if the commit should be yielded.

    If other keyword arguments are given, the keyword arguments will be passed directly into repo.iter_commits, which expects
    the following:
      * rev (active_branch is used if none provided)
      * paths (the files to limit commits to [use a tuple to union commits from different files together])
      * any other args that git-rev-list takes like max_count, reverse, and skip.

    Note: the order of retrieved commits should not be relied on. Currently, if provided, commits for the given 
          refs are retrieved first, followed by commits in the range between from_ref and to_ref, followed by the 
          results from git-rev-list for kwargs (all filtered by the filter_function if provided)
    '''
    for commit in self.commits_for(*refs):
      if filter_function(commit):
        yield commit

    for commit in self.commits_in_range(from_ref, to_ref):
      if filter_function(commit):
        yield commit

    if kwargs:
      for commit in self.repo.iter_commits(**kwargs):
        if filter_function(commit):
          yield commit

  def switch_to(self, ref):
    '''Checkout the given ref (could be a branch name, tag name, commit number, etc) in the working directory.'''
    self.ref = ref
    self.git.checkout(self.ref)
    return self.ref

  @property
  def first_commit(self):
    '''Get the first commit chronologically (the commit you'd get with git rev-list --reverse HEAD | head -1)'''
    return self.get_commits(rev=self.ref, reverse=True).next()

  @property
  def last_commit(self):
    '''Get the last commit chronologically (i.e. HEAD)'''
    return self.repo.head.commit

  def first_commit_for(self, filename):
    '''Get the first commit for a given file.'''
    return self.get_commits(paths=filename, reverse=True).next()



