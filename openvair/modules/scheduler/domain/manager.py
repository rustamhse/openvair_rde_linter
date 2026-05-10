"""Module for managing scheduler domain operations.

This module provides the entry point for managing scheduler domain operations.
It creates an RPC server to consume messages related to scheduler management.

#TODO classes

#TODO dependencies
"""

from openvair.libs.log import get_logger
from openvair.modules.scheduler.domain import model
from openvair.libs.messaging.messaging_agents import MessagingServer

LOG = get_logger('domain-manager')


class SchedulerDomainManager:
    """RPC manager bootstrap contract for scheduler domain layer."""

    def create_job(self, data: dict) -> dict:
        """Compatibility RPC method name."""
        scheduler = model.SchedulerFactory()(
            {'type': 'system_cron', 'user': 'root'}
        )
        return scheduler.create(data)

    def edit_job(self, data: dict) -> dict:
        """Compatibility RPC method name."""
        scheduler = model.SchedulerFactory()(
            {'type': 'system_cron', 'user': 'root'}
        )
        return scheduler.edit(data)

    def delete_job(self, data: dict) -> None:
        """Compatibility RPC method name."""
        scheduler = model.SchedulerFactory()(
            {'type': 'system_cron', 'user': 'root'}
        )
        scheduler.delete(data)

    @staticmethod
    def run() -> None:
        """Start scheduler domain RPC server."""
        server = MessagingServer(
            queue_name='scheduler_service_layer_domain_queue',
            manager=model.SchedulerFactory(),
        )
        server.start()


if __name__ == '__main__':
    LOG.info('Starting RPCServer for consuming')
    SchedulerDomainManager.run()
