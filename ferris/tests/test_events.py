import unittest
from ferris.core.event import Event, NamedEvents


class EventTest(unittest.TestCase):

    def testEvent(self):
        event = Event()
        called_list = []

        def test_listener(x):
            called_list.append(x)

        event += test_listener
        event(True)

        self.assertTrue(True in called_list)

        del called_list[:]

        event -= test_listener
        event.fire(True)
        self.assertTrue(True not in called_list)


class NamedEventsTest(unittest.TestCase):

    def testNamedEvents(self):
        events = NamedEvents()

        called_list = []

        def test_listener_one(x):
            called_list.append(x)

        def test_listener_two(x):
            called_list.remove(x)

        events.add_item += test_listener_one
        events.remove_item += test_listener_two

        events.add_item(True)

        self.assertTrue(True in called_list)

        events.remove_item(True)

        self.assertTrue(True not in called_list)
