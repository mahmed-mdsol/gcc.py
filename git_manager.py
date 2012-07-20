import git

class GitManager:
  '''GitManager will help manage your repo with helpful utility methods'''

  def __init__(self, repo):
    '''Initialize the GitManager with the given local repo''' # TODO add ability to clone repos.
    self.repo = git.repo.Repo(repo)
    self.git = self.repo.git    #For direct access to actual the actual git executable.
    self.ref = self.repo.head

  def get_commits(self, filter_function=(lambda *args: True)):
    '''
    Returns a generator that will return commits that satisfy the given filter.
    The filter function can accept a Commit object and should return a Truthy value if the commit should be yielded.
    '''
    for commit in self.ref.commit.traverse():
      if filter_function(commit):
        yield commit

  def switch_to(self, ref):
    '''Checkout the given ref (could be a branch name, tag name, commit number, etc) in the working directory.'''
    self.ref = self.repo.refs[ref].checkout()
    return self.ref

  @property
  def first_commit(self):
    '''Get the first commit chronologically (the commit you'd get with git rev-list --reverse HEAD | head -1)'''
    return git.objects.commit.Commit.iter_items(self.repo, self.ref, reverse=True).next()

  @property
  def last_commit(self):
    '''Get the last commit chronologically (i.e. HEAD)'''
    return self.repo.head.commit


