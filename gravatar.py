from cStringIO import StringIO
from md5 import md5
import Image
import urllib2 as urllib


def gravatar_url_for_email(email):
  return "http://www.gravatar.com/avatar/{0}.jpg".format(md5(email).hexdigest())

def image_from_url(url):
  return Image.open(StringIO(urllib.urlopen(url).read()))

def commit_author_gravatar_image(commit):
  return image_from_url(gravatar_url_for_email(commit.author.email))

if __name__ == '__main__':
  from git.repo import Repo
  repo = Repo('../balance')
  for thing in ['balance-release-2010.1.0', 'balance-release-2012.1.2', 'develop', 'release']:
    commit_author_gravatar_image(repo.commit(thing)).show()

