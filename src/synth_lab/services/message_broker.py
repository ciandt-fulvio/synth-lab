"""
Message broker for real-time SSE streaming.

Singleton pub/sub broker for interview messages during research execution.

References:
    - asyncio.Queue: https://docs.python.org/3/library/asyncio-queue.html
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BrokerMessage:
    """Message published through the broker."""

    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class MessageBroker:
    """Singleton broker for pub/sub of interview messages.

    Allows multiple SSE clients to subscribe to execution events.
    Each execution has its own list of subscriber queues.
    """

    _instance: "MessageBroker | None" = None
    _subscribers: dict[str, list[asyncio.Queue[BrokerMessage | None]]]

    def __new__(cls) -> "MessageBroker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance

    def subscribe(self, exec_id: str) -> asyncio.Queue[BrokerMessage | None]:
        """Subscribe to messages for an execution.

        Args:
            exec_id: Execution ID to subscribe to

        Returns:
            Queue that will receive messages for this execution
        """
        if exec_id not in self._subscribers:
            self._subscribers[exec_id] = []
        queue: asyncio.Queue[BrokerMessage | None] = asyncio.Queue()
        self._subscribers[exec_id].append(queue)
        return queue

    async def publish(self, exec_id: str, message: BrokerMessage) -> None:
        """Publish a message to all subscribers for an execution.

        Args:
            exec_id: Execution ID to publish to
            message: Message to publish
        """
        if exec_id in self._subscribers:
            for queue in self._subscribers[exec_id]:
                await queue.put(message)

    def unsubscribe(self, exec_id: str, queue: asyncio.Queue[BrokerMessage | None]) -> None:
        """Unsubscribe a queue from an execution.

        Args:
            exec_id: Execution ID to unsubscribe from
            queue: Queue to remove
        """
        if exec_id in self._subscribers:
            try:
                self._subscribers[exec_id].remove(queue)
            except ValueError:
                pass  # Queue already removed
            if not self._subscribers[exec_id]:
                del self._subscribers[exec_id]

    async def close_execution(self, exec_id: str) -> None:
        """Signal end of execution to all subscribers.

        Sends None sentinel to all queues, signaling they should close.

        Args:
            exec_id: Execution ID that completed
        """
        if exec_id in self._subscribers:
            for queue in self._subscribers[exec_id]:
                await queue.put(None)

    def get_subscriber_count(self, exec_id: str) -> int:
        """Get number of subscribers for an execution.

        Args:
            exec_id: Execution ID to check

        Returns:
            Number of active subscribers
        """
        return len(self._subscribers.get(exec_id, []))

    def clear(self) -> None:
        """Clear all subscriptions. Used for testing."""
        self._subscribers.clear()


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Singleton pattern
    total_tests += 1
    try:
        broker1 = MessageBroker()
        broker2 = MessageBroker()
        if broker1 is not broker2:
            all_validation_failures.append("MessageBroker should be singleton")
        broker1.clear()  # Clean state for tests
    except Exception as e:
        all_validation_failures.append(f"Singleton test failed: {e}")

    # Test 2: Subscribe creates queue
    total_tests += 1
    try:
        broker = MessageBroker()
        broker.clear()
        queue = broker.subscribe("test_exec_1")
        if not isinstance(queue, asyncio.Queue):
            all_validation_failures.append(f"Subscribe should return Queue: {type(queue)}")
        if broker.get_subscriber_count("test_exec_1") != 1:
            all_validation_failures.append(
                f"Should have 1 subscriber: {broker.get_subscriber_count('test_exec_1')}"
            )
    except Exception as e:
        all_validation_failures.append(f"Subscribe test failed: {e}")

    # Test 3: Multiple subscribers
    total_tests += 1
    try:
        broker = MessageBroker()
        broker.clear()
        queue1 = broker.subscribe("test_exec_2")
        queue2 = broker.subscribe("test_exec_2")
        if broker.get_subscriber_count("test_exec_2") != 2:
            all_validation_failures.append(
                f"Should have 2 subscribers: {broker.get_subscriber_count('test_exec_2')}"
            )
        if queue1 is queue2:
            all_validation_failures.append("Each subscription should have unique queue")
    except Exception as e:
        all_validation_failures.append(f"Multiple subscribers test failed: {e}")

    # Test 4: Publish and receive (async)
    total_tests += 1

    async def test_publish_receive() -> str | None:
        broker = MessageBroker()
        broker.clear()
        queue = broker.subscribe("test_exec_3")

        msg = BrokerMessage(
            event_type="message",
            data={"synth_id": "synth_001", "text": "Hello"},
        )
        await broker.publish("test_exec_3", msg)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        if received is None:
            return "Received None instead of message"
        if received.event_type != "message":
            return f"Event type mismatch: {received.event_type}"
        if received.data["synth_id"] != "synth_001":
            return f"Data mismatch: {received.data}"
        return None

    try:
        result = asyncio.run(test_publish_receive())
        if result:
            all_validation_failures.append(result)
    except Exception as e:
        all_validation_failures.append(f"Publish/receive test failed: {e}")

    # Test 5: Unsubscribe removes queue
    total_tests += 1
    try:
        broker = MessageBroker()
        broker.clear()
        queue = broker.subscribe("test_exec_4")
        if broker.get_subscriber_count("test_exec_4") != 1:
            all_validation_failures.append("Should have 1 subscriber before unsubscribe")
        broker.unsubscribe("test_exec_4", queue)
        if broker.get_subscriber_count("test_exec_4") != 0:
            all_validation_failures.append(
                f"Should have 0 subscribers after unsubscribe: "
                f"{broker.get_subscriber_count('test_exec_4')}"
            )
    except Exception as e:
        all_validation_failures.append(f"Unsubscribe test failed: {e}")

    # Test 6: Close execution sends sentinel
    total_tests += 1

    async def test_close_execution() -> str | None:
        broker = MessageBroker()
        broker.clear()
        queue = broker.subscribe("test_exec_5")
        await broker.close_execution("test_exec_5")

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        if received is not None:
            return f"Close should send None sentinel: {received}"
        return None

    try:
        result = asyncio.run(test_close_execution())
        if result:
            all_validation_failures.append(result)
    except Exception as e:
        all_validation_failures.append(f"Close execution test failed: {e}")

    # Test 7: BrokerMessage dataclass
    total_tests += 1
    try:
        msg = BrokerMessage(event_type="message", data={"key": "value"})
        if msg.event_type != "message":
            all_validation_failures.append(f"Event type mismatch: {msg.event_type}")
        if msg.timestamp is None:
            all_validation_failures.append("Timestamp should have default")
        if not isinstance(msg.timestamp, datetime):
            all_validation_failures.append(f"Timestamp should be datetime: {type(msg.timestamp)}")
    except Exception as e:
        all_validation_failures.append(f"BrokerMessage test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
