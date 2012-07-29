from collections import defaultdict

class EventDispatcher(object):
	'''
	Implement the Observer pattern. 
	Inheriting from this class will give the class the ability to register and notify observers.
	The only restriction on observers is that they must be callable and must take the 
	'''

	def __init__(self):
		self.__observers = defaultdict(list) # Create a dict that will initialize the key to an empty list if it doesn't exist.

	# TODO: cool feature: look for on_* methods in the observer and register the methods for each * event!
	def add_observer(self, observer, *events):
		for event in events:
			self.__observers[event].append(observer)

	def add_observers(self, **eventToObservers):
		'''
		Register multiple observers to different events at once using key-value pairs.
		event1=observer1, other_event=observer1, yet_another_event=observer2, interesting_event=(observer1, observer2)
		'''
		for event in eventToObservers:
			try:
				# Pretend that the observers are lists
				for observer in eventToObservers[event]:
					self.add_observer(observer, event)
			except TypeError:
				# Well if that didn't work, assume it's an individual observer
				self.add_observer(eventToObservers[event], event)

	def fire(self, event, *args, **kwargs):
		if event in self.__observers: # Technically, this isn't needed, but this prevents unnecessary entries into the observers dict.
			for observer in self.__observers[event]:
				try:
					observer(*args, **kwargs)
				except Exception as e:
					print "Observer", observer, "raised", repr(e), "when called with", args, kwargs

	# Aliases
	register_observer = add_observer
	register_observers = add_observers
	notify = fire


# The GlobalDispatcher can be used if an application needs a singleton instance to use for dispatching and observing.
GlobalDispatcher = EventDispatcher()
