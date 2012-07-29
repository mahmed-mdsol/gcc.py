import pytest
from gcc.observers import EventDispatcher

class TestEventDispatcher:

	def observer(self, *args):
		self.observer_called = True
		self.observer_called_with = args

	def specific_observer(self, name, thing, number):
		self.observer_called = True
		self.name = name
		self.thing = thing
		self.number = number

	def setup_method(self, method):
		self.dispatcher = EventDispatcher()
		self.observer_called = False

	def test_event(self):
		'''If an event is provided, the observer is registered to the event.'''
		events = ['event1', 'event2']
		self.dispatcher.add_observer(self.observer, *events)
		for evt in events:
			self.dispatcher.fire(evt)
			assert self.observer_called
			assert self.observer_called_with == ()
			self.observer_called = False

	def test_event_with_args(self):
		event = 'lulz'
		self.dispatcher.add_observer(self.observer, event)
		self.dispatcher.fire(event, 1337, 9001)
		assert self.observer_called
		assert self.observer_called_with == (1337, 9001)


